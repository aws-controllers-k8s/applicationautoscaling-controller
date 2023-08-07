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

from acktest.resources import random_suffix_name
from acktest.k8s import resource as k8s

from e2e import service_marker, create_adopted_resource

from e2e.replacement_values import REPLACEMENT_VALUES
from e2e.common.sagemaker_utils import (
    sagemaker_client,
    wait_sagemaker_endpoint_status,
    sagemaker_make_model,
    sagemaker_make_endpoint_config,
    sagemaker_make_endpoint,
)
from e2e.common.utils import (
    sagemaker_endpoint_register_scalable_target,
    sagemaker_endpoint_put_scaling_policy,
    sagemaker_endpoint_deregister_scalable_target,
    sagemaker_endpoint_delete_scaling_policy,
)

TARGET_RESOURCE_PLURAL = "scalabletargets"
POLICY_RESOURCE_PLURAL = "scalingpolicies"
ENDPOINT_STATUS_INSERVICE = "InService"
CRD_GROUP = "applicationautoscaling.services.k8s.aws"
CRD_VERSION = "v1alpha1"


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

    _, _ = sagemaker_make_model(model_name)
    _, _ = sagemaker_make_endpoint_config(model_name, variant_name, endpoint_config_name)
    _, _ = sagemaker_make_endpoint(endpoint_name, endpoint_config_name)

    wait_sagemaker_endpoint_status(endpoint_name, ENDPOINT_STATUS_INSERVICE)
    assert resource_id is not None

    yield resource_id
    sagemaker_client().delete_endpoint(EndpointName=endpoint_name)
    sagemaker_client().delete_endpoint_config(EndpointConfigName=endpoint_config_name)
    sagemaker_client().delete_model(ModelName=model_name)


@pytest.fixture(scope="module")
def register_scalable_target(sagemaker_endpoint):
    resource_id = sagemaker_endpoint
    _ = sagemaker_endpoint_register_scalable_target(resource_id)

    yield resource_id
    sagemaker_endpoint_deregister_scalable_target(resource_id)


@pytest.fixture(scope="module")
def put_scaling_policy(register_scalable_target):
    resource_id = register_scalable_target
    policy_name = random_suffix_name("policy_name", 32)
    _ = sagemaker_endpoint_put_scaling_policy(resource_id, policy_name)

    yield resource_id, policy_name
    sagemaker_endpoint_delete_scaling_policy(resource_id, policy_name)


@pytest.fixture(scope="module")
def adopt_scalable_target(register_scalable_target):
    resource_id = register_scalable_target
    target_resource_name = random_suffix_name("sagemaker-scalable-target", 32)

    replacements = REPLACEMENT_VALUES.copy()
    replacements["ADOPTED_TARGET_NAME"] = target_resource_name
    replacements["RESOURCE_ID"] = resource_id

    adopted_target_reference, _, adopted_target_resource = create_adopted_resource(
        resource_name=target_resource_name,
        spec_file="sagemaker_endpoint_adopted_target",
        replacements=replacements,
    )

    assert adopted_target_resource is not None

    yield (resource_id, adopted_target_reference)

    if k8s.get_resource_exists(adopted_target_reference):
        _, deleted = k8s.delete_custom_resource(adopted_target_reference)
        assert deleted


@pytest.fixture(scope="module")
def adopt_scaling_policy(adopt_scalable_target, put_scaling_policy):
    resource_id, adopted_target_reference = adopt_scalable_target
    _, policy_name = put_scaling_policy
    policy_resource_name = random_suffix_name("sagemaker-scaling-policy", 32)

    replacements = REPLACEMENT_VALUES.copy()
    replacements["ADOPTED_POLICY_NAME"] = policy_resource_name
    replacements["RESOURCE_ID"] = resource_id
    replacements["POLICY_NAME"] = policy_name

    adopted_policy_reference, _, adopted_policy_resource = create_adopted_resource(
        resource_name=policy_resource_name,
        spec_file="sagemaker_endpoint_adopted_policy",
        replacements=replacements,
    )

    assert adopted_policy_resource is not None

    yield (resource_id, adopted_target_reference, adopted_policy_reference)

    if k8s.get_resource_exists(adopted_policy_reference):
        _, deleted = k8s.delete_custom_resource(adopted_policy_reference)
        assert deleted


@service_marker
@pytest.mark.canary
class TestAdopted:
    def test_sagemaker_endpoint_autoscaling(
        self, put_scaling_policy, adopt_scaling_policy
    ):
        sdk_resource_id, _ = put_scaling_policy

        (
            adopted_resource_id,
            adopted_target_reference,
            adopted_policy_reference,
        ) = adopt_scaling_policy

        assert sdk_resource_id == adopted_resource_id

        target_name = k8s.get_resource(adopted_target_reference)["spec"]["kubernetes"][
            "metadata"
        ]["name"]
        policy_name = k8s.get_resource(adopted_policy_reference)["spec"]["kubernetes"][
            "metadata"
        ]["name"]

        assert target_name is not None
        assert policy_name is not None

        for reference in (
            adopted_target_reference,
            adopted_policy_reference,
        ):
            assert k8s.wait_on_condition(reference, "ACK.Adopted", "True")

        target_reference = k8s.create_reference(
            CRD_GROUP, CRD_VERSION, TARGET_RESOURCE_PLURAL, target_name, "default"
        )
        target_resource = k8s.wait_resource_consumed_by_controller(target_reference)
        assert target_resource is not None

        assert target_resource["spec"].get("resourceID", None) == sdk_resource_id

        policy_reference = k8s.create_reference(
            CRD_GROUP, CRD_VERSION, POLICY_RESOURCE_PLURAL, policy_name, "default"
        )
        policy_resource = k8s.wait_resource_consumed_by_controller(policy_reference)
        assert policy_resource is not None

        assert policy_resource["spec"].get("resourceID", None) == sdk_resource_id

        # Delete the Adopted Resources
        _, deleted = k8s.delete_custom_resource(adopted_policy_reference)
        assert deleted is True

        _, deleted = k8s.delete_custom_resource(adopted_target_reference)
        assert deleted is True

        # Delete the ApplicationAutoscaling Resources
        _, deleted = k8s.delete_custom_resource(policy_reference)
        assert deleted is True

        _, deleted = k8s.delete_custom_resource(target_reference)
        assert deleted is True
