FROM ubuntu
ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"
RUN apt-get update \
    && apt-get install -y wget \
    && rm -rf /var/lib/apt/lists/* \
    && wget \
    https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh
COPY conda-env.yaml .
RUN conda env create -n python38 -f conda-env.yaml \
    && conda clean -a -f -y
COPY . .
ENV PATH /root/miniconda3/envs/python38/bin:$PATH
RUN python setup.py install