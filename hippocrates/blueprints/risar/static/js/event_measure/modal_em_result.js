'use strict';

WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/RISAR/modal/em_result_edit.html',
        '\
<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title">Результат по мероприятию</h4>\
</div>\
<div class="modal-body">\
<section class="content">\
    <div class="row">\
    <div class="col-md-12">\
        <div class="box box-info">\
            <div class="box-body">\
                <wm-action-layout action="action"></wm-action-layout>\
                <hr>\
                <h4>Файл <button type="button" class="btn btn-link lmargin20" ngf-select="addNewFiles($files)" \
                ngf-multiple="true" ngf-max-size="10MB" ngf-pattern="\'.pdf,.bmp,.jpg,.jpeg,.png,.tiff,.gif,.psd\'"\
                            ng-show="canAddFile()">Добавить</button>\
                </h4> <p class="text-info">Разрешена загрузка файлов размером не более 10Мб с расширением .pdf, .bmp, .jpg, .jpeg, .png, .tiff, .gif, .psd</p>\
                <table class="table table-condensed" ng-show="filesTableVisible()">\
                    <thead>\
                        <tr>\
                            <th>Наименование</th>\
                            <th>Файл</th>\
                        </tr>\
                    </thead>\
                    <tbody>\
                        <tr ng-repeat="attach in action.attached_files">\
                            <td><input type="text" class="form-control" ng-model="attach.file_meta.name" ng-required="true"\
                                ng-disabled="!canEditFileInfo(attach)"></td>\
                            <td>\
                                <a ng-href="[[attach.file_meta.url]]" target="_blank" class="btn btn-sm btn-primary" title="Скачать"\
                                    ng-disabled="!canDownloadFile(attach)">\
                                    <i class="fa fa-download"></i>\
                                </a>\
                                <button type="button" class="btn btn-sm btn-danger" ng-click=removeFile($index)\
                                    title="Удалить" ng-if="canDeleteFile(attach)">\
                                    <i class="fa fa-trash"></i>\
                                </button>\
                            </td>\
                        </tr>\
                        <tr ng-repeat="file in new_files">\
                            <td><input type="text" class="form-control" ng-model="file.name" ng-required="true"\
                                ng-disabled="!canEditFileInfo(file)"></td>\
                            <td>\
                                <button type="button" class="btn btn-sm btn-danger" ng-click=removeNewFile($index)\
                                    title="Удалить" ng-if="!file.id">\
                                    <i class="fa fa-remove"></i>\
                                </button>\
                            </td>\
                        </tr>\
                    </tbody>\
                </table>\
            </div>\
        </div>\
    </div>\
    </div>\
</section>\
</div>\
<div class="modal-footer">\
    <ui-print-button ps="ps" resolve="ps_resolve()" before-print="save_em_result(true)" fast-print="true"\
        class="pull-left"></ui-print-button>\
    <button type="button" class="btn btn-default" ng-click="close()">Закрыть</button>\
    <button type="button" class="btn btn-primary" ng-click="save_em_result()">Сохранить</button>\
</div>');
}]);


