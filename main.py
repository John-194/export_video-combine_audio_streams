import noisereduce as nr
from scipy.io.wavfile import read
from pydub import AudioSegment
import subprocess
from pathlib import Path
from multiprocessing import Pool
from functools import cached_property
from time import time

class Video:
    def __init__(self, video_path, fixer):
        self.fixer, self.path = fixer, video_path

    def fix_audio(self):
        if self.mic_path is None:
            print(f'{self.path.name}: Video has only 1 audio track, 2 required to fix audio.')
            return
        rate, mic = read(self.mic_path.as_posix())
        mic = mic[:, 0]
        # Reducing noise
        if self.fixer.noise is not None:
            mic = nr.reduce_noise(y=mic, y_noise=self.fixer.noise, sr=rate, stationary=True)

        # Amplifying
        mic = AudioSegment(
            mic.tobytes(),
            frame_rate=rate,
            sample_width=mic.dtype.itemsize,
            channels=1
        )
        if self.fixer.mic_amp != 0:
            mic += self.fixer.mic_amp

        mic.export(self.mic_path, format='wav')

    @cached_property
    def mic_path(self):
        mic_path = self.fixer.output_dir_path / f'{self.path.stem}_mic.wav'
        subprocess.run(f'ffmpeg -i "{self.path.as_posix()}" -map 0:a:1 -y "{mic_path.as_posix()}"',
                       stderr=self.fixer.debug)
        if not mic_path.is_file():
            return None
        return mic_path

    @cached_property
    def bitrate(self):
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                 "format=bit_rate", "-of",
                                 "default=noprint_wrappers=1:nokey=1", self.path.as_posix()],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        return float(result.stdout) // 1000000  # Megabits

    @cached_property
    def audio_bitrate(self):
        return 0.016  # in MBps TODO: make it not hardcoded

    @cached_property
    def length(self):
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                 "format=duration", "-of",
                                 "default=noprint_wrappers=1:nokey=1", self.path.as_posix()],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        return float(result.stdout)

    def remove_mic_file(self):
        if self.mic_path is not None:
            self.mic_path.unlink()
            del self.mic_path


