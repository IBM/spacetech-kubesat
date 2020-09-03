FROM localhost:5000/kubesat-utils:1.0
WORKDIR /home/iot
COPY . .
CMD ["python", "run.py", "-c", "host.docker.internal", "-p", "orbit"]
