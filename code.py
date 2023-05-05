# SPDX-FileCopyrightText: 2018 John Edgar Park for Adafruit Industries
# SPDX-License-Identifier: MIT
# Updated by Joey Fortuna (2022)

"""LASER SWORD (pew pew) example for Adafruit Hallowing & NeoPixel strip"""
# pylint: disable=bare-except
 
import time
import math
import gc
from digitalio import DigitalInOut, Direction, Pull
import audioio
import audiocore
import busio
import board
import neopixel
import adafruit_lis3dh
import random
from analogio import AnalogIn

vbat_voltage = AnalogIn(board.VOLTAGE_MONITOR)


def get_voltage(pin):
    return (pin.value * 3.3) / 65536 * 2


battery_voltage = get_voltage(vbat_voltage)
print("VBat voltage: {:.2f}".format(battery_voltage))

# CUSTOMIZE YOUR COLOR HERE:
# (red, green, blue) -- each 0 (off) to 255 (brightest)
# COLOR = (255, 0, 0)  # red
WHITE_COLOR = (200, 200, 200) 
COLOR = (150, 0, 255)  # purple
BLUE_COLOR = (0, 0, 255) 
GREEN_COLOR = (0, 255, 0)
PURPLE_COLOR = (100, 0, 255)
RED_COLOR = (255, 0, 0)
RAINBOW_COLOR = (-1, -1, -1)
SPARKLE_COLOR = (-2, -2, -2)
PONG_COLOR = (-3, -3, -3)
RAINBOW = [
    (255, 0, 0),
    (200, 100, 0),
    (200, 255, 0),
    (100, 255, 0),
    (0, 255, 0),
    (0, 0, 255),
    (100, 0, 200),
    (200, 0, 100),
]
NEXT_COLOR = BLUE_COLOR
# COLOR = (0, 100, 255) #cyan

# CUSTOMIZE SENSITIVITY HERE: smaller numbers = more sensitive to motion
HIT_THRESHOLD = 550  # 250
SWING_THRESHOLD = 125

NUM_PIXELS = 85
# NUM_PIXELS = 85
NEOPIXEL_PIN = board.D5
POWER_PIN = board.D10
SWITCH_PIN = board.D9
OTHER_SWITCH_PIN = board.D4

enable = DigitalInOut(POWER_PIN)
enable.direction = Direction.OUTPUT
enable.value = False

red_led = DigitalInOut(board.D11)
red_led.direction = Direction.OUTPUT
green_led = DigitalInOut(board.D12)
green_led.direction = Direction.OUTPUT
blue_led = DigitalInOut(board.D13)
blue_led.direction = Direction.OUTPUT

audio = audioio.AudioOut(board.A0)  # Speaker
mode = 0  # Initial mode = OFF

strip = neopixel.NeoPixel(NEOPIXEL_PIN, NUM_PIXELS, brightness=1, auto_write=False)
strip.fill(0)  # NeoPixels off ASAP on startup
strip.show()

switch = DigitalInOut(SWITCH_PIN)
switch.direction = Direction.INPUT
switch.pull = Pull.UP

other_switch = DigitalInOut(OTHER_SWITCH_PIN)
other_switch.direction = Direction.INPUT
other_switch.pull = Pull.UP
time.sleep(0.1)

# Set up accelerometer on I2C bus, 4G range:
i2c = busio.I2C(board.SCL, board.SDA)
accel = adafruit_lis3dh.LIS3DH_I2C(i2c)
accel.range = adafruit_lis3dh.RANGE_4_G

# "Idle" color is 1/4 brightness, "swinging" color is full brightness...
COLOR_IDLE = (int(COLOR[0] / 2), int(COLOR[1] / 2), int(COLOR[2] / 2))
COLOR_SWING = COLOR
COLOR_HIT = (255, 255, 255)  # "hit" color is white


