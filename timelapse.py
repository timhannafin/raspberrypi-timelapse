from picamera import PiCamera
from os import system
from time import sleep
import time

camera = PiCamera()
camera.resolution = (1024, 768)

i = 0
while(1):
    camera.capture('lapse_frames/image{0:08d}.jpg'.format(i))
    i = i+1
    sleep(3)
