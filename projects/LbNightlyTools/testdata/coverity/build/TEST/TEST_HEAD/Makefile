ifneq ($(COV_TEST_BUILD_ERROR),)
all:
	@mkdir -p build.$(CMTCONFIG)
	@echo Error | tee build.$(CMTCONFIG)/`date +%s%N`-$@-build.log
	exit 1
endif

%:
	@mkdir -p build.$(CMTCONFIG)
	@echo Invoked target $@ | tee build.$(CMTCONFIG)/`date +%s%N`-$@-build.log
