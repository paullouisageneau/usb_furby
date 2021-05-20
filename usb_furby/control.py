import enum
import serial
import threading
import queue
import sys

TIMEOUT = 2


def print_err(*args):
    print(*args, file=sys.stderr)


class Move(enum.IntEnum):
    EARS_UP = 0
    EARS_UP_MOUTH_OPEN = 50
    EYES_CLOSED = 130
    EARS_DOWN_EYES_CLOSED = 180
    EARS_DOWN = 300
    EARS_DOWN_MOUTH_OPEN = 350


class Control(threading.Thread):
    def __init__(self, device='/dev/ttyACM0', baudrate=9600):
        super().__init__()
        self.serial = serial.Serial(device, baudrate, timeout=1)
        self.acks = queue.Queue()
        self.on_light = None

    def run(self):
        while self.serial.is_open:
            self.send('L')
            while True:
                cmd = self.read()
                if not cmd:
                    break
                self.process(cmd)

    def send(self, cmd):
        self.serial.write((cmd + '\n').encode())

    def read(self):
        return self.serial.readline().decode()

    def process(self, cmd):
        c = cmd[0]
        arg = cmd[1:].strip()
        if c == 'E':
            print_err("Furby: command error")
        elif c == 'M':
            self.acks.put(int(arg))
        elif c == 'L':
            if self.on_light is not None:
                self.on_light(int(arg))

    def home(self):
        self.send('H')

    def move(self, target):
        target = int(target)
        self.send('M {:d}'.format(target))
        try:
            while self.acks.get(timeout=TIMEOUT) != target:
                pass
        except queue.Empty:
            print_err("Furby: mechanical problem")
            self.stop()

    def stop(self):
        self.send('S')
        try:
            self.acks.get(timeout=TIMEOUT)
        except queue.Empty:
            pass
