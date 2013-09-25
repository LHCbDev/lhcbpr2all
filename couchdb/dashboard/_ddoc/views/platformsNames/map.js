function(doc) {
	if (doc.type == "slot-config") {
		doc.default_platforms.forEach(function(platform) {
			emit(platform, null);
		});
	}
}
