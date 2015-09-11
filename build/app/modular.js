var modular = (function(angular, undefined){
    'use strict';
    var modular = {};

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

/** The Menu class
 *  It represents the links on the sidebar
 */

/**
 * Constructor
 */
var Menu = function(app){
    this.app = app;
    this.items = [];
}

/**
 * Add items to the menu
 */
Menu.prototype.add = function(item) {
    var self = this;
    if(Array === item.constructor){
        item.forEach(function(element){
            self.add(element);
        });
    } else {
        self.items.push(item);
    }
};

/**
 * Getter for all items
 */
Menu.prototype.getItems = function() {
    return this.items;
};

/**
 * Class representing a module of the application
 */

/**
 * Module Constructor
 * @param {string} name      name of the module
 * @param {string} title     title to show in the sidebar
 * @param {int}    position  position of modules links in the sidebar menu
 * @param {Object} settings  Additional settings
 */
var Module = function(app, name, title, position, settings){
    this.app = app;
    this.name = name;
    this.title = title;
    this.app.addState(this.name, {
        url: '/' + this.name,
        abstract: true,
        template: '<div ui-view></div>'
    });

    this.app.menu.add({
        text: title,
        position: position,
        href: '#',
        icon: "fa fa-server",
        childs: []
    });
    this.menu = this.app.menu.items[this.app.menu.items.length - 1];

    if(undefined !== settings && undefined !== settings.folder)
        this.folder = settings.folder;
    else
        this.folder = name;
    this.states = [];

    this.views = {};

    // Deps.addModules([{
    //     name: name,
    //     files: ['app/modules/' + name + '/all.js', 'app/modules/' + name + '/style.css']
    // }]);
};

Module.prototype.addView = function(params) {
    if(this.views[params.name] != undefined)
        throw new Error('Duplicated view name "' + params.name + '" on the module "' + this.name + '"');
    else {
        this.views[params.name] = new View(this, params);
        return this.views[params.name];
    }
};

Module.prototype.addMenuItems = function(items){
    var self = this;
    if(Array === items.constructor)
        items.forEach(function(item){
            self.menu.childs.push(item);
        });
    else
        self.menu.childs.push(items);
    return this;
};

Module.prototype.addStates = function(states){
    var self = this;
    if(Array === states.constructor)
        states.forEach(function(state){
            self.addState(state);
        });
    else
        self.addState(states);
    return this;
};

Module.prototype.addState = function(state){
    if(undefined === state.name){
        console.error('Cannot add a state without a name !');
        return;
    }
    // words in the last name (after last '.')
    // assuming that words are seperated with '_'
    var words = state.name.split('.');
    words = words[words.length - 1];
    words = words.split('_');
    if(undefined === state.url){
        state.url = '/' + words.join('-');
    }
    if(undefined === state.title){ 
        var parts = [];
        for(var i in words)
            parts.push(words[i].charAt(0).toUpperCase() + words[i].substr(1));
        state.title = parts.join(' ');
    }
    if(undefined === state.templateUrl && undefined === state.template){
        state.templateUrl = 'app/modules/' + this.folder + '/views/' + words.join('-') + '.html';
    } else if(undefined !== state.templateUrl){
        state.templateUrl = 'app/modules/' + this.folder + '/views/' + state.templateUrl;
    }
    if(undefined === state.controller){
        state.controller = [];
        var parts = state.name.split('.');
        parts.forEach(function(part){
            part.split('_').forEach(function(word){
                state.controller.push(word.charAt(0).toUpperCase() + word.substr(1));
            });
        });
        state.controller = state.controller.join('') + 'Controller';
    }
    if(undefined !== state.resolve){
        Deps.commonModules.forEach(function(cm){
            state.resolve.push(cm);
        });
        state.resolve = this.makePromises(state.resolve);
    } else {
        state.resolve = this.makePromises(Deps.commonModules);
    }
    
    state.name = 'app.' + state.name;
    this.states.push(state);
    return this;
};

Module.prototype.makePromises = function(deps) {
    return {
        loadDeps: ['$ocLazyLoad', '$q', function($ll, $q){
            var promise = $q.when(1);
            deps.forEach(function(dep){
                if(typeof dep === 'function')
                    promise = promise.then(dep);
                else
                    promise = promise.then(function(){
                        var files = Deps.get(dep);
                        if(null === files)
                            return $.error('Cannot find the dependency : "' + dep + '" !');
                        return $ll.load(files);
                    });
            });
            return promise;
        }]
    };
};

Module.prototype.start = function(){
    var self = this;
    // Adding menu items
    this.$app.run(['$rootScope', function($rootScope){
        $rootScope.menuItems.push(self.menu);
    }]);
    // Adding routes
    this.$app.config(['$stateProvider', function($stateProvider){
        self.states.forEach(function(state){
            $stateProvider.state(state.name, state);
        });
    }]);
};

/**
 * The vendor collection class
 * It handles the list of vendors and dependencies
 */

var VendorCollection = function(){
    this.modules = {};
    this.ngModules = {};
    this.libs = {};
}

VendorCollection.prototype.addModule = function(name) {
    // ...
};

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

/**
 * Additional methods to the Array class
 */

/**
 * Gets array elements without duplicates
 */
Array.prototype.unique = function(){
    var index = {}, 
        list = [],
        size = this.length;
    for(var i = 0; i < size; i++){
        if(index.hasOwnProperty(this[i]))
            continue;
        list.push(this[i]);
        index[this[i]] = 1;
    }
    return list;
}

/**
 * Additional methods for the Function objects
 */

/**
 * Gets list of parameter names of the function
 */
Function.prototype.getParameterNames = function() {
    return this.toString()
        .between('(', ')')
        .split(',')
        .map(function(name){
            return name.trim();
        })
        .filter(function(name){
            return name != '';
        });
}

/**
 * Gets the attributes of a var used in the code of the function
 * @param  {String} name The name of the var
 */
Function.prototype.getAttributesOf = function(name) {
    var regex = new RegExp("[^a-zA-Z0-9_$]+"  + name + "\\.[0-9a-zA-Z_$]+", 'g');
    var matches = this.toString().match(regex);
    if(matches)
        return matches.unique().map(function(expr){
            var parts = expr.split('.');
            return parts[1];
        });
    return [];
}

/**
 * Additional methods to the String class
 */

String.prototype.between = function(a, b) {
    var result = null;
    var indexA = this.indexOf(a);
    if(indexA != -1){
        var indexB = this.indexOf(b, indexA);
        if(indexB != -1 && indexB > indexA)
            result = this.substring(indexA + 1, indexB);
    }
    return result;
}

modular.app = function(ngModule){
    return new Application(ngModule);
};

    return modular;
})(angular);
