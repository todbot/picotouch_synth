# pts_drum_machine code.py -- drum machine for picotouch_synth
# 1 Oct 2023 - @todbot / Tod Kurt
# Part of https://github.com/todbot/picotouch_synth

import asyncio
import os
import audiocore
import rainbowio
import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

from synthio_instrument import WavePolyTwoOsc, Patch
from picotouch_synth import PicoTouchSynthHardware

base_note = 24
drum_dir = "drum_wavs"

SAMPLE_RATE = 11025

# FIXME: put these in PicoTouchSynthHardware
num_pads = 17
num_trig_pads = 10

hw = PicoTouchSynthHardware(sample_rate=SAMPLE_RATE, num_voices=num_trig_pads)

midi_uart = adafruit_midi.MIDI(midi_out=hw.uart, midi_in=hw.uart)
midi_usb = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], midi_in=usb_midi.ports[0])


class DrumMachine:
    def __init__(self, drum_dir, kit_name, num_trigs):
        self.drum_dir = drum_dir
        self.num_trig_pads = num_trigs
        self.load_kit(kit_name)

    def load_kit(self, kit_name):
        self.kit_name = kit_name
        self.drum_fnames = [None] * self.num_trig_pads  # maximum number
        wav_list = []
        for fname in sorted(os.listdir( self.drum_dir + '/' + self.kit_name )):
            if fname.lower().endswith('.wav') and not fname.startswith('.'):
                wav_list.append(fname)
        for i in range(self.num_trig_pads):
            fprefix = "%02d" % i
            fns = [fn for fn in wav_list if fn.startswith(fprefix)]
            if len(fns):  # if there's a match
                self.drum_fnames[i] = drum_dir + "/" + self.kit_name + '/' + fns[0]
        self.kit_size = self.calc_kit_size()
        return self.drum_fnames

    def calc_kit_size(self):
        """ """
        kit_size = self.num_trig_pads
        for i in range(self.num_trig_pads):
            if not self.drum_fnames[ self.num_trig_pads-i-1 ]:
                kit_size = i
        return kit_size

    def play_drum(self, num, vel=100):
        print("play_drum",num)
        wav_fname = self.drum_fnames[ num ]
        loopit = False   # FIXME
        voice = hw.mixer.voice[num]
        if wav_fname is not None:
            try:
                wave = audiocore.WaveFile(open(wav_fname,"rb"))
                voice.play(wave,loop=loopit)
            except (OSError, ValueError) as e:
                print(e)

    def stop_drum(self, num, vel=0):
        wav_fname = self.drum_fnames[ num ]
        loopit = False
        voice = hw.mixer.voice[num]
        if loopit:
            voice.stop()  # only stop looping samples, others one-shot


dm = DrumMachine( drum_dir, 'kitA', num_trig_pads )

held_pads = [False] * hw.num_touch_pads
#pad_states = [False] * num_pads  #

def note_on(midi_note, vel=100):
    pad_num = midi_note - base_note
    dm.play_drum( pad_num )

def note_off(midi_note, vel=0):
    pad_num = midi_note - base_note
    dm.stop_drum( pad_num )

def note_off_all():
    pass

def midi_note_on(midi_note, vel=100):
    msg = NoteOn(midi_note, velocity=vel)
    midi_usb.send( msg )
    midi_uart.send( msg )

def midi_note_off(midi_note, vel=0):
    msg = NoteOff(midi_note, velocity=vel)
    midi_usb.send( msg )
    midi_uart.send( msg )

async def touch_updater():
    global base_note

    while True:
        touches = hw.check_touch()
        for t in touches:
            pad_num = t.key_number
            trig_num = hw.bottom_pad_to_trig_num(pad_num)
            print("pad:",pad_num, t.pressed, "trig:",trig_num)

            if t.pressed:  # pad pressed
                held_pads[pad_num] = True

                if trig_num is not None:  # it was a trigger pad, act as drum machine
                    note_on(base_note + trig_num)
                    print(pad_num, trig_num)

                if pad_num < 17:
                    midi_note_on(base_note + pad_num)  # act as MIDI controller
                elif pad_num == 17: # A key
                    print("load patch A")
                    dm.load_kit('kitA')
                elif pad_num == 18: # B key
                    print("load patch B")
                    dm.load_kit('kitB')
                elif pad_num == 19: # C key
                    print("load patch C")
                    dm.load_kit('kitC')
                elif pad_num == 20:  # X key, oct down
                    base_note = max(base_note - 12, 0)
                    note_off_all()
                elif pad_num == 21:  # Y key, oct up
                    base_note = min(base_note + 12, 60)
                    note_off_all()
            else:  # release
                held_pads[pad_num] = False
                if trig_num is not None:  # act as drum machine
                    note_off(base_note + trig_num)
                if pad_num < 17:
                    midi_note_off( base_note + pad_num )  # act as MIDI controller

        await asyncio.sleep(0.0)

async def led_updater():
    fade_by = 5
    while True:
        # show sample status for key pads
        for i in range(num_pads):
            if held_pads[i]:  # key pressed
                hw.leds[i] = 0x222222
            else:
                #pad_num = hw.trig_num_to_pad_num(i)
                #hw.leds[i] = hw.leds[17] if dm.drum_fnames[i] else 0x080000
                hw.leds[i] = hw.leds[17] # if dm.drum_fnames[i] else 0x080000

        # octave up/down leds
        if base_note == 24:  # FIXME, center point is midi note 24
            hw.leds[18:20] = 0x080000, 0x080000
        else:
            m = (base_note-24) // 12
            hw.leds[18] = (-0x08 * m, 0,0) if m < 0 else 0x040000
            hw.leds[19] = (0x08 * m, 0,0) if m > 0 else 0x040000

        # kit select LED
        if dm.kit_name == 'kitA':
            hw.leds[17] = 0x080008
        elif dm.kit_name == 'kitB':
            hw.leds[17] = 0x000808
        elif dm.kit_name == 'kitC':
            hw.leds[17] = 0x110800

        hw.leds.show()
        await asyncio.sleep(0.03)

async def midi_handler():
    while True:
        # MIDI input
        while msg := midi_usb.receive() or midi_uart.receive():
            if isinstance(msg, NoteOn) and msg.velocity != 0:
                note_on(msg.note, msg.velocity)
            elif isinstance(msg,NoteOff) or isinstance(msg,NoteOn) and msg.velocity==0:
                note_off(msg.note, msg.velocity)
        await asyncio.sleep(0)

async def main():
    tasks = (
        asyncio.create_task(touch_updater()),
        asyncio.create_task(led_updater()),
        asyncio.create_task(midi_handler()),
    )
    await asyncio.gather( *tasks )


print("\n----------")
print("pts_drum_machine hello")

asyncio.run(main())
