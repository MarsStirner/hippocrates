//TODO: Refactoring: унести в nemesis
angular.module('hitsl.core')
.service('CurrentUser', ['$http', function ($http) {
    var self = this;
    angular.extend(self, {{ current_user | tojson | safe }});
    this.get_main_user = function () {
        return this.master || this;
    };
    this.has_right = function () {
        return [].clone.call(arguments).filter(aux.func_in(this.get_user().rights)).length > 0;
    };
    this.has_role = function () {
        return [].clone.call(arguments).filter(aux.func_in(this.roles)).length > 0;
    };
    this.current_role_in = function () {
        return [].clone.call(arguments).has(this.current_role);
    };
}]);