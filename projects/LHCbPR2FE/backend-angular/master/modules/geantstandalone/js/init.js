Module.create('geantstandalone', 'GEANT', 2)
	.addMenuItems([{
		text: "Hadronic",
		sref: "app.geantstandalone",
		icon: "icon-grid"
	},
	{
		text: 'TestEm3',
		sref: 'app.geanttestem3',
		icon: "icon-grid"
	},
	{
		text: 'TestEm5',
		sref: 'app.geanttestem5',
		icon: "icon-grid"
	},
	])
	.addState({
		name: 'geantstandalone',
		title: 'Hadronic',
		url: '/geantstandalone',
		templateUrl: 'geantstandalone.html',
		resolve: ['geantstandalone', 'jsroot','ngTable', 'ngDialog']
	})
	.addState({
		name: 'geanttestem3',
		title: 'TestEm3',
		url: '/geanttestem3',
		templateUrl: 'geanttestem3.html',
		resolve: ['geantstandalone','jsroot','ngTable', 'ngDialog']
	})
	.addState({
		name: 'geanttestem5',
		title: 'TestEm5',
		url: '/geanttestem5',
		templateUrl: 'geanttestem5.html',
		resolve: ['geantstandalone','jsroot','ngTable', 'ngDialog']
	})
	.start();
