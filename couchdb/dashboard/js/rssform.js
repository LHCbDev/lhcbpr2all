// links
var href = window.location.href.split("/");
href.pop(0);

//alert(href);
var resultserverlink = href.join("/")+"/rss";
var diskserverlink = href.join("/")+"/diskspacerss";
var slot_name_view = "_view/slotsNames?group=true";
var platform_name_view = "_view/platformsNames?group=true";
var project_name_view = "_view/projectsNames?group=true" ;

// number of element into the containers
var slotnumber = 0;
var platformnumber = 0;
var projectnumber =0;


// create a valid http arg list or a valid http arg regex
function createlist(liste,type){
	if (liste && liste.length !=0){
		if(type=="regex"){
			var output = [];
			for (var j = 0; j < liste.length;j++){
				output.push(liste[j].value.replace(/-/g,"\\-")); // "-" protection to regex
			}
			return "("+output.join("|")+")";
		}else{
			var output = [];
			for (var j = 0; j < liste.length;j++){
				output.push("'"+liste[j].value+"'");
			}
			return "("+output.join(",")+")";
		}
	}else{
		return "('all')";
	}
}
// method to add a choice button
$.fn.addchoice = function(choicecat,choicename){
	var choice = $('<button>',{id:choicecat+choicename,cat:choicecat,target:choicename,text:choicename});
	choice.button()
		.click(function(){
			$("#"+$(this).attr("cat")+" #"+$(this).attr("target")).click();
		});
	$(this).append(choice);

};

function processform1(event){
	if(event.target.getAttribute("class")  == "ui-tabs-anchor" ||event.target.nodeName == "INPUT" && (event.type =="click" && (event.target.type == "checkbox" || event.target.type == "radio")|| event.type=="change" && event.target.getAttribute("class") == "regexinput")){

		var link = resultserverlink;
		var args = []; // first arg to have in the result classified by descending date
		var active = $( "#advancedoption" ).tabs( "option", "active" );
		if(event.type =="click" && event.target.type == "checkbox"){
			if(event.target.checked){
				$("#selected").addchoice(event.target.getAttribute("parentid"),event.target.value);
			}else{
				$("#selected").find('#'+event.target.getAttribute("parentid")+event.target.value).remove();
			}
		}
		// active == 0 <-> list mode else : regex mode
		if(active == 0){
			$("#selected").show();
			// process slots
			if(createlist($("#slotcontainer").find( "input:checked" )) != "('all')" && $("#slotcontainer").find( "input:checked" ).length != slotnumber){
				args.push("slotlist="+createlist($("#slotcontainer").find( "input:checked" )));
				// set the regex corresponding to the user choice
				$("#slotregex").val(createlist($("#slotcontainer").find( "input:checked" ),"regex"));
			}else{
				$("#slotregex").val(".*");
			}
			// process project
			if(createlist($("#projectcontainer").find( "input:checked" )) != "('all')" && $("#projectcontainer").find( "input:checked" ).length != projectnumber ){
				args.push("projectlist="+createlist($("#projectcontainer").find( "input:checked" )));
				$("#projectregex").val(createlist($("#projectcontainer").find( "input:checked" ),"regex"));
			}else{
				$("#projectregex").val(".*");
			}
			// process platform
			if(createlist($("#platformcontainer").find( "input:checked" )) != "('all')" && $("#platformcontainer").find( "input:checked" ).length != platformnumber ){
				args.push("platformlist="+createlist($("#platformcontainer").find( "input:checked" )));
				$("#platformregex").val(createlist($("#platformcontainer").find( "input:checked" ),"regex"));
			}else{
				$("#platformregex").val(".*");
			}

		}else{
			// hide the "selected" div because it is useless with the advance option.( and shows bad information )
			$("#selected").hide();
			// process the regex
			if($("#slotregexinput").find("input").val() && $("#slotregexinput").find("input").val() !=""){
				// use "encodeURIComponent" to escape invalid http argument chars
				args.push("slotpattern="+encodeURIComponent($("#slotregexinput").find("input").val()));
			}
			if($("#platformregexinput").find("input").val() && $("#platformregexinput").find("input").val() !=""){
				args.push("platformpattern="+encodeURIComponent($("#platformregexinput").find("input").val()));
			}
			if($("#projectregexinput").find("input").val() && $("#projectregexinput").find("input").val() !=""){
				args.push("projectpattern="+encodeURIComponent($("#projectregexinput").find("input").val()));
			}

		}
		// process the nature
		if( $("#nature").find("input:checked").val() && $("#nature").find("input:checked").val() != ""){
			args.push("nature="+$("#nature").find("input:checked").val());
		}
		// process the alert level
		if( $("#alertlevel").find("input:checked").val() && $("#alertlevel").find("input:checked").val() != ""){
			args.push("alertlevel="+$("#alertlevel").find("input:checked").val());
		}
		// join the args and use a final escape
		if(args.length != 0){
			link+=encodeURI("?"+args.join(";"));
		}
		// set the result link
		$("#result").attr("href",link)
					.text(link);
	}
}

