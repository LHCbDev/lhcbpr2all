App.controller('Geanttestem3Controller', function($scope, $log, lhcbprResourcesHelper, BUILD_PARAMS) {
	var plots = ['CSampling', '1_2','2_2'];
	$scope.url = BUILD_PARAMS.url_root;


	$scope.analyze = function(ids) {
    lhcbprResourcesHelper.search({ids: ids}).then(showJobs);
  };

  function showJobs(jobs){
  	var items = [];
  	plots.forEach(function(plot){
  		jobs.forEach(function(job){
  		   var file = {};
  		   file[job.id + '/Save.root'] = job.job_description.application_version.version + ' ' + job.platform.content;
  		   var item = {
  		   		'files_and_titles': file,
  		   		'items': [plot]
  		   };
  		   items.push(item);
  		});
  	});
  	if (items){
  	   $scope.items = items;
    }
  		
  }
});
