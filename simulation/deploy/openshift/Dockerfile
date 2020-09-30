FROM continuumio/miniconda3:4.8.2-alpine
USER root
WORKDIR /opt/kubesat
RUN apk update && apk --no-cache add bash wget git
SHELL ["/bin/bash", "-c"]
ENV PYTHONDONTWRITEBYTECODE=true
ENV PATH $PATH:/opt/conda/condabin
RUN git clone https://github.com/IBM/spacetech-kubesat --branch master --single-branch /opt/kubesat/
COPY env.yaml env.yaml
COPY run.sh run.sh
RUN conda env create -n kubesat -f env.yaml && conda clean -afy
ENV PATH /opt/conda/envs/kubesat/bin/:$PATH
RUN mkdir -p $HOME/orekit && wget https://gitlab.orekit.org/orekit/orekit-data/-/archive/master/orekit-data-master.zip -O "$HOME/orekit-data.zip"
RUN cd utils && python setup.py install
