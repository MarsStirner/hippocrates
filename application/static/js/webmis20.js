/**
 * Created by mmalkov on 10.02.14.
 */
var WebMis20 = angular.module('WebMis20', []);
WebMis20.config(function ($interpolateProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
});