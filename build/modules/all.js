var pages = app.addModule('pages', 'Pages Module', 1);

var trends = app.addModule('trends', 'Trends Module', 2);

var HomeController = function(services){
    services.$scope.message = 'Yes I am working !';
};

pages.addView({
    name: 'home',
    title: 'Home page',
    controller: HomeController
}).compile();

var TrendsController = function(services){
    services.ngDialog.open({
        template: '<h1> Hey there !</h1>',
        plain: true
    });
};

trends.addView({
    name: 'trends',
    title: 'Trends',
    controller: TrendsController,
    vendors: ['ngDialog']
}).compile();