// process the disk space rss customisation
function processform2(value){
	var link = diskserverlink;
	var args = [];

	args.push("minfreespacepercentage="+value);

	link+=encodeURI("?"+args.join(";"));

	$("#diskresult").attr("href",link)
				.text(link);
}

var dialogCalls = 3;
function prepareDialog() {
	dialogCalls -= 1;
	if (dialogCalls <= 0) {
		// loading finished
		$(".rssicon").attr("src","images/rss.png");
		// resize the accordion to fill the free space
		$( ".accordion" ).accordion("refresh");
	}
}

function refreshAccordion(){
	setTimeout(function(){$( ".accordion" ).accordion("refresh");},500);
}
$(function(){
	// load slots
	$.getJSON(slot_name_view)
	.success(function(data){
		var dataTemp = [];
		for(var index = 0;index<data["rows"].length;index++){
			dataTemp.push(data["rows"][index]["key"]);
		}
		data = dataTemp;
		for( var slotname in data){
			$("#slotcontainer").append($('<li class="checkbox" ><input type="checkbox" name="slotnames" parentid="slotcontainer"value="'+data[slotname]+'" id="'+data[slotname]+'"><label for="'+data[slotname]+'">'+data[slotname]+'</label></li>'));
		}
		// activate the jquery-ui theme
		$("#slotcontainer").buttonset();
		slotnumber = $("#slotcontainer").find(".checkbox").length;

		prepareDialog();
	});
		// load platforms
		$.getJSON(platform_name_view)
	.success(function(data){
		var dataTemp = [];
		for(var index = 0;index<data["rows"].length;index++){
			dataTemp.push(data["rows"][index]["key"]);
		}
		data = dataTemp;
		for( var platformname in data){
			$("#platformcontainer").append($('<li class="checkbox" ><input type="checkbox" name="platformnames" parentid="platformcontainer" value="'+data[platformname]+'" id="'+data[platformname]+'"><label for="'+data[platformname]+'">'+data[platformname]+'</label></li>'));
		}
		$("#platformcontainer").buttonset();
		platformnumber = $("#platformcontainer").find(".checkbox").length;
		prepareDialog();
	});
		//load projects
		$.getJSON(project_name_view)
	.success(function(data){
		var dataTemp = [];
		for(var index = 0;index<data["rows"].length;index++){
			dataTemp.push(data["rows"][index]["key"]);
		}
		data = dataTemp;
		for( var projectname in data){
			$("#projectcontainer").append($('<li class="checkbox" ><input type="checkbox" name="projectnames" parentid="projectcontainer"value="'+data[projectname]+'" id="'+data[projectname]+'"><label for="'+data[projectname]+'">'+data[projectname]+'</label></li>'));
		}
		$("#projectcontainer").buttonset();
		projectnumber = $("#projectcontainer").find(".checkbox").length;
		prepareDialog();
	});

		// Catch event on high to activate the form processing
		$("#high").bind("click",processform1).bind("change",processform1);
		$('#slider').slider({
		    change: function(event, ui) {
		    	var value = ui.value;
		    	processform2(value);
		    }
		});


		// set unfiltered url at first display
		$("#result").attr("href",resultserverlink)
		.text(resultserverlink);
		$("#diskresult").attr("href",diskserverlink+"?minfreespacepercentage=1")
		.text(diskserverlink+"?minfreespacepercentage=1");

		//activate (un)check all buttons
		$(".checkall").click(function(){
			var state = false;
			if($(this).hasClass("check")){
				state = true;
			}
			$.each($("#"+$(this).attr("value")+"container").find( "input" ),function(){
				if ($(this).prop("checked") != state){
					$(this).click();
				}
			});
			return false;

		});

});


// jquery ui theme setting

$(function(){
	$(".radiocontainer").buttonset();
	$(".containeroptions").button();
	$( ".accordion" ).accordion({collapsible: true,	active: false,	heightStyle : "fill"	});
	$("#simple-tab").height($("#high").height()-75); // to debug the height problem of the accordion
	$(".tabs").tabs();

	var valuemin = valuemax = 0;
	$('#slider').slider({
        min:    1,
        max:    100,
        range:  false,
        values: [1],
        slide:  function(event, ui) {
            valuemin = ui.values[0];
            $(this).prev().val(valuemin);
        }
    });



});
