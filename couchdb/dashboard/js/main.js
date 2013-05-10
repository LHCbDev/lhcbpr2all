jQuery.fn.lbSlotTable = function(data) {
	var tab = $('<table class="summary" border="1"/>');
	// header
	var hdr = $('<tr/>');
	hdr.append('<th>Project</th><th>Version</th>');
	$.each(data.value.platforms, function(idx, val) {
		hdr.append('<th nowrap>' + val + '</th>');
	});
	tab.append(hdr);

	// rows
	$.each(data.value.projects, function(idx, val) {
		var tr = $('<tr project="' + val.name + '"/>')
		   .append('<th>' + val.name + '</th><th>' + val.version + '</th>');
		$.each(data.value.platforms, function(idx, val) {
			tr.append('<td platform="' + val + '">' +
					  '<table class="results"><tr>' +
					  '<td class="build"/><td class="tests"/></tr></table>');
		});
		tab.append(tr);
	});
	this.append(tab);

	// trigger load of the results of each platform
	$.each(data.value.platforms, function(idx, val) {
		var query = {'key': JSON.stringify([data.key[1], data.value.build_id, val])};
		$.getJSON('_view/summaries', query, function(data) {
			$.each(data.rows, function(idx, row){
				/* Expects row like:
				 * {"key": ["slot", build_id, "platform"],
				 *  "value": {"project": "Gaudi",
				 *            "build": {"warnings": 0, "errors": 0},
				 *            "tests": {"failed": 0, "total": 100}}
				 * }
				 */
				var key = row.key;
				var value = row.value;
				if (value.project) {
					// FIXME: simplify the selector
					var summ = $('div[slot="' + key[0] + '"][build_id="' + key[1] + '"]'
				                 + ' tr[project="' + value.project + '"]'
					             + ' td[platform="' + key[2] + '"]');
					if (value.build) {
						var b = summ.find('.build').text('build');
						if (value.build.errors) {
							b.addClass('failure').append(' (' + value.build.errors + ')');
						} else if (value.build.warnings) {
							b.addClass('warning').append(' (' + value.build.warnings + ')');
						} else {
							b.addClass('success');
						}
					}
					if (value.tests) {
						var t = summ.find('.tests').text('tests');
						if (value.tests.failed) {
							t.addClass('failure').append(' (' + value.tests.failed + ')');
						} else if (!value.tests.total) {
							t.addClass('warning').append(' (0)');
						} else {
							t.addClass('success');
						}
					}
				}
			});
		});
	});
	return this;
}

// fill an element with one <div> per slot build for the given day
jQuery.fn.lbNightly = function () {
	return this.each(function(){
		var el = $(this);
		var day = moment(el.attr('day'));
		var next = moment(day).add('days', 1);
		var query = {'startkey': JSON.stringify([day.format('YYYY/MM/DD')]),
					 'endkey': JSON.stringify([next.format('YYYY/MM/DD')])};
		el.append($('<h1/>').append(day.format('dddd')).append('<hr/>'));
		$.getJSON('_view/slots', query, function(data) {
			$.each(data.rows, function(idx, row){
				var slot = $('<div class="slot" slot="' + row.key[1]
				             + '" build_id="' + row.value.build_id + '"/>');
				slot.append($('<h4/>').append(row.key[1] + ': ' + row.value.description));
				// FIXME: This is a bit convoluted, but it is needed to ensure that we work on the right element
				$('.day[day="' + row.key[0] + '"]').append(slot);
				slot.lbSlotTable(row);
			});
		});
	});
}

$(function(){
	var today = moment();
	for(var day = 0; day < 7; day++) {
		var d = moment(today).subtract('days', day);
		$('#middle').append('<div class="day" day="' + d.format('YYYY/MM/DD') + '"/>');
	}

	$('.day').lbNightly();
});