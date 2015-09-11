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
