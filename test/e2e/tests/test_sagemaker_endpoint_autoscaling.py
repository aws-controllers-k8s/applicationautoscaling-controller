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
import pytest
import logging
from typing import Dict, Tuple

from acktest.resources import random_suffix_name
from acktest.k8s import resource as k8s

from e2e import service_marker, CRD_GROUP, CRD_VERSION, load_autoscaling_resource
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
ENDPOINT_CONFIG_RESOURCE_PLURAL = "endpointconfigs"
MODEL_RESOURCE_PLURAL = "models"
ENDPOINT_RESOURCE_PLURAL = "endpoints"
ENDPOINT_STATUS_INSERVICE = "InService"


@pytest.fixture(scope="module")
def name_suffix():
    return random_suffix_name("sagemaker-endpoint", 32)


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

    yield resource_id
    sagemaker_client().delete_endpoint(EndpointName=endpoint_name)
    sagemaker_client().delete_endpoint_config(EndpointConfigName=endpoint_config_name)
    sagemaker_client().delete_model(ModelName=model_name)


@pytest.fixture(scope="module")
def applicationautoscaling_client():
    return boto3.client("application-autoscaling")


@service_marker
@pytest.mark.canary
class TestSageMakerEndpointAutoscaling:
    resource_id: str

    def _generate_sagemaker_target_spec(
        self, bootstrap_resources: TestBootstrapResources
    ):
        target_resource_name = random_suffix_name("sagemaker-scalable-target", 32)

        replacements = REPLACEMENT_VALUES.copy()
        replacements["SCALABLETARGET_NAME"] = target_resource_name
        replacements["RESOURCE_ID"] = self.resource_id

        spec_file = load_autoscaling_resource(
            "sagemaker_endpoint_autoscaling_target",
            additional_replacements=replacements,
        )

        # Create the k8s resource
        reference = k8s.CustomResourceReference(
            CRD_GROUP,
            CRD_VERSION,
            TARGET_RESOURCE_PLURAL,
            target_resource_name,
            namespace="default",
        )

        return (target_resource_name, reference, spec_file)

    def _generate_sagemaker_policy_spec(
        self, bootstrap_resources: TestBootstrapResources
    ):
        policy_resource_name = random_suffix_name("sagemaker-scaling-policy", 32)

        replacements = REPLACEMENT_VALUES.copy()
        replacements["SCALINGPOLICY_NAME"] = policy_resource_name
        replacements["RESOURCE_ID"] = self.resource_id

        spec_file = load_autoscaling_resource(
            "sagemaker_endpoint_autoscaling_policy",
            additional_replacements=replacements,
        )

        # Create the k8s resource
        reference = k8s.CustomResourceReference(
            CRD_GROUP,
            CRD_VERSION,
            POLICY_RESOURCE_PLURAL,
            policy_resource_name,
            namespace="default",
        )

        return (policy_resource_name, reference, spec_file)

    def _get_sagemaker_scalable_target_exists(
        self, applicationautoscaling_client, target_name: str
    ) -> bool:
        targets = applicationautoscaling_client.describe_scalable_targets(
            ServiceNamespace="sagemaker",
            ResourceIds=[
                self.resource_id,
            ],
        )

        return len(targets["ScalableTargets"]) == 1

    def _get_sagemaker_scaling_policy_exists(
        self, applicationautoscaling_client, policy_name: str
    ) -> bool:
        targets = applicationautoscaling_client.describe_scaling_policies(
            ServiceNamespace="sagemaker",
            ResourceId=self.resource_id,
        )

        return len(targets["ScalingPolicies"]) == 1

    def test_smoke(self, applicationautoscaling_client, sagemaker_endpoint):
        self.resource_id = sagemaker_endpoint
        (
            target_name,
            target_reference,
            target_spec_file,
        ) = self._generate_sagemaker_target_spec(get_bootstrap_resources())
        (
            policy_name,
            policy_reference,
            policy_spec_file,
        ) = self._generate_sagemaker_policy_spec(get_bootstrap_resources())

        target_resource = k8s.create_custom_resource(target_reference, target_spec_file)
        target_resource = k8s.wait_resource_consumed_by_controller(target_reference)
        assert k8s.get_resource_exists(target_reference)

        policy_resource = k8s.create_custom_resource(policy_reference, policy_spec_file)
        policy_resource = k8s.wait_resource_consumed_by_controller(policy_reference)
        assert k8s.get_resource_exists(policy_reference)

        target_exists = self._get_sagemaker_scalable_target_exists(
            applicationautoscaling_client, target_name
        )
        assert target_exists

        policy_exists = self._get_sagemaker_scaling_policy_exists(
            applicationautoscaling_client, policy_name
        )
        assert policy_exists

        _, deleted = k8s.delete_custom_resource(policy_reference)
        assert deleted is True

        _, deleted = k8s.delete_custom_resource(target_reference)
        assert deleted is True

        target_exists = self._get_sagemaker_scalable_target_exists(
            applicationautoscaling_client, target_name
        )
        assert not target_exists

        # TODO: Ideally this check should pass after line 190 itself; but it requires the scalabletarget to be deleted too.
        policy_exists = self._get_sagemaker_scaling_policy_exists(
            applicationautoscaling_client, policy_name
        )
        assert not policy_exists
