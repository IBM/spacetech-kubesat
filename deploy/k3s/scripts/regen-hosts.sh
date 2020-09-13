#!/bin/bash

homedir="$(dirname $0)/.."
mkdir -p ${homedir}/logs
log="${homedir}/logs/$(basename -s .sh ${0}).log"
>$log
. ${homedir}/scripts/logger.sh
log "Log file: ${log}"

hosts_file='/etc/hosts'
log "host name: $(hostname -s)"
log "domain name: $(hostname -d)"
log "hostnames to add to hosts file: $1"
log "private ip-addresses to add: $2"
log "public ip-addresses to add: $3"

IFS=, read -r -a hosts <<< "$(echo $1 | sed -E 's/\[|\]//g')"
IFS=, read -r -a ips_pri <<< "$(echo $2 | sed -E 's/\[|\]//g')"
IFS=, read -r -a ips <<< "$(echo $3 | sed -E 's/\[|\]//g')"

# remove existing hostnames
log "Deleting any existing entries from hosts file..."
for i in ${hosts[@]}; do
   [ $(hostname -s) == $i ] \
    && log "skip deleting local hostname: $i" \
    || sed -i -E "/$i/d" ${hosts_file}
done

# removed existing ip-addresses
for i in ${ips_pri[@]}; do
  sed -i -E "/$i/d" ${hosts_file}
done

for i in ${ips[@]}; do
  sed -i -E "/$i/d" ${hosts_file}
done

# hosts entry
log "Appending entries to hosts file..."
for i in ${!hosts[@]}; do
  echo "${ips_pri[$i]}  ${hosts[$i]}.$(hostname -d)  $(echo ${hosts[$i]})" \
    2>&1 | tee -a ${hosts_file}
  echo "${ips[$i]}  ${hosts[$i]}.$(hostname -d) $(echo ${hosts[$i]})" \
    2>&1 | tee -a ${hosts_file}
done
log "hosts file regenerated: ${hosts_file}"
cat ${hosts_file}
exit 0
