
'use strict';

var ErrandsListCtrl = function ($scope, $window, $modal, UserErrand, CurrentUser) {
    var params = aux.getQueryParams($window.location.search);
    $scope.unread = 0;
    $scope.errands = [];
    $scope.current_user = CurrentUser.info;
    UserErrand.subscribe('unread', reset_errands)
    UserErrand.subscribe('ready', reload_errands);
    UserErrand.subscribe('new:id', reload_errands);

    $scope.reset_filters = function () {
        if (Object.keys(params).length){
            $scope.query = params;
        } else {
            $scope.query = {
                exec_person: CurrentUser.info,
                show_deleted: false
            }
        }
;
    };
    function reset_errands (result) {
        if (result) {
            $scope.errands = result.errands;
        }
    }
    function reload_errands () {
        UserErrand.get_errands(10, $scope.query).then(reset_errands);
    }

    $scope.edit_errand = function (errand, is_author) {
        errand.is_author = is_author;
        open_edit_errand(errand).result.then(
            function (rslt) {
            var result = rslt[0],
                exec = rslt[1];
            UserErrand.edit_errand(result, exec).then(reload_errands);
        },
            function(){
            if (!is_author && !errand.reading_date){
            UserErrand.mark_as_read(errand).then(reload_errands);
            }
        })
    };

    $scope.delete_errand = function (errand) {
        UserErrand.delete_errand(errand).then(reload_errands);
    };

    var open_edit_errand = function(e){
        var scope = $scope.$new();
        scope.model = e;
        return $modal.open({
            templateUrl: '/WebMis20/RISAR/modal/create_errand.html',
            scope: scope,
            resolve: {
                model: function () {return e}
            },
            size: 'lg'
        })
    }
    $scope.reset_filters();
    $scope.reload_errands = reload_errands;
    $scope.$watchCollection('query', function () {
        reload_errands();
    });
}