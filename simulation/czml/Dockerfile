FROM localhost:5000/kubesat-utils:1.0
COPY requirements.yaml .
RUN mkdir -p $HOME/orekit \
    && wget https://gitlab.orekit.org/orekit/orekit-data/-/archive/master/orekit-data-master.zip -O "$HOME/orekit-data.zip" \
    && conda env update  --name python38 --file requirements.yaml \
    && conda clean -a -f -y
WORKDIR /home/czml
ADD . .
CMD ["python", "run.py", "-c", "host.docker.internal", "-p", "orbit", "-f", "./", "-o", "6378"]
