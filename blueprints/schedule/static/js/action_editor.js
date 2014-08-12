/**
 * Created by mmalkov on 14.07.14.
 */
var ActionEditorCtrl = function ($scope, $http, $window, WMAction, PrintingService, RefBookService) {
    var params = aux.getQueryParams(location.search);
    $scope.ps = new PrintingService("action");
    $scope.ps_resolve = function () {
        return {
            action_id: $scope.action.id
        }
    };
    $scope.action_id = params.action_id;
    $scope.action = new WMAction();
    if (params.action_id) {
        $scope.action.get(params.action_id).success(update_print_templates);
    } else if (params.event_id && params.action_type_id) {
        $scope.action.get_new(params.event_id, params.action_type_id).success(update_print_templates);
    }
    function update_print_templates (data) {
        $scope.ps.set_context(data.result.action.action_type.context_name)
    }
    $scope.ActionStatus = RefBookService.get('ActionStatus');
};
WebMis20.controller('ActionEditorCtrl', ['$scope', '$http', '$window', 'WMAction', 'PrintingService', 'RefBookService', ActionEditorCtrl]);