sparkle_data = {
    "blue": {
        "hit": (255, 255, 255),
        "idle_sound": "idle_blue",
        "tx_sound": "wave_blue",
        "swing_sound": ["wave_blue","wave_blue2"],
        "swing": (0, 255, 255),
        "gradient": [
            (0, 0, 255),
            (0, 50, 255),
            (0, 100, 200),
            (0, 150, 200),
            (0, 200, 200),
        ],
    },
    "red": {
        "hit": (255, 255, 0),
        "tx_sound": "tx_red",
        "idle_sound": "idle_red",
        "swing_sound": "tx_red",
        "hit_sound": "hit_red",
        "swing": (255, 0, 0),
        "gradient": [
            (255, 0, 0),
            (255, 0, 0),
            (200, 100, 0),
            (200, 100, 0),
            (255, 150, 0),
            (255, 255, 0),
        ],
    },
}

NUM_SPARKLES = 60
SPARKLE_TYPE = "blue"
SPARKLE_DELAY = 0.0001
SPARKLE_TIMEIN = 0
FLIP_FLOP = False
float_increment = 0.0
sparkling_pix = [-1] * NUM_SPARKLES
sparkling_inc = [0.0] * NUM_SPARKLES
for i in range(0, NUM_SPARKLES):
    sparkling_inc[i] = random.random()
sparkling_bool = [False] * NUM_SPARKLES
indx = 0
while indx < NUM_SPARKLES:
    pix = random.randint(0, NUM_PIXELS - 1)
    if pix not in sparkling_pix:
        sparkling_pix[indx] = pix
        indx += 1

print(sparkling_pix)

pong_iterator = 0;
pong_incrementor = 1;
pong_ff = False
pong_timein = 0
GRAVITY = 9.8
velocity = 0.0
def get_velocity(v,accel, delta_time):
    return velocity + GRAVITY * delta_time

def pong(mode):
    global pong_iterator
    global pong_ff
    global pong_incrementor
    global pong_timein

    strip[pong_iterator] = (0,0,0)
    strip[pong_iterator+1] = (0,0,0)
    strip[pong_iterator+2] = (0,0,0)

    x, y, z = accel.acceleration  # Read accelerometer
    if (y>5):
        if (pong_incrementor<=0 and (time.monotonic()-pong_timein)>1):
            play_wav("wave_pong")
            pong_timein = time.monotonic()
        pong_incrementor = 1
    elif (y<-5):
        if (pong_incrementor>=0 and (time.monotonic()-pong_timein)>1):
            play_wav("wave_pong")
            pong_timein = time.monotonic()
        pong_incrementor = -1
    else:
        pong_incrementor = 0

    pong_iterator+=pong_incrementor
    if pong_iterator>=NUM_PIXELS-4 and pong_incrementor>0:
        #pong_incrementor = -pong_incrementor
        pong_iterator = NUM_PIXELS-4
    elif pong_iterator<=0 and pong_incrementor<0:
        #pong_incrementor = -pong_incrementor
        pong_iterator = 0
    strip[pong_iterator] = (0,255,0)
    strip[pong_iterator+1] = (0,255,0)
    strip[pong_iterator+2] = (0,255,0)


def sparkle(mode):
    global sparkle_data
    global SPARKLE_TIMEIN
    global sparkling_bool
    global sparkling_inc
    global sparkling_pix

    if time.monotonic() - SPARKLE_TIMEIN < SPARKLE_DELAY:
        return False
    sd = sparkle_data[SPARKLE_TYPE]
    SEGMENT = NUM_PIXELS / len(sd["gradient"])
    for i in range(0, NUM_SPARKLES):
        weight = sparkling_inc[i]
        ff = sparkling_bool[i]
        pix = sparkling_pix[i]
        if ff:
            weight = 1 - weight
        if mode == 2:
            colr = mix((0, 0, 0), sd["swing"], weight)
        elif mode == 3:
            colr = mix((0, 0, 0), sd["hit"], weight)
        else:
            colr= mix((0,0,0), sd["gradient"][-1],weight)
            match = False
            for k in range(0, len(sd["gradient"])):
                section = (k + 1) * SEGMENT
                if pix < section:
                    match = True
                    colr = mix((0, 0, 0), sd["gradient"][k], weight)
                    break
        strip[pix] = colr
        sparkling_inc[i] += 0.1
        if sparkling_inc[i] > 1.0:
            sparkling_inc[i] = 0.0
            if not ff:
                newpix = random.randint(0, NUM_PIXELS - 1)
                while newpix == pix or newpix in sparkling_pix:
                    newpix = random.randint(0, NUM_PIXELS - 1)
                sparkling_pix[i] = newpix
            sparkling_bool[i] = not sparkling_bool[i]
    for i in range(0, NUM_PIXELS):
        if i not in sparkling_pix:
            strip[i] = (0, 0, 0)
    SPARKLE_TIMEIN = time.monotonic()
    return True


