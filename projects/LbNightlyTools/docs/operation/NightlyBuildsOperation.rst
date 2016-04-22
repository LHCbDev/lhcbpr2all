===============================
Nightly Builds Operation Manual
===============================

.. contents:: Table of Contents

Introduction
============
The LHCb Nightly Build System is based on a few subsystems:

- Jenkins_, for scheduling
- custom scripts, for checkout, build and test
- CouchDB_, for the dashboard


Logical organization
--------------------
The LHCb Nightly builds are organized in *slots*, *projects* and *platforms*.

A *slot* is a named set of *projects* meant to test the build of the software
under some well defined conditions.  For example, the slot *lhcb-head* is used
to build the latest version in the repository of all the LHCb software projects
on top of a released version version of Gaudi (and the externals), while
*lhcb-cmake* is used to test the build with CMake of the projects already
converted to it.

A *project* in a *slot* is a well defined version of a LHCb software project,
which could be a *tagged* version (as it can be released) or the latest version
in the repository (using the special version tag ``HEAD``). A *project* can also
be tuned by changing the version used for one (or more) of its packages with
respect to the one that is implied by the specified version of the project (for
example use a released version of a package in the ``HEAD`` version of the project
or vice versa).

Each *project* in each *slot* is built and tested on one or more *platforms*,
i.e. combinations of CPU architecture, Operating System (OS), compiler and
optimization level.  A *platform* is identified by a string where the four parts
of its definition are separated by a ``-``, for example ``x86_64-slc6-gcc46-opt``
means Intel/AMD (x86) 64 bits architecture, Scientific Linux CERN 6 (SLC6), gcc
4.6.x and optimized build.

Configuration
=============
**TO-DO**


Scheduling
==========

There is no particular scheduling (or throttling) for the nightly builds slots.

Every night, around midnight, the nightly bootstrap Jenkins job
(``nightly-slot``) is started.  It is a *parameterized job* that can be used to
start any slot, but in the default configuration it triggers all the slot
flagged as *enabled* (or, better, not disabled) in the configuration.

The ``nightly-slot`` job triggers one ``nightly-slot-checkout`` job per enabled
slot, which will then trigger ``nightly-slot-build-platform`` either directly or
via ``nightly-slot-precondition`` (as shown in the figure below).


.. figure:: images/jenkins-jobs.dot.png
   :align: center

   Trigger diagram of the jobs controlling the nightly builds in Jenkins.


We try to recover from temporary failures of the jobs infrastructure by
automatically restarting the failed jobs (up to 3 times).  An overview of the
status of the nightly build jobs can be found in the `Jenkins Jobs Status
page`_.

It must be noted that only failures of the Nightly Build System
are shown as failures in Jenkins, and failures of the builds or tests are
considered successful run of the Jenkins jobs.


Checkout, Build and Test
========================
**TO-DO**


Dashboard
=========
**TO-DO**


Common Tasks
============

Create a New Slot
-----------------
1. choose the slot configuration style:

  * XML (can use the web-based configuration editor, but not the new features of
    the build system)
  * JSON (requires manual editing from a checkout of LHCbNightlyConf_)
  * Python (most powerful, requires manual editing)

2. prepare the configuration of the slot, making sure that the ``disabled``
   field is unset or set to ``false`` (it is usually a good idea to clone an
   existing slot configuration and change it)

3. if the build products have to be installed on AFS

  1. create the slot directories and volumes in ``$LHCBNIGHTLIES`` (they can be
     symlinks to other directories, if needed)
  2. add the slot name to the special file ``slots_on_afs.txt`` in
     LHCbNightlyConf_


Stop a Build
------------
Sometimes it is necessary to stop a slot before it completes (for example to
restart the builds).

Stop One Platform
~~~~~~~~~~~~~~~~~
If there are pathologic problems with the build of a slot on one platform, or
before triggering its rebuild, we can stop it following these steps:

1. go to the `Nightly Builds Dashboard`_
2. locate on the page the slot/platform to stop
3. click on the corresponding Jenkins icon
4. click on the small red square icon with an X at the top right, close to the
   text *Progress:*

The build will terminate shortly, after some Jenkins internal book keeping
operations.

Stop the Whole Slot
~~~~~~~~~~~~~~~~~~~
If the slot is still in the checkout step, stopping the checkout job will be
enough:

1. go to the `Jenkins Jobs Status page`_
2. identify the running checkout job you want to stop in the *checkout* column
3. click on the job link
4. click on the small red square icon with an X at the top right, close to the
   text *Progress:*

If the checkout was completed, you need to stop all the building platforms and
the wrapper build job:

1. got to the `Jenkins Jobs Status page`_
2. identify the running build job you want to stop in the *precondition-build*
   column
3. click on the job link
4. click on the small red square icon with an X at the top right, close to the
   text *Progress:*
5. repeat for all the platforms (it may not be needed if the builds were
   terminated quickly enough and if the job is not waiting for some external
   conditions)


Trigger a Rebuild
-----------------
Re-building can be triggered at different levels:

* full rebuild: new checkout and new build of every platform
* no checkout: keep the existing checkout and rebuild all the platforms
* one platform: rebuild only one platform

Full Rebuild
~~~~~~~~~~~~
This is the easiest option and should be preferred to the others if we can
afford the time it takes for a checkout (for slots with several projects it may
take more than one hour).

