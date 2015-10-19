function(doc) {
	if (doc.type == "slot-config") {
		doc.projects.forEach(function(project) {
			emit([project.name, project.version], doc.build_id);
		});
	}
}
