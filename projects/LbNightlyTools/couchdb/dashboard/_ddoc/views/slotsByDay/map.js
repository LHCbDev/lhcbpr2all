function(doc) {
	if (doc.type == "slot-config") {
		var projs = [];
		for(var idx in doc.projects) {
			var proj_data = {name: doc.projects[idx].name,
							 version: doc.projects[idx].version};
			if (doc.projects[idx].disabled == undefined)
				proj_data.disabled = doc.projects[idx].checkout == "ignore";
			else
				proj_data.disabled = doc.projects[idx].disabled;
			if (doc.projects[idx].no_test)
			    proj_data.no_test = true;
			projs.push(proj_data);
		}
		data = {"slot": doc.slot,
				"description": doc.description,
				"build_id": doc.build_id,
				"platforms": [],
				"projects": projs};
		if (doc.build_tool) {
			data.build_tool = doc.build_tool;
		} else {
			if (doc.USE_CMT) {
				data.build_tool = "cmt";
			} else {
				data.build_tool = "cmake";
			}
		}
		if (doc.platforms) {
			data.platforms = doc.platforms;
		} else if (doc.default_platforms) {
			data.platforms = doc.default_platforms;
		}
		if (doc.no_test) data.no_test = true;
		emit(doc.date, data);
	}
}