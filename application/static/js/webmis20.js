/**
 * Created by mmalkov on 10.02.14.
 */
var WebMis20 = angular.module('WebMis20', ['ngResource', 'ui.bootstrap', 'ui.select', 'ngSanitize', 'ngCkeditor']);
WebMis20.config(function ($interpolateProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
});
WebMis20.filter('asDateTime', function ($filter) {
    return function (data) {
        if (!data) return data;
        var result = moment(data);
        if (!result.isValid()) return data;
        return result.format('DD.MM.YYYY HH:mm');
    }
});
WebMis20.filter('asDate', function ($filter) {
    return function (data) {
        if (!data) return data;
        var result = moment(data);
        if (!result.isValid()) return data;
        return result.format('DD.MM.YYYY');
    }
});
WebMis20.filter('asShortDate', function ($filter) {
    return function (data) {
        if (!data) return data;
        var result = moment(data);
        if (!result.isValid()) return data;
        return result.format('DD.MM');
    }
});
WebMis20.filter('asTime', function ($filter) {
    return function (data) {
        if (!data) return data;
        var result = moment(data);
        if (!result.isValid()) return data;
        return result.format('HH:mm');
    }
});
WebMis20.filter('asMomentFormat', function ($filter) {
    return function (data, format) {
        if (!data) return data;
        var result = moment(data);
        if (!result.isValid()) return data;
        return result.format(format);
    }
});
WebMis20.filter('asAutoFormat', function ($filter) {
    return function (data, key) {
        var value = data[key];
        if (!value) return value;
        var result = moment(value);
        if (aux.endswith(key, 'Date')) {
            return result.format('DD.MM.YYYY');
        } else if (aux.endswith(key, 'DateTime')) {
            return result.format('DD.MM.YYYY HH:mm');
        } else if (aux.endswith(key, 'Time')) {
            return result.format('HH:mm');
        } else {
            if (result.isValid()) {
                return result.toISOString();
            } else {
                return value;
            }
        }
    }
});
WebMis20.filter('join', function ($filter) {
    return function (data, char) {
        if (data instanceof Array)
            return data.join(char);
        return data
    }
});
// Services
WebMis20.factory('RefBook', ['$http', function ($http) {
    var RefBook = function (name) {
        this.name = name;
//        this.objects = [];
        this.load();
    };
    RefBook.prototype.load = function () {
        var t = this;
        $http.get(rb_root + this.name).success(function (data) {
            t.objects = data.result;
        });
        return this;
    };
    RefBook.prototype.get = function (id) {
        var i = this.objects.length;
        while (i--) {
            if (this.objects[i].id == id) return this.objects[i];
        }
        return null;
    };
    RefBook.prototype.get_by_code = function (code) {
        var i = this.objects.length;
        while (i--) {
            if (this.objects[i].code == code) return this.objects[i];
        }
        return null;
    };
    return RefBook;
}]);
WebMis20.factory('ClientResource',
    function($resource) {
        return $resource(url_client_get, {}, {
            save: {url: url_client_save, method: 'POST',
                params: {client_info: {}}}
        });
    }
);
WebMis20.factory('Client',
    ['ClientResource', '$q', function(ClientResource, $q) {
        var Client = function(client_id) {
            this.client_id = client_id;
            this.reload();
        }

        Client.prototype.reload = function() {
            var t = this;
            ClientResource.get({client_id: this.client_id},
                function(data) {
                    t.client_info = data.result.clientData;
                    t.appointments = data.result.appointments;
                    t.events = data.result.events;
                },
                function(data) {
                    throw 'Error requesting Client, id = ' + client_id;
                });
        }

        Client.prototype.save = function() {
            t = this
            var deferred = $q.defer();
            ClientResource.save({ client_info: this.client_info },
                function(value, headers) {
                    deferred.resolve();
                },
                function(httpResponse) {
                    var r = httpResponse.data;
                    var message = [r['result']['name'], ':\nНе заполнено поле ', r['result']['data']].join('')
                    deferred.reject(message);
                }
            );
            return deferred.promise;
        }

        Client.prototype.add_allergy = function() {
            this.client_info['allergies'].push({
                'nameSubstance': '',
                'power': 0,
                'createDate': '',
                'deleted':0,
                'notes': '' })
        };

        Client.prototype.add_medicament = function() {
            this.client_info['intolerances'].push({
                'nameMedicament': '',
                'power': 0,
                'createDate': '',
                'deleted':0,
                'notes': '' })
        };

        Client.prototype.add_identification = function() {
            this.client_info['identifications'].push({
                'deleted': 0,
                'identifier': '',
                'accountingSystem_code': '',
                'checkDate': ''})
        };

        Client.prototype.add_contact = function() {
            this.client_info['contacts'].push({
                'deleted': 0,
                'contactType_code': '',
                'contact': '',
                'notes': ''})
        };

        Client.prototype.add_blood = function () {
            this.client_info['bloodHistory'].push({'bloodGroup_code': '',
                'bloodDate': '',
                'person_id': 0
            })
        };

        Client.prototype.add_relation = function (entity) {
            this.client_info[entity].push({'deleted': 0,
                'relativeType_name': '',
                'relativeType_code': '',
                'other_id': 0
            })
        };

        Client.prototype.add_soc_status = function () {
            this.client_info['socStatuses'].push({'deleted': 0,
                'classCode': '',
                'typeCode': '',
                'begDate': '',
                'endDate': ''
            })
        };

        Client.prototype.delete_record = function(entity, record) {
            if ('id' in record) {
                record['deleted'] = 1;
            } else {
                var idx = this.client_info[entity].indexOf(record);
                this.client_info[entity].splice(idx, 1);
            }
        };

        return Client;
    }
    ])
