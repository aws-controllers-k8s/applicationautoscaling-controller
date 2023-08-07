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
"""Integration tests for the Application Auto Scaling ScalingPolicy API.
"""

import boto3
import botocore
import pytest
import datetime
import logging
from typing import Dict, Tuple

from acktest.resources import random_suffix_name
from acktest.k8s import resource as k8s
from time import sleep

from e2e import service_marker, create_applicationautoscaling_resource

from e2e.replacement_values import REPLACEMENT_VALUES
from e2e.bootstrap_resources import TestBootstrapResources, get_bootstrap_resources
from e2e.common.sagemaker_utils import (
    sagemaker_client,
    wait_sagemaker_endpoint_status,
    sagemaker_make_model,
    sagemaker_make_endpoint_config,
    sagemaker_make_endpoint,
)

TARGET_RESOURCE_PLURAL = "scalabletargets"
POLICY_RESOURCE_PLURAL = "scalingpolicies"
ENDPOINT_STATUS_INSERVICE = "InService"


@pytest.fixture(scope="module")
def name_suffix():
    return random_suffix_name("sagemaker-endpoint", 32)


@pytest.fixture(scope="module")
def applicationautoscaling_client():
    return boto3.client("application-autoscaling")


@pytest.fixture(scope="module")
def sagemaker_endpoint(name_suffix):
    model_name = name_suffix + "-model"
    endpoint_config_name = name_suffix + "-config"
    endpoint_name = name_suffix
    variant_name = "variant-1"
    resource_id = f"endpoint/{endpoint_name}/variant/variant-1"

    model_input, model_response = sagemaker_make_model(model_name)
    endpoint_config_input, endpoint_config_response = sagemaker_make_endpoint_config(
        model_name, variant_name, endpoint_config_name
    )
    endpoint_input, endpoint_response = sagemaker_make_endpoint(
        endpoint_name, endpoint_config_name
    )

    wait_sagemaker_endpoint_status(endpoint_name, ENDPOINT_STATUS_INSERVICE)
    assert resource_id is not None

    yield resource_id, endpoint_name, variant_name
    sagemaker_client().delete_endpoint(EndpointName=endpoint_name)
    sagemaker_client().delete_endpoint_config(EndpointConfigName=endpoint_config_name)
    sagemaker_client().delete_model(ModelName=model_name)


@pytest.fixture(scope="module")
def generate_sagemaker_target(sagemaker_endpoint):
    resource_id, endpoint_name, variant_name = sagemaker_endpoint
    target_resource_name = random_suffix_name("sagemaker-scalable-target", 32)

    replacements = REPLACEMENT_VALUES.copy()
    replacements["SCALABLETARGET_NAME"] = target_resource_name
    replacements["RESOURCE_ID"] = resource_id

    (
        target_reference,
        target_spec,
        target_resource,
    ) = create_applicationautoscaling_resource(
        resource_plural=TARGET_RESOURCE_PLURAL,
        resource_name=target_resource_name,
        spec_file="sagemaker_endpoint_autoscaling_target",
        replacements=replacements,
    )

    assert target_resource is not None

    yield (resource_id, endpoint_name, variant_name, target_reference, target_spec, target_resource)

    if k8s.get_resource_exists(target_reference):
        _, deleted = k8s.delete_custom_resource(target_reference)
        assert deleted


@pytest.fixture(scope="module")
def generate_sagemaker_policy_A(generate_sagemaker_target):
    (
        resource_id, _, _,
        target_reference,
        target_spec,
        target_resource,
    ) = generate_sagemaker_target
    policy_resource_name = random_suffix_name("sagemaker-scaling-policyA", 32)

    replacements = REPLACEMENT_VALUES.copy()
    replacements["SCALINGPOLICY_NAME"] = policy_resource_name
    replacements["RESOURCE_ID"] = resource_id

    (
        policy_reference,
        policy_spec,
        policy_resource,
    ) = create_applicationautoscaling_resource(
        resource_plural=POLICY_RESOURCE_PLURAL,
        resource_name=policy_resource_name,
        spec_file="sagemaker_endpoint_autoscaling_policy",
        replacements=replacements,
    )

    assert policy_resource is not None

    yield (
        resource_id,
        target_reference,
        target_spec,
        target_resource,
        policy_resource,
        policy_spec,
        policy_reference,
    )

    if k8s.get_resource_exists(policy_reference):
        _, deleted = k8s.delete_custom_resource(policy_reference)
        assert deleted


