'use strict';

WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/RISAR/modal/errand.html',
        '\
<div class="modal-header">\
    <h3 class="modal-title">Поручение [[model.number]] по карте [[model.event.external_id]]</h3>\
</div>\
<div class="modal-body">\
    <div class="das-form">\
        <ng-form id="createErrandForm" name="createErrandForm">\
        <table class="table table-condensed">\
            <thead>\
                <tr>\
                    <th class="col-md-3"></th>\
                    <th class="col-md-9"></th>\
                </tr>\
            </thead>\
            <tbody>\
                <tr>\
                    <th class="text-right">Статус</th>\
                    <td>\
                        <div class="col-md-12">\
                            <span ng-class="{\'label-info\': model.status.code == \'waiting\',\
                                             \'label-success\': model.status.code == \'executed\',\
                                             \'label-danger\': model.status.code == \'expired\',\
                                             \'label-warning\': model.status.code == \'late_execution\'}" class="label">\
                                [[model.status.name]]\
                            </span>\
                        </div>\
                    </td>\
                </tr>\
                <tr>\
                    <th class="text-right">Описание <span class="text-danger">*</span></th>\
                    <td>\
                        <div class="col-md-12"><wysiwyg ng-disabled="!isAuthor()" contenteditable="isAuthor()"\
                                                        ng-model="model.text" ng-required="true" /></div>\
                    </td>\
                </tr>\
                <tr>\
                    <th class="text-right">Автор, дата создания</th>\
                    <td>\
                        <div class="col-md-5">\
                            [[model.set_person.short_name]]<span ng-if="model.create_datetime">, </span>[[model.create_datetime | asDate]]\
                        </div>\
                    </td>\
                </tr>\
                 <tr ng-show="model.communications.length || isAuthor()">\
                    <th class="text-right">Контактные данные</th>\
                    <td>\
                        <div class="col-md-12">\
                            <textarea rows="4" style="border-radius:0.2em!important;" ng-disabled="!isAuthor()"\
                                id="communications" name="communications" class="form-control col-md-12" rows="3"\
                                ng-model="model.communications"></textarea>\
                        </div>\
                    </td>\
                </tr>\
                <tr>\
                    <th class="text-right">Выполнить до <span class="text-danger">*</span></th>\
                    <td>\
                        <div class="col-md-4">\
                            <wm-date name="date" ng-disabled="!isAuthor()" ng-model="model.planned_exec_date"\
                                     style="width: 250px" ng-required="true"></wm-date>\
                        </div>\
                    </td>\
                </tr>\
                <tr>\
                    <th class="text-right">Исполнитель <span class="text-danger">*</span></th>\
                    <td>\
                        <div class="col-md-5">\
                            <ui-select ng-model="model.exec_person" theme="select2" class="form-control" ref-book="vrbPersonWithSpeciality"\
                                       ng-disabled="!isAuthor()" ng-required="true">\
                                <ui-select-match>[[ $select.selected.name ]]</ui-select-match>\
                                <ui-select-choices repeat="item in $refBook.objects | filter: $select.search | limitTo: 50">\
                                    <span ng-bind-html="item.name | highlight: $select.search"></span>\
                                </ui-select-choices>\
                            </ui-select>\
                        </div>\
                    </td>\
                </tr>\
            </tbody>\
        </table>\
\
        <table class="table table-condensed" ng-if="model.id">\
            <thead>\
                <tr>\
                    <th class="col-md-3"></th>\
                    <th class="col-md-9"></th>\
                </tr>\
            </thead>\
            <tbody>\
                <tr>\
                    <th class="text-right">Ответ </th>\
                    <td>\
                        <div class="col-md-12">\
                            <span ng-show="isExecutor()"><wysiwyg ng-model="model.result"/></span>\
                            <span ng-show="isAuthor()">[[model.result]]</span>\
                        </div>\
                    </td>\
                </tr>\
                <tr>\
                    <th class="text-right">Дата выполнения</th>\
                    <td>\
                        <div class="col-md-4">\
                            [[model.exec_date | asDateTime]]\
                        </div>\
                    </td>\
                </tr>\
            </tbody>\
        </table>\
\
        <table class="table table-condensed">\
            <thead>\
                <tr>\
                    <th class="col-md-3"></th>\
                    <th class="col-md-9"></th>\
                </tr>\
            </thead>\
            <tbody>\
            <tr>\
                <th class="text-right">Файлы</th>\
                <td>\
                    <div class="col-md-12">\
                        <button type="button" class="btn btn-link" ngf-select ngf-multiple="true"\
                            ngf-change="addNewFiles($files)"\
                            ng-disabled="!isAuthor() && !isExecutor()">Добавить</button><br>\
                        <table class=table table-compact>\
                        <tr>\
                            <th>Наименование</th>\
                            <th>Комментарий</th>\
                            <th>Файл</th>\
                            <th></th>\
                        </tr>\
                        <tr ng-repeat="attach in model.errand_files">\
                            <td><input type="text" class="form-control" ng-model="attach.file_meta.name" ng-required="true"\
                                ng-disabled="!canEditFileInfo(attach)"></td>\
                            <td><input type="text" class="form-control" ng-model="attach.file_meta.note"\
                                ng-disabled="!canEditFileInfo(attach)"></td>\
                            <td>\
                                <a ng-href="[[attach.file_meta.url]]" target="_blank" class="btn btn-sm btn-primary" title="Скачать"\
                                    ng-disabled="!canDownloadFile(attach)">\
                                    <i class="fa fa-download"></i>\
                                </a>\
                            </td>\
                            <td></td>\
                        </tr>\
                        <tr><tr>\
                        <tr ng-repeat="file in new_files">\
                            <td><input type="text" class="form-control" ng-model="file.name" ng-required="true"\
                                ng-disabled="!canEditFileInfo(file)"></td>\
                            <td><input type="text" class="form-control" ng-model="file.note"\
                                ng-disabled="!canEditFileInfo(file)"></td>\
                            <td>\
                                <button type="button" class="btn btn-sm btn-danger" ng-click=removeNewFile($index)\
                                    title="Удалить" ng-if="!file.id">\
                                    <i class="fa fa-remove"></i>\
                                </button>\
                            </td>\
                            <td></td>\
                        </tr>\
                        </table>\
                    </div>\
                </td>\
            </tr>\
            </tbody>\
        </table>\
        </ng-form>\
    </div>\
</div>\
<div class="modal-footer">\
    <button class="btn btn-success" ng-click="executeErrand()" ng-if="canExecute()">Выполнить</button>\
    <button class="btn btn-success" ng-click="saveAndClose()" ng-disabled="createErrandForm.$invalid" >Сохранить</button>\
    <button class="btn btn-default" ng-click="$dismiss()">Закрыть</button>\
</div>');
}]);


