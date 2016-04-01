App.controller('HistogramsController', ['$scope', '$location', 'ngTableParams', 'ngDialog', 'lhcbprResources', function($scope, $location, $tableParams, $dialog, $api) {

	$scope.lineOptions = {
		animation: false,
		barShowStroke : false,
	    barValueSpacing : 0,
	    barDatasetSpacing : 0,
	    tooltipHideZero: true,
	    barShowStroke : false,
	    barStrokeWidth : 0,
	    barValueSpacing : 1,
  		tooltipTemplate: "<%if (label){%><%=label%>: <%}%><%= value %>",
		legendTemplate : '<% for (var i=0; i<datasets.length; i++){%><span class="label label-default" style="background-color:<%=datasets[i].fillColor%>"><%if(datasets[i].label){%><%=datasets[i].label%><%}%></span> <%}%>'
	};

	$scope.appId = undefined;
	$scope.options = undefined;
	$scope.versions = undefined;
	$scope.min = '';
	if($location.search().min)
		$scope.min = parseFloat($location.search().min);
	$scope.max = '';
	if($location.search().max)
		$scope.max = parseFloat($location.search().max);
	$scope.intervals = 40;
	if($location.search().intervals)
		$scope.intervals = parseInt($location.search().intervals);
	$scope.attrFilter = '';
	if($location.search().attr_filter)
		$scope.attrFilter = $location.search().attr_filter;
	$scope.loading = false;
	$scope.noData = true;

	$scope.tableParams = new $tableParams(
		{ page: 1, count: 10 }, 
		{ total: 0, getData: function($defer, params) {
            if($scope.appId && $scope.options && $scope.versions){
            	var requestParams = {
					app: $scope.appId,
					options: $scope.options.join(','),
					versions: $scope.versions.join(','),
					intervals: $scope.intervals,
					page: params.page(),
					page_size: params.count()
				};
				if(! isNaN(parseFloat($scope.min))){
					requestParams.min = parseFloat($scope.min);
				}
				if(! isNaN(parseFloat($scope.max))){
					requestParams.max = parseFloat($scope.max);
				}
				$scope.attrFilter = $scope.attrFilter.trim();
				$location.search('attr_filter', $scope.attrFilter);
				if($scope.attrFilter != ''){
					requestParams.attr_filter = $scope.attrFilter;
				}
				console.log('requestParams: ', requestParams);
				$api.all('histograms').getList(requestParams).then(function(response){
					if(response._resultmeta){
						params.total(response._resultmeta.count);
					}
					$scope.noData = (response.length < 1);
					$defer.resolve(response);
					var paramsAttr = $location.search().attr;
					var paramsAttrVersion = $location.search().attr_version;
					if(paramsAttr != undefined){
						var a = null;
						response.forEach(function(r){
							if(r.id == paramsAttr)
								a = r;
						});
						if(a != null){
							if(paramsAttrVersion) {
								var index = parseInt(paramsAttrVersion);
								if( ! isNaN(index) && index < a.values.length )
									$scope.showChart(a, index);
							} else {
								$scope.showAllCharts(a);
							}
						}
					}
					$scope.loading = false;
				});
            }
        }
	});

	$scope.tableParams.settings().$scope = $scope;

	$scope.requestStatistics = function(params) {
		if(params.apps.length > 0 && params.options.length > 0 ){
			$scope.appId = params.apps[0];
			$scope.options = params.options;
			$scope.versions = params.versions;
			console.log('Histograms versions:', $scope.versions);
			$scope.update();
		}
	};

	$scope.update = function(){
		$scope.loading = true;
		$location.search('min', $scope.min);
		$location.search('max', $scope.max);
		$location.search('intervals', $scope.intervals);
		$scope.tableParams.page(1);
		$scope.tableParams.reload();
	}

	$scope.showAllCharts = function(a){
		console.log('Show chart of ' + a.name);
		var labels = [];
		var datasets = [];
		// Fill labels
		var first, last;
		for(var i = 0, count = a.values[0].jobs.length; i < count; i ++){
			first = parseInt((a.min_value + i * a.interval_width) * 100) / 100.0;
			last = parseInt((a.min_value + (i + 1) * a.interval_width) * 100) / 100.0;
			labels.push('[' + first + ', ' + last + ']');
		}

		// Fill datasets
		var index = -1;
		datasets = a.values.map(function(value){
			index ++;
			return {
				label: value.version,
				fillColor: Colors.get(index),
				strokeColor: Colors.getDark(index),
				highlightFill: Colors.getLight(index),
				highlightStroke: Colors.get(index),
				data: value.jobs
			};
		});

		$scope.lineData = {
			labels: labels,
			datasets: datasets
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

	$scope.showChart = function(a, index){
		console.log('Show chart of ' + a.name + ' for ' + index);
		var labels = [];
		var datasets = [];
		// Fill labels
		var first, last;
		for(var i = 0, count = a.values[index].jobs.length; i < count; i ++){
			first = parseInt((a.min_value + i * a.interval_width) * 100) / 100.0;
			last = parseInt((a.min_value + (i + 1) * a.interval_width) * 100) / 100.0;
			labels.push('[' + first + ', ' + last + ']');
		}

		datasets = [{
			label: a.values[index].version,
			fillColor: Colors.get(index),
			strokeColor: Colors.getDark(index, 0.5),
			highlightFill: Colors.getLight(index, 0.5),
			highlightStroke: Colors.get(index),
			data: a.values[index].jobs
		}];

		$scope.lineData = {
			labels: labels,
			datasets: datasets
		};
		$scope.name = a.name;
		$dialog.open({
			template: 'chartTemplate',
			className: 'chart-dialog',
			scope: $scope,
			preCloseCallback: function() {
				$scope.$apply(function(){
					$location.search('attr', null);
					$location.search('attr_version', null);
				});
			}
		});

		$location.search('attr', a.id);
		$location.search('attr_version', index);
	}

	$scope.chartHeight = function() {
		return $(window).height() - 140;
	};

	$scope.chartWidth = function() {
		return $(window).width() - 80;
	};

}]);
