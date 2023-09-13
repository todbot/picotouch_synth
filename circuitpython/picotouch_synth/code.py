import asyncio
import time
import ulab.numpy as np
import synthio
import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn

from synthio_instrument import WavePolyTwoOsc, Patch, FiltType, WaveType
from picotouch_synth import PicoTouchSynthHardware, map_range

base_note = 36
filter_freq = 4000
filter_resonance = 1.2

hw = PicoTouchSynthHardware()

patchA = Patch('fourfor')
patchA.wave_type = WaveType.WTB
patchA.wave = 'PLAITS02'  # 'MICROW02' 'BRAIDS04'
patchA.wave_mix_lfo_amount = 0.23
#patchA.detune = 0  # disable 2nd oscillator
patchA.amp_env_params.release_time = 0.5

inst = WavePolyTwoOsc(hw.synth, patchA)
inst.reload_patch()

# set up midi
midi_uart = adafruit_midi.MIDI(midi_out=hw.uart, midi_in=hw.uart)
midi_usb = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], midi_in=usb_midi.ports[0])


def note_on(midi_note, vel=100):
    inst.note_on(midi_note)
    hw.leds[midi_note-base_note] = 0x330033

def note_off(midi_note, vel=0):
    inst.note_off(midi_note)
    hw.leds[midi_note-base_note] = 0x000000

print("\n----------")
print("picotouch_synth hello")

mod_left = 0.02
mod_mid = 0.02
mod_right = 0.02

async def instrument_updater():
    while True:
        inst.update()
        await asyncio.sleep(0.01)  # as fast as possible

async def touch_updater():
    global mod_left, mod_mid, mod_right

    held_keys = [False] * hw.num_touch_pads

    while True:
        touches = hw.check_touch()
        for t in touches:
            print("t:",t)
            if t.pressed:
                held_keys[t.key_number] = True
                if hw.is_mode_key(t.key_number):
                    print("mode key")
                elif hw.is_bottom_note_key(t.key_number):
                    note_on( base_note + t.key_number)
            else:
                held_keys[t.key_number] = False
                if hw.is_bottom_note_key(t.key_number):
                    note_off( base_note + t.key_number)

        for key_number, held in enumerate(held_keys):
            if held:
                # mod_left keys
                if key_number == 1:
                    mod_left = max( mod_left - 0.02, 0.02)
                elif key_number == 3:
                    mod_left =  min(mod_left + 0.02, 0.98)
                # mod_mid keys
                elif key_number == 6:
                    mod_mid = max( mod_mid - 0.02, 0.02)
                elif key_number == 8:
                    mod_mid = 0.5
                elif key_number == 10:
                    mod_mid =  min(mod_mid + 0.02, 0.98)
                # mod_right keys
                elif key_number == 13:
                    mod_right = max( mod_right - 0.02, 0.02)
                elif key_number == 15:
                    mod_right =  min(mod_right + 0.02, 0.98)

        inst.patch.wave_mix_lfo_amount = mod_left

        await asyncio.sleep(0.0)

async def led_updater():
    while True:
        #hw.leds_control_left( mod_left, hue=map_range(inst.wave_lfo.value,0,1, 0.00,0.15) )
        hw.leds_control_left( mod_left)
        hw.leds_control_mid( mod_mid)
        hw.leds_control_right( mod_right)
        await asyncio.sleep(0.03)

async def debug_printer():
    while True:
        print("hi %.2f %.2f %.2f %.2f" % (time.monotonic(), mod_left, mod_mid, mod_right) )
        await asyncio.sleep(0.3)

async def main():
    task1 = asyncio.create_task(touch_updater())
    task2 = asyncio.create_task(led_updater())
    task3 = asyncio.create_task(instrument_updater())
    task4 = asyncio.create_task(debug_printer())
    await asyncio.gather(task1, task2, task3, task4)

asyncio.run(main())
