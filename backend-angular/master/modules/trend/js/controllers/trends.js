App.controller('TrendController', ['$scope', '$location', 'ngTableParams', 'ngDialog', 'lhcbprResources', function($scope, $location, $tableParams, $dialog, $api) {
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

	$scope.appId = undefined;
	$scope.options = undefined;
	$scope.versions = undefined;
	$scope.attrFilter = '';
	$scope.loading = false;
	$scope.noData = true;

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
	            if($scope.appId && $scope.options.length > 0){
	            	$scope.loading = true;
	            	console.log('Sending Trends request !');
	            	// We construct the data to send with the request to the API
	            	var requestParams = {
						app: $scope.appId,
						options: $scope.options.join(','),
						versions: $scope.versions.join(','),
						page: params.page(),
						page_size: params.count()
	            	};
	            	$scope.attrFilter = $scope.attrFilter.trim();
	            	if($scope.attrFilter != '')
	            		requestParams.attr_filter = $scope.attrFilter;
					$api.all('trends').getList(requestParams).then(function(trends){
						console.log('Trends Reponse received');
						if(trends._resultmeta){
							params.total(trends._resultmeta.count);
						}
						console.log(trends);
						$scope.noData = (trends.length < 1);
						$defer.resolve(trends);
						$scope.loading = false;
						var paramsAttr = $location.search().attr;
						if(paramsAttr !== undefined){
							var a = undefined;
							trends.forEach(function(t){
								if(t.id == paramsAttr)
									a = t;
							});
							if(a !== undefined)
								$scope.showChart(a);
						}
					});
	            }
	        }
	    }
    );

	$scope.attrsTableParams.settings().$scope = $scope;

	$scope.requestStatistics = function(params) {
		$scope.appId = params.apps[0];
		$scope.options = params.options;
		$scope.versions = params.versions;
		$scope.update();
	};

	$scope.update = function(){
		console.log('Updating !!');
		// Set the current page of the table to the first page
		$scope.attrsTableParams.page(1);
		// reloading data
		$scope.attrsTableParams.reload();
	}

	$scope.showChart = function(a){
		console.log('Show chart of ' + a.name);
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
		$scope.lineOptions.scaleStartValue = minValue;
		$scope.lineOptions.scaleSteps = maxValue - minValue;
		$scope.lineOptions.scaleStepWidth = 1;
		while ( $scope.lineOptions.scaleSteps > 25 ){
			$scope.lineOptions.scaleSteps /= 2;
			$scope.lineOptions.scaleStepWidth *= 2;
		}

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
		$scope.name = a.name;
		$dialog.open({
			template: 'chartTemplate',
			className: 'chart-dialog',
			scope: $scope,
			preCloseCallback: function() {
				$scope.$apply(function(){
					$location.search('attr', null);
				});
			}
		});

		$location.search('attr', a.id);
	}

	$scope.chartHeight = function() {
		return $(window).height() - 140;
	};

	$scope.chartWidth = function() {
		return $(window).width() - 60;
	};

}]);
