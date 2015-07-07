/**
 * Created by mmalkov on 11.07.14.
 */
var IndexCtrl = function ($scope, $timeout, ApiCalls, WMConfig, Simargl, misPerson) {
    $scope.mode = 0;
    $scope.messages = [];
    Simargl.subscribe('mail', function (result) {
        ApiCalls.wrapper('GET', '/user/api/mail', {
            ids: result.data.id
        }).then(function (messages) {
            $scope.messages = _.first(messages.concat($scope.messages), 10);
        })
    });
    Simargl.when_ready(function () {
        ApiCalls.wrapper('GET', '/user/api/mail').then(function (result) {
            $scope.messages = result;
        });
    });
    $scope.view_mail = function (message) {
        $scope.message = message;
        $scope.mode = 1;
    };
    $scope.view_list = function () {
        $scope.mode = 0;
    }
};
angular.module('WebMis20')
.service('misPerson', function ($q, ApiCalls) {
        var cache = {};
        var promise = function (promise) {
            var d = $q.defer();
            promise.then(function (result) {
                d.resolve(result);
                return result;
            });
            return d.promise;
        };
        this.get = function (id) {
            if (!_.has(cache, id)) {
                cache[id] = ApiCalls.wrapper('GET', '/user/api/persons/{0}'.format(id)).then(function (result) {
                    cache[id] = result;
                    return result;
                });
                return promise(cache[id])
            } else if (_.has(cache[id], 'then')) {
                return promise(cache[id])
            } else {
                var d = $q.defer();
                d.resolve(cache[id]);
                return d.promise;
            }
        }
    });