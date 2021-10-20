from .speech import Speech
from .control import Control, Move

import time

class Furby:
    def __init__(self, device='/dev/ttyACM0', lang='mb-en1', pitch=4):
        self.control = Control(device)
        self.speech = Speech(lang, pitch)
        self.awake = False

    def light(self):
        return self.control.light()

    def say(self, text):
        if not self.awake:
            self.wakeup()

        self.control.move(Move.EARS_UP)
        self.speech.say(str(text))
        self.control.move(Move.EARS_UP_MOUTH_OPEN)
        while self.speech.left() > 0.1:
            t = self.speech.volume(0.2)
            self.control.move(Move.EARS_UP_MOUTH_OPEN * t + Move.EARS_UP * (1.0 - t))
            time.sleep(0.01)

        self.control.move(Move.EARS_UP)
        self.speech.wait()
        time.sleep(0.5)

    def wakeup(self):
        if self.awake:
            return

        self.control.move(Move.EARS_UP)
        time.sleep(0.5)
        self.awake = True

    def sleep(self):
        if not self.awake:
            return

        self.control.move(Move.EYES_CLOSED)
        time.sleep(0.5)
        self.control.move(Move.EARS_DOWN_EYES_CLOSED)
        time.sleep(0.5)
        self.awake = False

    def shutdown(self, delay=0):
        self.control.shutdown(delay)
