// ============================================================================
var gulp        = require('gulp'),
		changed     = require('gulp-changed'),
		concat      = require('gulp-concat'),
		connect		= require('gulp-connect'),
		expect      = require('gulp-expect-file'),
		flip        = require('css-flip'),
		fs 			= require('fs'),
		gulpFilter  = require('gulp-filter'),
		gulpsync    = require('gulp-sync')(gulp),
		gutil       = require('gulp-util'),
		jade        = require('gulp-jade'),
		less        = require('gulp-less'),
		livereload  = require('gulp-livereload'), // Livereload plugin needed: https://chrome.google.com/webstore/detail/livereload/jnihajbhpnppcggbcgedagnkighmdlei
		marked      = require('marked'), // For :markdown filter in jade
		merge 		= require('merge-stream'),
		minifyCSS   = require('gulp-minify-css'),
		ngAnnotate  = require('gulp-ng-annotate'),
		ngConstant  = require('gulp-ng-constant'),
		path        = require('path'),
		PluginError = gutil.PluginError,
		prettify    = require('gulp-html-prettify'),
		rename      = require('gulp-rename'),
		sourcemaps  = require('gulp-sourcemaps'),
		through     = require('through2'),
		uglify      = require('gulp-uglify'),
		w3cjs       = require('gulp-w3cjs');
// ============================================================================

// ignore everything that begins with underscore
var hidden_files = '**/_*.*';
var ignored_files = '!'+hidden_files;
// ============================================================================
// BUILD PARAMS
// ============================================================================
var params = {
	dist: gutil.env.output || '../../dist/dev',
    url_api: gutil.env.urlapi || 'http://lblhcbpr2.cern.ch:8080/api',
    url_root: gutil.env.urlroot || 'http://lblhcbpr2.cern.ch:8081',
    port: gutil.env.port || '9000',
    lvr_port: gutil.env.liveport || 35729,
	minify:  gutil.env.minify !== undefined,
	sourcemaps: gutil.env.sourcemaps !== undefined
};


// ============================================================================
// VENDOR CONFIG
var vendor = {
	// vendor scripts required to start the app
	base: {
		source: require('./vendor.base.json'),
		dest: params.dist + '/app/js',
		name: 'base.js'
	},
	// vendor scripts to make to app work. Usually via lazy loading
	app: {
		source: require('./vendor.json'),
		dest: params.dist + '/vendor'
	}
};
// ============================================================================
// SOURCES CONFIG 
var source = {
	scripts: {
		app:    [   'js/init.js',
					'js/classes/*.js',
					'js/*.js',
					'js/controllers/*.js',
					'js/directives/*.js',
					'js/directives/custom/*.js',
					'js/services/*.js',
					'js/filters/*.js',
					'modules/*/js/init.js'
				],
		watch: ['js/**/*.js', 'modules/**/*.js']
	},
	templates: {
		app: {
				files : ['jade/index.jade'],
				watch: ['jade/index.jade', hidden_files]
		},
		views: {
				files : ['jade/views/*.jade', 'jade/views/**/*.jade', ignored_files],
				watch: ['jade/views/**/*.jade', 'modules/*/views/**/*.jade']
		},
		pages: {
				files : ['jade/pages/*.jade'],
				watch: ['jade/pages/*.jade']
		}
	},
	styles: {
		app: {
			main: ['less/app.less', '!less/themes/*.less'],
			dir:  'less',
			watch: ['less/*.less', 'less/**/*.less', '!less/themes/*.less']
		},
		themes: {
			main: ['less/themes/*.less', ignored_files],
			dir:  'less/themes',
			watch: ['less/themes/*.less']
		},
	},
	bootstrap: {
		main: 'less/bootstrap/bootstrap.less',
		dir:  'less/bootstrap',
		watch: ['less/bootstrap/*.less']
	}
};
// ============================================================================
// BUILD TARGET CONFIG 
var build = {
	scripts: {
		app: {
			main: 'app.js',
			dir: params.dist + '/app/js'
		}
	},
	styles: params.dist + '/app/css',
	templates: {
		app: params.dist,
		views: params.dist + '/app/views',
		pages: params.dist + '/app/pages'
	}
};
// ============================================================================
// TASKS
// ============================================================================
// JS APP
// ----------------------------------------------------------------------------
gulp.task('scripts:app', function() {
		// Minify and copy all JavaScript (except vendor scripts)
		ngConstant(
			{
				stream: true,
				name: "buildParams",
				constants: {
					BUILD_PARAMS: {
						url_api: params.url_api,
						url_root: params.url_root
					}
				}
			}).pipe(gulp.dest(build.scripts.app.dir));
		return  gulp.src(source.scripts.app)
				.pipe( params.sourcemaps ? sourcemaps.init() : gutil.noop())
				.pipe(concat(build.scripts.app.main))
				.pipe(ngAnnotate())
				.on("error", handleError)
				.pipe( params.minify ? uglify({preserveComments:'some'}) : gutil.noop() )
				.on("error", handleError)
				.pipe( params.sourcemaps ? sourcemaps.write('.') : gutil.noop() )
				.pipe(gulp.dest(build.scripts.app.dir));
});

