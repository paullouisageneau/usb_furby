import enum
import serial

from concurrent.futures import ThreadPoolExecutor

TIMEOUT = 5


class Move(enum.IntEnum):
    EARS_UP = 0
    EARS_UP_MOUTH_OPEN = 50
    EYES_CLOSED = 130
    EARS_DOWN_EYES_CLOSED = 180
    EARS_DOWN = 300
    EARS_DOWN_MOUTH_OPEN = 350


class Control:
    def __init__(self, device='/dev/ttyACM0', baudrate=9600):
        self.serial = serial.Serial(device, baudrate, timeout=TIMEOUT)
        self.executor = ThreadPoolExecutor(max_workers=1)

    def write(self, cmd):
        self.serial.write((cmd + '\n').encode())

    def read(self):
        return self.serial.readline().decode()

    def run(self, cmd, arg=None):
        if arg is not None:
            self.write('{} {:d}'.format(cmd, int(arg)))
        else:
            self.write(cmd)

        ans = self.read()
        if ans is None:
            raise TimeoutError("Furby: command timeout")
        elif ans[0] != cmd[0]:
            raise RuntimeError("Furby: command error")
        else:
            ansarg = ans[1:].strip()
            return int(ansarg) if len(ansarg) > 0 else None

    def submit(self, cmd, arg=None):
        return self.executor.submit(self.run, cmd, arg)

    def light(self):
        light = self.submit('L').result()
        return light if light is not None else 0

    def home(self):
        self.submit('H').result()

    def move(self, target):
        try:
            self.submit('M', int(target)).result()
        except TimeoutError:
            try:
                self.stop()
            except TimeoutError:
                pass

            raise RuntimeError("Furby: mechanical issue")

    def stop(self):
        self.submit('S').result()
