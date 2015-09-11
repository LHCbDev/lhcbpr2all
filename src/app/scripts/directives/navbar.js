$app.directive('navbar', ['$rootScope', '$menu', function ($rootScope, $menu) {
    return {
        restrict: 'E',
        templateUrl: 'app/views/directives/navbar.html',
        scope: {},
        link: function($scope, $element, $attrs) {
            $rootScope.showSideBar = true;

            $scope.toggleSideBar = function(){
                $rootScope.showSideBar = ! $rootScope.showSideBar;
            }
        }
    }
}]);
