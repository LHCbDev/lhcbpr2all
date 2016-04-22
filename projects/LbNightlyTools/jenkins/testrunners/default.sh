#!/usr/bin/env sh

set -x
time lbn-test --debug \
              --build-id "${slot}.${slot_build_id}" \
              --artifacts-dir "${ARTIFACTS_DIR}" \
              --projects ${project} \
              ${prepare_opt} \
              ${submit_opt} \
              ${rsync_opt} \
              ${coverity_opt} \
              ${summary_prefix_opt} \
              ${config_file}
