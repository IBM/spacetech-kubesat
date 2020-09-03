#!/bin/bash
kube_ns=swarm
port_number=8001
svc_name=clock
cat << EOF >${svc_name}-service.yaml
---
apiVersion: apps/v1 
kind: Deployment
metadata:
  name: ${svc_name} 
  namespace: ${kube_ns}
  labels:
    app: cubesat
    msvce: ${svc_name}
spec:
  selector:
    matchLabels:
      app: cubesat
      msvce: ${svc_name}
  replicas: 1
  template:
    metadata:
      labels:
        app: cubesat
        msvce: ${svc_name}
    spec:
      containers:
      - name: config-container
        image: localhost:5000/${svc_name}-service:1.0
        imagePullPolicy: Always
        env:
        - name: APIHOST
          valueFrom:
            configMapKeyRef:
              name: ${svc_name}-cm
              key: apihost
        - name: APIPORT
          valueFrom:
            configMapKeyRef:
              name: ${svc_name}-cm
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
        command:
        - "python"
        args:
        - "run.py"
        - -a \$(APIHOST)
        - -t \$(APIPORT)
        - -u \$(NATSUSER)
        - -p \$(NATSPASS)
        - -r \$(REDISPASS)
        ports:
        - containerPort: ${port_number}
---
apiVersion: v1
kind: Service
metadata:
  name: ${svc_name}-service
  namespace: ${kube_ns}
  labels:
    app: cubesat
    msvce: ${svc_name}
spec:
  type: LoadBalancer
  ports:
  - port: ${port_number}
    targetPort: ${port_number}
  selector:
    app: cubesat
    msvce: ${svc_name}
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: ${svc_name}-cm
  namespace: ${kube_ns}
  labels:
    app: cubesat
    msvce: ${svc_name}
data:
  apihost: $(hostname)
  apiport: "${port_number}"
---
EOF
kubectl -n ${kube_ns} apply -f ${svc_name}-service.yaml