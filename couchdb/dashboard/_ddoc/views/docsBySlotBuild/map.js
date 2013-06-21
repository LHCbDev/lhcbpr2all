function(doc) {
	if (doc.slot && doc.build_id != undefined)
		emit([doc.slot, doc.build_id], null);
}
