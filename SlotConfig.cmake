# Slot configuration
set(slot lhcb-gaudi-head)
#set(config x86_64-slc6-gcc46-opt)
set(config $ENV{CMTCONFIG})

set(projects DaVinci Gaudi Lbcom LHCb Rec Brunel Phys Analysis Stripping)

set(Gaudi_version     v23r5 )
set(LHCb_version      v35r3 )
set(Lbcom_version     v13r3 )
set(Rec_version       v14r3 )
set(Brunel_version    v44r1 )
set(Phys_version      v16r3 )
set(Analysis_version  v10r3 )
set(Stripping_version v6r3  )
set(DaVinci_version   v33r1 )

set(Gaudi_dependencies     )
set(LHCb_dependencies      Gaudi)
set(Lbcom_dependencies     LHCb)
set(Rec_dependencies       LHCb)
set(Brunel_dependencies    Lbcom Rec)
set(Phys_dependencies      Rec)
set(Analysis_dependencies  Phys)
set(Stripping_dependencies Phys Lbcom)
set(DaVinci_dependencies   Analysis Stripping Lbcom)

set(CTEST_CUSTOM_WARNING_EXCEPTION
    ${CTEST_CUSTOM_WARNING_EXCEPTION}
    ".*/boost/.*"
    "^--->> genreflex: WARNING:.*")
