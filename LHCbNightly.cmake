cmake_minimum_required(VERSION 2.8.5)

set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_LIST_DIR} ${CMAKE_MODULE_PATH})
include(lbnMacros)

include(SlotConfig)

set(sorted_projects)
get_deps(sorted_projects ${projects})
set(projects ${sorted_projects})

set(SLOT_BUILD_DIR "/tmp/marcocle/${slot}/build.${config}")

# Checkout
#execute_process(COMMAND checkoutSlot.py lhcb-gaudi-head)
#execute_process(COMMAND git clone -b dev/cmake http://cern.ch/gaudi/Gaudi.git GAUDI/GAUDI_v23r5
#                COMMAND getpack -Pr LHCb v35r3)
execute_process(COMMAND rm -rf ${SLOT_BUILD_DIR})
file(MAKE_DIRECTORY ${SLOT_BUILD_DIR})
execute_process(COMMAND tar xf ${CMAKE_CURRENT_LIST_DIR}/${slot}.sources.tar.bz2
                WORKING_DIRECTORY ${SLOT_BUILD_DIR})

# Generate the project configuration valid now
set(CTEST_PROJECT_NAME "${slot}")
set(CTEST_BINARY_DIRECTORY "${SLOT_BUILD_DIR}")
gen_projects_xml()
#ctest_submit(FILES "${CTEST_BINARY_DIRECTORY}/Project.xml")

# This choses which kind of build we are doing.
set(Model Nightly)

foreach(project ${projects})
  string(TOUPPER "${project}" PR)
  if(project STREQUAL Gaudi)
    set(SOURCE_DIR "${SLOT_BUILD_DIR}/GAUDI/GAUDI_v23r5")
  else()
    set(SOURCE_DIR "${SLOT_BUILD_DIR}/${PR}/${PR}_${${project}_version}")
  endif()

  configure_file("${CMAKE_CURRENT_LIST_DIR}/CTestConfig.template.cmake"
                 "${SOURCE_DIR}/CTestConfig.cmake")

  configure_file("${CMAKE_CURRENT_LIST_DIR}/CTestScript.template.cmake"
                 "${SOURCE_DIR}/CTestScript.cmake" @ONLY)

  configure_file("${CMAKE_CURRENT_LIST_DIR}/CTestCustom.cmake"
                 "${SOURCE_DIR}/CTestCustom.cmake" COPYONLY)

  configure_file("${CMAKE_CURRENT_LIST_DIR}/SlotConfig.cmake"
                 "${SOURCE_DIR}/SlotConfig.cmake" COPYONLY)

  execute_process(COMMAND ctest -VV -S CTestScript.cmake
                  WORKING_DIRECTORY ${SOURCE_DIR})
endforeach()
