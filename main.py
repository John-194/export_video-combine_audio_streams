from src.start import start
from src.settings import *

if __name__ == "__main__":
  settings1 = Settings(
    input=r"D:\Videos\Desktop\battlebit\bb 1 rm.mp4",  # dir or file
    output_dir=r'D:\Videos\Desktop\battlebit\conv',  # dir
    main_audio=Settings.Audio(
      track=0,
      remove=False,
    ),
    mic_audio=Settings.Audio(
      track=1,
      amplify=10,
      noise_file=Path(__file__).parent / 'data/mic_noise.wav',
      remove=True,
    ),
    encode=Settings.Encode(
      device=Encoder.Device.GPU,
      format=Encoder.Format.H264,
      speed=Encoder.Speed.SLOW,
      target_bit_rate=10,   # in megabits
      target_size=None,  # in megabits
    )
  )
  settings2 = Settings(
    input=r"D:\Videos\Desktop\battlebit\bb 3.mp4",  # dir or file
    output_dir=r'D:\Videos\Desktop\battlebit\conv',  # dir
    main_audio=Settings.Audio(
      track=0,
      remove=False,
    ),
    mic_audio=Settings.Audio(
      track=1,
      amplify=10,
      noise_file=Path(__file__).parent / 'data/mic_noise.wav',
      remove=False,
    ),
    encode=Settings.Encode(
      device=Encoder.Device.GPU,
      format=Encoder.Format.H264,
      speed=Encoder.Speed.SLOW,
      target_bit_rate=10,   # in megabits
      target_size=None,  # in megabits
    )
  )
  start((settings1,settings2 ))
