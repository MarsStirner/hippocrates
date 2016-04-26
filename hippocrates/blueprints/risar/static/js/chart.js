/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var ChartCtrl = function ($scope, $modal, $window, RisarApi, PrintingService, PrintingDialog, NotificationService, CurrentUser,
                          UserErrand, RefBookService, Config) {
    var params = aux.getQueryParams(window.location.search);
    var ticket_id = params.ticket_id;
    var client_id = params.client_id;
    var event_id = params.event_id;

    $scope.rbErrandStatus = RefBookService.get('ErrandStatus');
    $scope.ps_talon = new PrintingService("risar");
    $scope.ps_talon.set_context("risar_talon");
    $scope.ps_resolve = function () {
        return {
            event_id: $scope.chart.id
        }
    };
    $scope.ps = new PrintingService("risar");
    $scope.ps.set_context("risar");
    $scope.has_desease = function(has_diag){
        if ($scope.chart){
            if (has_diag){
                return 'Положительно'
            } else if ($scope.chart.checkups.length){
                return 'Отрицательно'
            }
        }
        return 'Нет данных'
    };

    var reload_chart = function () {
        if (event_id) {
            RisarApi.chart.get_header(event_id).
                then(function (data) {
                    $scope.header = data.header;
                });
        }
        RisarApi.chart.get(event_id, ticket_id, client_id)
            .then(function (event) {
                $scope.chart = event;
                var mother_anamnesis = $scope.chart.anamnesis.mother;
                $scope.chart.bad_habits_mother = [{value:mother_anamnesis ? mother_anamnesis.alcohol: false, text: 'алкоголь'},
                    {value:mother_anamnesis ? mother_anamnesis.smoking: false, text: 'курение'},
                    {value:mother_anamnesis ? mother_anamnesis.toxic: false, text: 'токсические вечества'},
                    {value:mother_anamnesis ? mother_anamnesis.drugs: false,text: 'наркотики'}];
                //$scope.chart.bad_habits_father = [{value:$scope.chart.anamnesis.father.alcohol, text: 'алкоголь'},
                //    {value:$scope.chart.anamnesis.father.smoking, text: 'курение'},
                //    {value:$scope.chart.anamnesis.father.toxic, text: 'токсические вечества'},
                //    {value:$scope.chart.anamnesis.father.drugs,text: 'наркотики'}];

                if (ticket_id || client_id) {
                    RisarApi.chart.get_header($scope.chart.id).
                        then(function (data) {
                            $scope.header = data.header;
                        });
                }
            });
    };

    $scope.$on('printing_error', function (event, error) {
        NotificationService.notify(
                        error.code,
                        error.text,
                        'error',
                        5000
                    );
    });

    $scope.open_print_window = function () {
        if ($scope.ps.is_available()) {
            PrintingDialog.open($scope.ps, $scope.$parent.$eval($scope.ps_resolve));
        }
    };
    $scope.create_errand = function () {
        var model = {
            set_person: CurrentUser.info,
            exec_person: $scope.chart.person,
            is_author: true,
            event: {external_id: $scope.chart.external_id},
            status: $scope.rbErrandStatus.get_by_code('waiting')
        };
        open_edit_errand(model).result.then(function (rslt) {
            var result = rslt[0],
                restart = rslt[1];
            UserErrand.create_errand(result.exec_person, result.text, $scope.chart.id, result.status, result.planned_exec_date);
        })
    };
    $scope.add_inspection = function() {
        $window.open(Config.url.inpection_edit_html + '?event_id=' + $scope.chart.id, '_self');
    };
    var open_edit_errand = function(e){
        var scope = $scope.$new();
        scope.model = e;
        return $modal.open({
            templateUrl: '/WebMis20/RISAR/modal/create_errand.html',
            scope: scope,
            resolve: {
                model: function () {return e}
            },
            size: 'lg'
        })
    };
    $scope.close_event = function() {
        var model = {};
        open_edit_epicrisis(model).result.then(function (rslt) {
            var result = rslt[0];
            RisarApi.chart.close_event($scope.chart.id, result).then(function (data) {
                _.extend($scope.header.event, data);
                NotificationService.notify(
                    200,
                    [
                        'Случай беременности закрыт',
                        {
                            bold: false,
                            text: ''
                        }, '. ',
                        {
                            click: function () {
                                $scope.close_event();
                            },
                            text: 'Изменить'
                        }, ' ',
                        {
                            click: function () {
                                RisarApi.chart.close_event($scope.chart.id, {cancel: true}).then(function(data){
                                    _.extend($scope.header.event, data);
                                });
                            },
                            text: 'Отменить'
                        }
                    ],
                    'success'
                );
            });
        })
    };
    var open_edit_epicrisis = function(e){
        var scope = $scope.$new();
        scope.model = e;
        return $modal.open({
            templateUrl: '/WebMis20/RISAR/modal/edit_epicrisis.html',
            scope: scope,
            resolve: {
                model: function () {return e}
            },
            size: 'lg'
        })
    };
    reload_chart();
};

