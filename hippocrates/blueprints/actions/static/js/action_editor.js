/**
 * Created by mmalkov on 14.07.14.
 */
var ActionEditorCtrl = function ($scope, $window, $modal, $q, $http, $document, WMAction, PrintingService, PrintingDialog,
        RefBookService, MessageBox, NotificationService, WMConfig, AccountingService, PatientActionsModalService, CurrentUser) {
    var params = aux.getQueryParams(location.search);
    $scope.ps = new PrintingService("action");
    $scope.ps_resolve = function () {
        return {
            action_id: $scope.action.id
        }
    };
    $scope.ActionStatus = RefBookService.get('ActionStatus');
    $scope.rbDiagnosisType = RefBookService.get('rbDiagnosisTypeN');

    $scope.action_id = params.action_id;
    $scope.action = new WMAction();
    $scope.locker_person = null;

    // Здесь начинается хрень
    //var user_activity_events = 'mousemove keydown DOMMouseScroll mousewheel mousedown touchstart touchmove scroll',
    //    on_user_activity = _.throttle(_autosave, 10000);
    //function _autosave () {
    //    $scope.action.autosave();
    //}
    //function _set_tracking(on) {
    //    $document.find('body')[(on)?'on':'off'](user_activity_events, on_user_activity)
    //}
    //_set_tracking(true);
    // Здесь она типа заканчивается

    $scope.init = function () {
        if (params.action_id) {
            WMAction.get(params.action_id).then(function (action) {
                $scope.action = action;
                update_print_templates(action.action_type.context_name);
                process_printing();
                return action;
            }).then(function (action) {
                if (!$scope.action.ro) {
                    $scope.$watch('action.lock.success', function (newVal, oldVal) {
                        if (!newVal && $scope.action.lock.locker) {
                            var locker_id = $scope.action.lock.locker;
                            $http.get(WMConfig.url.schedule.person + locker_id)
                                .success(function (data) {
                                    $scope.locker_person = data.result;
                                })
                        } else if (newVal) {
                            $scope.locker_person = null;
                        }
                    });
                }
            });
        } else if (params.event_id && params.action_type_id) {
            WMAction.get_new(
                params.event_id,
                params.action_type_id
            ).then(function (action) {
                $scope.action = action;
                update_print_templates(action.action_type.context_name);

                if (params.price_list_item_id && params.service_kind_id) {
                    AccountingService.get_service(undefined, {
                        price_list_item_id: params.price_list_item_id,
                        service_kind_id: params.service_kind_id,
                        event_id: params.event_id,
                        serviced_entity_from_search: {
                            action_type_id: params.action_type_id
                        }
                    }).then(function (new_service) {
                        $scope.action.service = new_service;
                    });
                }
            });
        }
    };

    function update_print_templates (context_name) {
        $scope.ps.set_context(context_name);
    }
    function process_printing() {
        if ($window.sessionStorage.getItem('open_action_print_dlg')) {
            $window.sessionStorage.removeItem('open_action_print_dlg');
            PrintingDialog.open($scope.ps, $scope.ps_resolve());
        }
    }

    $scope.isActionLockedByOtherPerson = function () {
        return Boolean($scope.locker_person);
    };
    $scope.on_status_changed = function () {
        if ($scope.action.status.code === 'finished') {
            if (!$scope.action.end_date) {
                $scope.action.end_date = new Date();
            }
        } else {
            $scope.action.end_date = null;
        }
    };
    $scope.on_enddate_changed = function () {
        if ($scope.action.end_date) {
            if ($scope.action.status.code !== 'finished') {
                $scope.action.status = $scope.ActionStatus.get_by_code('finished');
            }
        } else {
            $scope.action.status = $scope.ActionStatus.get_by_code('started');
        }
    };

    $scope.save_action = function (need_to_print) {
        var was_new = $scope.action.is_new();
        return $scope.check_can_save_action()
        .then(function () {
            if (was_new && need_to_print) { $window.sessionStorage.setItem('open_action_print_dlg', true) }
            return $scope.action.save()
                .then(function (action) {
                    if (was_new) {
                        $window.open(WMConfig.url.actions.action_html + '?action_id=' + action.id, '_self');
                    } else {
                        NotificationService.notify(
                            200,
                            'Успешно сохранено',
                            'success',
                            5000
                        );
                    }
                }, function (result) {
                    NotificationService.notify(
                        500,
                        'Ошибка сохранения, свяжитесь с администратором',
                        'danger'
                    );
                });
        }, function (result) {
            var deferred = $q.defer();
            if (need_to_print) {
                if (!result.silent) {
                    MessageBox.info('Невозможно сохранить действие', result.message)
                    .then(function () {
                        deferred.resolve();
                    });
                } else {
                    deferred.resolve();
                }
            } else {
                return MessageBox.error('Невозможно сохранить действие', result.message);
            }
            return deferred.promise;
        });
    };
    $scope.sign_n_save_action = function () {
        $scope.action.person = CurrentUser.info;
        $scope.save_action();
    };
    $scope.cancel = function () {
        $scope.action.discard().then($window.close, $window.close);
    };
    $scope.check_can_save_action = function () {
        function check_diagnosis (action){
            var deferred = $q.defer();
            var diags_without_result = action.diagnoses.filter(function(diag){
                for (var diag_type_code in diag.diagnosis_types){
                    var diag_type = $scope.rbDiagnosisType.get_by_code(diag_type_code);
                    if (diag.diagnosis_types[diag_type_code].code != 'associated' && diag_type.require_result && !diag.diagnostic.ache_result){
                        return true
                    }
                }
                return false
            })
            if (action.status.code === 'finished' && diags_without_result.length) {
                deferred.reject({
                    silent: false,
                    message: 'Необходимо указать результат для дагнозов.'
                });
            }
            deferred.resolve();
            return deferred.promise;
        }

        var deferred = $q.defer();
        if ($scope.action.readonly) {
            deferred.reject({
                silent: true,
                message: 'Действие открыто в режиме чтения'
            });
        } else {
            return check_diagnosis($scope.action);
        }
        return deferred.promise;
    };
    $scope.openPatientActions = function () {
        PatientActionsModalService.open($scope.action.client.id);
    };
    $scope.is_med_doc = function () { return $scope.action.action_type && $scope.action.action_type.class === 0; };
    $scope.is_diag_lab = function () { return $scope.action.action_type && $scope.action.action_type.class === 1; };
    $scope.is_treatment = function () { return $scope.action.action_type && $scope.action.action_type.class === 2; };

    $scope.template_save = function () {
        var action_type_id = $scope.action.action_type_id || $scope.action.action_type.id;
        function process_modal() {
            $modal.open({
                templateUrl: '_action_template_save_model.html',
                controller: ActionTemplateController,
                size: 'lg',
                resolve: {
                    args: function () {
                        return {
                            action_id: $scope.action_id,
                            action_type_id: action_type_id,
                            mode: 'save'
                        }
                    }
                },
                backdrop : 'static'
            })
        }
        if ($scope.action.readonly) {
            process_modal()
        } else {
            $scope.save_action(false).then(process_modal);
        }
    };
    $scope.template_load = function () {
        $modal.open({
            templateUrl: '_action_template_load_model.html',
            controller: ActionTemplateController,
            backdrop : 'static',
            size: 'lg',
            resolve: {
                args: function () {
                    return {
                        action_id: $scope.action_id,
                        action_type_id: $scope.action.action_type_id || $scope.action.action_type.id,
                        mode: 'load'
                    }
                }
            }
        }).result.then(function (action_id) {
            WMAction.get(action_id).then(function (src) {
                $scope.action.merge_template(src)
            });
        });
    };
    $scope.template_prev = function () {
        WMAction.previous($scope.action).then(function (action) {
            $scope.action.merge_template(action);
        })
    };

    $q.all([$scope.ActionStatus.loading, $scope.rbDiagnosisType.loading]).then($scope.init);
};
var ActionTemplateController = function ($scope, $modalInstance, $http, FlatTree, SelectAll, args) {
    $scope.model = {
        id: null,
        gid: null,
        name: '',
        code: '',
        owner: false,
        speciality: false,
        action_id: args.action_id,
        parent: null
    };
    $scope.flat_tree = null;
    $scope.hier_tree = new FlatTree('gid');
    $scope.tree = {};
    $scope.selected = null;
    var sas = $scope.sas = new SelectAll([]);
    var filter_mode = (args.mode === 'save') ? purge_leafs : purge_nodes;
    function load_tree () {
        return $http.get('/actions/api/templates/{0}'.format(args.action_type_id)).then(function (response) {
            $scope.flat_tree = response.data.result;
            rebuild_tree();
            $scope.select($scope.tree);
            return response;
        })
    }
    function rebuild_tree () {
        $scope.hier_tree.set_array($scope.flat_tree).filter(filter_mode);
        var tree = $scope.hier_tree.render(make_tree_object);
        tree.children = tree.root.children;
        sas.setSource(tree.masterDict.keys().map(function (key) {
            var result = parseInt(key);
            if (isNaN(result)) { return key } else { return result }
        }));
        sas.selectAll();
        $scope.tree = tree.root;
    }
    function purge_nodes (node, id_dict) {
        return !!node.aid;
    }
    function purge_leafs (node, id_dict) {
        return !node.aid;
    }
    function make_tree_object(item, is_node) {
        if (item === null) {
            var result = {};
            result.parent_id = null;
            result.id = 'root';
            result.children = [];
            result.is_node = true;
            result.name = 'Корень';
            return result
        }
        return angular.extend(item, {is_node: is_node || !item.aid});
    }
    $scope.select = function (item) {
        $scope.model.parent = item;
    };
    $scope.save_new = function () {
        var model = $scope.model;
        var parent_id = (model.parent.id === 'root') ? null : model.parent.id;
        $http.put(
            '/actions/api/templates/{0}'.format(args.action_type_id), {
                id: null,
                gid: parent_id,
                name: model.name,
                aid: parseInt(args.action_id)
            }
        ).then($scope.$close);
    };
    $scope.create_group = function () {
        var model = $scope.model;
        var parent_id = (model.parent.id === 'root') ? null : model.parent.id;
        $http.put(
            '/actions/api/templates/{0}'.format(args.action_type_id), {
                id: null,
                gid: parent_id,
                name: model.name,
                aid: null
            }
        ).then(function (response) {
            var result = response.data.result;
            $scope.flat_tree.push(result);
            rebuild_tree();
            $scope.model = {
                id: null,
                gid: null,
                name: '',
                code: '',
                owner: false,
                speciality: false,
                action_id: args.action_id,
                parent: result
            };
        })
    };
    load_tree();
};

