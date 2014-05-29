'use strict';

angular.module('WebMis20.kladrDirectives', ['ui.bootstrap']).
    directive('wmKladrAddress', [function () {
        return {
            restrict: 'E',
            transclude: true,
            scope: {
//                id: '@',
//                name: '@',
//                ngModel: '=',
//                ngRequired: '=',
//                ngDisabled: '='
            },
            controller: function ($scope) {
                var widgets = $scope.widgets = {}

                this.regLocality = function(w) {
                    widgets.locality = w;
                };

            },
            template: '<div ng-transclude>' +
                      '</div>'
        };
    }]).
    directive('wmKladrBaseLayout', [function() {
        return {
            restrict: 'E',
            transclude: true,
            scope: {
                localityModel: '=',
                localityTypeModel: '=',
                streetModel: '=',
                houseModel: '=',
                korpusModel: '=',
                flatModel: '=',
                freeInputModel: '='
            },
            templateUrl: 'kladr-ui.html'
        };
    }]).
    directive('wmKladrLocality', ['$http', function($http) {
        return {
            require: '^wmKladrAddress',
            restrict: 'A',
            replace: true,
            scope: {
                id: '@',
                name: '@',
                model: '='
            },
            controller: function($scope) {
                $scope.getCity = function(val) {
                    return $http.get(url_kladr_get, {
                        params: {
                            city: val
                        }
                    }).then(function(res) {
                        return res.data.result;
                    });
                };
            },
            link: function(scope, elm, attrs, kladrctrl) {
                kladrctrl.regLocality(scope);
            },
            template: '<input type="text" id="[[id]]" name="[[name]]" class="form-control"' +
                      'autocomplete="off" placeholder="Населенный пункт"' +
                      'ng-model="model" typeahead="city for city in getCity($viewValue)"' +
                      'typeahead-wait-ms="1000" typeahead-min-length="2"' +
                      'ng-required="false"/>'
        }
    }])
;