@pytest.fixture(scope="module")
def generate_sagemaker_policy_B(generate_sagemaker_target):
    (
        resource_id,
        endpoint_name,
        variant_name,
        target_reference,
        target_spec,
        target_resource,
    ) = generate_sagemaker_target
    policy_resource_name = random_suffix_name("sagemaker-scaling-policyB", 32)

    replacements = REPLACEMENT_VALUES.copy()
    replacements["SCALINGPOLICY_NAME"] = policy_resource_name
    replacements["RESOURCE_ID"] = resource_id
    replacements["ENDPOINT_NAME"] = endpoint_name
    replacements["VARIANT_NAME"] = variant_name

    (
        policy_reference,
        policy_spec,
        policy_resource,
    ) = create_applicationautoscaling_resource(
        resource_plural=POLICY_RESOURCE_PLURAL,
        resource_name=policy_resource_name,
        spec_file="sagemaker_endpoint_autoscaling_policy",
        replacements=replacements,
    )

    assert policy_resource is not None

    yield (
        resource_id,
        policy_resource,
        policy_spec,
        policy_reference,
    )

    if k8s.get_resource_exists(policy_reference):
        _, deleted = k8s.delete_custom_resource(policy_reference)
        assert deleted

@service_marker
@pytest.mark.canary
class TestSageMakerEndpointAutoscaling:
    def wait_until_update(
        self, reference, previous_modified_time, wait_period=2, wait_time=30
    ):
        for i in range(wait_period):
            resource = k8s.get_resource(reference)
            assert resource is not None
            assert "lastModifiedTime" in resource["status"]
            last_modified_time = resource["status"]["lastModifiedTime"]
            d1 = datetime.datetime.strptime(last_modified_time, "%Y-%m-%dT%H:%M:%SZ")
            d2 = datetime.datetime.strptime(
                previous_modified_time, "%Y-%m-%dT%H:%M:%SZ"
            )
            if d1 > d2:
                return True
            sleep(wait_time)
        return False

    def get_sagemaker_scalable_target_description(
        self, applicationautoscaling_client, resource_id: str, expectedTargets: int
    ):
        try:
            targets = applicationautoscaling_client.describe_scalable_targets(
                ServiceNamespace="sagemaker",
                ResourceIds=[resource_id],
            )

            assert len(targets["ScalableTargets"]) == expectedTargets
            return targets["ScalableTargets"]
        except botocore.exceptions.ClientError as error:
            logging.error(
                f"ApplicationAutoscaling could not find a scalableTarget for the resource {resource_id}. Error {error}."
            )
            return None

    def get_sagemaker_scaling_policy_description(
        self, applicationautoscaling_client, resource_id: str, policy_name: str
    ):
        try:
            policies = applicationautoscaling_client.describe_scaling_policies(
                ServiceNamespace="sagemaker",
                ResourceId=resource_id,
                PolicyNames=[policy_name]

            )
            return policies["ScalingPolicies"]
        except botocore.exceptions.ClientError as error:
            logging.error(
                f"ApplicationAutoscaling could not find a scalingPolicy for the resource {resource_id}, policyName {policy_name}. Error {error}."
            )
            return None

    def test_create(self, applicationautoscaling_client, generate_sagemaker_policy_A, generate_sagemaker_policy_B):
        (
            resource_id,
            target_reference,
            target_spec,
            target_resource,
            policy_resource_A,
            policy_spec_A,
            policy_reference_A,
        ) = generate_sagemaker_policy_A
        
        (resource_id, policy_resource_B, policy_spec_B, _) = generate_sagemaker_policy_B

        target_description = self.get_sagemaker_scalable_target_description(
            applicationautoscaling_client, resource_id, 1
        )
        assert target_description is not None

        assert k8s.get_resource_arn(policy_resource_A) is not None
        assert k8s.get_resource_arn(policy_resource_B) is not None

        policy_description_A = self.get_sagemaker_scaling_policy_description(
            applicationautoscaling_client, resource_id, policy_spec_A["spec"]["policyName"]
        )
        assert len(policy_description_A) > 0
        assert (
            k8s.get_resource_arn(policy_resource_A) == policy_description_A[0]["PolicyARN"]
        )

        policy_description_B = self.get_sagemaker_scaling_policy_description(
            applicationautoscaling_client, resource_id, policy_spec_B["spec"]["policyName"]
        )
        assert len(policy_description_B) > 0
        assert (
            k8s.get_resource_arn(policy_resource_B) == policy_description_B[0]["PolicyARN"]
        )

    def test_update(self, applicationautoscaling_client, generate_sagemaker_policy_A):
        (
            resource_id,
            target_reference,
            target_spec,
            target_resource,
            policy_resource,
            policy_spec,
            policy_reference,
        ) = generate_sagemaker_policy_A

        updatedMaxCapacity = 4
        updatedTargetValue = 120

        # Update the ScalableTarget
        target_spec["spec"]["maxCapacity"] = updatedMaxCapacity
        assert "lastModifiedTime" in target_resource["status"]
        last_modified_time = target_resource["status"]["lastModifiedTime"]
        k8s.patch_custom_resource(target_reference, target_spec)
        assert self.wait_until_update(target_reference, last_modified_time) == True

        updated_target_description = self.get_sagemaker_scalable_target_description(
            applicationautoscaling_client, resource_id, 1
        )
        assert updated_target_description is not None
        assert updated_target_description[0]["MaxCapacity"] == updatedMaxCapacity

        # Update the ScalingPolicy
        policy_spec["spec"]["targetTrackingScalingPolicyConfiguration"][
            "targetValue"
        ] = updatedTargetValue
        assert "lastModifiedTime" in policy_resource["status"]
        last_modified_time = policy_resource["status"]["lastModifiedTime"]
        k8s.patch_custom_resource(policy_reference, policy_spec)
        assert self.wait_until_update(policy_reference, last_modified_time) == True

        updated_policy_description = self.get_sagemaker_scaling_policy_description(
            applicationautoscaling_client, resource_id, policy_spec["spec"]["policyName"]
        )
        assert updated_policy_description is not None
        assert (
            updated_policy_description[0]["TargetTrackingScalingPolicyConfiguration"][
                "TargetValue"
            ]
            == updatedTargetValue
        )

    def test_delete(self, applicationautoscaling_client, generate_sagemaker_policy_A, generate_sagemaker_policy_B):
        (
            resource_id,
            target_reference,
            target_spec,
            target_resource,
            policy_resource_A,
            policy_spec_A,
            policy_reference_A,
        ) = generate_sagemaker_policy_A

        (_, policy_resource_B, policy_spec_B, _) = generate_sagemaker_policy_B

        # Delete the Resource

        _, deleted = k8s.delete_custom_resource(policy_reference_A)
        assert deleted is True

        _, deleted = k8s.delete_custom_resource(policy_reference_B)
        assert deleted is True

        _, deleted = k8s.delete_custom_resource(target_reference)
        assert deleted is True

        target_description = self.get_sagemaker_scalable_target_description(
            applicationautoscaling_client, resource_id, 0
        )

        # TODO: Ideally this check should pass after line 188 itself; but it requires the scalabletarget to be deleted too.
        policy_description_A = self.get_sagemaker_scaling_policy_description(
            applicationautoscaling_client, resource_id, policy_spec_A["spec"]["policyName"]
        )
        assert len(policy_description_A) = 0

        policy_description_B = self.get_sagemaker_scaling_policy_description(
            applicationautoscaling_client, resource_id, policy_spec_B["spec"]["policyName"]
        )
        assert len(policy_description_B) = 0
