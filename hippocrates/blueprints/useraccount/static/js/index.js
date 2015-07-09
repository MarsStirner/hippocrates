/**
 * Created by mmalkov on 11.07.14.
 */
var IndexCtrl = function ($scope, $timeout, ApiCalls, WMConfig, Simargl, CurrentUser, NotificationService, SelectAll) {
    $scope._ = _;
    $scope.mode = 0;
    $scope.messages = [];
    $scope.messages_count = 0;
    $scope.messages_folder_count = 0;
    $scope.messages_unread = 0;
    $scope.skip = 0;
    $scope.limit = 10;
    $scope.current_folder = 'inbox';
    $scope.select_all = new SelectAll([]);
    var get_mail = _.partial(ApiCalls.wrapper, 'GET', WMConfig.url.api_user_mail),
        mark_read = _.partial(ApiCalls.wrapper, 'POST', WMConfig.url.api_user_mail_read),
        mark_star = _.partial(ApiCalls.wrapper, 'POST', WMConfig.url.api_user_mail_mark),
        move_mail = _.partial(ApiCalls.wrapper, 'POST', WMConfig.url.api_user_mail_move);
    Simargl.subscribe('mail', reload_messages);
    function set_summary (result) {
        $scope.messages_count = result.count;
        $scope.messages_inbox_count = result.inbox_count || $scope.messages_inbox_count;
        $scope.messages_unread = result.unread;
        return result
    }
    function reload_messages () {
        get_mail({
            skip: $scope.skip || undefined,
            folder: $scope.current_folder
        }).then(set_summary).then(function (result) {
            if (result.messages) {
                $scope.select_all.setSource(_.pluck(result.messages, 'id'));
                $scope.select_all.selectNone();
                $scope.messages = result.messages;
            }
        });
    }
    $scope.reload_messages = reload_messages;
    Simargl.when_ready(reload_messages);
    $scope.view_mail = function (message) {
        if (message.recipient.id == CurrentUser.id && !message.read) {
            mark_read({ids: message.id}).then(set_summary).then(function () {
                message.read = 1;
                $scope.message = message;
                $scope.mode = 1;
            })
        } else {
            $scope.message = message;
            $scope.mode = 1;
        }
    };
    $scope.list_mail = function () {
        $scope.mode = 0;
    };
    $scope.compose_mail = function (message) {
        $scope.mode = 2;
        if (message !== undefined) {
            $scope.message = {
                to: message.sender,
                parent_id: message.id
            }
        } else {
            $scope.message = {};
        }
    };
    $scope.send_mail = function (message) {
        ApiCalls.coldstar('POST', WMConfig.url.simargl.simargl_rpc, undefined, {
            topic: 'mail:new',
            recipient: message.to.id,
            sender: CurrentUser.id,
            data: {
                subject: message.subject,
                text: message.text,
                parent_id: message.parent_id
            },
            ctrl: true
        }, {allowCredentials: true}).then(function () {
            NotificationService.notify(undefined, 'Письмо успешно отправлено', 'success', 5000);
            $scope.mode = 0;
        }, function () {
            NotificationService.notify(undefined, 'Не удалось отправить письмо', 'danger', 5000);
        })
    };
    $scope.change_skip = function (amount) {
        var prev = $scope.skip,
            next = _.max([0, _.min([$scope.skip + amount, $scope.messages_count - $scope.limit])]);
        if (prev != next) {
            $scope.skip = next;
            reload_messages();
        }
    };
    $scope.change_folder = function (name) {
        $scope.current_folder = name;
        $scope.skip = 0;
        $scope.mode = 0;
        reload_messages();
    };
    var format_ids = function (idlist) {
        if (idlist instanceof Array) {
            return idlist.join(':')
        } else {
            return idlist
        }
    };
    $scope.mark_star = function (selected) {
        mark_star({
            ids: selected.id,
            mark: (selected.mark)?(0):(1)
        }).then(reload_messages)
    };
    $scope.delete_selected = function () {
        move_mail({
            ids: format_ids($scope.select_all.selected()),
            folder: 'trash'
        }).then(reload_messages)
    };
};
angular.module('WebMis20')
.service('misPerson', function ($q, ApiCalls) {
        var cache = {};
        var promise = function (promise) {
            var d = $q.defer();
            promise.then(function (result) {
                d.resolve(result);
                return result;
            });
            return d.promise;
        };
        this.get = function (id) {
            if (!_.has(cache, id)) {
                cache[id] = ApiCalls.wrapper('GET', '/user/api/persons/{0}'.format(id)).then(function (result) {
                    cache[id] = result;
                    return result;
                });
                return promise(cache[id])
            } else if (_.has(cache[id], 'then')) {
                return promise(cache[id])
            } else {
                var d = $q.defer();
                d.resolve(cache[id]);
                return d.promise;
            }
        }
    });