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
"""Bootstraps the resources required to run the Application Auto Scaling
integration tests.
"""

import boto3
import logging
from time import sleep
import json
import time
import subprocess

from acktest import resources
from acktest.aws.identity import get_region, get_account_id
from e2e import bootstrap_directory
from e2e.bootstrap_resources import TestBootstrapResources
from acktest.aws.s3 import duplicate_bucket_contents
from e2e.bootstrap_resources import TestBootstrapResources, SAGEMAKER_SOURCE_DATA_BUCKET


def service_bootstrap() -> dict:
    logging.getLogger().setLevel(logging.INFO)

    try:
        data_bucket = create_data_bucket()
    except:
        data_bucket = ""
        logging.exception(
            "Unable to create data bucket"
        )

    try:
        execution_role = create_execution_role()
    except:
        execution_role = ""
        logging.exception(
            "Unable to create execution role"
        )

    try:
        scalable_table = create_dynamodb_table()
    except:
        scalable_table = ""
        logging.exception(
            "Unable to create DynamoDB table"
        )

    try:
        registered_table = create_dynamodb_table()
        register_scalable_dynamodb_table(registered_table)
    except:
        registered_table = ""
        logging.exception(
            "Unable to create DynamoDB table"
        )

    if not wait_for_dynamodb_table_active(
        scalable_table
    ) or not wait_for_dynamodb_table_active(registered_table):
        raise Exception("DynamoDB tables did not become ACTIVE")

    return TestBootstrapResources(
        data_bucket,
        execution_role,
        scalable_table,
        registered_table,
    ).__dict__


def create_execution_role() -> str:
    region = get_region()
    role_name = resources.random_suffix_name(f"ack-sagemaker-execution-role", 63)
    iam = boto3.client("iam", region_name=region)

    iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "sagemaker.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        ),
        Description="SageMaker execution role for ACK integration and canary tests",
    )

    iam.attach_role_policy(
        RoleName=role_name,
        PolicyArn="arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
    )
    iam.attach_role_policy(
        RoleName=role_name, PolicyArn="arn:aws:iam::aws:policy/AmazonS3FullAccess"
    )

    iam_resource = iam.get_role(RoleName=role_name)
    resource_arn = iam_resource["Role"]["Arn"]

    # There appears to be a delay in role availability after role creation
    # resulting in failure that role is not present. So adding a delay
    # to allow for the role to become available
    sleep(10)
    logging.info(f"Created SageMaker execution role {resource_arn}")

    return resource_arn


def create_data_bucket() -> str:
    region = get_region()
    account_id = get_account_id()
    bucket_name = resources.random_suffix_name(
        f"ack-data-bucket-{region}-{account_id}", 63
    )

    s3 = boto3.client("s3", region_name=region)
    if region == "us-east-1":
        s3.create_bucket(Bucket=bucket_name)
    else:
        s3.create_bucket(
            Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": region}
        )

    logging.info(f"Created SageMaker data bucket {bucket_name}")

    s3_resource = boto3.resource("s3", region_name=region)

    source_bucket = s3_resource.Bucket(SAGEMAKER_SOURCE_DATA_BUCKET)
    destination_bucket = s3_resource.Bucket(bucket_name)
    temp_dir = "/tmp/ack_s3_data"
    # awscli is not installed in test-infra container hence use boto3 to copy in us-west-2
    if region == "us-west-2":
        duplicate_bucket_contents(source_bucket, destination_bucket)
        # above method does an async copy
        # TODO: find a way to remove random wait
        sleep(180)
    else:
        # workaround to copy if buckets are across regions
        # TODO: check if there is a better way and merge to test-infra
        subprocess.call(["mkdir", f"{temp_dir}"])
        subprocess.call(
            [
                "aws",
                "s3",
                "sync",
                f"s3://{SAGEMAKER_SOURCE_DATA_BUCKET}",
                f"./{temp_dir}/",
                "--quiet",
            ]
        )
        subprocess.call(
            ["aws", "s3", "sync", f"./{temp_dir}/", f"s3://{bucket_name}", "--quiet"]
        )

    logging.info(f"Synced data bucket")

    return bucket_name


def create_dynamodb_table() -> str:
    """Create a DynamoDB table with a randomised table name.

    Returns:
        str: The name of the DynamoDB table
    """
    region = get_region()
    account_id = get_account_id()
    table_name = resources.random_suffix_name(
        f"ack-autoscaling-table-{region}-{account_id}", 63
    )

    dynamodb = boto3.client("dynamodb", region_name=region)
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{"AttributeName": "TablePrimaryAttribute", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "TablePrimaryAttribute", "AttributeType": "N"}
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 10, "WriteCapacityUnits": 10},
    )

    assert table["TableDescription"]["TableName"] == table_name
    logging.info(f"Created DynamoDB table {table_name}")

    return table_name


def wait_for_dynamodb_table_active(
    table_name: str, wait_periods: int = 6, period_length: int = 5
) -> bool:
    """Wait for the given DynamoDB table to reach ACTIVE status.

    Args:
        table_name: The DynamoDB table to poll.
        wait_periods: The number of times to poll for the status.
        period_length: The delay between polling calls.

    Returns:
        bool: True if the table reached ACTIVE status.
    """
    region = get_region()
    dynamodb = boto3.client("dynamodb", region_name=region)

    for _ in range(wait_periods):
        sleep(period_length)
        table = dynamodb.describe_table(TableName=table_name)

        status = table["Table"]["TableStatus"]
        if status == "ACTIVE":
            logging.info(f"DynamoDB table {table_name} has reached status {status}")
            return True

        logging.debug(f"DynamoDB table {table_name} is in status {status}. Waiting...")

    logging.error(f"Wait for DynamoDB table {table_name} to become ACTIVE timed out")
    return False


def register_scalable_dynamodb_table(table_name: str) -> str:
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
    applicationautoscaling_client.register_scalable_target(
        ServiceNamespace="dynamodb",
        ResourceId=f"table/{table_name}",
        ScalableDimension="dynamodb:table:WriteCapacityUnits",
        MinCapacity=50,
        MaxCapacity=100,
    )

    logging.info(f"Registered DynamoDB table {table_name} as scalable target")

    return table_name


if __name__ == "__main__":
    config = service_bootstrap()
    # Write config to current directory by default
    resources.write_bootstrap_config(config, bootstrap_directory)
