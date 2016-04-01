# LHCbPR Modules Development Guide

## Contents

1. [Introduction](#introduction)

2. [The Web Application Structure](#the-web-application-structure)

3. [Getting Started](#getting-started)

4. [Using Directives](#using-directives)

5. [Using LHCbPR API](#using-lhcbpr-api)

6. [Advanced Module Example](#advanced-module-example)

## Introduction

The LHCbPR web application was designed to be scalable and allow adding/removing modules easily. This document presents how to create new module and add it to the application.

### Development Tools

The following tools are used in the development workflow of the application and modules:

- [npm](https://www.npmjs.com/): The package manager for [NodeJS](https://nodejs.org/) modules. It is used to install some NodeJS modules needed for the application development process; particularly the Gulp build system.

- [Gulp](http://gulpjs.com/): A build system based on NodeJS. It is used to automatically run tasks like compiling sources files or minifying them for production.

- [Bower](http://bower.io/): A package manager for the web. Used to install Angular, jQuery, Bootstrap and all other libraries and plugins.

## The Web Application Structure

### Files Structure

The LHCbPR web application has the following files structure:

```
app/               # the build folder
master/            # the sources folder
	|-- bower_components/   # bower installed packages
	|-- jade/        		# the core application views
	|-- js/          		# the core application js files
	|-- less/        		# the core application styles
	|-- modules/     		# modules folder
	|-- node_modules/     	# NodeJs installed modules
	|-- bower.json 			# bower manifest file
	|-- gulpfile.js  		# Gulp tasks definition
	|-- package.json 		# npm manifest file
	|-- vendor.base.json
	|-- vendor.json
vendor/            # the libraries folder
index.html
```

All the application source code is inside the `master` directory. Under this directory we find:

- `bower_components/`: When we install a package using Bower, it is stored into this directory. Then when Gulp is run, it takes all needed Javascript and CSS files from this directory, minify them and store them into the `vendor` directory. Gulp knows the needed files from the `vendor.base.json` and `vendor.json`. `vendor.base.json` tells the list of packages to be loaded with the core application (like Angular and jQuery). `vendor.json` tells what are the other needed packages which will be loaded specifically depending on the visited module.

- `jade/`: The core view files are stored into this directory. Views are written using the [Jade language](http://jade-lang.com/) and compiled into HTML files by Gulp. The compiled HTML files are stored into the `app/views` directory.

- `js/`: This directory contains all the core javascript files of the application. Since AngularJS is used to build this application; we find `controllers`, `directives` and `services` directories inside the `js` one following the Angular conventions. Additional javascript classes are stored inside the `js/classes` folder. One of this classes is the `Module` class which will be used to create modules for the application.

- `less/`: This directory holds all application style definitions. They are written using a CSS pre-processor called [Less](http://lesscss.org/). Gulp will compile all this files into CSS files and store them in `app/css` directory.

- `modules/`: This directory contains source code of modules. the module structure is detailed below.

- `node_modules/`: NodeJs modules installed using `npm install` will be stored into this directory.

- `gulpfile.js`: This file contains the Gulp tasks definitions.

### Module Files Structure

All modules are stored under the `master/modules` directory. Each module have the following files structure:

```		
module_name/
	|-- js/               # the javascript files
	|   |-- controllers/  # controllers
	|   |-- directives/   # custom directives
	|   |-- filters/      # custom filters
	|   |-- services/     # custom services
	|   |-- init.js       # initialization file
	|-- less/
	|     |-- style.less  # custom styles
	|-- views/            # views
```

## Getting Started

### Setting Up The Web Application Locally

In order to be able to clone and run the web application locally, you will need to install the following tools first:

- [Git:](https://git-scm.com/) If you don't already have it, You can install Git using your package manager such as `yum` or `apt-get`.

- [Nodejs and npm:](https://nodejs.org/) To install Nodejs and npm follow instructions on their website [https://nodejs.org/](https://nodejs.org/)

- [Bower:](http://bower.io/) Plase run this command to install bower

	npm install -g bower

- [LiveReload:](http://livereload.com/) You can optionaly install LiveReload for you browser to enable automatic page reload when you change source files. Please visit this website for further instructions: [http://livereload.com/](http://livereload.com/)
Now you can clone the web application and run it locally using the following commands:

```bash	
#  clone the github repository
git clone ssh://git@gitlab.cern.ch:7999/lhcb-core/LHCbPR2FE.git
#  go inside the master folder
cd LHCbPR2FE/backend-angular/master
#  install gulp and npm dependencies.
[sudo] npm install
#  install vendor dependencies
bower install
#  compile and run the application
gulp
```

If everything goes fine, you should see the messages in the terminal telling you that most the task are done successfully. Going to [http://localhost:9000/](http://localhost:9000/) should show you the local website. As you can see, the page can be divided on three parts: the header, the sidebar, and the content.

- The header : contains the logo.

- The sidebar : shows the list of modules. When a module is clicked; the list of its links is shown. Clicking a one of these links will show the corresponding view in the content part.

- The content : shows the active view of the active module.

### Elements Of A Module

A module is a group of states of the application. A `state` is defined by an `URL`, a `view` and a `controller`. When the URL of a state is opened; the corresponding view and controller are loaded. The view consists on the HTML elements that are shown on the content area of the page. The controller is a javascript function handling these elements. To make a module accessible, we add URLs to its states on the sidebar.

Here is an example of a module having two states:

```
master
	|-- modules
		|-- module-name/
			|-- js/
			|   |-- controllers/     
			|   	 |-- controllerA.js     
			|   	 |-- controllerB.js     
			|   |-- init.js     
			|-- less/
			|     |-- style.less
			|-- views/
				|-- viewA.jade
				|-- viewB.jade
```

- `js/init.js`: contains the definition of the module. Here we describe what are the state of module and what are links to add on the sidebar.

- `js/controllers/`: This directory contains the two controllers of the states; each controller is written on it's own javascript file.

- `views/`: This directory contains the two views of the states; each view is defined by a .jade file.

### Hello World Module

Let's create a new module called `Test` containing only one state. We start by creating a new directory under `master/modules` following the minimal module structure (we create only required files for the module to work; we can add more files later when needed):

```
master
	|-- modules
		|-- test/
			|-- js/
			|   |-- init.js     
			|-- less/
			|     |-- style.less
			|-- views/
```

Now we should write the initialization of our module on the file `test/js/init.js`. We will use the class `Module` for this.
		
#### The Module Class

This is a helper class simplifying the creation of modules. It offers easy methods and call the corresponding AngularJS methods behind the scene.

`Module.create(name, title, position, settings)`

- **name:** The name of the module, it should be unique for each module.

- **title:** The title of the module menu in the sidebar.

- **position:** The position of the module menu in the sidebar. If two modules have the same position, there are shown one under the other.

- **settings:** An optional plain object specifying the folder name of the module.

```javascript
Module.create('name', 'Title', 1, { 
	folder: 'my_folder_name' 
});
```

If no settings is provided; the folder name is assumed to be the same as the module name.

This method returns an instance of the `Module` class, providing the following methods:

`addMenuItems(items)`

- **items:** Menu object or array of menu objects. A menu object has the following format:

```javascript
{
	text: "Title", // Text to show on the sidebar
	sref: "app.state.name", // Target state name 
	// prefixed by 'app.'
	icon: "icon-grid", // Icon of the menu item
	alert: "new" // Added a budge to the menu item
}
```

This method returns the same calling `Module` instance so that we can chain calls to other methods.

`addStates(states)`

A state can be considered as a view or page of the module. One module can have multiple states and not all of them should have direct links on the sidebar.

- **states:** State object or array of state objects. A state object has the following format:

```javascript
{
	name: 'test.state_one', // Required
	url: '/my-url', // If not provided,it will be defined
	// based on the name ('/state-one' for this example)
	title: 'Title', // If not provided,it will be defined
	// based on the name ('State One' for this example)
	templateUrl: 'view.html', // name of the view file 
	// with html extension instead of jade. If not provided 
	// the view name will be 'state-one.html' in this case.
	controller: 'MyController', // name of the controller 
	// handeling the state. If not provided, it will be 
	// 'TestStateOneController' for this case.
	resolve: ['test', 'chartjs'] // names of dependencies
	// on which this state depends. The name of its own
	// module should be part of the dependencies.
}
```

This method returns the same calling `Module` instance so that we can chain calls to other methods.

`start()`

This method should be called once all the desired menu items and states were added to the module. It executes the corresponding code on the AngularJS instance and integrate the module with the rest of the web application.

Now let's use this class to initialize our module. We will write the following code in the file `test/js/init.js`:

```javascript
Module.create('test', 'Test Title', 1)
	.addMenuItems({
		text: "Test Module",
		sref: "app.test",
		icon: "icon-grid"
	})
	.addStates({
		name: 'test',
		resolve: ['test']
		// This will assume that:
		// title is 'Test'
		// templateUrl is 'test.html'
		// controller is 'TestController'
	})
	.start();
```

The code above assume that we have a view and a controller. So we have to create them so that our module works properly.

#### Adding a controller

In Angular, a controller is a javascript function that handles a view or a part of the page. Take a look at the official documentation [https://docs.angularjs.org/guide/controller](https://docs.angularjs.org/guid/controller"). The controller javascript file can be stored anywhere inside the `test/js` directory. Let's store it inside a controllers directory like this `test/js/controllers/test.js` and write the following code:

```javascript
/**
* TestController
*/
App.controller('TestController', ['$scope', function($scope){
	// the $scope variable holds variables and methods 
	// which can be used directly from the view
	// we define a variable message 
	// with the value "Hello World !" for example:
	$scope.message = 'Hello World !';
	
	// and a function to show and alert
	$scope.showAlert = function(){
			alert('Here is the alert !');
	};
}]);
```

Please note that we have given the name "TestController" to our controller as assumed by the module declaration. The next step is to create a view and use the variable `message` and the function `showAlert()`.

#### Adding a View

A view is an HTML file to be rendered as part of the web page. But instead of writing views in basic HTML language which is very verbose. We are using the `Jade` template engine that makes writing HTML files more easier. Check the Jade official website for more details: [http://jade-lang.com](http://jade-lang.com/). One of the Gulp tasks is to compile every jade file and produce the corresponding HTML file. So you will not need to run Jade from the command-line manually.
Now Let's create our test view. its name should be `test.jade` because the templateUrl we are assuming in the module declaration is `test.html`. It should be stored inside the `test/views` directory.

```jade
h2 Just for test
	div.alert.alert-info.
		the message is : {{message}}
	button.btn.btn-primary(ng-click="showAlert()")
		| Click to show the alert
```

Now after re-running the command `gulp` from the terminal. You should see the new test module added to the sidebar and once clicked it shows the view.



## Using Directives

The LHCbPR web application contains many predefined directives that you can use in your modules. Check this link to know more about directives: [docs.angularjs.org/guide/directive](https://docs.angularjs.org/guide/directive). The most used directives are explained below.

### Search Jobs

This is the most used directive in analysis modules. It shows a form in which the user can filter jobs by application, options and versions. And notifies the controller each time the selection changes.

#### Usage Example

Code to add on the view:

```jade
search-jobs(on-found="updateJobs(searchParams)")
```

Code to add on the controller:

```javascript
$scope.updateJobs = function(params){
	// You can use the selected parameters:
	// params.apps[0]: the selected application id
	// params.options: array of selected options ids
	// params.versions: array of selected versions ids
};
```

#### Syntax

```jade
search-jobs(
	on-found="updateJobs(searchParams)"
		//- Required: the function to call with selected params
	filter-options="true"
		//- show options filtering? default is "true"
	filter-versions="false" 
		//- show versions filtering? default is "true"
)
```
### ngTable

This directive can be used to add table with sorting, filtering and pagination features.

#### Usage Example

Code to add on the view:

```jade
table.table.table-striped.table-bordered.table-hover(
ng-table="tableParams")
thead
	th ID
	th Name
tbody
	tr(ng-repeat="attr in $data")
		td {{attr.id}}
		td {{attr.name}}
```

Code to add on the controller:

```javascript
App.controller('TestController', [
	'$scope', 'ngTableParams', function($scope, ngTableParams) 
{
	// We define some hard coded data
	$scope.attrs = [
		{ id: 56, name: "EVENT_LOOP" },	
		{ id: 57, name: "EVENT_LOOP_count" },	
		{ id: 58, name: "EVENT_LOOP_rank" },	
		{ id: 60, name: "EVENT_LOOP_id" },	
		{ id: 81, name: "BrunelInit" },	
		{ id: 82, name: "BrunelInit_count" },	
		{ id: 83, name: "BrunelInit_rank" },	
		{ id: 85, name: "BrunelInit_id" },	
		{ id: 91, name: "L0DUFromRaw" },	
		{ id: 92, name: "L0DUFromRaw_count" }
	];

	// Table parameters
	$scope.tableParams = new ngTableParams(
		{ page: 1, count: 10 }, 
		{ total: 0, getData: function($defer, params) {
			// We just show the hard coded values
			$defer.resolve($scope.attrs);
		}});

	// Add this line to fix a bug in the ng-table directive				
	$scope.tableParams.settings().$scope = $scope;

}]);
```

For full ngTable documentation, please visit the official site: [ng-table.com](http://ng-table.com)

## Using LHCbPR API

The `lhcbprResources` service is based on `Restangular` and can be used to interact with the API.

### Usage Example

here is an example retreiving the list of active applications

```javascript
App.controller('TestController', [
'$scope','lhcbprResources',function($scope,lhcbprResources) 
{
	// Get the list of active applications for example
	lhcbprResources.all('active/applications')
		.getList()
		.then(function(response){
			// Do what ever you want with the response
			// This will show it on the console
			console.log(response);
		});

		// Some other code here
		// Please note that the AJAX calls are asynchronious 
		// which means that the code here maybe executed while 
		// waiting for the response

}]);
```

For full Restangular documentation please visit [https://github.com/mgonto/restangular](https://github.com/mgonto/restangular)

## Advanced Module Example

Now let's make a module and use the API and some directives on it. For this example we will create the trends analysis module.

### Use Case

The first step is to define the features or use cases of our module. The use case is the following:

- User should select an application and possibly multiple options and versions.

- On every change of the selection; We have to retrieve all the job results of jobs from the selected application, options and version. Then a table should show the list of attributes found on these results.

- User should be able to filter attributes by name.

- User should be able to show the Trends plot (showing the mean and deviation by version) of any attribute by clicking on the corresponding button.

- If a plot is shown and the user copied the link. Visiting that link again should re-produce the plot with the same selected application, options and version for the same attribute.

### Files structure

This module will have only one state, so one view and one controller; the files structure can be like this:

```
master
	|-- modules
		|-- demo/
			|-- js/
			|   |-- controllers/
			|   	  |-- demo.js
			|   |-- init.js
			|-- less/
			|     |-- style.less
			|-- views/
				  |-- demo.jade
```

### Module declaration

The module declaration is written on the file `js/init.js`:

```javascript
Module.create('demo', 'Demo', 2)
	.addMenuItems({
		text: "Demo",
		sref: "app.demo",
		icon: "icon-grid"
	})
	.addState({
		name: 'demo',
		resolve: ['demo', 'chartjs', 'ngTable', 'ngDialog']
	})
	.start();
```

According to the code above, we are creating a module named `demo` having one menu item pointing to the `app.demo` state. The only state of the module is named `demo`. Note that the menu item is pointing to `app.demo` while the state's name is just `demo`. That's fine because the `Module` class prefixes all state names with `app.`. This module depends on 

- `chartjs`: used to draw plots

- `ngTable`: used to show the attributes table

- `ngDialog`: used to create the popup showing the plot. 

### Adding Search Form

Now let's write this code on the view to show the search form:

```jade
h3 Trends
  small.text-muted Attributes values by version
.row.traditional(ng-class="csspinner")
  .col-lg-4
    search-jobs(on-found="requestStatistics(searchParams)")
  .col-lg-8
  	p The attributes table will be added here !
```

As you see, we have told the `search-jobs` directive to call the function `requestStatistics` on every change; So we have to define this function in the controller. So for the moment the controller's code will be like this:

```javascript
App.controller('DemoController', ['$scope', function($scope) {

	$scope.appId = undefined;
	$scope.options = undefined;
	$scope.versions = undefined;
	
	$scope.requestStatistics = function(params) {
		$scope.appId = params.apps[0];
		$scope.options = params.options;
		$scope.versions = params.versions;
	};

}]);
```

On every change, we are saving the selected parameters in the variables `$scope.appId`, `$scope.options` and `$scope.versions`. 

### Showing Attributes on a table

Let's add the attributes table to our view; the code will become like this:

```jade
h3 Trends
  small.text-muted Attributes values by version
.row.traditional(ng-class="csspinner")
  .col-lg-4
    search-jobs(on-found="requestStatistics(searchParams)")
  .col-lg-8
    table.table.table-striped.table-bordered.table-hover.be-responsive(ng-table="attrsTtableParams")
      thead
        th ID
        th Name
        th 
      tbody
        tr(ng-repeat="a in $data")
          td {{a.id}}
          td {{a.name}}
          td
            button.btn.btn-primary(ng-click="showChart(a)") Show
```

We have defined a table and applied some CSS classes to it. The notation:

`table.table.table-striped.table-bordered.table-hover.be-responsive`

is equivalent to this:

`table(class="table table-striped table-bordered table-hover be-responsive")`

These css classes are already defined by Bootstrap. The last class `be-responsive` is to make the table responsive so that it shows properly in tablet and phone screens.

We applied the `ng-table` directive to our table using `attrsTtableParams` variable which will be defined in the controller. Each row of the table shows the id of the attribute, its name and a button to show its corresponding plot. Note that we pass the attribute to the function `showChart(a)` when the button is clicked using the `ng-click` directive.

Now let's add the variable `attrsTableParams` and the function `showChart` to the controller. First of all, we need to inject the `ngTableParams` and `lhcbprResources` services into our controller to be able to use them; we do this by Adding them to controller parameters like this:

```javascript
App.controller('DemoController', ['$scope', 'ngTableParams', 'lhcbprResources', function($scope, $tableParams, $api) {
```

Note that we add the `ngTableParams` and `lhcbprResources` to the array and to the function arguments. The order of arguments should be the same as in the array. So here the argument `$scope` is referencing the `$scope` service, `$tableParams` is referencing the `ngTableParams` and `$api` is referencing `lhcbprResources`.

Now we can use `$tableParams` to define `attrsTableParams` like this:

```javascript
$scope.attrsTableParams = new $tableParams(
	{
		page: 1, // the page to show initialy
		count: 10 // number of rows on each page
	}, 
	{ 
		total: 0, // total number of rows initialy
		// function that fetchs data to fill the table
		getData: function($defer, params) {
			// We check if an application and options were selected
            if($scope.appId && $scope.options){
            	// We construct the data to send with the request to the API
            	var requestParams = {
					app: $scope.appId,
					options: $scope.options,
					versions: $scope.versions,
					page: params.page(),
					page_size: params.count()
            	};
            	// TODO: The filter code will be added here
            	// We send the request to the '/trends' url of the API
				$api.all('trends')
					.getList(requestParams)
					.then(function(trends){ // When we receive the response
					// We set the total number of rows
					if(trends._resultmeta){
						params.total(trends._resultmeta.count);
					}
					// We fill the table with the response
					$defer.resolve(trends);
					// TODO: the code to show the plot based on the URL will be added here
				});

            }
        }
    }
);
// We add this line of code to fix a bug in the ngTable service
$scope.attrsTableParams.settings().$scope = $scope;
```

After this, we need a function which updates the table's content after every change of the selected application, options or versions.

```javascript
$scope.update = function(){
	// Set the current page of the table to the first page
	$scope.attrsTableParams.page(1);
	// reloading data
	$scope.attrsTableParams.reload();
}
```

Now we go back to the function `requestStatistics` and call the function `update` after every change:

```javascript
$scope.requestStatistics = function(params) {
	$scope.appId = params.apps[0];
	$scope.options = params.options;
	$scope.versions = params.versions;
	$scope.update();
};
```

Finally let's add the `showChart` function

```javascript
$scope.showChart = function(a){
	console.log('Showing chart of ' + a.name);
};
```

This function just prints the message "Showing chart of [attribute name]" on the console for the moment.

Now if you re-run the gulp command and visit the website. You should see your module added to the sidebar. Visiting it should show the search form and once you select an application and same options; The table should be filled with attributes.

### Filtering attributes by name

Now let's add a text input to filter attributes by name. We start by adding a form containing one input before the table on the view; the code of the view becomes like this:

```jade
h3 Trends
  small.text-muted Attributes values by version
.row.traditional(ng-class="csspinner")
  .col-lg-4
    search-jobs(on-found="requestStatistics(searchParams)")
  .col-lg-8
  	form
  	  .form-group
  	    label Filter Attributes
  	    input.form-control(ng-model='attrFilter', ng-change='update()', type='text')
    table.table.table-striped.table-bordered.table-hover.be-responsive(ng-table="attrsTtableParams")
      thead
        th ID
        th Name
        th 
      tbody
        tr(ng-repeat="a in $data")
          td {{a.id}}
          td {{a.name}}
          td
            button.btn.btn-primary(ng-click="showChart(a)") Show
```

Please note that in this line:

```jade
input.form-control(ng-model='attrFilter', ng-change='update()', type='text')
```

We bind the value of the input to the scope variable named `attrFilter` and we call `update()` on every change.

Let's go to the controller and replace this comment on the getData function:

```javascript
// TODO: The filter code will be added here
```

By this piece of code:

```javascript
// remove additional spaces from the input value
$scope.attrFilter = $scope.attrFilter.trim();
// if the value is not empty; we add it to the request parameters
if($scope.attrFilter && $scope.attrFilter != '')
	requestParams.attr_filter = $scope.attrFilter;
```

Now the attributes filtering by name should work properly.

### Showing the Plot

Till now, when we click the "Show" button to show the chart; nothing happens. Let's fix this.

The plot will be shown into a ngDialog (which is a popup). So we have to define the content of this popup. One of the simple way to do it is to include it in the view as an inline template by adding this code at the end of the view code:

```jade
script(type="text/ng-template", id="chartTemplate")
  .row
    .col-lg-10.col-lg-offset-1.col-md-10.col-md-offset-1.col-sx-10.col-sx-offset-1
      h2 {{name}}
      .chart
        canvas(linechart='', options='lineOptions', data='lineData', height='chartHeight()', width='chartWidth()')
```

In this code, we defined an inline template with the name "chartTemplate". The plot will be shown into the canvas element because we applied the directive `linechart` to it. This directive needs two properties `options` and `data` which we filled with the scope variables `lineOptions` and `lineData`; We will define these variables in the controller. We have also specified the width and height of the chart using the scope functions `chartWidth` and `chartHeight` that will be defined on the controller too.

Now we move to the controller and add the following code:

```javascript
$scope.lineOptions = {
	animation: false,
	errorDir : "both",
	errorStrokeWidth : 3,
	datasetFill : false,
	scaleOverride : true,
    scaleSteps : 10,
    scaleStepWidth : 1,
    scaleStartValue : 0,
		tooltipTemplate: "<%if (label){%><%=label%>: <%}%><%= value %><%if (errorBar){%> ± <%=errorBar.errorVal%><%}%>",
	legendTemplate : '<% for (var i=0; i<datasets.length; i++){%><span class="label label-default" style="background-color:<%=datasets[i].fillColor%>"><%if(datasets[i].label){%><%=datasets[i].label%><%}%></span> <%}%>'
};

$scope.chartHeight = function() {
	return $(window).height() - 140;
};

$scope.chartWidth = function() {
	return $(window).width() - 60;
};
```

Then we write the code of the `showChart` function:

```javascript
$scope.showChart = function(a){
	console.log('Show chart of ' + a.name);
	// We store versions, averages and deviations in separated tables
	// with the same order and we compute the min and max values
	var minValue = a.values[0].average - a.values[0].deviation, 
		maxValue = a.values[0].average + a.values[0].deviation,
		value = 0,
		versions = [],
		averages = [],
		deviations = [];
	a.values.forEach(function(v){
		v.average = parseInt(100 * v.average) / 100.0;
		v.deviation = parseInt(100 * v.deviation) / 100.0;
		averages.push(v.average);
		versions.push(v.version);
		deviations.push(v.deviation);
		value = v.average - v.deviation;
		if(value < minValue)
			minValue = value;
		value = v.average + v.deviation;
		if(value > maxValue)
			maxValue = value;
	});
	minValue = Math.floor(minValue);
	maxValue = Math.floor(maxValue) + 1;
	// We configure the chart to show only values between minValue and maxValue
	$scope.lineOptions.scaleStartValue = minValue;
	$scope.lineOptions.scaleSteps = maxValue - minValue;
	$scope.lineOptions.scaleStepWidth = 1;
	while ( $scope.lineOptions.scaleSteps > 25 ){
		$scope.lineOptions.scaleSteps /= 2;
		$scope.lineOptions.scaleStepWidth *= 2;
	}

	// We set the data to show on the chart
	$scope.lineData = {
		labels: versions,
		datasets: [{
			label: a.name,
			fillColor : "rgba(220,220,220,0.2)",
			strokeColor : "#2F49B1",
			pointColor : "#5E87D6",
			pointStrokeColor : "#fff",
			pointHighlightFill : "#fff",
			pointHighlightStroke : "#5E87D6",
			data: averages,
			error: deviations
		}]
	};
	// We set the name of the attribute
	$scope.name = a.name;
	// We show the popup
	$dialog.open({
		template: 'chartTemplate',
		className: 'chart-dialog',
		scope: $scope
	});
}
```

### Binding selected values to the URL

When we show the chart, we need to add the id of the shown attribute to the URL, and when the popup is closed we just remove this information from the URL. To do this, we need the `$location` service that we will inject into our controller:

```javascript
App.controller('DemoController', ['$scope', 'ngTableParams', 'lhcbprResources', '$location', function($scope, $tableParams, $api, $location) {
```

Then we change the last part of `showChart` function:

```javascript
$scope.showChart = function(a){
	// ... code here remains the same
	// We show the popup
	$dialog.open({
		template: 'chartTemplate',
		className: 'chart-dialog',
		scope: $scope,
		preCloseCallback: function() { // When the popup is closed
			$scope.$apply(function(){
				// We remove the attr from the URL
				$location.search('attr', null);
			});
		}
	});
	// After showing the popup we set the attr on the URL
	$location.search('attr', a.id);
}
```

The last step is to check if the attr is set on the URL when the user first visits the page and if set show the chart directly. We will have to do this check after loading the data from the API. So we go back to the `getData` function of the `$scope.attrsTableParams` and we replace the comment:

```javascript
// TODO: the code to show the plot based on the URL will be added here
```

With the following code:

```javascript
// Read the attribute id from the URL
var paramsAttr = $location.search().attr;
// if found
if(paramsAttr !== undefined){
	// Search the corresponding attribute on the response
	var a = undefined;
	trends.forEach(function(t){
		if(t.id == paramsAttr)
			a = t;
	});
	// If the corresponding attribute found
	if(a !== undefined){
		// Show the chart
		$scope.showChart(a);
	}
}
```
