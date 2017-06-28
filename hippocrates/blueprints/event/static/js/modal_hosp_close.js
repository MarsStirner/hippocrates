'use strict';

var HospCloseModalCtrl = function ($scope, RefBookService, WMEventService, PrintingService,
        wmevent) {
    $scope.event = wmevent;

    $scope.ps = new PrintingService('event');
    $scope.OrgStructure = RefBookService.get('OrgStructure');

    $scope.filter_rb_result = function (event_purpose) {
        return function(elem) {
            return elem.eventPurpose_id == event_purpose;
        };
    };
    $scope.isContractDraft = function () {
        return !!safe_traverse($scope, ['event', 'info', 'contract', 'draft']);
    };
    $scope.isContractDraftLabelVisible = function () {
        return $scope.isContractDraft();
    };
    $scope.leavedAvailable = function () {
        return Boolean($scope.event.leaved);
    };
    $scope.deathEpicrisisAvailable = function () {
        return Boolean($scope.event.death_epicrisis);
    };
    $scope.operationPropertyAvailable = function () {
    };

    $scope.saveHospClose = function () {
        return WMEventService.save_hosp_to_close($scope.event);
    };
    $scope.saveAndClose = function () {
        $scope.saveHospClose()
            .then(function (data) {
                $scope.$close();
            });
    };
    $scope.init = function () {
        if (!$scope.event.info.exec_date) {
            $scope.event.info.exec_date = new Date();
        }
    };

    $scope.init();
};


WebMis20.controller('HospCloseModalCtrl', ['$scope', 'RefBookService', 'WMEventService',
    'PrintingService', HospCloseModalCtrl]);
WebMis20.directive('nonEmptyEditable', ['$compile', function ($compile) {
    return {
        restrict: 'A',
        priority: 50000,
        terminal: true,
        compile: function compile (tElement, tAttrs, transclude) {
            tElement.removeAttr('non-empty-editable');
            tElement.removeAttr('data-non-empty-editable');

            return {
                pre: function preLink(scope, iElement, iAttrs, controller) {},
                post: function postLink(scope, iElement, iAttrs, controller) {
                    var ngModel = scope.$eval(iAttrs.ngModel);
                    var ngDisabled = iAttrs.ngDisabled;
                    // custom disable flag
                    var _disable = true;
                    scope.disableIfInitialValIsEmpty = function () {
                        return _disable;
                    };

                    // append custom ng-disabled
                    if (ngDisabled) ngDisabled += ' && disableIfInitialValIsEmpty()';
                    else ngDisabled = 'disableIfInitialValIsEmpty()';
                    iAttrs.$set('ngDisabled', ngDisabled);

                    // read initial value from ng-model
                    if (ngModel) {
                        var unwatch = scope.$watch(ngModel, function (n) {
                            _disable = (n === null || n === undefined);
                            unwatch();
                        });
                    }

                    $compile(iElement)(scope);
                }
            }
        }
    }
}]);
