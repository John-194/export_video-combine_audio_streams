import noisereduce as nr
from scipy.io.wavfile import read
from pydub import AudioSegment
import subprocess
from pathlib import Path
from multiprocessing import Pool

class AudioFixer:
    def __init__(self, output_dir_path, noise_file_path=None, mic_amp=9, debug=False):
        self.output_dir_path = output_dir_path
        self.mic_amp = mic_amp
        self.debug = debug
        try:
            _, self.noise = read(noise_file_path.as_posix())
        except:
            print("Noise file not found.")
            self.noise = None
        self.output_dir_path.mkdir(exist_ok=True)

    def fix_audio(self, input_video_path):
        msg_toggle = None if self.debug else subprocess.DEVNULL
        if input_video_path.is_dir():
            return
        # Importing
        mic_path = self.output_dir_path / f'{input_video_path.stem}_mic.wav'
        subprocess.run(f'ffmpeg -i "{input_video_path.as_posix()}" -map 0:a:1 -y "{mic_path.as_posix()}"',
                       stderr=msg_toggle)
        if not mic_path.is_file():
            print(f'{input_video_path.name}: Video has only 1 audio track, 2 required.')
            return
        rate, mic = read(mic_path.as_posix())

        # Reducing noise
        if self.noise is not None:
            reduced_noise = nr.reduce_noise(y=mic[:, 0], y_noise=self.noise, sr=rate, stationary=True)
        else:
            reduced_noise = mic

        # Amplifying
        reduced_noise_amplified = AudioSegment(
            reduced_noise.tobytes(),
            frame_rate=rate,
            sample_width=reduced_noise.dtype.itemsize,
            channels=1
        )
        reduced_noise_amplified += self.mic_amp

        # Saving
        reduced_noise_amplified.export(mic_path, format='wav')
        output_video_path = self.output_dir_path / input_video_path.name
        subprocess.run(f'ffmpeg -i "{input_video_path.as_posix()}" -i "{mic_path.as_posix()}" \
                        -filter_complex [0:a:0][1:a]amerge=inputs=2[a] \
                        -map 0:v -map [a] -c:v copy -ac 2 -y "{output_video_path.as_posix()}"', stderr=msg_toggle)
        mic_path.unlink()
        print(f'{input_video_path.name}: Done.')

if __name__ == '__main__':
    video_path = Path('D:/Videos/dayz')  # Can be a single file or folder (don't forget '.mp4' suffix).
    output_dir_path = Path('R:/')  # I used RAM disk for output.
    noise_file_path = Path(__file__).resolve().parent / 'mic_noise1.wav'  # Noise file (.wav) was next to script
    THREADS = 6  # Number of CPU threads

    fixer = AudioFixer(output_dir_path, noise_file_path, mic_amp=9, debug=False)
    if video_path.is_file():
        fixer.fix_audio(video_path)
    else:
        p = Pool(THREADS)
        p.map(fixer.fix_audio, video_path.glob('*'))
