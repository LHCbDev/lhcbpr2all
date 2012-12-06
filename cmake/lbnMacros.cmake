# Macros, functions and settings used by the test driver

# - Settings

find_program(hostname_cmd hostname)

# This choses which kind of build we are doing.
if(NOT DEFINED Model)
  set(Model Nightly)
endif()

# STEP can be BUILD (do not run tests), TEST (do not build), ALL (run
# everything, default).
if(NOT DEFINED STEP)
  set(STEP ALL)
endif()

# - Macros

macro(gen_projects_xml)
  set(data "<Project name=\"${slot}\">")
  foreach(p ${projects})
    set(data "${data}\n  <SubProject name=\"${p} ${${p}_version}\">")
    foreach(d ${${p}_dependencies})
      set(data "${data}\n    <Dependency name=\"${d} ${${d}_version}\"/>")
    endforeach()
    set(data "${data}\n  </SubProject>")
  endforeach()
  set(data "${data}\n</Project>\n")
  file(WRITE "${SLOT_BUILD_DIR}/Project.xml" "${data}")
endmacro()

macro(get_deps output)
  foreach(name ${ARGN})
    get_deps(${output} ${${name}_dependencies})
    set(${output} ${${output}} ${name})
  endforeach()
  if(${output})
    list(REMOVE_DUPLICATES ${output})
  endif()
endmacro()

macro(sort_projects)
  set(sorted_projects)
  get_deps(sorted_projects ${projects})
  set(projects ${sorted_projects})
endmacro()

macro(load_config)
  message(STATUS "Loading slot configuration.")
  include(SlotConfig)
  sort_projects()
  get_site(site)
  message(STATUS "Building ${slot} for ${config} on ${site}.")
endmacro()

function(get_source_dir project var)
  set(version ${${project}_version})
  string(TOUPPER "${project}" PROJECT)

  if(DEFINED ${project}_dir)
    set(${var} "${SLOT_BUILD_DIR}/${${project}_dir}" PARENT_SCOPE)
  else()
    set(${var} "${SLOT_BUILD_DIR}/${PROJECT}/${PROJECT}_${version}" PARENT_SCOPE)
  endif()
endfunction()

# Prepare the build directories for the build
macro(prepare_build_dir)

  message(STATUS "Preparing sources.")

  file(GLOB sources "sources/*.tar.bz2")
  if(sources)
    execute_process(COMMAND rm -rf ${SLOT_BUILD_DIR})
    file(MAKE_DIRECTORY ${SLOT_BUILD_DIR})
    foreach(source ${sources})
      message(STATUS "  unpacking ${source}")
      execute_process(COMMAND tar xf ${source}
                      WORKING_DIRECTORY ${SLOT_BUILD_DIR})
    endforeach()
  else()
    message(FATAL_ERROR "No source tarball found: nothing to build.")
  endif()

  message(STATUS "Generating CTest scripts and configurations.")

  gen_projects_xml()

  foreach(project ${projects})
    set(version ${${project}_version})
    string(TOUPPER "${project}" PROJECT)
    get_source_dir(${project} SOURCE_DIR)

    configure_file("${CMAKE_CURRENT_LIST_DIR}/cmake/CTestConfig.template.cmake"
                   "${SOURCE_DIR}/CTestConfig.cmake")

    configure_file("${CMAKE_CURRENT_LIST_DIR}/cmake/CTestScript.template.cmake"
                   "${SOURCE_DIR}/CTestScript.cmake" @ONLY)

    configure_file("${CMAKE_CURRENT_LIST_DIR}/SlotConfig.cmake"
                   "${SOURCE_DIR}/SlotConfig.cmake" COPYONLY)
  endforeach()
endmacro()

macro(get_site var)
  execute_process(COMMAND ${hostname_cmd} OUTPUT_VARIABLE ${var})
  string(STRIP "${${var}}" ${var})
endmacro()
