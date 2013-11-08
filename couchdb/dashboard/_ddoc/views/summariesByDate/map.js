function(doc) {

  if(doc.type == 'build-result' || doc.type == 'tests-result') {

	var key = doc.completed;
    var dateTemp = new Date(eval(key.substring(0,4)),eval(key.substring(5,7))-1,eval(key.substring(8,10)),eval(key.substring(11,13)),eval(key.substring(14,16)),eval(key.substring(17,19)));

    var data = {slot: doc.slot, project: doc.project, platform: doc.platform,date:doc.completed,build_id:doc.build_id,date:dateTemp.toGMTString()};




   if(doc.type == 'build-result'){
	   data.build = {warnings: doc.warnings, errors: doc.errors};
   }else{
		data.tests = {failed: 0, total: doc.results.length};
	    for (var idx in doc.results) {
		if (doc.results[idx].outcome != 'PASS' &&
		    doc.results[idx].outcome != 'UNTESTED')
		 data.tests.failed++;
	    }
   }
   emit(key, data);

  }
}

