'use strict';

WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/modal/accounting/contract_edit.html',
        '\
<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title">[[ is_new_contract() ? "Создание договора" : "Редактирование договора" ]]</h4>\
    <span class="text-muted" ng-if="is_new_contract()">пациент [[ client.info.full_name ]], [[ client.info.birth_date | asDate ]]</span>\
</div>\
<div class="modal-body">\
    <ng-form name="contractForm">\
    <div class="row">\
    <div class="col-md-12">\
        <div class="box box-info">\
            <div class="box-body">\
                <div class="row">\
                <div class="col-md-6">\
                    <div class="form-group"\
                        ng-class="{\'has-error\': contractForm.finance.$invalid}">\
                        <label for="finance" class="control-label">Источник финансирования</label>\
                        <rb-select ref-book="rbFinance" ng-model="contract.finance" id="finance" name="finance"\
                            ng-required="true"></rb-select>\
                    </div>\
                    <div class="row">\
                        <div class="col-md-6"\
                            ng-class="{\'has-error\': contractForm.number.$invalid}">\
                            <label for="number" class="control-label">Номер</label>\
                            <input type="text" class="form-control" ng-model="contract.number" id="number" name="number"\
                                ng-required="true">\
                        </div>\
                        <div class="col-md-6"\
                            ng-class="{\'has-error\': contractForm.date.$invalid}">\
                            <label for="date" class="control-label">Дата заключения</label>\
                            <wm-date ng-model="contract.date" id="date" name="date" ng-required="true"></wm-date>\
                        </div>\
                    </div>\
                </div>\
                <div class="col-md-6">\
                    <div class="form-group"\
                        ng-class="{\'has-error\': contractForm.contract_type.$invalid}">\
                        <label for="contract_type" class="control-label">Тип договора</label>\
                        <rb-select ref-book="rbContractType" ng-model="contract.contract_type" id="contract_type"\
                            name="contract_type" ng-required="true"></rb-select>\
                    </div>\
                    <div class="row">\
                        <div class="col-md-6"\
                            ng-class="{\'has-error\': contractForm.beg_date.$invalid}">\
                            <label for="date" class="control-label">Дата начала</label>\
                            <wm-date ng-model="contract.beg_date" id="beg_date" name="beg_date" ng-required="true"></wm-date>\
                        </div>\
                        <div class="col-md-6"\
                            ng-class="{\'has-error\': contractForm.end_date.$invalid}">\
                            <label for="date" class="control-label">Дата окончания</label>\
                            <wm-date ng-model="contract.end_date" id="end_date" name="end_date"></wm-date>\
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
                            append-to-body="true" theme="select2" ng-if="!isPayerCreateMode()">\
                        </ui-select>\
                        <ui-select ng-model="contract.payer.org" ext-select-org theme="select2"\
                            append-to-body="true" placeholder="Выберите организацию" ng-if="isPayerCreateMode() && isPayerLegal()">\
                        </ui-select>\
                        <ui-select ng-model="contract.payer.client" ext-select-client-search theme="select2"\
                            append-to-body="true" placeholder="Выберите клиента" ng-if="isPayerCreateMode() && isPayerIndividual()">\
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
                            append-to-body="true" theme="select2" ng-if="!isRecipientCreateMode()">\
                        </ui-select>\
                        <ui-select ng-model="contract.recipient.org" ext-select-org theme="select2"\
                            append-to-body="true" placeholder="Выберите организацию" ng-if="isRecipientCreateMode() && isRecipientLegal()">\
                        </ui-select>\
                        <ui-select ng-model="contract.recipient.client" ext-select-client-search theme="select2"\
                            append-to-body="true" placeholder="Выберите клиента" ng-if="isRecipientCreateMode() && isRecipientIndividual()">\
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
                    <ui-select ng-model="new_pricelist.pl" ext-select-price-list-search finance="contract.finance"\
                        theme="select2" append-to-body="true" placeholder="Выберите подходящий прайс-лист">\
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
                    <ui-select ng-model="new_contingent.client" ext-select-client-search theme="select2"\
                        append-to-body="true" placeholder="Выберите пациента">\
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
    <pre>[[ contract | json ]]</pre>\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-default" ng-click="$dismiss(\'cancel\')">Отменить</button>\
    <button type="button" class="btn btn-primary" ng-disabled="contractForm.$invalid" ng-click="saveAndClose()">Сохранить</button>\
</div>');
}]);


var ContractModalCtrl = function ($scope, $filter, AccountingService, contract, client) {
    $scope.contract = contract;
    $scope.client = client;
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

    $scope.init = function () {
        if ($scope.is_new_contract()) {
            if (!$scope.contract.payer.ca_type_code || $scope.contract.payer.ca_type_code === 'undefined') {
                $scope.contract.payer.ca_type_code = 'individual';
            }
            if (!$scope.contract.recipient.ca_type_code || $scope.contract.recipient.ca_type_code === 'undefined') {
                $scope.contract.recipient.ca_type_code = 'legal';
            }
        }
    };

    $scope.init();
};


WebMis20.controller('ContractModalCtrl', ['$scope', '$filter', 'AccountingService', ContractModalCtrl]);