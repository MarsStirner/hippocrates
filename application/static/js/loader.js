'use strict';
// https://github.com/MandarinConLaBarba/angular-examples/blob/master/loading-indicator/index.html
angular.module('WebMis20.LoadingIndicator', []).
    config(function ($httpProvider) {
        $httpProvider.interceptors.push('requestInterceptor');
    }).
    factory('requestInterceptor', function ($q, $rootScope) {
        $rootScope.pendingRequests = 0;
        return {
               'request': function (config) {
                    $rootScope.pendingRequests++;
                    return config || $q.when(config);
                },

                'requestError': function(rejection) {
                    $rootScope.pendingRequests--;
                    return $q.reject(rejection);
                },

                'response': function(response) {
                    $rootScope.pendingRequests--;
                    return response || $q.when(response);
                },

                'responseError': function(rejection) {
                    $rootScope.pendingRequests--;
                    return $q.reject(rejection);
                }
            }
        });