// ----------------------------------------------------------------------------
// VENDOR BUILD
// ----------------------------------------------------------------------------
gulp.task('scripts:vendor', ['scripts:vendor:base', 'scripts:vendor:app']);

//  This will be included vendor files statically
gulp.task('scripts:vendor:base', function() {

		// Minify and copy all JavaScript (except vendor scripts)
		return gulp.src(vendor.base.source)
				.pipe(expect(vendor.base.source))
				//.pipe(uglify())
				.pipe(concat(vendor.base.name))
				.pipe(gulp.dest(vendor.base.dest))
				;
});

// copy file from bower folder into the app vendor folder
gulp.task('scripts:vendor:app', function() {
	
	var jsFilter = gulpFilter('**/*.js');
	var cssFilter = gulpFilter('**/*.css');

	return gulp.src(vendor.app.source, {base: 'bower_components'})
			.pipe(expect(vendor.app.source))
			.pipe(jsFilter)
			.pipe(uglify())
			.pipe(jsFilter.restore())
			.pipe(cssFilter)
			.pipe(minifyCSS())
			.pipe(cssFilter.restore())
			.pipe( gulp.dest(vendor.app.dest) );

});
// ----------------------------------------------------------------------------
// APP LESS
// ----------------------------------------------------------------------------
gulp.task('styles:app', function() {
		return gulp.src(source.styles.app.main)
				.pipe( params.sourcemaps ? sourcemaps.init() : gutil.noop())
				.pipe(less({
						paths: [source.styles.app.dir]
				}))
				.on("error", handleError)
				.pipe( params.minify ? minifyCSS({processImport: false}) : gutil.noop() )
				.pipe( params.sourcemaps ? sourcemaps.write('.') : gutil.noop())
				.pipe(gulp.dest(build.styles));
});
// ----------------------------------------------------------------------------
// APP RTL
// ----------------------------------------------------------------------------
gulp.task('styles:app:rtl', function() {
		return gulp.src(source.styles.app.main)
				.pipe( sourcemaps ? sourcemaps.init() : gutil.noop())
				.pipe(less({
						paths: [source.styles.app.dir]
				}))
				.on("error", handleError)
				.pipe(flipcss())
				.pipe( params.minify ? minifyCSS() : gutil.noop() )
				.pipe( sourcemaps ? sourcemaps.write('.') : gutil.noop())
				.pipe(rename(function(path) {
						path.basename += "-rtl";
						return path;
				}))
				.pipe(gulp.dest(build.styles));
});
// ----------------------------------------------------------------------------
// LESS THEMES
// ----------------------------------------------------------------------------
gulp.task('styles:themes', function() {
		return gulp.src(source.styles.themes.main)
				.pipe(less({
						paths: [source.styles.themes.dir]
				}))
				.on("error", handleError)
				.pipe(gulp.dest(build.styles));
});
// ----------------------------------------------------------------------------
// BOOTSTRAP
// ----------------------------------------------------------------------------
gulp.task('bootstrap', function() {
		return gulp.src(source.bootstrap.main)
				.pipe(less({
						paths: [source.bootstrap.dir]
				}))
				.on("error", handleError)
				.pipe(gulp.dest(build.styles));
});
// ----------------------------------------------------------------------------
// JADE APP
// ----------------------------------------------------------------------------
gulp.task('templates:app', function() {
		return gulp.src(source.templates.app.files)
				.pipe(changed(build.templates.app, { extension: '.html' }))
				.pipe(jade())
				.on("error", handleError)
				.pipe(prettify({
						indent_char: ' ',
						indent_size: 3,
						unformatted: ['a', 'sub', 'sup', 'b', 'i', 'u']
				}))
				.pipe(gulp.dest(build.templates.app))
				;
});
// ----------------------------------------------------------------------------
// JADE PAGES
// ----------------------------------------------------------------------------
gulp.task('templates:pages', function() {
		return gulp.src(source.templates.pages.files)
				.pipe(changed(build.templates.pages, { extension: '.html' }))
				.pipe(jade())
				.on("error", handleError)
				.pipe(prettify({
						indent_char: ' ',
						indent_size: 3,
						unformatted: ['a', 'sub', 'sup', 'b', 'i', 'u']
				}))
				.pipe(gulp.dest(build.templates.pages))
				;
});
// ----------------------------------------------------------------------------
// JADE VIEWS
// ----------------------------------------------------------------------------
gulp.task('templates:views', function() {
		return gulp.src(source.templates.views.files)
				.pipe(changed(build.templates.views, { extension: '.html' }))
				.pipe(jade())
				.on("error", handleError)
				.pipe(prettify({
						indent_char: ' ',
						indent_size: 3,
						unformatted: ['a', 'sub', 'sup', 'b', 'i', 'u']
				}))
				.pipe(gulp.dest(build.templates.views))
				;
});
// ----------------------------------------------------------------------------
// CONNECT
// ----------------------------------------------------------------------------
gulp.task('connect', function() {
	connect.server({
		root: params.dist,
		port: params.port,
		livereload: true
	});
});
// ----------------------------------------------------------------------------
// MODULES SCRIPTS
// ----------------------------------------------------------------------------
gulp.task('modules:scripts', function() {
	var modulesPath = 'modules';
	var folders = fs.readdirSync(modulesPath)
		.filter(function(file) {
			return fs.statSync(path.join(modulesPath, file)).isDirectory();
		});

	var tasks = folders.map(function(folder) {
		return gulp.src(['modules/' + folder + '/**/*.js', '!modules/' + folder + '/js/init.js'])
			.pipe(concat('all.js'))
			.pipe(gulp.dest(params.dist + '/app/modules/' + folder));
   });

   return merge(tasks);
});
// ----------------------------------------------------------------------------
// MODULES STYLES
// ----------------------------------------------------------------------------
gulp.task('modules:styles', function() {
	var modulesPath = 'modules';
	var folders = fs.readdirSync(modulesPath)
		.filter(function(file) {
			return fs.statSync(path.join(modulesPath, file)).isDirectory();
		});

	var tasks = folders.map(function(folder) {
		return gulp.src('modules/' + folder + '/less/style.less')
			.pipe(less({
				paths: ['modules/' + folder + '/less']
			}))
			.pipe(rename('style.css'))
			.pipe(gulp.dest(params.dist + '/app/modules/' + folder));
   });

   return merge(tasks);
});
// ----------------------------------------------------------------------------
// MODULES VIEWS
// ----------------------------------------------------------------------------
gulp.task('modules:views', function() {
	var modulesPath = 'modules';
	var folders = fs.readdirSync(modulesPath)
		.filter(function(file) {
			return fs.statSync(path.join(modulesPath, file)).isDirectory();
		});

	var tasks = folders.map(function(folder) {
		return gulp.src(['modules/' + folder + '/views/*.jade', 'modules/' + folder + '/views/**/*.jade'])
			.pipe(jade())
			.pipe(rename(function(path){ path.extname = '.html'; }))
			.pipe(gulp.dest(params.dist + '/app/modules/' + folder + '/views'));
   });

   return merge(tasks);
});
// ----------------------------------------------------------------------------
// WATCH
// ----------------------------------------------------------------------------

