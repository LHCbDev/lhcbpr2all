Module.create('jobs', 'LHCbPR Jobs', 1)
	.addMenuItems([
		{
			text: "Job Descriptions",
			sref: "app.job_descriptions.list",
			icon: "icon-grid",
			alert: "new"
		},
		{
			text: "Jobs",
			sref: "app.jobs.list",
			icon: "icon-grid",
			alert: "new"
		}
	])
	.addState({
		name: 'job_descriptions',
		abstract: true,
		template: '<ui-view/>',
		resolve: ['jobs']
	})
	.addState({
		name: 'job_descriptions.list',
		title: 'Job Descriptions',
		templateUrl: 'job-descriptions.html'
	})
	.addState({
		name: 'job_descriptions.add',
		title: 'Add Job Description',
		templateUrl: 'job-description.html'
	})
	.addState({
		name: 'jobs',
		abstract: true,
		template: '<ui-view/>',
		resolve: ['jobs']
	})
	.addState({
		name: 'jobs.list',
		title: 'Jobs',
		templateUrl: 'jobs.html',
		resolve: ['chartjs','ngTable', 'ngDialog']
	})
	.addState({
		name: 'jobs.example',
		templateUrl: 'jobs.example.html',
		resolve: ['ngTable']
	})
	.addState({
		name: 'jobs.detail',
		url: '/detail/:job',
		title: 'Jobs',
		templateUrl: 'job.html',
		resolve: ['ngTable']
	})
	.addState({
		name: 'trends',
		abstract: true,
		template: '<ui-view/>',
		controller: 'NullController',
		resolve: ['jobs']
	})
	.addState({
		name: 'trends.chart',
        url: '/option/:option/attribute/:attribute',
        templateUrl: 'trends.chart.html',
		resolve: ['chartjs']
	})
	.start();
