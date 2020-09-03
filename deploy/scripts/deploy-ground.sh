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
iot_count=$4
groundstation_count=$5
port_number=8001

log "Deploying ${app}:${ver} ground station services in namespace:${kube_ns}..."
log "Number of IOT Sensors: ${iot_count}"

mkdir -p ${homedir}/${app}

deploy_service() {
  local svc=$1
  log "creating deployment files for $svc..."

  [[ ${svc} == iot* ]] && s=iot || s=${svc}

  local non_dashboard_cm=$(cat <<EOF
        - name: REDISPASS
          valueFrom:
            secretKeyRef:
              name: redis
              key: redisa
        - name: APIHOST
          valueFrom:
            configMapKeyRef:
              name: ${app}-${s}-cm
              key: apihost
EOF
  )

  if [[ ${svc} == dashboard ]]; then
    log "set port to 8080"
    port_number=8080
    log "setting non_dashboard cm to blank and command for dashboard"
    non_dashboard_cm=""
    container_args=$( cat <<EOF
        command:
        - "node"
        args:
        - "app.js"
        - -t \$(APIPORT)
        - -u \$(NATSUSER)
        - -p \$(NATSPASS)
EOF
    )
    dashboard_ing=$( cat <<EOF
---
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
  name: ${app}-${svc}-ing
  namespace: ${kube_ns}
  labels:
    ver: "1.0"
    app: ${app}
    msvc: ${svc}
spec:
  rules:
  - host: ${kube_ns}.kubesat.space
    http:
      paths:
      - path: /
        backend:
          serviceName: ${app}-${svc}
          servicePort: ${port_number}
EOF
    )
  else
    container_args=$( cat <<EOF
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
EOF
    )
  fi

  cat << EOF >${homedir}/${app}/${s}/${svc}_service.yaml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: ${app}-${s}-cm
  namespace: ${kube_ns}
  labels:
    ver: "${ver}"
    app: "${app}"
    msvc: "${s}"
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
      - name: "${svc}"
        image: "localhost:5000/${app}-${s}:${ver}"
        imagePullPolicy: Always
        env:
        - name: APIPORT
          valueFrom:
            configMapKeyRef:
              name: ${app}-${s}-cm
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
${non_dashboard_cm}
${container_args}
        ports:
        - containerPort: ${port_number}
${dashboard_ing}
---
EOF
  log "created deployment files for ${svc} at ${homedir}/${app}/$s/${svc}_service.yaml"
  log "deploying $svc"
  kubectl -n ${kube_ns} apply -f ${homedir}/${app}/$s/${svc}_service.yaml 2>&1 | tee -a $log
  [ $? -eq 0 ] && log "deployed $svc" \
    || log 1 "ERROR: Failed to deploy $svc. Exiting"
  wait_for_running_pods
  port_number=$(( $port_number + 1 ))
}

# untar
rm -rf ${homedir}/${app}/*
log "Untar from ${homedir}/ground_${ver}.tgz to ${homedir}/${app}/"
tar -C ${homedir}/${app}/ -xvzf ${homedir}/ground_${ver}.tgz
[ $? -eq 0 ] || log 1 "ERROR: Failed to extract app files tarball. Exiting"

# build and deploy
log "building utils container image..."
docker build -t localhost:5000/${app}-utils:${ver} ${homedir}/${app}/utils 2>&1 | tee -a $log
[ $? -eq 0 ] || log 1 "ERROR: Failed docker build for utils. Exiting"

log "push utils container image to local registry..."
docker push localhost:5000/${app}-utils:${ver} 2>&1 | tee -a $log
[ $? -eq 0 ] || log 1 "ERROR: Failed to push utils image to local registry. Exiting"

node_index=$(hostname|rev|cut -d- -f1)
if [ $iot_count -lt $groundstation_count ]; then
  iot_count=1
else
  on_each=$(( $iot_count/$groundstation_count ))
  on_first=$(( $iot_count%$groundstation_count ))
fi

if [ $node_index -eq 0 ]; then
# groundstation-1
  for svc in config logging groundstation iot czml clock dashboard; do
    sed -i "s/kubesat-utils.*/${app}-utils:${ver}/" ${homedir}/${app}/${svc}/Dockerfile

    log "building $svc container image..."
    docker build -t localhost:5000/${app}-${svc}:${ver} ${homedir}/${app}/${svc} 2>&1 | tee -a $log
    [ $? -eq 0 ] || log 1 "ERROR: Failed docker build for $svc. Exiting"

    log "push $svc container image to local registry..."
    docker push localhost:5000/${app}-${svc}:${ver} 2>&1 | tee -a $log
    [ $? -eq 0 ] || log 1 "ERROR: Failed to push $svc image to local registry. Exiting"

    if [[ $svc == iot ]]
    then
      if [ $iot_count -gt 1 ]; then
        # multiple iot sensors
        # first groundstation node will have on_each+on_first number of sensors
        iot_end=$(( on_each+on_first ))
        log "iot: generating different deployment files for each sensor..."
        log "node: ground station: $(hostname)"
        log "iot sensor count on this node: $(( iot_end ))"
        log "starting iot sensor: 1 ending iot sensor: $iot_end"

        for (( i=1; i <= $iot_end; i++ ))
        do
          deploy_service "iot$i"
        done
      elif [ $iot_coount -eq 1 ]; then
        # single iot sensor on first groundstation
        deploy_service "iot"
      fi
    else
      deploy_service $svc
    fi
  done

elif [ $node_index -gt 0 ]; then
  # second groundstaion or higher
  n_id=$(( node_index+1 ))

  for svc in groundstation iot; do
    sed -i "s/kubesat-utils.*/${app}-utils:${ver}/" ${homedir}/${app}/${svc}/Dockerfile

    log "building $svc container image..."
    docker build -t localhost:5000/${app}-${svc}:${ver} ${homedir}/${app}/${svc} 2>&1 | tee -a $log
    [ $? -eq 0 ] || log 1 "ERROR: Failed docker build for $svc. Exiting"

    log "push $svc container image to local registry..."
    docker push localhost:5000/${app}-${svc}:${ver} 2>&1 | tee -a $log
    [ $? -eq 0 ] || log 1 "ERROR: Failed to push $svc image to local registry. Exiting"

    if [[ $svc == iot ]]; then
      if [ $iot_count -gt 1 ]; then
        iot_begin=$(( $(( n_id-1 ))*on_each+on_first+1 ))
        iot_end=$(( $(( n_id*on_each ))+on_first ))
        log "iot: generating different deployment files for each sensor..."
        log "node: ground station: $(hostname)"
        log "iot sensor count on this node: $(( iot_end-iot_begin+1 ))"
        log "starting iot sensor: $iot_begin ending iot sensor: $iot_end"
        for (( i=$iot_begin; i <= $iot_end; i++ ))
        do
          deploy_service "iot$i"
        done
      fi
    else
      deploy_service $svc
    fi
  done

fi
log "KubeSat application ${app}:${ver} services deployment to groundstation complete."
log "Done"
