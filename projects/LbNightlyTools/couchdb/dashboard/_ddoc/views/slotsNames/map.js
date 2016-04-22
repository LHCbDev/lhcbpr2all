function(doc) {
	if (doc.type == "slot-config") {
		emit(doc.slot, null);
	}
}
