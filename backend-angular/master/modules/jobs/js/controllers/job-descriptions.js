/**=========================================================
 * Module:lhcbpr-job-descriptions.js
 * Provides a simple demo for typeahead
 =========================================================*/

App.controller('JobDescriptionsController', 
     ["$scope", function ($scope) {
 
 }]);


App.controller('JobDescriptionsListController', 
     ["$scope", "lhcbprResources", function ($scope, lhcbprResources) {
	lhcbprResources.all('applications').getList()  // GET: /users
	.then(function(apps) {
  		$scope.apps = apps;
	})
}]);

App.controller('JobDescriptionsAddController', 
     ["$scope", "$q", "lhcbprResources", function ($scope, $q, lhcbprResources) {
    
}]);