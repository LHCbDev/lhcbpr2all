App.controller('TrendsChartController',
	["$scope", "$filter", "$stateParams", "$q", "lhcbprResources", 
	function($scope,  $filter, $stateParams, $q, lhcbprResources) {
		var option = $stateParams.option;
		var attr = $stateParams.attribute;
		var option1 = lhcbprResources.one('options',$stateParams.option).get();
		var attr1 = lhcbprResources.one('attributes',$stateParams.attribute).get();

		$q.all([option1, attr1]).then(function(result) {
			$scope.option = result[0].valueOf();
			$scope.attr = result[1].valueOf();
			
			lhcbprResources.all(
			"result_by_opt_and_attr/" + option + '_' + attr + '/').getList().then(
				function(results) {
					var labels = results.map(function(result){
						var version = result.job.job_description.application_version;
						return version.application.name + " " + version.version;
					});
					var data = results.map(function(result){
						return result.val_float;
					});
					var upper = [];
					var down = [];
					var threshold = $filter("filter")($scope.option.thresholds, {"attribute": {"id": $scope.attr.id}});
					if (threshold.length) {
						for(var i=0; i < labels.length; ++i) {
							upper.push(threshold[0].up_value);
							down.push(threshold[0].down_value);
						}
					}
					chart(data, labels, upper, down);
				}
			);  
		});
		var chart = function(data, labels, upper, down) {
			var datasets =  [
			        {
			          label: $scope.attr.name,
			          fillColor : 'rgba(0,255,0,0)',
			          strokeColor : 'green',
			          pointColor : 'green',
			          pointStrokeColor : '#fff',
			          pointHighlightFill : '#fff',
			          pointHighlightStroke : 'green',
			          data : data
			        },
			        {
			          label: 'Upper threshold',
			          fillColor : 'rgba(35,183,229,0)',
			          strokeColor : 'red',
			          pointColor : 'red',
			          pointStrokeColor : '#fff',
			          pointHighlightFill : '#fff',
			          pointHighlightStroke : 'red',
			          data : upper
        			},
        			{
			          label: 'Down threshold',
			          fillColor : 'rgba(35,183,229,0)',
			          strokeColor : 'blue',
			          pointColor : 'blue',
			          pointStrokeColor : '#fff',
			          pointHighlightFill : '#fff',
			          pointHighlightStroke : 'blue',
			          data : down
        			}
			];

			if (!upper.length) {
				delete datasets[2];
				delete datasets[3];
			}
			$scope.lineData = {
			      labels : labels,
			      datasets: datasets
	    	};
	    	console.log($scope.lineData);
		};
		
		  
}]);
