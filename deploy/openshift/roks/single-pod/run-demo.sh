#!/bin/bash

app=kubesat
svc=demo
ver="1.0"
repo=ibmkubesat
ns="$app-$svc"

# usage
usage() {
  cat <<USG
Usage: bash \$0 [OPTIONS]
  OPTIONS:
  -c|--cubesat-count  Number of cubesats in demo swarm
                      Recommended between 1 and 5
  -g|--ground-count   Number of ground stations
                      Recommended between 1 and 2
  -i|--iot-count      Number of iot sensors
                      Recommended between 1 and 5
  -n|--dns-name       DNS Name to use to launch demo
  -h|--help)          Usage/help
  (no args)           Use default settings
                      Redis and NATS on localhost
                      1 cubesat, 1 ground-station, 1 iot-sensor
USG
}

# defaults
sat_count=1
ground_count=1
iot_count=1
dns_name=''

# parse options
while (( "$#" )); do
  case "$1" in
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

echo "cubesat count:  $sat_count" |tee -a $log
echo "ground count:   $ground_count" |tee -a $log
echo "iot-sensors:    $iot_count" |tee -a $log

oc delete namespace $ns 2>/dev/null
oc create namespace $ns 2>/dev/null
oc project $ns 2>/dev/null
oc adm policy add-scc-to-user anyuid -z default -n $ns >/dev/null
cat <<EOF >kubesat-demo.yaml
---
apiVersion: v1
kind: Pod
metadata:
  name: "${app}"
  namespace: "${app}-${svc}"
  labels:
    app: "${app}"
    svc: "${svc}"
    ver: "${ver}"
spec:
  containers:
  - name: redis
    image: redis
    ports:
      - containerPort: 6379
  - name: nats
    image: nats
    ports:
      - containerPort: 4222
  - name: "sim"
    image: "${repo}/${app}-${svc}:${ver}"
    imagePullPolicy: Always
    command:
    - bash
    args:
    - "/opt/kubesat/run-kubesat.sh"
    - "-d"
    - "localhost"
    - "-s"
    - "localhost"
    - "-c"
    - "1"
    - "-g"
    - "1"
    - "-i"
    - "1"
  - name: "dashboard"
    image: "${repo}/${app}-dashboard:1.0"
    imagePullPolicy: Always
    ports:
      - containerPort: 8080
    command:
      - node
    args:
      - app.js
      - -s
      - localhost
---
apiVersion: v1
kind: Service
metadata:
  name: "${app}"
  namespace: "${app}-${svc}"
  labels:
    app: "${app}"
    svc: "${svc}"
    ver: "${ver}"
spec:
  type: ClusterIP
  selector:
    app: "${app}"
    svc: "${svc}"
    ver: "${ver}"
  ports:
    - protocol: TCP
      port: 8080
      targetPort: 8080
---
kind: Route
apiVersion: route.openshift.io/v1
metadata:
  name: "${app}"
  namespace: "${app}-${svc}"
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
    name: "${app}"
    weight: 100
  port:
    targetPort: 8080
  wildcardPolicy: None
EOF

oc apply -f kubesat-demo.yaml

echo "${app} pod starting..." |tee -a $log
i=0; sleep 50;
while [ -z "$(oc exec -it po/${app} -c sim -- \
cat /tmp/run-kubesat.log | tail -n 1 | \
grep 'kubesat started')" ]; do
  if [ $i -ge 20 ]; then
    echo "${app} pod did not start" |tee -a $log
    exit
  else
    i=$((i+1))
    echo "${app} pod starting..." |tee -a $log
    sleep 25
  fi
done
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
