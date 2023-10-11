# picotouch_synth.py -- hardware definitions and functions for picotouch_synth
# 1 Sep 2023 - @todbot / Tod Kurt
# Part of https://github.com/todbot/picotouch_synth
#
import time
import board, busio, digitalio
import audiomixer, synthio, audiopwmio
import neopixel
import touchio
import keypad  # to use KeypadEvent
import adafruit_fancyled.adafruit_fancyled as fancy

from synthio_instrument import map_range, lerp

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

top_pads = (1,3,  6,8,10,  13,15)     # "black" keys
bot_pads = (0,2,4,5,7,9,11,12,14,16)  # "white" keys
mode_pads = (17,18,19, 20,21)         # A, B, C, X, Y


class PicoTouchSynthHardware():
    def __init__(self, sample_rate=28000, num_voices=1, buffer_size=2048, touch_threshold_adjust=300):
        self.leds= neopixel.NeoPixel(neopixel_pin, num_leds, brightness=0.2, auto_write=False)
        self.uart = busio.UART(rx=uart_rx_pin, tx=uart_tx_pin, baudrate=31250, timeout=0.001)

        # make power supply less noisy on real Picos
        self.pwr_mode = digitalio.DigitalInOut(pico_pwr_pin)
        self.pwr_mode.switch_to_output(value=True)

        self.touch_ins = []  # for debug
        for pin in touch_pins:
            touchin = touchio.TouchIn(pin)
            touchin.threshold += touch_threshold_adjust
            self.touch_ins.append(touchin)
        self.num_touch_pads = len(self.touch_ins)
        self.last_touch_vals = [t.value for t in self.touch_ins]  # get initial value

        self.synth_voicenum = num_voices-1
        self.audio = audiopwmio.PWMAudioOut(pwm_audio_pin)
        self.mixer = audiomixer.Mixer(voice_count=num_voices, sample_rate=sample_rate,
                                      channel_count=1, bits_per_sample=16,
                                      samples_signed=True, buffer_size=buffer_size )
        self.audio.play(self.mixer)
        self.synth = synthio.Synthesizer(sample_rate=sample_rate)
        self.mixer.voice[self.synth_voicenum].level = 0.75 # turn down the volume a bit since this can get loud
        self.mixer.voice[self.synth_voicenum].play(self.synth)

    def set_synth_volume(self,v):
        self.mixer.voice[self.synth_voicenum].level = v

    def fade_leds(self,fade_by=5):
        # FIXME: use np
        self.leds[:] = [[max(i-fade_by,0) for i in l] for l in self.leds]

    def is_bottom_pad(self,i):
        return i in bot_pads

    def bottom_pad_to_trig_num(self,padnum):
        try:
            return bot_pads.index(padnum)
        except ValueError:
            return None

    def trig_num_to_pad_num(self,trig_num):
        return bot_pads[trig_num]

    def bottom_pad_to_keynum(self,i):
        try:
            return bot_pads.index(i)
        except ValueError:
            return None

    def is_top_pad(self,i):
        return i in top_pads

    def is_mode_pad(self,i):
        return i in mode_pads

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

    # using Debouncer instead of Button: 15 millis vs 24 millis
    # using DIY debouncer instead of Debouncer: 9 millis vs 15 millis
    # using PIO on 7 pads: 8 millis vs 9 millis
    def check_touch(self):
        events = []
        st = time.monotonic()
        for i in range(self.num_touch_pads):
            touch_val = self.touch_ins[i].value
            last_touch_val = self.last_touch_vals[i]
            if touch_val and not last_touch_val:
                events.append(keypad.Event(i,True))
            if not touch_val and last_touch_val:
                events.append(keypad.Event(i,False))
            self.last_touch_vals[i] = touch_val
        #print("check_touch:",int((time.monotonic()-st)*1000))
        return events

    def check_touch_hold(self, hold_func):
        for i in range(self.num_touch_pads):
            if self.touch_ins[i].value:  # pressed
                v = self.touchins[i].raw_value - self.touchins[i].threshold
                hold_func(i, v)
