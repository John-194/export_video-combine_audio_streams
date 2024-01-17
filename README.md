# Multitrack audio merger for ShadowPlay (or other)

## About this script

### Problems by using ShadowPlay
1. Microphone too quiet.
2. Audible microphone noise.

### To fix these problems
1. Record a video with ShadowPlay settings -> "Audio" -> "Separate both tracks" selected.  
   Note: video players cannot play both audio streams at once.
2. Use this script.

### How this script fixes the problems
1. Amplifying microphone audio (optional).
2. Reducing microphone noise (optional).
3. Merging two audio streams into one.

### For convenience, this script also allows
1. Removal of audio streams.
2. Encoding of videos to reduce size.

### What it currently does not do:
1. It does not allow cutting videos.  
   You can use [VidCutter](https://github.com/ozmartian/vidcutter) for that. It can quickly cut videos without encoding.  
   (note: using more than one 'chapter' will remove microphone audio track)
2. Does not have a GUI.

## Requirements:

### FFmpeg

Download: https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z  
Extract somewhere and put the extraction path in 'Environment Variables'. Example:
```
WIN+s -> 'system variables' -> Enviroment Variables... -> Path -> Edit -> New -> 'C:\ffmpeg\bin'
```
To test the installation, in a terminal type: 
```
ffmpeg -version
```

### Packages

```
pip install -r requirements.txt
```

## Usage

1. Data folder provides a noise .wav file. 
If noise reduction doesn't work then Use [Audacity](https://www.audacityteam.org/) to record your mic noise accordingly.
2. Settings are in `main.py`.
3. You can provide a path to a single video or a folder to process many videos concurrently. 