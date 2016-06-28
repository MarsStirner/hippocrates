
'use strict';

var ErrandsListCtrl = function ($scope, $window, $timeout, RisarApi, UserErrand,
        CurrentUser, ErrandModalService, TimeoutCallback) {
    var params = aux.getQueryParams($window.location.search);
    $scope.unread = 0;
    $scope.errands = [];
    $scope.current_user = CurrentUser.info;
    $scope.pager = {
        current_page: 1,
        max_pages: 10,
        pages: 1,
        record_count: 0
    };

    $scope.reset_filters = function () {
        if (Object.keys(params).length){
            $scope.query = params;
        } else {
            $scope.query = {
                exec_person: CurrentUser.info,
                show_deleted: false
            }
        }
    };
    $scope.onPageChanged = function () {
        reload_errands($scope.pager.current_page);
    };
    $scope.edit_errand = function (errand) {
        var is_author = CurrentUser.id == errand.set_person.id;
        ErrandModalService.openEdit(errand, is_author)
            .then(function () {
                reload_errands($scope.pager.current_page);
            });
    };
    $scope.delete_errand = function (errand) {
        UserErrand.delete_errand(errand).then(function () {
            reload_errands($scope.pager.current_page);
        });
    };

    var _unread_sbscr = false;
    var reload_errands = function (page) {
        var args = {
            per_page: 10,
            page: page ? page : ($scope.pager.current_page || 1)
        };
        RisarApi.errands.list(args, $scope.query).then(function (result) {
            reset_errands(result);
            if (!_unread_sbscr) {
                _unread_sbscr = true;
                UserErrand.subscribe('unread', function () {
                    tc.start();
                });
            }
        });
    };
    var reset_errands = function (result) {
        if (result) {
            $scope.errands = result.errands;
            $scope.pager.pages = result.total_pages;
            $scope.pager.record_count = result.count;
        }
        $timeout(function(){
            $scope.errands.forEach(function(errand){
                var slices = [errand.progress, 100-errand.progress];
                $('.progress#'+errand.id).sparkline(slices, {type: 'pie', sliceColors: ['green', 'red']} );
            })
        }, 0);
    };

    var tc = new TimeoutCallback(reload_errands, 600);
    $scope.reload_errands = function () {
        tc.start();
    };

    // start
    $scope.reset_filters();
    $scope.$watchCollection('query', function () {
        tc.start();
    });
    UserErrand.subscribe('new:id', function () {
        tc.start();
    });
};


WebMis20.controller('ErrandsListCtrl', ['$scope', '$window', '$timeout', 'RisarApi', 'UserErrand',
    'CurrentUser', 'ErrandModalService', 'TimeoutCallback', ErrandsListCtrl]);