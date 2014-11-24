###############################################################################
# (c) Copyright 2013 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
cmake_minimum_required(VERSION 2.8.5)

include("$${CTEST_SCRIPT_DIRECTORY}/SlotConfig.cmake")

# STEP can be BUILD (do not run tests), TEST (do not build), ALL (run
# everything, default).
if(NOT DEFINED STEP)
  set(STEP ALL)
endif()

# CTest-specific configuration
set(CTEST_SITE "${site}")
set(CTEST_BUILD_NAME "$${config}")
set(CTEST_NOTES_FILES "$${CTEST_SCRIPT_DIRECTORY}/SlotConfig.json"
                      "$${CTEST_SCRIPT_DIRECTORY}/SlotConfig.cmake")

set(CTEST_CMAKE_GENERATOR "Unix Makefiles")
set(CTEST_PROJECT_NAME "$${slot}")

set(CTEST_SOURCE_DIRECTORY "$${CTEST_SCRIPT_DIRECTORY}")
set(CTEST_BINARY_DIRECTORY "$${CTEST_SCRIPT_DIRECTORY}/build.$${config}")

if(NOT STEP STREQUAL TEST)
  # Clean up the build directory
  execute_process(COMMAND rm -rf "$${CTEST_BINARY_DIRECTORY}")
endif()

set(ENV{CMTCONFIG}      "$${config}")
set(ENV{CMTPROJECTPATH} "${build_dir}:$$ENV{CMTPROJECTPATH}")

set(CTEST_CONFIGURE_COMMAND "$${CMAKE_COMMAND}")
if(EXISTS $${CTEST_SCRIPT_DIRECTORY}/toolchain.cmake)
  set(CTEST_CONFIGURE_COMMAND "$${CTEST_CONFIGURE_COMMAND} -DCMAKE_TOOLCHAIN_FILE=$${CTEST_SCRIPT_DIRECTORY}/toolchain.cmake")
endif()
if(NOT DISABLE_DISTCC)
  set(CTEST_CONFIGURE_COMMAND "$${CTEST_CONFIGURE_COMMAND} -DCMAKE_USE_DISTCC=TRUE")
endif()
if(EXISTS $${CTEST_SCRIPT_DIRECTORY}/cache_preload.cmake)
  set(CTEST_CONFIGURE_COMMAND "$${CTEST_CONFIGURE_COMMAND} -C$${CTEST_SCRIPT_DIRECTORY}/cache_preload.cmake")
endif()
set(CTEST_CONFIGURE_COMMAND "$${CTEST_CONFIGURE_COMMAND} $${CTEST_SCRIPT_DIRECTORY}")

if(JOBS)
  set(JOBS "-j$${JOBS}")
endif()
if(MAX_LOAD)
  set(MAX_LOAD "-l$${MAX_LOAD}")
endif()
set(CTEST_BUILD_COMMAND "make $${JOBS} $${MAX_LOAD} -k")

if(USE_CMT)
  # Builds driven by CMT need special settings
  set(CTEST_BINARY_DIRECTORY "$${CTEST_SOURCE_DIRECTORY}")
  set(CTEST_CONFIGURE_COMMAND "echo no config step in CMT-based build")
  set(CTEST_BUILD_COMMAND "$${CTEST_BUILD_COMMAND} Package_failure_policy=ignore logging=enabled")
  # guess the container: it can be *Release (Gaudi) or *Sys (LHCb projects)
  if (EXISTS "${project}Release")
    set(CMT_CONTAINER_PACKAGE "${project}Release")
  else()
    set(CMT_CONTAINER_PACKAGE "${project}Sys")
  endif()
  set(ENV{GAUDI_QMTEST_HTML_OUTPUT} "$${CTEST_BINARY_DIRECTORY}/test_results")
  if(NOT ENV{CMTEXTRATAGS} STREQUAL "")
    set(ENV{CMTEXTRATAGS} "$$ENV{CMTEXTRATAGS},no-pyzip")
  else()
    set(ENV{CMTEXTRATAGS} "no-pyzip")
  endif()
  if(NOT DISABLE_DISTCC)
    find_program(distcc_cmd NAMES distcc)
    if(distcc_cmd)
      set(ENV{CMTEXTRATAGS} "$$ENV{CMTEXTRATAGS},use-distcc")
    endif()
  endif()