var ErrandModalCtrl = function ($scope, $q, RisarApi, RefBookService, CurrentUser, UserErrand, Upload,
                                WMConfig, model, is_author) {
    $scope.model = model;
    $scope.is_author = is_author !== undefined ?
        is_author :
        CurrentUser.id === model.set_person.id;
    $scope.new_files = [];
    $scope.errand_attach_type_id = null;

    $scope.saveAndClose = function () {
        $scope.save_errand().then(function () {
            $scope.$close({
                status: 'ok',
                errand: $scope.model
            });
        });
    };
    $scope.save_errand = function () {
        var errand;
        if ($scope.isNewErrand()) {
            errand = UserErrand.create_errand($scope.model);
        } else {
            errand = UserErrand.edit_errand($scope.model);
        }
        return errand.then(function (errand) {
            $scope.model = errand;
            return $scope.processNewFiles(errand);
        });
    };
    $scope.processNewFiles = function (errand) {
        var attach_data = make_attach_data(errand);
        return $scope.uploadFiles($scope.new_files, attach_data);
    };
    $scope.executeErrand = function () {
        UserErrand.execute($scope.model).then(reload);
    };
    $scope.uploadFiles = function (files, attach_data) {
        if (files && files.length) {
            return Upload.upload({
                url: WMConfig.url.devourer.upload,
                data: {
                    files: _.pluck($scope.new_files, 'file'),
                    info: Upload.json({
                        attach_data: attach_data,
                        files_info: _.map($scope.new_files, function (f) { return _.pick(f, 'name', 'note') })
                    })
                },
                arrayKey: '',
                withCredentials: true
            });
        }
    };

    var make_attach_data = function (errand) {
        return {
            attach_type: $scope.errand_attach_type_id,
            errand_id: errand.id,
            set_person_id: CurrentUser.id
        }
    };
    var make_file = function (file_obj) {
        return {
            file: file_obj,
            name: null,
            note: null
        };
    };

    $scope.addNewFiles = function (files) {
        files.forEach(function (new_file) {
            var nf = make_file(new_file);
            $scope.setFileName(nf);
            $scope.new_files.push(nf);
        });
    };
    $scope.removeNewFile = function (idx) {
        $scope.new_files.splice(idx, 1);
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
    $scope.isNewErrand = function () {
        return !$scope.model.id;
    };
    $scope.isAuthor = function () {
        return $scope.is_author;
    };
    $scope.isExecutor = function () {
        return CurrentUser.id === safe_traverse($scope, ['model', 'exec_person', 'id']);
    };
    $scope.canExecute = function () {
        return $scope.model.id && !$scope.model.exec_date && $scope.isExecutor();
    };
    $scope.executorFirstRead = function () {
        return !$scope.isNewErrand() && $scope.isExecutor() && !$scope.model.reading_date;
    };
    $scope.canEditFileInfo = function (file_attach) {
        return !file_attach.id || file_attach.set_person_id === CurrentUser.id;
    };
    $scope.canDownloadFile = function (attach) {
        return $scope.isAuthor() || $scope.isExecutor() || CurrentUser.current_role_in('admin');
    };

    var reload = function () {
        $scope.new_files = [];
        RisarApi.errands.get($scope.model.id).then(function (errand) {
            $scope.model = errand;
        });
    };
    $scope.init = function () {
        var fat = RefBookService.get('FileAttachType');
        $q.all([fat.loading]).then(function () {
            $scope.errand_attach_type_id = fat.get_by_code('errand').id;
            if ($scope.executorFirstRead()) {
                UserErrand.mark_as_read($scope.model);
            }
        });
    };

    $scope.init();
};


WebMis20.controller('ErrandModalCtrl', ['$scope', '$q', 'RisarApi', 'RefBookService', 'CurrentUser',
    'UserErrand', 'Upload', 'WMConfig', ErrandModalCtrl]);