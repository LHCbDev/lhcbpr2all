Module.create('histograms', 'Histograms', 2)
	.addMenuItems({
		text: "Histograms",
		sref: "app.histograms",
		icon: "icon-grid"
	})
	.addState({
		name: 'histograms',
		title: 'Histograms',
		url: '/histograms',
		templateUrl: 'histograms.html',
		resolve: ['histograms', 'chartjs', 'slider', 'ngTable', 'ngDialog']
	})
	.start();
