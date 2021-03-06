/**
 * Created by mmalkov on 11.07.14.
 */
var IndexCtrl = function ($scope, $modal, PrintingService) {
    $scope.aux = aux;
    $scope.query = "";
    var ps = $scope.ps = new PrintingService('free');
    ps.set_context('free');

    var outer_print = function (data, callback) {
        ps.print_template(data, false).then(angular.noop, callback);
    };

    $scope.print_template = function (template) {
        var model = {};
        template.meta.map(function (variable) {
            model[variable.name] = variable.default;
        });

        function prepare_data () {
            var context = {};
            template.meta.map(function (meta) {
                var name = meta.name;
                var typeName = meta['type'];
                var value = model[name];
                if (typeName == 'Integer')
                    context[name] = parseInt(value);

                else if (typeName == 'Float')
                    context[name] = parseFloat(value);

                else if (typeName == 'Boolean')
                    context[name] = Boolean(value);

                else if (['Organisation', 'OrgStructure', 'Person', 'Service', 'MKB'].has(typeName))
                    context[name] = value ? value.id : null;

                else if (typeName == 'SpecialVariable') {
                    if (!('special_variables' in context))
                        context['special_variables']={};
                    context['special_variables'][name] = meta['arguments'];
                }

                else context[name] = value
            });
            return {
                template_id: template.id,
                context: context
            }
        }
        if (template.meta.length > 0) {
            $modal.open({
                templateUrl: 'modal-print.html',
                controller: function ($scope, $modalInstance) {
                    // For view
                    $scope.ps = ps;
                    $scope.model = model;
                    $scope.template = template;

                    $scope.print = function () {
                        outer_print([prepare_data()], angular.bind($scope, $scope.close))
                    };
                    $scope.cancel = function () {
                        $modalInstance.dismiss('cancel');
                    };
                },
                size: 'lg'
            });
        } else {
            outer_print([prepare_data()], angular.noop);
        }
    }
};