def fill_rainbow(mode):
    indx = 0
    for i in range(0, NUM_PIXELS):
        colr = RAINBOW[indx]
        if (i + 1) % 7 == 0:
            indx += 1
            if indx > 7:
                indx = 0
        if mode == 1:
            colr = (int(colr[0] / 2), int(colr[1] / 2), int(colr[2] / 2))
        elif mode == 3:
            colr = (255, 255, 255)
        strip[i] = colr


def play_wav(name, loop=False):
    """
    Play a WAV file in the 'sounds' directory.
    @param name: partial file name string, complete name will be built around
                 this, e.g. passing 'foo' will play file 'sounds/foo.wav'.
    @param loop: if True, sound will repeat indefinitely (until interrupted
                 by another sound).
    """
    print("playing", name)
    try:
        wave_file = open("sounds/" + name + ".wav", "rb")
        wave = audiocore.WaveFile(wave_file)
        audio.play(wave, loop=loop)
    except Exception as e:
        print(e)
        return


def power(sound, duration, reverse):
    """
    Animate NeoPixels with accompanying sound effect for power on / off.
    @param sound:    sound name (similar format to play_wav() above)
    @param duration: estimated duration of sound, in seconds (>0.0)
    @param reverse:  if True, do power-off effect (reverses animation)
    """
    if reverse:
        prev = NUM_PIXELS
    else:
        prev = 0
    gc.collect()  # Tidy up RAM now so animation's smoother
    start_time = time.monotonic()  # Save audio start time
    play_wav(sound)
    while True:
        elapsed = time.monotonic() - start_time  # Time spent playing sound
        if elapsed > duration:  # Past sound duration?
            break  # Stop animating
        fraction = elapsed / duration  # Animation time, 0.0 to 1.0
        if reverse:
            fraction = 1.0 - fraction  # 1.0 to 0.0 if reverse
        fraction = math.pow(fraction, 0.5)  # Apply nonlinear curve
        threshold = int(NUM_PIXELS * fraction + 0.5)
        # print(threshold)
        num = threshold - prev  # Number of pixels to light on this pass
        if num != 0:
            if reverse:
                strip[threshold:prev] = [0] * -num
            else:
                strip[prev:threshold] = [COLOR_IDLE] * num
            strip.show()
            # NeoPixel writes throw off time.monotonic() ever so slightly
            # because interrupts are disabled during the transfer.
            # We can compensate somewhat by adjusting the start time
            # back by 30 microseconds per pixel.
            start_time -= NUM_PIXELS * 0.00003
            prev = threshold

    if reverse:
        strip.fill(0)  # At end, ensure strip is off
    else:
        strip.fill(COLOR_IDLE)  # or all pixels set on
    strip.show()
    while audio.playing:  # Wait until audio done
        pass


def mix(color_1, color_2, weight_2):
    """
    Blend between two colors with a given ratio.
    @param color_1:  first color, as an (r,g,b) tuple
    @param color_2:  second color, as an (r,g,b) tuple
    @param weight_2: Blend weight (ratio) of second color, 0.0 to 1.0
    @return: (r,g,b) tuple, blended color
    """
    if weight_2 < 0.0:
        weight_2 = 0.0
    elif weight_2 > 1.0:
        weight_2 = 1.0
    weight_1 = 1.0 - weight_2
    return (
        int(color_1[0] * weight_1 + color_2[0] * weight_2),
        int(color_1[1] * weight_1 + color_2[1] * weight_2),
        int(color_1[2] * weight_1 + color_2[2] * weight_2),
    )


