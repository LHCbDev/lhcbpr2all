var ARTIFACTS_BASE_URL = 'https://buildlhcb.cern.ch/artifacts/';
var JENKINS_JOB_URL = 'https://buildlhcb.cern.ch/jenkins/job/nightly-slot-build-platform/';
var HOST_MONITOR_PREFIX = 'https://meter.cern.ch/public/_plugin/kibana/#/dashboard/elasticsearch/Metrics:%20Host?query=@fields.entity:';
var MAX_BUILD_IDLE_TIME = 180; // minutes
var FILTER_DEFAULT = {
    days: ["Today"],
    slots: [],
    projects: []
};

// special artifacts locations
var flavour = /:\/\/[^/]+\/(nightlies-)?([^/]+)\//.exec(window.location);
if (!flavour || flavour[2] == 'nightlies') {
    flavour = 'nightly';
} else {
    flavour = flavour[2];
}
ARTIFACTS_BASE_URL = ARTIFACTS_BASE_URL + flavour + "/";
if (flavour == 'testing') {
    // special url for testing slots
    JENKINS_JOB_URL = 'https://buildlhcb.cern.ch/jenkins/job/nightly-test-slot-build-platform/'
}

function getParameterByName(name) {
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}

var REQUESTED_SLOT = getParameterByName("slot");
var REQUESTED_PROJECT = getParameterByName("project");
var REQUESTED_DAY = getParameterByName("day");
var REQUESTED_BUILD_ID = getParameterByName("build_id");

if (flavour == 'release')
    REQUESTED_SLOT = 'lhcb-release';

// variables set from cookies
if (!$.cookie("filters")) {
    $.cookie("filters", JSON.stringify(FILTER_DEFAULT));
}
var filters = JSON.parse($.cookie("filters"));

function checkoutURL(slot, build_id, project) {
    return ARTIFACTS_BASE_URL + slot + '/' + build_id + '/' + project + '.checkout.log.html';
}

function buildURL(slot, build_id, platform, project) {
    return ARTIFACTS_BASE_URL + slot + '/' + build_id + '/summaries.' + platform + '/' + project + '/build_log.html';
}

function testsURL(slot, build_id, platform, project) {
    return ARTIFACTS_BASE_URL + slot + '/' + build_id + '/summaries.' + platform + '/' + project + '/html';
}

function spinInit(spinkey) {
    var spin = $('<img id="spinner-' + spinkey + '" src="images/ajax-loader.gif" title="loading...">');
    spin.data('count', 0);
    spin.hide();
    return spin;
}

function spinIncrease(spinkey) {
    if (!spinkey) return;
    var spin = $('#spinner-' + spinkey);
    var count = spin.data('count');
    spin.data('count', count + 1);
    spin.show();
}

function spinDecrease(spinkey) {
    if (!spinkey) return;
    var spin = $('#spinner-' + spinkey);
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

function hostMonitorLink(hostname) {
    var host = hostname.replace(/\..*/,'');
    return $('<a href="' + HOST_MONITOR_PREFIX + host + '" target="_blank">')
        .append('<img src="images/kibana_16.png" alt="Lemon stats" ' +
            'title="Stats for ' + host + '"/>').tooltip();
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
    $('#confirm-build-info > tbody:last').append('<table><tr><td>Build System: <b>' + data.build_tool + '</b></td></tr></table>');
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
    }).text('Rebuild');
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

