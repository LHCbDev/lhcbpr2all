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
