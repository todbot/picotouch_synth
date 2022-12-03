// https://gist.github.com/todbot/27c34c55d36002c601b2c28ae8f1b8a4
// and https://github.com/adafruit/circuitpython/blob/main/shared-module/touchio/TouchIn.c
//
//////////////

#define N_SAMPLES 10
#define TIMEOUT_TICKS 10000

class FakeyTouch
{
  public:
    FakeyTouch( int apin = 0 ) {
      pin = apin;
    }

    void begin() {
      baseline = readTouch();
      threshold = (baseline * 1.05) + 100;
    }

    int readTouch() {
      uint16_t ticks = 0;
      for (uint16_t i = 0; i < N_SAMPLES; i++) {
        // set pad to digital output high for 10us to charge it
        pinMode(pin, OUTPUT);
        digitalWrite(pin, HIGH);
        delayMicroseconds(10);
        // set pad back to an input and take some samples
        pinMode(pin, INPUT);
        while ( digitalRead(pin) ) {
          if (ticks >= TIMEOUT_TICKS) {
            return TIMEOUT_TICKS;
          }
          ticks++;
        }
      }
      raw_val_last = ticks;
      return ticks;
    }

    int readTouch0() {
      pinMode(pin, OUTPUT);
      digitalWrite(pin, HIGH);
      delayMicroseconds(10);
      pinMode(pin, INPUT);
      int i = 0;
      while ( digitalRead(pin) ) {
        i++;
      }
      raw_val_last = i;
      return i;
    }

    bool isTouched() {
      return (readTouch() > threshold);
    }

    int pin;
    uint16_t baseline;
    uint16_t threshold;
    uint16_t raw_val_last;
};
///////////////////
