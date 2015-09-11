var gulp = require('gulp'),
    connect = require('gulp-connect');

var config = require('../config.json'),
    run = require('../utils/run'),
    helper = require('../utils/helper');

// *** Vendors Tasks *** //

// Base vendors
gulp.task('vendors:base', function(cb){
    var size = 3;
    var done = function(){
        size --;
        if(size == 0)
            cb(null);
    };
    // Scripts
    run.concat(config.vendors.base.js.src, config.vendors.base.js.dest)
        .on('end', done);
    // Styles
    run.concat(config.vendors.base.css.src, config.vendors.base.css.dest)
        .on('end', done);
    // Fonts
    gulp.src(config.vendors.base.fonts.src)
        .pipe(gulp.dest(config.vendors.base.fonts.dest))
        .on('end', done);
});

// Lazy loading vendors
gulp.task('vendors:lazy', function(cb){
    var size = config.vendors.lazy.modules.length;
    var done = function(){
        size --;
        if(size == 0)
            cb(null);
    }

    config.vendors.lazy.modules.forEach(function(m){
        gulp.src(m.src, { base: config.vendors.lazy.base })
            .pipe(gulp.dest(config.vendors.lazy.dest))
            .on('end', done);
    });
});

// All Tasks
gulp.task('vendors', ['vendors:base', 'vendors:lazy']);
