FROM localhost:5000/kubesat-utils:1.0
WORKDIR /home/orbit
ADD . .
RUN mkdir -p $HOME/orekit \
    && wget https://gitlab.orekit.org/orekit/orekit-data/-/archive/master/orekit-data-master.zip -O "$HOME/orekit-data.zip" \
    && conda env update  --name python38 --file requirements.yaml \
    && conda clean -a -f -y
CMD ["python", "run.py"]
