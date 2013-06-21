function(doc) {
	if (doc.slot && doc.build_id != undefined)
		if (doc.platform)
			emit([doc.slot, doc.build_id, doc.platform], null);
		else
			emit([doc.slot, doc.build_id], null);
}
