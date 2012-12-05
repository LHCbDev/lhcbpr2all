cmake_minimum_required(VERSION 2.8.5)

include("${CTEST_SCRIPT_DIRECTORY}/SlotConfig.cmake")

# CTest-specific configuration
set(CTEST_SITE "pclhcb117")
set(CTEST_BUILD_NAME "${config}")
set(CTEST_NOTES_FILES "${CTEST_SCRIPT_DIRECTORY}/SlotConfig.cmake")

set(CTEST_CMAKE_GENERATOR "Unix Makefiles")
set(CTEST_PROJECT_NAME "${slot}")

set(CTEST_SOURCE_DIRECTORY "${CTEST_SCRIPT_DIRECTORY}")
set(CTEST_BINARY_DIRECTORY "${CTEST_SCRIPT_DIRECTORY}/build.${config}")

# Clean up the build directory
execute_process(COMMAND rm -rf "${CTEST_BINARY_DIRECTORY}")

set(ENV{CMTCONFIG}      "${config}")
set(ENV{CMTPROJECTPATH} "@SLOT_BUILD_DIR@:$ENV{CMTPROJECTPATH}")

set(CTEST_CONFIGURE_COMMAND "${CMAKE_COMMAND} -DCMAKE_TOOLCHAIN_FILE=${CTEST_SCRIPT_DIRECTORY}/toolchain.cmake")
set(CTEST_CONFIGURE_COMMAND "${CTEST_CONFIGURE_COMMAND} -DCMAKE_USE_DISTCC=TRUE ${CTEST_SCRIPT_DIRECTORY}")

set(CTEST_BUILD_COMMAND "make -j 8 -k install")

##########################
# Start the session
ctest_start(@Model@)

##########################
# Start the session
ctest_start(Experimental)

set_property(GLOBAL PROPERTY SubProject @project@)

##ctest_update()
ctest_submit(FILES "@SLOT_BUILD_DIR@/Project.xml")
ctest_submit(PARTS Update Notes)

ctest_configure()
ctest_submit(PARTS Configure)

ctest_build()
ctest_submit(PARTS Build)

ctest_test()
ctest_submit(PARTS Test)