This is also the only option in case we need a fresh checkout.

1. go to the `Jenkins Jobs Status page`_
2. click on the checkout job of the slot you want to restart
3. click on the *Rebuild* button in the column on the left
4. (optionally) if you want to override the default list of platforms to build,
   fill the *platforms* field with a space-separated list of the required
   platforms
5. click on the *Build* button

The field *os_label* allows you to override the system a build is run on. For
example to build *slc5* binaries on a *slc6* machine or to force the build on a
specific host. In most cases it must be left empty.

No Checkout
~~~~~~~~~~~
Useful if the checkout of a slot was correct, but all the builds failed for some
reason.

1. stop the build of the whole slot following the instructions above
2. go to the `Jenkins Jobs Status page`_
3. identify the job corresponding to the slot you need to restart and click on
   its link
4. click on *Rebuild* in the menu on the left
5. click on the *Rebuild* button not modifying the content of the fields

One Platform
~~~~~~~~~~~~
If, for example, there has been a problem with a machine you can rebuild only
one platform:

1. stop the build of the platform following the instructions above (`Stop One
   Platform`_), if needed
2. from the job page, click on *Rebuild* in the menu on the left
3. click on the *Rebuild* button not modifying the content of the fields

Note that you can access the specific build page from the `Jenkins Jobs Status
page`_ if you cannot find it through the `Nightly Builds Dashboard`_.


Dashboard Database Manipulation
-------------------------------

Remove a Build
~~~~~~~~~~~~~~
In principle there is no need to remove builds from the database, because each
new complete build of a slot will be reported in its own table and new partial
builds will overwrite the old entries, but sometimes a broken (or aborted) build
is just noise in the web page.

1. if you need to remove the current build of the day:

  1. connect to ``lhcb-archive.cern.ch`` as *lhcbsoft*
  2. remove the symlink ``/data/archive/artifacts/nightly/<slot>/<day>``, where
     ``<day>`` is the current date as yyyy-mm-dd

2. as *lhcbsoft* set up the environment for the Nightly Build tools

  1. cd ~/LbNightlyTools
  2. source setup.csh

3. start a Python shell and type the following commands (replacing <slot> with
   the slot name and <build_id> with build numeric id, which can be seen in the
   URL of the build or tests results)

  1. from LbNightlyTools.Utils import Dashboard
  2. d = Dashboard()
  3. d.dropBuild(<slot>, <build_id>)


Update the Dashboard CouchApp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To update the dashboard CouchApp avoiding downtime of the web page, we need to
use a fallback replica.

1. Replicate the dashboard database to a backup instance

  1. connect to http://lbcouchdb.cern.ch:5984/_utils/replicator.html (only a
     few machines can do it)
  2. select the local database ``nightlies-nightly`` as source and
     ``nightlies-nightly-bk`` as destination
  3. click on the *Replicate* button and wait

2. Ensure that the views' caches of the backup database are up to date

  a. either from the web

    1. go to http://lbcouchdb.cern.ch:5984/_utils/database.html?nightlies-nightly-bk
    2. select a view (under _dashboard_) in the dropdown list (all views of
       the dashboard will be cached, which will take some time, but you can check the
       progress at http://lbcouchdb.cern.ch:5984/_utils/status.html)

  b. or with a script (from LbNightlyTools)::

         ./cron/preheat_nightly_dashboard.sh -v -d http://lbcouchdb.cern.ch:5984/nightlies-nightly-bk/_design/dashboard

3. Repeat step 1 to ensure that the most recent data is replicated to the backup
   copy
4. Redirect the dashboard web page traffic to the backup database

  1. edit ``/etc/httpd/conf.d/25-lbcouchdb443.conf`` replacing  ``nightlies-nightly``
     with ``nightlies-nightly-bk``
  2. (as root) call ``service httpd reload``

5. Update/modify the Dashboard CouchApp in the main database
6. Regenerate the views' caches of the main database

  a. either from the web

    1. go to http://lbcouchdb.cern.ch:5984/_utils/database.html?nightlies-nightly
    2. select a view (under _dashboard_) in the dropdown list (all views of
       the dashboard will be cached, which will take some time, but you can check the
       progress at http://lbcouchdb.cern.ch:5984/_utils/status.html)

  b. or with a script (from LbNightlyTools)::

         ./cron/preheat_nightly_dashboard.sh -v -d http://lbcouchdb.cern.ch:5984/nightlies-nightly/_design/dashboard

7. Replicate new documents from the backup instance to the main one

    1. same as step 1, but swapping source and target
    2. check for conflicts

8. Restore the original web page configuration (see step 4)
9. Replicate once more from the backup instance to the main one (see step 7)

*Note*: The replication and the view caching may take a lot of time, unless the
        updates are performed regularly (less data to copy/cache).

.. _Jenkins: http://jenkins-ci.org/
.. _CouchDB: http://couchdb.apache.org/

.. _LHCbNightlyConf: https://svnweb.cern.ch/trac/lhcb/browser/LHCbNightlyConf/trunk

.. _Nightly Builds View: https://lhcb-jenkins.cern.ch/view/Nightly%20Builds/
.. _Nightly Builds Dashboard: https://lhcb-nightlies.cern.ch/

.. _Jenkins Jobs Status page: https://lhcb-jenkins.cern.ch/follow-builds-status
