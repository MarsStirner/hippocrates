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
        $http.get(Config.url.schedule, {
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
    this.event = function () {
        var event_id = arguments[0];
        var ticker_id = arguments[1];
        var defer = $q.defer();
        $http.get(Config.url.event + (event_id)?(event_id):'', {
            params: {
                ticket_id: ticker_id
            }
        }).success(function (data) {
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