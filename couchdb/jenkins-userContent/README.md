This folder contains files required by the dashboard, that should be installed
in $JENKINS_HOME/userContent.

For it to work, the Jenkins' [Content Security Policy](https://wiki.jenkins-ci.org/display/JENKINS/Configuring+Content+Security+Policy) must be relaxed to include, at least, `script-src 'self';` (see http://content-security-policy.com/ for details).

When running in Tomcat, one can append these lines to the file `catalina.properties`:
```
#
# Relax Jenkins Content Security Policy settings
hudson.model.DirectoryBrowserSupport.CSP=default-src 'none'; script-src 'self'; img-src 'self'; style-src 'self';
```
