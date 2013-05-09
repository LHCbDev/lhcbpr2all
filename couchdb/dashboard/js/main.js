$(function(){
	var today = moment();
	var daylist = $("<ul/>");
	$("#slots").append(daylist);

	for(var day = 0; day < 7; day++) {
		var d = moment(today).subtract('days', day);
		var item = $("<li id=\"day_" + d.format("YYYYMMDD") + "\"/>").append(d.format("LL"));
		daylist.append(item);
	}

	for(var day = 0; day < 7; day++) {
		var d = moment(today).subtract('days', day);
		var daystring = d.format("YYYY/MM/DD");
		$.getJSON('_view/slots', {"startkey": JSON.stringify([daystring]),
			                      "endkey": JSON.stringify([moment(d).add('days', 1).format("YYYY/MM/DD")])},
			      function(data) {
			var k = null;
			var l = $("<ul/>");
			$.each(data.rows, function(idx, row){
				k = row.key[0];
				l.append($("<li/>").append(row.key[1]));
			});
			if (k)
				$("#day_" + k.replace(/\//g, "")).append(l);
		});
	}
});