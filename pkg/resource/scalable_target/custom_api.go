// Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License"). You may
// not use this file except in compliance with the License. A copy of the
// License is located at
//
//     http://aws.amazon.com/apache2.0/
//
// or in the "license" file accompanying this file. This file is distributed
// on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
// express or implied. See the License for the specific language governing
// permissions and limitations under the License.

package scalable_target

import (
	"context"
	ackcompare "github.com/aws-controllers-k8s/runtime/pkg/compare"
	svcsdk "github.com/aws/aws-sdk-go/service/applicationautoscaling"
)

func (rm *resourceManager) customDescribeScalableTarget(
	ctx context.Context,
	latest *resource,
	input *svcsdk.DescribeScalableTargetsInput,
) {
	latestSpec := latest.ko.Spec

	var resourceIDList []*string
	if latestSpec.ResourceID != nil {
		resourceIDList = append(resourceIDList, latestSpec.ResourceID)
		input.SetResourceIds(resourceIDList)
	}
}

func customCompare(
	a *resource,
	b *resource,
	delta *ackcompare.Delta,
) {
	if a.ko.Spec.RoleARN != nil {
		if ackcompare.HasNilDifference(a.ko.Spec.RoleARN, b.ko.Spec.RoleARN) {
			delta.Add("Spec.RoleARN", a.ko.Spec.RoleARN, b.ko.Spec.RoleARN)
		} else if a.ko.Spec.RoleARN != nil && b.ko.Spec.RoleARN != nil {
			if *a.ko.Spec.RoleARN != *b.ko.Spec.RoleARN {
				delta.Add("Spec.RoleARN", a.ko.Spec.RoleARN, b.ko.Spec.RoleARN)
			}
		}
	}

	if a.ko.Spec.SuspendedState != nil {
		if ackcompare.HasNilDifference(a.ko.Spec.SuspendedState, b.ko.Spec.SuspendedState) {
			delta.Add("Spec.SuspendedState", a.ko.Spec.SuspendedState, b.ko.Spec.SuspendedState)
		} else if a.ko.Spec.SuspendedState != nil && b.ko.Spec.SuspendedState != nil {
			if a.ko.Spec.SuspendedState.DynamicScalingInSuspended != nil {
				if ackcompare.HasNilDifference(a.ko.Spec.SuspendedState.DynamicScalingInSuspended, b.ko.Spec.SuspendedState.DynamicScalingInSuspended) {
					delta.Add("Spec.SuspendedState.DynamicScalingInSuspended", a.ko.Spec.SuspendedState.DynamicScalingInSuspended, b.ko.Spec.SuspendedState.DynamicScalingInSuspended)
				} else if a.ko.Spec.SuspendedState.DynamicScalingInSuspended != nil && b.ko.Spec.SuspendedState.DynamicScalingInSuspended != nil {
					if *a.ko.Spec.SuspendedState.DynamicScalingInSuspended != *b.ko.Spec.SuspendedState.DynamicScalingInSuspended {
						delta.Add("Spec.SuspendedState.DynamicScalingInSuspended", a.ko.Spec.SuspendedState.DynamicScalingInSuspended, b.ko.Spec.SuspendedState.DynamicScalingInSuspended)
					}
				}
			}
			if a.ko.Spec.SuspendedState.DynamicScalingOutSuspended != nil {
				if ackcompare.HasNilDifference(a.ko.Spec.SuspendedState.DynamicScalingOutSuspended, b.ko.Spec.SuspendedState.DynamicScalingOutSuspended) {
					delta.Add("Spec.SuspendedState.DynamicScalingOutSuspended", a.ko.Spec.SuspendedState.DynamicScalingOutSuspended, b.ko.Spec.SuspendedState.DynamicScalingOutSuspended)
				} else if a.ko.Spec.SuspendedState.DynamicScalingOutSuspended != nil && b.ko.Spec.SuspendedState.DynamicScalingOutSuspended != nil {
					if *a.ko.Spec.SuspendedState.DynamicScalingOutSuspended != *b.ko.Spec.SuspendedState.DynamicScalingOutSuspended {
						delta.Add("Spec.SuspendedState.DynamicScalingOutSuspended", a.ko.Spec.SuspendedState.DynamicScalingOutSuspended, b.ko.Spec.SuspendedState.DynamicScalingOutSuspended)
					}
				}
			}
			if a.ko.Spec.SuspendedState.ScheduledScalingSuspended != nil {
				if ackcompare.HasNilDifference(a.ko.Spec.SuspendedState.ScheduledScalingSuspended, b.ko.Spec.SuspendedState.ScheduledScalingSuspended) {
					delta.Add("Spec.SuspendedState.ScheduledScalingSuspended", a.ko.Spec.SuspendedState.ScheduledScalingSuspended, b.ko.Spec.SuspendedState.ScheduledScalingSuspended)
				} else if a.ko.Spec.SuspendedState.ScheduledScalingSuspended != nil && b.ko.Spec.SuspendedState.ScheduledScalingSuspended != nil {
					if *a.ko.Spec.SuspendedState.ScheduledScalingSuspended != *b.ko.Spec.SuspendedState.ScheduledScalingSuspended {
						delta.Add("Spec.SuspendedState.ScheduledScalingSuspended", a.ko.Spec.SuspendedState.ScheduledScalingSuspended, b.ko.Spec.SuspendedState.ScheduledScalingSuspended)
					}
				}
			}
		}
	}
}
