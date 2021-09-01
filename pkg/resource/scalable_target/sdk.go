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

// Code generated by ack-generate. DO NOT EDIT.

package scalable_target

import (
	"context"
	"strings"

	ackv1alpha1 "github.com/aws-controllers-k8s/runtime/apis/core/v1alpha1"
	ackcompare "github.com/aws-controllers-k8s/runtime/pkg/compare"
	ackerr "github.com/aws-controllers-k8s/runtime/pkg/errors"
	ackrtlog "github.com/aws-controllers-k8s/runtime/pkg/runtime/log"
	"github.com/aws/aws-sdk-go/aws"
	svcsdk "github.com/aws/aws-sdk-go/service/applicationautoscaling"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	svcapitypes "github.com/aws-controllers-k8s/applicationautoscaling-controller/apis/v1alpha1"
)

// Hack to avoid import errors during build...
var (
	_ = &metav1.Time{}
	_ = strings.ToLower("")
	_ = &aws.JSONValue{}
	_ = &svcsdk.ApplicationAutoScaling{}
	_ = &svcapitypes.ScalableTarget{}
	_ = ackv1alpha1.AWSAccountID("")
	_ = &ackerr.NotFound
)

// sdkFind returns SDK-specific information about a supplied resource
func (rm *resourceManager) sdkFind(
	ctx context.Context,
	r *resource,
) (latest *resource, err error) {
	rlog := ackrtlog.FromContext(ctx)
	exit := rlog.Trace("rm.sdkFind")
	defer exit(err)
	// If any required fields in the input shape are missing, AWS resource is
	// not created yet. Return NotFound here to indicate to callers that the
	// resource isn't yet created.
	if rm.requiredFieldsMissingFromReadManyInput(r) {
		return nil, ackerr.NotFound
	}

	input, err := rm.newListRequestPayload(r)
	if err != nil {
		return nil, err
	}
	rm.customDescribeScalableTarget(ctx, r, input)
	var resp *svcsdk.DescribeScalableTargetsOutput
	resp, err = rm.sdkapi.DescribeScalableTargetsWithContext(ctx, input)
	rm.metrics.RecordAPICall("READ_MANY", "DescribeScalableTargets", err)
	if err != nil {
		if awsErr, ok := ackerr.AWSError(err); ok && awsErr.Code() == "UNKNOWN" {
			return nil, ackerr.NotFound
		}
		return nil, err
	}

	// Merge in the information we read from the API call above to the copy of
	// the original Kubernetes object we passed to the function
	ko := r.ko.DeepCopy()

	found := false
	for _, elem := range resp.ScalableTargets {
		if elem.MaxCapacity != nil {
			ko.Spec.MaxCapacity = elem.MaxCapacity
		} else {
			ko.Spec.MaxCapacity = nil
		}
		if elem.MinCapacity != nil {
			ko.Spec.MinCapacity = elem.MinCapacity
		} else {
			ko.Spec.MinCapacity = nil
		}
		if elem.ResourceId != nil {
			ko.Spec.ResourceID = elem.ResourceId
		} else {
			ko.Spec.ResourceID = nil
		}
		if elem.RoleARN != nil {
			ko.Spec.RoleARN = elem.RoleARN
		} else {
			ko.Spec.RoleARN = nil
		}
		if elem.ScalableDimension != nil {
			ko.Spec.ScalableDimension = elem.ScalableDimension
		} else {
			ko.Spec.ScalableDimension = nil
		}
		if elem.ServiceNamespace != nil {
			ko.Spec.ServiceNamespace = elem.ServiceNamespace
		} else {
			ko.Spec.ServiceNamespace = nil
		}
		if elem.SuspendedState != nil {
			f7 := &svcapitypes.SuspendedState{}
			if elem.SuspendedState.DynamicScalingInSuspended != nil {
				f7.DynamicScalingInSuspended = elem.SuspendedState.DynamicScalingInSuspended
			}
			if elem.SuspendedState.DynamicScalingOutSuspended != nil {
				f7.DynamicScalingOutSuspended = elem.SuspendedState.DynamicScalingOutSuspended
			}
			if elem.SuspendedState.ScheduledScalingSuspended != nil {
				f7.ScheduledScalingSuspended = elem.SuspendedState.ScheduledScalingSuspended
			}
			ko.Spec.SuspendedState = f7
		} else {
			ko.Spec.SuspendedState = nil
		}
		found = true
		break
	}
	if !found {
		return nil, ackerr.NotFound
	}

	rm.setStatusDefaults(ko)
	return &resource{ko}, nil
}

// requiredFieldsMissingFromReadManyInput returns true if there are any fields
// for the ReadMany Input shape that are required but not present in the
// resource's Spec or Status
func (rm *resourceManager) requiredFieldsMissingFromReadManyInput(
	r *resource,
) bool {
	return false
}

