function(doc) {
	if (doc.type == "build-result"
		|| doc.type == "tests-result"
		|| doc.type == "job-infos") {
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
		} else {
			data.host = doc.host;
			data.job_id = doc.job_id;
			data.started = doc.started;
			data.completed = doc.completed;
		}
		emit(k, data);
	}
}
