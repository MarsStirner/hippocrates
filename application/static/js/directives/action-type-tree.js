/**
 * Created by mmalkov on 14.07.14.
 */
angular.module('WebMis20.directives.ActionTypeTree', ['WebMis20.directives.goodies'])
.service('ActionTypeTreeService', ['$http', function ($http) {
    var trees = [];
    var Tree = function () {
        var TreeItem = function (source) {
            if (!source) {
                this.id = null;
                this.name = null;
                this.code = null;
                this.flat_code = null;
                this.gid = null;
                this.age = null;
                this.sex = null;
                this.osids = [];
            } else if (angular.isArray(source)) {
                this.id = source[0];
                this.name = source[1];
                this.code = source[2];
                this.flat_code = source[3];
                this.gid = source[4];
                this.age = source[5];
                this.sex = source[6];
                this.osids = source[7];
            } else {
                angular.extend(this, source)
            }
            this.children = []
        };
        TreeItem.prototype.clone = function () {
            return new TreeItem(this)
        };
        var self = this;
        self.lookup = {};
        self.set_data = function (data) {
            self.lookup = {};
            data.map(function (item) {
                self.lookup[item[0]] =  new TreeItem(item)
            })
        };
        function age_acceptable(client_info, selector) {
            return ! (
                selector[0] != 0 && client_info.age_tuple[selector[0] - 1] < selector[1] ||
                selector[2] != 0 && client_info.age_tuple[selector[2] - 1] > selector[3]
            )
        }
        function sex_acceptable(client_info, sex) {
            return ! (sex && sex != client_info.sex_raw);
        }
        function os_acceptable(orgstructures) {
            return !orgstructures || aux.any_in(current_user.action_type_org_structures, orgstructures)
        }
        function personally_acceptable(id) {
            return !current_user.action_type_personally.length || current_user.action_type_personally.has(id)
        }
        function keywords_acceptable(keywords, item) {
            return keywords.filter(function (keyword) {
                return (item.name.toLowerCase() + ' ' + item.code.toLowerCase()).indexOf(keyword) !== -1
            }).length == keywords.length
        }
        self.filter = function (query, client_info, check_os, check_person) {
            function is_acceptable(keywords, item) {
                return Boolean(
                        ! item.children.length
                        && sex_acceptable(client_info, item.sex)
                        && age_acceptable(client_info, item.age)
                        && (!check_os || os_acceptable(item.osids))
                        && (!check_person || personally_acceptable(item.id))
                        // TODO: Check for MES
                        && keywords_acceptable(keywords, item)
                )
            }
            var keywords = query.toLowerCase().split(/\s+/i);
            console.log(keywords);
            var filtered = {
                root: new TreeItem(null)
            };
            angular.forEach(self.lookup, function (value, key) {
                if (is_acceptable(keywords, value)) {
                    filtered[key] = value.clone();
                    for (var id = value.gid; id; value = self.lookup[id], id = value.gid) {
                        if (id && !filtered.hasOwnProperty(id)) {
                            filtered[id] =  self.lookup[id].clone();
                        }
                    }
                }
            });
            angular.forEach(filtered, function (value) {
                var gid = value.gid;
                if (!value.id) return;
                var o = filtered[gid || 'root'];
                if (o) {
                    o.children.push(value.id)
                }
            });
            var render_node = function (id) {
                var value = filtered[id];
                return {
                    id: value.id,
                    name: value.name,
                    code: value.code,
                    children: value.children.map(render_node)
                };
            };
            return render_node('root');
        }
    };
    this.get = function (at_class) {
        if (! trees[at_class]) {
            trees[at_class] = new Tree();
            $http.get(url_for_schedule_api_atl_get_flat, {
                params: {
                    at_class: at_class
                }
            }).success(function (data) {
                trees[at_class].set_data(data.result);
            })
        }
        return trees[at_class];
    }
}])
.service('ActionTypeTreeModal', ['$modal', 'ActionTypeTreeService', function ($modal, ActionTypeTreeService) {
    return {
        open: function (at_class, event_id, client_info) {
            return $modal.open({
                template:
                    '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                        <button type="button" class="close" ng-click="cancel()">&times;</button>\
                        <h4 class="modal-title" id="myModalLabel">Новое действие</h4>\
                    </div>\
                    <div class="modal-body">\
                        <input class="form-control" type="text" ng-model="conditions.query" wm-slow-change="set_filter()"></input>\
                        <div class="checkbox">\
                            <label>\
                                <input type="checkbox" ng-model="conditions.person_check" ng-change="set_filter()" />\
                                Только разрешённые мне\
                            </label>\
                        </div>\
                        <div class="checkbox">\
                            <label>\
                                <input type="checkbox" ng-model="conditions.os_check" ng-change="set_filter()" />\
                                Только разрешённые в моём отделении\
                            </label>\
                        </div>\
                        <div class="ui-treeview">\
                            <ul ng-repeat="root in tree.children">\
                                <li sf-treepeat="node in children of root">\
                                    <a ng-href="[[ url_for_schedule_html_action ]]?action_type_id=[[ node.id ]]&event_id=[[ event_id ]]" \
                                       ng-if="!node.children.length" target="_blank">\
                                        <div class="tree-label leaf">&nbsp;</div>\
                                        [ [[node.code]] ] [[ node.name ]]\
                                    </a>\
                                    <a ng-if="node.children.length" ng-click="toggle_vis(node.id)" class="node">\
                                        <div class="tree-label"\
                                             ng-class="{\'collapsed\': !subtree_shown(node.id),\
                                                        \'expanded\': subtree_shown(node.id)}">&nbsp;</div>\
                                        [ [[node.code]] ] [[ node.name ]]\
                                    </a>\
                                    <ul ng-if="node.children.length && subtree_shown(node.id)">\
                                        <li sf-treecurse></li>\
                                    </ul>\
                                </li>\
                            </ul>\
                        </div>\
                    </div>\
                    <div class="modal-footer">\
                        <button type="button" class="btn btn-default" ng-click="cancel()">Закрыть</button>\
                    </div>',
                size: 'lg',
                controller: function ($scope, $modalInstance) {
                    var service = ActionTypeTreeService.get(at_class);
                    $scope.url_for_schedule_html_action = url_for_schedule_html_action;
                    $scope.event_id = event_id;
                    var conditions = $scope.conditions = {
                        query: '',
                        os_check: true,
                        person_check: true
                    };
                    $scope.query = '';
                    $scope.os_check = true;
                    $scope.person_check = true;
                    $scope.tree = undefined;
                    $scope.set_filter = function () {
                        $scope.tree = service.filter(
                            conditions.query,
                            client_info,
                            conditions.os_check,
                            conditions.person_check
                        );
                    };
                    $scope.hidden_nodes = [];
                    $scope.toggle_vis = function (node_id) {
                        if ($scope.hidden_nodes.has(node_id)) {
                            $scope.hidden_nodes.splice($scope.hidden_nodes.indexOf(node_id), 1);
                        } else {
                            $scope.hidden_nodes.push(node_id);
                        }
                    };
                    $scope.subtree_shown = function (node_id) {
                        return !$scope.hidden_nodes.has(node_id);
                    };
                    $scope.cancel = function () {
                        $modalInstance.dismiss('close');
                    };
                }
            })
        }
    }
}])
;