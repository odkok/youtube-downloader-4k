import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk, Image
import os.path
import threading
from helper import YouTubeHelper, FfmpegNotAvailableError, FFMPEG_AVAILABLE


# TODO: use multiple threads to download things in background


class DropDown(tk.OptionMenu):
    def __init__(self, parent, options: list, initial_value: str = None):
        """
        Constructor for drop down entry

        :param parent: the tk parent frame
        :param options: a list containing the drop down options
        :param initial_value: the initial value of the dropdown
        """
        self.var = tk.StringVar(parent)
        self.var.set(initial_value if initial_value else options[0])

        self.option_menu = tk.OptionMenu.__init__(self, parent, self.var, *options)

        self.callback = None

    def add_callback(self, callback: callable):
        """
        Add a callback on change

        :param callback: callable function
        :return:
        """

        def internal_callback(*args):
            callback()

        self.var.trace_add("write", internal_callback)

    def reset(self, new_options: list, initial_value=None):
        self['menu'].delete(0, 'end')
        for label in new_options:
            self['menu'].add_command(label=label, command=tk._setit(self.var, label))
        self.var.set(initial_value if initial_value else new_options[0])

    def get(self):
        """
        Retrieve the value of the dropdown

        :return:
        """
        return self.var.get()

    def set(self, value: str):
        """
        Set the value of the dropdown

        :param value: a string representing the
        :return:
        """
        self.var.set(value)


class EntryWithPlaceholder(tk.Entry):
    def __init__(self, master, placeholder="PLACEHOLDER", color='grey', **kwargs):
        super().__init__(master, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']  # default input text color

        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)

        self.put_placeholder()

    def put_placeholder(self):
        self.insert(0, self.placeholder)  # insert placeholder text
        self['fg'] = self.placeholder_color  # set the text color to placeholder color (default grey)

    def foc_in(self, *args):
        # if text color = placeholder color -> placeholder exist
        if self['fg'] == self.placeholder_color:
            self.delete('0', 'end')  # delete placeholder text
            self['fg'] = self.default_fg_color  # change text color to default text color to avoid being deleted

    def foc_out(self, *args):
        # if no input, place placeholder again
        if not self.get():
            self.put_placeholder()


