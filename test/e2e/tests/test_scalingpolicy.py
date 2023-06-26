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

RESOURCE_PLURAL = "scalingpolicies"


@pytest.fixture(scope="module")
def applicationautoscaling_client():
    return boto3.client("application-autoscaling")


@service_marker
@pytest.mark.canary
class TestScalingPolicy:
    def _generate_dynamodb_policy(
        self, bootstrap_resources: TestBootstrapResources
    ) -> Tuple[k8s.CustomResourceReference, Dict]:
        resource_name = random_suffix_name("dynamodb-scaling-policy", 32)

        replacements = REPLACEMENT_VALUES.copy()
        replacements["SCALINGPOLICY_NAME"] = resource_name
        replacements["DYNAMODB_TABLE"] = bootstrap_resources.RegisteredDynamoTableName

        policy = load_autoscaling_resource(
            "dynamodb_scalingpolicy", additional_replacements=replacements
        )
        logging.debug(policy)

        # Create the k8s resource
        reference = k8s.CustomResourceReference(
            CRD_GROUP, CRD_VERSION, RESOURCE_PLURAL, resource_name, namespace="default"
        )

        return (reference, policy)

    def _get_dynamodb_scaling_policy_exists(
        self, applicationautoscaling_client, policy_name: str
    ) -> bool:
        targets = applicationautoscaling_client.describe_scaling_policies(
            ServiceNamespace="dynamodb", PolicyNames=[policy_name]
        )

        return len(targets["ScalingPolicies"]) == 1

    def test_smoke(self, applicationautoscaling_client):
        (reference_a, policy_a) = self._generate_dynamodb_policy(get_bootstrap_resources())
        (reference_b, policy_b) = self._generate_dynamodb_policy(get_bootstrap_resources())

        resource = k8s.create_custom_resource(reference_a, policy_a)
        resource = k8s.wait_resource_consumed_by_controller(reference_a)
        assert k8s.get_resource_exists(reference_a)
        
        resource = k8s.create_custom_resource(reference_b, policy_b)
        resource = k8s.wait_resource_consumed_by_controller(reference_b)
        assert k8s.get_resource_exists(reference_b)

        policyNameA = policy_a["spec"].get("policyName")
        assert policyNameA is not None
        policyNameB = policy_b["spec"].get("policyName")
        assert policyNameB is not None

        exists = self._get_dynamodb_scaling_policy_exists(
            applicationautoscaling_client, policyNameA,
        )
        assert exists
        exists = self._get_dynamodb_scaling_policy_exists(
            applicationautoscaling_client, policyNameB,
        )
        assert exists

        _, deleted = k8s.delete_custom_resource(reference_a)
        assert deleted is True
        _, deleted = k8s.delete_custom_resource(reference_b)
        assert deleted is True

        exists = self._get_dynamodb_scaling_policy_exists(
            applicationautoscaling_client, policyName
        )
        assert not exists
