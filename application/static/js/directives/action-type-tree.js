/**
 * Created by mmalkov on 14.07.14.
 */
angular.module('WebMis20.directives.ActionTypeTree', ['WebMis20.directives.goodies'])
.service('ActionTypeTreeService', ['$http', function ($http) {
    var trees = [];
    var Tree = function () {
        var self = this;
        self.lookup = {};
        self.set_data = function (data) {
            self.lookup = {};
            data.map(function (item) {
                self.lookup[item[0]] =  {
                    id: item[0],
                    name: item[1],
                    gid:item[2],
                    code: item[3],
                    children: item[4],
                    clone: function () {
                        return {
                            id: this.id,
                            name: this.name,
                            gid: this.gid,
                            code: this.code,
                            children: []
                        };
                    }
                }
            })
        };
        self.filter = function (query) {
            var filtered = {
                root: {
                    id: null,
                    name: null,
                    code: null,
                    gid: null,
                    children: []
                }
            };
            angular.forEach(self.lookup, function (value, key) {
                if (value.name.indexOf(query) != -1 || value.code.indexOf(query) != -1) {
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
.directive('actionTypeTree', ['ActionTypeTreeService', function (ActionTypeTreeService) {
    return {
        restrict: 'E',
        scope: {
            eventId: '='
        },
        template:
            '<button class="btn btn-info" ng-click="pop_toggle()">Создать...</button>\
            <div class="well popupable" style="overflow-y: auto; max-height: 400px" ng-if="popped">\
                <input class="form-control" type="text" ng-model="query" wm-slow-change="set_filter(query)"></input>\
                <div class="ui-treeview">\
                    <ul ng-repeat="root in tree.children">\
                        <li sf-treepeat="node in children of root">\
                            <div ng-if="node.children.length" class="tree-label"\
                            ng-class="{\'collapsed\': !subtree_shown(node.id),\
                                        \'expanded\': subtree_shown(node.id)}"\
                            ng-click="toggle_vis(node.id)">&nbsp;</div>\
                            <div ng-if="!node.children.length" class="tree-label leaf">&nbsp;</div>\
                            <a ng-href="[[ url_for_schedule_html_action ]]?action_type_id=[[ node.id ]]&event_id=[[ eventId ]]" ng-if="!node.children.length">\
                            [ [[node.code]] ] [[ node.name ]]\
                            </a>\
                            <span ng-if="node.children.length">[ [[node.code]] ] [[ node.name ]]</span>\
                            <ul ng-if="node.children.length && subtree_shown(node.id)">\
                                <li sf-treecurse></li>\
                            </ul>\
                        </li>\
                    </ul>\
                </div>\
            </div>',
        link: function (scope, element, attrs) {
            var service = ActionTypeTreeService.get(parseInt(attrs.atClass));
            scope.query = '';
            scope.tree = undefined;
            scope.popped = false;
            scope.pop_toggle = function () {
                scope.popped = ! scope.popped;
            };
            scope.set_filter = function (query) {
                scope.tree = service.filter(query);
            };
            scope.hidden_nodes = [];
            scope.toggle_vis = function (node_id) {
                if (aux.inArray(scope.hidden_nodes, node_id)) {
                    scope.hidden_nodes.splice(scope.hidden_nodes.indexOf(node_id), 1);
                } else {
                    scope.hidden_nodes.push(node_id);
                }
            };
            scope.subtree_shown = function (node_id) {
                return !aux.inArray(scope.hidden_nodes, node_id);
            };

            scope.open_action = function (action_id) {
                window.open(url_for_schedule_html_action + '?action_id=' + action_id);
            };
        }
    }
}]);