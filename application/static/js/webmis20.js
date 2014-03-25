/**
 * Created by mmalkov on 10.02.14.
 */
var WebMis20 = angular.module('WebMis20', ['ui.bootstrap', 'ui.select', 'ngSanitize']);
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
    return RefBook;
}]);
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