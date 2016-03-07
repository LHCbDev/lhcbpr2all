# Special wrapper to load the declared version of the heptools toolchain.
set(heptools_version 83)

if(ENV{HEPTOOLS_VERSION})
  set(heptools_version $ENV{HEPTOOLS_VERSION})
endif()

# this check is needed because the toolchain is called when checking the
# compiler (without the proper cache)
if(NOT CMAKE_SOURCE_DIR MATCHES "CMakeTmp")

 # Note: normally we should look for GaudiDefaultToolchain.cmake, but in Gaudi
 # it is not needed
 find_file(gdf GaudiDefaultToolchain.cmake)
 include(${gdf})

endif()
