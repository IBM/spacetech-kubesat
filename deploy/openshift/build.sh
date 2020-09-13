#!/bin/bash

log="build.log"
>$log

# usage
usage() {
  cat <<USG
Usage: bash $0 [OPTIONS]
  OPTIONS:
  -r|--image-registry   image registry name/url
  -t|--image-tag        REDIS server hostname/ip-address
  -h|--help             Show help/usage
USG
}

# default values
repo="ibmkubesat"
tag="1.0"
app="kubesat"
svc="dashboard"

# parse options
while (( "$#" )); do
  case "$1" in
    -r|--image-registry)
      repo="$2"
      shift 2
      ;;
    -t|--image-tag)
      tag="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo -e "Error. Invalid arg(s)" |tee -a $log
      usage
      exit 1
      ;;
  esac
done

docker login -u ${repo}

app_img="${repo}/${app}:${tag}"
svc_img="${repo}/${app}-${svc}:${tag}"

docker build -t ${app_img} .
echo "container image ${app_img} created" |tee -a $log

docker push ${app_img}
echo "container image ${app_img} pushed" |tee -a $log

docker build -t ${svc_img} -f ${svc}.Dockerfile .
echo "container image ${svc_img} created" |tee -a $log
docker push ${svc_img}
echo "container image ${svc_img} pushed" |tee -a $log

echo "Done" |tee -a $log
