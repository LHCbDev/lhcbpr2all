cmake_minimum_required(VERSION 2.8.5)

set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_LIST_DIR}/cmake ${CMAKE_CURRENT_LIST_DIR} ${CMAKE_MODULE_PATH})
include(lbnMacros)

load_config()

set(SLOT_BUILD_DIR "${CMAKE_CURRENT_LIST_DIR}/build")
set(SLOT_SOURCES_DIR "${CMAKE_CURRENT_LIST_DIR}/sources")

macro(checkout project version)
  message(STATUS "Checking out ${project} ${version}...")
  string(TOUPPER "${project}" PROJECT)
  if(${project} STREQUAL "Gaudi")
    execute_process(COMMAND git clone -b dev/cmake http://cern.ch/gaudi/Gaudi.git ${PROJECT}/${PROJECT}_${version}
                    WORKING_DIRECTORY ${SLOT_BUILD_DIR})
    file(WRITE "${SLOT_BUILD_DIR}/${PROJECT}/${PROJECT}_${version}/Makefile"
         "include \$(LBCONFIGURATIONROOT)/data/Makefile\n")
  else()
    if(${version} STREQUAL "HEAD")
      execute_process(COMMAND time getpack -PH --no-config ${project} ${version}
                      WORKING_DIRECTORY ${SLOT_BUILD_DIR})
    else()
      execute_process(COMMAND time getpack -Pr --no-config ${project} ${version}
                      WORKING_DIRECTORY ${SLOT_BUILD_DIR})
    endif()
  endif()
endmacro()


execute_process(COMMAND rm -rf "${SLOT_BUILD_DIR}" "${SLOT_SOURCES_DIR}")
file(MAKE_DIRECTORY "${SLOT_BUILD_DIR}" "${SLOT_SOURCES_DIR}")

foreach(project ${projects})
  checkout(${project} ${${project}_version})
endforeach()

foreach(project ${projects})
  message(STATUS "Packing ${project} ${${project}_version}...")
  string(TOUPPER "${project}" PROJECT)
  execute_process(COMMAND tar cjf ${SLOT_SOURCES_DIR}/${project}.src.tar.bz2 ${PROJECT}/${PROJECT}_${${project}_version}
                  WORKING_DIRECTORY ${SLOT_BUILD_DIR})
endforeach()

message(STATUS "Sources ready for build")
