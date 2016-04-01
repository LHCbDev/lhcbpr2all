Module.create('geantstandalone', 'GEANT', 2)
	.addMenuItems({
		text: "GEANT standalone tests",
		sref: "app.geantstandalone",
		icon: "icon-grid"
	})
	.addState({
		name: 'geantstandalone',
		title: 'GEANT standalone tests',
		url: '/geantstandalone',
		templateUrl: 'geantstandalone.html',
		resolve: ['geantstandalone', 'jsroot','ngTable', 'ngDialog']
	})
	.start();
