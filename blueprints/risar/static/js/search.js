/**
 * Created by mmalkov on 24.09.14.
 */
var EventSearchCtrl = function ($scope, RisarApi) {
    $scope.query = {
        org: {},
        person: {}
    };
    $scope.results = [];
    $scope.perform = function () {
        RisarApi.search_event.get({
            org_id: $scope.query.org.id,
            doc_id: $scope.query.person.id
        }).then(function (result) {
            $scope.results = result;
        })
    };
    $scope.refresh_organisations = function () {
        RisarApi.search_event.lpu_list()
        .then(function (result) {
            $scope.organisations = result;
        })
    };
    $scope.refresh_doctors = function () {
        RisarApi.search_event.lpu_doctors_list($scope.query.org.id)
        .then(function (result) {
            $scope.person = {};
            $scope.doctors = result;
        })
    };

    $scope.refresh_organisations()
};
