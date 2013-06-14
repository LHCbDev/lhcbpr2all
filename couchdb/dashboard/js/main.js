var ARTIFACTS_BASE_URL = 'http://buildlhcb.cern.ch/artifacts/';
var JENKINS_JOB_URL = 'https://buildlhcb.cern.ch/jenkins/job/nightly-slot-build-platform/';
var LEMON_SEARCH_PREFIX = 'https://lemon.cern.ch/lemon-web/index.php?target=process_search&amp;fb=';
var MAX_BUILD_IDLE_TIME = 180; // minutes

// variables set from cookies
if (!$.cookie("filters")) {
	$.cookie("filters",
			JSON.stringify({
				days: ["Today"],
				slots: [],
				projects: []
			}));
}
var filters = JSON.parse($.cookie("filters"));


function buildURL(slot, build_id, platform, project) {
	return ARTIFACTS_BASE_URL + slot + '/' + build_id
		+ '/summaries.' + platform + '/' + project + '/build_log.html';
}

function testsURL(slot, build_id, platform, project) {
	return ARTIFACTS_BASE_URL + slot + '/' + build_id
		+ '/summaries.' + platform + '/' + project + '/html';
}

function spinInit(day) {
	var spin = $('<img id="spinner-' + day + '" src="images/ajax-loader.gif" title="loading...">');
	spin.data('count', 0);
	spin.hide();
	return spin;
}

function spinIncrease(day) {
	var spin = $('#spinner-' + day);
	var count = spin.data('count');
	spin.data('count', count + 1);
	spin.show();
}

function spinDecrease(day) {
	var spin = $('#spinner-' + day);
	var count = spin.data('count');
	count = count - 1;
	if (count <= 0) {
		count = 0;
		spin.hide();
	}
	spin.data('count', count);
}

function jenkinsIcon(build_id) {
	return $('<a href="' + JENKINS_JOB_URL + build_id + '/">')
	  .append('<img src="images/jenkins_16.png" alt="Jenkins build" ' +
			  'title="Jenkins build"/>').tooltip();
}

function lemonIcon(hostname) {
	return $('<a href="' + LEMON_SEARCH_PREFIX + hostname + '">')
	  .append('<img src="images/lemon_16.png" alt="Lemon stats" ' +
			  'title="Lemon stats for ' + hostname + '"/>').tooltip();
}

jQuery.fn.lbSlotTable = function(data) {
	var tab = $('<table class="summary" border="1"/>');
	// header
	var hdr = $('<tr class="slot-header"/>');
	hdr.append('<th>Project</th><th>Version</th>');
	$.each(data.value.platforms, function(idx, val) {
		hdr.append('<th platform="' + val + '" nowrap>' +
				   val + '<div class="slot-info"/></th>');
	});
	tab.append(hdr);

	// rows
	$.each(data.value.projects, function(idx, val) {
		var tr = $('<tr project="' + val.name + '"/>')
		   .append('<th>' + val.name + '</th><th>' + val.version + '</th>');
		if (val.disabled) {
			tr.addClass('disabled');
		}

		$.each(data.value.platforms, function(idx, val) {
			tr.append('<td platform="' + val + '">' +
					  '<table class="results"><tr>' +
					  '<td class="build"/><td class="tests"/></tr></table>');
		});
		if ($.inArray(val.name, filters.projects) >= 0) {
			tr.hide();
		}
		tab.append(tr);
	});
	this.append(tab);

	// trigger load of the results of each platform
	$.each(data.value.platforms, function(idx, val) {
		var query = {'key': JSON.stringify([data.value.slot, data.value.build_id, val])};
		spinIncrease(data.key);

		var jqXHR = $.ajax({dataType: "json",
			url: '_view/summaries',
			data: query});
		jqXHR.day = data.key;
		jqXHR.key = [data.value.slot, data.value.build_id, val];
		jqXHR.done(function(data, textStatus, jqXHR) {
			var last_update = moment('1970-01-01');
			var started = last_update;
			var running = data.rows.length > 0;
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
					if (value.completed) {
						var m = moment(value.completed);
						if (m.isAfter(last_update)) {
							last_update = m;
						}
					}
				} else if (value.type == 'job-start') {
					// FIXME: simplify the selector
					var h = $('div[slot="' + key[0] + '"][build_id="' + key[1] + '"]'
			                 + ' tr.slot-header'
				             + ' th[platform="' + key[2] + '"] div');
					started = moment(value.started);
					if (running) {
						h.text('running for ' + started.fromNow(true));
						h.append('&nbsp;')
						 .append(jenkinsIcon(value.build_number))
						 .append('&nbsp;')
						 .append(lemonIcon(value.host));
					}
					if (started.isAfter(last_update)) {
						last_update = started;
					}
				} else if (value.type == 'job-end') {
					// FIXME: simplify the selector
					var h = $('div[slot="' + key[0] + '"][build_id="' + key[1] + '"]'
			                 + ' tr.slot-header'
				             + ' th[platform="' + key[2] + '"] div');
					h.text('completed at ' + moment(value.completed).format('H:mm:ss'));
					running = false;
				}
			});
			if (running && ! last_update.isSame(started)) {
				var m = moment();
				if (m.diff(last_update, 'minutes') > MAX_BUILD_IDLE_TIME) {
					var key = jqXHR.key;
					var h = $('div[slot="' + key[0] + '"][build_id="' + key[1] + '"]'
			                 + ' tr.slot-header'
				             + ' th[platform="' + key[2] + '"]');
					h.addClass('lagging')
					 .attr('title',
						   'no update for ' + last_update.fromNow(true))
					 .tooltip();
				}
			}
			spinDecrease(jqXHR.day);
		});
	});
	return this;
}

