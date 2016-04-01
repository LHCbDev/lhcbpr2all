/**=========================================================
 * Module:lhcbpr-job-descriptions.js
 * Provides a simple demo for typeahead
 =========================================================*/

App.controller('JobsController', ['$scope', function($scope) {

}]);

App.controller('JobsListController', ['$scope', '$filter', '$q', 'ngTableParams', 'ngDialog', 'lhcbprResources', '$timeout', '$sce', '$http', '$location', 'BUILD_PARAMS',
	function($scope, $filter, $q, ngTableParams, ngDialog, lhcbprResources, $timeout, $sce, $http, $location, BUILD_PARAMS) {

		$scope.jobsIds = [];
		$scope.isShowSearchForm = !($location.search().ssf == 'false');
		$scope.cachedJobs = {};
		$scope.isShowingDialog = false;
		$scope.media_url = BUILD_PARAMS.url_api + '/media/jobs';

		var isImage = function(filename) {
			var ext = filename.split('.').pop().toLowerCase();
			return ext == 'gif' || ext == 'png' || ext == 'jpeg' || ext == 'jpg';
		};

		$scope.jobsTableParams = new ngTableParams({
			page: 1, // show first page
			count: 10 // count per page
		}, {
			total: 0, // length of data
			getData: function($defer, params) {
				// use build-in angular filter

				if (!$scope.searchParams) {
					return;
				}
				lhcbprResources.all('search-jobs').getList({
					application: $scope.searchParams.apps.join(),
					versions: $scope.searchParams.versions.join(),
					options: $scope.searchParams.options.join(),
					platforms: $scope.searchParams.platforms.join(),
					page: params.page(),
					page_size: params.count()
				}).then(function(jobs) {
					if (jobs._resultmeta) {
						params.total(jobs._resultmeta.count);
					}
					// $defer.resolve(orderedData.slice((params.page() - 1) * params.count(), params.page() * params.count()));
					$defer.resolve(jobs);
				});
			}
		});

		$scope.attrsTableParams = new ngTableParams({
			page: 1, // show first page
			count: 10 // count per page
		}, {
			total: 0, // length of data
			getData: function($defer, params) {
				// use build-in angular filter
				if ($scope.jobsIds && $scope.jobsIds.length > 0) {
					lhcbprResources.all('compare').getList({
						ids: $scope.jobsIds.join(),
						contains: $scope.contains,
						page: params.page(),
						page_size: params.count()
					}).then(function(attrs) {
						if (attrs._resultmeta) {
							params.total(attrs._resultmeta.count);
						}
						$defer.resolve(attrs);
						var attrId = $location.search().attr;
						if (attrId && !$scope.isShowingDialog) {
							attrId = parseInt(attrId);
							if (!isNaN(attrId)) {
								var theAttr = null;
								attrs.forEach(function(a) {
									if (a.id == attrId)
										theAttr = a;
								});
								if (theAttr != null)
									$scope.showCompareDialog(theAttr);
							}
						}
					});
				}
			}
		});

		// Fix bug in ng-table
		$scope.jobsTableParams.settings().$scope = $scope;
		$scope.attrsTableParams.settings().$scope = $scope;

		$scope.showResults = function(job) {
			// console.log(job.resource_uri);
		};

		$scope.onJobsFound = function(params) {
			console.log('AAA', params);
			$scope.searchParams = params;
			$scope.jobsTableParams.page(1);
			$scope.jobsIds = [];
			$scope.jobsTableParams.reload();
		};

		$scope.isDisabledCompare = function() {
			return $scope.jobsIds && $scope.jobsIds.length == 0;
		};

		var showAttributes = function(attributes) {
			console.log(attributes);
		};

		var reloadAttrsTable = function() {
			$scope.attrsTableParams.page(1);
			$scope.attrsTableParams.reload();

			console.log($scope.cachedJobs);
		};

		$scope.$watch('attrFilter', function(val) {
			$scope.contains = val;
			reloadAttrsTable();
		});

		$scope.compare = function(ids) {
			var requestIds = [];
			$scope.isShowSearchForm = false;
			$location.search('ssf', false);
			$scope.jobsIds = ids;

			for (var i = 0, l = ids.length; i < l; ++i) {
				var promises = [];
				promises.push(
					lhcbprResources.one('jobs', ids[i]).get().then(
						function(job) {
							$scope.cachedJobs[job.id] = job;
						}
					)
				);

				$q.all(promises).then(reloadAttrsTable);
			}
		};

		$scope.showSearchForm = function() {
			$scope.isShowSearchForm = true;
			$location.search('ssf', true);
		};

		$scope.getJobName = function(id) {
			var job = $scope.cachedJobs[id];
			if (job) {
				var av = job.job_description.application_version;
				return av.application.name + ' ' + av.version + '(id=' + job.id + ')';
			} else {
				return 'undefined';
			}
		};

		$scope.getJobValue = function(attr, jv) {
			if (attr.dtype == 'File') {
				return;
			}
		};

		$scope.showCompareButton = function(dtype, values) {
			if (dtype == 'File') {
				if (values.length > 0) {
					return isImage(values[0].value);
				}
				return false;
			}
			return true;
		};

		$scope.showCompareDialog = function(attr) {
			$location.search('attr', attr.id);
			$scope.isShowingDialog = true;
			if (attr.dtype == 'Integer' || attr.dtype == 'Float')
				$scope.trend(attr);
			else if (attr.dtype == 'File')
				$scope.filesCompare(attr);
		};

		$scope.trend = function(attr) {
			// $scope.isShowTrend = true;
			attr.jobvalues.reverse();
			$scope.attr = attr;
			var labels = attr.jobvalues.map(function(v) {
				return $scope.getJobName(v.job.id);
			});
			$scope.mean = attr.jobvalues.reduce(function(prev, curr) {
				return prev + parseFloat(curr.value);
			}, 0) / attr.jobvalues.length;
			$scope.err = Math.sqrt(attr.jobvalues.reduce(function(prev, curr) {
				return prev + Math.pow(parseFloat(curr.value) - $scope.mean, 2);
			}, 0) / (attr.jobvalues.length - 1));
			var datasets = [{
				label: attr.name,
				fillColor: 'rgba(0,255,0,0)',
				strokeColor: 'blue',
				pointColor: 'blue',
				pointStrokeColor: '#fff',
				pointHighlightFill: '#fff',
				pointHighlightStroke: 'blue',
				data: attr.jobvalues.map(function(v) {
					return parseFloat(v.value);
				})
			}];
			if (attr.thresholds.length > 0) {
				datasets.push({
					label: 'Upper threshold',
					fillColor: 'rgba(35,183,229,0)',
					strokeColor: 'red',
					pointColor: 'red',
					pointStrokeColor: '#fff',
					pointHighlightFill: '#fff',
					pointHighlightStroke: 'red',
					data: attr.jobvalues.map(function(v) {
						return attr.thresholds[0].up_value;
					})
				});
				datasets.push({
					label: 'Down threshold',
					fillColor: 'rgba(35,183,229,0)',
					strokeColor: 'green',
					pointColor: 'green',
					pointStrokeColor: '#fff',
					pointHighlightFill: '#fff',
					pointHighlightStroke: 'green',
					data: attr.jobvalues.map(function(v) {
						return attr.thresholds[0].down_value;
					})
				});
			}
			$scope.lineData = {
				labels: labels,
				datasets: datasets
			};

			ngDialog.open({
				template: 'chartTemplate',
				className: 'chart-dialog',
				scope: $scope,
				preCloseCallback: function() {
					$scope.$apply(function() {
						$location.search('attr', null);
					});
				}
			});
		};

		$scope.filesCompare = function(attr) {
			attr.jobvalues.reverse();
			$scope.files = attr.jobvalues.map(
				function(v) {
					return {
						type: 'image',
						url: '/media/jobs/' + v.job.id + '/' + v.value
					};
				}
			);

			ngDialog.open({
				template: 'filesTemplate',
				className: 'chart-dialog',
				scope: $scope,
				preCloseCallback: function() {
					$scope.$apply(function() {
						$location.search('attr', null);
					});
				}
			});
		};

		$scope.chartHeight = function() {
			return $(window).height() - 160;
		};

		$scope.chartWidth = function() {
			return $(window).width() - 60;
		};

		if (!$scope.isShowSearchForm && $location.search().jobs) {
			var paramsJobIds = $location.search().jobs;
			if (paramsJobIds) {
				if (typeof paramsJobIds === 'string')
					paramsJobIds = [parseInt(paramsJobIds)];
				else
					paramsJobIds = paramsJobIds.map(function(v) {
						return parseInt(v);
					});
				$scope.compare(paramsJobIds);
			}
		}

	}
]);

App.controller('JobsDetailController', ['$scope', '$filter', '$stateParams', 'ngTableParams', 'lhcbprResources',
	function($scope, $filter, $stateParams, ngTableParams, lhcbprResources) {

		var createTable = function(data) {
			//console.log(data);
			$scope.tableParams = new ngTableParams({
				page: 1, // show first page
				count: 10 // count per page
			}, {
				total: data.length, // length of data
				getData: function($defer, params) {
					// use build-in angular filter
					var orderedData = params.sorting() ?
						$filter('orderBy')(data, params.orderBy()) :
						data;

					$defer.resolve(orderedData.slice((params.page() - 1) * params.count(), params.page() * params.count()));
				}
			});
		};

		lhcbprResources.one('jobs', $stateParams.job).get().then(function(job) {
			$scope.job = job;
			createTable(job.results);
		});
	}
]);
