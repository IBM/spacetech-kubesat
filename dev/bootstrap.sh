#!/bin/bash

kubesat_repo="/tmp/spacetech-kubesat"

# create kubesat conda env
cat <<EOF >${kubesat_repo}/dev/conda-manifest.yaml
channels:
  - anaconda
  - defaults
  - conda-forge
dependencies:
  - orekit==10.1
  - python==3.8.3
  - pip==20.1.1
  - pip:
    - pytest==5.4.3
    - jsonschema==3.2.0
    - aiologger==0.5.0
    - aiohttp==3.6.2
    - uvicorn==0.11.5
    - fastapi==0.58.1
    - asyncio-nats-client==0.10.0
    - redis==3.5.3
    - numpy==1.19.0
    - gym==0.17.2
    - tensorflow==2.2.0
    - keras-rl2==1.0.4
    - pandas==1.0.5
EOF

# create kubesat setup
cat <<EOF >${kubesat_repo}/dev/setup.sh
#!/bin/bash
apk update
apk --no-cache add git bash curl wget unzip tar git vim docker
echo "setting up conda environment..."
conda env create -n kubesat -f ${kubesat_repo}/dev/conda-manifest.yaml
[ $? -eq 0 ] && conda init bash
source /home/anaconda/.profile
conda activate kubesat
conda clean -afy
echo "downloading orekit data..."
mkdir -p \$HOME/orekit
wget https://gitlab.orekit.org/orekit/orekit-data/-/archive/master/orekit-data-master.zip -O "\$HOME/orekit-data.zip"
EOF

# run kubesat
cat <<EOF >${kubesat_repo}/dev/run-kubesat.sh
#!/bin/bash

kubesat_repo=${kubesat_repo}

sats_count=1
iot_count=1
ground_count=1

pkill python

docker stop dev-redis
docker rm dev-redis
docker run -d --name dev-redis -p 6379:6379 redis
redis=\$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' dev-redis)

docker stop dev-nats
docker rm dev-nats
docker run -d --name dev-nats -p 4222:4222 nats
nats=\$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' dev-nats)

cd \${kubesat_repo}/utils && python setup.py install
simhost=\$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' dev-kubesat)
port=8001

start_svc() {
  echo "Starting service \$1..."
  cd \${kubesat_repo}/\$1 && nohup python -u run.py -a \$simhost -s \$nats -d \$redis -t \$port > \${kubesat_repo}/dev/\$1.log &
  echo "\$! \$1"
  port=\$(( port+ 1 )) && sleep 5
}

for s in config logging czml; do
  start_svc \$s
done

for (( i=1; i <= \$iot_count; i++ )) ; do
  start_svc "iot"
done

for (( i=1; i <= \$ground_count; i++ )) ; do
  start_svc "groundstation"
done

for (( i=1; i <= \$sats_count; i++ )) ; do
  start_svc "orbits"
  start_svc "data"
  start_svc "rl"
  start_svc "agriculture"
  start_svc "cluster"
  start_svc "rl-training"
done

# dashboard service
dashboard_imgid=\$(docker images -q kubesat-dashboard:1.0)
[[ -n "\$dashboard_imgid" ]] || \
docker build \${kubesat_repo}/dashboard -t kubesat-dashboard:1.0
docker stop dev-dashboard
docker rm dev-dashboard
docker run -d --name dev-dashboard -p 8080:8080 kubesat-dashboard:1.0 node app.js -s \$nats

# clock service
start_svc "clock"
EOF

# create dockerfile
cat <<EOF >${kubesat_repo}/dev/Dockerfile
FROM continuumio/miniconda3:4.8.2-alpine
USER root
WORKDIR ${kubesat_repo}
EXPOSE 8080
ENV PYTHONDONTWRITEBYTECODE=true
ENV PATH \$PATH:/opt/conda/condabin
EOF

# build
docker build -t dev-kubesat:1.0 ${kubesat_repo}/dev
docker stop dev-kubesat
docker rm dev-kubesat
docker run --name dev-kubesat -td \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ${kubesat_repo}:${kubesat_repo} dev-kubesat:1.0
echo "Run setup..."
docker exec -it dev-kubesat sh ${kubesat_repo}/dev/setup.sh
echo "kubesat dev environment successfully bootstrapped."
echo "Run following commands to run kubesat from dev-kubesat container"
echo "docker exec -it dev-kubesat /bin/bash"
echo "conda activate kubesat && bash dev/run-kubesat.sh"
