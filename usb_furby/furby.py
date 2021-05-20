#!/usr/bin/env python3

from .speech import Speech
from .control import Control, Move

import time


class Furby:
    def __init__(self, device='/dev/ttyACM0', lang='mb-fr4'):
        self.control = Control(device)
        self.control.on_light = lambda light: self.on_light(light)
        self.control.start()
        self.speech = Speech(lang)

    def on_light(self, light):
        print("Light: {:d}".format(light))

    def say(self, text):
        self.control.move(Move.EARS_UP)
        self.speech.say(str(text))
        self.control.move(Move.EARS_UP_MOUTH_OPEN)
        while self.speech.left() > 0.1:
            t = self.speech.volume(0.1)
            self.control.move(Move.EARS_UP_MOUTH_OPEN * t + Move.EARS_UP * (1.0 - t))
            time.sleep(0.01)

        self.control.move(Move.EARS_UP)
        self.speech.wait()
        time.sleep(0.5)

    def wakeup(self):
        self.control.move(Move.EARS_UP)
        time.sleep(0.5)

    def sleep(self):
        self.control.move(Move.EYES_CLOSED)
        time.sleep(0.5)
        self.control.move(Move.EARS_DOWN_EYES_CLOSED)
        time.sleep(0.5)

