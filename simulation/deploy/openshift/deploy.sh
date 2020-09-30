#!/bin/bash

# usage
usage() {
  cat <<USG
Usage: bash \$0 [OPTIONS]
  OPTIONS:
  -s|--nats-server    NATS server hostname/ip-address
  -d|--redis-server   REDIS server hostname/ip-address
  -c|--cubesat-count  Number of cubesats
                      Recommended between 1 and 5
  -g|--ground-count   Number of ground stations
                      Recommended between 1 and 2
  -i|--iot-count      Number of iot sensors
                      Recommended between 1 and 5
  -n|--dns-name       DNS Name to use to launch dashboard
  -p|--ocp-project    Target OpenShift project (default: kubesat-tmp)
  -r|--image-registry Container registry name/url
  -t|--image-tag      Container image tag
  -h|--help)          Usage/help
  (no args)           Use default settings
                      OpenShift project: kubesat-tmp
                      Redis: redis.kubesat-tmp.svc.cluster.local
                      NATS:  nats
                      Container image: ibmkubesat/kubesat:1.0
                      1 cubesat, 1 ground-station, 1 iot-sensor
USG
}

# defaults
repo=ibmkubesat
app=kubesat
ver="1.0"
ns="kubesat-tmp"
sat_count=1
ground_count=1
iot_count=1
dns_name=''

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
    -c|--cubesat-count)
      sat_count=$2
      shift 2
      ;;
    -g|--ground-count)
      ground_count=$2
      shift 2
      ;;
    -i|--iot-count)
      iot_count=$2
      shift 2
      ;;
    -n|--dns-name)
      dns_name=$2
      shift 2
      ;;
    -p|--ocp-project)
      ns=$2
      shift 2
      ;;
    -r|--image-registry)
      repo=$2
      shift 2
      ;;
    -t|--image-tag)
      ver=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit
      ;;
    *)
      echo -e "Error. Invalid arg(s)" |tee -a $log
      usage
      exit 1
      ;;
  esac
done

[ -z "${redis}" ] && redis="redis.${ns}.svc.cluster.local"
[ -z "${nats}" ] && nats="nats.${ns}.svc.cluster.local"
echo "redis host:     ${redis}" |tee -a $log
echo "nats host:      ${nats}" |tee -a $log
echo "cubesat count:  $sat_count" |tee -a $log
echo "ground count:   $ground_count" |tee -a $log
echo "iot-sensors:    $iot_count" |tee -a $log

# begin
echo "Start deployment..."
oc delete namespace $ns 2>/dev/null
sleep 55
oc create namespace $ns 2>/dev/null
oc project $ns 2>/dev/null
oc adm policy add-scc-to-user anyuid -z default -n $ns >/dev/null
oc run redis --image=redis --port=6379 --expose=true 2>/dev/null
oc run nats --image=nats --port=4222 --expose=true 2>/dev/null

# deploy service
deploy() {
  oc apply -f $1.yaml
  echo "${app}-${svc} resource(s) starting..." |tee -a $log
  j=0; sleep 50;
  local po=$(oc get po -l app=${app},svc=${svc} | \
  tail -n 1 | awk '{print $1}')
  while [ -z "$(oc exec -it po/${po} -- \
  cat /tmp/run.log | tail -n 1 | \
  grep 'Done')" ]; do
    if [ $j -ge 20 ]; then
      echo "${app}-${svc} resource(s) did not start" |tee -a $log
      exit
    else
      j=$((j+1))
      echo "${app}-${svc} resource(s) starting..." |tee -a $log
      sleep 25
    fi
  done
  sleep 20
  rm $1.yaml
  echo "${app}-${svc} deployment completed" |tee -a $log
}

