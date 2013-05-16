function(doc) {
	if (doc.type == "build-result" || doc.type == "tests-result") {
		var k = [doc.slot, doc.build_id, doc.platform];
		var data = {project: doc.project};
		if (doc.type == "build-result") {
			data.build = {warnings: doc.warnings,
						  errors: doc.errors}
		} else if (doc.type == "tests-result") {
			data.tests = {failed: 0, total: doc.results.length}
			for (var idx in doc.results) {
				if (doc.results[idx].outcome != 'PASS' &&
					doc.results[idx].outcome != 'UNTESTED')
					data.tests.failed++;
			}
		}
		emit(k, data);
	} else if (doc.type == "job-start" || doc.type == "job-end") {
		var k = [doc.slot, doc.build_id, doc.platform];
		var data = {type: doc.type};
		if (doc.type == "job-start") {
			data.host = doc.host;
			data.job_id = doc.job_id;
			data.started = doc.started;
		} else if (doc.type == "job-end") {
			data.completed = doc.completed;
		}
		emit(k, data);
	}
}
