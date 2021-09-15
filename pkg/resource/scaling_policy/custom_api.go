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

package scaling_policy

import (
	svcapitypes "github.com/aws-controllers-k8s/applicationautoscaling-controller/apis/v1alpha1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"time"
)

// customSetOutputUpdate sets the LastModifiedTime field to the creationTime
func (rm *resourceManager) customSetLastModifiedTimeToCreationTime(ko *svcapitypes.ScalingPolicy) {
	if ko.Status.CreationTime != nil && ko.Status.LastModifiedTime == nil {
		ko.Status.LastModifiedTime = ko.Status.CreationTime
	}
}

// customSetOutputUpdate sets the LastModifiedTime field to the current time post an update
func (rm *resourceManager) customSetLastModifiedTimeToCurrentTime(ko *svcapitypes.ScalingPolicy) {
	currentTime := metav1.Time{Time: time.Now().UTC()}
	ko.Status.LastModifiedTime = &currentTime
}