// newListRequestPayload returns SDK-specific struct for the HTTP request
// payload of the List API call for the resource
func (rm *resourceManager) newListRequestPayload(
	r *resource,
) (*svcsdk.DescribeScalableTargetsInput, error) {
	res := &svcsdk.DescribeScalableTargetsInput{}

	if r.ko.Spec.ScalableDimension != nil {
		res.SetScalableDimension(*r.ko.Spec.ScalableDimension)
	}
	if r.ko.Spec.ServiceNamespace != nil {
		res.SetServiceNamespace(*r.ko.Spec.ServiceNamespace)
	}

	return res, nil
}

// sdkCreate creates the supplied resource in the backend AWS service API and
// returns a copy of the resource with resource fields (in both Spec and
// Status) filled in with values from the CREATE API operation's Output shape.
func (rm *resourceManager) sdkCreate(
	ctx context.Context,
	desired *resource,
) (created *resource, err error) {
	rlog := ackrtlog.FromContext(ctx)
	exit := rlog.Trace("rm.sdkCreate")
	defer exit(err)
	input, err := rm.newCreateRequestPayload(ctx, desired)
	if err != nil {
		return nil, err
	}

	var resp *svcsdk.RegisterScalableTargetOutput
	_ = resp
	resp, err = rm.sdkapi.RegisterScalableTargetWithContext(ctx, input)
	rm.metrics.RecordAPICall("CREATE", "RegisterScalableTarget", err)
	if err != nil {
		return nil, err
	}
	// Merge in the information we read from the API call above to the copy of
	// the original Kubernetes object we passed to the function
	ko := desired.ko.DeepCopy()

	rm.setStatusDefaults(ko)
	return &resource{ko}, nil
}

// newCreateRequestPayload returns an SDK-specific struct for the HTTP request
// payload of the Create API call for the resource
func (rm *resourceManager) newCreateRequestPayload(
	ctx context.Context,
	r *resource,
) (*svcsdk.RegisterScalableTargetInput, error) {
	res := &svcsdk.RegisterScalableTargetInput{}

	if r.ko.Spec.MaxCapacity != nil {
		res.SetMaxCapacity(*r.ko.Spec.MaxCapacity)
	}
	if r.ko.Spec.MinCapacity != nil {
		res.SetMinCapacity(*r.ko.Spec.MinCapacity)
	}
	if r.ko.Spec.ResourceID != nil {
		res.SetResourceId(*r.ko.Spec.ResourceID)
	}
	if r.ko.Spec.RoleARN != nil {
		res.SetRoleARN(*r.ko.Spec.RoleARN)
	}
	if r.ko.Spec.ScalableDimension != nil {
		res.SetScalableDimension(*r.ko.Spec.ScalableDimension)
	}
	if r.ko.Spec.ServiceNamespace != nil {
		res.SetServiceNamespace(*r.ko.Spec.ServiceNamespace)
	}
	if r.ko.Spec.SuspendedState != nil {
		f6 := &svcsdk.SuspendedState{}
		if r.ko.Spec.SuspendedState.DynamicScalingInSuspended != nil {
			f6.SetDynamicScalingInSuspended(*r.ko.Spec.SuspendedState.DynamicScalingInSuspended)
		}
		if r.ko.Spec.SuspendedState.DynamicScalingOutSuspended != nil {
			f6.SetDynamicScalingOutSuspended(*r.ko.Spec.SuspendedState.DynamicScalingOutSuspended)
		}
		if r.ko.Spec.SuspendedState.ScheduledScalingSuspended != nil {
			f6.SetScheduledScalingSuspended(*r.ko.Spec.SuspendedState.ScheduledScalingSuspended)
		}
		res.SetSuspendedState(f6)
	}

	return res, nil
}

// sdkUpdate patches the supplied resource in the backend AWS service API and
// returns a new resource with updated fields.
func (rm *resourceManager) sdkUpdate(
	ctx context.Context,
	desired *resource,
	latest *resource,
	delta *ackcompare.Delta,
) (*resource, error) {
	// TODO(jaypipes): Figure this out...
	return nil, ackerr.NotImplemented
}

// sdkDelete deletes the supplied resource in the backend AWS service API
func (rm *resourceManager) sdkDelete(
	ctx context.Context,
	r *resource,
) (latest *resource, err error) {
	rlog := ackrtlog.FromContext(ctx)
	exit := rlog.Trace("rm.sdkDelete")
	defer exit(err)
	input, err := rm.newDeleteRequestPayload(r)
	if err != nil {
		return nil, err
	}
	var resp *svcsdk.DeregisterScalableTargetOutput
	_ = resp
	resp, err = rm.sdkapi.DeregisterScalableTargetWithContext(ctx, input)
	rm.metrics.RecordAPICall("DELETE", "DeregisterScalableTarget", err)
	return nil, err
}

