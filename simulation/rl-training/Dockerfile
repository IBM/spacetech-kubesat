FROM localhost:5000/kubesat-utils:1.0
WORKDIR /home/rl
ADD requirements.yaml .
RUN conda env update  --name python38 --file requirements.yaml
ADD . .
CMD ["python", "run.py"]
