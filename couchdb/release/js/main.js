var ARTIFACTS_BASE_URL = 'https://buildlhcb.cern.ch/artifacts/';
var JENKINS_JOB_URL = 'https://buildlhcb.cern.ch/jenkins/job/nightly-slot-build-platform/';
var LEMON_SEARCH_PREFIX = 'https://lemon.cern.ch/lemon-web/index.php?target=process_search&amp;fb=';
var MAX_BUILD_IDLE_TIME = 180; // minutes
var FILTER_DEFAULT = {
    days: ["Today"],
    slots: [],
    projects: []
};

// special artifacts locations
var flavour = /\/nightlies-([^/]+)\//.exec(window.location);
if (flavour)
	ARTIFACTS_BASE_URL = ARTIFACTS_BASE_URL + flavour[1] + "/";

// variables set from cookies
if (!$.cookie("filters")) {
    $.cookie("filters", JSON.stringify(FILTER_DEFAULT));
}
var filters = JSON.parse($.cookie("filters"));


function buildURL(slot, build_id, platform, project) {
    return ARTIFACTS_BASE_URL + slot + '/' + build_id + '/summaries.' + platform + '/' + project + '/build_log.html';
}

function testsURL(slot, build_id, platform, project) {
    return ARTIFACTS_BASE_URL + slot + '/' + build_id + '/summaries.' + platform + '/' + project + '/html';
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
    return $('<a href="' + JENKINS_JOB_URL + build_id + '" target="_blank"/>')
        .append('<img src="images/jenkins_16.png" alt="Jenkins build" ' +
            'title="Jenkins build"/>').tooltip();
}

function lemonIcon(hostname) {
    return $('<a href="' + LEMON_SEARCH_PREFIX + hostname + '" target="_blank">')
        .append('<img src="images/lemon_16.png" alt="Lemon stats" ' +
            'title="Lemon stats for ' + hostname + '"/>').tooltip();
}

function DelayTimeOut(data){
	return alert("Rebuild " + data  + "Started").delay(8);
}

function prepareRebuildInfo(data){

	//Transform the project and platform data to strings

	var projects = "";
	//make string of projects with spacing
	$.each(data.projects,function(idx,project){
		projects+=project.name+" "+project.version+" ";
	});
	//remove the last space
	projects = projects.substring(0, projects.length - 1);


	var platforms = "";
	//make string of platforms with spacing
	for (var platform in data.platforms){
		platform =(data.platforms[platform]).toString();
		platforms+= platform + " ";
	}
	//remove the last space
	platforms = platforms.substring(0, platforms.length - 1);

	//fill in the form for the post request
	var form = $('#rebuild_info');
	(form.find('input[name="projects_list"]')).val(projects);
	(form.find('input[name="platforms"]')).val(platforms);
	(form.find('input[name="build_tool"]')).val(data.build_tool);

	//prepare the information to display in the dialog

	var tableprojects = $('<table id=tprojects></table>');

	tableprojects.append('<tbody/>');
	tableprojects.append('<tr><td>Projects:</td><td>Version:</td></tr>');

	for(var i=0;i <data.projects.length;i++){
		tableprojects.append('<tr><td><b>'+data.projects[i].name+
		'</b></td><td><b>'+data.projects[i].version+'</b></td></tr>');
	}

	//prepare the platform information to display in the dialog

	var tableplatforms = $('<table id=tplatforms></table>');

	tableplatforms.append('<tbody/>');
	tableplatforms.append('<tr><td>Platforms:</td></tr>');

	for(var i=0;i <data.platforms.length;i++){
		tableplatforms.append('<tr><td><b>'+data.platforms[i]+'</b></td><tr>');
	}

	//fill in confirmation build info table dialog
	$('#confirm-build-info > tbody:last').append('<tr><td><b>Would you like to rebuild slot ' +
					data.build_id + ' with the following parameters?</b></td></tr>');
	$('#confirm-build-info > tbody:last').append('<br/>');
	$('#confirm-build-info > tbody:last').append(tableprojects);
	$('#confirm-build-info > tbody:last').append('<br/>');
	$('#confirm-build-info > tbody:last').append(tableplatforms);
	$('#confirm-build-info > tbody:last').append('<br/>');
	$('#confirm-build-info > tbody:last').append('<tr><td><img style="width:20px;" alt="!"'+
				'src="images/exclamation.png"/>'+
				'<i>rebuild is set to start in 60 secs</i></td></tr>');


        $('#dialog-confirm').dialog({
		autoOpen: false,
		resizable: false,
		height: 'auto',
		width: 'auto',
		modal: true,
		buttons: {
			//In case of cancel clean the dialog table
			Cancel: function() {
				$('#confirm-build-info > tbody').empty();
				$( this ).dialog( "close" );
			},
			//process to rebuild submiting the form
			"OK": function() {
				$('#confirm-build-info > tbody').empty();
				form.submit();
				$( this ).dialog( "close" );
			},
		},
		close: function(){
			$('#confirm-build-info > tbody').empty();
		}
	});

}

