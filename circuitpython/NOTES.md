
# Saving UF2 images for releases

To save full state of Pico, use `picotool`
(available via homebrew on MacOS, build from source on Ubuntu)

Once picotool is installed, put board in BOOT mode by holding BOOTSEL on power up.
Then, save entire state of device into a 4MB UF2 file (twice the 2MB flash on a Pico) with:

```sh
picotool save -a picotouch_synth.uf2
```

Note that if you're using a 16MB Pico clone like the
[purple "RetroScaler" 16MB USB-C ones](https://www.aliexpress.us/item/3256804731684211.html),
the `-a` flag will generate a 32MB UF2 file.

So, to "fool" the RP2040 and CircuitPython into thinking a 16MB flash
(which is slower to write for some reason) is only a 2MB flash (and thus faster to write)
by doing a ranged save:

```sh
picotool save -r 0x10000000 0x10200000  picotouch_synth.uf2
```

This can be uploaded to a 16MB Pico clone and it will now look and act like a 2MB Pico.
The downside is you cannot access the other 14MB of the flash.
