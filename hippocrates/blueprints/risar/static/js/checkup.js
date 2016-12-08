
'use strict';

WebMis20.controller('CheckupCtrl', ['$scope', '$timeout', 'RisarApi', 'RefBookService', 'PrintingService', 'PrintingDialog',
function ($scope, $timeout, RisarApi, RefBookService, PrintingService, PrintingDialog) {
    $scope.rbDiagnosisType = RefBookService.get('rbDiagnosisType');
    $scope.ps = new PrintingService("risar");
    $scope.ps.set_context("risar");
    $scope.ps_talon = new PrintingService("risar");
    $scope.ps_talon.set_context("risar_talon");
    $scope.ps_inspections = new PrintingService("risar_inspections");
    $scope.ps_resolve = function () {
        return {
            event_id: $scope.header.event.id
        }
    };
    $scope.currentDate = new Date();
    $scope.minDate = new Date();
    $scope.inFiveDate = moment().add(5, 'y').toDate();
    $scope.clientBd = new Date();

    $scope.ps_fi = new PrintingService("risar_inspection");
    $scope.ps_fi.set_context("risar_first_inspection");
    $scope.ps_si = new PrintingService("risar_inspection");
    $scope.ps_si.set_context("risar_second_inspection");
    $scope.ps_resolve_inspection = function () {
        return {
            event_id: $scope.header.event.id,
            action_id: $scope.checkup_id
        }
    };
    $scope.add_child = function (){
        $scope.checkup.fetuses.push({
            id: null,
            alive: true,
            deleted: 0
        });
        $timeout(function(){
            $('#childrenTabs').find('a:last').tab('show');
        }, 0);

    };
    $scope.delete_child = function(child){
        child.deleted = 1;
        $timeout(function(){
            // Использовать в контроллере jQuery - абсурд, но мне некогда с этим разбираться
            $('#childrenTabs li.active').removeClass('active');
            $('#childrenTabs').find('a:first').tab('show');
        }, 0);
    };

    $scope.init = function () {
        var hash = document.location.hash;
        if (hash) {
            hash = hash.replace(/\//, '').replace("tab_","");
            // Использовать в контроллере jQuery - абсурд, но мне некогда с этим разбираться
            $('.nav-pills a[href={0}]'.format(hash)).tab('show');
        }
    };

    $scope.open_print_window = function () {
        if ($scope.ps.is_available()) {
            PrintingDialog.open($scope.ps, $scope.$parent.$eval($scope.ps_resolve));
        }
    };
    $scope.$watch('checkup.pregnancy_continuation', function (newVal) {
        if (newVal) {  // если "Да", то очистить
            $scope.checkup.pregnancy_continuation_refusal = null;
        }
    });
    $scope.pregContRefusalDisabled = function () {
        if (!$scope.checkup) return true;
        return Boolean($scope.checkup.pregnancy_continuation === null || $scope.checkup.pregnancy_continuation);  // задизейблено при "Да"
    };
    $scope.pregContRefusalRequired = function () {
        if (!$scope.checkup) return false;
        return !Boolean($scope.checkup.pregnancy_continuation);  // требуется при "Нет"
    };
    $scope.print_checkup_ticket = function () {
        var ticket_id = $scope.checkup.ticket_25.id;
        RisarApi.print_ticket_25(ticket_id, 'pdf');
    };
    $scope.begDateIsSameNextDate = false;
    $scope.begDateIsAfterNextDate = false;
    $scope.$watch('checkup.next_date', function (n, o) {
        if (n!==o && $scope.checkup) {
            var beg_date = moment($scope.checkup.beg_date).startOf('day');
            var next_date = moment(n).startOf('day');
            $scope.begDateIsAfterNextDate = beg_date.isAfter(next_date);
            $scope.begDateIsSameNextDate = beg_date.isSame(next_date);
        }
    });
    $scope.$watch('checkup.beg_date', function (n, o) {
        if (n!==o && $scope.checkup.ticket_25) {
            var beg_date = moment(n).startOf('day');
            var next_date = moment($scope.checkup.next_date).startOf('day');
            $scope.checkup.ticket_25.beg_date = beg_date.toDate();
            $scope.checkup.ticket_25.end_date = beg_date.toDate();
            $scope.begDateIsAfterNextDate = beg_date.isAfter(next_date);
            $scope.begDateIsSameNextDate = next_date.isSame(beg_date);
        }
    });
}])
;


WebMis20.controller('CheckupTicket25Ctrl', ['$scope', function ($scope) {
    $scope.init = function (rc_step) {
        $scope.thisRcStep = rc_step;
    };
}])
;