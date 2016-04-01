/**=========================================================
 * Directive: Select jobs
 =========================================================*/

App.directive('selectJobs', ["ngTableParams", "ngDialog", "lhcbprResources", '$location',
	function(ngTableParams, ngDialog, lhcbprResources, $location) {
		return {
			templateUrl: 'app/views/directives/select-jobs.html',
			restrict: 'ECA',
			scope: {
				selectedApp: '@',
				selectedOptions: '@',
				onJobsSelected: '&'
			},
			link: function(scope, element, attrs) {

				scope.jobsIds = [];
				scope.searchParams = undefined;
				scope.noData = true;
				scope.jobsTableParams = new ngTableParams({
					page: 1, // show first page
					count: 10 // count per page
				}, {
					total: 0, // length of data
					getData: function($defer, params) {
						// use build-in angular filter
						if (!scope.searchParams) {
							return;
						}
						lhcbprResources.all("search-jobs").getList({
							application: scope.searchParams.apps.join(','),
							versions: scope.searchParams.versions.join(','),
							options: scope.searchParams.options.join(','),
							platforms: scope.searchParams.platforms.join(','),
							page: params.page(),
							page_size: params.count()
						}).then(function(jobs) {
							scope.noData = (jobs.length < 1);
							if (jobs._resultmeta) {
								params.total(jobs._resultmeta.count);
							}
							$defer.resolve(jobs);
							var allJobIds = jobs.map(function(job) {
								return job.id;
							});
							scope.jobsIds = scope.jobsIds.filter(function(id) {
								return allJobIds.indexOf(id) != -1;
							});
							$location.search('jobs', scope.jobsIds);
						});
					}
				});

				scope.onJobsFound = function(params) {
					// console.log('params: ', params);
					scope.searchParams = params;
					scope.jobsTableParams.page(1);

					var paramsJobIds = $location.search().jobs;
					if (paramsJobIds) {
						if (typeof paramsJobIds === 'string')
							paramsJobIds = [parseInt(paramsJobIds)];
						else
							paramsJobIds = paramsJobIds.map(function(v) {
								return parseInt(v);
							});

						scope.jobsIds = paramsJobIds;

						console.log('paramsJobIds: ', paramsJobIds);
					} else {
						scope.jobIds = [];
					}
					scope.jobsTableParams.reload();
				}

				scope.callback = function() {
					scope.onJobsSelected({
						jobIds: scope.jobsIds
					});
				}

				scope.update = function() {
					$location.search('jobs', scope.jobsIds);
				}

			}
		}
	}
]);
