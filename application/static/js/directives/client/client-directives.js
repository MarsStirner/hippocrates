'use strict';

angular.module('WebMis20.directives').
//    directive('wmPolicyWrapper', [function() {
//        return {
//            restrict: 'E',
////            transclude: true,
//            scope: {},
//            controller: function($scope) {
//                $scope.edit = {
//                    activated: false
//                };
//            },
//            link: function(scope, elm, atts) {
//                scope.edita = {
//                    activated: false
//                };
//            }
////            template: '<div><div ng-transclude></div></div>'
//        };
//    }]).
    directive('wmPolicy', ['RefBookService',
        function(RefBookService) {
            return {
                restrict: 'E',
                require: '^form',
                scope: {
                    pType: '@',
                    idPostfix: '@',
                    modelType: '=',
                    modelSerial: '=',
                    serialValidator: '=',
                    modelNumber: '=',
                    numberValidator: '=',
                    modelBegDate: '=',
                    modelEndDate: '=',
                    modelInsurer: '=',
                    edit_mode: '&editMode'
                },
                link: function(scope, elm, attrs, formCtrl) {
                    scope.policyForm = formCtrl;
                    scope.rbPolicyType = RefBookService.get('rbPolicyType');
                    scope.rbOrganisation = RefBookService.get('Organisation');
                    var cpolicy_codes = ['cmiOld', 'cmiTmp', 'cmiCommonPaper', 'cmiCommonElectron',
                        'cmiUEC', 'cmiFnkcIndustrial', 'cmiFnkcLocal', '1', '2'];
                    var vpolicy_codes = ['vmi', '3'];
                    scope.filter_policy = function(type) {
                        return function(elem) {
                            var codes;
                            if (type === '0') codes = cpolicy_codes;
                            else codes = vpolicy_codes;
                            return codes.indexOf(elem.code) != -1;
                        };
                    };

                    // todo: fix? промежуточные модели для ui-select...
                    // вероятно проблема в том, что ui-select в качестве модели нужен объект в скоупе
                    scope.intmd_models = {};
                    scope.intmd_models.type = scope.modelType;
                    scope.intmd_models.insurer = scope.modelInsurer;
                    scope.$watch('intmd_models.type', function(n, o) {
                        if (n !== o) {
                            scope.modelType = n;
                        }
                    });
                    scope.$watch('intmd_models.insurer', function(n, o) {
                        if (n !== o) {
                            scope.modelInsurer = n;
                        }
                    });
                },
                templateUrl: 'policy-ui.html'
            };
        }
    ])
;