# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from rpi_ws281x import *
from .utils import blend_colors
from datetime import datetime
import time
import traceback
import json


def run_effect(effect, lock, queue, settings, color, delay, shutdown_event, reverse=False, **kwargs):
    lock.acquire()
    strip = Adafruit_NeoPixel(*settings)
    strip.begin()
    try:
        while not shutdown_event.is_set():
           if not queue.empty():
               raw_json_str = queue.get()
               json_str = json.loads(raw_json_str)
               data = {}
               for key in json_str['data']:
                   data[key] = json_str['data'][key]
               if "cmd" in data:
                   if data["cmd"] == "KILL":
                       break
               if "progress" in data:
                   kwargs['progress'] = data["progress"]
               if "r" in data or "g" in data or "b" in data:
                   r = 0
                   if "r" in data:
                       r = data["r"]
                   g = 0
                   if "g" in data:
                       g = data["g"]
                   b = 0
                   if "b" in data:
                       b = data["b"]
                   color = (r, g, b,)
               p = 0
               if "brightness" in data:
                   p = data["brightness"]
               d = 10
               if "delay" in data:
                   delay = data["delay"]
               i = -1
               if "index" in data:
                   i = data["index"]
               kwargs['index'] = i
               kwargs['brightness'] = p
           effect(strip, color, queue, delay, reverse=reverse, **kwargs)
    finally:
        lock.release()
        while not queue.empty():
            msg = queue.get_nowait()
        queue.close()
        queue.join_thread()

def progress_effect(strip, color, queue, delay=0, iterations=1, reverse=False, progress=0, progress_color=None, **kwargs):
   perc = float(progress) / 100 * float(strip.numPixels())
   pixels_range = range(strip.numPixels())
   if reverse:
       pixels_range = reversed(pixels_range)
   for i, p in enumerate(pixels_range):
       if i+1 <= int(perc):
           strip.setPixelColorRGB(p, *progress_color)
       elif i+1 == int(perc)+1:
           strip.setPixelColorRGB(p, *blend_colors(color, progress_color, (perc % 1)))
       else:
           strip.setPixelColorRGB(p, *color)
   strip.show()

# Define functions which animate LEDs in various ways.
def solid_color(strip, color, queue, delay=0, iterations=1, reverse=False, **kwargs):
    for p in range(strip.numPixels()):
        strip.setPixelColorRGB(p, *color)
    strip.show()

def solid_with_brightness(strip, color, queue, delay=10, iterations=1, reverse=False, brightness=255, index=-1, **kwargs):
    if index==-1:
        for p in range(strip.numPixels()):
            strip.setPixelColorRGB(p, *color)
    else:
        for p in range(strip.numPixels()):
            strip.setPixelColor(p, strip.getPixelColor(p))
            strip.setPixelColorRGB(index, *color)
    strip.setBrightness(brightness)
    strip.show()

def color_wipe(strip, color, queue, delay=50, iterations=1, reverse=False, **kwargs):
    """Wipe color across display a pixel at a time."""
    pixels_range = range(strip.numPixels())
    if reverse:
        pixels_range = list(reversed(pixels_range))

    for i in range(iterations):
        for p in pixels_range:
            strip.setPixelColorRGB(p, *color)
            strip.show()
            if not queue.empty():
                return
            time.sleep(delay/100.0)
        for p in pixels_range:
            strip.setPixelColorRGB(p, 0, 0, 0)
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay/100.0)


def theater_chase(strip, color, queue, delay=50, iterations=10, reverse=False, **kwargs):
    """Movie theater light style chaser animation."""
    pixels_range = range(0, strip.numPixels(), 3)
    if reverse:
        pixels_range = list(reversed(pixels_range))

    for i in range(iterations):
        for r in range(3):
            for p in pixels_range:
                strip.setPixelColorRGB(p+r, *color)
            strip.show()
            if not queue.empty():
                return
            time.sleep(delay/1000.0)
            for p in pixels_range:
                strip.setPixelColor(p+r, 0)


def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)


def rainbow(strip, color, queue, delay=20, iterations=1, reverse=False, **kwargs):
    """Draw rainbow that fades across all pixels at once."""
    for i in range(256*iterations):
        for p in range(strip.numPixels()):
            strip.setPixelColor(p, wheel((p+i) & 255))
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay/1000.0)


def rainbow_cycle(strip, color, queue, delay=20, iterations=5, reverse=False, **kwargs):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for i in range(256*iterations):
        for p in range(strip.numPixels()):
            strip.setPixelColor(p, wheel((int(p * 256 / strip.numPixels()) + i) & 255))
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay/1000.0)


def theater_chase_rainbow(strip, color, queue, delay=50, iterations=1, reverse=False, **kwargs):
    """Rainbow movie theater light style chaser animation."""
    for i in range(256*iterations):
        for r in range(3):
            for p in range(0, strip.numPixels(), 3):
                strip.setPixelColor(p+r, wheel((p+i) % 255))
            strip.show()
            if not queue.empty():
                return
            time.sleep(delay/1000.0)
            for p in range(0, strip.numPixels(), 3):
                strip.setPixelColor(p+r, 0)


def pulse(strip, color, queue, delay, iterations=1, reverse=False, **kwargs):
    for p in range(strip.numPixels()):
        strip.setPixelColorRGB(p, *color)
    for i in range(255):
        strip.setBrightness(i)
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay/1000.0)
    for i in reversed(range(255)):
        strip.setBrightness(i)
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay/1000.0)


def knight_rider(strip, color, queue, delay, iterations=1, reverse=False, **kwargs):
    for active_pixel in range(strip.numPixels()):
        for i in range(strip.numPixels()):
            if i == active_pixel or i+1 == active_pixel or i-1 == active_pixel:
                strip.setPixelColorRGB(i, *color)
            else:
                strip.setPixelColorRGB(i, *(0,0,0))
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay/100.0)
    for active_pixel in reversed(range(strip.numPixels())):
        for i in range(strip.numPixels()):
            if i == active_pixel or i+1 == active_pixel or i-1 == active_pixel:
                strip.setPixelColorRGB(i, *color)
            else:
                strip.setPixelColorRGB(i, *(0,0,0))
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay/100.0)
        

def plasma(strip, color, queue, delay, iterations=1000, reverse=False, **kwargs):
    import colorsys
    import math
    pixels_range = list(range(strip.numPixels()))
    iterations_range = list(range(iterations))
    for f in iterations_range:
        for i in pixels_range:
            x = f + i
            hue = 4.0 + math.sin(x / 19.0) + math.sin(i / 9.0) + math.sin((x + i) / 25.0) + math.sin(math.sqrt(x**2.0 + i**2.0) / 8.0)
            rgb = colorsys.hsv_to_rgb(hue/8.0, 1, 1)
            color = tuple([int(round(c * 255.0)) for c in rgb])
            strip.setPixelColorRGB(i, *color)
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay/50.0)

    for f in reversed(iterations_range):
        for i in pixels_range:
            x = f + i
            hue = 4.0 + math.sin(x / 19.0) + math.sin(i / 9.0) + math.sin((x + i) / 25.0) + math.sin(math.sqrt(x**2.0 + i**2.0) / 8.0)
            rgb = colorsys.hsv_to_rgb(hue/8.0, 1, 1)
            color = tuple([int(round(c * 255.0)) for c in rgb])
            strip.setPixelColorRGB(i, *color)
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay/50.0)
