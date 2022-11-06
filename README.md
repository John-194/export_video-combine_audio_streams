# Audio fix for ShadowPlay
This script fixes a few problems with ShadowPlay recordings:
1. My mic was way quieter than my system audio so I recorded seperate tracks for them (an option in ShadowPlay settings)
2. Video players cannot play 2 seperate tracks at once.
3. My mic made noise and needed amplification.

## Requirements:
### Video
Videos must have 2 audio tracks (system and microphone).
### FFmpeg
Download: https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z  
Extract somewhere and put the extraction path in 'Enviroment Variables'. Example:
```
WIN+s -> 'system variables' -> Enviroment Variables... -> Path -> Edit -> New -> 'C:\ffmpeg\bin'
```
To test the installation, in a terminal type: 
```
ffmpeg -version
```
FFmpeg works by making a copy of the original video (cannot overwrite original).   
Since I further process the videos, I made the output a RAM disk with ImDisk, that is optional. 
### Packages
```
pip install -r requirements.txt
```
## Usage
Edit variables on line 51-54.
