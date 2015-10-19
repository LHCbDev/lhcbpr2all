function(head, req) {
	var row;
	start({
		"headers": {
			"Content-Type": "text/plain"
		}
	});
	while(row = getRow()) {
		send(row.value + "\n");
	}
}
