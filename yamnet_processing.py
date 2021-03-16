import sys
import os
import argparse
import subprocess
import json
import csv
from json import load
import numpy as np
import resampy
import soundfile as sf

import params as yamnet_params
import yamnet as yamnet_model

EVENT_THRESHOLDS = {'Silence': 0.5, 'Music': 0.1, 'Speech': 0.5, 'Other' : 0.3}

TMP_AUDIO_FILE = "/tmp/audio.wav"
VIDEO_FILE_EXTENSIONS = [".mp4",".avi",".mpg",".mpeg",".m4p",".m4v",".ogg",".mpe",".mpv"] # not complete, extend to your needs

def extract_wav(videofile):
    print("Extracting audio track 1 using ffmpeg from video",videofile)
    command = "ffmpeg -y -loglevel quiet -i {0} -ab 160k -ac 1 -ar 16000 -vn {1}".format(videofile, TMP_AUDIO_FILE)
    ret = subprocess.call(command, shell=True)
    if ret != 0:
        print("Wav extraction with ffmpeg failed, error code:", ret, file=sys.stderr)
        sys.exit(1)

def yamet_inference(inputfile, audiofile, outputfile):
    print("Initializing yamnet...")
    params = yamnet_params.Params()
    yamnet = yamnet_model.yamnet_frames_model(params)
    yamnet.load_weights('yamnet.h5')
    yamnet_classes = yamnet_model.class_names('yamnet_class_map.csv')
    
    wav_data, sr = sf.read(audiofile, dtype=np.int16)
    assert wav_data.dtype == np.int16, 'Bad sample type: %r' % wav_data.dtype
    waveform = wav_data / 32768.0
    waveform = waveform.astype('float32')
    
    if len(waveform.shape) > 1:
        waveform = np.mean(waveform, axis=1)
    if sr != params.sample_rate:
        waveform = resampy.resample(waveform, sr, params.sample_rate)
        
    print("Inference with yamnet model...")
    scores, embeddings, spectrogram = yamnet(waveform)
    
    data = {}
    patch_window = params.patch_window_seconds * 1000
    patch_hop = params.patch_hop_seconds * 1000
    data['file_info'] = {
        'path': inputfile,
        'patch_window_ms': patch_window,
        'patch_hop_ms': patch_hop
    }
    
    data['audio_events'] = []
    begin = 0
    for timeslice in scores:
        top_five = np.argsort(timeslice)[::-1][:5]        
        top_five_events = []
        top_five_scores = []
        for i in top_five:
            top_five_events.append(yamnet_classes[i])
            top_five_scores.append(float(timeslice[i]))
            
        data['audio_events'].append({
            'begin': int(begin),
            'end': int(begin + patch_window),
            'events': top_five_events,
            'scores': top_five_scores
        })
        begin = begin + patch_hop
    
    print("Writing json output...")
    with open(outputfile, 'w') as f:
        json.dump(data, f)
    
def filter_merge_events(jsonfile, file):
    print("Filter and merge audio events...")
    f = open(jsonfile)
    data = load(f)
    
    processed_events = dict()
    for e in EVENT_THRESHOLDS:
        processed_events[e] = []
        
    # First categorize and filter
    for audio_data in data['audio_events']:
        print(audio_data['begin'], audio_data['end'], audio_data['events'], audio_data['scores'])
        caption_texts = dict()
        for e in EVENT_THRESHOLDS:
            caption_texts[e] = ""
        for i, score in enumerate(audio_data['scores']):
            event = audio_data['events'][i]
            event_threshold = 0
            event_cat = ''
            if event in EVENT_THRESHOLDS:
                event_threshold = EVENT_THRESHOLDS.get(event)
                event_cat = event
            else:
                event_threshold = EVENT_THRESHOLDS.get('Other')
                event_cat = 'Other'
                
            if score >= event_threshold:
                ct = caption_texts[event_cat]
                ct += event + "; "
                caption_texts[event_cat] = ct
                
        for cat,ct in caption_texts.items():
            if ct != "":
                ct = ct[:-2]
                processed_events[cat].append([audio_data['begin'], audio_data['end'] , ct])
            
    merged_events = dict()
    for e in EVENT_THRESHOLDS:
        merged_events[e] = []

    # Merge consecutive events in each category
    for cat, processed_data in processed_events.items():
        if len(processed_data) == 0:
            continue
        prev_data = processed_data[0]
        del processed_data[0]    
        for yamnet_data in processed_data:
            if (prev_data[2] != yamnet_data[2] or yamnet_data[0] - prev_data[1] > 960):
                if (prev_data[1] > yamnet_data[0]):
                    prev_data[1] = prev_data[1] - 240
                    yamnet_data[0] = yamnet_data[0] + 240
                merged_events[cat].append(prev_data)
                prev_data = yamnet_data
            else:
                prev_data[1] = yamnet_data[1]
        merged_events[cat].append(prev_data)
        
    for cat, merged_data in merged_events.items():
        if len(merged_data) == 0:
            continue
        csvfile = file+"_"+cat.lower()+".csv"
        with open(csvfile, "wt", newline='') as of:
            tsv_writer = csv.writer(of, delimiter='\t')
            for yamnet_data in merged_data:
                tsv_writer.writerow([yamnet_data[0], yamnet_data[1], yamnet_data[2]]);


def main(inputfile):
    if not os.path.exists(inputfile):
        print("Input file " + str(inputfile) + " not found", file=sys.stderr)
        sys.exit(1)
    file, ext = os.path.splitext(inputfile)
    jsonfile = file+".json"
    audiofile = inputfile
    if ext in VIDEO_FILE_EXTENSIONS:
        extract_wav(inputfile)
        audiofile = TMP_AUDIO_FILE
    else:
        if ext != ".wav":
            print("File extension not recognized as audio or video file", file=sys.stderr)
            sys.exit(1)
            
    yamet_inference(inputfile, audiofile, jsonfile)
    filter_merge_events(jsonfile,file)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Audio or video file to analyse")
    args = parser.parse_args()
    
    main(args.input_file)