# noinspection PyAttributeOutsideInit
class App(tk.Frame):
    # TODO: add clear button of input bar (if possible)
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('YouTube Downloader')
        self.yt = None
        self.url = None
        self.res_list = ['default']
        self.bitrate_list = ['default']
        self.original_image = None  # original thumbnail image
        self.img = None  # image for tkinter

        self.root.geometry('500x600')
        tk.Frame.__init__(self, self.root)

        # input bar for getting video url
        self.input_bar = EntryWithPlaceholder(self.root, placeholder='enter video url', width=200, borderwidth=5)
        self.input_bar.pack()
        self.input_bar.bind('<Return>', lambda event: self.go())

        # button for getting video (PyTube)
        self.goButton = tk.Button(self.root, text='GO', command=self.go)
        self.goButton.pack()

        # widgets to get download mode (video / audio)
        self.middleFrame = tk.Frame(self.root, padx=5, pady=5)
        self.middleFrame.pack(padx=5, pady=5)
        self.mode = tk.IntVar()
        self.videoButton = tk.Radiobutton(self.middleFrame, text='video', value=0, variable=self.mode,
                                          command=self.gotoVideoMode)
        self.videoButton.pack(side='left')
        self.audioButton = tk.Radiobutton(self.middleFrame, text='audio', value=1, variable=self.mode,
                                          command=self.gotoAudioMode)
        self.audioButton.pack(side='left')

        # frame for downloading
        self.downloadFrame = tk.Frame(self.root, padx=10, pady=10)  # set distance of inner widgets to this frame
        self.downloadFrame.pack(padx=5, pady=5)  # set distance of the frame to main frame

        # frame for detail setting of downloading (refresh if download mode change)
        self.settingFrame = tk.Frame(self.downloadFrame, padx=5, pady=5)
        self.settingFrame.pack(padx=5, pady=5)

        self.downloadButton = tk.Button(self.downloadFrame, text='Download', command=self.download, state=tk.DISABLED)
        self.downloadButton.pack(side='bottom', pady=10)

        # initiate widgets for video and place them
        self.resolutionLabel = tk.Label(self.settingFrame, text='resolution:')
        self.resolutionLabel.grid(row=0, column=0)
        self.resolutionOptions = DropDown(self.settingFrame, ['default'])
        self.resolutionOptions.grid(row=0, column=1)

        # frame at bottom for displaying thumbnail and video info
        self.bottomFrame = tk.Frame(self.root, padx=5, pady=5)
        self.bottomFrame.pack(padx=5, pady=5)

        if not FFMPEG_AVAILABLE:
            messagebox.showwarning('ffmpeg not found in PATH, some functionality may not be available')

    def go(self):
        url = self.input_bar.get().strip()
        if url == self.input_bar.placeholder:
            self.url = None
            messagebox.showwarning(message='You did not enter any url!')
            # deactivate download button
            self.downloadButton.config(state=tk.DISABLED)
        elif url != self.url:
            # update url and YouTube Helper
            self.url = url
            try:
                self.yt = YouTubeHelper(self.url)
                self.res_list = ['default'] + self.yt.get_all_resolution()
                self.bitrate_list = ['default'] + self.yt.get_all_audio_quality()
                img_path = self.yt.get_thumbnail(myfolder='assets')
                self.original_image = Image.open(img_path)
                self.img = ImageTk.PhotoImage(self.original_image)
                time_duration = self.yt.get_video_length()
                title = self.yt.get_title()

                # update options
                if self.getDownloadMode() == 0:
                    self.resolutionOptions.reset(self.res_list)
                elif self.getDownloadMode() == 1:
                    self.bitrateOptions.reset(self.bitrate_list)
            except Exception as e:
                messagebox.showerror(message=str(e))
                return

            # activate download button
            self.downloadButton.config(state=tk.ACTIVE)

            # update frame
            for wid in self.bottomFrame.winfo_children():
                wid.destroy()

            # display title
            self.titleLabel = tk.Message(self.bottomFrame, text=title, width=490)
            self.titleLabel.pack()

            # display video length
            self.durationLabel = tk.Label(self.bottomFrame, text=f'video length: {time_duration}')
            self.durationLabel.pack(side='bottom')

            # display video thumbnail
            self.imageLabel = tk.Label(self.bottomFrame, image=self.img)
            self.imageLabel.pack(fill='both', expand=True)  # fill the whole frame
            self.bottomFrame.update()  # update the change to get actual size of frame
            h, w = self.bottomFrame.winfo_height(), self.bottomFrame.winfo_width()  # get frame size
            self.original_image = self.original_image.resize((w, h))  # resize image to fit the frame
            self.img = ImageTk.PhotoImage(self.original_image)  # keep reference
            self.imageLabel.config(image=self.img)  # change the image in label

    # TODO: solve the race condition problem
    def download(self):
        if not self.yt or not self.url:
            messagebox.showerror(message='cannot download')
        mode = self.getDownloadMode()
        print('the download mode is', mode)
        download_path = os.path.normpath(os.path.expanduser('~/Downloads'))
        try:
            if mode == 0:
                # download video
                res = self.getResolution()
                if res:
                    i = res.find('p')
                    fps = int(res[i + 1:]) if res[i + 1:] else None
                    t = thread_with_messagebox(self.yt.get_video, 'download success', args=[res[:i + 1]],
                                               kwargs={'myfolder': download_path, 'fps': fps})
                else:
                    t = thread_with_messagebox(self.yt.auto_download, 'download success',
                                               kwargs={'myfolder': download_path})
            elif mode == 1:
                # download audio
                bitrate = self.getBitRate()
                if bitrate is not None:
                    i = bitrate.find('kbps')
                    bitrate = int(bitrate[:i])
                audio_format = self.getFormat()
                t = thread_with_messagebox(self.yt.get_audio, 'download success',
                                           kwargs={'myfolder': download_path, 'quality': bitrate,
                                                   'audio_format': audio_format})
        except FfmpegNotAvailableError as e:
            messagebox.showerror(message=e.message)

    def gotoVideoMode(self):
        # destroy all widgets
        for wid in self.settingFrame.winfo_children():
            wid.destroy()
        # widgets for getting resolution
        self.resolutionLabel = tk.Label(self.settingFrame, text='resolution:')
        self.resolutionOptions = DropDown(self.settingFrame, self.res_list)
        self.resolutionLabel.grid(row=0, column=0)
        self.resolutionOptions.grid(row=0, column=1)

    def gotoAudioMode(self):
        # destroy all widgets
        for wid in self.settingFrame.winfo_children():
            wid.destroy()
        # widgets for getting bit rate
        self.bitrateLabel = tk.Label(self.settingFrame, text='bit rate: ')
        self.bitrateLabel.grid(row=0, column=0)
        self.bitrateOptions = DropDown(self.settingFrame, self.bitrate_list)
        self.bitrateOptions.grid(row=0, column=1)

        # widgets for getting audio format
        self.formatLabel = tk.Label(self.settingFrame, text='audio format: ')
        self.formatOptions = DropDown(self.settingFrame, ['mp3', 'webm', 'w4a', 'default'])
        self.formatLabel.grid(row=1, column=0)
        self.formatOptions.grid(row=1, column=1)

    def getDownloadMode(self) -> int:
        return self.mode.get()

    def getResolution(self) -> str:
        return self.resolutionOptions.get() if self.resolutionOptions.get() != 'default' else None

    def getBitRate(self) -> str:
        return self.bitrateOptions.get() if self.bitrateOptions.get() != 'default' else None

    def getFormat(self) -> str:
        return self.formatOptions.get() if self.formatOptions.get() != 'default' else None

    def start(self):
        self.root.mainloop()


def thread_with_messagebox(target, message, args=[], kwargs={}):
    def run_target_with_messagebox(*args, **kwargs):
        target(*args, **kwargs)
        messagebox.showinfo(message=message)

    t = threading.Thread(target=run_target_with_messagebox, args=args, kwargs=kwargs)
    t.start()
    return t


if __name__ == '__main__':
    app = App()
    app.start()
