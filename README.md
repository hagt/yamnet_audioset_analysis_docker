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
docker run --rm -it --name yamnet -v /path/to/video/audio/file:/data hagt/yamnet:1.0 /data/my_video.mp4
```

### Output data

The yamnet processing script outputs a JSON serialization of the original classification. It contains a *file_info* part and a list of *audio_events*. Each audio event is a 960ms segment of the waveform (the step size is 480ms, so they overlap) and lists the top 5 highest-scoring *events* and their corresponding *scores*.

```json
{
    "file_info": {
        "path": "/data/TV-20210315-2033-2200.webs.h264.mp4",
        "patch_window_ms": 960.0,
        "patch_hop_ms": 480.0
    },
    "audio_events": [{
            "begin": 0,
            "end": 960,
            "events": ["Silence", "Music", "Musical instrument", "Speech", "Inside, small room"],
            "scores": [0.9924958348274231, 0.00016120076179504395, 2.1329778974177316e-05, 2.0468718503252603e-05, 1.929334939632099e-05]
        }, {
            "begin": 480,
            "end": 1440,
            "events": ["Silence", "Music", "Inside, small room", "Musical instrument", "Keyboard (musical)"],
            "scores": [0.19930168986320496, 0.1958259642124176, 0.004749268293380737, 0.0017569959163665771, 0.0016628503799438477]
        }, {
            "begin": 960,
            "end": 1920,
            "events": ["Music", "Musical instrument", "Ukulele", "Pizzicato", "Plucked string instrument"],
            "scores": [0.8656256198883057, 0.07309243083000183, 0.06837290525436401, 0.02548578381538391, 0.020604193210601807]
        }, {
        ...
```

The data is then processed to categorize audio events into "music", "speech", "silence" and any "other" events and to merge consecutive events. The results are saved as tab-separated CSV files in the format "Begin (ms)" *TAB* "End (ms)" *TAB* "Event". 

```
example_music.csv
480	18240	Music
94560	95520	Music
208320	210240	Music
...

example_speech.csv
6240	7680	Speech
14880	940320	Speech
941760	958080	Speech
...

example_silence.csv
0	960	Silence
624480	625440	Silence
894240	895200	Silence
...

example_other.csv
9360	9840	Background music; Theme music
9840	10560	Theme music
65280	66240	Narration, monologue
...
```

