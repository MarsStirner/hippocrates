/**
 * Created by mmalkov on 11.07.14.
 */
angular.module('WebMis20.directives.personTree', [])
.directive('personTree', ['$http', function($http) {
    return {
        restrict: 'E',
        replace: true,
        scope: {
            personId: '=',
            userSelected: '=',
            lockedPersons: '='
        },
        template:
            '<div>\
                <span class="input-group" id="person-query-group">\
                    <span class="input-group-addon"><span class="glyphicon glyphicon-search"></span></span>\
                    <input id="person_query" class="form-control" type="text" ng-model="query" placeholder="Поиск врача" ng-change="compose()" ng-focus="show_tree()"/>\
                    <span class="input-group-btn">\
                        <button type="button" class="btn btn-danger" ng-click="clear()"><span class="glyphicon glyphicon-remove"></span></button>\
                    </span>\
                </span>\
                <div class="css-treeview well well-sm scrolled-tree" ng-mouseleave="hide_tree()" ng-class="{popup: popupable}">\
                    <ul>\
                        <li ng-repeat="spec_group in tree">\
                            <input class="group" type="checkbox" id="spec-[[spec_group.speciality.id]]" checked>\
                                <label class="group" for="spec-[[spec_group.speciality.id]]" ng-bind="spec_group.speciality.name" ></label>\
                                <ul>\
                                    <li ng-repeat="person in spec_group.persons">\
                                        <a class="leaf" ng-bind="person.nameFull" ng-click="person_selected(person)" ng-if="!checkboxed"></a>\
                                        <input type="checkbox" id="doc-[[person.id]]" ng-model="person.checked" ng-disabled="person.disabled" ng-change="selection_change(person)" class="leaf" ng-if="checkboxed">\
                                        <label class="leaf" for="doc-[[person.id]]" ng-bind="person.name" ng-if="checkboxed"></label>\
                                    </li>\
                                </ul>\
                        </li>\
                    </ul>\
                </div>\
            </div>',
        link: function ($scope, element, attrs) {
            $scope.popupable = Boolean(attrs.popupable);
            $scope.checkboxed = Boolean(attrs.checkboxed);
            $scope.data = [];
            $scope.query = '';
            $scope.tree = [];
//            $scope.lockedPersons = [];
//            $scope.userSelected = [];
            $scope.reloadTree = function() {
                $http.get(
                    url_schedule_all_persons_tree
                ).success(function (data) {
                    $scope.data = data.result;
                    $scope.compose();
                })
            };
            $scope.reset = function () {
                $scope.query = '';
//                $scope.userSelected = [];
                $scope.reloadTree();
            };
            $scope.compose = function () {
                $scope.tree = $scope.data.map(function (spec_group) {
                    return {
                        speciality: spec_group.speciality,
                        persons: (spec_group.persons).filter(function (person) {
                            var words = $scope.query.split(' ');
                            return $scope.query == '' || words.filter(function (word) {
                                var data = [].concat(person.nameFull, [spec_group.speciality.name]);
                                return data.filter(function (namePart) {
                                    return aux.startswith(namePart.toLocaleLowerCase(), word.toLocaleLowerCase())
                                }).length > 0;
                            }).length == words.length;
                        }).map(function (person) {
                            return {
                                id: person.id,
                                name: person.name,
                                nameFull: person.nameFull.join(' '),
                                disabled: $.inArray(person.id, $scope.lockedPersons) !== -1,
                                checked: $.inArray(person.id, [].concat($scope.lockedPersons, $scope.userSelected)) !== -1
                            }
                        })
                    }
                }).filter(function (spec_group) {
                    return spec_group.persons.length > 0;
                })
            };
            $scope.selection_change = function (person) {
                var userSelected = [];
                $scope.tree.map(function (spec_group) {
                    spec_group.persons.filter(function (person) {
                        return person.checked;
                    }).map(function (person) {
                        userSelected.push(person.id);
                    })
                });
                $scope.userSelected = userSelected;
//                $scope.$root.$broadcast('UserSelectionChanged', person, userSelected);
            };
            $scope.clear = function () {
                $scope.query = '';
                $scope.compose();
            };
            $scope.$watch('lockedPersons', function (new_value, old_value) {
                $scope.compose();
            });
            $scope.$watch('personId', function (new_value, old_value) {
                $scope.compose();
            });
//            $scope.$on('DataSelectedChanged', function (event, lockedPersons) {
//                $scope.lockedPersons = lockedPersons;
//                $scope.compose();
//            });
//            $scope.$on('UserSelectionChanged', function (event) {
//                $scope.compose();
//            });
//            $scope.$on('Reset', function () {
//                $scope.reset();
//            });
            var we = $(element);
            var person_input = we.find('input#person_query');
            var person_query_group = we.find('#person-query-group');
            var person_tree_div = we.find('div.scrolled-tree');
            $scope.show_tree = function () {
                if (!$scope.popupable) return;
                $scope.compose();
                if (person_tree_div) {
                    person_tree_div.width(person_query_group.width() - 20);
                    person_tree_div.show();
                }
            };
            $scope.hide_tree = function () {
                if (!$scope.popupable) return;
                if (person_tree_div) {
                    person_tree_div.hide();
                    person_input.blur();
                }
            };
            $scope.person_selected = function (person) {
                $scope.query = person.nameFull;
                $scope.hide_tree();
                $scope.personId = person.id;
//                $scope.$root.$broadcast('PersonSelected', person);
            };
//            $scope.$on('ManuallySelectedPersonId', function (event, id) {
//                var name = null;
//                $scope.data.map(function (spec_group) {
//                    spec_group.map(function (person) {
//                        if (person.id == id) {
//                            name = person.nameFull.join(' ')
//                        }
//                    })
//                });
//                $scope.query = name;
//            });
            $scope.reset();
        }
    }
}]);