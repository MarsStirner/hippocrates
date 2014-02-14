/**
 * Created by mmalkov on 10.02.14.
 */
var WebMis20 = angular.module('WebMis20', []);
WebMis20.config(function ($interpolateProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
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
    ]
};