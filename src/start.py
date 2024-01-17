from typing import Sequence
from concurrent.futures import ProcessPoolExecutor
from time import time
from src.ffmpeg import Ffmpeg
from src.settings import *


def start(input: Settings | Sequence[Settings]) -> None:
  settings_set = set()  # removes duplicates
  try:
    settings_set.update(input.get_settings_for_files_if_dir())
  except AttributeError:
    for settings in input:
      settings_set.update(settings.get_settings_for_files_if_dir())

  # for l in settings_set:
  #   print(l)
  # exit()
  start = time()

  with ProcessPoolExecutor() as executor:
    list(executor.map(Ffmpeg.init_and_run, settings_set))

  print(f"{time() - start:.2f}s")