WebMis20.controller('ActionEditorCtrl', ['$scope', '$window', '$modal', '$q', '$http', '$document', 'WMAction', 'PrintingService',
    'PrintingDialog', 'RefBookService', 'MessageBox', 'NotificationService',
    'WMConfig', 'AccountingService', 'PatientActionsModalService', 'CurrentUser', ActionEditorCtrl]);

WebMis20.factory('WMAction', ['$q', 'ApiCalls', 'EzekielLock', 'WMConfig', function ($q, ApiCalls, EzekielLock, WMConfig) {
    // FIXME: На данный момент это ломает функциональность действий, но пока пофиг.
    var template_fields = ['set_person', 'note', 'office', 'amount', 'uet', 'pay_status', 'account', 'is_urgent'];
    var excluded_template_fields = ['status', 'direction_date', 'beg_date', 'end_date', 'planned_end_date', 'person', 'coord_date'];
    var fields = ['id', 'event_id', 'client', 'prescriptions', 'diagnoses', 'service'].concat(excluded_template_fields, template_fields);
    var Action = function () {
        this.action = {};
        this.layout = {};
        this.action_columns = {};
        this.properties_by_id = {};
        this.properties_by_code = {};
        this.ro = true;
        this.lock = null;
        this.readonly = true;
    };
    /* Приватные методы */
    function merge_template_fields (self, source) {
        /* Перетягивает основные атрибуты действия */
        _.extend(self, _.pick(source, template_fields));
    }
    function merge_fields (self, source) {
        /* Перетягивает основные атрибуты действия */
        _.extend(self, _.pick(source, fields));
    }
    function merge_meta (self, source) {
        /* Перетягивает статические метаданные действия */
        self.action_type = source.action_type;
        self.layout = source.layout;
        // ro - атрибут нашего представления действия, обозначающий, разрешено ли нам вообще это действие редактировать
        // в дальнейшем атрибут readonly определяет разрешения на редактирование с учётом блокировки.
        self.ro = source.ro;
        self.bak_lab_info = source.bak_lab_info;
        self.event_info = source.event_info;
    }
    function merge_properties (self, source) {
        /* Перетягивает свойства действия */
        self.properties = source.properties.clone();
    }
    function process_properties (self, source) {
        self.action_columns = {
            assignable: false,
            unit: false
        };
        self.properties_by_id = {};
        self.properties_by_code = {};

        _.forEach(source.properties, function (item) {
            self.action_columns.assignable |= item.type.is_assignable;
            self.action_columns.unit |= item.type.unit;

            self.properties_by_id[item.type.id] = item;

            if (item.type.code) {
                self.properties_by_code[item.type.code] = item;
            }
        });
    }
    /* class methods */
    Action.get = function (id) {
        /* Получение экземпляра (в обёртке $q.defer().promise) Action по id */
        return ApiCalls.wrapper('GET', WMConfig.url.actions.action_get.format(id)).then(
            function (result) {
                var action = (new Action()).merge(result, true);
                if (!arguments[1] && !action.ro) {
                    var lock = action.lock = new EzekielLock('hitsl.mis.action.{0}'.format(action.id));
                    lock.subscribe('acquired', function () {
                        action.readonly = false
                    });
                    lock.subscribe('lost', function () {
                        action.readonly = true
                    });
                    lock.subscribe('released', function () {
                        action.readonly = true
                    });
                    lock.subscribe('rejected', function () {
                        action.readonly = true;
                    });
                } else {
                    action.lock = null;
                    action.readonly = action.ro;
                }
                return action;
            });
    };
    Action.get_new = function (event_id, action_type_id) {
        /* Получение экземпляра (в обёртке $q.defer().promise) Action по Event.id и ActionType.id */
        var action = new Action();
        action.event_id = event_id;
        action.action_type_id = action_type_id;
        return ApiCalls.wrapper('GET', WMConfig.url.actions.action_new.format(action_type_id, event_id)).then(function (result) {
            var retval = action.merge(result);
            retval.readonly = result.ro;
            return retval;
        });
    };
    Action.previous = function (action) {
        var dest = new Action();
        return ApiCalls.wrapper(
            'GET',
            WMConfig.url.actions.action_previous, {
                client_id: action.client.id,
                at_id: action.action_type_id || action.action_type.id,
                id: action.id
            }).then(function (result) {
            return dest.merge_template(result);
        })
    };
    Action.prototype.merge = function (src_action) {
        merge_fields(this, src_action);
        merge_meta(this, src_action);
        merge_properties(this, src_action);
        process_properties(this, src_action);
        return this;
    };
    Action.prototype.merge_template = function (src_action) {
        merge_template_fields(this, src_action);
        merge_properties(this, src_action);
        process_properties(this, src_action);
        return this;
    };
    Action.prototype.get_data = function () {
        var data = {};
        merge_fields(data, this);
        data.action_type_id = this.action_type_id || this.action_type.id;
        merge_properties(data, this);
        data.id = self.id;
        return data;
    };
    Action.prototype.is_new = function () {
        return !this.id;
    };
    Action.prototype.save = function () {
        var self = this,
            data = {};
        merge_fields(data, self);
        data.diagnoses = self._get_entity_changes('diagnoses');
        data.action_type_id = self.action_type_id || self.action_type.id;
        merge_properties(data, self);
        data.id = self.id;
        return ApiCalls.wrapper(
            'POST',
            WMConfig.url.actions.action_save.format(this.id || ''), undefined, data
        )
            .then(function (result) {
                self.readonly = result.ro;
                return self.merge(result);
            }, function (result) {
                return $q.reject(result);
            });
    };
    Action.prototype.autosave = function () {
        var self = this,
            data = {};
        merge_fields(data, self);
        data.diagnoses = self._get_entity_changes('diagnoses');
        data.action_type_id = self.action_type_id || self.action_type.id;
        merge_properties(data, self);
        if (this.id && !_.isNaN(this.id)) {
            data.id = self.id;
            return ApiCalls.wrapper(
                'POST',
                WMConfig.url.actions.autosave_normal.format(this.id), undefined, data
            )
        } else {
            return ApiCalls.wrapper(
                'POST',
                WMConfig.url.actions.autosave_new.format(
                    self.event_id,
                    self.action_type_id || self.action_type.id
                ), undefined, data
            )
        }
    };
    Action.prototype.discard = function () {
        if (this.id && !_.isNaN(this.id)) {
            return ApiCalls.wrapper('DELETE', WMConfig.url.actions.autosave_normal.format(this.id))
        } else {
            return ApiCalls.wrapper(
                'DELETE',
                WMConfig.url.actions.autosave_new.format(
                    this.event_id,
                    this.action_type_id || this.action_type.id
                )
            );
        }
    };
    Action.prototype.reload = function () {
        var self = this;
        if (self.is_new()) {return}
        ApiCalls.wrapper('GET', WMConfig.url.actions.action_get.format(self.id)).then(function (result) {
            return self.merge(result);
        })
    };
    Action.prototype.get_property = function (id) {
        return this.properties_by_id[id] || this.properties_by_code[id];
    };
    Action.prototype.get_baklab_info = function () {
        return this.bak_lab_info ? this.bak_lab_info : null;
    };
    Action.prototype.is_assignable = function (id) {
        var prop = this.get_property(id);
        return prop ? prop.type.is_assignable : false;
    };
    Action.prototype._get_entity_changes = function(entity) {
        var dirty_elements = this[entity].filter(function(el) {
            return el.kind_changed || el.diagnostic_changed;
        });
        var deleted_elements = [];
//        var deleted_elements = this.deleted_entities[entity] || [];
        var changes = dirty_elements.concat(deleted_elements.filter(function(del_elmnt) {
            return dirty_elements.indexOf(del_elmnt) === -1;
        }));
        return changes.length ? changes : undefined;
    };
    return Action;
}]);