jQuery.fn.loadButton = function () {
	return this.button({label: "show"})
	.click(function () {
		var day = $(this).attr('day');

		$(this).unbind('click').button("disable");
		spinIncrease(day);
		var jqXHR = $.ajax({dataType: "json",
			url: '_view/slotsByDay',
			data: {'key': JSON.stringify(day)}});
		jqXHR.day = day;
		jqXHR.done(function(data, textStatus, jqXHR) {
			var el = $('.day[day="' + jqXHR.day + '"] div.slots');
			if (data.rows.length) {
				$.each(data.rows, function(idx, row){
					var value = row.value;

					var slot = $('<div class="slot" slot="' + value.slot
					+ '" build_id="' + value.build_id + '"/>');
					slot.append($('<h4/>').append(value.slot + ': ' + value.description));
					el.append(slot);

					// do show/load only non-hidden slots
					if ($.inArray(value.slot, filters.slots) >= 0) {
						slot.append($('<p>Data for this slot not loaded. </p>')
								.append('<a href="' + window.location.href + '">Reload the page</a>'));
						slot.hide();
					} else {
						slot.lbSlotTable(row);
					}
				});
			} else {
				el.text('no data for this day');
			}
			el.show();
			spinDecrease(jqXHR.day);
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
		var day = $(this).attr('day');
		var dayName = moment(day).format('dddd');
		var btn = $('<button day="' + day + '">show</button>')
		.loadButton();

		var spin = spinInit(day);

		$(this).append($('<table class="header"/>')
				 .append($('<tr/>')
				   .append($('<td class="button"/>').append(btn))
				   .append($('<td class="spinner"/>').append(spin))
				   .append('<td class="day-name">' + dayName + '</td>')))
			.append($('<div class="slots"/>').hide());

		if (isDayEnabled(dayName))
			btn.click();
	});
}

function initFilterCheckboxes(tab) {
	var reverse = tab != 'days'; // days use the direct filtering
	var id = "#filter-dialog-" + tab;
	var flags = filters[tab];
	if ($(id).attr('loaded')) {
		$(id + ' input:checkbox').val(function(){
			var el = $(this);
			if ($.inArray(el.val(), flags) >= 0) {
				el.prop('checked', ! reverse);
			} else {
				el.prop('checked', reverse);
			}
			return el.val();
		});
	}
}
function getFilterCheckboxes(tab) {
	var reverse = tab != 'days'; // days use the direct filtering
	var values = [];
	$('#filter-dialog-' + tab + ' input:checkbox')
	.each(function (idx, el) {
		var el = $(this);
		var checked = el.prop('checked')
		if ((reverse && !checked) || (!reverse && checked))
			values.push(el.val());
	});
	filters[tab] = values;
}

var todayName = moment().format('dddd');
var yesterdayName = moment().subtract('days', 1).format('dddd');

function isDayEnabled(dayName) {
	return ($.inArray(dayName, filters.days) >= 0
			|| (dayName == todayName && $.inArray('Today', filters.days) >= 0)
			|| (dayName == yesterdayName && $.inArray('Yesterday', filters.days) >= 0));
}


function fillDialogTab(tab) {
	var id = "#filter-dialog-" + tab;
	if (!$(id).attr("loaded")) {
		$(id).attr("loaded", "true");

		var jqXHR = $.ajax({dataType: "json",
			url: "_view/" + tab + "Names?group=true"});
		jqXHR.tab_id = id;
		jqXHR.done(function (data, textStatus, jqXHR) {
			$(jqXHR.tab_id + ' > img').hide();

			var table = $(jqXHR.tab_id + ' > table').show();

			$.each(data.rows, function(idx, row){
				table.append('<tr><td><input type="checkbox" value="'
						+ row.key  +'">' + row.key + '</td></tr>');
			});
			initFilterCheckboxes(tab);
		});
	}
}

function prepareFilterDialog() {
	// prepare the dialog data

	// the list of days is known, the others are retrieved
	$('#filter-dialog-days').attr("loaded", "true")
	initFilterCheckboxes('days');

	// bind buttons
	$("#filter-dialog-tabs > div > table button").button().click(function() {
		var el = $(this);
		// if the button has label 'all' it checks all entries, otherwise unchecks
		var check = el.button('option', 'label') == 'all';
		// apply the check to all the checkboxes in the same div as the button
		el.parentsUntil('#filter-dialog-tabs', 'div')
		  .find('input:checkbox').prop("checked", check);
	});

	// initialize tabbed view
	$("#filter-dialog-tabs").tabs();
	$('#filter-dialog-slots > table').hide();
	$('#filter-dialog-projects > table').hide();

	// initialize dialog
	$("#filter-dialog").dialog({
		autoOpen: false,
		modal: true,
		buttons: {
	        OK: function() {
	        	getFilterCheckboxes('days');
        		getFilterCheckboxes('slots');
        		getFilterCheckboxes('projects');

        		$('div.day table.header button').each(function(){
        			var btn = $(this);
        			var day = moment(btn.attr('day')).format('dddd');
        			if (isDayEnabled(day)) {
        				if (btn.button('option', 'label') == 'show')
        					btn.click();
        			} else {
        				if (btn.button('option', 'label') == 'hide')
        					btn.click()
        			}
        		});

        		$('div.slot').each(function(){
	        		var el = $(this);
	        		var s = el.attr("slot")
	        		if (s && $.inArray(s, filters.slots) < 0) {
	        			el.show();
	        		} else {
	        			el.hide();
	        		}
	        	});

        		$('tr[project]').each(function() {
        			var el = $(this);
        			if ($.inArray(el.attr('project'), filters.projects) >= 0) {
        				el.hide();
        			} else {
        				el.show();
        			}
        		});

	        	$.cookie("filters", JSON.stringify(filters));

	        	$(this).dialog("close");
	        },
	        Cancel: function() {
	        	// restore previous settings
				initFilterCheckboxes('days');
				initFilterCheckboxes('slots');
				initFilterCheckboxes('projects');
	        	$(this).dialog("close");
	        }
		}
	});

	$("#set-filter")
    	.button()
    	.click(function() {
    		fillDialogTab('slots');
    		fillDialogTab('projects');
       		$("#filter-dialog").dialog("open");
    });
}

$(function(){
	prepareFilterDialog();

	// Prepare day tables
	var today = moment();
	for(var day = 0; day < 7; day++) {
		var d = moment(today).subtract('days', day);
		$('#middle').append('<div class="day" day="' + d.format('YYYY-MM-DD') + '"/>');
	}

	$('.day').lbNightly();
});