// end services
WebMis20.directive('uiPopup', function ($timeout) {
    return {
        restrict: 'E',
        template:
            '<input type="text" class="form-control" ng-click="to_show()" ng-model="query">' +
            '<div class="well well-sm popupable" ng-show="shown" ng-transclude ng-mouseleave="to_hide_delay()" ng-mouseenter="to_hide_cancel()">',
        transclude: true,
        controller: function ($scope, $element) {
            var input_elem = $($element.children()[0]);
            var div_elem = $($element.children()[1]);
            var timeout = null;
            $scope.shown = false;
            $scope.query='';
            $scope.to_show = function () {
                div_elem.width(input_elem.width());
                $scope.shown = true;
            };
            $scope.to_hide_delay = function () {
                if (!timeout) {
                    timeout = $timeout(to_hide, 600)
                }
            };
            $scope.to_hide_cancel = function () {
                if (timeout) {
                    $timeout.cancel(timeout);
                    timeout = null;
                }
            };
            this.finish_him =function (query) {
                to_hide();
                $scope.query = query;
            };
            function to_hide () {
                timeout = null;
                $scope.shown = false;
            }
        }
    }
});
WebMis20.directive('uiRbTable', function () {
    return {
        restrict: 'E',
        require: '^uiPopup',
        template: '<table class="table table-condensed table-hover table-clickable">' +
            '<thead><tr><th>Код</th><th>Наименование</th></tr></thead>' +
            '<tbody>' +
                '<tr ng-repeat="row in refBook.objects | filter:query" ng-click="onClick(row)">' +
                    '<td ng-bind="row.code"></td><td ng-bind="row.name"></td>' +
                '</tr>' +
            '</tbody></table>',
        link: function (scope, element, attributes, popupCtrl) {
            scope.refBook = scope.$eval(attributes.refBook);
            scope.$parent.$watch('query', function (newVal, oldVal) {
                scope.query = newVal;
            });
            scope.onClick = function (row) {
                scope.$parent.$parent[attributes.ngModel] = row; // HACK!
                popupCtrl.finish_him(row.name);
            };
            scope.search = function (actual, expected) {
                return actual.split(' ').filter(function (part) {
                    return aux.startswith(part, expected)
                }).length > 0;
            }
        }
    }
});
var aux = {
    getQueryParams: function (qs) {
        qs = qs.split("+").join(" ");

        var params = {}, tokens,
                re = /[?&]?([^=]+)=([^&]*)/g;

        while (tokens = re.exec(qs)) {
            params[decodeURIComponent(tokens[1])] = decodeURIComponent(tokens[2]);
        }

        return params;
    },
    range: function (num) {
        return Array.apply(null, new Array(num)).map(function(_, i) {return i;})
    },
    moment: moment,
    months: [
        {name: 'Январь', value: 0},
        {name: 'Февраль', value: 1},
        {name: 'Март', value: 2},
        {name: 'Апрель', value: 3},
        {name: 'Май', value: 4},
        {name: 'Июнь', value: 5},
        {name: 'Июль', value: 6},
        {name: 'Август', value: 7},
        {name: 'Сентябрь', value: 8},
        {name: 'Октябрь', value: 9},
        {name: 'Ноябрь', value: 10},
        {name: 'Декабрь', value: 11}
    ],
    endswith: function (str, suffix) {
        return str.indexOf(suffix, str.length - suffix.length) !== -1;
    },
    startswith: function (str, prefix) {
        return str.indexOf(prefix) === 0;
    },
    format: function (record, key) {
        if (typeof (record) === 'undefined') {
            return null;
        } else if (aux.endswith(key, 'DateTime')) {
            return moment(record[key]).format('DD-MM-YYYY HH:mm');
        } else if (aux.endswith(key, 'Date')) {
            return moment(record[key]).format('DD-MM-YYYY');
        } else {
            return record[key];
        }
    },
    arrayCopy: function (source) {
        // proven fastest copy mechanism http://jsperf.com/new-array-vs-splice-vs-slice/28
        var b = [];
        var i = source.length;
        while (i--) {b[i] = source[i]}
        return b;
    },
    func_in: function (against) {
        return function (item) {
            return against.indexOf(item) !== -1;
        }
    },
    func_not_in: function (against) {
        return function (item) {
            return against.indexOf(item) === -1;
        }
    },
    find_by_code: function (where, code, field) {
        if (typeof (field) === 'undefined') field = 'code';
        var subresult = where.filter(function (item) {return item[field] == code});
        if (subresult.length === 0) return null;
        return subresult[0]
    },
    inArray: function (array, item) {
        return array.indexOf(item) !== -1;
    },
    forEach: function (object, callback) {
        var result = {};
        var key;
        for (key in object) {
            result[key] = callback(object[key]);
        }
        return result
    }
};