var EMResultModalCtrl = function ($scope, $q, $rootScope, RisarApi, RefBookService, Upload, WMAction,
                                  PrintingService, PrintingDialog, MessageBox, WMConfig, EventMeasureService,
                                  CurrentUser, event_measure, em_result) {
    $scope.action_attach_type_id = null;
    $scope.new_files = [];
    $scope.ro = false;
    var _saved = false;
    $scope.ps = new PrintingService("event_measure");
    $scope.ps_resolve = function () {
        return {
            event_measure_id: event_measure.data.id
        }
    };

    function update_print_templates (context_name) {
        $scope.ps.set_context(context_name);
    }

    $scope.close = function () {
        if (_saved) {
            $scope.$close();
        } else {
            $scope.$dismiss('cancel');
        }
    };
    $scope.saveAndClose = function () {
        $scope.save_em_result().then(function () {
            $scope.$close();
        });
    };
    $scope.save_em_result = function (need_to_print) {
        var data = $scope.action.get_data(),
            event_measure_id = event_measure.data.id,
            em_result_id = em_result.id;
        return $scope.check_can_save_action()
            .then(function () {
                // новый экшен надо сначала сохранить
                return RisarApi.measure.save_em_result(
                    event_measure_id,
                    em_result_id,
                    data
                ).
                    then(function (action) {

                        _saved = true;
                        $scope.action.merge(action);
                        event_measure.data.result_action_id = action.id;
                        em_result.id = action.id;
                        // затем сохранить его файлы
                        return $scope.processNewFiles(action)
                            .then(function () {
                                // затем получить новые данные по экшену
                                return EventMeasureService.get_em_result(event_measure)
                                    .then(function (action) {
                                        $scope.action.merge(action);
                                        $rootScope.$broadcast('mayBeUziSrokChanged');
                                    })
                            });
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
    $scope.processNewFiles = function (action) {
        var attach_data = make_attach_data(action);
        var upload_promises = _.map($scope.new_files, function (f) { return $scope.uploadFiles([f], attach_data) });
        return $q.all(upload_promises)
            .then(function () {
                $scope.new_files = [];
            });
    };
    $scope.uploadFiles = function (files, attach_data) {
        if (files && files.length) {
            return Upload.upload({
                url: WMConfig.url.devourer.upload,
                data: {
                    files: _.pluck(files, 'file'),
                    info: Upload.json({
                        attach_data: attach_data,
                        files_info: _.map(files, function (f) { return _.pick(f, 'name') })
                    })
                },
                arrayKey: '',
                withCredentials: true
            }).then(angular.noop, function (result) {
                return MessageBox.error(
                    'Ошибка сохранения файла',
                    'Не удалось сохранить прикреплённый файл. Свяжитесь с администратором.'
                );
            });
        }
        var defer = $q.defer();
        defer.resolve('no files to upload');
        return defer.promise;
    };
    $scope.check_can_save_action = function () {
        var deferred = $q.defer();
        if ($scope.action.readonly) {
            deferred.reject({
                silent: true,
                message: 'Действие открыто в режиме чтения'
            });
        } else {
            deferred.resolve();
        }
        return deferred.promise;
    };

    var make_attach_data = function (action) {
        return {
            attach_type: $scope.action_attach_type_id,
            action_id: action.id,
            set_person_id: CurrentUser.id
        }
    };
    var make_file = function (file_obj) {
        return {
            file: file_obj,
            name: null
        };
    };

    $scope.addNewFiles = function (files) {
        _.map(files, function (file) {
            var nf = make_file(file);
            $scope.setFileName(nf);
            $scope.new_files.push(nf);
        });
    };
    $scope.removeNewFile = function (idx) {
        $scope.new_files.splice(idx, 1);
    };
    $scope.removeFile = function (idx) {
        $scope.action.attached_files.splice(idx, 1);
    };
    $scope.setFileName = function (file) {
        if (file.file) {
            var orig_name = file.file.name,
                ext_idx = orig_name.lastIndexOf('.');
            if (ext_idx !== -1) {
                orig_name = orig_name.substring(0, ext_idx);
            }
            file.name = orig_name;
        }
    };

    $scope.canAddFile = function () {
        return $scope.action.attached_files && !$scope.ro;
    };
    $scope.filesTableVisible = function () {
        return $scope.action.attached_files && $scope.action.attached_files.length > 0 ||
            $scope.new_files.length > 0;
    };
    $scope.canEditFileInfo = function (file_attach) {
        return !file_attach.id || !$scope.ro || CurrentUser.current_role_in('admin');
    };
    $scope.canDownloadFile = function (attach) {
        return true;
    };
    $scope.canDeleteFile = function (attach) {
        return !$scope.ro || CurrentUser.current_role_in('admin');
    };

    $scope.init = function () {
        $scope.action = new WMAction();
        $scope.ActionStatus = RefBookService.get('ActionStatus');
        var fat = RefBookService.get('FileAttachType');
        $q.all([$scope.ActionStatus.loading, fat.loading]).then(function () {
            $scope.action = $scope.action.merge(em_result);
            $scope.ro = $scope.action.readonly = $scope.action.ro = em_result.ro;
            update_print_templates(em_result.action_type.context_name);
            $scope.action_attach_type_id = fat.get_by_code('action').id;
        });
    };

    $scope.init();
};


WebMis20.controller('EMResultModalCtrl', ['$scope', '$q', 'RisarApi', 'RefBookService', 'Upload', 'WMAction',
    'PrintingService', 'PrintingDialog', 'MessageBox', 'WMConfig', 'EventMeasureService',
    'CurrentUser', EMResultModalCtrl]);