# dummy = False
# Main program loop, repeats indefinitely
is_rainbow = False
while True:

    # red_led.value = True
    blue_led.value = True

    if not other_switch.value and mode > 0:
        COLOR = NEXT_COLOR
        COLOR_IDLE = (int(COLOR[0] / 2), int(COLOR[1] / 2), int(COLOR[2] / 2))
        COLOR_HIT = (255,255,255)
        COLOR_SWING = COLOR
        if COLOR == BLUE_COLOR:
            print("to blue")
            NEXT_COLOR = GREEN_COLOR
        elif COLOR == GREEN_COLOR:
            print("to green")
            NEXT_COLOR = RED_COLOR
        elif COLOR == RED_COLOR:
            print("to red")
            NEXT_COLOR = PURPLE_COLOR
        elif COLOR == PURPLE_COLOR:
            print("to purple")
            NEXT_COLOR = BLUE_COLOR
        COLOR_ACTIVE = COLOR
        TRIGGER_TIME = time.monotonic()  # Save initial time of hit
        play_wav("switch_color")
        for k in range(0, 5):
            strip.fill(WHITE_COLOR)
            strip.show()
            time.sleep(0.05)
            strip.fill(COLOR_ACTIVE)
            strip.show()
            time.sleep(0.05)
        while not other_switch.value:  # Wait for button release
            if (time.monotonic() - TRIGGER_TIME) > 3:
                if COLOR == PURPLE_COLOR:
                    print("Switching to RAINBOW")
                    COLOR = RAINBOW_COLOR
                    COLOR_HIT = RAINBOW_COLOR
                    COLOR_SWING = RAINBOW_COLOR
                    COLOR_IDLE = RAINBOW_COLOR
                    play_wav("rainbow")
                    fill_rainbow(1)
                elif COLOR == BLUE_COLOR:
                    print("Switching to CATTLE PROD")
                    SPARKLE_TYPE = "blue"
                    COLOR = SPARKLE_COLOR
                    COLOR_HIT = SPARKLE_COLOR
                    COLOR_SWING = SPARKLE_COLOR
                    COLOR_IDLE = SPARKLE_COLOR
                    if "tx_sound" in sparkle_data[SPARKLE_TYPE]:
                        play_wav(sparkle_data[SPARKLE_TYPE]["tx_sound"])
                    sparkle(1)
                elif COLOR == RED_COLOR:
                    print("Switching to FIRE SWORD")
                    SPARKLE_TYPE = "red"
                    COLOR = SPARKLE_COLOR
                    COLOR_HIT = SPARKLE_COLOR
                    COLOR_SWING = SPARKLE_COLOR
                    COLOR_IDLE = SPARKLE_COLOR
                    if "tx_sound" in sparkle_data[SPARKLE_TYPE]:
                        play_wav(sparkle_data[SPARKLE_TYPE]["tx_sound"])
                    sparkle(1)
                elif COLOR == GREEN_COLOR:
                    print("Switching to PONG")
                    strip.fill(0)
                    strip.show()
                    COLOR = PONG_COLOR
                    COLOR_HIT = PONG_COLOR
                    COLOR_SWING = PONG_COLOR
                    COLOR_IDLE = PONG_COLOR
                    pong_timein = time.monotonic()
                    play_wav("tx_green")
                    pong(1)
                strip.show()
            time.sleep(0.2)  # to avoid repeated triggering

    if not switch.value:  # button pressed?
        #    if not dummy:
        dummy = True
        if mode == 0:  # If currently off...
            enable.value = True
            power("on", 0.5, False)  # Power up!
            if COLOR_IDLE == SPARKLE_COLOR:
                play_wav(sparkle_data[SPARKLE_TYPE]["idle_sound"], loop=True)
            else:
                play_wav("idle", loop=True)  # Play background hum sound
            mode = 1  # ON (idle) mode now
        else:  # else is currently on...
            power("off", 0.5, True)  # Power down
            mode = 0  # OFF mode now
            enable.value = False
        while not switch.value:  # Wait for button release
            time.sleep(0.2)  # to avoid repeated triggering

    elif mode >= 1:  # If not OFF mode...
        x, y, z = accel.acceleration  # Read accelerometer
        accel_total = x * x + z * z
        # (Y axis isn't needed for this, assuming Hallowing is mounted
        # sideways to stick.  Also, square root isn't needed, since we're
        # just comparing thresholds...use squared values instead, save math.)
        # if other_switch:
        if accel_total > HIT_THRESHOLD:  # Large acceleration = HIT
            TRIGGER_TIME = time.monotonic()  # Save initial time of hit
            if COLOR_IDLE == SPARKLE_COLOR and "hit_sound" in sparkle_data[SPARKLE_TYPE]:
                snd = sparkle_data[SPARKLE_TYPE]["hit_sound"]
                play_wav(snd)
            elif COLOR_IDLE == RAINBOW_COLOR:
                play_wav("hit_rainbow")
            elif COLOR_IDLE == PONG_COLOR:
                pass
            else:
                play_wav("hit")  # Start playing 'hit' sound
            COLOR_ACTIVE = COLOR_HIT  # Set color to fade from
            mode = 3  # HIT mode
        elif mode == 1 and accel_total > SWING_THRESHOLD:  # Mild = SWING
            TRIGGER_TIME = time.monotonic()  # Save initial time of swing
            if COLOR_IDLE == SPARKLE_COLOR and "swing_sound" in sparkle_data[SPARKLE_TYPE]:
                snd = sparkle_data[SPARKLE_TYPE]["swing_sound"]
                if isinstance(snd, list):
                    k = random.randint(0,len(snd)-1)
                    snd = snd[k]
                play_wav(snd)
            elif COLOR_IDLE == RAINBOW_COLOR:
                k = random.randint(0,1)
                k+=1
                snd = "wave_rainbow%d" % k
                play_wav(snd)
            elif COLOR_IDLE == PONG_COLOR:
                pass
            else:
                play_wav("swing")  # Start playing 'swing' sound
            COLOR_ACTIVE = COLOR_SWING  # Set color to fade from
            mode = 2  # SWING mode
        elif mode > 1:  # If in SWING or HIT mode...
            if audio.playing:  # And sound currently playing...
                blend = time.monotonic() - TRIGGER_TIME  # Time since triggered
                if mode == 2:  # If SWING,
                    blend = abs(0.5 - blend) * 2.0  # ramp up, down
                if COLOR_ACTIVE == RAINBOW_COLOR:
                    fill_rainbow(mode)
                elif COLOR_ACTIVE == SPARKLE_COLOR:
                    sparkle(mode)
                elif COLOR_ACTIVE == PONG_COLOR:
                    pong(mode)
                else:
                    strip.fill(mix(COLOR_ACTIVE, COLOR_IDLE, blend))
                strip.show()
            else:  # No sound now, but still MODE > 1
                if COLOR_IDLE == SPARKLE_COLOR:
                    play_wav(sparkle_data[SPARKLE_TYPE]["idle_sound"], loop=True)
                elif COLOR_IDLE == RAINBOW_COLOR:
                    play_wav("idle_rainbow",loop=True)
                elif COLOR_IDLE == PONG_COLOR:
                    pass
                else:
                    play_wav("idle", loop=True)  # Resume background hum
                if COLOR_IDLE == RAINBOW_COLOR:
                    fill_rainbow(1)
                elif COLOR_IDLE == SPARKLE_COLOR:
                    sparkle(1)
                elif COLOR_IDLE == PONG_COLOR:
                    pong(1)
                else:
                    strip.fill(COLOR_IDLE)  # Set to idle color
                strip.show()
                mode = 1  # IDLE mode now
        elif COLOR_IDLE == SPARKLE_COLOR:
            # print("sparkle")
            if sparkle(1):
                strip.show()
        elif COLOR_IDLE == PONG_COLOR:
            pong(1)
            strip.show()
        if mode==1 and not audio.playing:
            if COLOR_IDLE == SPARKLE_COLOR:
                play_wav(sparkle_data[SPARKLE_TYPE]["idle_sound"], loop=True)
            elif COLOR_IDLE == RAINBOW_COLOR:
                play_wav("idle_rainbow",loop=True)
            elif COLOR_IDLE == PONG_COLOR:
                pass
            else:
                play_wav("idle", loop=True)  # Resume background hum
