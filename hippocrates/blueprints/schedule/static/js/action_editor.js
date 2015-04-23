/**
 * Created by mmalkov on 14.07.14.
 */
var ActionEditorCtrl = function ($scope, $window, WMAction, PrintingService, PrintingDialog, RefBookService,
        WMEventCache, $q, MessageBox, NotificationService) {
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
        $scope.action.get(params.action_id).success(function (data) {
            update_print_templates(data);
            process_printing();
            WMEventCache.get($scope.action.action.event_id).then(function (event) {
                $scope.event = event;
            });
        });
    } else if (params.event_id && params.action_type_id) {
        $scope.action.get_new(
            params.event_id,
            params.action_type_id
        ).success(function (data) {
            update_print_templates(data);
        });
        WMEventCache.get(parseInt(params.event_id)).then(function (event) {
            $scope.event = event;
        });
    }

    function update_print_templates (data) {
        $scope.ps.set_context(data.result.action.action_type.context_name);
    }
    function process_printing() {
        if ($window.sessionStorage.getItem('open_action_print_dlg')) {
            $window.sessionStorage.removeItem('open_action_print_dlg');
            PrintingDialog.open($scope.ps, $scope.ps_resolve());
        }
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

    $scope.save_action = function (need_to_print) {
        return $scope.check_can_save_action()
        .then(function () {
            if ($scope.action.is_new() && need_to_print) {
                $window.sessionStorage.setItem('open_action_print_dlg', true);
            }
            return $scope.action.save().
                then(function (result) {
                    if ($scope.action.is_new()) {
                        $window.open(url_for_schedule_html_action + '?action_id=' + result.action.id, '_self');
                    } else {
                        NotificationService.notify(
                            200,
                            'Успешно сохранено',
                            'success',
                            5000
                        );
                        $scope.action.get(result.action.id);
                    }
                }, function (result) {
                    NotificationService.notify(
                        500,
                        'Ошибка сохранения, свяжитесь с администратором',
                        'danger'
                    );
                });
        }, function (result) {
            var deferred = $q.defer();
            if (need_to_print) {
                if (!result.silent) {
                    MessageBox.info('Невозможно сохранить действие', result.message)
                    .then(function () {
                        deferred.resolve();
                    });
                } else {
                    deferred.resolve();
                }
            } else {
                return MessageBox.error('Невозможно сохранить действие', result.message);
            }
            return deferred.promise;
        });
    };
    $scope.check_can_save_action = function () {
        function check_diagnoses_conflicts(event, action) {
            var deferred = $q.defer();
            var self_diagnoses = action.action.properties.map(function (prop) {
                    return prop.type.type_name === 'Diagnosis' ? prop.value : undefined;
                }).reduce(function (diag_list, cur_elem) {
                    if (cur_elem !== undefined && cur_elem !== null) {
                        if (cur_elem instanceof Array) {
                            diag_list = diag_list.concat(cur_elem);
                        } else {
                            diag_list.push(cur_elem);
                        }
                    }
                    return diag_list;
                }, []).filter(function (diag) {
                    return diag.deleted === 0;
                }),
                fin_diagnoses = self_diagnoses.filter(function (diag) {
                    return diag.diagnosis_type.code === '1';
                }),
                event_has_closed_fin_diagnoses = event.diagnoses.some(function (diag) {
                    var diag_action_id = safe_traverse(diag, ['action', 'id']);
                    return (
                        // рассматриваем только другие действия в обращении,
                        // считаем, что без id может быть только текущее действие
                        diag_action_id && diag_action_id !== action.action.id &&
                        diag.diagnosis_type.code === '1' &&
                        safe_traverse(diag, ['action', 'status', 'code']) === 'finished');
                });
            if (action.action.status.code === 'finished' && fin_diagnoses.length && event_has_closed_fin_diagnoses) {
                deferred.reject({
                    silent: false,
                    message: 'В обращении уже есть закрытые осмотры с заключительным дагнозом. ' +
                        'Нельзя указывать больше одного заключительного диагноза в обращении.'
                });
            }
            deferred.resolve();
            return deferred.promise;
        }

        var deferred = $q.defer();
        if (action.ro) {
            deferred.reject({
                silent: true,
                message: 'Действие открыто в режиме чтения'
            });
        } else {
            return check_diagnoses_conflicts($scope.event, $scope.action);
        }
        return deferred.promise;
    };
    $scope.is_med_doc = function () { return $scope.action.action.action_type && $scope.action.action.action_type.class === 0; };
    $scope.is_diag_lab = function () { return $scope.action.action.action_type && $scope.action.action.action_type.class === 1; };
    $scope.is_treatment = function () { return $scope.action.action.action_type && $scope.action.action.action_type.class === 2; };
};
WebMis20.controller('ActionEditorCtrl', ['$scope', '$window', 'WMAction', 'PrintingService', 'PrintingDialog',
    'RefBookService', 'WMEventCache', '$q', 'MessageBox', 'NotificationService', ActionEditorCtrl]);
