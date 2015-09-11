var gulp = require('gulp'),
    connect = require('gulp-connect');

var config = require('../config.json'),
    run = require('../utils/run'),
    helper = require('../utils/helper');

// *** Application Tasks *** //

// Application Views
gulp.task('app:views', function(cb){
    run.jadeAll(config.app.views, cb);
});
gulp.task('watch:app:views', function(){
    var srcs = helper.getSources(config.app.views);
    gulp.watch(srcs, ['app:views']);
});

// Application Scripts
gulp.task('app:scripts', function(cb){
    run.concatAll(config.app.scripts, cb);
});
gulp.task('watch:app:scripts', function(){
    var srcs = helper.getSources(config.app.scripts);
    return gulp.watch(srcs, ['app:scripts']);
});

// Application Styles
gulp.task('app:styles', function(){
    var dest = helper.splitPath(config.app.styles.dest);
    return run.less(config.app.styles.src, dest.dir, config.app.styles.path);
});
gulp.task('watch:app:styles', function(){
    return gulp.watch(config.app.styles.src, ['app:styles']);
});

// Application Images
gulp.task('app:imgs', function(){
    return gulp.src(config.app.imgs.src)
        .pipe(gulp.dest(config.app.imgs.dest))
        .pipe(connect.reload());
});

// All Application Tasks
gulp.task('app', ['app:views', 'app:scripts', 'app:styles', 'app:imgs']);
gulp.task('watch:app', ['watch:app:views', 'watch:app:scripts', 'watch:app:styles']);
