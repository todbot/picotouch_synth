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
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange

from synthio_instrument import WavePolyTwoOsc, Patch, FiltType, WaveType
from picotouch_synth import PicoTouchSynthHardware, map_range

base_note_default = 36
base_note = 36
filter_freq = 3000
filter_resonance = 1.2

# some musical scales, extended for our 17-key range
scale_mixolydian   = (0, 2, 4, 5, 7, 9, 10, 12, 14, 16)
scale_minor        = (0, 2, 3, 5, 7, 8, 10, 12, 14, 15)
scale_major        = (0, 2, 4, 5, 7, 9, 11, 12, 14, 16)
scale = scale_major

hw = PicoTouchSynthHardware()

# set up the patch that describes how this synth sounds
patchA = Patch('wtbA')
patchA.wave_type = WaveType.WTB
patchA.wave = 'PLAITS02'  # 'MICROW02' 'BRAIDS04'
patchA.wave_mix_lfo_amount = 0.23
#patchA.detune = 0  # disable 2nd oscillator
patchA.amp_env_params.attack_time = 0.2
patchA.amp_env_params.attack_level = 0.8
patchA.amp_env_params.sustain_level = 0.8
patchA.amp_env_params.release_time = 0.5
patchA.filt_env_params.attack_time = 1.5

patchB = Patch('sawB')
patchB.filt_q = 1.8
patchB.waveB = 'square'
patchA.amp_env_params.attack_time = 0.01
patchA.amp_env_params.release_time = 0.5

patchC = Patch('mixC')
patchC.detune=1.02
patchA.wave_type = WaveType.WTB
patchA.wave = 'PLAITS02'  # 'MICROW02' 'BRAIDS04'
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
    led_num = midi_note - base_note
    if led_num >=0 and led_num < 17:
        hw.leds[led_num] = 0x330033

def note_off(midi_note, vel=0):
    inst.note_off(midi_note)
    led_num = midi_note - base_note
    if led_num >=0 and led_num < 17:
        hw.leds[led_num] = 0

def note_off_all():
    inst.note_off_all()

def midi_note_on(midi_note, vel=100):
    msg = NoteOn(midi_note, velocity=vel)
    midi_usb.send( msg )
    midi_uart.send( msg )

def midi_note_off(midi_note, vel=0):
    msg = NoteOff(midi_note, velocity=vel)
    midi_usb.send( msg )
    midi_uart.send( msg )


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
            pad_num = t.key_number
            trig_num = hw.bottom_pad_to_trig_num(pad_num)

            if t.pressed:
                held_keys[pad_num] = True
                if trig_num is not None:
                    note_num = scale[trig_num]
                    note_on( base_note + note_num)

                if pad_num < 17:
                    midi_note_on(base_note + pad_num)  # act as MIDI controller

                elif pad_num == 17: # A key
                    print("load patch A")
                    inst.note_off_all()
                    inst.load_patch(patchA)
                elif pad_num == 18: # B key
                    print("load patch B")
                    inst.note_off_all()
                    inst.load_patch(patchB)
                elif pad_num == 19: # C key
                    print("load patch C")
                    inst.note_off_all()
                    inst.load_patch(patchC)
                elif pad_num == 20:  # X key, oct down
                    base_note = max(base_note - 12, 12)
                    note_off_all()
                elif pad_num == 21:  # Y key, oct up
                    base_note = min(base_note + 12, 60)
                    note_off_all()

            else: # release
                held_keys[pad_num] = False
                if trig_num is not None:
                    note_num = scale[trig_num]
                    note_off( base_note + note_num)
                if pad_num < 17:
                    midi_note_off(base_note + pad_num)  # act as MIDI controller

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
        if base_note == base_note_default:
            hw.leds[18:20] = 0x080000, 0x080000
        else:
            m = (base_note-base_note_default) // 12
            hw.leds[18] = (-0x10 * m, 0,0) if m < 0 else 0x080000
            hw.leds[19] = (0x10 * m, 0,0) if m > 0 else 0x080000

        # patch LED
        if inst.patch == patchA:
            hw.leds[17] = 0x110011
        elif inst.patch == patchB:
            hw.leds[17] = 0x001111
        elif inst.patch == patchC:
            hw.leds[17] = 0x111100

        # mod LEDs
        hw.leds_control_left( mod_left)
        hw.leds_control_mid( mod_mid)
        hw.leds_control_right( mod_right)

        hw.leds.show()
        await asyncio.sleep(0.05)

async def midi_handler():
    while True:
        # MIDI input
        while msg := midi_usb.receive() or midi_uart.receive():
            if isinstance(msg, NoteOn) and msg.velocity != 0:
                note_on(msg.note, msg.velocity)
            elif isinstance(msg,NoteOff) or isinstance(msg,NoteOn) and msg.velocity==0:
                note_off(msg.note, msg.velocity)
            elif isinstance(msg,ControlChange):
                print("CC:",msg.control, msg.value)
                if msg.control == 71:  # "sound controller 1"
                    inst.patch.wave_mix = msg.value/127
                elif msg.control == 1: # mod wheel
                    inst.patch.wave_mix_lfo_amount = msg.value/127 * 50
                    #inst.patch.wave_mix_lfo_rate = msg.value/127 * 5
                elif msg.control == 74: # filter cutoff
                    inst.patch.filt_f = msg.value/127 * 8000

        await asyncio.sleep(0.001)

async def debug_printer():
    while True:
        print("%.2f mods: %.2f %.2f %.2f base_note:%d" % (time.monotonic(), mod_left, mod_mid, mod_right, base_note) )
        await asyncio.sleep(0.3)

async def main():
    tasks = (
        asyncio.create_task(touch_updater()),
        asyncio.create_task(led_updater()),
        asyncio.create_task(instrument_updater()),
        asyncio.create_task(midi_handler()),
        asyncio.create_task(debug_printer()),
    )
    await asyncio.gather( *tasks )

print("\n----------")
print("picotouch_synth hello")

asyncio.run(main())
