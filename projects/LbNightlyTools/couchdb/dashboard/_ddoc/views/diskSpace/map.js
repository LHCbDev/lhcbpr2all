function(doc) {
	if (doc.type == "disk-usage")
		emit([doc.slot, doc.build_id],
			 {path:doc.path,
			  volume: doc.name,
			  free: doc.bsize * doc.bavail,
			  free_ratio: doc.bavail / doc.blocks,
			  updated: doc.updated});
}
