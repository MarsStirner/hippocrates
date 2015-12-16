var IndexCtrl = function ($scope, $modal, $http, RefBookService, PrintingService) {
    $scope.selected_records = [];
    $scope.TTJStatus = RefBookService.get('TTJStatus');
    $scope.filter = {execDate:new Date(),
                     status: null
    }

    $scope.toggle_select_record = function (record) {
        if ($scope.selected_records.has(record)) {
            $scope.selected_records.remove(record);
        } else {
            $scope.selected_records.push(record);
        }
    };
    $scope.select_all_records = function () {
        if ($scope.selected_records.length == $scope.ttj_records.length) {
            $scope.selected_records = [];
        } else {
            $scope.selected_records = $scope.ttj_records.map(function (record) {
                if (!$scope.selected_records.has(record)) {
                }
                return record;
            })
        }
    };
    $scope.get_data = function() {
        $http.post(url_get_ttj_records, {
                filter: $scope.filter
        })
        .then(function (res) {
                $scope.ttj_records = res.data.result[0];
                $scope.tubes = res.data.result[1];
                $scope.number_by_status = res.data.result[2];
        });
    };
    $scope.change_status = function(status){
        var ids = $scope.selected_records.map(function(record){return record.id});
        $http.post(url_ttj_update_status, {
            ids: ids,
            status: $scope.TTJStatus.get_by_code(status)
        })
        .success(function(result) {
        })
    }

    $scope.$watchCollection('filter', function (new_value, old_value) {
        $scope.get_data();
    });
};
