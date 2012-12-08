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
set(CTEST_CONFIGURE_COMMAND "$${CTEST_CONFIGURE_COMMAND} -DCMAKE_USE_DISTCC=TRUE $${CTEST_SCRIPT_DIRECTORY}")

set(CTEST_BUILD_COMMAND "make -j 8 -k")

##########################
# Start the session
ctest_start(${Model})

set_property(GLOBAL PROPERTY SubProject "${project} ${version}")
set_property(GLOBAL PROPERTY Label "${project} ${version}")

if(NOT STEP STREQUAL TEST)
  ##ctest_update()
  ctest_configure()
  ctest_build()
  ctest_submit(FILES "${build_dir}/Project.xml")
  ctest_submit(PARTS Update Notes Configure Build)
  execute_process(COMMAND $${CMAKE_COMMAND} -P $${CTEST_BINARY_DIRECTORY}/cmake_install.cmake)
endif()

if(NOT STEP STREQUAL BUILD)
  ctest_test() # it seems there is no need for APPEND here
  ctest_submit(PARTS Test)
endif()
