#!/bin/bash

homedir="$(dirname $0)/../.."
mkdir -p ${homedir}/deploy/logs ${homedir}/deploy/files
log="${homedir}/deploy/logs/$(basename ${0} .sh).log"
>$log
. ${homedir}/deploy/scripts/logger.sh
log "Log file: ${log}"
ver=$1

log "\ncreating ground tarball..."
tar -czvf ${homedir}/deploy/files/ground_${ver}.tgz \
--exclude=${homedir}/kubesat \
--exclude=${homedir}/agriculture \
--exclude=${homedir}/orbits \
--exclude=${homedir}/data \
--exclude=${homedir}/rl \
--exclude=${homedir}/rl-training \
--exclude=${homedir}/platform \
--exclude=${homedir}/*/test* \
--exclude=${homedir}/*/assets \
--exclude=${homedir}/*/_* \
--exclude=${homedir}/*/*.md \
--exclude=${homedir}/*/.* \
${homedir}/*/*.yaml \
${homedir}/*/*.py \
${homedir}/*/*.sh \
${homedir}/*/Dockerfile \
${homedir}/utils/kubesat \
${homedir}/config/simulation_config \
${homedir}/dashboard \
2>&1 | tee -a $log
log "\nKubeSat app files for ground nodes added to ${homedir}/deploy/files/ground_${ver}.tgz"

log "\ncreating swarm tarball..."
tar -czvf ${homedir}/deploy/files/swarm_${ver}.tgz \
--exclude=${homedir}/kubesat \
--exclude=${homedir}/config \
--exclude=${homedir}/logging \
--exclude=${homedir}/groundstation \
--exclude=${homedir}/iot \
--exclude=${homedir}/czml \
--exclude=${homedir}/dashboard \
--exclude=${homedir}/clock \
--exclude=${homedir}/platform \
--exclude=${homedir}/*/test* \
--exclude=${homedir}/*/assets \
--exclude=${homedir}/*/_* \
--exclude=${homedir}/*/*.md \
--exclude=${homedir}/*/.* \
${homedir}/*/*.yaml \
${homedir}/*/*.py \
${homedir}/*/*.sh \
${homedir}/*/Dockerfile \
${homedir}/utils/kubesat \
${homedir}/rl \
2>&1 | tee -a $log
log "\nKubeSat app files for swarm nodes added to ${homedir}/deploy/files/swarm_${ver}.tgz"
exit
