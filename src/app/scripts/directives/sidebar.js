$app.directive('sidebar', ['$window', 'LAYOUT_WIDTHS', '$menu', function ($win, mq, $menu) {
    return {
        restrict: 'E',
        templateUrl: 'app/views/directives/sidebar.html',
        scope: {},
        link: function($scope, $element, $attrs){
            $scope.isCollapsed = true;
            $scope.menuItems = $menu.getItems().sort(function(a, b){
                return b.position < a.position;
            });
            $scope.$watch($menu.getItems, function(){
                $scope.menuItems = $menu.getItems().sort(function(a, b){
                    return b.position < a.position;
                });
            });
        }
    }
}]);
