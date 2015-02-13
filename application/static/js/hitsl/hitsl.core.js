/**
 * Created by mmalkov on 12.02.15.
 */

angular.module('hitsl.core', [])
.service('CurrentUser', ['$http', function ($http) {
    var self = this;
    $http.get('/api/current-user.json').success(function (data) {
        angular.extend(self, data.result);
    });
    this.get_main_user = function () {
        return this.master || this;
    };
    this.has_right = function () {
        return [].clone.call(arguments).filter(aux.func_in(this.get_user().rights)).length > 0;
    };
    this.has_role = function () {
        return [].clone.call(arguments).filter(aux.func_in(this.roles)).length > 0;
    };
    this.current_role_in = function () {
        return [].clone.call(arguments).has(this.current_role);
    };
}])
.service('MessageBox', ['$modal', function ($modal) {
    return {
        info: function (head, message) {
            var MBController = function ($scope) {
                $scope.head_msg = head;
                $scope.message = message;
            };
            var instance = $modal.open({
                templateUrl: '/WebMis20/modal-MessageBox-info.html',
                controller: MBController
            });
            return instance.result;
        },
        error: function (head, message) {
            var MBController = function ($scope) {
                $scope.head_msg = head;
                $scope.message = message;
            };
            var instance = $modal.open({
                templateUrl: '/WebMis20/modal-MessageBox-error.html',
                controller: MBController
            });
            return instance.result;
        },
        question: function (head, question) {
            var MBController = function ($scope) {
                $scope.head_msg = head;
                $scope.question = question;
            };
            var instance = $modal.open({
                templateUrl: '/WebMis20/modal-MessageBox-question.html',
                controller: MBController
            });
            return instance.result;
        }
    };
}])
.run(['$templateCache', function ($templateCache) {
    $templateCache.put('/WebMis20/modal-MessageBox-info.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
            <h4 class="modal-title">[[head_msg]]</h4>\
        </div>\
        <div class="modal-body">\
            <p ng-bind-html="message"></p>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-success" ng-click="$close()">Ок</button>\
        </div>'
    );
    $templateCache.put('/WebMis20/modal-MessageBox-error.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
            <h4 class="modal-title">[[head_msg]]</h4>\
        </div>\
        <div class="modal-body">\
            <p ng-bind-html="message"></p>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-danger" ng-click="$dismiss()">Ок</button>\
        </div>'
    );
    $templateCache.put('/WebMis20/modal-MessageBox-question.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
            <h4 class="modal-title">[[head_msg]]</h4>\
        </div>\
        <div class="modal-body">\
            <p ng-bind-html="question"></p>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-danger" ng-click="$close(true)">Да</button>\
            <button type="button" class="btn btn-default" ng-click="$dismiss()">Отмена</button>\
        </div>'
    );
}])
.config(function ($httpProvider) {
    $httpProvider.interceptors.push('requestInterceptor');
})
.factory('requestInterceptor', function ($q, $rootScope) {
    // https://github.com/MandarinConLaBarba/angular-examples/blob/master/loading-indicator/index.html
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
})
;

angular.module('hitsl.ui', [
    'ui.bootstrap',          // /static/angular.js/ui-bootstrap-tpls.js
    'ui.select',             // /static/angular-ui-select/select.js
    'ngSanitize',            // /static/js/angular-sanitize.js
    'sf.treeRepeat',         // /static/angular.js/angular-tree-repeat.js
    'ui.mask',               // /static/angular-ui-utils/mask_edited.js
    'formstamp',             // /static/angular-formstamp/formstamp.js
    'mgcrea.ngStrap.affix',  // /static/js/angular-strap.js
    'duScroll',              // /static/angular-scroll/angular-scroll.js
    'rcWizard',
    'nvd3ChartDirectives',
    'legendDirectives'
])
;