'use strict';

angular.module('WebMis20.directives').
    directive('wmSearchClient', ['$q', '$http', 'WMClientController', function ($q, $http, WMClientController) {
        return {
            restrict: 'E',
            scope: {
                client_id: '=clientId',
                query: '=',
                onSelectCallback: '&onSelect'
            },
            controller: function ($scope) {
                $scope.clear_results = function () {
                    $scope.results = null;
                    $scope.client_id = null;
                };

                $scope.query_clear = function () {
                    $scope.query = '';
                    $scope.clear_results();
                };

                var canceler = $q.defer();
                $scope.perform_search = function () {
                    canceler.resolve();
                    canceler = $q.defer();
                    if ($scope.query) {
                        $http.get(
                            url_client_search, {
                                params: {
                                    q: $scope.query
                                },
                                timeout: canceler.promise
                            }
                        ).success(function (data) {
                            $scope.results = data.result;
                        });
                    }
                };

                $scope.open_new_client = function (client_id) {
                    window.open(url_client_html + '?client_id=' + client_id, '_blank');
                };

                $scope.onClientSelect = function (selected_record) {
                    $scope.client_id = selected_record.info.id;
                    ($scope.onSelectCallback || angular.noop)({
                        selected_client: selected_record
                    });
                };
            },
            link: function (scope, element, attrs) {
                scope.wmClientCtrl = WMClientController;
                scope.results = null;
                scope.allow_register = angular.isDefined(attrs.allowRegister);
            },
            template: '\
<form class="form-horizontal marginal" role="form">\
    <div class="input-group">\
        <span class="input-group-addon"><span class="glyphicon glyphicon-search"></span></span>\
        <input id="search" class="form-control" type="text" ng-model="query" autocomplete="off"\
               ng-change="clear_results()" wm-slow-change="perform_search()"\
               placeholder="Поиск пациента по коду, ФИО, дате рождения, полису или документу, удостоверяющему личность">\
        <span class="input-group-btn">\
            <button class="btn btn-danger" ng-click="query_clear()"><span class="glyphicon glyphicon-remove"></span></button>\
        </span>\
    </div>\
</form>\
<div class="panel panel-default" ng-class="{\'panel-danger\': results.length === 0, \'panel-success\': results.length > 0}">\
    <div class="panel-heading">\
        <div class="row">\
            <div class="col-sm-8">\
                <span ng-if="results.length > 0" class="lead">Результаты поиска</span>\
                <span ng-if="results.length === 0 && query">Пациент не найден в базе данных</span>\
            </div>\
            <div class="col-sm-4 text-right" ng-if="allow_register">\
                <button ng-click="open_new_client(\'new\')" class="btn btn-primary btn-lg">Зарегистрировать пациента</button>\
            </div>\
        </div>\
    </div>\
    <table id="result_tbl" class="table table-condensed table-clickable table-hover" ng-if="results.length > 0">\
        <thead>\
        <tr>\
            <th>Код</th>\
            <th>ФИО</th>\
            <th>Дата рождения</th>\
            <th>Пол</th>\
            <th>Документ</th>\
            <th>СНИЛС</th>\
            <th>Полис ОМС</th>\
            <th>Полис ДМС</th>\
        </tr>\
        </thead>\
        <tbody>\
        <tr ng-repeat="result in results" style="cursor: pointer"\
            ng-click="onClientSelect(result)" ng-class="{\'bg-info text-info\': result.info.id === client_id}">\
            <td ng-bind-html="result.info.id | highlight: query"></td>\
            <td ng-bind-html="result.info.full_name | highlight: query"></td>\
            <td ng-bind-html="result.info.birth_date | asDate | highlight: query"></td>\
            <td ng-bind="result.info.sex.name"></td>\
            <td ng-bind-html="result.id_document.doc_text | highlight: query"></td>\
            <td class="whitespace: nowrap" ng-bind-html="wmClientCtrl.formatSnils(result.info.snils) | highlight: query"></td>\
            <td ng-bind-html="result.compulsory_policy.policy_text | highlight: query"></td>\
            <td><div ng-repeat="policy in result.voluntary_policies"><span ng-bind-html="policy.policy_text | highlight: query"></span></div></td>\
        </tr>\
        </tbody>\
    </table>\
</div>'
        };
    }]);