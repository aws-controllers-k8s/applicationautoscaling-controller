# Application Autoscaling Policy on a SageMaker Endpoint
Autoscaling an endpoint requires two steps: registering the variant as a scalable target and putting the scaling policy onto each target (endpoint/variant). A step by Step guide is provided below.


## Prerequisites

1. Any Kubernetes Cluster with Kubectl installed. 
2. The ACK ApplicationAutoscaling CRDs installed on your cluster. Use the following command to verify:
```
$ kubectl get crd | grep applicationautoscaling

scalabletargets.applicationautoscaling.services.k8s.aws    2021-05-14T07:22:50Z
scalingpolicies.applicationautoscaling.services.k8s.aws    2021-05-14T07:22:50Z
scheduledactions.applicationautoscaling.services.k8s.aws   2021-05-14T07:22:50Z
```

3. The ACK ApplicationAutoscaling Controller Pod is running on your cluster. Use the following command to verify it is running:
```
$ kubectl get pods -A | grep applicationautoscaling

ack-system   ack-applicationautoscaling-controller-6945848b6c-krnx8    1/1   Running   0    23m
```

4. A SageMaker Endpoint `In-Service` with a variant deployed. You can apply the autoscaling policy to an existing endpoint/variant or you can create one using the ACK Sagemaker operator. If your Endpoint has multiple variants, you can apply the autoscaling policy to any one of them at one time. 


## Steps
1. For this demo, we will use the spec files included in this directory, namely `hosting-autoscaling-predefined.yaml`. It contains the specs necessary for both Registering the variant as a ScalableTarget as well as applying the desired ScalingPolicy to the variant. 
2. ApplicationAutoscaling on SageMaker requires the ResourceId to be in the following format - `endpoint/<your-endpoint-name>/variant/<endpoint's-variant-name>`. 
3. Use any text editor to open this file and edit as follows -
  - Replace the ResourceID for both the ScalableTarget and the ScalingPolicy with the string created above. 
  - Change the two metadata names and the ScalingPolicy Name if required. 
  - SageMaker requires some specific values to apply the autoscaling to your variant. Do not change these fields: `scalableDimension`, `serviceNamespace`. 
4. CREATION: This example applies a pre-defined metric to a single existing endpoint/variant as - 
```
$ kubectl apply -f hosting-autoscaling-predefined.yaml

scalabletarget.applicationautoscaling.services.k8s.aws/m-target-may13 created
scalingpolicy.applicationautoscaling.services.k8s.aws/m-scalingpolicy-may13 created
```

6. Check the Status of the ScalingPolicy by ensuring an ARN was generated. Else you can also logon to the AWS Console and check the endpoint Autoscaling status under the Amazon SageMaker service. 
```
$ kubectl describe scalingpolicy.applicationautoscaling.services.k8s.aws/m-scalingpolicy-may13

Name:         m-scalingpolicy-may13
Namespace:    default
Labels:       <none>
Annotations:  <none>
API Version:  applicationautoscaling.services.k8s.aws/v1alpha1
Kind:         ScalingPolicy
Metadata:
  Creation Timestamp:  2021-05-14T08:38:30Z
  Finalizers:
    finalizers.applicationautoscaling.services.k8s.aws/ScalingPolicy
  Generation:        1
  Resource Version:  6828
  Self Link:         /apis/applicationautoscaling.services.k8s.aws/v1alpha1/namespaces/default/scalingpolicies/m-scalingpolicy-may13
  UID:               abcdefghijklmnopqrstuvwxyz
Spec:
  Policy Name:         m-scalingpolicy-may13
  Policy Type:         TargetTrackingScaling
  Resource ID:         endpoint/m-no-ssm-custom-model-1/variant/AllTraffic
  Scalable Dimension:  sagemaker:variant:DesiredInstanceCount
  Service Namespace:   sagemaker
  Target Tracking Scaling Policy Configuration:
    Predefined Metric Specification:
      Predefined Metric Type:  SageMakerVariantInvocationsPerInstance
    Scale In Cooldown:         700
    Scale Out Cooldown:        300
    Target Value:              60
Status:
  Ack Resource Metadata:
    Arn:               arn:aws:autoscaling:<edited>:resource/sagemaker/endpoint/m-no-ssm-custom-model-1/variant/AllTraffic:policyName/m-scalingpolicy-may13
    Owner Account ID:  123456789012
  Alarms:
    Alarm ARN:   arn:aws:cloudwatch:us-west-2:123456789012:alarm:TargetTracking-endpoint/m-no-ssm-custom-model-1/variant/AllTraffic-AlarmHigh-..
    Alarm Name:  TargetTracking-endpoint/m-no-ssm-custom-model-1/variant/AllTraffic-AlarmHigh-..
    Alarm ARN:   arn:aws:cloudwatch:us-west-2:123456789012:alarm:TargetTracking-endpoint/m-no-ssm-custom-model-1/variant/AllTraffic-AlarmLow-..
    Alarm Name:  TargetTracking-endpoint/m-no-ssm-custom-model-1/variant/AllTraffic-AlarmLow-..
  Conditions:
Events:      <none>
```

7. DELETION: If you want to remove the policy from the variant, simply delete the kubernetes object using the same file as - 
```
$ kubectl delete -f hosting-autoscaling-predefined.yaml

scalabletarget.applicationautoscaling.services.k8s.aws "m-target-may13" deleted
scalingpolicy.applicationautoscaling.services.k8s.aws "m-scalingpolicy-may13" deleted
```

8. UPDATES: If you want to update the policy applied to your endpoint, you will have to follow a step by step process to first delete the existing policy, update the spec file and then re-apply the scaling policy. 

9. Other Spec Fields:
You can refer to the second sample provided here `hosting-autoscaling-custom-metric.yaml` to check out an example of using a `customMetric` in the scaling policy or fields like `suspendedState` in the scalable Target. 




 

