#!/bin/bash

log="build.log"
>$log

ver="1.0"
app="kubesat"
img="ibmkubesat/${app}:${ver}-demo"

build_and_push_image() {
  docker build -t ${img} .
  echo "docker image $img created" |tee -a $log
  docker login -u ibmkubesat
  docker push $img
}

build_files() {
  # create kubesat conda env
  cat <<EOF >conda-env.yaml
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
  echo "conda env manifest created" |tee -a $log

  # create run-kubesat
  cat <<EOF >run-kubesat.sh
#!/bin/bash

log="/tmp/run-kubesat.log"
>log
kubesat="/opt/kubesat"

# usage
usage() {
  cat <<USG
Usage: bash \$0 [OPTIONS]
  OPTIONS:
  -s|--nats-server    NATS server hostname/ip-address
  -d|--redis-server   REDIS server hostname/ip-address
  -a|--api-host       Service name for this node
  -t|--node-type      Node type. Valid values: sim, gs, iot, cs
                      sim: config, logging
                           czml, cluster, clock
                      gs:  groundstation
                      iot: iot
                      cs:  orbits, data, rl, agriculture
USG
}

# parse options
if [ \$# -eq 0 ]; then
  echo "Missing args" |tee -a \$log
  usage
  exit
else
  while (( "\$#" )); do
    case "\$1" in
      -s|--nats-server)
        nats="\$2"
        shift 2
        ;;
      -d|--redis-server)
        redis="\$2"
        shift 2
        ;;
      -t|--node-type)
        node_type=\$2
        shift 2
        ;;
      -a|--api-host)
        api_host=\$2
        shift 2
        ;;
      *)
        echo -e "Error. Invalid arg(s)" |tee -a \$log
        usage
        exit 1
        ;;
    esac
  done
fi

port=8001

echo "kubesat host:   \${sim}" |tee -a \$log
echo "redis host:     \${redis}" |tee -a \$log
echo "nats host:      \${nats}" |tee -a \$log
echo "api host:      \${api_host}" |tee -a \$log
echo "node type:      \${node_type}" |tee -a \$log

pkill python

svcs=""
case "\${node_type}" in
  sim)
    svcs="config logging czml cluster clock"
    ;;
  gs)
    svcs="groundstation"
    ;;
  iot)
    svcs="iot"
    ;;
  cs)
    svcs="orbits data rl agriculture"
    ;;
esac

# start kubesat services
start_svc() {
  echo "Starting \$1..." |tee -a \$log
  cd \${kubesat}/\$1 && nohup python -u run.py -a \$api_host -s \$nats -d \$redis -t \$port > /tmp/\$1.log &
  echo "\$! \$1" |tee -a \$log
  port=\$(( port+ 1 )) && sleep 10
}

for s in \${svcs}; do
  start_svc \$s
done

echo "Done. Logs available in /tmp folder" |tee -a \$log
while true; do sleep 50; done
EOF

  # create Dockerfile
  cat <<EOF >Dockerfile
FROM continuumio/miniconda3:4.8.2-alpine
USER root
WORKDIR /opt/kubesat
RUN apk update && \
    apk --no-cache add bash wget tar unzip git vim
SHELL ["/bin/bash", "-c"]
ENV PYTHONDONTWRITEBYTECODE=true
ENV PATH \$PATH:/opt/conda/condabin
RUN git clone https://github.com/IBM/spacetech-kubesat \
    --branch master --single-branch /opt/kubesat/
COPY conda-env.yaml conda-env.yaml
RUN conda env create -n kubesat -f conda-env.yaml
ENV PATH /opt/conda/envs/kubesat/bin/:\$PATH
RUN mkdir -p \$HOME/orekit && \
    wget https://gitlab.orekit.org/orekit/orekit-data/-/archive/master/orekit-data-master.zip \
    -O "\$HOME/orekit-data.zip"
COPY run-kubesat.sh run-kubesat.sh
RUN cd utils && python setup.py install
EOF
  echo "kubesat demo Dockerfile created" |tee -a $log
}

# begin
build_files
build_and_push_image
#rm Dockerfile conda-env.yaml run-kubesat.sh
echo "kubesat-demo image build complete." |tee -a $log