class Fixer:
    def __init__(self, output_dir_path, debug=False):
        self.encode, self.fix_audio = False, False
        self.output_dir_path = output_dir_path
        self.output_dir_path.mkdir(exist_ok=True)
        self.debug = None if debug else subprocess.DEVNULL
        self.mic_amp, self.noise, self.target_bitrate, self.target_size, self.device, self.format, self.speed = (None,)*7

    def enable_audio_fix(self, mic_amp=0, noise_file_path=None):
        if noise_file_path is not None:
            try:
                _, self.noise = read(noise_file_path.as_posix())
            except:
                raise Exception("Error: noise file not found.")
        self.mic_amp = mic_amp
        self.fix_audio = True

    def ffmpeg_audio_merger(self, video):
        if self.fix_audio and video.mic_path:
            return "-filter_complex [0:a:0][1:a]amerge=inputs=2[a] "
        return ""

    def ffmpeg_audio_map(self, video):
        if self.fix_audio and video.mic_path:
            return "-map [a] "
        else:
            return "-map 0:a "

    def ffmpeg_mic_path(self, video):
        if self.fix_audio:
            mic_path = video.mic_path
            if mic_path:
                return f'-i "{mic_path.as_posix()}" '
        return ""

    def enable_encode(self, device="gpu", format="h265", speed="fast", target_size=None, target_bitrate=None):
        self.device = device
        self.format = format
        self.speed = speed
        self.target_size = target_size
        self.target_bitrate = target_bitrate
        self.encode = True

    def ffmpeg_device(self):
        output = ""
        if self.device == "gpu":
            output += "-hwaccel cuda -hwaccel_output_format cuda "
        return output

    def ffmpeg_encoder(self):
        if self.encode:
            output = "-c:v "
            if self.device == "gpu":
                if self.format == "h265":
                    output += "hevc_nvenc "
                elif self.format == "h264":
                    output += "h264_nvenc "
                if self.speed == "fast":
                    output += "-preset 2 "
                elif self.speed == "slow":
                    output += "-preset 1 "
            elif self.device == "cpu":
                if self.format == "h265":
                    output += "libx265 "
                elif self.format == "h264":
                    output += "libx264 "
                if self.speed == "fast":
                    output += "-preset medium "
                elif self.speed == "slow":
                    output += "-preset slow "
            return output
        else:
            return "-c:v copy "

    def ffmpeg_bitrate(self, video):
        if self.encode:
            if self.target_size:
                target_video_size = (self.target_size - video.audio_bitrate * video.length)
                bitrate = target_video_size * 8 / video.length
                if self.target_bitrate and self.target_bitrate < bitrate:
                    bitrate = self.target_bitrate
            elif self.target_bitrate:
                bitrate = self.target_bitrate
            else:
                return "copy "
            return f"-b:v {bitrate:.2f}M -maxrate {min(bitrate * 2, video.bitrate):.2f}M -bufsize {bitrate:.2f}M "
        return ""

    def ffmpeg_video_path(self, video):
        return f'-i "{video.path.as_posix()}" '

    def ffmpeg_output_path(self, video):
        path = self.output_dir_path / video.path.name
        return path.as_posix()

    def libx_2pass(self, video):
        if self.device == "cpu" and self.speed == "slow":
            cmd = (f'ffmpeg {self.ffmpeg_video_path(video)}'
                   f'{self.ffmpeg_encoder()}{self.ffmpeg_bitrate(video)}-x265-params pass=1 -an -f null')
            print(cmd)
            subprocess.run(cmd, stderr=self.debug)
            return '-x265-params pass=2 '
        return ""

    def fix(self, video_path):
        if not self.fix_audio and not self.encode:
            raise Exception("No options selected. Needs fix_audio() and/or encode().")
        if video_path.is_dir():
            return
        video = Video(video_path, self)
        if self.fix_audio:
            video.fix_audio()

        cmd = (f'ffmpeg {self.ffmpeg_device()}{self.ffmpeg_video_path(video)}{self.ffmpeg_mic_path(video)}'
               f'{self.ffmpeg_audio_merger(video)}'
               f'-map 0:v {self.ffmpeg_audio_map(video)}'
               f'{self.ffmpeg_encoder()}{self.ffmpeg_bitrate(video)}{self.libx_2pass(video)}'
               f'-ac 2 -y "{self.ffmpeg_output_path(video)}"')

        print(cmd)
        subprocess.run(cmd, stderr=self.debug)


        video.remove_mic_file()
        print(f'{video_path.name}: Done.')


if __name__ == '__main__':
    # TODO: command line and arg parser
    # TODO: normal documentation
    # TODO: encoder doesn't work with: [gpu, h264, slow] and [cpu, slow]

    # for encoder options "ffmpeg -h encoder=h264_nvenc"

    # Audio fixer merges 2 audio tracks into 1, amplifies and removes noise for audio stream #2
    # Encoder uses:
    # device="cpu" (much slower, better quality)
    #       ="gpu" (much faster)
    # format="h264" (much worse quality, more compatibility)
    #       ="h265" (much better quality)
    # speed="slow" (better quality, uses 2 pass)
    #      ="fast" (faster)

    video_path = Path('D:/Videos/Dayz/test.mp4')  # Can be a single file or folder (don't forget '.mp4' suffix).
    THREADS = 2  # Number of CPU threads for multiple videos, lower if corruption occurs

    fixer = Fixer(output_dir_path=Path('R:/'), debug=True)

    # Audio fixer
    noise_file_path = Path(__file__).resolve().parent / 'mic_noise_combined.wav'  # Noise file (.wav) was next to script
    fixer.enable_audio_fix(mic_amp=9, noise_file_path=noise_file_path)

    # Encoder
    fixer.enable_encode(device="gpu", format="h265", speed="slow", target_bitrate=11, target_size=20)

    start = time()
    if video_path.is_file():
        fixer.fix(video_path)
    else:
        p = Pool(THREADS)
        p.map(fixer.fix, video_path.glob('*'))
    print(f"{time()-start:.2f}s")