// Rerun the task when a file changes
gulp.task('watch', function() {
	livereload.listen({port: params.lvr_port});

	gulp.watch(source.scripts.watch,           ['scripts:app']);
	gulp.watch(source.styles.app.watch,        ['styles:app', 'styles:app:rtl']);
	gulp.watch(source.styles.themes.watch,     ['styles:themes']);
	gulp.watch(source.bootstrap.watch,         ['styles:app']); //bootstrap
	gulp.watch(source.templates.pages.watch,   ['templates:pages']);
	gulp.watch(source.templates.views.watch,   ['templates:views']);
	gulp.watch(source.templates.app.watch,     ['templates:app']);
	gulp.watch('modules/**/*.js', ['modules:scripts']);
	gulp.watch('modules/**/*.less', ['modules:styles']);
	gulp.watch('modules/**/*.jade', ['modules:views']);

	gulp.watch([
			params.dist + '/app/**'
	]).on('change', function(event) {

			livereload.changed( event.path );
			connect.reload();

	});

});
// ----------------------------------------------------------------------------
// STATIC FILES
// ----------------------------------------------------------------------------
gulp.task('static', function(){
	gulp.src('../app/**').pipe(gulp.dest(params.dist + '/app'));
}
);





// ----------------------------------------------------------------------------
// DEFAULT TASK
// ----------------------------------------------------------------------------
// build for production (minify)
gulp.task('build', gulpsync.async([
		'static',
		'scripts:vendor',
		'scripts:app',	
		'styles:app',
		'styles:app:rtl',
		'styles:themes',
		'templates:app',
		'templates:pages',
		'templates:views',
		'modules:scripts',
		'modules:styles',
		'modules:views'
	])
);

// ----------------------------------------------------------------------------
// default (no minify)
gulp.task('default', gulpsync.sync([
					'start'
				]), function(){

	gutil.log(gutil.colors.cyan('************'));
	gutil.log(gutil.colors.cyan('* All Done *'), 'You can start editing your code, LiveReload will update your browser after any change..');
	gutil.log(gutil.colors.cyan('************'));

});
// ----------------------------------------------------------------------------
gulp.task('start',[
					'build',
					'connect',
					'watch'
				]);
// ----------------------------------------------------------------------------
gulp.task('done', function(){
	console.log('All Done!! You can start editing your code, LiveReload will update your browser after any change..');
});
// ----------------------------------------------------------------------------

// Error handler
function handleError(err) {
	console.log(err.toString());
	this.emit('end');
}

// Mini gulp plugin to flip css (rtl)
function flipcss(opt) {
	
	if (!opt) opt = {};

	// creating a stream through which each file will pass
	var stream = through.obj(function(file, enc, cb) {
		if(file.isNull()) return cb(null, file);

		if(file.isStream()) {
				console.log("todo: isStream!");
		}

		var flippedCss = flip(String(file.contents), opt);
		file.contents = new Buffer(flippedCss);
		cb(null, file);
	});

	// returning the file stream
	return stream;
}
