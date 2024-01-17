from __future__ import annotations
import subprocess
from pathlib import Path
from src.settings import Settings, Encoder
from src.video import Video, Audio

MB = 1024 * 1024
AUDIO_BIT_RATE = 0.128
BITS_IN_BYTE = 8
MAXRATE_MULTIPLIER = 2
BUFSIZE_MULTIPLIER = 1


class Ffmpeg:
  def __init__(self, settings: Settings):
    self.debug = settings.debug
    print(settings.input_path)
    self.video = Video(settings.input_path)
    self.settings = settings

  @property
  def _audio_str(self) -> str:
    """
    [0:a:0] - first input (0), first audio stream
    [1:a] - second input (1), all audio streams
    inputs=2 - 2 input audio streams
    [a] - label for merged stream
    not specifying -ac 2 or 1, there will be 4 audio channels after the merge
    """
    if self.video.audio_tracks == 1 or self.settings.mic_audio.remove:
      if self.settings.main_audio.remove:
        return "-an "
      return f"-map 0:a:{self.settings.main_audio.track} -b:a {AUDIO_BIT_RATE}M -ac 2 "
    if self.settings.main_audio.remove:
      return f'-i "{self.video.audio[self.settings.mic_audio.track].path}" ' \
             f"-map 1:a -b:a {AUDIO_BIT_RATE}M -ac 1 "
    return f'-i "{self.video.audio[self.settings.mic_audio.track].path}" ' \
           f"-filter_complex [0:a:{self.settings.main_audio.track}][1:a]amerge=inputs=2[a] -map [a] " \
           f"-b:a {AUDIO_BIT_RATE}M -ac 2 "

  @property
  def _encoder_str(self) -> str:
    if not self.settings.encode:
      return "-map 0:v -c:v copy "
    output = "-map 0:v -c:v "
    if self.settings.encode.device == Encoder.Device.GPU:
      if self.settings.encode.format == Encoder.Format.H265:
        output += "hevc_nvenc "
      elif self.settings.encode.format == Encoder.Format.H264:
        output += "h264_nvenc "

      if self.settings.encode.speed == Encoder.Speed.FAST:
        output += "-preset 2 "
      elif self.settings.encode.speed == Encoder.Speed.SLOW:
        output += "-preset 1 "

    elif self.settings.encode.device == Encoder.Device.CPU:
      if self.settings.encode.format == Encoder.Format.H265:
        output += "libx265 "
      elif self.settings.encode.format == Encoder.Format.H264:
        output += "libx264 "

      if self.settings.encode.speed == Encoder.Speed.FAST:
        output += "-preset medium "
      elif self.settings.encode.speed == Encoder.Speed.SLOW:
        output += "-preset slow "

    return output

  @property
  def _bit_rate_str(self) -> str:
    if not self.settings.encode:
      return ""
    if self.settings.encode.target_size:
      # BUG: audio bit rate * duration is larger than target size. -> lower audio bitrate
      target_video_size = (self.settings.encode.target_size * BITS_IN_BYTE - AUDIO_BIT_RATE * MB * self.video.duration)
      bit_rate = target_video_size / self.video.duration
      if self.settings.encode.target_bit_rate and self.settings.encode.target_bit_rate < bit_rate:
        bit_rate = self.settings.encode.target_bit_rate
    elif self.settings.encode.target_bit_rate:
      bit_rate = self.settings.encode.target_bit_rate
    else:
      return "copy "
    return (f"-b:v {bit_rate / MB:.2f}M "
            f"-maxrate {min(bit_rate * MAXRATE_MULTIPLIER, self.video.bit_rate) / MB:.2f}M "
            f"-bufsize {bit_rate * BUFSIZE_MULTIPLIER / MB:.2f}M ")

  @property
  def _video_path_str(self) -> str:
    return f'-i "{str(self.video.path)}" '

  @property
  def _decoder_str(self) -> str:
    return "-hwaccel auto "

  @property
  def _output_path_str(self) -> str:
    return str(self.settings.output_path / self.video.path.name)

  @property
  def _libx_2pass_str(self) -> str:
    if (not self.settings.encode or
        (self.settings.encode.device != Encoder.Device.CPU and
         self.settings.encode.speed != Encoder.Speed.SLOW)):
      return ""
    cmd = (f'ffmpeg {self._video_path_str}'
           f'{self._encoder_str}{self._bit_rate_str}-x265-params pass=1 -an -f null')
    pipe = subprocess.DEVNULL
    if self.debug:
      print(cmd)
      pipe = None
    subprocess.run(cmd, stderr=pipe, stdout=pipe)
    return '-x265-params pass=2 '

  def run(self):
    if self.video.audio_tracks > 1 and not self.settings.mic_audio.remove:
      audio: Audio = self.video.audio[self.settings.mic_audio.track]
      if self.settings.mic_audio.noise_file:
        audio.reduce_noise(self.settings.mic_audio.noise_file)
      if self.settings.mic_audio.amplify:
        audio.amplify(self.settings.mic_audio.amplify)
      audio.export(remove_export_on_del=True)

    self.settings.output_path.mkdir(parents=True, exist_ok=True)
    cmd = (f'ffmpeg {self._decoder_str}'
           f'{self._video_path_str}'
           f'{self._audio_str}'
           f'{self._encoder_str}{self._bit_rate_str}{self._libx_2pass_str}'
           f'-y "{self._output_path_str}"')
    pipe = subprocess.DEVNULL
    if self.debug:
      print(cmd)
      pipe = None
    subprocess.run(cmd, stderr=pipe, stdout=pipe)
    print(f'{self.video.path.name} Done: {self.video.path.stat().st_size / MB:.0f} MB -> '
          f'{Path(self.settings.output_path / self.video.path.name).stat().st_size / MB:.0f} MB')

  @staticmethod
  def init_and_run(settings: Settings):
    Ffmpeg(settings).run()