// newDeleteRequestPayload returns an SDK-specific struct for the HTTP request
// payload of the Delete API call for the resource
func (rm *resourceManager) newDeleteRequestPayload(
	r *resource,
) (*svcsdk.DeregisterScalableTargetInput, error) {
	res := &svcsdk.DeregisterScalableTargetInput{}

	if r.ko.Spec.ResourceID != nil {
		res.SetResourceId(*r.ko.Spec.ResourceID)
	}
	if r.ko.Spec.ScalableDimension != nil {
		res.SetScalableDimension(*r.ko.Spec.ScalableDimension)
	}
	if r.ko.Spec.ServiceNamespace != nil {
		res.SetServiceNamespace(*r.ko.Spec.ServiceNamespace)
	}

	return res, nil
}

// setStatusDefaults sets default properties into supplied custom resource
func (rm *resourceManager) setStatusDefaults(
	ko *svcapitypes.ScalableTarget,
) {
	if ko.Status.ACKResourceMetadata == nil {
		ko.Status.ACKResourceMetadata = &ackv1alpha1.ResourceMetadata{}
	}
	if ko.Status.ACKResourceMetadata.OwnerAccountID == nil {
		ko.Status.ACKResourceMetadata.OwnerAccountID = &rm.awsAccountID
	}
	if ko.Status.Conditions == nil {
		ko.Status.Conditions = []*ackv1alpha1.Condition{}
	}
}

// updateConditions returns updated resource, true; if conditions were updated
// else it returns nil, false
func (rm *resourceManager) updateConditions(
	r *resource,
	onSuccess bool,
	err error,
) (*resource, bool) {
	ko := r.ko.DeepCopy()
	rm.setStatusDefaults(ko)

	// Terminal condition
	var terminalCondition *ackv1alpha1.Condition = nil
	var recoverableCondition *ackv1alpha1.Condition = nil
	var syncCondition *ackv1alpha1.Condition = nil
	for _, condition := range ko.Status.Conditions {
		if condition.Type == ackv1alpha1.ConditionTypeTerminal {
			terminalCondition = condition
		}
		if condition.Type == ackv1alpha1.ConditionTypeRecoverable {
			recoverableCondition = condition
		}
		if condition.Type == ackv1alpha1.ConditionTypeResourceSynced {
			syncCondition = condition
		}
	}

	if rm.terminalAWSError(err) || err == ackerr.SecretTypeNotSupported || err == ackerr.SecretNotFound {
		if terminalCondition == nil {
			terminalCondition = &ackv1alpha1.Condition{
				Type: ackv1alpha1.ConditionTypeTerminal,
			}
			ko.Status.Conditions = append(ko.Status.Conditions, terminalCondition)
		}
		var errorMessage = ""
		if err == ackerr.SecretTypeNotSupported || err == ackerr.SecretNotFound {
			errorMessage = err.Error()
		} else {
			awsErr, _ := ackerr.AWSError(err)
			errorMessage = awsErr.Error()
		}
		terminalCondition.Status = corev1.ConditionTrue
		terminalCondition.Message = &errorMessage
	} else {
		// Clear the terminal condition if no longer present
		if terminalCondition != nil {
			terminalCondition.Status = corev1.ConditionFalse
			terminalCondition.Message = nil
		}
		// Handling Recoverable Conditions
		if err != nil {
			if recoverableCondition == nil {
				// Add a new Condition containing a non-terminal error
				recoverableCondition = &ackv1alpha1.Condition{
					Type: ackv1alpha1.ConditionTypeRecoverable,
				}
				ko.Status.Conditions = append(ko.Status.Conditions, recoverableCondition)
			}
			recoverableCondition.Status = corev1.ConditionTrue
			awsErr, _ := ackerr.AWSError(err)
			errorMessage := err.Error()
			if awsErr != nil {
				errorMessage = awsErr.Error()
			}
			recoverableCondition.Message = &errorMessage
		} else if recoverableCondition != nil {
			recoverableCondition.Status = corev1.ConditionFalse
			recoverableCondition.Message = nil
		}
	}
	// Required to avoid the "declared but not used" error in the default case
	_ = syncCondition
	if terminalCondition != nil || recoverableCondition != nil || syncCondition != nil {
		return &resource{ko}, true // updated
	}
	return nil, false // not updated
}

// terminalAWSError returns awserr, true; if the supplied error is an aws Error type
// and if the exception indicates that it is a Terminal exception
// 'Terminal' exception are specified in generator configuration
func (rm *resourceManager) terminalAWSError(err error) bool {
	// No terminal_errors specified for this resource in generator config
	return false
}
