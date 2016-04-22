function(head, req) {
    // server URLs (default values)
    var baseUrl = 'https://lhcb-nightlies.cern.ch/';

    var rssServerLocation;

    var flavour = /\/nightlies-([^/]+)\//.exec('/' + req.path.join("/") +'/');
    flavour = flavour ? flavour[1] : 'nightly';
    rssServerLocation = baseUrl + flavour + '/';

    var numberpattern = new RegExp("(^100$|^[1-9][0-9]$|^[1-9]$)");
    // parsing the http request
    var args = req["query"];
    var alertlevel = args["minfreespacepercentage"] || "100"; // alert level error only, errors and warnings or all. possible value : ["error","warnings",undefined]

    //number of day considered
    var daynumber = 1;
    var daylimit = daynumber * 86400000; // conversion en milisecond

    // input protection
    if (numberpattern.test(alertlevel)) {
        alertlevel = eval(alertlevel);
    } else {
        throw (['error', 'Bad Request', 'reason : Invalid argument for : minfreespacepercentage']);
    }

    row = getRow();

    if (!row) {
        send('<?xml version="1.0" encoding="iso-8859-1"?><rss version="2.0"><channel><title>Disk space news</title><description>There is no disk space data in the database. If this problem perist, please contact the webmaster</description><link>');
        send(rssServerLocation);
        if (args) {
            send("?");
            var arglist = [];
            for (var val in req["query"]) {
                arglist.push(val + "=" + args[val]);
            }
            send(encodeURIComponent(arglist.join(";")));

        }
        send('</link>');
    } else {
        send('<?xml version="1.0" encoding="iso-8859-1"?><rss version="2.0"><channel><title>Disk space news</title><description>Disk space available of the nightlies slots.</description><lastBuildDate>');
        send(row.value["date"]);
        send('</lastBuildDate><link>');
        send(rssServerLocation);
        if (args) {
            send("?");
            var arglist = [];
            for (var val in req["query"]) {
                arglist.push(val + "=" + args[val]);
            }
            send(encodeURIComponent(arglist.join(";")));

        }
        send('</link>');
        var startDate = new Date(row.value["date"]);


        do {
            var date = new Date(row.value["date"]);
            var WNbJours = startDate.getTime() - date.getTime();
            if (WNbJours > daylimit) {
                break;
            }

            var data = row.value;

            var btotal = data["blocks"];
            var bavailable = data["bavail"];
            var quot = 0;
            if (btotal != 0) {
                quot = bavailable * 100 / btotal;
            }

            if (quot > alertlevel) {
                continue;
            }

            // process the dis-usage doc
            send('<item><title>');
            send("disk-space " + data["slot"] + " : " + quot + "%");
            send('</title><description>');
            send(" Block : " + data["blocks"] + " Blocks Available : " + data["bavail"] + " Block Size : " + data["bsize"] + " Path : " + data["path"]);
            send('</description><pubDate>');
            send(data["date"]);
            send('</pubDate><guid isPermaLink="false">');
            send(data["slot"] + "diskspace" + row.key);
            send('</guid></item>');

        } while (row = getRow());

    }

    send('</channel></rss>');

}
