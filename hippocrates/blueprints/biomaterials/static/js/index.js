var IndexCtrl = function ($scope, $modal, $http, RefBookService, PrintingService, MessageBox) {
    $scope.selected_records = [];
    $scope.TTJStatus = RefBookService.get('TTJStatus');
    $scope.rbLaboratory = RefBookService.get('rbLaboratory');
    $scope.ps_bm = new PrintingService("biomaterials");
    $scope.ps_bm.set_context("biomaterials");
    $scope.ps_resolve = function () {
        if (!$scope.selected_records.length) {
            return MessageBox.error('Печать невозможна', 'Выберите хотя бы один забор биоматериала');
        }
        var ttj_ids = [];
        $scope.selected_records.forEach(function(record){
            ttj_ids.push(record.id)
        })
        return {
            ttj_ids: ttj_ids
        }
    };
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
                $scope.ttj_records = res.data.result.ttj_records;
                $scope.tubes = res.data.result.test_tubes;
                $scope.number_by_status = res.data.result.number_by_status;
        });
    };
    $scope.change_status = function(status){
        var ids = $scope.selected_records.map(function(record){return record.id});
        $http.post(url_ttj_update_status, {
            ids: ids,
            status: $scope.TTJStatus.get_by_code(status)
        })
        .success(function(result) {
            $scope.get_data();
        })
    }

    $scope.open_info = function(record){
        var scope = $scope.$new();
        scope.model = record;
        return $modal.open({
            templateUrl: 'modal-ttj-info.html',
            scope: scope,
            size: 'lg'
        })
    }

    $scope.$watchCollection('filter', function (new_value, old_value) {
        if($scope.filter.lab && $scope.filter.status != 2) {
            $scope.filter.lab = null;
        }
        $scope.get_data();
        $scope.selected_records = [];
    });
};
