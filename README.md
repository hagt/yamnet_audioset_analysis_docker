# Docker Image for YAMNet audio analysis

This repository contains the sources for creating a ready-to-use Docker image for audio event analysis using the Google YAMNet / AudioSet model.

The image can be used to automatically analyze a video or audio file according to the 521 audio event classes from the [AudioSet ontology] (https://research.google.com/audioset/ontology/index.html). If the input file is video, the audio track is extracted first.

Since the original source code did not provide serializations or post-processing of the analysis data, I developed a JSON output of the analysis that includes the five most important audio events and respective scores for each overlapping time slice of the audio file (currently 960 ms) and a merge strategy that combines the same consecutive events and outputs CSV data divided into music, speech, silence and other events.

The image uses the following resources:
* [YAMNet source code](https://github.com/tensorflow/models/tree/master/research/audioset/yamnet) of the TensorFlow Model Garden
* [YAMNet model weights](https://storage.googleapis.com/audioset/yamnet.h5) in HDF5 format.

### Installation

A recent docker installation is required. To build the image use the following command or use the **build.sh** script.

```
docker build --rm -t hagt/yamnet:1.0 .
```

The Docker image uses a CPU-based Tensorflow installation. If you have a GPU available, it can be accelerated using a GPU version of Tensorflow (change FROM part in the Dockerfile to tensorflow:2.3.0-gpu).

### Usage

To perform an analysis, I provide a **run.sh** script that accepts a video or audio file and automatically mounts the file into the container and starts the analysis. Only WAV audio files are accepted as input. A number of video formats are supported as long as the first audio track can be extracted using ffmpeg. The container requires write access to the directory in which the video or audio file is located in order to output the annotations.

```
./run.sh ./my_video.mp4
./run.sh ./my_audio.wav
```

If you want to run the image manually, use the following command:
```
docker run --rm -it --name yamnet -v /path/to/you/video/audio/file:/data hagt/yamnet:1.0 /data/my_video.mp4
```

### Output data

