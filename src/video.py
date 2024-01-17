from __future__ import annotations
import noisereduce as nr
from pydub import AudioSegment
import subprocess
from pathlib import Path
from shlex import split
import json

class Audio:
  def __init__(self, path: Path, metadata: dict):
    self._video_path = path
    self._audio_idx = int(metadata['index']) - 1
    self._path = path.parent / f'{path.stem}_track{self._audio_idx}.wav'
    self._sample_rate = int(metadata['sample_rate'])
    self._bit_rate = int(metadata['bit_rate'])
    self._channels = int(metadata['channels'])
    self._sound = None
    self.remove_export_on_del = False

  @property
  def path(self) -> Path:
    return self._path
  @property
  def channels(self) -> int:
    return self._channels

  @property
  def bit_rate(self) -> int:
    return self._bit_rate

  @property
  def sample_rate(self) -> int:
    return self._sample_rate

  @property
  def audio_track(self) -> int:
    return self._audio_idx

  def _load_data(self) -> bool:
    if self._sound:
      print('Warning: attempted to load sound twice')
      return False
    cmd = f'ffmpeg -i "{str(self._video_path)}" -map 0:a:{self._audio_idx} -f wav pipe:1'
    audio_data = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout
    self._sound = AudioSegment(audio_data)
    return True

  def reduce_noise(self, noise_path):
    """
    Reduce noise before amplifying.
    """
    assert noise_path.is_file(), f"{str(noise_path)} not found."
    if not self._sound:
      self._load_data()
    reduced = nr.reduce_noise(
      y=self._sound.get_array_of_samples(),
      y_noise=AudioSegment.from_wav(str(noise_path)).get_array_of_samples(),
      sr=self._sample_rate,
      stationary=True,
    )
    self._sound = AudioSegment(
      reduced.tobytes(),
      frame_rate=self._sample_rate,
      sample_width=self._sound.sample_width,
      channels=self._channels
    )

  def amplify(self, amount):
    """
    Amplify after reducing noise.
    """
    if not self._sound:
      self._load_data()
    self._sound += amount

  def get(self):
    return

  def export(self, remove_export_on_del: bool = False):
    if not self._sound:
      self._load_data()
    self._sound.export(self._path, format='wav')
    self.remove_export_on_del = remove_export_on_del

  def __del__(self):
    if self.remove_export_on_del:
      self.remove_export()

  def remove_export(self):
    self._path.unlink(missing_ok=True)


class Video:
  def __init__(self, video_path: Path):
    self._path = video_path
    cmd = f"ffprobe -v quiet -print_format json -show_format -show_streams '{str(video_path)}'"
    metadata = json.loads(subprocess.run(split(cmd), stdout=subprocess.PIPE).stdout)
    self._num_audio_tracks = sum(
      metadata['streams'][i]['codec_type'] == 'audio' for i in range(len(metadata['streams']))
    )
    self._duration = float(metadata['format']['duration'])
    self._size = int(metadata['format']['size'])
    self._bit_rate = int(metadata['format']['bit_rate'])
    self._audio = tuple(
      Audio(
        self._path,
        metadata['streams'][stream_idx],
      ) for stream_idx in range(1, self._num_audio_tracks + 1)
    )

  @property
  def duration(self) -> float:
    return self._duration

  @property
  def size(self) -> int:
    return self._size

  @property
  def bit_rate(self) -> int:
    return self._bit_rate

  @property
  def path(self) -> Path:
    return self._path

  @property
  def audio_tracks(self) -> int:
    return self._num_audio_tracks

  @property
  def audio(self) -> tuple[Audio]:
    return self._audio
