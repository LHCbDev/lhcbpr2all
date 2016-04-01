/**
 * Class holding the list of all dependencies
 */

var Deps = function() {};

Deps.all = {
	libraries: {},
	angularModules: [],
	modules: {}
};
Deps.$app = App;
Deps.commonModules = ['be-responsive'];

Deps.add = function(type, name, files) {
	if (undefined !== Deps.all[type][name])
		console.error('"' + name + '" exists already !');
	else {
		if (typeof name !== 'string')
			console.error('name should be a string !');
		else if (Array !== files.constructor)
			console.error('files should be an array !');
		else
			Deps.all[type][name] = files;
	}
};

Deps.addLibraries = function(libs) {
	if (Array !== libs.constructor)
		console.error('argument should be an array !');
	else
		libs.forEach(function(lib) {
			Deps.add('libraries', lib.name, lib.files);
		});
};

Deps.addAngularModules = function(modules) {
	if (Array !== modules.constructor)
		console.error('argument should be an array !');
	else
		modules.forEach(function(lib) {
			Deps.add('angularModules', lib.name, lib.files);
		});
};

Deps.addModules = function(modules) {
	if (Array !== modules.constructor)
		console.error('argument should be an array !');
	else
		modules.forEach(function(lib) {
			Deps.add('modules', lib.name, lib.files);
		});
};

Deps.get = function(name) {
	files = [];
	categories = ['libraries', 'modules'];
	categories.forEach(function(category) {
		if (undefined !== Deps.all[category][name])
			Deps.all[category][name].forEach(function(file) {
				files.push(file);
			});
	});
	if(-1 !== Deps.all.angularModules.indexOf(name))
		files.push(name);
	if(files.length === 0)
		return null;
	return files;
};

Deps.addCommonModules = function(modules){
	if (Array !== modules.constructor){
		modules.forEach(function(module){
			if( Deps.commonModules.indexOf(module) === -1 ){
				Deps.commonModules.push(module);
			}
		});
	} else {
		if( Deps.commonModules.indexOf(modules) === -1 ){
			Deps.commonModules.push(modules);
		}
	}
}
