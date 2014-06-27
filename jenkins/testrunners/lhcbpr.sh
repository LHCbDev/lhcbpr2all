#!/usr/bin/env sh

export buildid="${slot}.${slot_build_id}"
export artifactsdir="${ARTIFACTS_DIR}"

echo "Build file to run test"
echo scripts/lbpr-get-command -o runtest.sh $project $buildid $platform  $testgroup $testenv $config_file
scripts/lbpr-get-command  -o runtest.sh  $project $buildid $platform  $testgroup $testenv $config_file
echo
echo "Now running the test"
mycount=${count:-1}
echo "Will run the test $mycount time(s)"
for i in `seq 1 $mycount`; do
	sh runtest.sh
done

