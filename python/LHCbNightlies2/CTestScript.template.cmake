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

set(CTEST_CONFIGURE_COMMAND "$${CMAKE_COMMAND} -DCMAKE_TOOLCHAIN_FILE=$${CTEST_SCRIPT_DIRECTORY}/toolchain.cmake")
set(CTEST_CONFIGURE_COMMAND "$${CTEST_CONFIGURE_COMMAND} -DCMAKE_USE_DISTCC=TRUE")
if(EXISTS $${CTEST_SCRIPT_DIRECTORY}/cache_preload.cmake)
  set(CTEST_CONFIGURE_COMMAND "$${CTEST_CONFIGURE_COMMAND} -C$${CTEST_SCRIPT_DIRECTORY}/cache_preload.cmake")
endif()
set(CTEST_CONFIGURE_COMMAND "$${CTEST_CONFIGURE_COMMAND} $${CTEST_SCRIPT_DIRECTORY}")

if(JOBS)
  set(JOBS "-j$${JOBS}")
endif()
set(CTEST_BUILD_COMMAND "make $${JOBS} -k")

if(USE_CMT)
  # Builds driven by CMT need special settings
  set(CTEST_BINARY_DIRECTORY "$${CTEST_SOURCE_DIRECTORY}")
  set(CTEST_CONFIGURE_COMMAND "no config step in CMT-based build")
  set(CTEST_BUILD_COMMAND "make $${JOBS} -k Package_failure_policy=ignore logging=enabled")
  # guess the container: it can be *Release (Gaudi) or *Sys (LHCb projects)
  if (EXISTS "${project}Release")
    set(CMT_CONTAINER_PACKAGE "${project}Release")
  else()
    set(CMT_CONTAINER_PACKAGE "${project}Sys")
  endif()
  set(ENV{GAUDI_QMTEST_HTML_OUTPUT} "$${CTEST_BINARY_DIRECTORY}/test_results")
  if(ENV{CMTEXTRATAGS})
    set(ENV{CMTEXTRATAGS} "$ENV{CMTEXTRATAGS},no-pyzip,use-distcc"
  else()
    set(ENV{CMTEXTRATAGS} "no-pyzip,use-distcc"
  endif()
endif()

##########################
# Start the session
ctest_start(${Model})

set_property(GLOBAL PROPERTY SubProject "${project} ${version}")
set_property(GLOBAL PROPERTY Label "${project} ${version}")

if(NOT STEP STREQUAL TEST)
  ##ctest_update()
  ctest_configure()
  ctest_build()
  if(NOT NO_SUBMIT)
    ctest_submit(FILES "${build_dir}/Project.xml")
    ctest_submit(PARTS Update Notes Configure Build)
  endif()
  if(NOT USE_CMT)
    execute_process(COMMAND $${CMAKE_COMMAND} -P $${CTEST_BINARY_DIRECTORY}/cmake_install.cmake)
    execute_process(COMMAND make python.zip WORKING_DIRECTORY $${CTEST_BINARY_DIRECTORY})
  endif()
endif()

if(NOT STEP STREQUAL BUILD)
  # Create directory for QMTest summaries and reports
  file(MAKE_DIRECTORY ${build_dir}/summaries/${project})

  if(NOT USE_CMT)
    ctest_test() # it seems there is no need for APPEND here
    if(NOT NO_SUBMIT)
      ctest_submit(PARTS Test)
    endif()
    # produce plain text summary of QMTest tests
    execute_process(COMMAND make QMTestSummary WORKING_DIRECTORY $${CTEST_BINARY_DIRECTORY}
                    OUTPUT_FILE ${build_dir}/summaries/${project}/QMTestSummary.txt)
  else()
    # CMT requires special commands for the tests.
    set(ENV{PWD} "$${CTEST_BINARY_DIRECTORY}/$${CMT_CONTAINER_PACKAGE}/cmt")
    file(MAKE_DIRECTORY $${CTEST_BINARY_DIRECTORY}/test_results)
    execute_process(COMMAND cmt br - cmt TestPackage
                    WORKING_DIRECTORY $${CTEST_BINARY_DIRECTORY}/$${CMT_CONTAINER_PACKAGE}/cmt)
    execute_process(COMMAND cmt qmtest_summarize
                    WORKING_DIRECTORY $${CTEST_BINARY_DIRECTORY}/$${CMT_CONTAINER_PACKAGE}/cmt
                    OUTPUT_FILE ${build_dir}/summaries/${project}/QMTestSummary.txt)
  endif()

  # copy the QMTest HTML output
  file(COPY $${CTEST_BINARY_DIRECTORY}/test_results/.
       DESTINATION ${build_dir}/summaries/${project}/html/.)
endif()
