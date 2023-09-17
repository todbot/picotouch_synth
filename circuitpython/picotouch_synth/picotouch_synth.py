# picotouch_synth.py -- hardware definitions and functions for picotouch_synth
# 1 Sep 2023 - @todbot / Tod Kurt
# Part of https://github.com/todbot/picotouch_synth
#
import time
import board, busio, digitalio
import audiomixer, synthio, audiopwmio
import neopixel
import touchio
import touchpio
import keypad  # to use KeypadEvent
from adafruit_debouncer import Button
import adafruit_fancyled.adafruit_fancyled as fancy

from synthio_instrument import map_range, lerp

SAMPLE_RATE=28000
touch_threshold_adjust = 300

# pin definitions

num_leds = 20
neopixel_pin = board.GP26
pwm_audio_pin = board.GP22
uart_rx_pin = board.GP21
uart_tx_pin = board.GP20
pico_pwr_pin = board.GP23  # HIGH = improved ripple (lower noise) but less efficient

touch_pins = (board.GP0, board.GP1, board.GP2, board.GP3, board.GP4, board.GP5,
              board.GP6, board.GP7 ,board.GP8, board.GP9, board.GP10, board.GP11,
              board.GP12, board.GP13, board.GP14, board.GP15, board.GP16,
              board.GP17, board.GP18, board.GP19,
              board.GP27, board.GP28)

#touch_ctrl_pins = (board.GP1, board.GP3, board.GP6, board.GP8, board.GP10, board.GP13, board.GP15)
# touch_key_pins = (board.GP0, board.GP2, board.GP4, board.GP5,
#                   board.GP7, board.GP9, board.GP11,
#                   board.GP14, board.GP16)
# touch_mod_pins = ( board.GP17, board.GP18, board.GP19,
#                    board.GP27, board.GP28)
# touch_pins = touch_key_pins + touch_mod_pins

bot_keys = (0,2,4,5,7,9,11,12,14,16)
top_keys = (1,3,  6,8,10,  13,15)  #
mode_keys = (17,18,19, 20,21)  # A, B, C, X, Y


class PicoTouchSynthHardware():
    def __init__(self, sample_rate=SAMPLE_RATE, buffer_size=2048, touch_adjust_threshold=300):
        self.leds= neopixel.NeoPixel(neopixel_pin, num_leds, brightness=0.2)
        self.uart = busio.UART(rx=uart_rx_pin, tx=uart_tx_pin, baudrate=31250, timeout=0.001)

        # make power supply less noisy on real Picos
        self.pwr_mode = digitalio.DigitalInOut(pico_pwr_pin)
        self.pwr_mode.switch_to_output(value=True)

        self.touch_ins = []  # for debug
        self.touch_pads = []
        #self.touch_cache = []
        for pin in touch_pins:
            touchin = touchio.TouchIn(pin)
            touchin.threshold += touch_threshold_adjust
            self.touch_pads.append( Button(touchin, value_when_pressed=True))
            self.touch_ins.append(touchin)  # for debug
            #self.touch_cache.append(touchin.raw_value)
        self.num_touch_pads = len(self.touch_pads)
        self.audio = audiopwmio.PWMAudioOut(pwm_audio_pin)
        self.mixer = audiomixer.Mixer(voice_count=1, sample_rate=sample_rate,
                                      channel_count=1, bits_per_sample=16,
                                      samples_signed=True, buffer_size=buffer_size )
        self.audio.play(self.mixer)
        self.synth = synthio.Synthesizer(sample_rate=SAMPLE_RATE)
        self.mixer.voice[0].level = 0.75 # turn down the volume a bit since this can get loud
        self.mixer.voice[0].play(self.synth)

    def set_synth_volume(self,v):
        self.mixer.voice[0].level = v

    def fade_leds(self,fade_by=5):
        # FIXME: use np
        self.leds[:] = [[max(i-fade_by,0) for i in l] for l in self.leds]

    def is_bottom_note_key(self,i):
        return i in bot_keys

    def is_top_key(self,i):
        return i in top_keys

    def is_mode_key(self,i):
        return i in mode_keys

    def leds_control_left(self, v, hue=0.05):
        color1 = fancy.CHSV( hue, 0.98, 0.25 * 1-v)
        color2 = fancy.CHSV( hue, 0.98, 0.25 * v)
        self.leds[1] = color1.pack()
        self.leds[3] = color2.pack()

    def leds_control_mid(self,v, hue=0.30):
        color1 = fancy.CHSV( hue, 0.98, 0.25 * 1-v)
        color2 = fancy.CHSV( hue, 0.98, 0.25 * 0.5)
        color3 = fancy.CHSV( hue, 0.98, 0.25 * v)
        self.leds[6] = color1.pack()
        self.leds[8] = color2.pack()
        self.leds[10] = color3.pack()

    def leds_control_right(self,v, hue=0.98):
        color1 = fancy.CHSV( 0.6, 0.98, 0.25 * 1-v)
        color2 = fancy.CHSV( 0.6, 0.98, 0.25 * v)
        self.leds[13] = color1.pack()
        self.leds[15] = color2.pack()

    def check_touch(self):
        events = []
        st = time.monotonic()
        for i in range(self.num_touch_pads):
            touch = self.touch_pads[i]
            touch.update()
            if touch.pressed:
                events.append(keypad.Event(i,True))
            elif touch.released:
                events.append(keypad.Event(i,False))
        #print("check_touch:",int((time.monotonic()-st)*1000))
        return events

    def check_touch_hold(self, hold_func):
        for i in range(self.num_touch_pads):
            if self.touch_ins[i].value:  # pressed
                v = self.touchins[i].raw_value - self.touchins[i].threshold
                hold_func(i, v)
