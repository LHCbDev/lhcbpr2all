/**
 * The application class
 */

/**
 * Application constructor
 * @param {Object} angularModule The angular module managed by the application
 */
var Application = function (angularModule) {
    this.$app = angularModule;
    this.modules = {};
    this.vendors = new VendorCollection;
    this.menu = new Menu(this);
    // this.services = new ServicesHandler($app);
    this.init();
}

/**
 * The angular module getter
 */
Application.prototype.ng = function() {
    return this.$app;
}

/**
 * The application initialization
 */
Application.prototype.init = function() {
    // ...
}

/**
 * Adds a new module to the application
 * @param {string} name
 * @return {Module}
 */
Application.prototype.addModule = function(name, title, position, setts) {
    if(this.modules[name] != undefined)
        throw new Error('Duplicated module name: "' + name + '"');
    this.modules[name] = new Module(this, name, title, position, setts);
    this.vendors.addModule(name);
    return this.modules[name];
}

/**
 * Gets a module of the application by name or null if not found
 * @param {string} name the name of the module
 * @return {Module}
 */
Application.prototype.getModule = function(name) {
    return this.modules[name] || null;
}

/**
 * Adds new state to the angular module
 * @param {string} name 
 * @param {Object} setts
 */
Application.prototype.addState = function(name, setts) {
    if(setts.resolve !== undefined && setts.resolve.length > 0){
        setts.resolve = this.makeResolvePromises(setts.resolve);
    }
    this.$app.config(['$stateProvider', function($stateProvider){
        $stateProvider.state(name, setts);
    }]);
}

/**
 * 
 */
Application.prototype.makeResolvePromises = function(deps) {
    return {
        loadDeps: ['$ocLazyLoad', '$q', function($ll, $q){
            var promise = $q.when(1);
            deps.forEach(function(dep){
                if(typeof dep === 'function')
                    promise = promise.then(dep);
                else
                    promise = promise.then(function(){
                        return $ll.load(deps);
                    });
            });
            return promise;
        }]
    };
};
