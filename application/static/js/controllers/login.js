var LoginCtrl = function ($scope, $http) {
    $scope.login = null;
    $scope.role = null;
    $scope.roles = [];
    $scope.get_roles = function () {
        if (!$scope.login){
            return null;
        }
        $http.get(url_roles_api + $scope.login)
        .success(function (data) {
            $scope.roles = data.result;
        })
    };
};

WebMis20.controller('LoginCtrl', ['$scope', '$http', LoginCtrl]);