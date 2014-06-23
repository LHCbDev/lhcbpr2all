function(head, req) {
    // server URLs (default values)
	var baseUrl = 'https://buildlhcb.cern.ch/';

    var rssServerLocation;
    var resultServerLocation;

    var flavour = /\/nightlies-([^/]+)\//.exec('/' + req.path.join("/") +'/');
    if (flavour) {
        rssServerLocation = baseUrl + 'nightlies-' + flavour[1] + '/';
        resultServerLocation = baseUrl + 'artifacts/' + flavour[1] + '/';
    } else {
        rssServerLocation = baseUrl + 'nightlies/';
        resultServerLocation = baseUrl + 'artifacts/';
    }

    //protecting regex
    var listValidPatern = new RegExp("^([a-zA-Z0-9\-_]+,)*[a-zA-Z0-9\-_]+$");
    var regexValidPattern = /^[a-z0-9A-Z\[\]\|\(\)\\_\.\$\^\{\}\?\+\*\-\!\=\.\,(u\[0-9\]+)(o\[0-8\])(x\[0-9a-f\]+)(\\w)(\\W)(\\d)(\\D)(\\s)(\\S)(\\b)(\\B)(\\0)(\\n)(\\f)(\\r)(\\t)(\\v)]+$/;

    //number of day considered
    var daynumber = 1;
    var daylimit = daynumber * 86400000; // conversion en milisecond

    // parsing the http request
    var args = req["query"];

    var projectlist = args["projectlist"] || "all"; //project name or nothing for all
    var platformlist = args["platformlist"] || "all"; //platform name TODO regexp
    var nature = args["nature"] || "all"; // build only, test only or all possible value : ["build","tests",undefined]
    var alertlevel = args["alertlevel"] || "0"; // alert level error only, errors and warnings or all. possible value : {2,1,undefined / 0]["error","warnings",undefined]
    var slotlist = args["slotlist"] || "all";
    var slotpattern = args["slotpattern"] || 'false';
    var projectpattern = args["projectpattern"] || 'false';
    var platformpattern = args["platformpattern"] || 'false';

    //input decoding
    slotpattern = decodeURIComponent(slotpattern);
    projectpattern = decodeURIComponent(projectpattern);
    platformpattern = decodeURIComponent(platformpattern);

    // input protection
    //slot
    if (!regexValidPattern.test(slotpattern)) {
        throw (['error', 'Bad Request', 'reason : Invalid argument for : slotpattern']);
    } else if (slotpattern != 'false') {
        slotregex = new RegExp(slotpattern);
        slotlist = ["all"];
    } else {
        slotregex = new RegExp(".*");
        if (listValidPatern.test(slotlist)) {

            slotlist = slotlist.split(",");

        } else {
            throw (['error', 'Bad Request', 'reason : Invalid argument for : slotlist']);
        }
    }

    // project
    if (!regexValidPattern.test(projectpattern)) {
        throw (['error', 'Bad Request', 'reason : Invalid argument for : projectpattern']);
    } else if (projectpattern != 'false') {
        projectregex = new RegExp(projectpattern);
        projectlist = ["all"];
    } else {
        projectregex = new RegExp(".*");
        if (listValidPatern.test(projectlist)) {

            projectlist = projectlist.split(",");

        } else {
            throw (['error', 'Bad Request', 'reason : Invalid argument for : projectlist']);
        }

    }
    //platform
    if (!regexValidPattern.test(platformpattern)) {
        throw (['error', 'Bad Request', 'reason : Invalid argument for : platformpattern']);
    } else if (platformpattern != 'false') {
        platformregex = new RegExp(platformpattern);
        platformlist = ["all"];
    } else {
        platformregex = new RegExp(".*");
        if (listValidPatern.test(platformlist)) {

            platformlist = platformlist.split(",");

        } else {
            throw (['error', 'Bad Request', 'reason : Invalid argument for : platformlist']);
        }
    }

    if (nature != "build" && nature != "tests" && nature != "all") {

        throw (['error', 'Bad Request', 'reason : Invalid argument for : nature']);
    }
    if (alertlevel == "0" || alertlevel == "1" || alertlevel == "2") {
        alertlevel = eval(alertlevel);
    } else {
        throw (['error', 'Bad Request', 'reason : Invalid argument for : alertlevel']);
    }

    // initialisation
    row = getRow();
    if (!row) {
        send('<?xml version="1.0" encoding="iso-8859-1"?><rss version="2.0"><channel><title>Results</title><description>There is no recent activity of this feed</description><link>');
        send(rssServerLocation);
        send('</link>');
    } else {
        var startDate = new Date(row.value["date"]);
        send('<?xml version="1.0" encoding="iso-8859-1"?><rss version="2.0"><channel><title>Results</title><description>Test and Build results of the nightly builds.</description><lastBuildDate>');
        send(row.value["date"]);
        send('</lastBuildDate><link>');
        send(rssServerLocation);
        send('</link>');

        // add  items
        do {
            // verify the date and breck the loop if there are more than "daynumber" days between the first and this item
            var date = new Date(row.value["date"]);
            var WNbJours = startDate.getTime() - date.getTime();
            if (WNbJours > daylimit) {
                break;
            }

            var data = row.value;
            var datanature = "tests";
            var datanature2 = "TEST";
            if (data["build"]) {
                datanature = "build";
                datanature2 = "BUILD";
            }

            var warning = "PASS";
            var alert = 0;
            if (datanature == "tests") {
                wrong = data[datanature]["failed"];
                if (wrong > 0) {
                    warning = "FAIL";
                    alert = 2;
                }
            } else if (datanature == "build") {
                wrong = data[datanature]["errors"];
                var wrong2 = data[datanature]["warnings"];
                if (wrong2 > 0) {
                    warning = "WARNINGS";
                    alert = 1;
                }
                if (wrong > 0) {
                    warning = "ERROR";
                    alert = 2;
                }
            }

            // filter
            if (((slotlist.indexOf(data["slot"]) == -1 && slotlist.indexOf("all") == -1) || (projectlist.indexOf(data["project"]) == -1 && projectlist.indexOf("all") == -1) || (platformlist.indexOf(data["platform"]) == -1 && platformlist.indexOf("all") == -1) || (!slotregex.test(data["slot"])) || (!platformregex.test(data["platform"])) || (!projectregex.test(data["project"])) || (datanature != nature && nature != "all") || (alertlevel != 0 && (alert < alertlevel)))) {
                continue;
            }



            //process builds and tests docs

            send('<item><title>');
            send("[" + warning + "-" + datanature2 + "] " + data["slot"] + "  " + data["project"] + "  " + data["platform"]);
            send('</title><description>');
            send(warning);
            for (var val in data[datanature]) {
                send(" ");
                send(val);
                send(" : ");
                send(data[datanature][val]);
            }
            send('</description><pubDate>');
            send(data["date"]);
            send('</pubDate><link>');
            send(encodeURI(resultServerLocation + data["slot"] + "/" + data["build_id"] + "/summaries." + data["platform"] + "/" + data["project"] + "/"));
            if (datanature == "tests") {
                send("html/");
            } else {
                send("build_log.html");
            }
            send('</link><guid isPermaLink="false">');
            send(data["slot"] + "_" + data["project"] + "_" + data["platform"] + "_" + datanature + row.key);
            send('</guid></item>');

            // continue until there is no more row
        } while (row = getRow());

    }

    send('</channel></rss>');

}