//when rebuild button pressed
jQuery.fn.rebuild_btn = function(data){

	return this.button().click(function(){

		prepareRebuildInfo(data);
                $('#dialog-confirm').dialog('open');
	});
}
//when View all pressed
jQuery.fn.view_all = function(){

	return this.button().click(function(){
		//reload the full slot page
		window.location.assign(window.location.origin+window.location.pathname);
	});
}


// fill an element in side a "div.day" and "div.slot" with
// an alert button in case the free disk space for that slot.day is < 10%
jQuery.fn.lbSlotDiskSpace = function() {
    return this.each(function() {
        var elem = $(this);
        var slot = elem.parents('div.slot').attr('slot');
        var day = elem.parents('div.day').attr('day_id');

        var query = {
            key: JSON.stringify([slot, day])
        };

        var jqXHR = $.ajax({
            dataType: "json",
            url: '_view/diskSpace',
            data: query
        });
        jqXHR.elem = elem;
        jqXHR.done(function(data, textStatus, jqXHR) {
            if (data.rows.length > 0) {
                var val = data.rows[0].value;
                if (val.free_ratio < 0.1) {
                    var btn = $('<button>').button({
                        icons: {
                            primary: "ui-icon-alert"
                        },
                        label: "low disk space: " +
                            Math.round(val.free / 1024 / 1024) +
                            "MB (" + Math.round(val.free_ratio * 100) + "%)",
                        text: false
                    }).tooltip();
                    jqXHR.elem.append(btn);
                }
            }
        });
    });
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
    tab.attr("id","build-"+data.value.build_id);
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
        var query = {
            'key': JSON.stringify([data.value.slot, data.value.build_id, val])
        };
        spinIncrease(data.key);

        var jqXHR = $.ajax({
            dataType: "json",
            url: '_view/summaries',
            data: query
        });
        jqXHR.day = data.key;
        jqXHR.key = [data.value.slot, data.value.build_id, val];
        jqXHR.done(function(data, textStatus, jqXHR) {
            var last_update = moment('1970-01-01');
            var started = last_update;
            var running = data.rows.length > 0;
            $.each(data.rows, function(idx, row) {
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
                    var summ = $('div[slot="' + key[0] + '"][build_id="' + key[1] + '"]' + ' tr[project="' + value.project + '"]' + ' td[platform="' + key[2] + '"]');
                    if (value.build) {
                        var b = summ.find('.build');
                        b.html('<a href="' + buildURL(key[0], key[1], key[2], value.project) + '" target="_blank">build</a>');
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
                        t.html('<a href="' + testsURL(key[0], key[1], key[2], value.project) + '" target="_blank">tests</a>');
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
                    var h = $('div[slot="' + key[0] + '"][build_id="' + key[1] + '"]' + ' tr.slot-header' + ' th[platform="' + key[2] + '"] div');
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
                    var h = $('div[slot="' + key[0] + '"][build_id="' + key[1] + '"]' + ' tr.slot-header' + ' th[platform="' + key[2] + '"] div');
                    h.text('completed at ' + moment(value.completed).format('H:mm:ss'));
                    running = false;
                }
            });
            if (running && !last_update.isSame(started)) {
                var m = moment();
                if (m.diff(last_update, 'minutes') > MAX_BUILD_IDLE_TIME) {
                    var key = jqXHR.key;
                    var h = $('div[slot="' + key[0] + '"][build_id="' + key[1] + '"]' + ' tr.slot-header' + ' th[platform="' + key[2] + '"]');
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

function initFilterCheckboxes(tab) {
    var reverse = tab != 'days'; // days use the direct filtering
    var id = "#filter-dialog-" + tab;
    var flags = filters[tab];
    if ($(id).attr('loaded')) {
        $(id + ' input:checkbox').val(function() {
            var el = $(this);
            if ($.inArray(el.val(), flags) >= 0) {
                el.prop('checked', !reverse);
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
        .each(function(idx, el) {
            var el = $(this);
            var checked = el.prop('checked')
            if ((reverse && !checked) || (!reverse && checked))
                values.push(el.val());
        });
    filters[tab] = values;
}

var todayName = moment().format('dddd');
var yesterdayName = moment().subtract('days', 1).format('dddd');

function fillDialogTab(tab) {
    var id = "#filter-dialog-" + tab;
    if (!$(id).attr("loaded")) {
        $(id).attr("loaded", "true");

        var jqXHR = $.ajax({
            dataType: "json",
            url: "_view/" + tab + "Names?group=true"
        });
        jqXHR.tab_id = id;
        jqXHR.done(function(data, textStatus, jqXHR) {
            $(jqXHR.tab_id + ' > img').hide();

            var table = $(jqXHR.tab_id + ' > table').show();

            $.each(data.rows, function(idx, row) {
                table.append('<tr><td><input type="checkbox" value="' + row.key + '">' + row.key + '</td></tr>');
            });
            initFilterCheckboxes(tab);
        });
    }
}

function prepareViewAll(){

    $('#summaries').prepend('<div><button id="viewall" class="rebuild-button ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only" role="button" aria-disabled="false">View all</button></div>');
    $('#viewall').view_all().text('View all');

}

function applyFilters() {
    $('tr[project]').each(function() {
        var el = $(this);
        if ($.inArray(el.attr('project'), filters.projects) >= 0) {
            el.hide();
        } else {
            el.show();
        }
    });

    $.cookie("filters", JSON.stringify(filters), {
        expires: 365
    });
}

function prepareFilterDialog() {
    // prepare the dialog data

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
    $('#filter-dialog-projects > table').hide();

    // initialize dialog
    $("#filter-dialog").dialog({
        autoOpen: false,
        modal: true,
        buttons: {
            OK: function() {
                getFilterCheckboxes('projects');

                applyFilters();

                $(this).dialog("close");
            },
            Cancel: function() {
                // restore previous settings
                initFilterCheckboxes('projects');
                $(this).dialog("close");
            },
            Defaults: function() {
                // restore default settings
                filters = FILTER_DEFAULT;
                applyFilters();

                initFilterCheckboxes('projects');
                $(this).dialog("close");
            }
        }
    });

    $("#set-filter")
        .button()
        .click(function() {
            fillDialogTab('projects');
            $("#filter-dialog").dialog("open");
        });
}

function prepareRssForm() {
    $("#rssform").dialog({
        autoOpen: false,
        modal: true,
        width: 0.95 * $("#container").width(),
        buttons: {
            Cancel: function() {
                // restore previous settings
                initFilterCheckboxes('days');
                initFilterCheckboxes('slots');
                initFilterCheckboxes('projects');
                $(this).dialog("close");
            }
        }
    });
    $("#open-rssform")
        .button()
        .click(function() {
            $("#rssform").dialog("open");
            refreshAccordion();
        });

    /*
	$("#rssform").css("width",0.95*$("#container").width()).hide();

	$("#rss-form-iframe").css("width",$("#container").width()).css("visibility","hidden");//.hide();


	$("#open-rssform")
	.button()
	.click(function() {

		$("#rss-form-iframe").css("width",$("#container").width()).show().css("visibility","visible");
		var rssformposition = $("#rss-form-iframe").position();
		$("#close-rssform").css("top",rssformposition.top).css("left",rssformposition.left+$("#rss-form-iframe").width()-32).show();//.css("display","block");
	});

	$("#close-rssform").click(function(){
		$("#rss-form-iframe").hide();
		$(this).hide();
	});
	*/
}
$(function() {

    prepareFilterDialog();
    prepareRssForm();

    var today = moment();
    //starting date - today
    var d = moment(today);
    //ending date -a week ago
    var e = moment(today).subtract('days',6);


    $('#summaries').append('<div class="week" ' +
            'starting_day="' + d.format('YYYY-MM-DD') + '"' +
            'ending_day="' + e.format('YYYY-MM-DD') + '"' +
            'week_id="'+ d.format('ddd')+'"/>');

    $('.week').lbWeekly();
});

jQuery.fn.lbWeekly = function(){
	return this.each(function() {

		var week = $(this).attr('starting_day');
		var startingDayName = moment(week).format('dddd');
		var endweek = $(this).attr('ending_day');
		var endingDayName = moment(endweek).format('dddd');

		var spin  = spinInit(week);

		$(this).append($('<table class="header"/>')
			.append($('<tr/>')
			.append($('<td class="spinner"/>').append(spin))
			.append('<td class="week-name"></td>')))
		.append($('<div class="slots"/>').hide());

		$(this).loadSlots();

	});

}

//compare function for week_data
function bybuild_id(a,b) {
  if (a.value.build_id < b.value.build_id)
     return 1;
  if (a.value.build_id > b.value.build_id)
     return -1;
  return 0;
}

//load slots by build id decreasing order
jQuery.fn.loadSlots = function() {
	   var somday = $(this).attr('starting_day');
	   var today = moment();
	   var el = $('.week[starting_day="' + somday + '"] div.slots');
	   var week_data = new Array();
	   var day = moment(today).subtract('days',6);
	   day = day.format("YYYY-MM-DD");

	   spinIncrease(day);
	   //for each day of the week
            var jqXHR = $.ajax({
                dataType: "json",
                url: '_view/slotsByDay',
                data: {
                      'startkey': JSON.stringify(day)
                }
            });

	    jqXHR.day = day;
	    jqXHR.done(function(data,textStatus,jqXHR){

	    week_data = data.rows;
	    //sort objects inside the week_data
	    week_data.sort(bybuild_id);

	    var specificitem = ((window.location.search).split("="))[1];

	    if(specificitem){
		var specificslot = $.grep(week_data,function(e){
			if(e.value.build_id == specificitem){

				return e;} });
		week_data = [];
		week_data.push(specificslot[0]);

		prepareViewAll();
	    }

	        //each
		if (week_data.length) {
                    $.each(week_data, function(idx, day_data) {
                        var value = day_data.value;
                        var slot = $('<div class="slot" id="build-' + value.build_id +
					'"slot="' + value.slot + '" build_id="'
					+ value.build_id + '"/>');
                        var build_tool_logo = "";
                        if (value.build_tool) {
                        	build_tool_logo = '<td><img  height="22" width="22" src="images/' + value.build_tool + '.png"/></td>';
                        }
                        slot.append($('<h4/>').append('<span class="alerts"/> ')
				.append('<table><tr><td><a href="' + window.location.origin + window.location.pathname +
				"?build=" +value.build_id + '"><img src="images/link.png" title="direct link"></a>'+
				'</td><td nowrap>Release build ' + value.build_id +
                                '</td><td>(' + day_data.key  +
                                ')</td><td><button id="'+ value.build_id + '"class="rebuild-button"/>'+
				'</td><td><a href="https://buildlhcb.cern.ch/artifacts/release/lhcb-release/' + value.build_id +
				'" target="_blank"><img id="rpm" src="images/graphix-folder_283x283.png" title="artifacts directory"></a>'+
		                '</td>' + build_tool_logo + '</tr></table>'));

				el.append(slot);

				// do show/load only non-hidden slots
				if ($.inArray(value.slot, filters.slots) >= 0) {
					slot.append($('<p>Data for this slot not loaded. </p>')
					.append('<a href="' + window.location.href + '">Reload the page</a>'));
					slot.hide();
				}
				 else {
					slot.lbSlotTable(day_data);
					slot.find('.alerts').lbSlotDiskSpace();
				}
			        //send the value on user click
				(slot.find("button.rebuild-button")).rebuild_btn(value).text('Rebuild');

                    });

                }


	});

	el.show();
	spinDecrease(jqXHR.day);

}
