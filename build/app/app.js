var lazyLoadedModules = [
    {
        name: 'ngDialog',
        files: [
            "vendors/lazy/ngDialog/css/ngDialog.min.css",
            "vendors/lazy/ngDialog/css/ngDialog-theme-plain.min.css",
            "vendors/lazy/ngDialog/js/ngDialog.min.js"
        ]
    }
];

"use strict"; // execute the code in strict mode

// The angular module
var $app = angular.module('core', [
    'ui.router', 
    'oc.lazyLoad'
]);

// Constants
$app.constant('LAYOUT_WIDTHS', {
    'desktopLG': 1200,
    'desktop': 992,
    'tablet': 768,
    'mobile': 480
});

// Configuration
$app.config(['$urlRouterProvider', '$ocLazyLoadProvider', function($urlRouterProvider, $ocLazyLoadProvider){
    $urlRouterProvider.otherwise('/');
    $ocLazyLoadProvider.config({
        debug: false,
        events: true,
        modules: lazyLoadedModules
    });
}]);

// Initialisation
$app.run(['$rootScope', function($rootScope){
    $rootScope.pendingRequests = 0;
}]);

// The application instance
var app = modular.app($app);

app.init();

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

$app.factory('$menu', function(){
    return app.menu;
});

$app.constant('LHCBPR_PARAMS', {
    "api1": "http://127.0.0.1:8000/",
    "api": "https://test-lhcb-pr2.web.cern.ch/test-lhcb-pr2/api/"
});

$app.service('api', ["Restangular", "LHCBPR_PARAMS", '$rootScope', function(Restangular, lhcbpr_params, $rootScope) {
    var url = lhcbpr_params.api;
    Restangular.setBaseUrl(url);
    Restangular.setJsonp(true)
    Restangular.setDefaultRequestParams('jsonp', {format: 'jsonp', callback: 'JSON_CALLBACK'});
    Restangular.setDefaultHttpFields({cache: true});

    Restangular.setResponseExtractor(function(response, operation, what, url) {
        if (operation === "getList" && response.hasOwnProperty("results")) {
            // Use results as the return type, and save the result metadata
            // in _resultmeta
            var newResponse = response.results;
            newResponse._resultmeta = {
                "count": response.count,
                "next": response.next,
                "previous": response.previous
            };
            response = newResponse;
        }
        $rootScope.pendingRequests --;
        return response;
    });

    Restangular.addRequestInterceptor(function(element, operation, what, url){
        $rootScope.pendingRequests ++;
        return element;
    });

    return Restangular;
}]
);
