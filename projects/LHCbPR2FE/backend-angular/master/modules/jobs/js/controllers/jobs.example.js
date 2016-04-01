App.controller('JobsExampleController', 
     ["$scope",function ($scope) {
  

	$scope.onJobsFound = function(jobs) {
		$scope.jobs = jobs;	
	};

	//createTable();
}]);
