
import subprocess
import wave
import time
import math
import struct


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class Speech:
    def __init__(self, lang='mb-fr4'):
        self.lang = lang
        self.filename = '/tmp/out.wav'
        self.process = None
        self.duration = 0.0
        self.begin_time = 0.0

    def say(self, text):
        self.wait()
        self.process = subprocess.Popen(['espeak-ng',
            '-v', self.lang,
            '-s', '100',
            '-p', '50',
            '-w', self.filename,
            text],
            stdout=subprocess.DEVNULL)
        self.process.wait()

        with wave.open(self.filename, 'r') as f:
            rate = f.getframerate()
            nb_frames = f.getnframes()
            self.duration = nb_frames / float(rate)

            frames = f.readframes(nb_frames)
            sample_width = f.getsampwidth()
            nb_samples = len(frames) // sample_width
            fmt = {1: "{:d}b", 2: "<{:d}h", 4: "<{:d}l"}[sample_width].format(nb_samples)
            samples = struct.unpack(fmt, frames)
            volumes = [math.sqrt(sum([s**2 for s in c])) for c in chunks(samples, rate // 10)]
            max_volume = max(volumes)
            self.volumes = [v / float(max_volume) for v in volumes]

            self.begin_time = time.time()

        self.process = subprocess.Popen(['play',
            self.filename,
            'pitch', '400'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)

    def finished(self):
        if self.process is not None:
            return self.process.poll() is not None
        else:
            return None

    def wait(self):
        if self.process is not None:
            self.process.wait()

    def left(self):
        return max(self.begin_time + self.duration - time.time(), 0.0)

    def volume(self, after_delay=0.0):
        p = int((time.time() - self.begin_time + after_delay) * 10)
        return self.volumes[p] if self.volumes and p >= 0 and p < len(self.volumes) else 0.0