endif()

# Hack to overcome the slowness of CTest regexp parsing: reduce the lines of the
# build logs to no more than 1000 chars.
# See http://public.kitware.com/Bug/view.php?id=12381
file(WRITE "$${CTEST_BINARY_DIRECTORY}/build_cmd.sh" "#!/bin/sh -x
$${CTEST_BUILD_COMMAND} | sed -r 's/(.{695}).{5,}(.{300})/\\1[...]\\2/'
")
set(CTEST_BUILD_COMMAND "sh -x $${CTEST_BINARY_DIRECTORY}/build_cmd.sh")


##########################
# Start the session
ctest_start(${Model})

set_property(GLOBAL PROPERTY SubProject "${project} ${version}")
set_property(GLOBAL PROPERTY Label "${project} ${version}")

# Create directory for QMTest summaries and reports
file(MAKE_DIRECTORY ${summary_dir})

execute_process(COMMAND date OUTPUT_VARIABLE configure_start)
ctest_configure()
execute_process(COMMAND date OUTPUT_VARIABLE configure_end)

if(NOT STEP STREQUAL TEST)
  ##ctest_update()
  execute_process(COMMAND date OUTPUT_VARIABLE build_start)
  ctest_build()
  execute_process(COMMAND date OUTPUT_VARIABLE build_end)
  if(NOT NO_SUBMIT)
    ctest_submit(FILES "${build_dir}/Project.xml")
    ctest_submit(PARTS Update Notes Configure Build)
  endif()
  if(NOT USE_CMT)
    execute_process(COMMAND make unsafe-install WORKING_DIRECTORY $${CTEST_BINARY_DIRECTORY}
                    OUTPUT_VARIABLE install_log ERROR_VARIABLE install_log)
    message("$${install_log}")
    if(EXISTS $${CTEST_SCRIPT_DIRECTORY}/InstallArea/$${config}/python)
      execute_process(COMMAND make post-install WORKING_DIRECTORY $${CTEST_BINARY_DIRECTORY}
                      OUTPUT_VARIABLE post_install_log ERROR_VARIABLE post_install_log)
      message("$${post_install_log}")
    endif()
  endif()

  # Copy the build log to the summaries
  if(NOT USE_CMT)
    file(GLOB config_log $${CTEST_BINARY_DIRECTORY}/Testing/Temporary/LastConfigure_*.log)
    file(READ $${config_log} f)
    file(WRITE ${summary_dir}/build.log
         "#### CMake configure ####\n# Start: $${configure_start}\n$${f}# End: $${configure_end}\n")
    execute_process(COMMAND lbn-collect-build-logs --append
                              --exclude ".*unsafe-install.*"
                              --exclude ".*python.zip.*"
                              --exclude ".*precompile-.*"
                              $${CTEST_BINARY_DIRECTORY} ${summary_dir}/build.log
                    RESULT_VARIABLE collect_logs_result)
    if(NOT collect_logs_result EQUAL 0)
      file(GLOB build_log $${CTEST_BINARY_DIRECTORY}/Testing/Temporary/LastBuild_*.log)
      file(READ $${build_log} f)
      file(APPEND ${summary_dir}/build.log
           "#### CMake build ####\n# Start: $${build_start}\n$${f}# End: $${build_end}\n")
    endif()
    file(APPEND ${summary_dir}/build.log "#### CMake install ####\n$${install_log}")
    if(post_install_log)
      file(APPEND ${summary_dir}/build.log "#### CMake post-install ####\n$${post_install_log}")
    endif()
  else()
    # for CMT we need a different way
    # - find the package build logs
    file(GLOB_RECURSE build_logs build.$${config}.log)
    # - sort them according to the build counter they contain
    #    (# Building package ... [n/NN])
    set(sortable_build_logs)
    foreach(bl $${build_logs})
      file(READ $${bl} bl_head LIMIT 1024)
      string(REGEX MATCH "Building package[^[]*\\[([0-9]+)/[0-9]+\\]" bl_head "$${bl_head}")
      set(n $${CMAKE_MATCH_1})
      string(LENGTH "$${n}" l)
      math(EXPR l "4 - $${l}")
      foreach(i RANGE $${l})
        set(n "0$${n}")
      endforeach()
      list(APPEND sortable_build_logs $${n}.$${bl})
    endforeach()
    if(sortable_build_logs)
      list(SORT sortable_build_logs)
    endif()
    set(build_logs)
    foreach(bl $${sortable_build_logs})
      string(REGEX REPLACE "^[0-9]+\\." "" bl "$${bl}")
      list(APPEND build_logs $${bl})
    endforeach()
    # - concatenate all the logs in the right order
    file(REMOVE ${summary_dir}/build.log)
    foreach(bl $${build_logs})
      message(STATUS "adding $${bl}")
      file(READ $${bl} l)
      file(APPEND ${summary_dir}/build.log "$${l}")
    endforeach()
  endif()
endif()

if(NOT STEP STREQUAL BUILD)

  if(NOT USE_CMT)
    ctest_test() # it seems there is no need for APPEND here
    if(NOT NO_SUBMIT)
      ctest_submit(PARTS Test)
    endif()
    # produce plain text summary of QMTest tests
    execute_process(COMMAND make QMTestSummary WORKING_DIRECTORY $${CTEST_BINARY_DIRECTORY}
                    OUTPUT_FILE ${summary_dir}/QMTestSummary.txt)
    if(IS_DIRECTORY $${CTEST_BINARY_DIRECTORY}/Testing/xml_test_results OR
       IS_DIRECTORY $${CTEST_BINARY_DIRECTORY}/xml_test_results)
      # this is a build that supports CTest XML test results from QMTest
      execute_process(COMMAND make HTMLSummary WORKING_DIRECTORY $${CTEST_BINARY_DIRECTORY})
    endif()
  else()
    # CMT requires special commands for the tests.
    set(ENV{PWD} "$${CTEST_BINARY_DIRECTORY}/$${CMT_CONTAINER_PACKAGE}/cmt")
    file(MAKE_DIRECTORY $${CTEST_BINARY_DIRECTORY}/test_results)
    execute_process(COMMAND cmt br - cmt TestPackage
                    WORKING_DIRECTORY $${CTEST_BINARY_DIRECTORY}/$${CMT_CONTAINER_PACKAGE}/cmt
                    OUTPUT_FILE ${summary_dir}/QMTestSummary.run.txt)
    execute_process(COMMAND cmt qmtest_summarize
                    WORKING_DIRECTORY $${CTEST_BINARY_DIRECTORY}/$${CMT_CONTAINER_PACKAGE}/cmt
                    OUTPUT_FILE ${summary_dir}/QMTestSummary.txt)
  endif()

  # copy the QMTest HTML output
  if(IS_DIRECTORY $${CTEST_BINARY_DIRECTORY}/html)
    file(COPY $${CTEST_BINARY_DIRECTORY}/html/.
         DESTINATION ${summary_dir}/html/.)
  else()
    file(COPY $${CTEST_BINARY_DIRECTORY}/test_results/.
         DESTINATION ${summary_dir}/html/.)
  endif()

  # this is the old-style build log names
  set(OLD_BUILD_ID ${old_build_id})
  if(OLD_BUILD_ID)
    file(COPY $${CTEST_BINARY_DIRECTORY}/test_results/.
         DESTINATION ${summary_dir}/$${OLD_BUILD_ID}-qmtest/.)
    execute_process(COMMAND $${CMAKE_COMMAND} -E copy ${summary_dir}/QMTestSummary.txt ${summary_dir}/$${OLD_BUILD_ID}-qmtest.log)
  endif()
endif()
