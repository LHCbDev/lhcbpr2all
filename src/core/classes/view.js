/**
 * the view class
 */

var View = function(module, params){
    this.module = module;
    this.name = params.name;
    this.title = params.title || params.name;
    this.controller = new Controller();
    this.controller.add(this.initController());
    if(params.controller)
        this.controller.add(params.controller);
    this.template = params.template || params.name + '.html';
    this.vendors = params.vendors || [];
}

View.prototype.initController = function() {
    var self = this;
    return function(services){
        services.$rootScope.title = self.title + ' - ' + self.module.title + ' - ';
    };
}

View.prototype.compile = function() {
    // Adding state
    this.module.app.addState(this.module.name + '.' + this.name, {
        url: '/' + this.name,
        templateUrl: 'modules/' + this.module.name + '/views/' + this.template,
        controller: this.controller.getAngularController(),
        resolve: this.vendors
    });
    
    // Adding view to the sidebar
    this.module.addMenuItems({
        text: this.title,
        href: this.module.name + '/' + this.name,
        icon: "fa fa-laptop"
    });
}
