import os
import subprocess
import urllib.parse
import urllib.request

try:
    from pytube import YouTube
    from pytube.helpers import safe_filename
except ImportError:
    print('[ERROR: dependencies not installed]')
    print('[start installing dependencies by pip...]')
    subprocess.run(['pip', 'install', '-r', 'requirements.txt'])

    from pytube import YouTube
    from pytube.helpers import safe_filename

try:
    subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL)
except FileNotFoundError:
    FFMPEG_AVAILABLE = False
else:
    FFMPEG_AVAILABLE = True


class FfmpegNotAvailableError(Exception):
    pass


class YouTubeHelper:
    def __init__(self, video_link):
        """
        initialize helper object and check video availability

        :param video_link: link to the YouTube video
        :type video_link: str
        """
        self.yt = YouTube(video_link)
        self.index = 0
        self.yt.check_availability()  # throw error if not available

    def auto_download(self, myfolder=None):
        """
        download highest quality video available in mp4 format

        :param myfolder: directory of downloaded video
        :type myfolder: str or path-like or None
        :return: None
        """
        resolutions = self.get_all_resolution()
        highest_resolution = None
        fps = None
        # find highest resolution and highest fps if possible
        for res in resolutions:
            i = res.find('p')
            number = res[:i]
            frame_per_second = res[i + 1:]
            if highest_resolution and number < highest_resolution:
                break
            if not highest_resolution:
                highest_resolution = number
            if not fps and frame_per_second:
                fps = int(frame_per_second)
            elif frame_per_second and int(frame_per_second) > fps:
                fps = int(frame_per_second)
        highest_resolution = str(highest_resolution) + 'p'
        conventional = highest_resolution + str(fps) if fps else highest_resolution
        print('video with resolution {} will be downloaded'.format(conventional))
        self.get_video(highest_resolution, myfolder=myfolder, fps=fps)

    def get_video(self, resolution, myfolder=None, fps=None):
        """
        download video in mp4 format

        :param myfolder: path to folder for downloaded video and audio
        :type myfolder: path-like or str or None
        :param resolution: resolution ends with 'p'
        :type resolution: str
        :param fps: frame per second
        :type fps: int
        :return: None
        """
        self.index += 1
        title = self.yt.title
        idx = self.index
        valid_filename = safe_filename(title) + '.mp4'
        file_path = os.path.join(myfolder, valid_filename) if myfolder else valid_filename
        progressive_video = self.yt.streams.filter(progressive=True, resolution=resolution, fps=fps)

        # download progressive video if possible
        if progressive_video:
            print("[Downloading progressive video...]")
            progressive_video.last().download(output_path=myfolder, filename=valid_filename)
            return
        if not FFMPEG_AVAILABLE:
            raise FfmpegNotAvailableError('ffmpeg not found. Cannot perform downloading.'
                                          'Make sure ffmpeg is installed and added in PATH')

        # search for video with specific resolution and fps
        video_search_result = self.yt.streams.filter(only_video=True, resolution=resolution, fps=fps)
        if video_search_result:
            print("[Downloading...]")
            video_path = video_search_result.last().download(
                output_path=myfolder, filename=f'video{idx}')
            audio_path = self.yt.streams.filter(only_audio=True).order_by('abr').last().download(output_path=myfolder,
                                                                                                 filename=f'audio{idx}')
            subprocess.run(
                ['ffmpeg', '-i', video_path, '-i', audio_path, '-acodec', 'aac', '-vsync', 'vfr', '-preset', 'veryfast', file_path])
            os.remove(video_path)
            os.remove(audio_path)
        else:
            quality = resolution + str(fps) if fps else resolution
            raise ValueError("there is no video with quality {}".format(quality))

    def get_audio(self, myfolder=None, quality=None, audio_format=None):
        """
        download audio in different format

        :param myfolder: directory for downloading audio
        :type myfolder: str or path-like or None
        :param quality: bit rate
        :type quality: int or None
        :param audio_format: audio format e.g.mp3,w4a
        :type: str
        :return: None
        """
        filename = safe_filename(self.yt.title)
        if quality is None:
            target = self.yt.streams.filter(only_audio=True).order_by('abr').last()
        elif not isinstance(quality, int):
            raise TypeError("quality should be int")
        else:
            abr = str(quality) + 'kbps'
            search_result = self.yt.streams.filter(only_audio=True, abr=abr)
            if search_result:
                target = search_result.last()
            else:
                raise ValueError("there is no audio with bit rate {}".format(abr))
        print("audio with {} is going to be downloaded".format(target.abr))
        print("[Downloading...]")
        audio_path = target.download(output_path=myfolder, filename=filename)
        print('[Download success]')
        if audio_format:
            audio_format = audio_format if audio_format[0] == '.' else '.' + audio_format
            path, ext = os.path.splitext(audio_path)
            if ext != audio_format:
                if not FFMPEG_AVAILABLE:
                    raise FfmpegNotAvailableError('ffmpeg not found. Cannot perform downloading.'
                                                  'Make sure ffmpeg is installed and added in PATH')
                output_path = os.path.join(myfolder, filename + audio_format) if myfolder else filename + audio_format
                subprocess.run(['ffmpeg', '-i', audio_path, output_path])
                os.remove(audio_path)

    def get_thumbnail(self, myfolder=None):
        """
        download video thumbnail and return the path to downloaded thumbnail

        :param myfolder: directory for downloading thumbnail
        :type myfolder: str or path-like or None
        :return: path to thumbnail
        :rtype: str
        """
        src_link = self.yt.thumbnail_url
        filename = os.path.basename(urllib.parse.urlparse(src_link).path)
        full_path = os.path.normpath(os.path.join(myfolder, filename)) if myfolder is not None else filename
        urllib.request.urlretrieve(src_link, full_path)
        return full_path

    def get_all_resolution(self):
        """
        print all available resolution

        :return: list of strings containing available resolution
        :rtype: list[str]
        """
        resolutions = []
        for stream in self.yt.streams.filter(only_video=True).order_by('resolution').desc():
            res = stream.resolution
            fps = stream.fps
            if fps > 30:
                res += str(fps)
            if res in resolutions:
                continue
            else:
                resolutions.append(res)
        return resolutions

    def get_all_audio_quality(self):
        """
        print all available bit rate

        :return: list of string containing available bit rate in terms of kbps
        :rtype: list[str]
        """
        audios = []
        for stream in self.yt.streams.filter(only_audio=True).order_by('abr').desc():
            bytes_per_second = stream.abr
            if bytes_per_second not in audios:
                audios.append(bytes_per_second)
        return audios

    def get_info(self):
        """
        print video info: title, publish date, description, duration,
        available resolution and audio bit rate for download

        :return: None
        """
        print("title: ", self.yt.title)
        print("publish date: ", self.yt.publish_date)
        print("description:")
        print(self.yt.description)
        print("length: ", readable_time(self.yt.length))
        print("available resolution for download: ", self.get_all_resolution())
        print("available audio quality for download: ", self.get_all_audio_quality())

    def get_video_length(self):
        """
        video duration in human readable form

        :return: video duration
        :rtype str
        """
        return readable_time(self.yt.length)

    def get_title(self):
        """
        get video title

        :return: title
        :rtype: str
        """
        return self.yt.title


def readable_time(seconds):
    """
    convert seconds to hours:minutes:seconds, this assumes not extremely large number

    :param seconds: number of seconds
    :type seconds: int
    :return: time in format hours:minutes:seconds
    :rtype: str
    """
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "{0:d}:{1:02d}:{2:02d}".format(hours, minutes, seconds) if hours > 0 else "{0:02d}:{1:02d}".format(minutes,
                                                                                                              seconds)
