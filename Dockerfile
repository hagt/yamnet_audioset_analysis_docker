FROM tensorflow/tensorflow:2.3.0
LABEL maintainer="henning.agt@gmail.com"

RUN apt-get update && apt-get install -y libsndfile1 git ffmpeg && apt-get autoclean && apt-get autoremove && rm -rf /var/lib/apt/lists/*

COPY requirements_yamnet.txt /requirements_yamnet.txt
RUN python -m pip install --upgrade pip && pip install --trusted-host pypi.python.org -r /requirements_yamnet.txt

RUN git clone https://github.com/tensorflow/models.git && mv models/research/audioset/yamnet/ yamnet/ && rm -r models/

WORKDIR /yamnet
RUN curl -O https://storage.googleapis.com/audioset/yamnet.h5

COPY yamnet_processing.py yamnet_processing.py

ENTRYPOINT ["python", "-u", "./yamnet_processing.py"]

