# picotouchsynth_hw_test1.py -- test picotouchsynth 23 Nov 2022 PCB
# 30 Nov 2022 - @todbot / Tod Kurt
# Part of https://github.com/todbot/picotouchsynth/

import time
import board
import touchio
import neopixel
import rainbowio
from adafruit_debouncer import Debouncer

touch_pins = (
    board.GP0, board.GP1, board.GP2, board.GP3, board.GP4, board.GP5,
    board.GP6, board.GP7, board.GP8, board.GP9, board.GP10, board.GP11,
    board.GP12, board.GP13, board.GP14, board.GP15,
)

led_pin = board.GP16
disp_sda_pin = board.GP20
disp_scl_pin = board.GP21
midi_pin = board.GP17
audio_pin = board.GP28

touch_ins = []
touchs = []
for pin in touch_pins:
    print("pin:",pin)
    touchin = touchio.TouchIn(pin)
    #touchin.threshold += touch_threshold_adjust
    touch_ins.append(touchin)
    touchs.append( Debouncer(touchin) )

num_leds = 13
leds = neopixel.NeoPixel(led_pin, num_leds, brightness=0.2, auto_write=True)

print("\n----------\npicotouchsynth hello")

for i in range(255):
    leds.fill( rainbowio.colorwheel(i) )  # a little celebratory show
    time.sleep(0.01)
leds.fill(0x111111)

while True:
    for i in range(len(touchs)):
        touch = touchs[i]
        touch.update()
        if touch.rose:
            print("press",i)
            leds[i] = rainbowio.colorwheel( time.monotonic()*50 )
            #midi.send( NoteOn(midi_base_note + i, midi_velocity) )
        if touch.fell:
            leds[i] = 0x111111
            print("release",i)
            #midi.send( NoteOff(midi_base_note + i, midi_velocity) )
