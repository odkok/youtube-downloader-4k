import argparse
import os
import errno
import sys
from helper import YouTubeHelper


def is_pathname_valid(pathname: str) -> bool:
    """
    `True` if the passed pathname is a valid pathname for the current OS;
    `False` otherwise.
    credit: https://stackoverflow.com/questions/9532499/check-whether-a-path-is-valid-in-python-without-creating-a-file-at-the-paths-ta/9532586#9532586
    """
    ERROR_INVALID_NAME = 123
    # If this pathname is either not a string or is but is empty, this pathname
    # is invalid.
    try:
        if not isinstance(pathname, str) or not pathname:
            return False

        # Strip this pathname's Windows-specific drive specifier (e.g., `C:\`)
        # if any. Since Windows prohibits path components from containing `:`
        # characters, failing to strip this `:`-suffixed prefix would
        # erroneously invalidate all valid absolute Windows pathnames.
        _, pathname = os.path.splitdrive(pathname)

        # Directory guaranteed to exist. If the current OS is Windows, this is
        # the drive to which Windows was installed (e.g., the "%HOMEDRIVE%"
        # environment variable); else, the typical root directory.
        root_dirname = os.environ.get('HOMEDRIVE', 'C:') \
            if sys.platform == 'win32' else os.path.sep
        assert os.path.isdir(root_dirname)  # ...Murphy and her ironclad Law

        # Append a path separator to this directory if needed.
        root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

        # Test whether each path component split from this pathname is valid or
        # not, ignoring non-existent and non-readable path components.
        for pathname_part in pathname.split(os.path.sep):
            try:
                os.lstat(root_dirname + pathname_part)
            # If an OS-specific exception is raised, its error code
            # indicates whether this pathname is valid or not. Unless this
            # is the case, this exception implies an ignorable kernel or
            # filesystem complaint (e.g., path not found or inaccessible).
            #
            # Only the following exceptions indicate invalid pathnames:
            #
            # * Instances of the Windows-specific "WindowsError" class
            #   defining the "winerror" attribute whose value is
            #   "ERROR_INVALID_NAME". Under Windows, "winerror" is more
            #   fine-grained and hence useful than the generic "errno"
            #   attribute. When a too-long pathname is passed, for example,
            #   "errno" is "ENOENT" (i.e., no such file or directory) rather
            #   than "ENAMETOOLONG" (i.e., file name too long).
            # * Instances of the cross-platform "OSError" class defining the
            #   generic "errno" attribute whose value is either:
            #   * Under most POSIX-compatible OSes, "ENAMETOOLONG".
            #   * Under some edge-case OSes (e.g., SunOS, *BSD), "ERANGE".
            except OSError as exc:
                if hasattr(exc, 'winerror'):
                    if exc.winerror == ERROR_INVALID_NAME:
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False
    # If a "TypeError" exception was raised, it almost certainly has the
    # error message "embedded NUL character" indicating an invalid pathname.
    except TypeError:
        return False
    # If no exception was raised, all path components and hence this
    # pathname itself are valid.
    else:
        return True


parser = argparse.ArgumentParser()
parser.add_argument('url', help="url of video")
parser.add_argument('--folder', '-f', help="folder for saving downloaded video and audio")
parser.add_argument('--quality', '-q',
                    help="quality of video/audio, must be in the format of 1080p60/360p(for video) or 128(for audio)")
parser.add_argument('--info', '-i', action='store_true', help="show video info")
parser.add_argument('--audio', '-a', action='store_true', help="download audio only")
parser.add_argument('-aformat', choices=['mp3', 'm4a', 'webm', 'wav'], help="choose audio format")

args = parser.parse_args()

# processed directory for downloading to be passed to YouTubeHelper method, default to be current directory
target_dir = None
# processed video/audio quality to be passed to YouTubeHelper method
quality = None

if args.info:
    # print video info and leave
    YouTubeHelper(args.url).get_info()
    sys.exit()

downloader = YouTubeHelper(args.url)

# parse argument quality
if args.quality:
    quality = args.quality
    p_index = quality.find('p')
    # it may refer to video quality
    if p_index != -1:
        # check left of p and right of p are both int
        left = quality[:p_index]
        right = quality[p_index + 1:]
        for x in left:
            if not x.isdigit():
                print("[ERROR: incorrect format of argument quality]")
                parser.print_help()
                sys.exit()
        for x in right:
            if not x.isdigit():
                print("[ERROR: incorrect format of argument quality]")
                parser.print_help()
                sys.exit()
    # it may refer to audio quality, check if it only contain number
    else:
        for x in quality:
            if not x.isdigit():
                print("[ERROR: incorrect format of argument quality]")
                parser.print_help()
                sys.exit()
        quality = int(quality)  # audio quality in integer

# parse argument folder
if args.folder:
    folder_path = args.folder
    target_dir = folder_path  # directory of the path (assume path is valid)
    # check validity of path
    if not is_pathname_valid(folder_path):
        print("{} is not a valid path, download to current directory instead".format(folder_path))
        target_dir = None
    # if path is valid, extract the directory part
    else:
        dir_part, tail = os.path.split(target_dir)
        if '.' not in tail or ('.' in tail and tail[0] != '.'):
            target_dir = os.path.normpath(os.path.join(dir_part, tail))
        else:
            target_dir = dir_part
        # check if the directory exists, if not, try to make one
        if not os.path.isdir(target_dir):
            try:
                os.mkdir(target_dir)
            except (PermissionError, OSError) as e:
                print(e)
                print("[Error occur when creating directory {}. Download to current working directory instead]".format(
                    target_dir))
                target_dir = None

if args.audio:
    # download audio
    if not isinstance(quality, int) and quality is not None:
        raise TypeError("audio quality should be a positive integer")
    downloader.get_audio(myfolder=target_dir, quality=quality, audio_format=args.aformat)
else:
    # download video
    if quality is None:
        downloader.auto_download(myfolder=target_dir)
    elif isinstance(quality, str):
        i = quality.find('p')
        res = quality[:i]
        fps = int(quality[i + 1:]) if quality[i + 1:] else None
        downloader.get_video(res, fps=fps, myfolder=target_dir)
    else:
        raise TypeError("video quality should be in form of 1080p60/360p, etc.")
