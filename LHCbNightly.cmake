cmake_minimum_required(VERSION 2.8.5)

set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_LIST_DIR}/cmake ${CMAKE_CURRENT_LIST_DIR} ${CMAKE_MODULE_PATH})
include(lbnMacros)

load_config()

set(SLOT_BUILD_DIR "${CMAKE_CURRENT_LIST_DIR}/build")
set(SLOT_SOURCES_DIR "${CMAKE_CURRENT_LIST_DIR}/sources")

prepare_build_dir()

gen_projects_xml()

# This choses which kind of build we are doing.
if(NOT DEFINED Model)
  set(Model Nightly)
endif()

foreach(project ${projects})
  string(TOUPPER "${project}" PR)
  if(DEFINED ${project}_dir)
    set(SOURCE_DIR "${SLOT_BUILD_DIR}/${${project}_dir}")
  else()
    set(SOURCE_DIR "${SLOT_BUILD_DIR}/${PR}/${PR}_${${project}_version}")
  endif()

  configure_file("${CMAKE_CURRENT_LIST_DIR}/cmake/CTestConfig.template.cmake"
                 "${SOURCE_DIR}/CTestConfig.cmake")

  configure_file("${CMAKE_CURRENT_LIST_DIR}/cmake/CTestScript.template.cmake"
                 "${SOURCE_DIR}/CTestScript.cmake" @ONLY)

  configure_file("${CMAKE_CURRENT_LIST_DIR}/SlotConfig.cmake"
                 "${SOURCE_DIR}/SlotConfig.cmake" COPYONLY)

  execute_process(COMMAND ctest -VV -S CTestScript.cmake
                  WORKING_DIRECTORY ${SOURCE_DIR})
endforeach()