# dashboard
deploy_dashboard() {
  local svc='dashboard'
  cat <<EOF >$svc.yaml
---
apiVersion: v1
kind: Service
metadata:
  name: "${app}-${svc}"
  namespace: "${ns}"
  labels:
    ver: "${ver}"
    app: "${app}"
    svc: "${svc}"
spec:
  type: ClusterIP
  selector:
    app: "${app}"
    svc: "${svc}"
    ver: "${ver}"
  ports:
    - name: "dashboard"
      protocol: TCP
      port: 8080
      targetPort: 8080
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: "${app}-${svc}"
  namespace: "${ns}"
  labels:
    ver: "${ver}"
    app: "${app}"
    svc: "${svc}"
spec:
  selector:
    matchLabels:
      ver: "${ver}"
      app: "${app}"
      svc: "${svc}"
  replicas: 1
  template:
    metadata:
      labels:
        ver: "${ver}"
        app: "${app}"
        svc: "${svc}"
    spec:
      containers:
      - name: "${svc}"
        image: "${repo}/${app}-${svc}:${ver}"
        imagePullPolicy: Always
        ports:
          - containerPort: 8080
        command:
          - node
        args:
          - app.js
          - -s
          - nats.${ns}.svc.cluster.local
---
kind: Route
apiVersion: route.openshift.io/v1
metadata:
  name: "${app}"
  namespace: "${ns}"
  labels:
    app: "${app}"
    svc: "${svc}"
    ver: "${ver}"
  annotations:
    openshift.io/host.generated: 'true'
spec:
  host: "${dns_name}"
  to:
    kind: Service
    name: "${app}-${svc}"
    weight: 100
  port:
    targetPort: 8080
  wildcardPolicy: None
EOF
oc apply -f ${svc}.yaml
sleep 50
rm ${svc}.yaml
echo "dashboard deployment complete" |tee -a $log
}

# cubesats
# services: orbits, data, rl, agriculture
deploy_cs() {
  local svc="cs"
  for (( i=1; i <= $sat_count; i++ )); do
    svc="$svc$i"
    cat <<EOF >${svc}.yaml
---
apiVersion: v1
kind: Service
metadata:
  name: "${app}-${svc}"
  namespace: "${ns}"
  labels:
    ver: "${ver}"
    app: "${app}"
    svc: "${svc}"
spec:
  type: ClusterIP
  selector:
    app: "${app}"
    svc: "${svc}"
    ver: "${ver}"
  ports:
    - name: "orbits"
      protocol: TCP
      port: 8001
      targetPort: 8001
    - name: "data"
      protocol: TCP
      port: 8002
      targetPort: 8002
    - name: "rl"
      protocol: TCP
      port: 8003
      targetPort: 8003
    - name: "agriculture"
      protocol: TCP
      port: 8004
      targetPort: 8004
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: "${app}-${svc}"
  namespace: "${ns}"
  labels:
    ver: "${ver}"
    app: "${app}"
    svc: "${svc}"
spec:
  selector:
    matchLabels:
      ver: "${ver}"
      app: "${app}"
      svc: "${svc}"
  replicas: 1
  template:
    metadata:
      labels:
        ver: "${ver}"
        app: "${app}"
        svc: "${svc}"
    spec:
      containers:
      - name: "${svc}"
        image: "${repo}/${app}:${ver}"
        imagePullPolicy: Always
        ports:
        - containerPort: 8001
        - containerPort: 8002
        - containerPort: 8003
        - containerPort: 8004
        command:
        - bash
        args:
        - "/opt/kubesat/run.sh"
        - "-d"
        - "redis.${ns}.svc.cluster.local"
        - "-s"
        - "nats.${ns}.svc.cluster.local"
        - "-a"
        - "${app}-${svc}.${ns}.svc.cluster.local"
        - "-t"
        - "cs"
EOF
  deploy ${svc}
  svc='cs'
  done
}

# iot sensors
deploy_iot() {
  local svc='iot'
  for (( i=1; i <= $iot_count; i++ )); do
    svc="$svc$i"
    cat <<EOF >${svc}.yaml
---
apiVersion: v1
kind: Service
metadata:
  name: "${app}-${svc}"
  namespace: "${ns}"
  labels:
    ver: "${ver}"
    app: "${app}"
    svc: "${svc}"
spec:
  type: ClusterIP
  selector:
    app: "${app}"
    svc: "${svc}"
    ver: "${ver}"
  ports:
    - name: "iot"
      protocol: TCP
      port: 8001
      targetPort: 8001
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: "${app}-${svc}"
  namespace: "${ns}"
  labels:
    ver: "${ver}"
    app: "${app}"
    svc: "${svc}"
spec:
  selector:
    matchLabels:
      ver: "${ver}"
      app: "${app}"
      svc: "${svc}"
  replicas: 1
  template:
    metadata:
      labels:
        ver: "${ver}"
        app: "${app}"
        svc: "${svc}"
    spec:
      containers:
      - name: "${svc}"
        image: "${repo}/${app}:${ver}"
        imagePullPolicy: Always
        ports:
        - containerPort: 8001
        command:
        - bash
        args:
        - "/opt/kubesat/run.sh"
        - "-d"
        - "redis.${ns}.svc.cluster.local"
        - "-s"
        - "nats.${ns}.svc.cluster.local"
        - "-a"
        - "${app}-${svc}.${ns}.svc.cluster.local"
        - "-t"
        - "iot"
EOF
  deploy ${svc}
  svc='iot'
  done
}

