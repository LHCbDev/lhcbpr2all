App.controller('Geanttestem3Controller', function($scope, $log, lhcbprResourcesHelper, BUILD_PARAMS) {
	$scope.url = BUILD_PARAMS.url_root;


	$scope.analyze = function(ids) {
    lhcbprResourcesHelper.compare(ids, "TESTEM3_TABLE").then(showTable);
  };
  var graphs = [];
  function showTable(results){
  	var job_values = results[0].jobvalues;
  	graphs = [];
  	color = 1;
  	job_values.forEach(function(jvalue){
  		var x = [];
  		var y = [];
  		var values = JSON.parse(jvalue.value);
  		values.forEach(function(val){
  			x.push(val[0]);
  			y.push(val[1]);
  		});
  		var gr = JSROOT.CreateTGraph(x.length, x, y);
  		gr.fName = "Job id=" + jvalue.job.id;
  		gr.fFillColor = 1;
  		gr.fFillStyle = 1001;
  		gr.fLineColor = color++;
  		gr.fMarkerSize = 2;
  		gr.fMarkerStyle = 2;
  		graphs.push(gr);
  	});
  	console.log("SASHA1", graphs);
  	var mg = JSROOT.CreateTMultiGraph.apply(this, graphs);
  	JSROOT.draw("#em3", mg);
  }

  function createCanvas(objArr) {
	  var canvas = JSROOT.JSONR_unref({
	    '_typename': 'TCanvas',
	    'fUniqueID': 0,
	    'fBits': 53673992,
	    'fLineColor': 1,
	    'fLineStyle': 1,
	    'fLineWidth': 1,
	    'fFillColor': 0,
	    'fFillStyle': 1001,
	    'fLeftMargin': 0.1,
	    'fRightMargin': 0.1,
	    'fBottomMargin': 0.1,
	    'fTopMargin': 0.1,
	    'fXfile': 2,
	    'fYfile': 2,
	    'fAfile': 1,
	    'fXstat': 0.99,
	    'fYstat': 0.99,
	    'fAstat': 2,
	    'fFrameFillColor': 0,
	    'fFrameLineColor': 1,
	    'fFrameFillStyle': 1001,
	    'fFrameLineStyle': 1,
	    'fFrameLineWidth': 1,
	    'fFrameBorderSize': 1,
	    'fFrameBorderMode': 0,
	    'fX1': 0,
	    'fY1': 0,
	    'fX2': 1,
	    'fY2': 1,
	    'fXtoAbsPixelk': 0.00005,
	    'fXtoPixelk': 0.00005,
	    'fXtoPixel': 698,
	    'fYtoAbsPixelk': 475,
	    'fYtoPixelk': 475,
	    'fYtoPixel': -475,
	    'fUtoAbsPixelk': 0.00005,
	    'fUtoPixelk': 0.00005,
	    'fUtoPixel': 698,
	    'fVtoAbsPixelk': 475,
	    'fVtoPixelk': 475,
	    'fVtoPixel': -475,
	    'fAbsPixeltoXk': 0,
	    'fPixeltoXk': 0,
	    'fPixeltoX': 0.001432665,
	    'fAbsPixeltoYk': 1,
	    'fPixeltoYk': 0,
	    'fPixeltoY': -0.002105263,
	    'fXlowNDC': 0,
	    'fYlowNDC': 0,
	    'fXUpNDC': 0,
	    'fYUpNDC': 0,
	    'fWNDC': 1,
	    'fHNDC': 1,
	    'fAbsXlowNDC': 0,
	    'fAbsYlowNDC': 0,
	    'fAbsWNDC': 1,
	    'fAbsHNDC': 1,
	    'fUxmin': 0,
	    'fUymin': 0,
	    'fUxmax': 1,
	    'fUymax': 1,
	    'fTheta': 30,
	    'fPhi': 30,
	    'fAspectRatio': 0,
	    'fNumber': 0,
	    'fTickx': 0,
	    'fTicky': 0,
	    'fLogx': 0,
	    'fLogy': 0,
	    'fLogz': 0,
	    'fPadPaint': 0,
	    'fCrosshair': 0,
	    'fCrosshairPos': 0,
	    'fBorderSize': 2,
	    'fBorderMode': 0,
	    'fModified': true,
	    'fGridx': true,
	    'fGridy': true,
	    'fAbsCoord': false,
	    'fEditable': true,
	    'fFixedAspectRatio': false,
	    'fExecs': null,
	    'fTitle': 'multigraph',
	    'fDISPLAY': '$DISPLAY',
	    'fDoubleBuffer': 1,
	    'fRetained': true,
	    'fXsizeUser': 0,
	    'fYsizeUser': 0,
	    'fXsizeReal': 20,
	    'fYsizeReal': 13.61032,
	    'fWindowTopX': 0,
	    'fWindowTopY': 45,
	    'fWindowWidth': 700,
	    'fWindowHeight': 500,
	    'fCw': 698,
	    'fCh': 475,
	    'fCatt': {
	      '_typename': 'TAttCanvas',
	      'fXBetween': 2,
	      'fYBetween': 2,
	      'fTitleFromTop': 1.2,
	      'fXdate': 0.2,
	      'fYdate': 0.3,
	      'fAdate': 1
	    },
	    'kMoveOpaque': true,
	    'kResizeOpaque': true,
	    'fHighLightColor': 5,
	    'fBatch': true,
	    'kShowEventStatus': false,
	    'kAutoExec': true,
	    'kMenuBar': true
	  });

	  var lst = JSROOT.CreateTList();
	  _.forEach(objArr, function(o) { lst.Add(o);});
	  canvas.fPrimitives = lst;
	  return canvas;
	}
});
