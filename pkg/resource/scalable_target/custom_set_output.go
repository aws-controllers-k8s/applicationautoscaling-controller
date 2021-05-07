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

// import (
// 	"context"
// 	svcapitypes "github.com/aws-controllers-k8s/applicationautoscaling-controller/apis/v1alpha1"
// 	svcsdk "github.com/aws/aws-sdk-go/service/applicationautoscaling"
// )

// func (rm *resourceManager) CustomDescribeScalableTargetSetOutput(
// 	ctx context.Context,
// 	r *resource,
// 	resp *svcsdk.DescribeScalableTargetsOutput,
// 	ko *svcapitypes.ScalableTarget,
// ) (*svcapitypes.ScalableTarget, error) {
// 	if len(resp.ScalableTargets) == 0 {
// 		return ko, nil
// 	}
// 	ko := resp.ScalableTargets[0]

// 	return ko, nil
// }
