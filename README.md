# picotouch_synth

Thin captouch-based synth platform for Raspberry Pi Pico

<img width=500 src="./docs/picotouch_synth_flip_case_render1.jpg"/>

Features:
* PWM Audio out
* TRS-A MIDI In / Out
* USB MIDI In/Out
* 19 RGB LEDs
* 22 touch pads (17 notes, 5 modifiers)
* Completely flat surface (only reverse-mount LEDs, capsense pads)

<img width=600 src="./docs/picotouch_synth_flip_render_top.png"/>
<img width=600 src="./docs/picotouch_synth_flip_render_bot.png"/>


## Installing firmware

### Prebuilt UF2 images

If you want to install pre-built firmware for picotouch_synth,
go to the [Releases](https://github.com/todbot/picotouch_synth/releases) page
and download the UF2 you want.  Then, to install:

* Unplug picotouch_synth PCB board from USB
* Unclip PCB from case (if in a case)
* Hold BOOT button on Pico while plugging back into USB
* Copy the UF2 file to the RPI-RP2 drive
* When board is reflashed, it will reboot

__Note:__ if your Pico has more than the 2 MB standard flash
(like the purple USB-C 16 MB Pico clones), the UF2s will still work but the
resulting CIRCUITPY drive only be 1 MB.


## Sketching in Hardware 2023 Edition

For Sketching in Hardware conference, the firmware shipped on the boards is in
[circuitpython/picotouch_synth](https://github.com/todbot/picotouch_synth/tree/main/circuitpython/picotouch_synth)
and the pre-built UF2 firwmare in the [Releases section](https://github.com/todbot/picotouch_synth/releases/tag/v1).

The keyboard is laid out as top row is modulators (three groups of "sliders")
and the bottom row plays notes in a particular scale.

<img width=700 src="./docs/picotouch_synth_ui_sketching2023.png"/>
