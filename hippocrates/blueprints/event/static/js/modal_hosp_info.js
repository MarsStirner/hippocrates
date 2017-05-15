'use strict';

var EventHospInfoModalCtrl = function ($scope, PrintingService, CurrentUser, wmevent) {
    $scope.event = wmevent;
    $scope.alerts = [];

    $scope.ps = new PrintingService('event');
    $scope.ps_resolve = function () {
        return {
            event_id: $scope.event.event_id
        }
    };
    $scope.$on('printing_error', function (event, error) {
        $scope.alerts.push(error);
    });
    $scope.getEventPrintContext = function () {
        return $scope.event.info.event_type.print_context;
    };

};


WebMis20.controller('EventHospInfoModalCtrl', ['$scope', 'PrintingService', 'CurrentUser',
    EventHospInfoModalCtrl]);