var InspectionViewCtrl = function ($scope, $modal, RisarApi, PrintingService, PrintingDialog, RefBookService) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = params.event_id;
    $scope.rbRisarComplaints = RefBookService.get('rbRisarComplaints');
    $scope.ps = new PrintingService("risar");
    $scope.ps.set_context("risar");

    $scope.ps_fi = new PrintingService("risar_inspection");
    $scope.ps_fi.set_context("risar_osm1_talon");
    $scope.ps_si = new PrintingService("risar_inspection");
    $scope.ps_si.set_context("risar_osm2_talon");
    $scope.ps_resolve = function (checkup_id) {
        return {
            event_id: $scope.header.event.id,
            action_id: checkup_id
        }
    };

    $scope.declOfNum = function (number, titles) {
        var cases = [2, 0, 1, 1, 1, 2];
        return titles[ (number%100>4 && number%100<20)? 2 : cases[(number%10<5)?number%10:5] ];
    };

    var reload = function () {
        RisarApi.chart.get_header(event_id).
            then(function (data) {
                $scope.header = data.header;
            });
        RisarApi.checkup.get_list(event_id)
            .then(function (data) {
                $scope.checkups = data.checkups;

                // calculate mass gain
                $scope.first_checkup = $scope.checkups.length ? $scope.checkups[0] : null;
                function get_mass_gain(prev, curr, i){
                    if (i === 0) {
                        curr.weight_gain = [0, 0];
                    }
                    var num_days = moment(curr.beg_date).diff(moment(prev.beg_date), 'days');
                    curr.weight_gain = prev.weight ? [curr.weight - prev.weight, num_days ] : [0, num_days];
                    return curr
                }
                $scope.checkups.reduce(get_mass_gain, [{}]);

                // проверяем были жалобы на отеки
                var edema = $scope.rbRisarComplaints.get_by_code("oteki");
                $scope.checkups.map(function(checkup){
                    checkup.if_edema = (checkup.complaints && indexOf(checkup.complaints, edema)>=0) ? 'Да' : 'Нет'
                })
            });
    };

    $scope.open_print_window = function (ps, checkup_id) {
        if (ps.is_available()){
            PrintingDialog.open(ps, $scope.ps_resolve(checkup_id));
        }
    };
    reload();
};

var InspectionFetusViewCtrl = function ($scope, $modal, RisarApi) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = params.event_id;

    var reload = function () {
        RisarApi.chart.get_header(event_id).
            then(function (data) {
                $scope.header = data.header;
            });
        RisarApi.fetus.get_fetus_list(event_id)
            .then(function (data) {
                $scope.checkup = data;
            });
    };

    reload();
};

WebMis20.controller('ChartCtrl', ['$scope', '$modal', '$window', 'RisarApi', 'PrintingService', 'PrintingDialog',
    'NotificationService', 'CurrentUser', 'UserErrand', 'RefBookService', 'Config', ChartCtrl]);
WebMis20.controller('InspectionViewCtrl', ['$scope', '$modal', 'RisarApi', 'PrintingService', 'PrintingDialog',
    'RefBookService', InspectionViewCtrl]);
WebMis20.controller('InspectionFetusViewCtrl', ['$scope', '$modal', 'RisarApi', InspectionFetusViewCtrl]);
