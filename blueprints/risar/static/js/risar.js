/**
 * Created by mmalkov on 24.09.14.
 */
'use strict';

WebMis20
.service('RisarApi', ['$http', 'Config', '$q', function ($http, Config, $q) {
    this.schedule = function () {
        var date = arguments[0];
        var all = arguments[1];
        var defer = $q.defer();
        $http.get(Config.url.api_schedule, {
            params: {
                date: (date)?(moment(date).format('YYYY-MM-DD')):undefined,
                all: all
            }
        }).success(function (data) {
            if (data.meta.code != 200) {
                defer.reject(data.meta)
            } else {
                defer.resolve(data.result);
            }
        });
        return defer.promise;
    };
    this.chart = function () {
        var event_id = arguments[0];
        var ticket_id = arguments[1];
        var defer = $q.defer();
        var url = Config.url.api_chart;
        url += (event_id)?(event_id):'';
        $http.get(url, {
            params: {
                ticket_id: ticket_id
            }
        }).success(function (data) {
            if (data.meta.code != 200) {
                defer.reject(data.meta)
            } else {
                defer.resolve(data.result);
            }
        });
        return defer.promise;
    };
    this.anamnesis = function (event_id) {
        var defer = $q.defer();
        var url = Config.url.api_anamnesis + event_id;
        $http.get(url).success(function (data) {
            if (data.meta.code != 200) {
                defer.reject(data.meta)
            } else {
                defer.resolve(data.result);
            }
        });
        return defer.promise;
    }
}])
;