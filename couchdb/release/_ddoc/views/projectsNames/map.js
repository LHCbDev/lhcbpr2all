function(doc) {
	if (doc.type == "slot-config") {
		doc.projects.forEach(function(project) {
			emit(project.name, null);
		});
	}
}
