#!/bin/bash

homedir="$(dirname $0)/.."
mkdir -p ${homedir}/logs
log="${homedir}/logs/$(basename -s .sh ${0}).log"
>$log
. ${homedir}/scripts/logger.sh
log "Log file: ${log}"

kube_ns=$1
log "kubernetes namespace: ${kube_ns}"
log "routes to add: $2"
IFS=, read -r -a routes_to_add <<< "$(echo $2 | sed -E 's/\[|\]//g')"

# get existing nats configuration files
kubectl -n ${kube_ns} get cm nats-config \
  -o jsonpath="{.data['nats\.conf']}" > ${homedir}/conf/nats.conf
kubectl -n ${kube_ns} get cm nats-config \
  -o jsonpath="{.data['cluster\.json']}" > ${homedir}/conf/cluster.json
kubectl -n ${kube_ns} get cm nats-config \
  -o jsonpath="{.data['auth\.json']}" > ${homedir}/conf/auth.json
kubectl -n ${kube_ns} get cm nats-config \
  -o jsonpath="{.data['leafnode\.json']}" > ${homedir}/conf/leafnode.json
[ $? -eq 0 ] && log "Exported nats configuration files" \
  || log 1 "Failed to get nats configuration file"

for i in ${!routes_to_add[@]}; do
  route_to_add=$(cat <<EOF
[
  "nats://${routes_to_add[$i]}:6222"
]
EOF
  )
  log "route to add: ${route_to_add}"
  cat ${homedir}/conf/cluster.json \
    | jq ".cluster.routes += ${route_to_add}" \
    > ${homedir}/conf/cluster-tmp.json
  if [ $? -eq 0 ]; then
    mv ${homedir}/conf/cluster-tmp.json ${homedir}/conf/cluster.json
    log "route added to cluster.json"
  else
    log 1 "Failed to add route to cluster.json"
  fi
done

kubectl -n ${kube_ns} create cm nats-config \
  --from-file ${homedir}/conf/nats.conf \
  --from-file ${homedir}/conf/cluster.json \
  --from-file ${homedir}/conf/auth.json \
  --from-file ${homedir}/conf/leafnode.json -o yaml \
  --dry-run=client | kubectl replace -f - 2>&1 | tee -a $log
[ $? -eq 0 ] && log "nats cluster configuration updated" \
  || log 1 "Failed to update nats cluster configuration"
mv ${homedir}/conf/* ${homedir}/debug/
log "nats server will form cluster in few seconds at next auto-config reload"
exit 0
