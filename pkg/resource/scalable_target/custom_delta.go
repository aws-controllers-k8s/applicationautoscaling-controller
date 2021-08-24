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

// customSetDefaults is a temporary workaround until the code generator supports adding server-side defaults.
func customSetDefaults(
	a *resource,
	b *resource,
) {
	if ackcompare.IsNil(a.ko.Spec.SuspendedState) && ackcompare.IsNotNil(b.ko.Spec.SuspendedState) {
		a.ko.Spec.SuspendedState = &svcapitypes.SuspendedState{}
	}

	if ackcompare.IsNotNil(a.ko.Spec.SuspendedState) && ackcompare.IsNotNil(b.ko.Spec.SuspendedState) {
		if ackcompare.IsNil(a.ko.Spec.SuspendedState.DynamicScalingInSuspended) && ackcompare.IsNotNil(b.ko.Spec.SuspendedState.DynamicScalingInSuspended) {
			a.ko.Spec.SuspendedState.DynamicScalingInSuspended = b.ko.Spec.SuspendedState.DynamicScalingInSuspended
		}
		if ackcompare.IsNil(a.ko.Spec.SuspendedState.DynamicScalingOutSuspended) && ackcompare.IsNotNil(b.ko.Spec.SuspendedState.DynamicScalingOutSuspended) {
			a.ko.Spec.SuspendedState.DynamicScalingOutSuspended = b.ko.Spec.SuspendedState.DynamicScalingOutSuspended
		}
		if ackcompare.IsNil(a.ko.Spec.SuspendedState.ScheduledScalingSuspended) && ackcompare.IsNotNil(b.ko.Spec.SuspendedState.ScheduledScalingSuspended) {
			a.ko.Spec.SuspendedState.ScheduledScalingSuspended = b.ko.Spec.SuspendedState.ScheduledScalingSuspended
		}
	}

	if ackcompare.IsNil(a.ko.Spec.RoleARN) && ackcompare.IsNotNil(b.ko.Spec.RoleARN) {
		a.ko.Spec.RoleARN = b.ko.Spec.RoleARN
	}

}
