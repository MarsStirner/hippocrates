'use strict';

WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/modal/contract_edit.html',
        '\
<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title">[[ is_new_contract() ? "Создание договора" : "Редактирование договора" ]]</h4>\
</div>\
<div class="modal-body">\
    <ng-form name="contractForm">\
    <div class="row">\
    <div class="col-md-12">\
        <div class="box box-info">\
            <div class="box-body">\
                <div class="row">\
                <div class="col-md-6">\
                    <div class="form-group">\
                        <label for="finance">Источник финансирования</label>\
                        <rb-select ref-book="rbFinance" ng-model="contract.finance" id="finance"></rb-select>\
                    </div>\
                    <div class="row">\
                        <div class="col-md-6">\
                            <label for="number">Номер</label>\
                            <input type="text" class="form-control" ng-model="contract.number" id="number">\
                        </div>\
                        <div class="col-md-6">\
                            <label for="date">Дата заключения</label>\
                            <wm-date ng-model="contract.date" id="date"></wm-date>\
                        </div>\
                    </div>\
                </div>\
                <div class="col-md-6">\
                    <div class="form-group">\
                        <label for="contract_type">Тип договора</label>\
                        <rb-select ref-book="rbContractType" ng-model="contract.contract_type" id="contract_type"></rb-select>\
                    </div>\
                    <div class="row">\
                        <div class="col-md-6">\
                            <label for="date">Дата начала</label>\
                            <wm-date ng-model="contract.beg_date" id="beg_date"></wm-date>\
                        </div>\
                        <div class="col-md-6">\
                            <label for="date">Дата окончания</label>\
                            <wm-date ng-model="contract.end_date" id="end_date"></wm-date>\
                        </div>\
                    </div>\
                </div>\
                </div>\
                <div class="row">\
                <div class=col-md-12>\
                    <label for="resolution">Основание</label>\
                    <textarea ng-model="contract.resolution" rows="1" class="form-control" id="resolution"></textarea>\
                </div>\
                </div>\
            </div>\
        </div>\
    </div>\
    </div>\
    <div class="row">\
    <div class="col-md-12">\
        <div class="box box-info">\
            <div class="box-header with-border">\
                <h3 class="box-title">Стороны договора</h3>\
            </div>\
            <div class="box-body">\
                <div class="row">\
                <div class=col-md-6 col-sm-12>\
                    <div class="text-center vbmargin10">\
                        <span style="text-decoration: underline; font-size: larger;" ng-show="!isPayerCreateMode()">Выбор существующего</span>\
                        <a href="javascript:void(0);" ng-click="switchPayerCreateMode()" ng-show="!isPayerCreateMode()" class="lmargin20">Добавить нового</a>\
                        <a href="javascript:void(0);" ng-click="switchPayerCreateMode()" ng-show="isPayerCreateMode()">Выбрать существующего</a>\
                        <span style="text-decoration: underline; font-size: larger;" class="lmargin20" ng-show="isPayerCreateMode()">Создание нового</span>\
                    </div>\
                    <div class="form-group">\
                        <label>Заказчик (Плательщик)</label>\
                        <span>\
                            <label class="lmargin20" style="font-weight: normal">\
                            <input type="radio" ng-model="contract.payer.ca_type_code" ng-value="\'individual\'">Физ. лицо</label>\
                            <label class="lmargin20" style="font-weight: normal">\
                            <input type="radio" ng-model="contract.payer.ca_type_code" ng-value="\'legal\'">Юр. лицо</label>\
                        </span>\
                        <ui-select ng-model="contract.payer" ext-select-contragent-search ca-type-code="[[contract.payer.ca_type_code]]"\
                            theme="bootstrap" ng-show="!isPayerCreateMode()">\
                        </ui-select>\
                        <ui-select ng-model="contract.payer.org" ext-select-org theme="bootstrap"\
                            placeholder="Выберите организацию" ng-show="isPayerCreateMode() && isPayerLegal()">\
                        </ui-select>\
                        <ui-select ng-model="contract.payer.client" ext-select-client-search theme="bootstrap"\
                            placeholder="Выберите клиента" ng-show="isPayerCreateMode() && isPayerIndividual()">\
                        </ui-select>\
                    </div>\
                </div>\
                <div class=col-md-6 col-sm-12>\
                    <div class="text-center vbmargin10">\
                        <span style="text-decoration: underline; font-size: larger;" ng-show="!isRecipientCreateMode()">Выбор существующего</span>\
                        <a href="javascript:void(0);" ng-click="switchRecipientCreateMode()" ng-show="!isRecipientCreateMode()" class="lmargin20">Добавить нового</a>\
                        <a href="javascript:void(0);" ng-click="switchRecipientCreateMode()" ng-show="isRecipientCreateMode()">Выбрать существующего</a>\
                        <span style="text-decoration: underline; font-size: larger;" class="lmargin20" ng-show="isRecipientCreateMode()">Создание нового</span>\
                    </div>\
                    <div class="form-group">\
                        <label>Исполнитель (Получатель)</label>\
                        <span>\
                            <label class="lmargin20" style="font-weight: normal">\
                            <input type="radio" ng-model="contract.recipient.ca_type_code" ng-value="\'individual\'">Физ. лицо</label>\
                            <label class="lmargin20" style="font-weight: normal">\
                            <input type="radio" ng-model="contract.recipient.ca_type_code" ng-value="\'legal\'">Юр. лицо</label>\
                        </span>\
                        <ui-select ng-model="contract.recipient" ext-select-contragent-search ca-type-code="[[contract.recipient.ca_type_code]]"\
                            theme="bootstrap" ng-show="!isRecipientCreateMode()">\
                        </ui-select>\
                        <ui-select ng-model="contract.recipient.org" ext-select-org theme="bootstrap"\
                            placeholder="Выберите организацию" ng-show="isRecipientCreateMode() && isRecipientLegal()">\
                        </ui-select>\
                        <ui-select ng-model="contract.recipient.client" ext-select-client-search theme="bootstrap"\
                            placeholder="Выберите клиента" ng-show="isRecipientCreateMode() && isRecipientIndividual()">\
                        </ui-select>\
                    </div>\
                </div>\
                </div>\
            </div>\
        </div>\
    </div>\
    </div>\
    <div class="row">\
    <div class="col-md-12">\
        <div class="box box-info">\
            <div class="box-header with-border">\
                <h3 class="box-title">Прайс листы</h3>\
            </div>\
            <div class="box-body">\
                <ul class="list-group">\
                    <li ng-repeat="pl in contract.pricelist_list | flt_not_deleted" class="list-group-item">\
                        <span ng-bind="formatPriceListDescr(pl)"></span>\
                        <span class="fa fa-remove text-danger cursor-pointer pull-right"\
                            ng-click="removePricelist($index)" title="Удалить"></span>\
                    </li>\
                </ul>\
            </div>\
            <div class="box-footer">\
                <div class="row">\
                <div class="col-md-9">\
                    <ui-select ng-model="new_pricelist.pl" ext-select-price-list-search finance="contract.finance" theme="bootstrap"\
                        placeholder="Выберите подходящий прайс-лист">\
                    </ui-select>\
                </div>\
                <div class="col-md-3">\
                    <button type="button" class="btn btn-sm btn-primary pull-right" ng-click="addNewPricelist()"\
                        ng-disabled="btnAddPricelistDisabled()">\
                        <span class="fa fa-plus"> Добавить прайс-лист</span>\
                    </button>\
                </div>\
                </div>\
            </div>\
        </div>\
    </div>\
    </div>\
    <div class="row">\
    <div class="col-md-12">\
        <div class="box box-info">\
            <div class="box-header with-border">\
                <h3 class="box-title">Потребители услуг (Контингент)</h3>\
            </div>\
            <div class="box-body">\
                <ul class="list-group">\
                    <li ng-repeat="cont in contract.contingent_list | flt_not_deleted" class="list-group-item">\
                        <span><a ng-href="[[getClientInfoUrl(cont.client.id)]]" target="_blank">[[ cont.client.full_name ]], [[ cont.client.birth_date | asDate ]]</a></span>\
                        <span class="fa fa-remove text-danger cursor-pointer pull-right"\
                            ng-click="removeContingent($index)" title="Удалить"></span>\
                    </li>\
                </ul>\
            </div>\
            <div class="box-footer">\
                <div class="row">\
                <div class="col-md-9">\
                    <ui-select ng-model="new_contingent.client" ext-select-client-search theme="bootstrap"\
                        placeholder="Выберите пациента">\
                    </ui-select>\
                </div>\
                <div class="col-md-3">\
                    <button type="button" class="btn btn-sm btn-primary pull-right" ng-click="addNewContingent()"\
                        ng-disabled="btnAddContingentDisabled()">\
                        <span class="fa fa-plus"> Добавить пациента</span>\
                    </button>\
                </div>\
                </div>\
            </div>\
        </div>\
    </div>\
    </div>\
    </ng-form>\
    <!-- <pre>[[ contract | json ]]</pre> -->\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-default" ng-click="$dismiss(\'cancel\')">Отменить</button>\
    <button type="button" class="btn btn-primary" ng-click="saveAndClose()">Сохранить</button>\
</div>');
}]);


