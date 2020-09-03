#!/bin/bash

# redis checker
wait_for_redis() {
  local i=0
  local sts=""
  while [ "Running" != "${sts}" ]
  do
    log "Waiting for redis server to start..."
    sleep 20
    if [ $i -ge 10 ]; then
      log 1 "redis server did not start"
    else
      sts=$(kubectl -n $kube_ns get po -l app=redis \
      | tail -n 1 | awk '{ print $3 }')
      log "redis server status: ${sts}"
      i=$((i+1))
    fi
  done
  log "redis server started"
}

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
mkdir -p ${homedir}/logs ${homedir}/conf ${homedir}/debug
log="${homedir}/logs/$(basename -s .sh ${0}).log"
>$log
. ${homedir}/scripts/logger.sh
log "Log file: ${log}"

kube_ns=$1
log "kubernetes namespace: ${kube_ns}"

# install k3s
log "Installing k3s..."
curl -sfL https://get.k3s.io | sh - 2>&1 | tee -a ${log}
sleep 10
sudo systemctl is-active k3s || log 1 "k3s did not start. Exiting..."
kubectl get nodes 2>&1 | tee -a ${log}
[ $? -eq 0 ] && log "Successfully installed k3s" || log 1 "k3s install failed"
kubectl create ns ${kube_ns} | tee -a ${log}

log "Creating k3s registries.yaml..."
cd /etc/rancher/k3s/
cat <<EOF >registries.yaml
mirrors:
  docker.io:
    endpoint:
      - "http://localhost:5000"
EOF
log "Restarting k3s..."
sudo systemctl restart k3s
sudo systemctl is-active k3s || log 1 "k3s did not start. Exiting..."
log "k3s is now setup to pull from private registry at localhost:5000"

# install redis
log "Installing redis..."
kubectl -n ${kube_ns} create secret generic redis --from-literal=redisa=$(head /dev/urandom|tr -dc "a-zA-Z0-9"|head -c 10)
cat << EOF >/var/lib/rancher/k3s/server/manifests/redis.yaml
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: redis-data-pv
  namespace: ${kube_ns}
  labels:
    app: redis
spec:
  storageClassName: manual
  capacity:
    storage: 2Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: "/mnt/data"

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-data
  namespace: ${kube_ns}
  labels:
    app: redis
spec:
  storageClassName: manual
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 2Gi

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: ${kube_ns}
  labels:
    app: redis
spec:
  replicas: 3
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
        version: 5.0.1
    spec:
      containers:
      - name: redis
        image: localhost:5000/redis:5.0.1-alpine
        env:
        - name: REDISA
          valueFrom:
            secretKeyRef:
              name: redis
              key: redisa
        command:
        - redis-server
        args:
        - --bind 0.0.0.0
        - --requirepass \$(REDISA)
        ports:
        - containerPort: 6379
        volumeMounts:
        - mountPath: /data
          name: redis-data
      volumes:
        - name: redis-data
          persistentVolumeClaim:
            claimName: redis-data

---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: ${kube_ns}
  labels:
    app: redis
spec:
  type: ClusterIP
  ports:
  - port: 6379
    targetPort: 6379
  selector:
    app: redis
EOF
[ $? -eq 0 ] && log "redis manifest created" \
  || log 1 "Failed to create redis manifest"
wait_for_redis

# install nats
log "Installing nats..."
cat <<EOF >/var/lib/rancher/k3s/server/manifests/nats.yaml
---
apiVersion: v1
kind: Secret
metadata:
  name: nats-users
  namespace: ${kube_ns}
  labels:
    app: nats
type: Opaque
data:
  user: bG9jYWwtdXNlcgo=
  pass: $(head /dev/urandom|tr -dc "a-zA-Z0-9"|head -c 20|base64)

---
apiVersion: helm.cattle.io/v1
kind: HelmChart
metadata:
  name: nats
  namespace: kube-system
spec:
  repo: https://nats-io.github.io/k8s/helm/charts
  chart: nats
  targetNamespace: ${kube_ns}
  valuesContent: |-
    nats:
      externalAccess: false
      advertise: false
      image: localhost:5000/nats-server:nightly-20200710
    bootconfig:
      image: localhost:5000/nats-boot-config:0.5.2
    natsbox:
      image: localhost:5000/nats-box:0.3.0
    reloader:
      image: localhost:5000/nats-server-config-reloader:0.6.0
    exporter:
      image: localhost:5000/prometheus-nats-exporter:0.5.0
    cluster:
      enabled: true

---
apiVersion: v1
kind: Service
metadata:
  name: nats-lb
  namespace: ${kube_ns}
  labels:
    app: nats
spec:
  type: LoadBalancer
  selector:
    app: nats
  ports:
    - protocol: TCP
      name: client
      port: 4222
      targetPort: 4222
    - protocol: TCP
      name: cluster
      port: 6222
    - protocol: TCP
      name: leafnodes
      port: 7422
    - protocol: TCP
      name: gateways
      port: 7522
    - protocol: TCP
      name: metrics
      port: 7777
    - protocol: TCP
      name: monitor
      port: 8222
EOF
[ $? -eq 0 ] && log "nats manifest created" || log 1 "Failed to create nats manifest"

# configure nats
wait_for_nats
nats_user=$(kubectl -n ${kube_ns} get secret/nats-users \
  -o jsonpath="{.data.user}"|base64 --decode)
nats_pass=$(kubectl -n ${kube_ns} get secret/nats-users \
  -o jsonpath="{.data.pass}"|base64 --decode)
log "nats user: ${nats_user}"

kubectl -n $kube_ns get cm nats-config \
  -o jsonpath="{.data['nats\.conf']}" > ${homedir}/conf/nats.conf
[ $? -eq 0 ] && log "Exported nats.conf to ${homedir}/conf/nats.conf" \
  || log 1 "Failed to get nats configuration file"

cat <<EOF >${homedir}/conf/lfusers.json
{
  "leafnodes": {
    "port": 7422,
    "authorization": {
      "users": []
    }
  }
}
EOF

cat <<EOF >${homedir}/conf/accounts.json
{
  "accounts": {
    "swarm": {
      "users": [
        {
          "user": "${nats_user}",
          "password": "${nats_pass}"
        }
      ]
    }
  }
}
EOF

cat <<EOF >>${homedir}/conf/nats.conf
include "./lfusers.json"
include "./accounts.json"
EOF
log "Additional nats configuration files created"
kubectl -n $kube_ns create cm nats-config \
  --from-file ${homedir}/conf/nats.conf \
  --from-file ${homedir}/conf/lfusers.json \
  --from-file ${homedir}/conf/accounts.json \
  -o yaml --dry-run=client | kubectl replace -f - 2>&1 | tee -a $log
[ $? -eq 0 ] && log "nats configuration map updated" \
|| log 1 "Failed to update nats configuration map"

mv ${homedir}/conf/nats.conf ${homedir}/debug/nats.conf
mv ${homedir}/conf/lfusers.json ${homedir}/debug/lfusers.json
mv ${homedir}/conf/accounts.json ${homedir}/debug/accounts.json

kubectl -n $kube_ns delete po -l app=nats 2>&1 | tee -a $log
wait_for_nats
log "nats cluster configuration reloaded. ground nats cluster is ready."
exit 0
