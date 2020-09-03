#!/bin/bash

# service checker
wait_for_running_pods() {
  local i=0
  local sts=""
  while [ "Running" != "${sts}" ]
  do
    log "Waiting for ${svc} pods to start..."
    sleep 10
    if [ $i -ge 12 ]; then
      log 1 "${svc} pods did not start"
    else
      sts=$(kubectl -n ${kube_ns} get po -l app=${app},msvc=${svc},ver=${ver} \
      | tail -n 1 | awk '{ print $3 }')
      log "${svc} pods status: ${sts}"
      i=$((i+1))
    fi
  done
  log "${svc} pods started"
}

homedir="$(dirname $0)/.."
mkdir -p ${homedir}/logs
log="${homedir}/logs/$(basename -s .sh ${0}).log"
>$log
. ${homedir}/scripts/logger.sh
log "Log file: ${log}"

kube_ns=$1
app=$2
ver=$3
port_number=8001

log "Deploying ${app}:${ver} swarm node services in namespace:${kube_ns}..."

mkdir -p ${homedir}/${app}

deploy_service() {
  log "creating deployment files for $svc..."
  cat << EOF >${homedir}/${app}/${svc}/${svc}_service.yaml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: ${app}-${svc}-cm
  namespace: ${kube_ns}
  labels:
    ver: "${ver}"
    app: "${app}"
    msvc: "${svc}"
data:
  apihost: $(hostname -I | cut -d' ' -f1)
  apiport: "${port_number}"

---
apiVersion: v1
kind: Service
metadata:
  name: ${app}-${svc}
  namespace: ${kube_ns}
  labels:
    ver: "${ver}"
    app: "${app}"
    msvc: "${svc}"
spec:
  type: LoadBalancer
  ports:
  - port: ${port_number}
    targetPort: ${port_number}
  selector:
    ver: "${ver}"
    app: "${app}"
    msvc: "${svc}"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${app}-${svc}
  namespace: ${kube_ns}
  labels:
    ver: "${ver}"
    app: "${app}"
    msvc: "${svc}"
spec:
  selector:
    matchLabels:
      ver: "${ver}"
      app: "${app}"
      msvc: "${svc}"
  replicas: 1
  template:
    metadata:
      labels:
        ver: "${ver}"
        app: "${app}"
        msvc: "${svc}"
    spec:
      containers:
      - name: ${svc}
        image: "localhost:5000/${app}-${svc}:${ver}"
        imagePullPolicy: Always
        env:
        - name: APIPORT
          valueFrom:
            configMapKeyRef:
              name: ${app}-${svc}-cm
              key: apiport
        - name: NATSUSER
          valueFrom:
            secretKeyRef:
              name: nats-users
              key: user
        - name: NATSPASS
          valueFrom:
            secretKeyRef:
              name: nats-users
              key: pass
        - name: REDISPASS
          valueFrom:
            secretKeyRef:
              name: redis
              key: redisa
        - name: APIHOST
          valueFrom:
            configMapKeyRef:
              name: ${app}-${svc}-cm
              key: apihost
        command:
        - "python"
        args:
        - "-u"
        - "run.py"
        - -t \$(APIPORT)
        - -u \$(NATSUSER)
        - -p \$(NATSPASS)
        - -a \$(APIHOST)
        - -r \$(REDISPASS)
        ports:
        - containerPort: ${port_number}
---
EOF
  log "created deployment files for $svc at ${homedir}/${app}/$svc/${svc}_service.yaml"
  log "deploying $svc..."
  kubectl -n ${kube_ns} apply -f ${homedir}/${app}/${svc}/${svc}_service.yaml 2>&1 | tee -a $log
  port_number=$(( $port_number + 1 ));
  [ $? -eq 0 ] && log "deployed $svc" \
    || log 1 "ERROR: Failed to deploy $svc. Exiting"
    wait_for_running_pods
}

# untar
rm -rf ${homedir}/${app}/*
log "Untar from ${homedir}/swarm_${ver}.tgz to ${homedir}/${app}/"
tar -C ${homedir}/${app}/ -xvzf ${homedir}/swarm_${ver}.tgz
[ $? -eq 0 ] || log 1 "ERROR: Failed to extract app files from tarball. Exiting"

# build and deploy
log "building utils container image..."
docker build -t localhost:5000/${app}-utils:${ver} ${homedir}/${app}/utils 2>&1 | tee -a $log
[ $? -eq 0 ] || log 1 "ERROR: Failed docker build for utils. Exiting"

log "push utils container image to local registry..."
docker push localhost:5000/${app}-utils:${ver} 2>&1 | tee -a $log
[ $? -eq 0 ] || log 1 "ERROR: Failed to push utils image to local registry. Exiting"

for svc in orbits data rl "rl-training" agriculture; do
  sed -i "s/kubesat-utils.*/${app}-utils:${ver}/" ${homedir}/${app}/${svc}/Dockerfile

  log "building $svc container image..."
  docker build -t localhost:5000/${app}-${svc}:${ver} ${homedir}/${app}/${svc} 2>&1 | tee -a $log
  [ $? -eq 0 ] || log 1 "ERROR: Failed docker build for $svc. Exiting"

  log "push $svc container image to local registry..."
  docker push localhost:5000/${app}-${svc}:${ver} 2>&1 | tee -a $log
  [ $? -eq 0 ] || log 1 "ERROR: Failed to push $svc image to local registry. Exiting"

  deploy_service
done
log "KubeSat application ${app}:${ver} services deployment to swarm node complete."
log "Done"
