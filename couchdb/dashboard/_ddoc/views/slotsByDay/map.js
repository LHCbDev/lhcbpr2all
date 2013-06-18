function(doc) {
	if (doc.type == "slot-config") {
		var projs = [];
		for(var idx in doc.projects) {
			var proj_data = {name: doc.projects[idx].name,
							 version: doc.projects[idx].version};
			if (doc.projects[idx].checkout == "ignore")
				proj_data.disabled = true;
			projs.push(proj_data);
		}
		data = {"slot": doc.slot,
				"description": doc.description,
				"build_id": doc.build_id,
				"platforms": [],
				"projects": projs};
		if (doc.platforms) {
			data.platforms = doc.platforms;
		} else if (doc.default_platforms) {
			data.platforms = doc.default_platforms;
		}
		emit(doc.date, data);
	}
}
