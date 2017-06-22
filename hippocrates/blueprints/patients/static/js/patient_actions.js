'use strict';

var PatientActionsCtrl = function ($scope, $window, PatientATTreeService, RefBookService, WMConfig,
        PrintingService, LabDynamicsModal, client_id) {
    $scope.client_id = undefined;
    $scope.tree = null;
    $scope.filtered_tree = null;
    $scope.cond = {
        query: ''
    };
    $scope.common_ps = null;

    $scope.ActionTypeClass = RefBookService.get('ActionTypeClass');

    $scope.reloadData = function(client_id) {
        $scope.client_id = client_id;
        PatientATTreeService.get(client_id)
            .then(function (tree) {
                $scope.tree = tree;
                $scope.set_filter();
            });
    };
    $scope.set_filter = function (query_changed) {
        if (!$scope.tree) return;
        $scope.filtered_tree = $scope.tree.filter(
            $scope.cond.query
        );
        if (query_changed) {
            $scope.tree.expand_all($scope.filtered_tree);
        }
    };

    $scope.$on('patientActionsOpened', function (event, args) {
        if (!$scope.client_id || $scope.client_id !== args.client_id) {
            $scope.init(args.client_id);
        }
    });

    $scope.openAction = function(node) {
         $window.open(WMConfig.url.actions.html.action + '?action_id=' + node.action_id, '_blank');
    };
    $scope.openLabDynamics = function (node) {
        LabDynamicsModal.openLabDynamicsModal({event_id: node.event_id}, {id: node.id, type: {id: node.action_type.id}});
    };

    $scope.init = function (client_id) {
        $scope.reloadData(client_id);
        $scope.common_ps = new PrintingService("action");
    };

    if (client_id) {
        $scope.init(client_id);
    }
};


WebMis20.controller('PatientActionsCtrl', ['$scope', '$window', 'PatientATTreeService', 'RefBookService',
    'WMConfig', 'PrintingService', 'LabDynamicsModal', PatientActionsCtrl]);


