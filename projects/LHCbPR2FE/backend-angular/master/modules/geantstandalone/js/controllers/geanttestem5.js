App.controller('Geanttestem5Controller', function($scope, $log, lhcbprResourcesHelper, BUILD_PARAMS) {
	var plots = ['Graph;2'];
	$scope.url = BUILD_PARAMS.url_root;


	$scope.analyze = function(ids) {
		lhcbprResourcesHelper.search({ids: ids}).then(showJobs);
	};

	function showJobs(jobs){
		var files = {};

		jobs.forEach(function(job){
			 files[job.id + '/RMSResults.root'] = job.job_description.application_version.version + ' ' + job.platform.content;
		});

		if (files){
			console.log("SASHA10", files);
			$scope.plots = plots;
  	  $scope.items = files;
    }
			
	}
});