jQuery.fn.lbSlotTable = function(value, spinkey) {
    var tab = $('<table class="summary" border="1"/>');
    // header
    var hdr = $('<tr class="slot-header"/>');
    hdr.append('<th>Project</th><th>Version</th>');
    $.each(value.platforms, function(idx, val) {
        hdr.append('<th platform="' + val + '" nowrap>' +
            val + '<div class="slot-info"/></th>');
    });
    tab.append(hdr);

    // rows
    $.each(value.projects, function(idx, val) {
        var proj_name = val.name;
        if (!val.disabled) {
            proj_name = '<a href="' +
                checkoutURL(value.slot, value.build_id, val.name) +
                '" title="show checkout log" target="_blank">' + val.name + '</a>';
        }
        var proj_vers = val.version;
        if (proj_vers == 'None') {
            proj_vers = '-';
        }
        var tr = $('<tr project="' + val.name + '"/>')
            .append('<th>' + proj_name + '</th><th>' + proj_vers + '</th>');
        if (val.disabled) {
            tr.addClass('disabled');
        }

        if (!value.platforms && value.default_platforms) {
            value.platforms = value.default_platforms;
        }
        var proj_no_test = (value.no_test || val.no_test);
        $.each(value.platforms, function(idx, val) {
            tr.append('<td platform="' + val + '">' +
                '<table class="results"><tr>' +
                '<td class="build">&nbsp;</td><td class="tests' +
                ((proj_no_test) ? " disabled" : "") +
                '"/></tr></table>');
        });
        if (! isProjectRequested(val.name)) {
            tr.hide();
        }
        tab.append(tr);
    });
    this.append(tab);

    // trigger load of the results of each platform
    $.each(value.platforms, function(idx, val) {
        var query = {
            'key': JSON.stringify([value.slot, value.build_id, val])
        };
        spinIncrease(spinkey);

        var jqXHR = $.ajax({
            dataType: "json",
            url: '_view/summaries',
            data: query
        });
        jqXHR.spinkey = spinkey;
        jqXHR.key = [value.slot, value.build_id, val];
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
                        if (value.completed) {
                            b.html('<a href="' + buildURL(key[0], key[1], key[2], value.project) + '" target="_blank">build</a>');
                            if (value.build.errors) {
                                b.addClass('failure').append(' (' + value.build.errors + ')');
                            } else if (value.build.warnings) {
                                b.addClass('warning').append(' (' + value.build.warnings + ')');
                            } else {
                                b.addClass('success');
                            }
                        } else {
                            if (value.started) {
                                b.html((value.build_url) ?
                                        ('<a href="' + value.build_url + '/console" target="_blank">running</a>') :
                                        'running');
                            }
                        }
                    }
                    if (value.tests) {
                        var t = summ.find('.tests');
                        if (value.completed) {
                            t.html('<a href="' + testsURL(key[0], key[1], key[2], value.project) + '" target="_blank">tests</a>');
                            if (value.tests.failed) {
                                t.addClass('failure').append(' (' + value.tests.failed + ')');
                            } else if (!value.tests.total) {
                                t.addClass('warning').append(' (0)');
                            } else {
                                t.addClass('success');
                            }
                        } else {
                            if (value.started) {
                                t.html((value.build_url) ?
                                        ('<a href="' + value.build_url + '/console" target="_blank">running</a>') :
                                        'running');
                            }
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
                            .append(hostMonitorLink(value.host));
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
            spinDecrease(jqXHR.spinkey);
        });
    });
    return this;
}

function slotBlock(data) {
    var isRelease = flavour == 'release';

    var build_tool_logo = "";
    if (data.build_tool) {
        build_tool_logo = '<img class="build-logo" src="images/' + data.build_tool + '.png"/> ';
    }

    var title = isRelease ? ("Release build " + data.build_id) : data.slot;
    title += data.date ? (" (" + data.date + ")") : "";

    var header = '<table><tr><td nowrap>' + build_tool_logo +
        '<a class="permalink" title="Permalink to slot ' + data.slot + ', build ' + data.build_id +
        '" href="?slot=' + data.slot + '&build_id=' + data.build_id + '">' +
        title + '</a>' + (isRelease ? '' : ':') +
        '</td><td>';
    if (isRelease) {
        header += '<button id="'+ data.build_id + '"class="rebuild-button"/>';
        header += '<a href="' + ARTIFACTS_BASE_URL + 'lhcb-release/' + data.build_id +
                  '" target="_blank"><img class="rpm" src="images/graphix-folder_283x283.png" title="artifacts directory"></a>';
    } else {
        header += data.description;
    }
    header += '</td></tr></table>';

    var slot = $('<div class="slot" slot="' + data.slot + '" build_id="' + data.build_id + '"/>');
    slot.append($('<h4/>').append('<span class="alerts"/> ')
        .append(header));
    return slot;
}

