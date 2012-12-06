cmake_minimum_required(VERSION 2.8.5)

set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_LIST_DIR}/cmake ${CMAKE_CURRENT_LIST_DIR} ${CMAKE_MODULE_PATH})
include(lbnMacros)

load_config()

set(SLOT_BUILD_DIR    "${CMAKE_CURRENT_LIST_DIR}/build")
set(SLOT_SOURCES_DIR  "${CMAKE_CURRENT_LIST_DIR}/sources")

if(STEP STREQUAL BUILD OR STEP STREQUAL ALL)
  prepare_build_dir()
endif()

foreach(project ${projects})
  get_source_dir(${project} SOURCE_DIR)
  execute_process(COMMAND ctest -VV -DSTEP=${STEP} -S CTestScript.cmake
                  WORKING_DIRECTORY ${SOURCE_DIR})
endforeach()
