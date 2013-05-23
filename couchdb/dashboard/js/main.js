var ARTIFACTS_BASE_URL = 'http://buildlhcb.cern.ch/artifacts/';

// variable set from a cookie
if (!$.cookie("enabled_days")) {
	$.cookie("enabled_days", JSON.stringify(["Today"]));
}
var enabled_days = JSON.parse($.cookie("enabled_days"));

function buildURL(slot, build_id, platform, project) {
	return ARTIFACTS_BASE_URL + slot + '/' + build_id
		+ '/summaries.' + platform + '/' + project + '/build_log.html';
}

function testsURL(slot, build_id, platform, project) {
	return ARTIFACTS_BASE_URL + slot + '/' + build_id
		+ '/summaries.' + platform + '/' + project + '/html';
}

jQuery.fn.lbSlotTable = function(data) {
	var tab = $('<table class="summary" border="1"/>');
	// header
	var hdr = $('<tr class="slot-header"/>');
	hdr.append('<th>Project</th><th>Version</th>');
	$.each(data.value.platforms, function(idx, val) {
		hdr.append('<th platform="' + val + '" nowrap>' + val + '<div/></th>');
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
				 *            "build": {"warnings": 0, "errors": 0}},
				 * {"key": ["slot", build_id, "platform"],
				 *  "value": {"project": "Gaudi",
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
						var b = summ.find('.build');
						b.html('<a href="'
								+ buildURL(key[0], key[1], key[2], value.project)
								+ '">build</a>');
						if (value.build.errors) {
							b.addClass('failure').append(' (' + value.build.errors + ')');
						} else if (value.build.warnings) {
							b.addClass('warning').append(' (' + value.build.warnings + ')');
						} else {
							b.addClass('success');
						}
					}
					if (value.tests) {
						var t = summ.find('.tests');
						t.html('<a href="'
								+ testsURL(key[0], key[1], key[2], value.project)
								+ '">tests</a>');
						if (value.tests.failed) {
							t.addClass('failure').append(' (' + value.tests.failed + ')');
						} else if (!value.tests.total) {
							t.addClass('warning').append(' (0)');
						} else {
							t.addClass('success');
						}
					}
				} else if (value.type == 'job-start') {
					// FIXME: simplify the selector
					var h = $('div[slot="' + key[0] + '"][build_id="' + key[1] + '"]'
			                 + ' tr.slot-header'
				             + ' th[platform="' + key[2] + '"] div');
					if (! h.text()) {
						h.text('started: ' + moment(value.started).format('H:mm:ss'));
					}
				} else if (value.type == 'job-end') {
					// FIXME: simplify the selector
					var h = $('div[slot="' + key[0] + '"][build_id="' + key[1] + '"]'
			                 + ' tr.slot-header'
				             + ' th[platform="' + key[2] + '"] div');
					h.text('ended: ' + moment(value.completed).format('H:mm:ss'));
				}
			});
		});
	});
	return this;
}

jQuery.fn.loadButton = function () {
	return this.button({label: "show"})
	.click(function () {
		var day = moment($(this).attr('day'));
		var next = moment(day).add('days', 1).format('YYYY-MM-DD');
		day = day.format('YYYY-MM-DD');

		$(this).unbind('click').button("disable");
		$('img[day="' + day + '"]').show();
		var jqXHR = $.ajax({dataType: "json",
			url: '_view/slots',
			data: {'startkey': JSON.stringify([day]),
				'endkey': JSON.stringify([next])}});
		jqXHR.day = day;
		jqXHR.done(function(data, textStatus, jqXHR) {
			var el = $('.day[day="' + jqXHR.day + '"] div.slots');
			if (data.rows.length) {
				$.each(data.rows, function(idx, row){
					var slot = $('<div class="slot" slot="' + row.key[1]
					+ '" build_id="' + row.value.build_id + '"/>');
					slot.append($('<h4/>').append(row.key[1] + ': ' + row.value.description));
					el.append(slot);
					slot.lbSlotTable(row);
				});
			} else {
				el.text('no data for this day');
			}
			el.show();
			$('img[day="' + jqXHR.day + '"]').hide();
			$('button[day="' + jqXHR.day + '"]').hideButton().button("enable");
		});
	});
}

