function(doc) {
	if (doc.type == "slot-config") {
		var projs = [];
		for(var idx in doc.projects) {
			projs.push({name: doc.projects[idx].name,
				version: doc.projects[idx].version});
		}
		data = {"description": doc.description,
				"build_id": doc.build_id,
				"platforms": [],
				"projects": projs};
		if (doc.platforms) {
			data.platforms = doc.platforms
		} else if (doc.default_platforms) {
			data.platforms = doc.default_platforms
		}
		emit([doc.date, doc.slot], data)
	}
}
