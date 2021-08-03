# YouTube Downloader 4k
A simple, light-weight and high-quality youtube video downloader based on Pytube and ffmpeg, can support 4k video

***DISCLAIMER: I do not encourage and am not responsible for any illegal downloading. Please respect copyrights.***

### Requirements
1. Python 3.2 or above
2. [Pytube](https://pypi.org/project/pytube/) `pip install pytube`
3. [ffmpeg](https://ffmpeg.org/) (must be added to PATH) (download [here](https://ffmpeg.org/download.html))
4. [Pillow](https://pypi.org/project/Pillow/) `pip install Pillow`

**Remarks**: Due to irregular update of YouTube's API, pytube **MUST** be updated to latest version by `pip install -U pytube`, or you may encouter errors

### Quick Start
#### GUI
1. run `python gui.py`
2. copy the url of the video and download your video and audio!

#### Command Line
##### Video
1. copy the url of the video (e.g. https://youtu.be/wcgTStAuXQw)
2. run `python runme.py https://youtu.be/wcgTStAuXQw`
3. the video with highest quality will be downloaded to your current directory (you can add `-f [PATH TO FOLDER]` to specify where the video will be downloaded)

##### Audio
1. copy the url of the video (e.g. https://youtu.be/4OSu1MsKaZw)
2. run `python runme.py https://youtu.be/wcgTStAuXQw -a -aformat mp3`
3. the audio in mp3 format will be downloaded to your current directory (you can add `-f [PATH TO FOLDER]` to specify where the audio will be downloaded)

### Command description
`usage: runme.py [-h] [--folder FOLDER] [--quality QUALITY] [--info] [--audio] [-aformat {mp3,m4a,webm,wav}] url`

Optional Arguments:

 `-f`, `--folder`   folder for saving downloaded video and audio
 
 `-q`, `--quality`  quality of video/audio, must be in the format of 1080p60/360p(resolution for video) or 128(bit rate for audio), only use it when you know what you need
 
 `-i`, `--info`   show video info(including resolution/audio bit rate available) and exit program
 
 `-a`, `--audio`  download audio only
 
 `-aformat` audio format for downloading audio (mp3, m4a, webm, wav only, usually the default is webm, but it depends on the stream used for downloading)
 
 
You can also run `python runme.py -h` to see all options available

### About ffmpeg
The program depends on ffmpeg to create high-resolution video and do audio format conversion. It can still download audio without conversion and download some lower-quality progressive video(if you specify the right resolution) without ffmpeg. But most functionality will be lost.
