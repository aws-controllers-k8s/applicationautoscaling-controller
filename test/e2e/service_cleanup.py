# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may
# not use this file except in compliance with the License. A copy of the
# License is located at
#
# 	 http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.
"""Cleans up the resources created by the Application Auto Scaling bootstrapping process.
"""

import boto3
import logging
import re

from acktest import resources
from acktest.aws.identity import get_region

from e2e import bootstrap_directory
from e2e.bootstrap_resources import TestBootstrapResources

# Regex to match the role name from a role ARN
IAM_ROLE_ARN_REGEX = r"^arn:aws:iam::\d{12}:(?:root|user|role\/([A-Za-z0-9-]+))$"


def delete_dynamodb_table(table_name: str):
    region = get_region()
    dynamodb = boto3.client("dynamodb", region_name=region)

    dynamodb.delete_table(TableName=table_name)

    logging.info(f"Deleted DynamoDB table {table_name}")


def delete_execution_role(role_arn: str):
    region = get_region()
    iam = boto3.client("iam", region_name=region)

    role_name = re.match(IAM_ROLE_ARN_REGEX, role_arn).group(1)
    managedPolicy = iam.list_attached_role_policies(RoleName=role_name)
    for each in managedPolicy["AttachedPolicies"]:
        iam.detach_role_policy(RoleName=role_name, PolicyArn=each["PolicyArn"])

    inlinePolicy = iam.list_role_policies(RoleName=role_name)
    for each in inlinePolicy["PolicyNames"]:
        iam.delete_role_policy(RoleName=role_name, PolicyName=each)

    instanceProfiles = iam.list_instance_profiles_for_role(RoleName=role_name)
    for each in instanceProfiles["InstanceProfiles"]:
        iam.remove_role_from_instance_profile(
            RoleName=role_name, InstanceProfileName=each["InstanceProfileName"]
        )
    iam.delete_role(RoleName=role_name)

    logging.info(f"Deleted SageMaker execution role {role_name}")


def delete_data_bucket(bucket_name: str):
    region = get_region()
    s3_resource = boto3.resource("s3", region_name=region)

    bucket = s3_resource.Bucket(bucket_name)
    bucket.objects.all().delete()
    bucket.delete()

    logging.info(f"Deleted data bucket {bucket_name}")

def deregister_scalable_dynamodb_table(table_name: str) -> str:
    """Registers a DynamoDB table as a scalable target.

    Args:
        table_name: The DynamoDB table to register.

    Returns:
        str: The name of the DynamoDB table
    """
    region = get_region()

    applicationautoscaling_client = boto3.client(
        "application-autoscaling", region_name=region
    )
    applicationautoscaling_client.deregister_scalable_target(
        ServiceNamespace="dynamodb",
        ResourceId=f"table/{table_name}",
        ScalableDimension="dynamodb:table:WriteCapacityUnits",
    )

    logging.info(f"Deregistered DynamoDB table {table_name} as scalable target")

    return table_name

def service_cleanup(config: dict):
    logging.getLogger().setLevel(logging.INFO)

    resources = TestBootstrapResources(**config)

    try:
        delete_data_bucket(resources.SageMakerDataBucketName)
    except:
        logging.exception(
            f"Unable to delete data bucket {resources.SageMakerDataBucketName}"
        )
        pass

    try:
        delete_execution_role(resources.SageMakerExecutionRoleARN)
    except:
        logging.exception(
            f"Unable to delete execution role {resources.SageMakerExecutionRoleARN}"
        )
        pass

    try:
        delete_dynamodb_table(resources.ScalableDynamoTableName)
    except:
        logging.exception(
            f"Unable to delete DynamoDB table {resources.ScalableDynamoTableName}"
        )
        pass

    try:
        deregister_scalable_dynamodb_table(resources.RegisteredDynamoTableName)
    except:
        logging.exception(
            f"Unable to deregister scalable target {resources.RegisteredDynamoTableName}"
        )
        pass

    try:
        delete_dynamodb_table(resources.RegisteredDynamoTableName)
    except:
        logging.exception(
            f"Unable to delete DynamoDB table {resources.RegisteredDynamoTableName}"
        )
        pass


if __name__ == "__main__":
    bootstrap_config = resources.read_bootstrap_config(bootstrap_directory)
    service_cleanup(bootstrap_config)
