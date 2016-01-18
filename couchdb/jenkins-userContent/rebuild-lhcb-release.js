var JENKINS_JOB = '../job/lhcb-release';
function getParameterByName(name) {
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}
$(function(){
    var data = {
        delay: '60sec',
        projects_list: getParameterByName('projects_list'),
        platforms: getParameterByName('platforms'),
        build_tool: getParameterByName('build_tool')
    };
    if (data.projects_list && data.platforms){
        $.ajax({
            url: JENKINS_JOB + '/buildWithParameters',
            method: 'POST',
            data: data
        }).done(function(){
            document.location = JENKINS_JOB;
        }).fail(function(){
            alert('Error starting the job.');
            document.location = JENKINS_JOB;
        });
    } else {
        alert('Missing parameters for the rebuild.');
        document.location = JENKINS_JOB;
    }
});
