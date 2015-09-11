/**
 * A class representing a controller
 */

var Controller = function(functions){
    this.functions = functions || [];
}

Controller.prototype.add = function(fn) {
    this.functions.push(fn);
}

Controller.prototype.getServicesUsedIn = function(fn) {
    var services = [];
    var parameters = fn.getParameterNames();
    if(parameters.length > 0){
        var servicesParameterName = parameters[0];
        services = fn.getAttributesOf(servicesParameterName);
    }
    return services;
}

Controller.prototype.getAngularController = function() {
    var self = this;
    var ctrl = [];
    self.functions.forEach(function(fn){
        ctrl = ctrl.concat(self.getServicesUsedIn(fn));
    });
    ctrl = ctrl.unique();
    ctrl.push(function(){
        var services = {};
        var size = arguments.length;
        for(var i = 0; i < size; i ++)
            services[ctrl[i]] = arguments[i];

        self.functions.forEach(function(fn){
            fn(services);
        });
    });
    return ctrl;
}
