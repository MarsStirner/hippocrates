'use strict';

WebMis20.controller('FileUploadFormCtrl', ['$scope', '$http', 'Upload', function ($scope, $http, Upload) {
    $scope.new_files = [];
    $scope.fmetas = [];

    $scope.addNewFile = function () {
        $scope.new_files.push({
            file: null,
            name: null,
            note: null
        });
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

    //$scope.upload = function (file) {
    //    Upload.upload({
    //        url: 'api/0/upload',
    //        data: {file: file, 'username': $scope.username}
    //    }).then(function (resp) {
    //        console.log('Success ' + resp.config.data.file.name + 'uploaded. Response: ' + resp.data);
    //    }, function (resp) {
    //        console.log('Error status: ' + resp.status);
    //    }, function (evt) {
    //        var progressPercentage = parseInt(100.0 * evt.loaded / evt.total);
    //        console.log('progress: ' + progressPercentage + '% ' + evt.config.data.file.name);
    //    });
    //};

    $scope.uploadFiles = function () {
        if ($scope.new_files.length) {
            Upload.upload({
                url: 'api/0/upload',
                data: {
                    files: _.pluck($scope.new_files, 'file'),
                    info:  Upload.json({
                        //attach_data: {
                        //    attach_type: 1,
                        //    errand_id: 82,
                        //    set_person_id: 1
                        //},
                        files_info: _.map($scope.new_files, function (f) { return _.pick(f, 'name', 'note') })
                    })
                }, // check all files not null
                arrayKey: ''
            }).then($scope.refreshFiles);
        }
    };
    $scope.refreshFiles = function () {
        $http.get('api/0/file_list')
            .success(function (response) {
                $scope.fmetas = response.result.files;
            });
    };

    $scope.refreshFiles();
}]);