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

import pytest
from typing import Dict, Any
from pathlib import Path
import time
import boto3

from acktest.k8s import resource as k8s
from acktest.resources import load_resource_file
from e2e.replacement_values import REPLACEMENT_VALUES


def sagemaker_client():
    return boto3.client("sagemaker")


def wait_for_status(
    expected_status: str,
    wait_periods: int,
    period_length: int,
    get_status_method,
    *method_args,
):
    actual_status = None
    for _ in range(wait_periods):
        time.sleep(period_length)
        actual_status = get_status_method(*method_args)
        if actual_status == expected_status:
            break
    else:
        logging.error(
            f"Wait for status: {expected_status} timed out. Actual status: {actual_status}"
        )

    return actual_status


def get_endpoint_sagemaker_status(endpoint_name):
    response = sagemaker_client().describe_endpoint(EndpointName=endpoint_name)
    return response["EndpointStatus"]


def wait_sagemaker_endpoint_status(
    endpoint_name,
    expected_status: str,
    wait_periods: int = 60,
    period_length: int = 30,
):
    return wait_for_status(
        expected_status,
        wait_periods,
        period_length,
        get_endpoint_sagemaker_status,
        endpoint_name,
    )


def sagemaker_make_model(model_name):
    data_bucket = REPLACEMENT_VALUES["SAGEMAKER_DATA_BUCKET"]
    model_input = {
        "ModelName": model_name,
        "Containers": [
            {
                "Image": REPLACEMENT_VALUES["SAGEMAKER_XGBOOST_IMAGE_URI"],
                "ModelDataUrl": f"s3://{data_bucket}/sagemaker/model/xgboost-mnist-model.tar.gz",
            }
        ],
        "ExecutionRoleArn": REPLACEMENT_VALUES["SAGEMAKER_EXECUTION_ROLE_ARN"],
    }

    model_response = sagemaker_client().create_model(**model_input)
    assert model_response.get("ModelArn", None) is not None
    return model_input, model_response


def sagemaker_make_endpoint_config(model_name, endpoint_config_name):
    endpoint_config_input = {
        "EndpointConfigName": endpoint_config_name,
        "ProductionVariants": [
            {
                "VariantName": "variant-1",
                "ModelName": model_name,
                "InitialInstanceCount": 1,
                "InstanceType": "ml.c5.large",
            }
        ],
    }

    endpoint_config_response = sagemaker_client().create_endpoint_config(
        **endpoint_config_input
    )
    assert endpoint_config_response.get("EndpointConfigArn", None) is not None
    return endpoint_config_input, endpoint_config_response


def sagemaker_make_endpoint(endpoint_name, endpoint_config_name):
    endpoint_input = {
        "EndpointName": endpoint_name,
        "EndpointConfigName": endpoint_config_name,
    }
    endpoint_response = sagemaker_client().create_endpoint(**endpoint_input)
    assert endpoint_response.get("EndpointArn", None) is not None

    return endpoint_input, endpoint_response
