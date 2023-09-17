# picotouch_synth demo.py -- demo synth for picotouch_synth
# 1 Sep 2023 - @todbot / Tod Kurt
# Part of https://github.com/todbot/picotouch_synth

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

# set up the patch that describes how this synth sounds
patchA = Patch('wtbA')
patchA.wave_type = WaveType.WTB
patchA.wave = 'PLAITS02'  # 'MICROW02' 'BRAIDS04'
patchA.wave_mix_lfo_amount = 0.23
#patchA.detune = 0  # disable 2nd oscillator
patchA.amp_env_params.attack_time = 0.2
patchA.amp_env_params.attack_level = 0.8
patchA.amp_env_params.release_time = 0.5

patchB = Patch('sawB')
patchB.filt_q = 1.8
patchB.waveB = 'square'
patchA.amp_env_params.attack_time = 0.01
patchA.amp_env_params.release_time = 0.5

patchC = Patch('mixC')
patchC.detune=1.02
patchC.waveB = 'square'  # show off wavemixing
patchC.filt_type = FiltType.BP
patchC.filt_q = 0.5
patchC.filt_env_params.attack_time = 0.5
patchC.filt_env_params.attack_level = 0.8
patchC.amp_env_params.release_time = 1.0

mod_left = 0.02
mod_mid = 0.3
mod_right = 0.02

# set up the instrument that holds the patch
inst = WavePolyTwoOsc(hw.synth, patchA)

midi_uart = adafruit_midi.MIDI(midi_out=hw.uart, midi_in=hw.uart)
midi_usb = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], midi_in=usb_midi.ports[0])


def note_on(midi_note, vel=100):
    inst.note_on(midi_note)
    hw.leds[midi_note-base_note] = 0x330033

def note_off(midi_note, vel=0):
    inst.note_off(midi_note)
    hw.leds[midi_note-base_note] = 0x010001

def note_off_all():
    inst.note_off_all()

print("\n----------")
print("picotouch_synth hello")


async def instrument_updater():
    while True:
        inst.update()
        await asyncio.sleep(0.01)  # as fast as possible

async def touch_updater():
    global mod_left, mod_mid, mod_right, base_note

    held_keys = [False] * hw.num_touch_pads

    while True:
        touches = hw.check_touch()
        for t in touches:
            print("t:",t)
            if t.pressed:
                held_keys[t.key_number] = True
                #if hw.is_mode_key(t.key_number):
                #    print("mode key")
                if hw.is_bottom_note_key(t.key_number):
                    note_on( base_note + t.key_number)
                elif t.key_number == 17: # A key
                    print("load patch A")
                    inst.note_off_all()
                    inst.load_patch(patchA)
                elif t.key_number == 18: # B key
                    print("load patch B")
                    inst.note_off_all()
                    inst.load_patch(patchB)
                elif t.key_number == 19: # C key
                    print("load patch C")
                    inst.note_off_all()
                    inst.load_patch(patchC)
                elif t.key_number == 20:  # X key, oct down
                    base_note = max(base_note - 12, 12)
                    note_off_all()
                elif t.key_number == 21:  # Y key, oct up
                    base_note = max(base_note + 12, 60)
                    note_off_all()

            else: # release
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

        inst.patch.wave_mix = mod_right
        inst.patch.filt_f = 100 + mod_mid * 4000
        inst.patch.wave_mix_lfo_amount = mod_left * 2
        #inst.patch.filt_f = 50 + mod_mid * 8000

        await asyncio.sleep(0.0)

async def led_updater():
    while True:
        # octave up/down leds
        if base_note == 36:  # FIXME
            hw.leds[18:20] = 0x110000, 0x110000
        else:
            hw.leds[18] = 0x110000 if base_note < 36 else 0
            hw.leds[19] = 0x110000 if base_note > 36 else 0
        # patch LED
        if inst.patch == patchA:
            hw.leds[17] = 0x110011
        elif inst.patch == patchB:
            hw.leds[17] = 0x001111
        elif inst.patch == patchC:
            hw.leds[17] = 0x111100
        hw.leds_control_left( mod_left)
        hw.leds_control_mid( mod_mid)
        hw.leds_control_right( mod_right)

        await asyncio.sleep(0.03)

async def debug_printer():
    while True:
        print("%.2f mods: %.2f %.2f %.2f" % (time.monotonic(), mod_left, mod_mid, mod_right) )
        await asyncio.sleep(0.3)

async def main():
    task1 = asyncio.create_task(touch_updater())
    task2 = asyncio.create_task(led_updater())
    task3 = asyncio.create_task(instrument_updater())
    task4 = asyncio.create_task(debug_printer())
    await asyncio.gather(task1, task2, task3, task4)

asyncio.run(main())
