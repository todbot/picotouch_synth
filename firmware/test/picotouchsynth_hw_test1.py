
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

touch_threshold_adjust = 500

touch_ins = []
touchs = []
for pin in touch_pins:
    print("pin:",pin)
    touchin = touchio.TouchIn(pin)
    #touchin.threshold += touch_threshold_adjust
    touch_ins.append(touchin)
    touchs.append( Debouncer(touchin) )


print("\n----------")
print("picotouchsynth hello")
while True:
    for i in range(len(touchs)):
        touch = touchs[i]
        touch.update()
        if touch.rose:
            print("press",i)
            #midi.send( NoteOn(midi_base_note + i, midi_velocity) )
        if touch.fell:
            print("release",i)
            #midi.send( NoteOff(midi_base_note + i, midi_velocity) )