jQuery.fn.hideButton = function () {
	return this.button({label: "hide"})
	.click(function() {
		var day = $(this).attr("day");
		$('.day[day="' + day + '"] div.slots').hide();
		$(this).showButton();
	});
}

jQuery.fn.showButton = function () {
	return this.button({label: "show"})
	.click(function() {
		var day = $(this).attr("day");
		$('.day[day="' + day + '"] div.slots').show();
		$(this).hideButton();
	});
}

// fill an element with one <div> per slot build for the given day
jQuery.fn.lbNightly = function () {
	return this.each(function(){
		var day = moment($(this).attr('day'));
		var btn = $('<button day="' + day.format('YYYY-MM-DD') + '">show</button>')
		.loadButton();

		$(this).append($('<div class="header"/>')
				.append($('<span/>').append(btn))
				.append('<span class="day-name"> ' + day.format('dddd') + ' </span>')
				.append($('<img day="' + day.format('YYYY-MM-DD') + '" src="images/ajax-loader.gif" text="loading...">').hide())
				)
			.append($('<div class="slots"/>').hide());
		if ($(this).hasClass("enabled"))
			btn.click();
	});
}

$(function(){
	// prepare the dialog data
	$('#filter-dialog input[name="enabled_days"]').val(enabled_days);
	$('#all_days').button().click(function() {
		$('#filter-dialog input:checkbox[name="enabled_days"]').prop("checked", true);
	});
	$('#no_days').button().click(function() {
		$('#filter-dialog input:checkbox[name="enabled_days"]').prop("checked", false);
	});
	$("#filter-dialog").dialog({
		autoOpen: false,
		modal: true,
		buttons: {
	        OK: function() {
	        	var values = [];
	        	$('#filter-dialog input:checkbox[name="enabled_days"]:checked')
	        	.each(function (idx, el) { values.push($(el).val()); });
	        	enabled_days = values;
	        	$.cookie("enabled_days", JSON.stringify(enabled_days));

	        	var today = moment().format('dddd');
        		var yesterday = moment().subtract('days', 1).format('dddd');

        		$('div.day div.header button').each(function(){
        			var btn = $(this);
        			var day = moment(btn.attr('day')).format('dddd');
        			if ($.inArray(day, enabled_days) >= 0
        					|| (day == today && $.inArray('Today', enabled_days) >= 0)
        					|| (day == yesterday && $.inArray('Yesterday', enabled_days) >= 0)) {
        				if (btn.button('option', 'label') == 'show')
        					btn.click();
        			} else {
        				if (btn.button('option', 'label') == 'hide')
        					btn.click()
        			}
        		});
	        	$(this).dialog("close");
	        },
	        Cancel: function() {
	        	$(this).dialog("close");
	        }
		}
	});

	$("#set-filter")
    	.button()
    	.click(function() {
    		$("#filter-dialog").dialog("open");
    });

	// Prepare day tables
	var today = moment();
	for(var day = 0; day < 7; day++) {
		var d = moment(today).subtract('days', day);
		var e = "disabled";
		if (day == 0 && $.inArray('Today', enabled_days) >= 0) {
			e = "enabled";
		} else if (day == 1 && $.inArray('Yesterday', enabled_days) >= 0) {
			e = "enabled";
		} else if ($.inArray(d.format('dddd'), enabled_days) >= 0) {
			e = "enabled";
		}
		$('#middle').append('<div class="day ' + e + '" day="' + d.format('YYYY-MM-DD') + '"/>');
	}

	$('.day').lbNightly();
});
