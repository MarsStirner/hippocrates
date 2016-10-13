'use strict';

var ActiveUsersCtrl = function ($scope, ApiCalls, WMConfig, TimeoutCallback) {
    $scope.users_data = {
        count: 0
    };

    $scope.refresh_data = function () {
        ApiCalls.coldstar(
            'GET', WMConfig.url.coldstar.cas_active_users_count,
            undefined, undefined, { silent: true }
        )
            .addResolve(function (data) {
                $scope.users_data.count = data.count;
            });
    };

    var tc = new TimeoutCallback($scope.refresh_data, 30000);
    $scope.init = function () {
        $scope.refresh_data();
        tc.start_interval();
    };

    $scope.init();
};


WebMis20.controller('ActiveUsersCtrl', ['$scope', 'ApiCalls', 'WMConfig',
    'TimeoutCallback', ActiveUsersCtrl]);