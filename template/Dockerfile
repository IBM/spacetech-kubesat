FROM kubesat-utils:1.0
WORKDIR /home/template
COPY . .
CMD ["python", "run.py", "-c", "host.docker.internal", "-o", "4222", "-u", "a", "-p", "b", "-r", "6378", "-e", "host.docker.internal"]