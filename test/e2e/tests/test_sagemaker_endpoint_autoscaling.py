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
    resource_id = f"endpoint/{endpoint_name}/variant/variant-1"

    model_input, model_response = sagemaker_make_model(model_name)
    endpoint_config_input, endpoint_config_response = sagemaker_make_endpoint_config(
        model_name, endpoint_config_name
    )
    endpoint_input, endpoint_response = sagemaker_make_endpoint(
        endpoint_name, endpoint_config_name
    )

    wait_sagemaker_endpoint_status(endpoint_name, ENDPOINT_STATUS_INSERVICE)
    assert resource_id is not None

    yield resource_id
    sagemaker_client().delete_endpoint(EndpointName=endpoint_name)
    sagemaker_client().delete_endpoint_config(EndpointConfigName=endpoint_config_name)
    sagemaker_client().delete_model(ModelName=model_name)


@pytest.fixture(scope="module")
def generate_sagemaker_target(sagemaker_endpoint):
    resource_id = sagemaker_endpoint
    target_resource_name = random_suffix_name("sagemaker-scalable-target", 32)

    replacements = REPLACEMENT_VALUES.copy()
    replacements["SCALABLETARGET_NAME"] = target_resource_name
    replacements["RESOURCE_ID"] = resource_id

    target_reference, target_spec, target_resource = create_applicationautoscaling_resource(
        resource_plural=TARGET_RESOURCE_PLURAL,
        resource_name=target_resource_name,
        spec_file="sagemaker_endpoint_autoscaling_target",
        replacements=replacements,
    )

    assert target_resource is not None

    yield (resource_id, target_spec, target_reference)

    if k8s.get_resource_exists(target_reference):
        _, deleted = k8s.delete_custom_resource(target_reference)
        assert deleted


@pytest.fixture(scope="module")
def generate_sagemaker_policy(generate_sagemaker_target):
    resource_id, target_spec, target_reference = generate_sagemaker_target
    policy_resource_name = random_suffix_name("sagemaker-scaling-policy", 32)

    replacements = REPLACEMENT_VALUES.copy()
    replacements["SCALINGPOLICY_NAME"] = policy_resource_name
    replacements["RESOURCE_ID"] = resource_id

    policy_reference, policy_spec, policy_resource = create_applicationautoscaling_resource(
        resource_plural=POLICY_RESOURCE_PLURAL,
        resource_name=policy_resource_name,
        spec_file="sagemaker_endpoint_autoscaling_policy",
        replacements=replacements,
    )

    assert policy_resource is not None

    yield (resource_id, target_spec, target_reference, policy_resource, policy_spec, policy_reference)

    if k8s.get_resource_exists(policy_reference):
        _, deleted = k8s.delete_custom_resource(policy_reference)
        assert deleted


@service_marker
@pytest.mark.canary
class TestSageMakerEndpointAutoscaling:
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
        self, applicationautoscaling_client, resource_id: str, expectedPolicies: int
    ):
        try:
            policies = applicationautoscaling_client.describe_scaling_policies(
                ServiceNamespace="sagemaker",
                ResourceId=resource_id,
            )
            assert len(policies["ScalingPolicies"]) == expectedPolicies
            return policies["ScalingPolicies"]
        except botocore.exceptions.ClientError as error:
            logging.error(
                f"ApplicationAutoscaling could not find a scalingPolicy for the resource {resource_id}. Error {error}."
            )
            return None

    def test_create(self, applicationautoscaling_client, generate_sagemaker_policy):
        (
            resource_id,
            target_spec,
            target_reference,
            policy_resource,
            policy_spec,
            policy_reference,
        ) = generate_sagemaker_policy

        target_description = self.get_sagemaker_scalable_target_description(
            applicationautoscaling_client, resource_id, 1
        )
        assert target_description is not None

        policy_description = self.get_sagemaker_scaling_policy_description(
            applicationautoscaling_client, resource_id, 1
        )
        assert policy_description is not None

        assert k8s.get_resource_arn(policy_resource) is not None
        assert policy_description[0] is not None
        assert (
            k8s.get_resource_arn(policy_resource) == policy_description[0]["PolicyARN"]
        )

    def test_update(self, applicationautoscaling_client, generate_sagemaker_policy):
        (
            resource_id,
            target_spec,
            target_reference,
            policy_resource,
            policy_spec,
            policy_reference,
        ) = generate_sagemaker_policy

        updatedMaxCapacity = 4
        updatedTargetValue = 120
        
        # Update the ScalableTarget
        target_spec["spec"]["maxCapacity"] = updatedMaxCapacity
        k8s.patch_custom_resource(target_reference, target_spec)
        sleep(5)
        
        updated_target_description = self.get_sagemaker_scalable_target_description(
            applicationautoscaling_client, resource_id, 1
        )
        assert updated_target_description is not None
        assert (
            updated_target_description[0]["MaxCapacity"] == updatedMaxCapacity
        )

        # Update the ScalingPolicy
        policy_spec["spec"]["targetTrackingScalingPolicyConfiguration"]["targetValue"] = updatedTargetValue
        k8s.patch_custom_resource(policy_reference, policy_spec)
        sleep(5)
        updated_policy_description = self.get_sagemaker_scaling_policy_description(
            applicationautoscaling_client, resource_id, 1
        )
        assert updated_policy_description is not None
        assert (
            updated_policy_description[0]["TargetTrackingScalingPolicyConfiguration"]["TargetValue"] == updatedTargetValue
        )

    def test_delete(self, applicationautoscaling_client, generate_sagemaker_policy):
        (
            resource_id,
            target_spec,
            target_reference,
            policy_resource,
            policy_spec,
            policy_reference,
        ) = generate_sagemaker_policy

        # Delete the Resource

        _, deleted = k8s.delete_custom_resource(policy_reference)
        assert deleted is True

        _, deleted = k8s.delete_custom_resource(target_reference)
        assert deleted is True

        target_description = self.get_sagemaker_scalable_target_description(
            applicationautoscaling_client, resource_id, 0
        )

        # TODO: Ideally this check should pass after line 188 itself; but it requires the scalabletarget to be deleted too.
        policy_description = self.get_sagemaker_scaling_policy_description(
            applicationautoscaling_client, resource_id, 0
        )