# ground-stations
deploy_gs() {
  local svc='gs'
  for (( i=1; i <= $ground_count; i++ )); do
    svc="$svc$i"
    cat <<EOF >${svc}.yaml
---
apiVersion: v1
kind: Service
metadata:
  name: "${app}-${svc}"
  namespace: "${ns}"
  labels:
    ver: "${ver}"
    app: "${app}"
    svc: "${svc}"
spec:
  type: ClusterIP
  selector:
    app: "${app}"
    svc: "${svc}"
    ver: "${ver}"
  ports:
    - name: "groundstation"
      protocol: TCP
      port: 8001
      targetPort: 8001
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: "${app}-${svc}"
  namespace: "${ns}"
  labels:
    ver: "${ver}"
    app: "${app}"
    svc: "${svc}"
spec:
  selector:
    matchLabels:
      ver: "${ver}"
      app: "${app}"
      svc: "${svc}"
  replicas: 1
  template:
    metadata:
      labels:
        ver: "${ver}"
        app: "${app}"
        svc: "${svc}"
    spec:
      containers:
      - name: "${svc}"
        image: "${repo}/${app}:${ver}"
        imagePullPolicy: Always
        ports:
        - containerPort: 8001
        command:
        - bash
        args:
        - "/opt/kubesat/run.sh"
        - "-d"
        - "redis.${ns}.svc.cluster.local"
        - "-s"
        - "nats.${ns}.svc.cluster.local"
        - "-a"
        - "${app}-${svc}.${ns}.svc.cluster.local"
        - "-t"
        - "gs"
EOF
  deploy ${svc}
  svc='gs'
  done
}

# simulation services
# config, logging, czml, cluster, clock
deploy_sim() {
  local svc='sim'
  cat <<EOF >${svc}.yaml
---
apiVersion: v1
kind: Service
metadata:
  name: "${app}-${svc}"
  namespace: "${ns}"
  labels:
    ver: "${ver}"
    app: "${app}"
    svc: "${svc}"
spec:
  type: ClusterIP
  selector:
    app: "${app}"
    svc: "${svc}"
    ver: "${ver}"
  ports:
    - name: "config"
      protocol: TCP
      port: 8001
      targetPort: 8001
    - name: "logging"
      protocol: TCP
      port: 8002
      targetPort: 8002
    - name: "czml"
      protocol: TCP
      port: 8003
      targetPort: 8003
    - name: "cluster"
      protocol: TCP
      port: 8004
      targetPort: 8004
    - name: "clock"
      protocol: TCP
      port: 8005
      targetPort: 8005
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: "${app}-${svc}"
  namespace: "${ns}"
  labels:
    ver: "${ver}"
    app: "${app}"
    svc: "${svc}"
spec:
  selector:
    matchLabels:
      ver: "${ver}"
      app: "${app}"
      svc: "${svc}"
  replicas: 1
  template:
    metadata:
      labels:
        ver: "${ver}"
        app: "${app}"
        svc: "${svc}"
    spec:
      containers:
      - name: "${svc}"
        image: "${repo}/${app}:${ver}"
        imagePullPolicy: Always
        ports:
        - containerPort: 8001
        - containerPort: 8002
        - containerPort: 8003
        - containerPort: 8004
        - containerPort: 8005
        command:
        - bash
        args:
        - "/opt/kubesat/run.sh"
        - "-d"
        - "redis.${ns}.svc.cluster.local"
        - "-s"
        - "nats.${ns}.svc.cluster.local"
        - "-a"
        - "${app}-${svc}.${ns}.svc.cluster.local"
        - "-t"
        - "sim"
EOF
deploy ${svc}
}

deploy_sim
deploy_gs
deploy_iot
deploy_cs
deploy_dashboard

if [ -z "${dns_name}" ]; then
  d_url=$(oc get route ${app} -o yaml|grep 'host:'|\
  tail -n 1|cut -d: -f2|sed 's/ //g')
  echo "${app}-${svc} deployed to http://${d_url}"
else
  echo "Create CNAME record for ${dns_name} \
pointing to $(oc get route ${app} -o yaml | \
grep -i canonical|awk '{print $NF}')"
fi
echo "Done" |tee -a $log
exit
echo "kubesat deployment complete"
