'use strict';

angular.module('WebMis20.directives').
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
                    edit_mode: '&editMode',
                    modelPolicy: '='
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

                    scope.$watch('policyForm.$dirty', function(n, o) {
                        if (n !== o) {
                            scope.modelPolicy.dirty = n;
                        }
                    });

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
    ]).
    directive('wmSocStatus', ['RefBookService',
        function(RefBookService) {
            return {
                restrict: 'E',
                require: '^form',
                scope: {
                    ssClass: '@',
                    idPostfix: '@',
                    modelType: '=',
                    modelBegDate: '=',
                    modelEndDate: '=',
                    modelDocument: '=',
                    edit_mode: '&editMode',
                    modelSocStatus: '='
                },
                link: function(scope, elm, attrs, formCtrl) {
                    scope.socStatusForm = formCtrl;
                    scope.rbSocStatusType = RefBookService.get('rbSocStatusType');

                    scope.$watch('socStatusForm.$dirty', function(n, o) {
                        if (n !== o) {
                            scope.modelSocStatus.dirty = n;
                        }
                    });

                    scope.filter_soc_status = function(s_class) {
                        return function(elem) {
                            var classes_codes = elem.classes.map(function(s_class){
                                return s_class.code;
                                });
                            return classes_codes.indexOf(s_class) != -1;
                        };
                    };

                    // todo: fix? промежуточные модели для ui-select...
                    // вероятно проблема в том, что ui-select в качестве модели нужен объект в скоупе
                    scope.intmd_models = {};
                    scope.intmd_models.type = scope.modelType;
                    scope.$watch('intmd_models.type', function(n, o) {
                        if (n !== o) {
                            scope.modelType = n;
                        }
                    });
                },
                templateUrl: 'socstatus-ui.html'
            };
        }
    ]).
    directive('wmDocument', ['RefBookService',
        function(RefBookService) {
            return {
                restrict: 'E',
                require: '^form',
                scope: {
                    idPostfix: '@',
                    groupCode:'@',
                    modelType: '=',
                    modelSerial: '=',
                    serialValidator: '=',
                    modelNumber: '=',
                    numberValidator: '=',
                    modelBegDate: '=',
                    modelEndDate: '=',
                    modelOrigin: '=',
                    edit_mode: '&editMode',
                    modelDocument: '='
                },
                link: function(scope, elm, attrs, formCtrl) {
                    scope.docForm = formCtrl;
                    scope.rbDocumentType = RefBookService.get('rbDocumentType');
                    scope.rbUFMS = RefBookService.get('rbUFMS');
                    scope.ufmsItems = scope.rbUFMS.objects.map(function(o) {
                        return o.name;
                    });
                    scope.$watch('rbUFMS.objects', function(n, o) {
                        if (n !== o) {
                            scope.ufmsItems = n.map(function(o) {
                                return o.name;
                            });
                        }
                    });

                    scope.$watch('docForm.$dirty', function(n, o) {
                        if (n !== o) {
                            scope.modelDocument.dirty = n;
                        }
                    });

                    scope.filter_document = function(group_code) {
                        return function(elem) {
                            return elem.group.code == group_code;
                        };
                    };

                    // todo: fix? промежуточные модели для ui-select...
                    // вероятно проблема в том, что ui-select в качестве модели нужен объект в скоупе
                    scope.intmd_models = {};
                    scope.intmd_models.type = scope.modelType;
                    scope.intmd_models.origin = scope.modelOrigin;
                    scope.$watch('intmd_models.type', function(n, o) {
                        if (n !== o) {
                            scope.modelType = n;
                        }
                    });

                    scope.$watch('intmd_models.origin', function(n, o) {
                        if (n !== o) {
                            scope.modelOrigin = n;
                        }
                    });
                },
                template:
'<div class="panel panel-default">\
    <div class="panel-body">\
        <div class="row">\
            <div class="form-group col-md-4"\
                 ng-class="{\'has-error\': docForm.$dirty && docForm.doc_type.$invalid}">\
                <label for="doc_type[[idPostfix]]" class="control-label">Тип</label>\
                <ui-select class="form-control" id="doc_type[[idPostfix]]" name="doc_type" theme="select2"\
                           ng-model="intmd_models.type" ng-disabled="!edit_mode()" ng-required="docForm.$dirty">\
                    <ui-select-match placeholder="Тип документа">[[$select.selected.name]]</ui-select-match>\
                    <ui-select-choices repeat="dt in rbDocumentType.objects | filter: filter_document(groupCode) | filter: $select.search">\
                        <div ng-bind-html="dt.name | highlight: $select.search"></div>\
                    </ui-select-choices>\
                </ui-select>\
            </div>\
            <div class="form-group col-md-2"\
                 ng-class="{\'has-error\': (docForm.$dirty && docForm.doc_serial.$invalid) || docForm.doc_serial.$error.required}">\
                <label for="doc_serial[[idPostfix]]" class="control-label">Серия</label>\
                <input type="text" class="form-control" id="doc_serial[[idPostfix]]" name="doc_serial"\
                       autocomplete="off" placeholder="серия" validator-regexp="serialValidator"\
                       ng-model="modelSerial" ng-disabled="!edit_mode()" ng-required="serialValidator && docForm.$dirty"/>\
            </div>\
            <div class="form-group col-md-2"\
                 ng-class="{\'has-error\': docForm.$dirty && docForm.doc_number.$invalid}">\
                <label for="doc_number[[idPostfix]]" class="control-label">Номер</label>\
                <input type="text" class="form-control" id="doc_number[[idPostfix]]" name="doc_number"\
                       autocomplete="off" placeholder="номер" validator-regexp="numberValidator"\
                       ng-model="modelNumber" ng-required="docForm.$dirty" ng-disabled="!edit_mode()"/>\
            </div>\
            <div class="form-group col-md-2"\
                 ng-class="{\'has-error\': docForm.$dirty && docForm.doc_begdate.$invalid}">\
                <label for="doc_begdate[[idPostfix]]" class="control-label">Дата выдачи</label>\
                <wm-date id="doc_begdate[[idPostfix]]" name="doc_begdate"\
                         ng-model="modelBegDate" ng-disabled="!edit_mode()" ng-required="docForm.$dirty">\
                </wm-date>\
            </div>\
            <div class="form-group col-md-2"\
                 ng-class="{\'has-error\': docForm.pol_enddate.$invalid }">\
                <label for="doc_enddate[[idPostfix]]" class="control-label">Действителен до</label>\
                <wm-date id="doc_enddate" name="doc_enddate" ng-model="modelEndDate" ng-disabled="!edit_mode()">\
                </wm-date>\
            </div>\
        </div>\
    \
        <div class="row">\
            <div class="form-group col-md-12"\
                 ng-class="{\'has-error\': docForm.$dirty && docForm.doc_ufms.$invalid}">\
                <label for="doc_ufms[[idPostfix]]" class="control-label">Выдан</label>\
                <div ng-class="form-control" id="doc_ufms[[idPostfix]]" name="doc_ufms"\
                     fs-select="" freetext="true" items="ufmsItems"\
                     ng-disabled="!edit_mode()" ng-required="docForm.$dirty" ng-model="intmd_models.origin">\
                    {{item}}\
                </div>\
                <!-- <select class="form-control" id="doc_ufms[[idPostfix]]" name="doc_ufms"\
                        ng-model="intmd_models.origin"\
                        ng-options="org.name as org.name for org in rbUFMS.objects"\
                        ng-disabled="!edit_mode()" ng-required="docForm.$dirty">\
                </select> -->\
                <!-- TODO: manual-input -->\
            </div>\
        </div>\
    </div>\
</div>'
            };
        }
    ]).
    directive('wmClientBloodType', ['RefBookService',
        function(RefBookService) {
            return {
                restrict: 'E',
                require: '^form',
                scope: {
                    idPostfix: '@',
                    modelType: '=',
                    modelDate: '=',
                    modelPerson: '=',
                    edit_mode: '&editMode',
                    modelBloodType: '='
                },
                link: function(scope, elm, attrs, formCtrl) {
                    scope.cbtForm = formCtrl;
                    scope.rbBloodType = RefBookService.get('rbBloodType');
                    scope.rbPerson = RefBookService.get('vrbPersonWithSpeciality');

                    scope.$watch('cbtForm.$dirty', function(n, o) {
                        if (n !== o) {
                            scope.modelBloodType.dirty = n;
                        }
                    });

                    // todo: fix? промежуточные модели для ui-select...
                    // вероятно проблема в том, что ui-select в качестве модели нужен объект в скоупе
                    scope.intmd_models = {};
                    scope.intmd_models.type = scope.modelType;
                    scope.intmd_models.person = scope.modelPerson;
                    scope.$watch('intmd_models.type', function(n, o) {
                        if (n !== o) {
                            scope.modelType = n;
                        }
                    });
                    scope.$watch('intmd_models.person', function(n, o) {
                        if (n !== o) {
                            scope.modelPerson = n;
                        }
                    });
                },
                template:
'<div class="panel panel-default">\
    <div class="panel-body">\
        <div class="row">\
            <div class="form-group col-md-3"\
                 ng-class="{\'has-error\': cbtForm.$dirty && cbtForm.cbt_date.$invalid}">\
                <label for="cbt_date[[idPostfix]]" class="control-label">Дата установления</label>\
                <wm-date id="cbt_date[[idPostfix]]" name="cbt_date"\
                         ng-model="modelDate" ng-disabled="!edit_mode()" ng-required="cbtForm.$dirty">\
                </wm-date>\
            </div>\
            <div class="form-group col-md-4"\
                 ng-class="{\'has-error\': cbtForm.$dirty && cbtForm.cbt_type.$invalid}">\
                <label for="cbt_type[[idPostfix]]" class="control-label">Тип</label>\
                <ui-select class="form-control" id="cbt_type[[idPostfix]]" name="cbt_type" theme="select2"\
                           ng-model="intmd_models.type" ng-disabled="!edit_mode()" ng-required="cbtForm.$dirty">\
                    <ui-select-match placeholder="Группа крови">[[$select.selected.name]]</ui-select-match>\
                    <ui-select-choices repeat="bt in rbBloodType.objects | filter: $select.search">\
                        <div ng-bind-html="bt.name | highlight: $select.search"></div>\
                    </ui-select-choices>\
                </ui-select>\
            </div>\
            <div class="form-group col-md-5"\
                 ng-class="{\'has-error\': cbtForm.$dirty && cbtForm.cbt_person.$invalid}">\
                <label for="cbt_person[[idPostfix]]" class="control-label">Врач, установивший группу крови</label>\
                <ui-select class="form-control" id="cbt_person[[idPostfix]]" name="cbt_person" theme="select2"\
                           ng-model="intmd_models.person" ng-disabled="!edit_mode()" ng-required="cbtForm.$dirty">\
                    <ui-select-match placeholder="">[[$select.selected.name]]</ui-select-match>\
                    <ui-select-choices repeat="p in rbPerson.objects | filter: $select.search">\
                        <div ng-bind-html="p.name | highlight: $select.search"></div>\
                    </ui-select-choices>\
                </ui-select>\
            </div>\
        </div>\
    </div>\
</div>'
            };
        }
    ]).
    directive('wmClientAllergy', ['RefBookService',
        function(RefBookService) {
            return {
                restrict: 'E',
                require: '^form',
                scope: {
                    idPostfix: '@',
                    type: '@',
                    modelName: '=',
                    modelPower: '=',
                    modelDate: '=',
                    modelNote: '=',
                    edit_mode: '&editMode',
                    modelAllergy: '='
                },
                link: function(scope, elm, attrs, formCtrl) {
                    scope.algForm = formCtrl;
                    scope.rbAllergyPower = RefBookService.get('AllergyPower');

                    scope.$watch('algForm.$dirty', function(n, o) {
                        if (n !== o) {
                            scope.modelAllergy.dirty = n;
                        }
                    });
                },
                template:
'<div class="panel panel-default">\
    <div class="panel-body">\
        <div class="row">\
            <div class="form-group col-md-4"\
                 ng-class="{\'has-error\': algForm.$dirty && algForm.alg_name.$invalid}">\
                <label for="alg_name[[idPostfix]]" class="control-label">[[type === \'allergy\' ? \'Вещество\' : \'Медикамент\']]</label>\
                <input type="text" class="form-control" id="alg_name[[idPostfix]]" name="alg_name"\
                       autocomplete="off" placeholder=""\
                       ng-model="modelName" ng-disabled="!edit_mode()" ng-required="algForm.$dirty"/>\
            </div>\
            <div class="form-group col-md-3"\
                 ng-class="{\'has-error\': algForm.$dirty && algForm.alg_power.$invalid}">\
                <label for="alg_power[[idPostfix]]" class="control-label">Степень</label>\
                <select class="form-control" id="alg_power[[idPostfix]]" name="alg_power"\
                        ng-model="modelPower"\
                        ng-options="pow as pow.name for pow in rbAllergyPower.objects track by pow.id"\
                        ng-disabled="!edit_mode()" ng-required="algForm.$dirty">\
                </select>\
            </div>\
            <div class="form-group col-md-3"\
                 ng-class="{\'has-error\': algForm.$dirty && algForm.alg_date.$invalid}">\
                <label for="alg_date[[idPostfix]]" class="control-label">Дата установления</label>\
                <wm-date id="alg_date[[idPostfix]]" name="alg_date"\
                         ng-model="modelDate" ng-disabled="!edit_mode()" ng-required="algForm.$dirty">\
                </wm-date>\
            </div>\
        </div>\
        <div class="row">\
            <div class="form-group col-md-12">\
                <label for="alg_notes[idPostfix]">Примечание</label>\
                <textarea class="form-control" id="alg_notes" name="alg_notes" rows="2" autocomplete="off"\
                    ng-model="modelNote" ng-disabled="!edit_mode()"></textarea>\
            </div>\
        </div>\
    </div>\
</div>'
            };
        }
    ])
;
