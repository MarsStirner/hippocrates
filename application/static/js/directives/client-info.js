'use strict';

angular.module('WebMis20.directives')
.directive('wmClientInfo', ['$filter', '$window', function ($filter, $window) {
    return {
        restrict: 'E',
        scope: {
            client: '='
        },
        link: function (scope, element, attrs) {
            scope.format_doc = function (docs) {
                return docs && docs.length ? docs[0].doc_text : '&nbsp;';
            };
            scope.format_address = function (address) {
                return address ? address.text_summary : '&nbsp;';
            };
            scope.format_code = function (code) {
                return code ? ('' + code) : '&nbsp;';
            };
            scope.format_birth_date = function (birth_date) {
                return $filter('asDate')(birth_date) || '&nbsp;';
            };
            scope.format_age = function (age) {
                return age || '&nbsp;';
            };
            scope.format_sex = function (sex) {
                return sex || '&nbsp;';
            };
            scope.open_patient_info = function(client_id) {
                $window.open(url_for_patien_info_full + '?client_id=' + client_id, '_blank');
            };
        },
        template:
    '<div class="well well-sm">\
        <div class="row">\
            <div class="col-md-9">\
                <dl class="dl-horizontal novmargin">\
                    <dt ng-if="client.phones.length">Контакты:</dt>\
                        <dd ng-init="showAllPhones=false" ng-if="client.phones.length">\
                            <span ng-repeat="phone in client.phones" ng-show="$first || showAllPhones">[[(!$first ? \', \' : \'\') + phone]]</span>\
                            <a href="javascript:void(0);" ng-click="showAllPhones = !showAllPhones">[[ showAllPhones ? \'[скрыть]\' : \'[ещё]\' ]]</a>\
                        </dd>\
                    <dt>Адрес регистрации:</dt><dd ng-bind-html="format_address(client.reg_address)"></dd>\
                    <dt>Адрес проживания:</dt><dd ng-bind-html="format_address(client.live_address)"></dd>\
                    <dt>Документ:</dt><dd ng-bind-html="format_doc(client.id_docs)"></dd>\
                    <dt>Медицинский полис:</dt>\
                        <dd ng-if="client.compulsory_policy.id" ng-bind="client.compulsory_policy.policy_text"></dd>\
                        <dd ng-repeat="pol in client.voluntary_policies">[[pol.policy_text]]</dd>\
                </dl>\
            </div>\
            <div class="col-md-3">\
                <dl class="dl-horizontal novmargin pull-right">\
                    <dt>Код пациента:</dt><dd ng-bind-html="format_code(client.info.id)"></dd>\
                    <dt>Дата рождения:</dt><dd ng-bind-html="format_birth_date(client.info.birth_date)"></dd>\
                    <dt>Возраст:</dt><dd ng-bind-html="format_age(client.info.age)"></dd>\
                    <dt>Пол:</dt><dd ng-bind-html="format_sex(client.info.sex.name)"></dd>\
                </dl>\
                <button class="btn btn-sm btn-primary pull-right vmargin10" ng-click="open_patient_info(client.info.id)">Детальнее</button>\
            </div>\
        </div>\
    </div>'
    };
}]);