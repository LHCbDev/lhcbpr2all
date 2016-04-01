Module.create('trend', 'Trends', 2)
	.addMenuItems({
		text: "Trends",
		sref: "app.trend",
		icon: "icon-grid"
	})
	.addState({
		name: 'trend',
		title: 'Trends',
		templateUrl: 'trends.html',
		resolve: ['trend', 'chartjs', 'ngTable', 'ngDialog']
	})
	.start();
