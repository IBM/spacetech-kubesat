## Build KubeSat

Run build script to build and upload container images for kubesat and kubesat-dashboard. Set the image-registry and image-tag arguments to host container images in your repo.

```bash
bash build.sh [--image-registry <name/url>] [--image-tag <tag>]
```

## Deploy KubeSat to OpenShift

KubeSat application can be deployed to any OpenShift cluster, including CRC and RedHat OpenShift Kubernetes Service in IBM Cloud.

Log in to OpenShift cluster
```sh
oc login
```

Deploy with default options
```bash
bash deploy.sh
```

Deploy with custom options
```
OPTIONS:
-s|--nats-server    NATS server hostname/ip-address
-d|--redis-server   REDIS server hostname/ip-address
-c|--cubesat-count  Number of cubesats in demo swarm
                    Recommended between 1 and 5
-g|--ground-count   Number of ground stations
                    Recommended between 1 and 2
-i|--iot-count      Number of iot sensors
                    Recommended between 1 and 5
-n|--dns-name       DNS Name to use to launch demo
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
```
```sh
bash deploy.sh [ OPTIONS ]
```


If DNS name was used, create CNAME record pointing to the canonical hostname of the default router in your OpenShift cluster. And go to the DNS name to launch the dashboard.

If DNS name was not used, go to the Route url to launch the dashboard.
