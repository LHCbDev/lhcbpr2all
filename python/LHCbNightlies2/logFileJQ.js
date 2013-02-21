
foldLinks = function() {
  $(document).ready(function() {
    $(".summary ul.error").each(function(i,l) {
      var items = $(l).children();
      if (items.size() > 1) {
        items.hide();
        items.first().show();
        var lst = $(this);
        var button = $("<a/>").text("show all " + items.size() + " errors of this type").addClass("morebtn").click(function(){
          lst.children().show();
          $(this).hide();
        });
        lst.append(button);
      }
    });
    $(".summary ul.warning").each(function(i,l) {
      var items = $(l).children();
      if (items.size() > 1) {
        items.hide();
        items.first().show();
        var lst = $(this);
        var button = $("<a/>").text("show all " + items.size() + " warnings of this type").addClass("morebtn").click(function(){
          lst.children().show();
          $(this).hide();
        });
        lst.append(button);
      }
    });
  });
};

var logfilesLinksMap = {};
$.each(logfileLinks, function(i, v) { logfilesLinksMap[v.id] = v; });
var codeLinksMap = {};
$.each(codeLinks, function(i, v) { codeLinksMap[v.id] = v; });
var codeLineAnchors = {};
$.each(codeLinks, function(i, v) { codeLineAnchors["#line_" + v.line] = v.id; });

jQuery.fn.highlight = function(keep) {
  if (!keep)
    $(".highlight").removeClass("highlight");
  return this.addClass("highlight");
};

jQuery.fn.logfileLink = function(){
	this.each(function() {
		var packdata = logfilesLinksMap[$(this).attr("id")];
		if (packdata) {
			//var data = {log: logfile, f: packdata.f, l: packdata.l};
			$(this).click(function() {
				var line = $(this).data("line");
				$(this)//.removeClass('packageLink')
				.append(' <img src="http://lhcb-nightlies.web.cern.ch/lhcb-nightlies/images/ajax-loader.gif"/>').unbind("click")
				.parent().load(logfile + ".log." + packdata.id,
						line ? function() {
					window.scrollTo(0, $('#line_' + line).highlight().position().top);
				} : undefined
				);
			});
		}
	});
};

jQuery.fn.codeLink = function() {
  this.each(function() {
    var data = codeLinksMap[$(this).attr("id")];
    $(this).click(function() {
      window.scrollTo(0, $('#' + data.block).position().top);
      $("#" + data.block) // find the block to be loaded
        .data("line", data.line) // tell it which line to go to
        .click(); // trigger a click event on it
    }).attr("title", logfilesLinksMap[data.block].name);
    // ensure that when the block is expanded the error link points to the line
    // as a regular link (not a click handler)
    $("#" + data.block).click(function(){
      $("#" + data.id).unbind('click') // remove current click handler
       .attr("href", '#line_' + data.line) // make it a proper link
       .click(function(){$('#line_' + data.line).highlight()}); // highlight the requested line
    })
  });
};

// If the URL contains a reference to a line_1234 anchor,
// load what is needed.
function openAnchor() {
  if (window.location.hash) {
    // note: we use the id can be used as an anchor
    // This is a small trick: if the selector matches,
    // the highlight will work and return the selection
    // which will not be empty.
    if ($(window.location.hash).highlight().size() == 0) {
      // the selector didn't match: try to click on the error link
      var id = codeLineAnchors[window.location.hash];
      if (id) $("#" + id).click();
    }
  }
}

function countLinks(id, str) {
  var count = 0;
  $.each(codeLinks, function(i, entry) {
    if (entry.block == id && entry.id.match(str)) {
      count++;
    }
  });
  return count;
}

function summary(pkgLink) {
  var errors = countLinks(pkgLink.id, "error");
  var warnings = countLinks(pkgLink.id, "warning");
  var s = "";
  if ((errors + warnings) != 0) {
    s += " (";
    if (errors) s += '<span class="error">' + errors + ' errors</span>';
    if (errors != 0 && warnings != 0) s = s + ', ';
    if (warnings) s += '<span class="warning">' + warnings + ' warnings</span>';
    s += ")";
  }
  return s;
}

jQuery.fn.logfileEntries = function() {
  var selection = this;
  $.each(logfileLinks, function(i, l) {
    selection.append(
      // add the div element
      $("<div/>")
        // it's class is package, checkout or env, depending on the id
        .addClass((l.id.match("section") || l.id.match("checkout") || "env").toString())
        // add a span to the div
        .append($('<span class="packageLink"/>')
          // with the right id
          .attr("id", l.id)
          // using the description or the package name
          .html('&rarr;&nbsp;' + (l.desc || ("Package <strong>"+l.name+"</strong>"))).append(summary(l))
        )
    );
  });
  this.find(".env:first").before('<h3 id="environment">Environment:</h3>');
  this.find(".checkout:first").before('<h3 id="checkout">Checkout:</h3>');
  this.find(".section:first").before('<h3 id="build_log">Build log:</h3>');
};

// on ready
$(function(){
  // generate logfile sections
  $("#logfile").logfileEntries();

  // create links
  $('.packageLink').logfileLink();
  $('.codeLink').codeLink();
  // add an "expand all" button
  $('.section:first').before($("<p/>").append($("<a class=\"codeLink\">Expand all</a>").click(function(){
    $('.section .packageLink').click();
    $(this).hide();
  })));
  foldLinks();
  // check if we have to go to a specific line
  openAnchor();
});

