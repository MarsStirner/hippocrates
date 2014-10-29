/**
 * Created by mmalkov on 14.07.14.
 */
var ActionEditorCtrl = function ($scope, $http, $window, WMAction, PrintingService, RefBookService) {
    var params = aux.getQueryParams(location.search);
    $scope.ps = new PrintingService("action");
    $scope.ps_resolve = function () {
        return {
            action_id: $scope.action.action.id
        }
    };
    $scope.ActionStatus = RefBookService.get('ActionStatus');
    $scope.action_id = params.action_id;
    var action = $scope.action = new WMAction();
    if (params.action_id) {
        $scope.action.get(params.action_id).success(update_print_templates);
    } else if (params.event_id && params.action_type_id) {
        $scope.action.get_new(params.event_id, params.action_type_id).success(update_print_templates);
    }
    function update_print_templates (data) {
        $scope.ps.set_context(data.result.action.action_type.context_name)
    }

    $scope.on_status_changed = function () {
        if (action.action.status.code === 'finished') {
            if (!action.action.end_date) {
                action.action.end_date = new Date();
            }
        } else {
            action.action.end_date = null;
        }
    };
    $scope.on_enddate_changed = function () {
        if (action.action.end_date) {
            if (action.action.status.code !== 'finished') {
                action.action.status = $scope.ActionStatus.get_by_code('finished');
            }
        } else {
            action.action.status = $scope.ActionStatus.get_by_code('started');
        }
    };

    $scope.save_action = function () {
        $scope.action.save().
            then(function (result) {
                if ($scope.action.is_new()) {
                    $window.open(url_for_schedule_html_action + '?action_id=' + result.action.id, '_self');
                } else {
                    $scope.action.get(result.action.id);
                }
            });
    };
    $scope.is_med_doc = function () { return $scope.action.action.action_type && $scope.action.action.action_type.class === 0; };
    $scope.is_diag_lab = function () { return $scope.action.action.action_type && $scope.action.action.action_type.class === 1; };
    $scope.is_treatment = function () { return $scope.action.action.action_type && $scope.action.action.action_type.class === 2; };
};
WebMis20.controller('ActionEditorCtrl', ['$scope', '$http', '$window', 'WMAction', 'PrintingService', 'RefBookService', ActionEditorCtrl]);
