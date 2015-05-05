#!/bin/bash


export platform=${CMTCONFIG:-x86_64-slc6-gcc48-opt}
export slots="lhcb-test-new-config"
#export slots="lhcb-compatibility"

#Clean all
jenkins/mock.sh mock/clean_rsync None master
jenkins/mock.sh mock/clean_build None master
jenkins/mock.sh mock/clean_preconditions None master
jenkins/mock.sh mock/clean_checkout None master
jenkins/mock.sh mock/clean_enabled_slots None master


jenkins/mock.sh enabled_slots None master

files=`ls slot-params-*.txt`
jenkins/mock.sh mock/clean_enabled_slots None master

slots=""
for file in ${files}; do
	slot=${file%.txt*}
	slot=${slot#*slot-params-}
	slots="${slots} ${slot}"
	jenkins/mock.sh checkout ${slot} ${platform}
	files_preconditions="${files_preconditions} `ls slot-precondition-*.txt`"
	files_build="${files_build} `ls slot-*.txt`"
	jenkins/mock.sh mock/clean_checkout ${slot} ${platform}
done

for file in ${files_preconditions}; do
	touch ${file}
done

for slot in ${slots}; do
	for file in `ls slot-precondition-${slot}-*.txt`; do
		platform=${file%.txt*}
		platform=${platform#*${slot}-}
		rm ${file}
		jenkins/mock.sh preconditions ${slot} ${platform}
		jenkins/mock.sh mock/clean_preconditions ${slot} ${platform}
	done
done

for file in ${files_build}; do
	touch ${file}
done

for slot in ${slots}; do
	for file in `ls slot-*-${slot}-*.txt`; do
		platform=${file%.txt*}
		platform=${platform#*${slot}-}
		rm ${file}
		jenkins/mock.sh build ${slot} ${platform}
		exit 0
		jenkins/mock.sh mock/clean_build ${slot} ${platform}
	done
done

#jenkins/mock.sh mock/clean_rsync None master
