#!/usr/bin/env sh

echo time lbn-build --verbose --jobs 8 --timeout 18000 --build-id "${slot}.${slot_build_id}" --artifacts-dir "${ARTIFACTS_DIR}" --tests-only --projects ${project} ${prepare_opt} ${submit_opt} ${rsync_opt} ${coverity_opt} ${config_file}
time lbn-build --verbose --jobs 8 --timeout 18000 --build-id "${slot}.${slot_build_id}" --artifacts-dir "${ARTIFACTS_DIR}" --tests-only --projects ${project} ${prepare_opt} ${submit_opt} ${rsync_opt} ${coverity_opt} ${config_file}
