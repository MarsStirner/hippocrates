
'use strict';

var ErrandsListCtrl = function ($scope, UserErrand) {
    $scope.unread = 0;
    $scope.errands = [];
    UserErrand.subscribe('unread', reset_errands)
    UserErrand.subscribe('ready', reload_errands);
    UserErrand.subscribe('new:id', reload_errands);
    function reset_errands (result) {
        if (result) {
            $scope.errands = result.errands;
        }
    }
    function reload_errands () {
        UserErrand.get_errands(10).then(reset_errands);
    }
    $scope.reload_errands = reload_errands;
}