#!/bin/bash

# nats checker
wait_for_nats() {
  i=0
  sts=""
  while [ "Running" != "${sts}" ]
  do
    log "Waiting for nats cluster to start..."
    sleep 20
    if [ $i -ge 10 ]; then
      log 1 "nats cluster did not start"
    else
      sts=$(kubectl -n ${kube_ns} get po -l app=nats \
        | grep nats-2 | awk '{ print $3 }')
      log "nats cluster status: ${sts}"
      i=$((i+1))
    fi
  done
  log "nats cluster started"
}

homedir="$(dirname $0)/.."
mkdir -p ${homedir}/logs ${homedir}/conf ${homedir}/debug
log="${homedir}/logs/$(basename -s .sh ${0}).log"
>$log
. ${homedir}/scripts/logger.sh
log "Log file: ${log}"

kube_ns=$1
log "kubernetes namespace: ${kube_ns}"
log "leafnode hostnames: $3"
IFS=, read -r -a leafnode_hostnames <<< "$(echo $3 | sed -E 's/\[|\]//g')"
IFS=, read -r -a leafuser_pass <<< "$(echo $2 | sed -E 's/\[|\]//g')"

# get existing nats configuration files
kubectl -n ${kube_ns} get cm nats-config \
  -o jsonpath="{.data['nats\.conf']}" > ${homedir}/conf/nats.conf
kubectl -n $kube_ns get cm nats-config \
  -o jsonpath="{.data['lfusers\.json']}" > ${homedir}/conf/lfusers.json
kubectl -n $kube_ns get cm nats-config \
  -o jsonpath="{.data['accounts\.json']}" > ${homedir}/conf/accounts.json
[ $? -eq 0 ] && log "Exported nats configuration files" \
  || log 1 "Failed to get nats configuration file"

cat ${homedir}/conf/lfusers.json \
  | jq ".leafnodes.authorization.users = []" \
  > ${homedir}/conf/lfusers-tmp.json
mv ${homedir}/conf/lfusers-tmp.json ${homedir}/conf/lfusers.json

local_user=$(jq '.accounts.swarm.users[0]' /home/ground/conf/accounts.json)
jq ".accounts.swarm.users = []" ${homedir}/conf/accounts.json > ${homedir}/conf/accounts-tmp.json
jq ".accounts.swarm.users = [${local_user}]" ${homedir}/conf/accounts-tmp.json > ${homedir}/conf/accounts.json

for i in ${!leafnode_hostnames[@]}; do
  leafuser=$(cat <<EOF
[
  {
    "user": "leaf-${leafnode_hostnames[$i]}",
    "password": "${leafuser_pass[$i]}",
    "account": "swarm"
  }
]
EOF
  )
  log "leafuser to add: ${leafuser}"
  cat ${homedir}/conf/lfusers.json \
    | jq ".leafnodes.authorization.users += ${leafuser}" \
    > ${homedir}/conf/lfusers-tmp.json
  if [ $? -eq 0 ]; then
    log "leafuser added to nats conf"
    mv ${homedir}/conf/lfusers-tmp.json ${homedir}/conf/lfusers.json
  else
    log 1 "Failed to add leafuser to nats conf"
  fi

  leafuser=$(cat <<EOF
[
  {
    "user": "leaf-${leafnode_hostnames[$i]}",
    "password": "${leafuser_pass[$i]}"
  }
]
EOF
  )
  log "leafuser to add: ${leafuser}"

  cat ${homedir}/conf/accounts.json \
    | jq ".accounts.swarm.users += ${leafuser}" \
    > ${homedir}/conf/accounts-tmp.json

  if [ $? -eq 0 ]; then
    log "leafnode user added to swarm account in nats conf"
    mv ${homedir}/conf/accounts-tmp.json ${homedir}/conf/accounts.json
  else
    log 1 "Failed to add leafnode user to swarm account in nats conf"
  fi
done

kubectl -n ${kube_ns} create cm nats-config \
  --from-file ${homedir}/conf/nats.conf \
  --from-file ${homedir}/conf/lfusers.json \
  --from-file ${homedir}/conf/accounts.json \
  -o yaml --dry-run=client \
  | kubectl replace -f - 2>&1 | tee -a $log
[ $? -eq 0 ] && log "nats configuration map updated" \
  || log 1 "Failed to update nats configuration map"

mv ${homedir}/conf/* ${homedir}/debug/

kubectl -n $kube_ns delete po -l app=nats 2>&1 | tee -a $log
wait_for_nats
log "nats cluster configuration reloaded with leafnode updates."
exit 0
