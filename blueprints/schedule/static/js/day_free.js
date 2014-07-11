/**
 * Created by mmalkov on 11.07.14.
 */
var DayFreeCtrl = function ($scope, $http) {
    $scope.aux = aux;
    var params = aux.getQueryParams(location.search);

    $scope.destination = null;
    $scope.destinationDate = new Date();
    $scope.destinationPerson = null;

    $scope.source = null;
    $scope.sourceDate = moment(params.date);
    $scope.sourcePerson = null;

    $scope.reception_type = 'amb';
    $scope.day = null;

    $scope.selectedSourceTicket = null;

    $scope.reloadSchedule = function () {
        if ($scope.destinationPerson == null) return;
        $http.get(url_schedule_api_schedule, {
            params: {
                person_ids: $scope.destinationPerson.id,
                start_date: moment($scope.destinationDate).format('YYYY-MM-DD'),
                one_day: true
            }
        }).success(function (data) {
            if (data.result.schedules.length !== 1) {
                $scope.destination = null;
                return;
            }
            $scope.roa = false;
            $scope.day = data.result.schedules[0].grouped[$scope.reception_type].schedule[0];
            $scope.destination = aux.forEach(data.result.schedules[0].grouped, function (group) {
                $scope.roa |= Boolean(group.schedule[0].roa);
                return group.schedule[0].tickets;
            });
        });
    };

    var loadSchedule = function () {
        $http.get(url_schedule_api_schedule, {
            params: {
                person_ids: params.person_id,
                start_date: $scope.sourceDate.format('YYYY-MM-DD'),
                one_day: true
            }
        }).success(function (data) {
            if (data.result.schedules.length !== 1) {
                $scope.source = null;
                return;
            }
            $scope.sourcePerson = data.result.schedules[0].person;
            $scope.source = aux.forEach(data.result.schedules[0].grouped, function (group) {
                return group.schedule[0].tickets;
            });
        }).then(function () {
            $scope.selectedSourceTicket = null;
        });
    };

    $scope.selectSourceTicket = function (ticket) {
        $scope.selectedSourceTicket = ticket;
    };

    $scope.pasteSourceTicket = function (ticket) {
        if (!$scope.selectedSourceTicket) return;
        if (ticket.status !== 'free') return;
        $http.post(url_schedule_api_move_client, {
            ticket_id: $scope.selectedSourceTicket.id,
            destination_ticket_id: ticket.id
        })
            .success($scope.reloadSchedule)
            .success(loadSchedule)
    };

    $scope.$on('PersonSelected', function (event, person) {
        $scope.destinationPerson = person;
        $scope.reloadSchedule();
    });

    $scope.back2monthview = function () {
        window.open(url_schedule_html_person_schedule_monthview + '?person_id=' + params.person_id, '_self')
    };

    loadSchedule();
};
WebMis20.controller('DayFreeCtrl', ['$scope', '$http', DayFreeCtrl]);
