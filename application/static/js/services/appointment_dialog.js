/**
 * Created by mmalkov on 11.07.14.
 */
angular.module('WebMis20.services.dialogs', ['WebMis20.services', 'ui.bootstrap'])
.service('WMAppointmentDialog', function ($modal, WMAppointment) {
    return {
        cancel: function (ticket, person, client_id) {
            return $modal.open({
                template:
                    '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                        <button type="button" class="close" ng-click="cancel()">&times;</button>\
                        <h4 class="modal-title" id="myModalLabel">Отменить запись на приём?</h4>\
                    </div>\
                    <div class="modal-body" ng-if="!error">\
                        Отменить <span ng-if="ticket.attendance_type.code == \'CITO\'">экстренную</span>\
                        <span ng-if="ticket.attendance_type.code == \'extra\'">сверхплановую</span>\
                            запись на приём к <strong>[[ person.name ]]</strong> ([[ person.speciality.name ]])\
                        <span ng-if="ticket.attendance_type.code == \'planned\'">на <strong>[[ ticket.begDateTime | asMomentFormat:\'HH:mm DD.MM.YY\' ]]</strong></span>?\
                    </div>\
                    <div class="modal-body" ng-if="error">\
                        [[ error.text ]]\
                    </div>\
                    <div class="modal-footer">\
                        <button type="button" class="btn btn-success" ng-click="accept()" ng-disabled="error">Отменить запись</button>\
                        <button type="button" class="btn btn-danger" ng-click="cancel()">Не отменять запись</button>\
                    </div>',
                controller: function ($scope, $http, $modalInstance) {
                    $scope.ticket = ticket;
                    $scope.person = person;
                    $scope.error = null;
                    $scope.accept = function () {
                        WMAppointment.cancel(ticket, client_id).success(function (data) {
                            $modalInstance.close(data);
                        }).error(function () {
                            $scope.error = {
                                text: 'Ошибка при отмене записи на приём'
                            }
                        });
                    };
                    $scope.cancel = function () {
                        $modalInstance.dismiss('cancel');
                    };
                }
            });
        },
        make: function (ticket, person, client_id, client_name) {
            var size = client_id ? '' : 'lg';
            return $modal.open({
                template:
                    '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                        <button type="button" class="close" ng-click="cancel()">&times;</button>\
                        <h4 class="modal-title" id="myModalLabel">Записать на приём?</h4>\
                    </div>\
                    <div class="modal-body modal-scrollable">\
                        <div id="page1" ng-show="page === 0">\
                            <wm-search-client client-id="client.client_id" query="client_query"\
                                on-select="select_client(selected_client)"></wm-search-client>\
                        </div>\
                        <div id="page2" ng-show="page === 1">\
                            <dl class="dl-horizontal novmargin">\
                              <dt>Врач:</dt><dd>[[ person.name ]] ([[ person.speciality.name ]])</dd>\
                              <dt>Время приёма:</dt>\
                              <dd>\
                                <span ng-if="ticket.attendance_type.code == \'planned\'">[[ ticket.begDateTime | asMomentFormat:\'HH:mm DD.MM.YY\' ]]</span>\
                                <span ng-if="ticket.attendance_type.code == \'CITO\'"><strong>экстренно</strong></span>\
                                <span ng-if="ticket.attendance_type.code == \'extra\'"><strong>сверх плана</strong></span>\
                              </dd>\
                              <dt ng-show="client_name">Пациент:</dt><dd ng-show="client_name">[[ client_name ]]</dd>\
                            </dl>\
                        </div>\
                    </div>\
                    <div class="modal-footer">\
                        <button type="button" class="btn btn-primary" ng-click="next_page()" ng-show="page === 0" ng-disabled="!client.client_id">Далее</button>\
                        <button type="button" class="btn btn-default" ng-click="prev_page()" ng-show="page === 1">Назад</button>\
                        <button type="button" class="btn btn-success" ng-click="accept()" ng-show="page === 1">Записать</button>\
                        <button type="button" class="btn btn-danger" ng-click="cancel()">Не записывать</button>\
                    </div>',
                controller: function ($scope, $http, $modalInstance) {
                    $scope.ticket = ticket;
                    $scope.person = person;
                    $scope.client = {
                        client_id: client_id
                    };
                    $scope.client_name = client_name;
                    $scope.page = client_id ? 1 : 0;
                    $scope.client_query = '';

                    $scope.select_client = function (selected_client) {
                        $scope.client_name = selected_client.info.full_name;
                    };
                    $scope.next_page = function () {
                        $scope.page++;
                    };
                    $scope.prev_page = function () {
                        $scope.page--;
                    };
                    $scope.accept = function () {
                        WMAppointment.make(ticket, $scope.client.client_id).success(function (data) {
                            $modalInstance.close(data);
                        }).error(function () {
                            $scope.error = {
                                text: 'Ошибка при записи на приём'
                            };
                        });
                    };
                    $scope.cancel = function () {
                        $modalInstance.dismiss('cancel');
                    };
                },
                size: size
            });
        }
    }
});
