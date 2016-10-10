/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

WebMis20.controller('BaseChartCtrl', ['$scope', 'RisarApi', 'PrintingService', 'PrintingDialog', 'NotificationService', 'CurrentUser', 'RefBookService', 'ErrandModalService',
function ($scope, RisarApi, PrintingService, PrintingDialog, NotificationService, CurrentUser, RefBookService, ErrandModalService) {
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
    $scope.has_desease = function (has_diag) {
        if ($scope.chart) {
            if (has_diag) {
                return 'Положительно'
            } else if ($scope.chart.checkups.length) {
                return 'Отрицательно'
            }
        }
        return 'Нет данных'
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
        var errand = {
            event_id: $scope.chart.id,
            set_person: CurrentUser.info,
            communications: '',
            exec_person: $scope.chart.person,
            event: {external_id: $scope.chart.external_id},
            status: $scope.rbErrandStatus.get_by_code('waiting')
        };

        RisarApi.utils.get_person_contacts(errand.set_person.id).then(function (contacts) {
            errand.communications = contacts;
            ErrandModalService.openNew(errand, true)
                .then()
        });
    };
}
])
.controller('PregnancyChartCtrl', ['$scope', '$controller', '$window', 'RisarApi', 'Config', '$modal', 'NotificationService',
function ($scope, $controller, $window, RisarApi, Config, $modal, NotificationService) {
    $controller('BaseChartCtrl', {$scope: $scope});
    var params = aux.getQueryParams(window.location.search);
    var ticket_id = params.ticket_id;
    var client_id = params.client_id;
    var event_id = params.event_id;

    $scope.open_edit_epicrisis = function(e){
        var scope = $scope.$new();
        scope.model = e;
        $scope.minDate = $scope.header.event.set_date;
        return $modal.open({
            templateUrl: '/WebMis20/RISAR/modal/edit_epicrisis.html',
            scope: scope,
            resolve: {
                model: function () {return e}
            },
            size: 'lg'
        })
    };

    $scope.add_inspection = function() {
        $window.open(Config.url.inpection_edit_html + '?event_id=' + $scope.chart.id, '_self');
    };
    var load_header = function (event_id) {
        RisarApi.chart.get_header(event_id).then(function (data) {
            $scope.header = data.header;
        });
    };
    var reload_chart = function () {
        if (event_id) {
            load_header(event_id)
        }
        RisarApi.chart.get(
            event_id, ticket_id, client_id
        ).then(function (event) {
            $scope.chart = event;
            var mother_anamnesis = $scope.chart.anamnesis.mother;
            $scope.chart.bad_habits_mother = [{value:mother_anamnesis ? mother_anamnesis.alcohol: false, text: 'алкоголь'},
                {value:mother_anamnesis ? mother_anamnesis.smoking: false, text: 'курение'},
                {value:mother_anamnesis ? mother_anamnesis.toxic: false, text: 'токсичные вещества'},
                {value:mother_anamnesis ? mother_anamnesis.drugs: false,text: 'наркотики'}];
            //$scope.chart.bad_habits_father = [{value:$scope.chart.anamnesis.father.alcohol, text: 'алкоголь'},
            //    {value:$scope.chart.anamnesis.father.smoking, text: 'курение'},
            //    {value:$scope.chart.anamnesis.father.toxic, text: 'токсические вечества'},
            //    {value:$scope.chart.anamnesis.father.drugs,text: 'наркотики'}];

            if (ticket_id || client_id) {
                load_header($scope.chart.id)
            }
        });
    };

    $scope.close_event = function() {
        var model = _.extend({}, $scope.header.event);
        $scope.open_edit_epicrisis(model).result.then(function (rslt) {
            var result = rslt[0],
                edit_callback = function (data) {
                    $scope.close_event();
                },
                cancel_callback = function (data) {
                RisarApi.chart.close_event(
                    $scope.chart.id, {cancel: true}
                ).then(function(data) {
                    _.extend($scope.header.event, data);
                });
            };
            RisarApi.chart.close_event(
                $scope.chart.id, result, edit_callback, cancel_callback
            ).then(function (data) {
                _.extend($scope.header.event, data);
            });
        })
    };
    reload_chart();
}])
.controller('GynecologicalChartCtrl', ['$scope', '$controller', '$window', 'RisarApi', 'Config', '$modal',
function ($scope, $controller, $window, RisarApi, Config, $modal) {
    $controller('BaseChartCtrl', {$scope: $scope});
    var params = aux.getQueryParams(window.location.search);
    var ticket_id = params.ticket_id;
    var client_id = params.client_id;
    var event_id = params.event_id;

    $scope.open_edit_epicrisis = function(e){
        var scope = $scope.$new();
        scope.model = e;
        $scope.minDate = $scope.header.event.set_date;
        return $modal.open({
            templateUrl: '/WebMis20/RISAR/modal/edit_epicrisis.html',
            scope: scope,
            resolve: {
                model: function () {return e}
            },
            size: 'lg'
        })
    };

    $scope.add_inspection = function() {
        $window.open(Config.url.inpection_edit_html + '?event_id=' + $scope.chart.id, '_self');
    };
    
    var load_header = function (event_id) {
        RisarApi.gynecologic_chart.get_header(event_id).then(function (data) {
            $scope.header = data.header;
        });
    };
    var reload_chart = function () {
        if (event_id) {
            load_header(event_id)
        }
        RisarApi.gynecologic_chart.get(
            event_id, ticket_id, client_id
        ).then(function (event) {
            $scope.chart = event;
            var general_anamnesis = event.anamnesis.general;
            $scope.chart.bad_habits = [
                {value:general_anamnesis ? general_anamnesis.alcohol: false, text: 'алкоголь'},
                {value:general_anamnesis ? general_anamnesis.smoking: false, text: 'курение'},
                {value:general_anamnesis ? general_anamnesis.toxic: false, text: 'токсичные вещества'},
                {value:general_anamnesis ? general_anamnesis.drugs: false,text: 'наркотики'}
            ];
            if (ticket_id || client_id) {
                load_header($scope.chart.id)
            }
        });
    };

     $scope.close_event = function() {
        var model = _.extend({}, $scope.header.event);
        $scope.open_edit_epicrisis(model).result.then(function (rslt) {
            var result = rslt[0],
                edit_callback = function (data) {
                    $scope.close_event();
                },
                cancel_callback = function (data) {
                RisarApi.gynecologic_chart.cl1ose_event(
                    $scope.chart.id, {cancel: true}
                ).then(function(data) {
                    _.extend($scope.header.event, data);
                });
            };
            RisarApi.gynecologic_chart.close_event(
                $scope.chart.id, result, edit_callback, cancel_callback
            ).then(function (data) {
                _.extend($scope.header.event, data);
            });
        })
    };


    $scope.ps.set_context("risar_gyn");

    reload_chart();
}])
.controller('InspectionViewCtrl', ['$scope', '$modal', 'RisarApi', 'PrintingService', 'PrintingDialog', 'RefBookService',
function ($scope, $modal, RisarApi, PrintingService, PrintingDialog, RefBookService) {
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
    $scope.print_checkup_ticket = function (checkup, fmt) {
        // Вы потом не разберётесь, откуда у этого говна ноги растут. Простите. Я не хотел
        var ticket_id = checkup.ticket_25.id;
        RisarApi.print_ticket_25(ticket_id, fmt);
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
}])
.controller('InspectionGynViewCtrl', ['$scope', '$modal', 'RisarApi', 'PrintingService', 'PrintingDialog', 'RefBookService',
    function ($scope, $modal, RisarApi, PrintingService, PrintingDialog, RefBookService) {
        // Поскольку времени на то, чтобы с этим разбираться нет от слова "совсем", делаем тупую копипасту.
        // В будущем наши потомки, проклиная нас, буду разбирать этот код...
        // Но нам плевать. У нас проект горит.
        // Синем пламенем.
        // Пусть горит.
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

        $scope.print_checkup_ticket = function (checkup, fmt) {
            // Вы потом не разберётесь, откуда у этого говна ноги растут. Простите. Я не хотел
            var ticket_id = checkup.ticket_25.id;
            RisarApi.print_ticket_25(ticket_id, fmt);
        };

        $scope.declOfNum = function (number, titles) {
            var cases = [2, 0, 1, 1, 1, 2];
            return titles[ (number%100>4 && number%100<20)? 2 : cases[(number%10<5)?number%10:5] ];
        };

        var reload = function () {
            RisarApi.gynecologic_chart.get_header(event_id).then(
                function (data) {
                    $scope.header = data.header;
                });
            RisarApi.checkup_gyn.get_list(event_id)
                .then(function (data) {
                    $scope.checkups = data.checkups;
                });
        };

        $scope.open_print_window = function (ps, checkup_id) {
            if ($scope.ps.is_available()){
                PrintingDialog.open(ps, $scope.ps_resolve(checkup_id));
            }
        };
        reload();
    }])
.controller('InspectionFetusViewCtrl', ['$scope', '$modal', 'RisarApi', function ($scope, $modal, RisarApi) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = params.event_id;
    $scope.checkup = {};

    var reload = function () {
        RisarApi.chart.get_header(event_id).
            then(function (data) {
                $scope.header = data.header;
            });
        RisarApi.fetus.get_fetus_list(event_id)
            .then(function (checkup) {
                $scope.checkup = checkup;
            });
    };

    reload();
}])
;
