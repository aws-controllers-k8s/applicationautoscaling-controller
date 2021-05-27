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
)

func customSetDefaults(
	a *resource,
	b *resource,
) {
	if a.ko.Spec.SuspendedState == nil && b.ko.Spec.SuspendedState != nil {
		a.ko.Spec.SuspendedState = &svcapitypes.SuspendedState{}
	}
	if a.ko.Spec.SuspendedState.DynamicScalingInSuspended == nil && b.ko.Spec.SuspendedState.DynamicScalingInSuspended != nil {
		a.ko.Spec.SuspendedState.DynamicScalingInSuspended = b.ko.Spec.SuspendedState.DynamicScalingInSuspended
	}
	if a.ko.Spec.SuspendedState.DynamicScalingOutSuspended == nil && b.ko.Spec.SuspendedState.DynamicScalingOutSuspended != nil {
		a.ko.Spec.SuspendedState.DynamicScalingOutSuspended = b.ko.Spec.SuspendedState.DynamicScalingOutSuspended
	}
	if a.ko.Spec.SuspendedState.ScheduledScalingSuspended == nil && b.ko.Spec.SuspendedState.ScheduledScalingSuspended != nil {
		a.ko.Spec.SuspendedState.ScheduledScalingSuspended = b.ko.Spec.SuspendedState.ScheduledScalingSuspended
	}

	if a.ko.Spec.RoleARN == nil && b.ko.Spec.RoleARN != nil {
		a.ko.Spec.RoleARN = b.ko.Spec.RoleARN
	}

}