var ContractModalCtrl = function ($scope, $filter, AccountingService, contract) {
    $scope.contract = contract;
    $scope.ca_params = {
        payer_create_mode: false,
        recipient_create_mode: false
    };
    $scope.new_contingent = {
        client: null
    };
    $scope.new_pricelist = {
        pl: null
    };

    $scope.saveAndClose = function () {
        $scope.save_contract().then(function (upd_contract) {
            $scope.$close({
                status: 'ok',
                contract: upd_contract
            });
        });
    };
    $scope.save_contract = function () {
        return AccountingService.save_contract(
            $scope.contract
        );
    };
    $scope.is_new_contract = function () {
        return !$scope.contract.id;
    };

    // contragents
    function clearLegalPayer () {
        $scope.contract.payer.org = null;
        $scope.contract.payer.short_descr = $scope.contract.payer.full_descr = null;
    }
    function clearIndividualPayer () {
        $scope.contract.payer.client = null;
        $scope.contract.payer.short_descr = $scope.contract.payer.full_descr = null;
    }
    $scope.isPayerIndividual = function () {
        return $scope.contract.payer.ca_type_code === 'individual';
    };
    $scope.isPayerLegal = function () {
        return $scope.contract.payer.ca_type_code === 'legal';
    };
    $scope.isPayerCreateMode = function () {
        return $scope.ca_params.payer_create_mode;
    };
    $scope.switchPayerCreateMode = function () {
        $scope.ca_params.payer_create_mode = !$scope.ca_params.payer_create_mode;
        clearLegalPayer();
        clearIndividualPayer();
        $scope.contract.payer.id = null;
    };
    $scope.$watch('contract.payer.ca_type_code', function (newVal, oldVal) {
        if (newVal === oldVal) return;
        if (!$scope.isPayerCreateMode()) {
            clearLegalPayer();
            clearIndividualPayer();
        } else {
            if (newVal === 'individual') clearLegalPayer();
            else if (newVal === 'legal') clearIndividualPayer();
        }
    });
    function clearLegalRecipient () {
        $scope.contract.recipient.org = null;
        $scope.contract.recipient.short_descr = $scope.contract.recipient.full_descr = null;
    }
    function clearIndividualRecipient () {
        $scope.contract.recipient.client = null;
        $scope.contract.recipient.short_descr = $scope.contract.recipient.full_descr = null;
    }
    $scope.isRecipientIndividual = function () {
        return $scope.contract.recipient.ca_type_code === 'individual';
    };
    $scope.isRecipientLegal = function () {
        return $scope.contract.recipient.ca_type_code === 'legal';
    };
    $scope.isRecipientCreateMode = function () {
        return $scope.ca_params.recipient_create_mode;
    };
    $scope.switchRecipientCreateMode = function () {
        $scope.ca_params.recipient_create_mode = !$scope.ca_params.recipient_create_mode;
        clearLegalRecipient();
        clearIndividualRecipient();
        $scope.contract.recipient.id = null;
    };
    $scope.$watch('contract.recipient.ca_type_code', function (newVal, oldVal) {
        if (newVal === oldVal) return;
        if (!$scope.isRecipientCreateMode()) {
            clearLegalRecipient();
            clearIndividualRecipient();
        } else {
            if (newVal === 'individual') clearLegalRecipient();
            else if (newVal === 'legal') clearIndividualRecipient();
        }
    });

    // pricelist
    $scope.formatPriceListDescr = function (pl) {
        return '{0}. {1| }{2} ({3}), с {4} по {5}'.formatNonEmpty(
            pl.id, pl.code, pl.name, pl.finance.name,
            $filter('asDate')(pl.beg_date), $filter('asDate')(pl.end_date)
        );
    };
    $scope.addNewPricelist = function () {
        $scope.contract.pricelist_list.push($scope.new_pricelist.pl);
        $scope.new_pricelist.pl = null;
    };
    $scope.removePricelist = function (idx) {
        $scope.contract.pricelist_list.splice(idx, 1);
    };
    $scope.btnAddPricelistDisabled = function () {
        return !safe_traverse($scope.new_pricelist, ['pl', 'id']);
    };

    // contingent
    $scope.addNewContingent = function () {
        AccountingService.get_new_contingent({
            contract_id: $scope.contract.id
        })
            .then(function (new_cont) {
                new_cont.client = $scope.new_contingent.client;
                $scope.contract.contingent_list.push(new_cont);
                $scope.new_contingent.client = null;
            });
    };
    $scope.removeContingent = function (idx) {
        var cont = $scope.contract.contingent_list[idx];
        if (cont.id) {
            cont.deleted = 1;
        } else {
            $scope.contract.contingent_list.splice(idx, 1);
        }
    };
    $scope.btnAddContingentDisabled = function () {
        return !safe_traverse($scope.new_contingent, ['client', 'id']);
    };
    $scope.getClientInfoUrl = function (client_id) {
        return url_for_patien_info_full + '?client_id=' + client_id;
    };

    $scope.init = function () { };

    $scope.init();
};


WebMis20.controller('ContractModalCtrl', ['$scope', '$filter', 'AccountingService', ContractModalCtrl]);