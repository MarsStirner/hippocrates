WebMis20.controller('FileUploadCtrl', ['$scope', '$q', 'CurrentUser', 'Upload', 'WMAction', 'MessageBox', 'WMConfig', 'RefBookService',
    function ($scope, $q, CurrentUser, Upload, WMAction, MessageBox, WMConfig, RefBookService) {
    $scope.new_files = [];
    $scope.max_file_size = WMConfig.local_config.files_upload.max_file_size;
    $scope.files_pattern = WMConfig.local_config.files_upload.pattern;
    $scope.ro = false;
    $scope.action_attach_type_id = null;

    function reformatUploadedFiles(file_data) {
        return _.map(file_data, function(responseObj) {
                var arrayOfSingleFile = safe_traverse(responseObj, ['data', 'result', 'files']);
                if (arrayOfSingleFile && arrayOfSingleFile.length > 0) {
                    return {file_meta: arrayOfSingleFile[0]};
                }
        });
    }
    $scope.$on('before_action_saved', function(event, data) {
        if(data.action) {
            $scope.processNewFiles(data.action);
        }
    });

    $scope.processNewFiles = function (action) {
        var attach_data = make_attach_data(action);
        var upload_promises = _.map($scope.new_files, function (f) { return $scope.uploadFiles([f], attach_data) });
        return $q.all(upload_promises)
            .then(function (data) {
                var fileDatas = reformatUploadedFiles(data);
                // action.reload();
                $scope.new_files = [];
                action.attached_files = action.attached_files.concat(fileDatas);
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
            }).then(function(data) {
                return data;
            }, function (result) {
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
    $scope.init = function() {
        var fat = RefBookService.get('FileAttachType');
        $q.all([fat.loading]).then(function () {
            $scope.action_attach_type_id = fat.get_by_code('action').id;
        });
    };
    $scope.init();
    
}]);