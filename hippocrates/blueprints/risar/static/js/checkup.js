
'use strict';

WebMis20.controller('CheckupCtrl', ['$scope', '$timeout', 'RisarApi', 'RefBookService', 'PrintingService', 'PrintingDialog',
    'PropsDescriptor', 'checkup_descriptor', 'ticket_25_descriptor',
function ($scope, $timeout, RisarApi, RefBookService, PrintingService, PrintingDialog, PropsDescriptor, checkup_descriptor,
          ticket_25_descriptor) {
    $scope.checkupDescriptor = new PropsDescriptor(checkup_descriptor);
    $scope.ticket25Descriptor = new PropsDescriptor(ticket_25_descriptor);
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
    $scope.header = null;
    $scope.checkup = null;
    $scope.checkupAccess = null;

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
    $scope.canEditCheckup = function () {
        return $scope.checkupAccess && $scope.checkupAccess.can_edit;
    };
    $scope.isDisabledVisitType = function () {
        return $scope.checkup && $scope.checkup.ticket_25 && _.isEmpty($scope.checkup.ticket_25.visit_reason);
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

    // initialization
    $scope.init = function () {
        var hash = document.location.hash;
        if (hash) {
            hash = hash.replace(/\//, '').replace("tab_","");
            // Использовать в контроллере jQuery - абсурд, но мне некогда с этим разбираться
            $('.nav-pills a[href={0}]'.format(hash)).tab('show');
        }
    };

    var params = aux.getQueryParams(window.location.search);
    var checkup_id = $scope.checkup_id = params.checkup_id;
    var event_id = $scope.event_id = params.event_id;

    $scope.setCheckupData = function (data) {
        $scope.checkup = data.checkup;
        $scope.checkupAccess = data.access;
    };
    $scope.getHeader = function () {
        return RisarApi.chart.get_header(event_id)
            .then(function (data) {
                $scope.header = data.header;
                $scope.minDate = $scope.header.event.set_date;
                return data;
            });
    };
    $scope.getCheckup = function (flat_code) {
        if (!checkup_id) {
            RisarApi.checkup.create(event_id, flat_code)
                .then(function (data) {
                    $scope.setCheckupData(data);
                    if(!$scope.checkup.fetuses.length) {
                        $scope.add_child();
                    }
                    $scope.$broadcast('checkupLoaded');
                    return data;
                });
        } else {
            RisarApi.checkup.get(checkup_id)
                .then(function (data) {
                    $scope.setCheckupData(data);
                    if(!$scope.checkup.fetuses.length) {
                        $scope.add_child();
                    }
                    $scope.$broadcast('checkupLoaded');
                    return data;
                });
        }
    };

}])
;


WebMis20.controller('CheckupTicket25Ctrl', ['$scope', 'CurrentUser', 'PropsDescriptor', 'ticket_25_descriptor',
function ($scope, CurrentUser, PropsDescriptor, ticket_25_descriptor) {
    $scope.ticket25Descriptor = new PropsDescriptor(ticket_25_descriptor);
    $scope.get_current_user = function () {
        return { person: CurrentUser.info };
    };
    $scope.get_default_values = function () {
        var result = {
            person: CurrentUser.info,
            amount: 1
        };
        if ($scope.checkup && $scope.checkup._service) {
            result['service'] = $scope.checkup._service;
        }
        return result;
    };
    $scope.orgStructFilter = function (item) {
        return item.org_id === safe_traverse($scope.header, ['event', 'person', 'organisation', 'id']);
    };
    $scope.init = function (rc_step) {
        $scope.thisRcStep = rc_step;
    };
}])
;