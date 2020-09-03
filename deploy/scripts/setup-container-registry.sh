#!/bin/bash

homedir="$(dirname $0)/.."
mkdir -p ${homedir}/logs
log="${homedir}/logs/$(basename -s .sh ${0}).log"
>$log
. ${homedir}/scripts/logger.sh
log "Log file: ${log}"

push_to_local() {
  local img=$(echo $1|cut -d\/ -f2)
  log "Push $1 to local registry at localhost:5000/${img}..."
  sudo docker pull $1
  sudo docker tag $1 localhost:5000/${img}
  sudo docker push localhost:5000/${img} 2>&1 | tee -a ${log}
  sudo docker image remove $1 localhost:5000/${img}
}

sudo systemctl is-active docker
if [ $? -ne 0 ]; then
  log "Installing docker..."
  sudo apt update
  sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
  sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
  sudo apt update
  apt-cache policy docker-ce
  sudo apt install -y docker-ce
  sudo usermod -aG docker ${USER}
  sudo systemctl is-active docker || log 1 "docker install failed. Exiting..."
  log "docker install complete"
else
  log "docker running, skipping install"
fi
log "start private docker registry..."
sudo docker run -d -p 5000:5000 --restart=always --name registry registry:2
log "private docker registry setup at localhost:5000"

push_to_local redis:5.0.1-alpine
push_to_local synadia/nats-server:nightly-20200710
push_to_local connecteverything/nats-boot-config:0.5.2
push_to_local synadia/nats-box:0.3.0
push_to_local connecteverything/nats-server-config-reloader:0.6.0
push_to_local synadia/prometheus-nats-exporter:0.5.0

log "Done"
