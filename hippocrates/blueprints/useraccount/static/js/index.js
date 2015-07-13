/**
 * Created by mmalkov on 11.07.14.
 */
var IndexCtrl = function ($scope, $timeout, UserMail, SelectAll, CurrentUser) {
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
    UserMail.subscribe('unread', set_common_summary);
    UserMail.subscribe('ready', reload_messages);

    function set_common_summary (result) {
        $scope.messages_inbox_count = result.inbox_count || $scope.messages_inbox_count;
        $scope.messages_unread = result.unread;
        return result
    }
    function set_summary (result) {
        $scope.messages_count = result.count;
        return result
    }
    function reset_messages (result) {
        if (result.messages) {
            $scope.select_all.setSource(_.pluck(result.messages, 'id'));
            $scope.select_all.selectNone();
            $scope.messages = result.messages;
        }
    }
    function reload_messages () {
        UserMail.get_mail($scope.current_folder, $scope.skip || undefined, $scope.limit || undefined)
            .then(set_summary)
            .then(reset_messages);
    }
    $scope.reload_messages = reload_messages;
    $scope.view_mail = function (message) {
        if (message.recipient.id == CurrentUser.id && !message.read) {
            UserMail.set_mark('read', message.id, true).then(function () {
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
        reload_messages();
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
        UserMail.send_mail(message.to.id, message.subject, message.text, message.parent_id);
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
    $scope.mark_star = function (selected) {
        UserMail.set_mark('mark', selected.id, (!selected.mark)?(true):(false)).then(reload_messages)
    };
    $scope.delete_selected = function () {
        UserMail.mail_move('trash', $scope.select_all.selected()).then(reload_messages);
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