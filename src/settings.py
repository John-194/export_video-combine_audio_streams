from __future__ import annotations
from pathlib import Path

from dataclasses import dataclass
from enum import Enum
from copy import deepcopy

# from ffmpeg import Ffmpeg
MB = 1024 * 1024

class Encoder:
  class Device(Enum):
    CPU = 1
    GPU = 2


  class Format(Enum):
    H264 = 1
    H265 = 2


  class Speed(Enum):
    SLOW = 1
    FAST = 2


class Settings:
  @dataclass
  class Audio:
    track: int
    amplify: int = None
    noise_file: Path | None = None
    remove: bool = False

  @dataclass
  class Encode:
    device: Encoder.Device = None
    format: Encoder.Format = None
    speed: Encoder.Speed = None
    target_bit_rate: float | None = None
    target_size: float | None = None

    def check(self):
      assert self.device and self.speed, "must input device and speed"
      assert self.target_bit_rate or self.target_size, "must input target_bit_rate and/or target_size"
      if self.target_bit_rate:
        assert self.target_bit_rate > 0, "target_bit_rate must be greater than 0."
        self.target_bit_rate *= MB
      if self.target_size:
        assert self.target_size > 0, "target_size must be greater than 0."
        self.target_size *= MB

  def __init__(self, input: str | Path, output_dir: str | Path, debug: bool = False,
               main_audio: Settings.Audio = Audio(0),
               mic_audio: Settings.Audio = Audio(1),
               encode: Settings.Encode | None = None):
    assert main_audio.noise_file is None and main_audio.amplify is None, "Cannot remove noise or amplify main audio."
    assert mic_audio and main_audio.track != mic_audio.track, "Main and mic tracks cannot be the same."
    self.debug = debug
    self.input_path = Path(input)
    self.output_path = Path(output_dir)
    self.encode = encode
    if encode:
      self.encode.check()
    self.main_audio = main_audio
    self.mic_audio = mic_audio

  def get_settings_for_files_if_dir(self) -> list[Settings]:
    if not self.input_path.is_dir():
      return [self]
    settings_list_of_files = []
    for input_path in self.input_path.iterdir():
      if input_path.is_dir():
        continue
      new_settings = deepcopy(self)
      new_settings.input_path = input_path
      settings_list_of_files.append(new_settings)
    return settings_list_of_files

  def copy(self):
    return deepcopy(self)

  def __str__(self):
    return f"input: {self.input_path}\n" \
           f"output: {self.output_path}\n" \
           f"encode: {self.encode}\n" \
           f"main_audio: {self.main_audio}\n" \
           f"mic_audio: {self.mic_audio}\n"

  def __hash__(self):
    return hash((str(self.input_path), str(self.output_path)))

  def __eq__(self, other):
    return self.input_path == other.input_path and self.output_path == other.output_path


