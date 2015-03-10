'use strict';

angular.module('WebMis20.services', []).
    service('WMAppointment', ['$http', function ($http) {
        return {
            make: function (ticket, client_id, appointment_type_id, associated_event_id) {
                return $http.post(url_schedule_api_appointment, {
                    client_id: client_id,
                    ticket_id: ticket.id,
                    appointment_type_id: appointment_type_id,
                    event_id: associated_event_id
                });
            },
            cancel: function (ticket, client_id) {
                return $http.post(url_schedule_api_appointment, {
                    client_id: client_id,
                    ticket_id: ticket.id,
                    delete: true
                });
            },
            change_notes: function (ticket_client_id, notes) {
                return $http.post(url_schedule_api_appointment, {
                    client_id: client_id,
                    ticket_id: ticket.id,
                    note: notes
                });
            }
        }
    }]).
    service('AgeSex', [function() {
        return {
            sex_acceptable: function (client, sex) {
                return ! (sex && sex !== client.sex_raw);
            },
            age_acceptable: function (client, selector) {
                return ! (
                    selector[0] != 0 && client.age_tuple[selector[0] - 1] < selector[1] ||
                    selector[2] != 0 && client.age_tuple[selector[2] - 1] > selector[3]
                );
            }
        }
    }]).
    service('WMWindowSync', ['$window', '$rootScope', '$interval', function ($window, $rootScope, $interval) {
        return {
            openTab: function (url, onCloseCallback) {
                var interval,
                    clearInterval = function() {
                        $interval.cancel(interval);
                        interval = undefined;
                    };
                var w = $window.open(url);
                interval = $interval(function () {
                    if (w.closed) {
                        (onCloseCallback || angular.noop)();
                        clearInterval();
                        w = undefined;
                    }
                }, 500);
            }
        }
    }]).
    service('CurrentUser', [function () {
        // пока инициализация через глобального юзера, а потом через rest
        angular.extend(this, current_user);
        this.get_main_user = function () {
            return this.master || this;
        };
        this.has_right = function () {
            return [].clone.call(arguments).filter(aux.func_in(this.get_user().rights)).length > 0;
        };
        this.has_role = function () {
            return [].clone.call(arguments).filter(aux.func_in(this.roles)).length > 0;
        };
        this.current_role_in = function () {
            return [].clone.call(arguments).has(this.current_role);
        };
    }]).
    service('IdleTimer', ['$http', '$log', '$document', '$window', 'TimeoutCallback', 'WMConfig', 'IdleUserModal',
            function ($http, $log, $document, $window, TimeoutCallback, WMConfig, IdleUserModal) {
        var last_ping_time = null,
            last_activity_time = null,
            token_expire_time = null,
            ping_timeout = get_ping_timeout(),
            user_activity_events = 'mousemove keydown DOMMouseScroll mousewheel mousedown touchstart touchmove scroll',
            ping_timer = new TimeoutCallback(ping_cas, ping_timeout),
            token_life_timer = new TimeoutCallback(check_show_idle_warning, null),
            _onUserAction = function() {
                last_activity_time = get_current_time();
            };

        function get_ping_timeout() {
            var idle_time = WMConfig.settings.user_idle_timeout,
                ping_to;
            if (9 < idle_time && idle_time <= 60) {
                ping_to = 10;
            } else if (60 < idle_time && idle_time <= 60 * 3) {
                ping_to = 20;
            } else if (60 * 3< idle_time && idle_time <= 60 * 5) {
                ping_to = 30;
            } else if (60 * 5 < idle_time && idle_time <= 60 * 10) {
                ping_to = 60;
            } else if (60 * 10 < idle_time) {
                ping_to = 120;
            } else {
                throw 'user_idle_timeout cannot be less than 10 seconds';
            }
            $log.debug('ping_timeout = {0} sec'.format(ping_to));
            return ping_to * 1E3;
        }
        function get_current_token() {
            return document.cookie.replace(/(?:(?:^|.*;\s*)CastielAuthToken\s*\=\s*([^;]*).*$)|^.*$/, "$1");
        }
        function get_current_time() {
            return new Date().getTime();
        }
        function set_token_expire_time(deadline, token_live_time) {
            token_expire_time = deadline;
            $log.debug('new token deadline: {0} / {1}'.format(token_expire_time, new Date(token_expire_time * 1E3)));
            set_warning_timer(token_live_time);
        }
        function process_logout() {
            $window.open(WMConfig.url.logout, '_self');
        }
        function _set_tracking(on) {
            if (on) {
                $document.find('body').on(user_activity_events, _onUserAction);
            } else {
                $document.find('body').off(user_activity_events, _onUserAction);
            }
        }
        function _init_warning_timer() {
            check_token().then(function (result) {
                if (result) {
                    set_token_expire_time(result.data.deadline, result.data.ttl);
                }
            });
        }
        function check_token() {
            // do not prolong
            return $http.post(WMConfig.url.coldstar.cas_check_token, {
                token: get_current_token()
            }, {
                silent: true
            }).then(function (result) {
                if (!result.data.success) {
                    $log.error('Could not check token lifetime ({0}). You should be logged off.'.format(result.data.message));
                    return null;
                }
                return result;
            }, function (result) {
                $log.error('Could not check token lifetime (unknown error). You should be logged off.');
                return null;
            });
        }
        function ping_cas() {
            var cur_time = get_current_time();
            $log.debug('ping about to fire...');
            if ((cur_time - last_activity_time) < ping_timeout) {
                $log.debug('prolonging token (current expire time: {0} / {1})'.format(token_expire_time, new Date(token_expire_time * 1E3)));
                $http.post(WMConfig.url.coldstar.cas_prolong_token, { // TODO: url
                    token: get_current_token()
                }, {
                    silent: true
                }).success(function (result) {
                    if (!result.success) {
                        // TODO: накапливать ошибки и делать логаут?
                        $log.error('Could not prolong token on ping timer ({0})'.format(result.message));
                    } else {
                        last_ping_time = cur_time;
                        set_token_expire_time(result.deadline, result.ttl);
                    }
                }).error(function () {
                    $log.error('Could not prolong token on ping timer (unknown error)');
                });
            }
        }
        function set_warning_timer(token_live_time) {
            var warning_time = WMConfig.settings.logout_warning_timeout * 1E3,
                token_live_time = Math.floor(token_live_time * 1E3),
                to;
            if (token_live_time < 0) {
                $log.error('Token has already expired!');
            } else if (token_live_time < warning_time) {
                $log.warn('Logout warning time is greater than token lifetime.');
            } else {
                to = token_live_time - warning_time;
                $log.info('show warning dialog in (msec): ' + to);
                token_life_timer.start(to);
            }
        }
        function check_show_idle_warning() {
            var cur_time = get_current_time();
            if ((cur_time - last_activity_time) < ping_timeout) {
                $log.debug('fire ping instead of showing warning dialog');
                ping_cas();
            } else {
                check_token().then(function (result) {
                    if (result && result.data.deadline <= token_expire_time) {
                        show_logout_warning();
                    } else {
                        $log.debug('User is active in another system.');
                        set_token_expire_time(result.data.deadline, result.data.ttl);
                    }
                });
            }
        }
        function show_logout_warning() {
            _set_tracking(false);
            ping_timer.kill();
            IdleUserModal.open()
            .then(function cancelIdle (result) {
                $log.info('User has come back after idle.');
                _set_tracking(true);
                last_activity_time = get_current_time();
                ping_cas();
                ping_timer.start_interval();
            }, function logoutAfterIdle (result) {
                check_token().then(function (result) {
                    if (result && token_expire_time <= result.data.deadline) {
                        $log.info('Warning timer has expired, but logout won\'t be processed' +
                            ' because user was active in another system.');
                        _set_tracking(true);
                        ping_timer.start_interval();
                        set_token_expire_time(result.data.deadline, result.data.ttl);
                    } else {
                        $log.info('User is still idle. Logging off.');
                        process_logout();
                    }
                }, function () {
                    $log.info('Error checking token before logout. Logging off.');
                    process_logout();
                });
            });
        }

        return {
            start: function () {
                $log.debug('starting idle tracking');
                _set_tracking(true);
                ping_timer.start_interval();
                _init_warning_timer();
            }
        }
    }]).
    service('IdleUserModal', ['$modal', 'WMConfig', 'TimeoutCallback', function ($modal, WMConfig, TimeoutCallback) {
        return {
            open: function () {
                var IUController = function ($scope) {
                    $scope.countdown = WMConfig.settings.logout_warning_timeout;
                    $scope.idletime_minute = Math.floor(WMConfig.settings.user_idle_timeout / 60) || 1;
                    $scope.timer = new TimeoutCallback(function () {
                        if ($scope.countdown <= 0) {
                            $scope.$dismiss('Так и не вернулся...');
                        } else {
                            $scope.countdown--;
                        }
                    }, 1E3);
                    $scope.cancel_idle = function () {
                        $scope.timer.kill();
                        $scope.$close('Успел!');
                    };

                    $scope.timer.start_interval($scope.countdown + 1, 1E3);
                };
                var instance = $modal.open({
                    templateUrl: '/WebMis20/modal-IdleUser.html',
                    controller: IUController,
                    backdrop: 'static',
                    windowClass: 'idle-modal'
                });
                return instance.result;
            }
        };
    }]).
    run(['$templateCache', function ($templateCache) {
        $templateCache.put('/WebMis20/modal-IdleUser.html',
            '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                <h3 class="modal-title">Внимание!</h3>\
            </div>\
            <div class="modal-body">\
                <div>\
                  <p>Вы неактивны более <b>[[idletime_minute]]</b> минут.<br>\
                    Автоматический выход из системы произойдет через:</p>\
                    <h1 class="idle-countdown"><span class="label label-danger">[[countdown]]</span><small> секунд</small></h1>\
                </div>\
            </div>\
            <div class="modal-footer">\
                <button type="button" class="btn btn-success btn-lg" ng-click="cancel_idle()">Остаться в системе</button>\
            </div>'
        );
    }]).
    service('ScanningModal', ['$modal', '$http', 'WMConfig', function ($modal, $http, WMConfig) {
        function _getFileInfo(file) {
            var type = file.type,
                data;
            if (type === 'image') {
                data = file.image.src
            } else {
                data = file.binary_b64;
            }
            return {
                type: type,
                mime: file.mime,
                size: file.size,
                data: data
            }
        }
        return {
            open: function (client_id, cfa_id) {
                var FileEditController = function ($scope) {
                    $scope.mode = 'scanning';
                    $scope.device_list = [];
                    $scope.selected = { device: {name: 'test'} };
                    $scope.image = null;
                    $scope.file = { image: null };
                    var scales = [5, 10, 15, 30, 50, 75, 90, 100, 125, 150, 200, 300, 400, 500];
                    $scope.scalePct = 100;

                    $scope.get_device_list = function () {
                        $http.get(WMConfig.url.scanserver.list).success(function (data) {
                            $scope.device_list = data.devices;
                        });
                    };
                    $scope.start_scan = function () {
                        $http.post(WMConfig.url.scanserver.scan, {
                            name: $scope.selected.device.name
                        }).success(function (data) {
                            $scope.image = new Image();
                            $scope.image.src = 'data:image/png;base64,' + data.image;
                            $scope.file.encoded = $scope.image;
                        });
                    };
                    $scope.save_image = function () {
                        $http.post(WMConfig.url.api_patient_file_attach, {
                            file: _getFileInfo($scope.file),
                            client_id: client_id
                        }).success(function () {
                            alert('Сохранено');
                        }).error(function () {
                            alert('Ошибка сохранения');
                        });
                    };
                    $scope.clear_image = function () {
                        $scope.file.image = null;
                        $scope.image = null;
                    };
                    $scope.reset_image = function () {
                        $scope.$broadcast('resetImage');
                    };
                    $scope.rotate = function (w) {
                        var angle = w === 'left' ? -15 : 15;
                        $scope.$broadcast('rotateImage', {
                            angle: angle
                        });
                    };
                    $scope.zoom = function (how) {
                        $scope.scalePct = scales[scales.indexOf($scope.scalePct) + how];
                        $scope.$broadcast('zoomImage', {
                            scalePct: $scope.scalePct
                        });
                    };
                    $scope.crop = function (action) {
                        $scope.$broadcast('cropImage' + action);
                    };

                    $scope.correctFileSelected = function () {
                        return $scope.file.type === 'image' ?
                            $scope.file.image && $scope.file.image.src :
                            $scope.file.binary_b64;
                    };

                    if (cfa_id) {
                        $http.get(WMConfig.url.api_patient_file_attach, {
                            params: {
                                client_file_attach_id: cfa_id
                            }
                        }).success(function (data) {
                            $scope.image = new Image();
                            $scope.image.src = 'data:image/png;base64,' + data.result.image;
                            $scope.file.image = $scope.image;
                        }).error(function () {
                            alert('Ошибка открытия файла. Файл был удален.');
                        });
                    }
                };
                var instance = $modal.open({
                    templateUrl: '/WebMis20/modal-Scanning.html',
                    controller: FileEditController,
                    backdrop: 'static',
                    size: 'lg'
                });
                return instance.result;
            }
        };
    }]).
    run(['$templateCache', function ($templateCache) {
        $templateCache.put('/WebMis20/modal-Scanning.html',
            '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                <div class="btn-group pull-right">\
                    <label class="btn btn-lg btn-primary" ng-model="mode" btn-radio="\'scanning\'">Сканировать</label>\
                    <label class="btn btn-lg btn-primary" ng-model="mode" btn-radio="\'select_existing\'">Выбрать существующий</label>\
                </div>\
                <h3 class="modal-title">Добавление документа</h3>\
            </div>\
            <div class="modal-body">\
                <div class="row">\
                <div class="col-md-4">\
                    <div ng-show="mode === \'scanning\'">\
                    <h4>Выбор устройства</h4>\
                    <button type="button" class="btn btn-info btn-sm" ng-click="get_device_list()">\
                        Получить список доступных устройств\
                    </button>\
                    <div class="radio" ng-repeat="dev in device_list">\
                        <label>\
                            <input type="radio" id="dev[[$index]]" ng-model="selected.device"\
                                ng-value="dev">[[dev.model]]\
                        </label>\
                    </div>\
                    <hr>\
                    <h4>Параметры сканирования</h4>\
                    <button type="button" class="btn btn-warning btn-sm" ng-click="start_scan()"\
                        ng-disabled="!selected.device">\
                        Начать сканирование\
                    </button>\
                    </div>\
                    <div ng-show="mode === \'select_existing\'">\
                        <h4>Выбрать из файловой системы</h4>\
                        <input type="file" wm-input-file file="file">\
                    </div>\
                    <div id="help_canvas">\
                    </div>\
                </div>\
                <div class="col-md-8">\
                    <div class="btn-toolbar marginal bg-muted" role="toolbar" aria-label="...">\
                        <div class="btn-group btn-group-lg pull-right" role="group" aria-label="...">\
                            <button type="button" class="btn btn-default" ng-click="reset_image()" title="Вернуться к исходному изображению">\
                                <span class="fa fa-refresh"></span>\
                            </button>\
                            <button type="button" class="btn btn-default" ng-click="clear_image()" title="Очистить область изображения">\
                                <span class="fa fa-times"></span>\
                            </button>\
                        </div>\
                        <div class="btn-group btn-group-lg rmargin10" role="group" aria-label="...">\
                            <button type="button" class="btn btn-default" ng-click="rotate(\'left\')" title="Повернуть против часовой стрелки">\
                                <span class="fa fa-rotate-left"></span>\
                            </button>\
                            <button type="button" class="btn btn-default" ng-click="rotate(\'right\')" title="Повернуть по часовой стрелке">\
                                <span class="fa fa-rotate-right"></span>\
                            </button>\
                        </div>\
                        <div class="btn-group btn-group-lg rmargin10" role="group" aria-label="...">\
                            <button type="button" class="btn btn-default" ng-click="zoom(1)" title="Увеличить">\
                                <span class="fa fa-plus"></span>\
                            </button>\
                            <label class="label label-default">[[scalePct]] %</label>\
                            <button type="button" class="btn btn-default" ng-click="zoom(-1)" title="Уменьшить">\
                                <span class="fa fa-minus"></span>\
                            </button>\
                        </div>\
                        <div class="btn-group btn-group-lg" role="group" aria-label="...">\
                            <button type="button" class="btn btn-default" ng-click="crop(\'Start\')" title="Обрезать изображение">\
                                <span class="fa fa-crop"></span>\
                            </button>\
                            <button type="button" class="btn btn-default btn-success" ng-click="crop(\'Apply\')" title="Подтвердить">\
                                <span class="fa fa-check"></span>\
                            </button>\
                            <button type="button" class="btn btn-default btn-danger" ng-click="crop(\'Cancel\')" title="Отменить">\
                                <span class="fa fa-times"></span>\
                            </button>\
                        </div>\
                    </div>\
                    <div class="modal-scrollable-block">\
                        <wm-image-editor id="image_editor" model-image="file.image"></wm-image-editor>\
                    </div>\
                </div>\
                </div>\
            </div>\
            <div class="modal-footer">\
                <button type="button" class="btn btn-success" ng-click="save_image()" ng-disabled="!correctFileSelected()">\
                    Сохранить\
                </button>\
                <button type="button" class="btn btn-danger" ng-click="$dismiss()">Закрыть</button>\
            </div>'
        );
    }]).
    service('MessageBox', ['$modal', function ($modal) {
        return {
            info: function (head, message) {
                var MBController = function ($scope) {
                    $scope.head_msg = head;
                    $scope.message = message;
                };
                var instance = $modal.open({
                    templateUrl: '/WebMis20/modal-MessageBox-info.html',
                    controller: MBController
                });
                return instance.result;
            },
            error: function (head, message) {
                var MBController = function ($scope) {
                    $scope.head_msg = head;
                    $scope.message = message;
                };
                var instance = $modal.open({
                    templateUrl: '/WebMis20/modal-MessageBox-error.html',
                    controller: MBController
                });
                return instance.result;
            },
            question: function (head, question) {
                var MBController = function ($scope) {
                    $scope.head_msg = head;
                    $scope.question = question;
                };
                var instance = $modal.open({
                    templateUrl: '/WebMis20/modal-MessageBox-question.html',
                    controller: MBController
                });
                return instance.result;
            }
        };
    }]).
    run(['$templateCache', function ($templateCache) {
        $templateCache.put('/WebMis20/modal-MessageBox-info.html',
            '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
                <h4 class="modal-title">[[head_msg]]</h4>\
            </div>\
            <div class="modal-body">\
                <p ng-bind-html="message"></p>\
            </div>\
            <div class="modal-footer">\
                <button type="button" class="btn btn-success" ng-click="$close()">Ок</button>\
            </div>'
        );
    }]).
    run(['$templateCache', function ($templateCache) {
        $templateCache.put('/WebMis20/modal-MessageBox-error.html',
            '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
                <h4 class="modal-title">[[head_msg]]</h4>\
            </div>\
            <div class="modal-body">\
                <p ng-bind-html="message"></p>\
            </div>\
            <div class="modal-footer">\
                <button type="button" class="btn btn-danger" ng-click="$dismiss()">Ок</button>\
            </div>'
        );
    }]).
    run(['$templateCache', function ($templateCache) {
        $templateCache.put('/WebMis20/modal-MessageBox-question.html',
            '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
                <h4 class="modal-title">[[head_msg]]</h4>\
            </div>\
            <div class="modal-body">\
                <p ng-bind-html="question"></p>\
            </div>\
            <div class="modal-footer">\
                <button type="button" class="btn btn-danger" ng-click="$close(true)">Да</button>\
                <button type="button" class="btn btn-default" ng-click="$dismiss()">Отмена</button>\
            </div>'
        );
    }]);