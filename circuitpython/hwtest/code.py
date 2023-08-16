print("Hello World!")


import time, board, busio
import audiomixer, synthio, audiopwmio
import neopixel
import touchio
from adafruit_debouncer import Debouncer



SAMPLE_RATE=28000

num_leds = 19
neopixel_pin = board.GP26
pwm_audio_pin = board.GP22
uart_rx_pin = board.GP21
uart_tx_pin = board.GP20

touch_pins = (board.GP0, board.GP1, board.GP2, board.GP3, board.GP4, board.GP5,
              board.GP6, board.GP7 ,board.GP8, board.GP9, board.GP10, board.GP11,
              board.GP12, board.GP13, board.GP14, board.GP15, board.GP16,
              board.GP17, board.GP18, board.GP19,
              board.GP27, board.GP28)


audio = audiopwmio.PWMAudioOut(pwm_audio_pin)
mixer = audiomixer.Mixer(voice_count=1, sample_rate=SAMPLE_RATE, channel_count=1,
                         bits_per_sample=16, samples_signed=True, buffer_size=2048 ) # buffer_size=4096 )
audio.play(mixer)

uart = busio.UART(rx=uart_rx_pin, tx=uart_tx_pin, baudrate=31250, timeout=0.001)

leds = neopixel.NeoPixel(neopixel_pin, num_leds, brightness=0.1)


while True:
    print("hi")
    time.sleep(1)
