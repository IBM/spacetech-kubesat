#!/bin/bash

log="/tmp/run.log"
>log
kubesat="/opt/kubesat"

# usage
usage() {
  cat <<USG
Usage: bash $0 [OPTIONS]
  OPTIONS:
  -s|--nats-server    NATS server hostname/ip-address
  -d|--redis-server   REDIS server hostname/ip-address
  -a|--api-host       Service name for this node
  -t|--node-type      Node type. Valid values: sim, gs, iot, cs
                      sim: config, logging
                           czml, cluster, clock
                      gs:  groundstation
                      iot: iot
                      cs:  orbits, data, rl, agriculture
USG
}

# parse options
while (( "$#" )); do
  case "$1" in
    -s|--nats-server)
      nats="$2"
      shift 2
      ;;
    -d|--redis-server)
      redis="$2"
      shift 2
      ;;
    -t|--node-type)
      node_type=$2
      shift 2
      ;;
    -a|--api-host)r
      api_host=$2
      shift 2
      ;;
    -h|--help)r
      usage
      exit 0
      ;;
    *)
      echo -e "ERROR: Invalid arg(s)" |tee -a $log
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${nats}" || -z "${redis}" || -z "${api_host}" || -z "${node_type}" ]]; then
  echo "ERROR: Missing arg(s)"
  usage
  exit 1
fi

echo "redis host:     ${redis}" |tee -a $log
echo "nats host:      ${nats}" |tee -a $log
echo "api host:      ${api_host}" |tee -a $log
echo "node type:      ${node_type}" |tee -a $log

pkill python

svcs=""
case "${node_type}" in
  sim)
    svcs="config logging czml cluster clock"
    ;;
  gs)
    svcs="groundstation"
    ;;
  iot)
    svcs="iot"
    ;;
  cs)
    svcs="orbits data rl agriculture"
    ;;
esac

port=8001

# start kubesat services
start_svc() {
  echo "Starting $1..." |tee -a $log
  cd ${kubesat}/$1 && nohup python -u run.py -a $api_host -s $nats -d $redis -t $port > /tmp/$1.log &
  echo "$! $1" |tee -a $log
  port=$(( port+ 1 )) && sleep 10
}

for s in ${svcs}; do
  start_svc $s
done

echo "Done. Logs available in /tmp folder" |tee -a $log
while true; do sleep 50; done
