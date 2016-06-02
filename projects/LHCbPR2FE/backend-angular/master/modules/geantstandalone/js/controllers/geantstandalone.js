App.controller('GeantstandaloneController', function($scope, $log, lhcbprResourcesHelper, BUILD_PARAMS) {
  $scope.url = BUILD_PARAMS.url_root;
  $scope.graphs = '';
  $scope.files_and_titles = null;

  $scope.analyze = function(ids) {
    lhcbprResourcesHelper.search({ids: ids}).then(showJobs);
  };

  $scope.models = [
  	{value: 'FTFP', text: 'FTFP'},
  	{value: 'FTFP_BERT', text: 'FTFP_BERT'},
  	{value: 'QGSP_BERT', text: 'QGSP_BERT'},
  ];

  $scope.materials = [
  	{value: 'Al', text: 'Aluminium'},
  	{value: 'Be', text: 'Berilium'},
  	{value: 'Si', text: 'Silicon'},
  ];

  $scope.particles = [
  	{value: 'proton', text: 'Proton'},
  	{value: 'anti_proton', text: 'Anti-proton'},
  	{value: 'kaon+', text: 'Kaon+'},
  	{value: 'kaon-', text: 'Kaon-'},
  	{value: 'pi+', text: 'Pion+'},
  	{value: 'pi-', text: 'Pion-'},
  ];

  $scope.plots = [
  	{value: 'Total', text: 'Total'},
  	{value: 'Elastic', text: 'Elastic'},
  	{value: 'Inelastic', text: 'Inelastic'},
  ];
  var selected = ['Models', 'Materials', 'Particles', 'Plots', 'Jobs'];
  selected.forEach(function(item) {
    $scope['selected' + item] = [];
    $scope.$watchCollection('selected' + item, drawPlots);
  });

  // Preselected items
  $scope.selectedModels.push($scope.models[0].value);
  $scope.selectedParticles.push($scope.particles[0].value);
  $scope.selectedMaterials.push($scope.materials[0].value);
  $scope.selectedPlots.push($scope.plots[0].value);

  ///

  function drawPlots(values) {
    var newFiles = null;
    $scope.selectedJobs.forEach(function(job) {
      $scope.selectedModels.forEach(function(model) {
        $scope.selectedParticles.forEach(function(particle) {
          $scope.selectedMaterials.forEach(function(material) {
            var file = job.id + '/' + model + '_' + particle + '_' + material + '.root';
            if (!newFiles) newFiles = {};
            newFiles[file] = job.job_description.application_version.version + ' ' + job.platform.content + ' ' + model;
          });
        });
      });
    });
    if (newFiles) {
      $scope.files_and_titles = newFiles;
      $scope.graphs = $scope.selectedPlots;
    }
  }

  function showJobs(jobs) {
    $scope.selectedJobs = jobs;
  }

});
