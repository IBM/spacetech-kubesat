#!/bin/bash

# nats checker
wait_for_nats() {
  i=0
  sts=""
  while [ "Running" != "${sts}" ]
  do
    log "Waiting for nats server to start..."
    sleep 20
    if [ $i -ge 10 ]; then
      log 1 "nats server did not start"
    else
      sts=$(kubectl -n $kube_ns get po -l app=nats \
        | grep nats-0 | awk '{ print $3 }')
      log "nats server status: ${sts}"
      i=$((i+1))
    fi
  done
  log "nats server started"
}

homedir="$(dirname $0)/.."
mkdir -p ${homedir}/logs ${homedir}/conf ${homedir}/debug
log="${homedir}/logs/$(basename -s .sh ${0}).log"
>$log
. ${homedir}/scripts/logger.sh
log "Log file: ${log}"

kube_ns=$1
leafuser_pass=$2
ground_private_ip=$3
leafnode_hostname="$(hostname -s)"
log "kubernetes namespace: ${kube_ns}"
log "leafnode hostname: ${leafnode_hostname}"
log "ground ip address: $3"
IFS=, read -r -a ground_private_ip <<< "$(echo $3 | sed -E 's/\[|\]//g')"

# get existing nats configuration files
kubectl -n ${kube_ns} get cm nats-config \
  -o jsonpath="{.data['nats\.conf']}" > ${homedir}/conf/nats.conf
kubectl -n ${kube_ns} get cm nats-config \
  -o jsonpath="{.data['cluster\.json']}" > ${homedir}/conf/cluster.json
kubectl -n ${kube_ns} get cm nats-config \
  -o jsonpath="{.data['auth\.json']}" > ${homedir}/conf/auth.json
[ $? -eq 0 ] && log "Exported nats configuration files" \
  || log 1 "Failed to get nats configuration file"

urls=""
for i in ${!ground_private_ip[@]}; do
  urls=${urls}"\"nats://leaf-${leafnode_hostname}:${leafuser_pass}@${ground_private_ip[$i]}:7422\", "
done
urls=$(echo ${urls} | sed 's/,*$//g')
log "Remote leafnode service endpoints: ${urls}"
cat <<EOF >${homedir}/conf/leafnode.json
{
  "leafnodes": {
    "remotes": [
      {
        "urls": [ ${urls} ]
      }
    ]
  }
}
EOF

cat <<EOF >>${homedir}/conf/nats.conf
## leafnode
include "./leafnode.json"
EOF
log "leafnode stanza nats configuration file created"

kubectl -n ${kube_ns} create cm nats-config \
  --from-file ${homedir}/conf/nats.conf \
  --from-file ${homedir}/conf/cluster.json \
  --from-file ${homedir}/conf/auth.json \
  --from-file ${homedir}/conf/leafnode.json -o yaml \
  --dry-run=client | kubectl replace -f - 2>&1 | tee -a $log
[ $? -eq 0 ] && log "nats configuration map updated" \
  || log 1 "Failed to update nats configuration map"
mv ${homedir}/conf/* ${homedir}/debug/

kubectl -n ${kube_ns} delete po -l app=nats 2>&1 | tee -a $log
wait_for_nats
log "nats server configuration reloaded with leafnode remote url. nats server ready"
log "Done!"
exit 0
