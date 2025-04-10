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
	"time"

	svcapitypes "github.com/aws-controllers-k8s/applicationautoscaling-controller/apis/v1alpha1"
	svcsdk "github.com/aws/aws-sdk-go-v2/service/applicationautoscaling"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
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
		for _, resourceID := range resourceIDList {
			input.ResourceIds = append(input.ResourceIds, *resourceID)
		}
	}
}

// customSetLastModifiedTimeToCreationTime sets the LastModifiedTime field to the creationTime
func (rm *resourceManager) customSetLastModifiedTimeToCreationTime(ko *svcapitypes.ScalableTarget) {
	if ko.Status.CreationTime != nil && ko.Status.LastModifiedTime == nil {
		ko.Status.LastModifiedTime = ko.Status.CreationTime
	}
}

// customSetLastModifiedTimeToCurrentTime sets the LastModifiedTime field to the current time post an update
func (rm *resourceManager) customSetLastModifiedTimeToCurrentTime(ko *svcapitypes.ScalableTarget) {
	currentTime := metav1.Time{Time: time.Now().UTC()}
	ko.Status.LastModifiedTime = &currentTime
}

// customCheckRequiredFieldsMissing returns true if there are any fields
// for the ReadOne Input shape that are required but not present in the
// resource's Spec or Status
func (rm *resourceManager) customCheckRequiredFieldsMissing(
	r *resource,
) bool {
	return r.ko.Spec.ResourceID == nil

}
