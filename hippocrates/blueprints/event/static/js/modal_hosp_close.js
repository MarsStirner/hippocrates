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
