'use strict';

var ScheduleDayCtrl = function ($scope, RisarApi, CurrentUser, WMAppointmentDialog) {
    $scope.curation_level_code = $scope.curation_level.code; // from parent ctrl
    $scope.scheds = [];
    $scope.search_date = {date:new Date()};

    $scope.refresh_data = function (date) {
        RisarApi.schedule.get_day(CurrentUser.id, date)
            .then(function (scheds) {
                $scope.scheds = scheds;
            })
    };

    $scope.isEmpty = function (ticket) {
        return !ticket.client_id;
    };
    $scope.isBusy = function (ticket) {
        return ticket.client_id;
    };
    $scope.make_appointment = function (ticket) {
        return WMAppointmentDialog.make(ticket, CurrentUser.info).result
            .then(function() {
                $scope.refresh_data($scope.search_date.date);
            });
    };
    $scope.init = function () {
    };

    $scope.init();
    $scope.$watch('search_date.date', $scope.refresh_data);
};


WebMis20.controller('ScheduleDayCtrl', ['$scope', 'RisarApi', 'CurrentUser', 'WMAppointmentDialog',
    ScheduleDayCtrl]);