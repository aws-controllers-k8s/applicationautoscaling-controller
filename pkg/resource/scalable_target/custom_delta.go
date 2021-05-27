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
	svcapitypes "github.com/aws-controllers-k8s/applicationautoscaling-controller/apis/v1alpha1"
	ackcompare "github.com/aws-controllers-k8s/runtime/pkg/compare"
)

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
}

func customSetDefaults(
	a *resource,
) {
	defaultValue := false
	
	if a.ko.Spec.SuspendedState == nil {
		a.ko.Spec.SuspendedState = &svcapitypes.SuspendedState{}
	}
	if a.ko.Spec.SuspendedState.DynamicScalingInSuspended == nil {
		a.ko.Spec.SuspendedState.DynamicScalingInSuspended = &defaultValue
	}
	if a.ko.Spec.SuspendedState.DynamicScalingOutSuspended == nil {
		a.ko.Spec.SuspendedState.DynamicScalingOutSuspended = &defaultValue
	}
	if a.ko.Spec.SuspendedState.ScheduledScalingSuspended == nil {
		a.ko.Spec.SuspendedState.ScheduledScalingSuspended = &defaultValue
	}

}
