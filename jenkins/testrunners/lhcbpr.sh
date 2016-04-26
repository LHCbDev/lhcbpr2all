#!/usr/bin/env sh

export buildid="${slot}.${slot_build_id}"
export artifactsdir="${ARTIFACTS_DIR}"

export lhcbpr_api_url=${lhcbpr_api_url:-"https://lblhcbpr2.cern.ch/api"}
export lhcbpr_check_ssl=${lhcbpr_check_ssl:-"false"}

lhcbpr_check_ssl_cmd=$( [ $lhcbpr_check_ssl = "true" ] && echo "--check-ssl")
echo "Build file to run test"
#echo $WORKSPACE/scripts/lbpr-get-command -o runtest.sh $project $buildid $platform  $testgroup $testenv $config_file
$WORKSPACE/scripts/lbpr-get-command  --url $lhcbpr_api_url $lhcbpr_check_ssl_cmd -o runtest.sh  $project $buildid $platform  $testgroup $testenv $config_file
echo
echo "Now running the test"
mycount=${count:-1}
echo "Will run the test $mycount time(s)"
for i in `seq 1 $mycount`; do
    sh runtest.sh
done