WebMis20.service('PatientATTreeService', ['$q', '$filter', 'WebMisApi', 'RefBookService',
        function ($q, $filter, WebMisApi, RefBookService) {
    var Tree = function () {
        var self = this;
        var RootTreeItem = function (source) {
            this.id = null;
            this.name = null;
            this.code = null;
            this.flat_code = null;
            this.gid = null;
            this.children = [];
        };
        RootTreeItem.prototype.clone = function () {
            return new RootTreeItem(this)
        };
        RootTreeItem.prototype.sort_children = function () {
            var order = ['medical_documents', 'diagnostics', 'lab', 'treatments', 'movings'];
            if (this.children && _.isArray(this.children)) {
                this.children.sort(function (x, y) {
                    var x_idx = order.indexOf(x),
                        y_idx = order.indexOf(y);
                    return x_idx - y_idx;
                })
            }
        };
        var ClassTreeItem = function (source) {
            if (!source) {
                this.id = null;
                this.name = null;
                this.code = null;
                this.gid = null;
            } else {
                angular.extend(this, source);
            }
            this.children = [];
            this.is_at_class_item = true;
        };
        ClassTreeItem.prototype.clone = function () {
            return new ClassTreeItem(this)
        };
        ClassTreeItem.prototype.sort_children = function () {
            if (this.children && _.isArray(this.children)) {
                this.children.sort(function (x, y) {
                    var a = self.lookup[x],
                        b = self.lookup[y];
                    if (a.code > b.code) {
                        return 1;
                    } else if (a.code < b.code) {
                        return -1;
                    } else {
                        return 0;
                    }
                })
            }
        };
        var TreeItem = function (source) {
            if (!source) {
                this.id = null;
                this.name = null;
                this.code = null;
                this.flat_code = null;
                this.gid = null;
                this.class_code = null;
            } else if (angular.isArray(source)) {
                this.id = source[1];
                this.name = source[2];
                this.code = source[3];
                this.flat_code = source[4];
                this.gid = source[5];
                this.class_code = source[6];
            } else {
                angular.extend(this, source);
            }
            this.children = [];
            this.is_at_item = true;
        };
        TreeItem.prototype.clone = function () {
            return new TreeItem(this)
        };
        TreeItem.prototype.sort_children = function () {
            if (this.children && _.isArray(this.children)) {
                var node = self.lookup[this.children[0]];
                // TreeItems
                if (node.is_at_item) {
                    this.children.sort(function (x, y) {
                        var a = self.lookup[x],
                            b = self.lookup[y];
                        if (a.code > b.code) {
                            return 1;
                        } else if (a.code < b.code) {
                            return -1;
                        } else {
                            return 0;
                        }
                    });
                } else { // ActionTreeItem
                    this.children.sort(function (x, y) {
                        var a = self.lookup[x],
                            b = self.lookup[y];
                        if (a.getValuedDate() < b.getValuedDate()) {
                            return 1;
                        } else if (a.getValuedDate() > b.getValuedDate()) {
                            return -1;
                        } else {
                            return a.status - b.status;
                        }
                    });
                }

            }
        };
        var ActionTreeItem = function (source) {
            if (!source) {
                this.id = null;
                this.name = null;
                this.code = null;
                this.flat_code = null;
                this.gid = null;
                this.class_code = null;
            } else {
                angular.extend(this, source);
                this.class_code = this.action_type.action_type_class.code;
            }
            this.children = [];
            this.chilren_loaded = false;
            this.is_action_item = true;
        };
        ActionTreeItem.prototype.clone = function () {
            return new ActionTreeItem(this)
        };
        ActionTreeItem.prototype.formatData = function () {
            return '{|0| }{(|1|), }{2}, {3}'.formatNonEmpty(
                $filter('asDateTime')(this.getValuedDate()), $filter('asDateTime')(this.getValuedDateText()),
                this.action_type.name, this.status.name
            );
        };
        ActionTreeItem.prototype.get_ps_resolve = function () {
            return {action_id: this.action_id};
        };
        ActionTreeItem.prototype.getValuedDate = function () {
            if (this.class_code === 'lab' || this.class_code === 'diagnostics') {
                if (this.end_date) {
                    return this.end_date;
                } else if (this.planned_end_date) {
                    return this.planned_end_date;
                } else {
                    return this.beg_date;
                }
            } else {
                return this.beg_date;
            }
        };
        ActionTreeItem.prototype.getValuedDateText = function () {
            if (this.class_code === 'lab' || this.class_code === 'diagnostics') {
                if (this.end_date) {
                    return 'дата выполнения';
                } else if (this.planned_end_date) {
                    return 'плановая дата';
                } else {
                    return 'дата назначения';
                }
            } else {
                return '';
            }
        };
        ActionTreeItem.prototype.sort_children = function () {};
        ActionTreeItem.prototype.load_children = function () {
            if (!this.chilren_loaded) {
                var self = this;
                this.children = [];
                WebMisApi.action.get_action_properties(this.action_id).then(function (data) {
                    angular.forEach(data.properties, function (item) {
                        self.children.push(new APTreeItem(item));
                    });
                    self.chilren_loaded = true;
                });
            }
        };

        var APTreeItem = function (source) {
            if (!source) {
                this.id = null;
                this.action_id = null;
                this.type = {
                    id: null,
                    idx: null,
                    code: null,
                    name: null
                };
                this.is_assigned = null;
                this.value_str = null;
                this.unit = null;
                this.isSelected = null;
            } else {
                angular.extend(this, source);
                this.isSelected = this.is_assigned;
            }
            this.children = [];
            this.is_ap_item = true;
        };
        APTreeItem.prototype.clone = function () {
            return new APTreeItem(this)
        };
        APTreeItem.prototype.formatData = function () {
            return '<b>{0}:</b> {1} {2}'.formatNonEmpty(this.type.name, this.value_str, this.unit && this.unit.code);
        };
        APTreeItem.prototype.sort_children = function () {};

        self.lookup = {};
        self.set_data = function (data) {
            // init class_code nodes, ActionType nodes and Action nodes
            self.lookup = _.chain(
                data
            ).makeObject(
                function (item) {
                    return _.isArray(item) ? item[1] : item.id;
                },
                function (item) {
                    var node;
                    if (_.isArray(item)) {
                        if (item[0] === 'at_node') node = new TreeItem(item);
                        else throw 'Неизвестный тип узла ' + item[0];
                    } else {
                        if (item.node_type === 'action_node') node = new ActionTreeItem(item);
                        else if (item.node_type === 'at_class_node') node = new ClassTreeItem(item);
                        else throw 'Неизвестный тип узла ' + item.node_type;
                    }
                    return node;
                }
            ).each(function (item, key_id, context) {
                if (item.gid && _.has(context, item.gid)) {
                    context[item.gid].children.push(key_id);
                }
            }).value();
        };

        self.expanded = {};
        self.toggle_expanded = function (node, enabled) {
            var enabled = enabled !== undefined ? enabled : !self.expanded[node.id];
            self.expanded[node.id] = enabled;
        };
        self.is_expanded = function (node) {
            return Boolean(self.expanded[node.id]) || (node.is_action_item && node.children_loaded && !node.children.length);
        };
        self.toggle_group_expanded = function (node, enabled) {
            var enabled = enabled !== undefined ? enabled : !self.is_group_expanded(node);
            self.toggle_expanded(node, enabled);
            node.children.forEach(function (child_node) {
                self.toggle_group_expanded(child_node, enabled);
            });
        };
        self.is_group_expanded = function (node) {
            return self.is_expanded(node) && node.children.every(self.is_group_expanded);
        };
        self.expand_all = function (flt_tree) {
            flt_tree.children.forEach(function (node) {
                self.toggle_group_expanded(node, true);
            });
        };
        self.get_selected_data = function (node) {
            var actions_dict = {};
            var traverse = function (item) {
                if (item.hasOwnProperty('isSelected') && item.hasOwnProperty('id')) {
                    if (!actions_dict.hasOwnProperty(item.action_id)) {
                        actions_dict[item.action_id] = [];
                    }
                    actions_dict[item.action_id].push(item.id);
                }
                if (item.hasOwnProperty('children')) {
                    item.children.forEach(traverse);
                }
            };
            traverse(node);
            return actions_dict;
        };

        function at_class_acceptable(item) {
            return item.is_at_class_item || item.is_action_item;
        }
        function keywords_acceptable(keywords, item) {
            if (!item.is_action_item) return true;
            var item_test_data = '{0} {1}'.format(item.action_type.name, item.action_type.code).toLowerCase();
            return _.all(keywords, function (keyword) {
                return item_test_data.indexOf(keyword) !== -1
            });
        }
        self.filter = function (query) {
            function is_acceptable(keywords, item) {
                return Boolean(
                    at_class_acceptable(item) &&
                    keywords_acceptable(keywords, item)
                )
            }
            var keywords = query.toLowerCase().split(/\s+/i);
            var filtered = {
                root: new RootTreeItem(null)
            };
            _.chain(
                self.lookup
            ).filter(
                _.partial(is_acceptable, keywords)
            ).each(
                function (value) {
                    var id = value.id;
                    var clone = filtered[id] = value.clone();
                    // Построение недостающих родительских узлов - подъём по дереву вверх до первого найденного
                    while (id) {
                        id = value.gid;
                        if (!id) break;
                        if (!_.has(self.lookup, id)) {
                            console.log('Проблема с ActionType.id = {0}: его родитель ActionType.id = {1} не найден или удалён'.format(value.id, value.gid));
                            return
                        }
                        value = self.lookup[id];

                        if (!_.has(filtered, id)) {
                            filtered[id] = value.clone();
                        }
                    }
                }
            ).value();
            _.chain(
                filtered
            ).each(function (value) {
                // Установка идентификаторов дочерних элементов у каждого элемента в отфильтрованном дереве
                var gid = value.gid;
                if (!value.id) return;
                var o = filtered[gid || 'root'];
                if (o) {
                    o.children.push(value.id)
                }
            }).each(function (value) {
                // Сортировка идентификаторов дочерних элементов
                // Это нельзя сделать в перыдущей функции, потому что там они ещё не все готовы
                value.sort_children()
            }).value();
            var render_node = function (id) {
                var value = filtered[id];
                value.children = value.children.map(render_node);
                return value;
            };
            return render_node('root');
        }
    };
    this.get = function (client_id) {
        var tree = new Tree(),
            all_items = [];
        var ActionTypeClass = RefBookService.get('ActionTypeClass');

        return $q.all([ActionTypeClass.loading, WebMisApi.action.get_patient_actions(client_id)])
            .then(function (result) {
                var data = result[1];

                // extend flat trees with class_code items
                angular.forEach(ActionTypeClass.objects, function (item) {
                    var ni = _.deepCopy(item);
                    item.node_type = 'at_class_node';
                    item.class_id = item.id;
                    item.id = item.code;
                    item.gid = null;
                    all_items.push(item);
                });
                // modify at flat trees
                angular.forEach(data.flat_trees, function (item) {
                    item.unshift('at_node'); // 0 - type
                    if (!item[5]) {
                        // gid = class_code for root nodes
                        item[5] = item[6]
                    }

                    all_items.push(item);
                });
                // extend flat trees with actions as items
                angular.forEach(data.patient_actions, function (action) {
                    action.action_id = action.id;
                    action.id = 'a_' + action.id;
                    action.gid = action.action_type.id;
                    action.node_type = 'action_node';
                    all_items.push(action)
                });

                tree.set_data(all_items);

                return tree;
            });
    };
    this.get_with_values = function (client_id, at_class) {
        var tree = new Tree(),
            all_items = [];
        var ActionTypeClass = RefBookService.get('ActionTypeClass');

        return $q.all([ActionTypeClass.loading, WebMisApi.action.get_patient_actions_with_values(client_id,
            {'at_class': at_class})])
            .then(function (result) {
                var data = result[1];

                // extend flat trees with class_code items
                angular.forEach(ActionTypeClass.objects, function (item) {
                    var ni = _.deepCopy(item);
                    item.node_type = 'at_class_node';
                    item.class_id = item.id;
                    item.id = item.code;
                    item.gid = null;
                    all_items.push(item);
                });
                // modify at flat trees
                angular.forEach(data.flat_trees, function (item) {
                    item.unshift('at_node'); // 0 - type
                    if (!item[5]) {
                        // gid = class_code for root nodes
                        item[5] = item[6]
                    }

                    all_items.push(item);
                });
                // extend flat trees with actions as items
                angular.forEach(data.patient_actions, function (action) {
                    action.action_id = action.id;
                    action.id = 'a_' + action.id;
                    action.gid = action.action_type.id;
                    action.node_type = 'action_node';
                    all_items.push(action)
                });

                tree.set_data(all_items);

                return tree;
            });
    }
}]);


WebMis20.service('PatientActionsModalService', ['$modal', 'WMConfig', function ($modal, WMConfig) {
    return {
        open: function (client_id) {
            return $modal.open({
                templateUrl: WMConfig.url.patients.patient_actions_modal.format(client_id),
                controller: PatientActionsCtrl,
                size: 'lg',
                windowClass: 'modal-scrollable',
                backdrop : 'static',
                resolve: {
                    client_id: function () {
                        return client_id
                    }
                }
            }).result;
        }
    }
}]);
