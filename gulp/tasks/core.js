var gulp = require('gulp'),
    connect = require('gulp-connect');

var config = require('../config.json'),
    run = require('../utils/run'),
    helper = require('../utils/helper');
 
// *** Framework Core Tasks *** //

// Core Scripts
gulp.task('core:scripts', function(cb){
    run.concatAll(config.core.scripts, cb);
});

gulp.task('watch:core:scripts', function(){
    var srcs = helper.getSources(config.core.scripts);
    return gulp.watch(srcs, ['core:scripts']);
});

// All Core Tasks
gulp.task('core', ['core:scripts']);
gulp.task('watch:core', ['watch:core:scripts']);