jQuery.fn.loadButton = function() {
    return this.button({
        label: "show"
    })
        .click(function() {
            var day = $(this).attr('day');

            $(this).unbind('click').button("disable");
            spinIncrease(day);
            var jqXHR = $.ajax({
                dataType: "json",
                url: '_view/slotsByDay',
                data: {
                    'key': JSON.stringify(day)
                }
            });
            jqXHR.day = day;
            jqXHR.done(function(data, textStatus, jqXHR) {
                var el = $('.day[day="' + jqXHR.day + '"] div.slots');
                if (data.rows.length) {
                    $.each(data.rows, function(idx, row) {
                        var slot = slotBlock(row.value);
                        el.append(slot);

                        // do show/load only non-hidden slots
                        if (! isSlotRequested(row.value.slot)) {
                            slot.append($('<p>Data for this slot not loaded. </p>')
                                .append('<a href="' + window.location.href + '">Reload the page</a>'));
                            slot.hide();
                        } else {
                            slot.lbSlotTable(row.value, row.key);
                            slot.find('.alerts').lbSlotDiskSpace();
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

jQuery.fn.hideButton = function() {
    return this.button({
        label: "hide"
    })
        .click(function() {
            var day = $(this).attr("day");
            $('.day[day="' + day + '"] div.slots').hide();
            $(this).showButton();
        });
}

jQuery.fn.showButton = function() {
    return this.button({
        label: "show"
    })
        .click(function() {
            var day = $(this).attr("day");
            $('.day[day="' + day + '"] div.slots').show();
            $(this).hideButton();
        });
}

// fill an element with one <div> per slot build for the given day
jQuery.fn.lbNightly = function() {
    return this.each(function() {
        var day = $(this).attr('day');
        var mday = moment(day);
        var dayName = mday.format('dddd');
        var dayTitle = dayName;
        if (mday < moment().subtract(7, 'days'))
            dayTitle = mday.format('dddd YYYY-MM-DD');
        var btn = $('<button day="' + day + '">show</button>')
            .loadButton();
        if (REQUESTED_DAY) btn.hide();

        var spin = spinInit(day);


        $(this).append($('<table class="header"/>')
            .append($('<tr/>')
                .append($('<td class="button"/>').append(btn))
                .append($('<td class="spinner"/>').append(spin))
                .append($('<td class="day-name"><a class="permalink" title="Permalink to this day" href="?day=' + day + '">' + dayTitle + '</a></td>'))))
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
var yesterdayName = moment().subtract(1, 'days').format('dddd');

function isDayEnabled(dayName) {
    return (REQUESTED_DAY ||
            ($.inArray(dayName, filters.days) >= 0 ||
                    (dayName == todayName && $.inArray('Today', filters.days) >= 0) ||
                    (dayName == yesterdayName && $.inArray('Yesterday', filters.days) >= 0)));
}


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

function isSlotRequested(s) {
    if (REQUESTED_SLOT) {
        return s == REQUESTED_SLOT;
    }
    return $.inArray(s, filters.slots) < 0;
}

function isProjectRequested(p) {
    if (REQUESTED_PROJECT) {
        return p == REQUESTED_PROJECT;
    }
    return $.inArray(p, filters.projects) < 0;
}

function applyFilters() {
    $('div.day table.header button').each(function() {
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

    $('div.slot').each(function() {
        var el = $(this);
        var s = el.attr("slot")
        if (s && isSlotRequested(s)) {
            el.show();
        } else {
            el.hide();
        }
    });

    $('tr[project]').each(function() {
        var el = $(this);
        if (isProjectRequested(el.attr('project'))) {
            el.show();
        } else {
            el.hide();
        }
    });

    $.cookie("filters", JSON.stringify(filters), {
        expires: 365
    });
}

function prepareFilterDialog() {
    // prepare the dialog data

    if (flavour != 'release') {
        // the list of days is known, the others are retrieved
        $('#filter-dialog-days').attr("loaded", "true")
        initFilterCheckboxes('days');
    }

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
    if (flavour != 'release')
        $('#filter-dialog-slots > table').hide();
    $('#filter-dialog-projects > table').hide();

    // initialize dialog
    $("#filter-dialog").dialog({
        autoOpen: false,
        modal: true,
        buttons: {
            OK: function() {
                if (flavour != 'release') {
                    getFilterCheckboxes('days');
                    getFilterCheckboxes('slots');
                }
                getFilterCheckboxes('projects');

                applyFilters();

                $(this).dialog("close");
            },
            Cancel: function() {
                // restore previous settings
                if (flavour != 'release') {
                    initFilterCheckboxes('days');
                    initFilterCheckboxes('slots');
                }
                initFilterCheckboxes('projects');
                $(this).dialog("close");
            },
            Defaults: function() {
                // restore default settings
                filters = FILTER_DEFAULT;
                applyFilters();

                if (flavour != 'release') {
                    initFilterCheckboxes('days');
                    initFilterCheckboxes('slots');
                }
                initFilterCheckboxes('projects');
                $(this).dialog("close");
            }
        }
    });

    $("#set-filter")
        .button()
        .click(function() {
            if (flavour != 'release') fillDialogTab('slots');
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
}

$(function() {
    $('#banner h1').text('LHCb ' + flavour[0].toUpperCase() + flavour.slice(1) + ' Builds');
    var top_links = [['https://buildlhcb.cern.ch/jenkins/follow-builds-status', 'Jenkins Status'],
                     ['https://cern.ch/lhcb-nightlies/cgi-bin/overview_nightlies.py', 'Configuration overview'],
                     ['https://cern.ch/lhcb-nightlies/editor.html', 'Configuration editor'],
                     ['https://svnweb.cern.ch/trac/lhcb/browser/LHCbNightlyConf/trunk/configuration.xml', 'Configuration (SVN)'],
                     ['https://lhcb-coverity.cern.ch:8443', 'LHCb Coverity'],
                     ['https://its.cern.ch/jira/secure/CreateIssueDetails!init.jspa?pid=11500&amp;components=11303&amp;issuetype=1' ,'Report a bug']
                    ];
    if (flavour == 'release') {
        top_links = [['https://twiki.cern.ch/twiki/bin/view/LHCb/ProjectRelease', 'Project Deployment Instructions'],
                     ['https://sft.its.cern.ch/jira/browse/LHCBDEP', 'LHCb Deployment (JIRA)'],
                     ['https://buildlhcb.cern.ch/jenkins/plugin/follow-builds-status/filter?selectedView=release', 'Jenkins Status'],
                     ['https://buildlhcb.cern.ch/jenkins/job/lhcb-release/build', 'Manually Start lhcb-release'],
                     ['https://its.cern.ch/jira/secure/CreateIssueDetails!init.jspa?pid=11500&amp;components=11303&amp;issuetype=1' ,'Report a bug']
                    ];
    }
    var toolbar = $('#links ul');
    $.each(top_links, function(idx, link_data){
        toolbar.append('<li><a href="' + link_data[0] + '" target="_blank">' + link_data[1] + '</a>');
    });

    if (REQUESTED_DAY || REQUESTED_SLOT || REQUESTED_PROJECT) {
        // when there is a specific selection we filters do not make sense...
        $("#toolbar").hide();
        // ... and we need a link to the full page
        $('#banner > h1').wrapInner('<a href="index.html"/>');
    } else {
        prepareFilterDialog();
        prepareRssForm();
    }

    // Prepare day tables
    if (REQUESTED_DAY) {
        var d = moment(REQUESTED_DAY);
        $('#summaries').append('<div class="day" ' +
                'day="' + d.format('YYYY-MM-DD') + '"' +
                'day_id="' + d.format('ddd') + '"/>');
    } else if (REQUESTED_SLOT && REQUESTED_BUILD_ID) {
        $.ajax({url:'_view/docsBySlotBuild',
                data: {'key': JSON.stringify([REQUESTED_SLOT, parseInt(REQUESTED_BUILD_ID)]),
                       'include_docs': 'true'},
                dataType: "json"})
            .done(function(data) {
                var slots = $('<div class="slots"/>')
                $('#summaries').append(slots);
                if (data.rows.length) {
                    var value = data.rows[0].doc;
                    var slot = slotBlock(value);
                    slots.append(slot);
                    slot.lbSlotTable(value, null);
                    slot.find('button.rebuild-button').rebuild_btn(value);
                } else {
                    slots.append("Cannot find build " + REQUESTED_BUILD_ID +
                                 " for slot " + REQUESTED_SLOT);
                }
            });
    } else if (flavour == 'release') {
        var today = moment();
        var day = moment(today).subtract('days', 7); // we get builds for the last 7 days

        $.ajax({url:'_view/slotsByDay',
            data: {'startkey': JSON.stringify(day.format("YYYY-MM-DD"))},
            dataType: "json"})
        .done(function(data) {
            var slots = $('<div class="slots"/>')
            $('#summaries').append(slots);
            if (data.rows.length) {
                data.rows.sort(function(row1, row2){
                    return row2.value.build_id - row1.value.build_id;
                });
                $.each(data.rows, function(idx, row) {
                    row.value.date = row.key;
                    var slot = slotBlock(row.value);
                    slots.append(slot);
                    slot.lbSlotTable(row.value, null);
                    slot.find('.alerts').lbSlotDiskSpace();
                    slot.find('button.rebuild-button').rebuild_btn(row.value);
                });
            } else {
                slots.append("No " + REQUESTED_SLOT + " builds since " +
                        day.fromNow());
            }
        });
    } else {
        var today = moment();
        for (var day = 0; day < 7; day++) {
            var d = moment(today).subtract('days', day);
            $('#summaries').append('<div class="day" ' +
                'day="' + d.format('YYYY-MM-DD') + '"' +
                'day_id="' + d.format('ddd') + '"/>');
        }
    }
    $('.day').lbNightly();
});
