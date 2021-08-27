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


import boto3

def application_autoscaling_client():
    return boto3.client("application-autoscaling")

def sagemaker_endpoint_register_scalable_target(resource_id):
    target_input = {
        "ServiceNamespace": "sagemaker",
        "ResourceId": resource_id,
        "ScalableDimension": "sagemaker:variant:DesiredInstanceCount", 
        "MinCapacity": 1,
        "MaxCapacity": 2,
    }

    target_response = application_autoscaling_client().register_scalable_target(**target_input)
    return target_response

def sagemaker_endpoint_put_scaling_policy(resource_id, policy_name):
    policy_input = {
        "PolicyName": policy_name,
        "ServiceNamespace": "sagemaker",
        "ResourceId": resource_id,
        "ScalableDimension": "sagemaker:variant:DesiredInstanceCount", 
        "PolicyType": "TargetTrackingScaling",
        "TargetTrackingScalingPolicyConfiguration": {
            "TargetValue": 70.0,
            "ScaleInCooldown": 700,
            "ScaleOutCooldown": 300,
            "PredefinedMetricSpecification": {
                "PredefinedMetricType": "SageMakerVariantInvocationsPerInstance",
            },
        }
    }

    policy_response = application_autoscaling_client().put_scaling_policy(**policy_input)
    return policy_response

def sagemaker_endpoint_deregister_scalable_target(resource_id):
    target_input = {
        "ServiceNamespace": "sagemaker",
        "ResourceId": resource_id,
        "ScalableDimension": "sagemaker:variant:DesiredInstanceCount", 
    }

    target_response = application_autoscaling_client().deregister_scalable_target(**target_input)
    return target_response

def sagemaker_endpoint_delete_scaling_policy(resource_id, policy_name):
    policy_input = {
        "ServiceNamespace": "sagemaker",
        "ResourceId": resource_id,
        "ScalableDimension": "sagemaker:variant:DesiredInstanceCount", 
        "PolicyName": policy_name
    }

    policy_response = application_autoscaling_client().delete_scaling_policy(**policy_input)
    return policy_response

