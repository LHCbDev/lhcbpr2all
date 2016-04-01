/**
 * Class representing a module
 * This class abstracts a group of menu items and routes
 * to add to the angular application
 */

/**
 * Module Constructor
 * @param {string} name      name of the module
 * @param {string} title     title to show in the sidebar
 * @param {int}    position  position of modules links in the sidebar menu
 * @param {Object} settings  Additional settings
 */
var Module = function(name, title, position, settings){
	this.name = name;
	this.menu = {
	    text: title,
	    position: position,
	    sref: "#",
	    icon: "icon-doc",
	    submenu: []
	};
	if(undefined !== settings && undefined !== settings.folder)
		this.folder = settings.folder;
	else
		this.folder = name;
	this.states = [];
	this.$app = App; // referencing the angular application
	Deps.addModules([{
		name: name,
		files: ['app/modules/' + name + '/all.js', 'app/modules/' + name + '/style.css']
	}]);
};

Module.create = function(name, title, position, settings){
	return new Module(name, title, position, settings);
}

Module.prototype.addMenuItems = function(items){
	var self = this;
	if(Array === items.constructor)
		items.forEach(function(item){
			self.menu.submenu.push(item);
		});
	else
		self.menu.submenu.push(items);
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
