#!/bin/bash

# nats checker
wait_for_nats() {
  local i=0
  local sts=""
  while [ "Running" != "${sts}" ]
  do
    log "Waiting for nats cluster to start..."
    sleep 20
    if [ $i -ge 10 ]; then
      log 1 "nats cluster did not start"
    else
      sts=$(kubectl -n $kube_ns get po -l app=nats \
      | grep nats-2 | awk '{ print $3 }')
      log "nats cluster status: ${sts}"
      i=$((i+1))
    fi
  done
  log "nats cluster started"
}

homedir="$(dirname $0)/.."
mkdir -p ${homedir}/logs
log="${homedir}/logs/$(basename -s .sh ${0}).log"
>$log
. ${homedir}/scripts/logger.sh
log "Log file: ${log}"

kube_ns=$1
log "kubernetes namespace: ${kube_ns}"
log "gateway hosts to add: $2"
log "gateway ips to add  : $3"
IFS=, read -r -a gw_hosts <<< "$(echo $2 | sed -E 's/\[|\]//g')"
IFS=, read -r -a gw_ips <<< "$(echo $3 | sed -E 's/\[|\]//g')"

# get existing nats configuration files
kubectl -n ${kube_ns} get cm nats-config \
  -o jsonpath="{.data['nats\.conf']}" > ${homedir}/conf/nats.conf
kubectl -n $kube_ns get cm nats-config \
  -o jsonpath="{.data['lfusers\.json']}" > ${homedir}/conf/lfusers.json
kubectl -n $kube_ns get cm nats-config \
  -o jsonpath="{.data['accounts\.json']}" > ${homedir}/conf/accounts.json
[ $? -eq 0 ] && log "Exported nats configuration files" \
  || log 1 "Failed to get nats configuration file"

# create gateway.json conf file
cat <<EOF >${homedir}/conf/gateways.json
{
  "gateway": {
    "name": "$(hostname)",
    "port": 7522,
    "gateways": []
  }
}
EOF

# add each gateway name and url to gateways.json
for i in ${!gw_hosts[@]}; do
  gw_to_add=$(cat <<EOF
[
  {
    "name": "${gw_hosts[$i]}",
    "url": "nats://${gw_ips[$i]}:7522"
  }
]
EOF
  )
  log "adding gateway: ${gw_to_add}"

  cat ${homedir}/conf/gateways.json \
    | jq ".gateway.gateways += ${gw_to_add}" \
    > ${homedir}/conf/gateways-tmp.json
  if [ $? -eq 0 ]; then
    mv ${homedir}/conf/gateways-tmp.json ${homedir}/conf/gateways.json
    log "gateway added to gateways.json"
  else
    log 1 "Failed to add gateway to gateways.json"
  fi
done

sysacct=$(cat <<EOF
{
  "ACCCDYW3WJSLJJYUADYCBDAOOIZ6AGCC3L23BYNXTRRQ773YSHXH7OWB": {}
}
EOF
)
log "sysacct: ${sysacct}"

cat ${homedir}/conf/accounts.json \
  | jq ".accounts += ${sysacct}" \
  > ${homedir}/conf/accounts-tmp.json

if [ $? -eq 0 ]; then
  log "sys account added to nats accounts"
else
  log 1 "Failed to add sys account in nats conf"
fi

sysacct=$(cat <<EOF
{
  "system_account": "ACCCDYW3WJSLJJYUADYCBDAOOIZ6AGCC3L23BYNXTRRQ773YSHXH7OWB"
}
EOF
)
log "${sysacct}"

cat ${homedir}/conf/accounts-tmp.json \
  | jq ". += ${sysacct}" \
  > ${homedir}/conf/accounts.json

if [ $? -eq 0 ]; then
  log "system account set in nats server"
else
  log 1 "Failed to set system account in nats"
fi

cat <<EOF >>${homedir}/conf/nats.conf
include "./gateways.json"
EOF
log "nats gateway configuration file created"

kubectl -n ${kube_ns} create cm nats-config \
  --from-file ${homedir}/conf/nats.conf \
  --from-file ${homedir}/conf/lfusers.json \
  --from-file ${homedir}/conf/accounts.json \
  --from-file ${homedir}/conf/gateways.json \
  -o yaml --dry-run=client \
  | kubectl replace -f - 2>&1 | tee -a $log
[ $? -eq 0 ] && log "nats cluster configuration updated" \
  || log 1 "Failed to update nats cluster configuration"

mv ${homedir}/conf/* ${homedir}/debug/

kubectl -n $kube_ns delete po -l app=nats 2>&1 | tee -a $log
wait_for_nats
log "ground station nats clusters are interconnected through gateways"
exit 0
