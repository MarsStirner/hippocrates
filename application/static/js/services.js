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
    service('FileEditModal', ['$modal', '$http', 'WMConfig', function ($modal, $http, WMConfig) {
        function _getTemplate(openMode, attachType) {
            var template = '\
    <div class="modal-header">\
        <h3 class="modal-title">Добавление документа</h3>\
    </div>\
    <div class="modal-body">\
        <div class="row">\
            <div class="col-md-4">\
                <div class="btn-group">\
                    <label class="btn btn-default" ng-model="mode" btn-radio="\'scanning\'">Сканировать</label>\
                    <label class="btn btn-default" ng-model="mode" btn-radio="\'select_existing\'">Выбрать файл</label>\
                </div>\
            </div>\
            <div id="pages" class="col-md-8">\
                <div class="row">\
                    <div class="col-md-8 form-inline">\
                        <label class="control-label">Имя файла</label>\
                        <input type="text" class="form-control" ng-model="currentFile.name" style="width: inherit;">\
                        <button type="button" class="btn btn-sm btn-primary" ng-click="generateFileName(true)" title="Сформировать имя файла">\
                            <span class="glyphicon glyphicon-repeat"></span>\
                        </button>\
                    </div>\
                    <div class="col-md-4">\
                        <button type="button" class="btn btn-sm btn-success pull-right" ng-click="addPage()">\
                            <span class="glyphicon glyphicon-plus" title="Добавить страницу"></span>\
                        </button>\
                        <pagination total-items="file_attach.file_document.totalPages()" items-per-page="1" ng-model="selected.currentPage" ng-change="pageChanged()"\
                            previous-text="&lsaquo;" next-text="&rsaquo;" class="pagination-nomargin pull-right"></pagination>\
                    </div>\
                </div>\
            </div>\
        </div>\
        <hr>\
        <div class="row">\
        <div class="col-md-4">\
            {0}\
            {1}\
        </div>\
        <div class="col-md-8">\
            <div id="image_editor" ng-show="imageSelected()">\
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
                <wm-image-editor id="image_editor" model-image="currentFile.file.image"></wm-image-editor>\
            </div>\
            </div>\
            <div ng-show="notImageSelected()"><span>Предпросмотр недоступен. Выбранный файл не является изображением.</span></div>\
        </div>\
        </div>\
    </div>\
    <div class="modal-footer">\
        <button type="button" class="btn btn-success" ng-click="save_image()" ng-disabled="!correctFileSelected()">\
            Сохранить\
        </button>\
        <button type="button" class="btn btn-danger" ng-click="$dismiss()">Закрыть</button>\
    </div>';
            var addFileTemplate = '\
    <div ng-show="mode === \'scanning\'">\
        <ol>\
        <li><h4>Выбрать устройство</h4></li>\
        <button type="button" class="btn btn-primary btn-sm" ng-click="get_device_list()">\
            Получить список доступных устройств\
        </button>\
        <div class="radio" ng-repeat="dev in device_list">\
            <label>\
                <input type="radio" id="dev[[$index]]" ng-model="selected.device"\
                    ng-value="dev">[[dev.model]]\
            </label>\
        </div>\
        <hr>\
        <li><h4>Настроить параметры сканирования</h4></li>\
        <label>Качество изображения</label>\
        <select><option>Хорошее</option></select>\
        <label>Режим сканирования</label>\
        <select><option>Цветной</option></select>\
        <hr>\
        <li><h4>Начать сканирование</h4></li>\
        <button type="button" class="btn btn-warning btn-sm" ng-click="start_scan()"\
            ng-disabled="!selected.device">\
            Получить изображение\
        </button>\
        </ol>\
    </div>\
    <div ng-show="mode === \'select_existing\'">\
        <input type="file" wm-input-file file="currentFile.file" on-change="generateFileName()"\
            accept="image/*,.pdf,.txt,.odt,.doc,.docx,.ods,.xls,.xlsx">\
    </div>\
    <hr>';
            var metaInfoTemplate = '\
    <div id="metaInfoBlock" class="modal-scrollable-block2">\
        <legend>Информация о документе</legend>\
        <ng-form name="metaInfoForm">\
            <div class="form-group">\
                <label for="docName">Наименование</label>\
                <input type="text" class="form-control" id="docName" ng-model="file_attach.file_document.name">\
            </div>\
            <div class="form-group">\
                <label for="documentType">Тип документа</label>\
                <rb-select id="documentType" ng-model="file_attach.doc_type" ref-book="rbDocumentType"\
                    placeholder="Тип документа" ng-change="generateFileDocumentName()">\
                </rb-select>\
            </div>\
            <label class="radio-inline">\
                <input type="radio" id="relType" ng-model="file_attach.rel_type" ng-value="\'own\'" ng>Документ пациента\
            </label>\
            <label class="radio-inline">\
                <input type="radio" id="relType" ng-model="file_attach.rel_type" ng-value="\'relative\'">Документ родственника\
            </label>\
            <div class="form-group" ng-show="file_attach.rel_type === \'relative\'">\
                <label for="relativeType">Родство с пациентом</label>\
                <wm-relation-type-rb id="relativeType" class="form-control" name="relativeType"\
                    client="client.info" direct="false" ng-model="file_attach.relation_type"\
                    ng-change="generateFileDocumentName()" ng-required="relativeRequired()">\
                </wm-relation-type-rb>\
            </div>\
            <div class="form-group" ng-show="file_attach.rel_type === \'own\'">\
                <label for="relDocType">Связанный документ</label>\
                <span id="conDoc"></span>\
            </div>\
        </ng-form>\
    </div>';

            template = template.format(
                openMode === 'new' ? (addFileTemplate) : '',
                attachType === 'client' ? (metaInfoTemplate) : ''
            );
            return template;
        }

        var WMFile = function (source) {
            if (!source) {
                this.mime = null;
                this.size = null;
                this.name = null;
                this.type = null;
                this.image = null;
                this.binary_b64 = null;
            } else {
                this.load(source);
            }
        };
        WMFile.prototype.load = function (source) {
            this.mime = source.mime;
            this.size = source.size;
            this.name = source.name;
            if (this.mime === null || this.mime === undefined) {
                this.type = this.image = this.binary_b64 = null;
            } else if (/image/.test(this.mime)) {
                this.type = 'image';
                this.image = new Image();
                this.image.src = "data:{0};base64,".format(this.mime) + source.data;
                this.binary_b64 = null;
            } else {
                this.type = 'other';
                this.binary_b64 = source.data;
                this.image = null;
            }
        };

        var WMFileMeta = function (source, idx, id) {
            if (!source) {
                this.id = id || null;
                this.name = null;
                this.idx = idx || null;
                this.setFile();
            } else {
                angular.extend(this, source);
                this.file = new WMFile(source); // TODO
            }
        };
        WMFileMeta.prototype.setFile = function (file) {
            this.file = new WMFile(file);
        };
        WMFileMeta.prototype.isImage = function () {
            return this.file.type === 'image' && this.file.image.src;
        };
        WMFileMeta.prototype.isNotImage = function () {
            return this.file.type === 'other' && this.file.binary_b64;
        };
        WMFileMeta.prototype.isLoaded = function () {
            return this.file.type === 'image' ? Boolean(this.file.image.src) : Boolean(this.file.binary_b64);
        };

        var WMFileDocument = function (source) {
            if (!source) {
                this.id = null;
                this.name = null;
                this.files = [];
            } else {
                angular.extend(this, source);
                this.files = [];
                angular.forEach(source.files, function (file) {
                    this.files[file.idx] = new WMFileMeta(file);
                }, this);
            }
        };
        WMFileDocument.prototype.addPage = function () {
            this.files.push(new WMFileMeta(null, this.files.length));
        };
        WMFileDocument.prototype.getFile = function (pageNum) {
            return this.files[pageNum - 1];
        };
        WMFileDocument.prototype.totalPages = function () {
            return this.files.length;
        };
        WMFileDocument.prototype.setPages = function (pages) {
            angular.forEach(pages, function (fm) {
                if (!this.files.hasOwnProperty(fm[1])) {
                    this.files[fm[1]] = new WMFileMeta(null, fm[1], fm[0]);
                }
            }, this);
        };

        var WMFileAttach = function (source) {
            if (!source) {
                this.id = null;
                this.attach_date = null;
                this.doc_type = null;
                this.relation_type = null;
                this.file_document = new WMFileDocument();
            } else {
                angular.extend(this, source);
                this.file_document = new WMFileDocument(source.file_document);
            }
            this.rel_type = this.relation_type ? 'relative': 'own';
        };

        function makeAttachFileDocumentInfo(fileAttach) {
            angular.forEach(fileAttach.file_document.files, function (fileMeta, key) {
                var fileinfo = fileMeta.file,
                    data = fileinfo.type === 'image' ? fileinfo.image.src : fileinfo.binary_b64;

                fileAttach.file_document.files[key] = {
                    meta: {
                        id: fileMeta.id,
                        name: fileMeta.name,
                        idx: fileMeta.idx
                    },
                    file: {
                        mime: fileinfo.mime,
                        data: data
                    }
                };
            });
            return fileAttach;
        }

        function capitalize(text) {
            return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
        }
        function unspace(text) {
            return text.replace(/ /g, '_');
        }

        var FileEditController = function ($scope, file_attach, client_id, client) {
            $scope.client = client;
            $scope.mode = 'scanning';
            $scope.device_list = [];
            $scope.selected = {
                device: {},
                currentPage: 1
            };
            $scope.file_attach = file_attach;
            $scope.currentFile = $scope.file_attach.file_document.getFile($scope.selected.currentPage);
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
                    client_id: client_id,
                    file_attach: makeAttachFileDocumentInfo($scope.file_attach)
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

            $scope.addPage = function () {
                $scope.file_attach.file_document.addPage();
                $scope.selected.currentPage = $scope.file_attach.file_document.totalPages();
                $scope.pageChanged();
            };
            $scope.pageChanged = function () {
                $scope.currentFile.file.selected = false;
                $scope.currentFile = $scope.file_attach.file_document.getFile($scope.selected.currentPage);
                if ($scope.currentFile.id && !$scope.currentFile.isLoaded()) {
                    $http.get(WMConfig.url.api_patient_file_attach, {
                        params: {
                            file_meta_id: $scope.currentFile.id
                        }
                    }).success(function (data) {
                        $scope.currentFile.file.load(data.result);
                    }).error(function () {
                        alert('Ошибка открытия файла. Файл был удален.');
                    });
                }
            };
            $scope.generateFileName = function (force) {
                if ($scope.currentFile.name && !force) {
                    return
                }
                var docFileName = $scope.file_attach.file_document.name,
                    name = '{0}{_(|1|)}_Лист_№{2}'.formatNonEmpty(
                    unspace(docFileName ? docFileName :
                        safe_traverse($scope.file_attach, ['doc_type', 'name'], 'Файл')
                    ),
                    docFileName ? '' : safe_traverse($scope.file_attach, ['relation_type', 'leftName'], ''),
                    $scope.currentFile.idx + 1
                );
                $scope.currentFile.name = name;
            };
            $scope.generateFileDocumentName = function () {
                var name = '{0}{ (|1|)}'.formatNonEmpty(
                    safe_traverse($scope.file_attach, ['doc_type', 'name'], 'Документ'),
                    safe_traverse($scope.file_attach, ['relation_type', 'leftName'], '')
                );
                $scope.file_attach.file_document.name = name;
            };
            $scope.$watch('file_attach.rel_type', function (n, o) {
                if (n !== 'relative') {
                    $scope.file_attach.relation_type = null;
                    $scope.generateFileDocumentName();
                }
            });

            $scope.imageSelected = function () {
                return $scope.currentFile.isImage();
            };
            $scope.notImageSelected = function () {
                return $scope.currentFile.isNotImage();
            };
            $scope.correctFileSelected = function () {
                return true || $scope.file.type === 'image' ? // TODO
                    $scope.imageSelected() :
                    $scope.notImageSelected();
            };
        };
        return {
            addNew: function (client_id, params) {
                var file_attach = new WMFileAttach();
                file_attach.file_document.addPage();
                var instance = $modal.open({
                    template: _getTemplate('new', params.attachType),
                    controller: FileEditController,
                    backdrop: 'static',
                    size: 'lg',
                    windowClass: 'modal-full-screen',
                    resolve: {
                        file_attach: function () {
                            return file_attach;
                        },
                        client_id: function () {
                            return client_id;
                        },
                        client: function () {
                            return params.client;
                        }
                    }
                });
                return instance.result;
            },
            open: function (cfa_id, params) {
                var idx = params.idx,
                    file_attach;
                return $http.get(WMConfig.url.api_patient_file_attach, {
                    params: {
                        cfa_id: cfa_id,
                        idx: idx
                    }
                }).success(function (data) {
                    file_attach = new WMFileAttach(data.result.cfa);
                    file_attach.file_document.setPages(data.result.other_pages);
                    return open_modal();
                }).error(function () {
                    alert('Ошибка открытия файла. Файл был удален.');
                });

                function open_modal() {
                    var instance = $modal.open({
                        template: _getTemplate('open', params.attachType),
                        controller: FileEditController,
                        backdrop: 'static',
                        size: 'lg',
                        windowClass: 'modal-full-screen',
                        resolve: {
                            file_attach: function () {
                                return file_attach;
                            },
                            client_id: function () {
                                return params.client.client_id;
                            },
                            client: function () {
                                return params.client;
                            }
                        }
                    });
                    return instance.result;
                }
            }
        };
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