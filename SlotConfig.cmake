# Slot configuration
set(slot lhcb-gaudi-head)
set(config x86_64-slc6-gcc46-opt)

set(projects Gaudi LHCb)

set(Gaudi_version HEAD)
# Override the default Gaudi source directory.
set(Gaudi_dir GAUDI/GAUDI_v23r5)

set(LHCb_version  v35r3)
set(LHCb_dependencies Gaudi)

set(CTEST_CUSTOM_WARNING_EXCEPTION
    ${CTEST_CUSTOM_WARNING_EXCEPTION}
    ".*/boost/.*"
    "^--->> genreflex: WARNING:.*")
