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
	svcsdk "github.com/aws/aws-sdk-go/service/applicationautoscaling"
)

func (rm *resourceManager) customDescribeScalableTarget(
	ctx context.Context,
	latest *resource,
	input *svcsdk.DescribeScalableTargetsInput,
) {
	//input := &svcsdk.DescribeScalableTargetsInput{}
	latestSpec := latest.ko.Spec

	var resourceIDList []*string
	if latestSpec.ResourceID != nil {
		resourceIDList = append(resourceIDList, latestSpec.ResourceID)
		input.SetResourceIds(resourceIDList)
	}
}
