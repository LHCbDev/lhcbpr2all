function(doc) {
	if (doc.slot && doc.build_id != undefined) {
		var data = {_rev: doc._rev};
		if (doc.platform)
			emit([doc.slot, doc.build_id, doc.platform], data);
		else
			emit([doc.slot, doc.build_id], data);
	}
}
