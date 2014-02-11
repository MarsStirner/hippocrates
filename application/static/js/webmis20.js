/**
 * Created by mmalkov on 10.02.14.
 */
var WebMis20 = angular.module('WebMis20', []);
WebMis20.config(function ($interpolateProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
});
function getQueryParams(qs) {
    qs = qs.split("+").join(" ");

    var params = {}, tokens,
            re = /[?&]?([^=]+)=([^&]*)/g;

    while (tokens = re.exec(qs)) {
        params[decodeURIComponent(tokens[1])] = decodeURIComponent(tokens[2]);
    }

    return params;
}
function range(a, b, step){
    var A = [];
    A[0] = a;
    step = step || 1;
    while(a + step < b){
        A[A.length]= a+= step;
    }
    return A;
}