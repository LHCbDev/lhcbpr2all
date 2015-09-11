var HomeController = function(services){
    services.$scope.message = 'Yes I am working !';
};

pages.addView({
    name: 'home',
    title: 'Home page',
    controller: HomeController
}).compile();
