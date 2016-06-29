App.directive('rootjs', function($timeout) {
  JSROOT.source_dir = 'app/vendor/jsroot/';
  return {
  restrict: 'E',
  scope: {
    data: '=',
    width: '@',
    height: '@'
  },
  template: '<div ng-style="{\'width\': width, \'height\': height}"></div>',
  link: function(scope, element) {

    scope.$watch('data', function(value) {
    	if(!value) return;
    	// console.log('data', value.fGraphs.arr);
      try {
        if (angular.isObject(value)) {
          scope.json = value;
        } else {
          	scope.json = angular.fromJson(value);
        }
        var pad = element.children()[0];
        var obj = JSROOT.JSONR_unref(scope.json);
        var canvas = null;
        if (obj._typename != 'TCanvas'){
        	var primitives = [obj];
        	if (obj._typename == "TMultiGraph" ){
        		primitives.push(createLegend(obj));
        	}
        	console.log(primitives);
	        canvas = createCanvas(primitives);
        } else {
	        	canvas = obj;
	      }
        
        pad.innerHTML = "";
        $timeout(function(){JSROOT.draw(pad, canvas)},2);


        // setTimeout(function(){JSROOT.draw(pad, createLegend({}));},1000);
        //JSROOT.draw(pad, createLegend({}));
      } catch (ex) {
        console.log('rootjs directive: ' + ex);
      }
    });
  }
};

  function createLegend(obj) {
  var legend = JSROOT.JSONR_unref({
    '_typename': 'TLegend',
    'fUniqueID': 0,
    'fBits': 50331657,
    'fLineColor': 1,
    'fLineStyle': 1,
    'fLineWidth': 1,
    'fFillColor': 0,
    'fFillStyle': 1001,
    'fX1': 1.600000e-01,
    'fY1': 7.500000e-01,
    'fX2': 0.99,
    'fY2': 0.99,
    'fX1NDC': -2.353437e-185,
    'fY1NDC': -2.353437e-185,
    'fX2NDC': -2.353437e-185,
    'fY2NDC': -2.353437e-185,
    'fBorderSize': 1,
    'fInit': 0,
    'fShadowColor': 1,
    'fCornerRadius': 0,
    'fOption': 'brNDC',
    'fName': 'TPave',
    'fTextAngle': 0,
    'fTextSize': 0,
    'fTextAlign': 12,
    'fTextColor': 1,
    'fTextFont': 42,
    'fEntrySeparation': 1.000000e-01,
    'fMargin': 2.500000e-01,
    'fNColumns': 1,
    'fColumnSeparation': 0
  });
  var lst = JSROOT.CreateTList();
  _.forEach(obj.fGraphs.arr, function(p) {
    lst.Add(createTLegendEntry(p.fTitle, p.fLineColor));
  });

  legend.fPrimitives = lst;
  return legend;
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

  function createTLegendEntry(title, color) {
  var entry = {
    '_typename': 'TLegendEntry',
    'fUniqueID': 0,
    'fBits': 50331648,
    'fTextAngle': 0,
    'fTextSize': 1,
    'fTextAlign': 0,
    'fTextColor': 0,
    'fTextFont': 0,
    'fLineColor': color,
    'fLineStyle': 1,
    'fLineWidth': 1,
    'fFillColor': 0,
    'fFillStyle': 0,
    'fMarkerColor': color,
    'fMarkerStyle': 21,
    'fMarkerSize': 1,
    'fLabel': title,
    'fOption': 'lpf'
  };
  return entry;
}
});

App.directive('rootjsserver', function($http) {
  return {
  restrict: 'E',
  scope: {
    entrypoint: '=',
    files: '=',
    items: '=',
    width: '@',
    height: '@'
  },
  template: '<rootjs data="data" width="{{width}}" height="{{height}}"></rootjs>',
  link: function(scope) {
    scope.$watchGroup(['files', 'items'], function(values) {
    	console.log('watch', values);
    	if(values[0] && values[1]) {
      	activate(values[0], values[1]);
    	}
    });

    ///
    function activate(files, items) {
    	console.log("activate", files, items);
      var strFiles = _.map(_.keys(files), encodeURIComponent).join(',');
      var url = scope.entrypoint + '/?files=' +
      strFiles +
      '&items=' + encodeURIComponent(items) +
      '&callback=JSON_CALLBACK';
      $http.jsonp(url).then(loaded, error);

    }

    function loaded(data) {
      var graph, mg, color;
      var graphs = [];
      var others = [];
      color = 1;
      _.forEach(data.data['result'], function(file) {
        _.forEach(file['items'], function(value, key) {
        	if(value['_typename'] == 'TGraph' || value['_typename'] == 'TGraphErrors'){
	          graph = JSROOT.JSONR_unref(value);
	          graph.fLineColor = color++;
	          graph.fTitle = scope.files[file.root] + ' ' + graph.fTitle;
	          graphs.push(graph);
          } else{
	          others.push(JSROOT.JSONR_unref(value));
          }
        });
      });

      if (others.length > 0){
      	scope.data = others[0];

      }else{
      	console.log("SASHA", graphs);
      	scope.data = JSROOT.CreateTMultiGraph.apply(this, graphs);
      }
    }

    function error(err) {
      console.error(err);
    }
  }
};
});

