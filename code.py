# SPDX-FileCopyrightText: 2018 John Edgar Park for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""LASER SWORD (pew pew) example for Adafruit Hallowing & NeoPixel strip"""
# pylint: disable=bare-except

import time
import time, board, digitalio, neopixel
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
import analogio, supervisor

# vbat_voltage = AnalogIn(board.VOLTAGE_MONITOR)


def get_voltage(pin):
    return (pin.value * 3.3) / 65536 * 2


# battery_voltage = get_voltage(vbat_voltage)
# print("Battery voltage: {:.2f}".format(battery_voltage))
print("now with 10 pixel battery meter...")

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
SWITCH_SILVER_PIN = board.D9
SWITCH_OTHER_PIN = board.D4
EASTER_EGG_DELAY = 2
BATTERY_DELAY = 5

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

switch_silver = DigitalInOut(SWITCH_SILVER_PIN)
switch_silver.direction = Direction.INPUT
switch_silver.pull = Pull.UP

switch_red = DigitalInOut(SWITCH_OTHER_PIN)
switch_red.direction = Direction.INPUT
switch_red.pull = Pull.UP
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

    strip.fill(0)  # clear the whole blade so no leftover pixels stick around

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

vbat = analogio.AnalogIn(board.VOLTAGE_MONITOR)

# Approximate LiPo resting voltage -> percent
CURVE = [(4.20, 100), (4.10, 90), (4.00, 80), (3.90, 65), (3.80, 50),
         (3.75, 40), (3.70, 25), (3.65, 15), (3.55, 8), (3.40, 3), (3.30, 0)]

def battery_voltage(samples=16):
    total = sum(vbat.value for _ in range(samples))
    return total / samples / 65535 * 3.3 * 2

def battery_percent(v):
    if v >= CURVE[0][0]:
        return 100
    for (v_hi, p_hi), (v_lo, p_lo) in zip(CURVE, CURVE[1:]):
        if v >= v_lo:
            return p_lo + (v - v_lo) / (v_hi - v_lo) * (p_hi - p_lo)
    return 0

# v = battery_voltage()
# if supervisor.runtime.usb_connected:
#     print(f"{v:.2f} V (on USB, charging; percentage not reliable)")
# else:
#     print(f"{v:.2f} V, about {battery_percent(v):.0f}%")

def show_battery_gauge(pixels, seconds=5):
    V_MIN, V_MAX = 3.2, 4.2   # each pixel ≈ 0.012 V
    v = battery_voltage()     # read BEFORE powering/lighting pixels
    pct = battery_percent(v)
    print(f"battery {v:.2f} V, {pct:.1f}%")
    lit = max(1, min(NUM_PIXELS, round((v - V_MIN) / (V_MAX - V_MIN) * NUM_PIXELS)))
    print(lit)
    # green when healthy, yellow when getting low, red when nearly empty
    color = (0, 40, 0) if pct > 50 else (40, 30, 0) if pct > 20 else (40, 0, 0)
    enable.value = True        # power up the NeoPixel strip

    pixels.fill((0, 0, 0))
    for i in range(lit):
        pixels[i] = color
    pixels.show()
    time.sleep(seconds)
    pixels.fill((0, 0, 0))
    pixels.show()
    enable.value = False       # power the strip back down (blade is off)


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


# ---- Blaster charge-and-fire effect (both buttons held) ----
COMBO_HOLD_TIME = 1.5   # seconds both buttons must be held
COMBO_WINDOW = 0.15     # how close together the two presses must be
CHARGE_PIXELS = 20      # size of the crackling zone at the base
CRACKLE_FLICKER = 0.15  # dimmest a crackle pixel flickers down to (0..1)
CRACKLE_SPARK = 0.02    # chance per pixel per frame of a bright white spark
CHARGE_TIME = 1.2       # minimum build-up time; set to about the length of charge_up.wav
FIZZLE_TIME = 1.8       # seconds for the sparks to die out if released too early
BLAST_TIME = 0.25       # seconds for the bolt to travel base -> tip
BOLT_LENGTH = 18        # bolt head + tail, in pixels

# Bolt gradient from the leading tip (0.0) to the end of the tail (1.0):
# white tip -> blue -> purple -> black
BOLT_STOPS = [
    (0.0, (255, 255, 255)),  # white-hot tip
    (0.2, (0, 0, 255)),      # blue
    (0.6, (150, 0, 255)),    # purple
    (1.0, (0, 0, 0)),        # fades to black
]


# Crackle gradient from the base (0.0) to the top of the crackle zone (1.0):
# purple -> blue -> white -> black
CRACKLE_STOPS = [
    (0.0, (150, 0, 255)),    # purple 
    (0.25, (0, 0, 255)),     # blue
    (0.9, (100, 100, 200)),  # white
    (1.0, (0, 0, 0)),        # fades to black at the top of the zone
]


def gradient_color(stops, pos):
    """Color at pos (0..1) along a list of (position, color) stops."""
    for (p1, c1), (p2, c2) in zip(stops, stops[1:]):
        if pos <= p2:
            return mix(c1, c2, (pos - p1) / (p2 - p1))
    return stops[-1][1]


def make_bolt_colors(length):
    return [gradient_color(BOLT_STOPS, k / (length - 1)) for k in range(length)]


BOLT_COLORS = make_bolt_colors(BOLT_LENGTH)  # computed once at startup


def both_pressed():
    return not switch_silver.value and not switch_red.value


def wait_for_release():
    while not switch_silver.value or not switch_red.value:
        time.sleep(0.05)


def draw_sparks(t, brightness=1.0):
    """
    One frame of crackle. t = charge level 0..1, brightness = 0..1.
    Each pixel takes its color from CRACKLE_STOPS by position and flickers
    in brightness; the odd pixel flashes bright white.
    """
    strip.fill(0)
    # the crackle zone grows up the blade as it charges
    reach = max(3, int(CHARGE_PIXELS * (0.4 + 0.6 * t)))
    spark_chance = CRACKLE_SPARK * (0.3 + 0.7 * t)  # more sparks as it charges
    for i in range(reach):
        if random.random() < spark_chance:
            w = int(255 * brightness)
            strip[i] = (w, w, w)                         # bright white spark
        else:
            r, g, b = gradient_color(CRACKLE_STOPS, i / reach)
            f = random.uniform(CRACKLE_FLICKER, 1.0) * brightness
            strip[i] = (int(r * f), int(g * f), int(b * f))
    strip.show()


def charge(ramp_time):
    """
    Build-up sound, then a looping crackle, until BOTH buttons are released.
    Returns (charged, t): charged is True if the build-up finished,
    t is the charge level (0..1) at the moment of release.
    """
    play_wav("charge_up")
    start = time.monotonic()
    charged = False
    t = 0.0
    while not switch_silver.value or not switch_red.value:
        t = min(1.0, (time.monotonic() - start) / ramp_time)
        # fully charged once the ramp is done AND the build-up sound has ended
        if not charged and t >= 1.0 and not audio.playing:
            charged = True
            play_wav("crackle", loop=True)
        draw_sparks(t)
        time.sleep(random.uniform(0.01, 0.04))      # irregular = crackly
    return charged, t


def fizzle(start_t, duration):
    """Released too early: sparks shrink and fade out with a wind-down sound."""
    audio.stop()
    play_wav("charge_fail")
    start = time.monotonic()
    while True:
        elapsed = time.monotonic() - start
        if elapsed >= duration:
            break
        fade = 1.0 - elapsed / duration
        draw_sparks(start_t * fade, fade)
        time.sleep(random.uniform(0.02, 0.06))      # sputtering, slower
    strip.fill(0)
    strip.show()


def blast(duration):
    audio.stop()  # end the crackle loop even if blast.wav is missing
    play_wav("blast")
    start = time.monotonic()
    end_pos = NUM_PIXELS + BOLT_LENGTH  # travel until the tail clears the tip
    while True:
        t = (time.monotonic() - start) / duration
        if t >= 1.0:
            break
        head = int(end_pos * t * t)  # t*t makes the bolt accelerate
        strip.fill(0)
        for k in range(BOLT_LENGTH):
            p = head - k
            if 0 <= p < NUM_PIXELS:
                strip[p] = BOLT_COLORS[k]
        strip.show()
    strip.fill(0)
    strip.show()


def restore_blade():
    if mode == 0:  # blade was off: go dark and cut power again
        strip.fill(0)
        strip.show()
        enable.value = False
        return
    if COLOR_IDLE == RAINBOW_COLOR:
        fill_rainbow(1)
    elif COLOR_IDLE == SPARKLE_COLOR:
        strip.fill(0)
        sparkle(1)
    elif COLOR_IDLE == PONG_COLOR:
        pong(1)
    else:
        strip.fill(COLOR_IDLE)
    strip.show()


def ignite():
    """Power up the lightsaber blade with sound (same as the silver button)."""
    global mode
    enable.value = True
    power("on", 0.5, False)  # Power up!
    if COLOR_IDLE == SPARKLE_COLOR:
        play_wav(sparkle_data[SPARKLE_TYPE]["idle_sound"], loop=True)
    else:
        play_wav("idle", loop=True)  # Play background hum sound
    mode = 1  # ON (idle) mode now


def crackle_frame():
    """One frame of full-strength blaster crackle."""
    draw_sparks(1.0)
    time.sleep(random.uniform(0.01, 0.04))


def blaster_mode():
    """
    Charged blaster: crackle at the base until a button is pressed.
    Red button          = fire a blast, then back to crackling.
    Silver button       = ignite the lightsaber and leave blaster mode.
    Both held for COMBO_HOLD_TIME = cancel the charge (charge_fail sound)
                          and return to normal mode.
    After leaving, the user must charge up again to get blasts back.
    """
    global mode
    play_wav("crackle", loop=True)
    red_was_down = False
    silver_was_down = False
    while True:
        red_down = not switch_red.value
        silver_down = not switch_silver.value
        if (red_down and not red_was_down) or (silver_down and not silver_was_down):
            # give the other button a moment to join in (combo check)
            deadline = time.monotonic() + COMBO_WINDOW
            while time.monotonic() < deadline and not both_pressed():
                crackle_frame()
            if both_pressed():
                start = time.monotonic()
                while both_pressed():
                    if time.monotonic() - start >= COMBO_HOLD_TIME:
                        fizzle(1.0, FIZZLE_TIME)  # charge_fail sound + fade
                        wait_for_release()
                        mode = 0              # normal mode = blade off
                        restore_blade()       # strip dark, power cut
                        return
                    crackle_frame()
                # combo let go too early: ignore it, keep crackling
                while not switch_silver.value or not switch_red.value:
                    crackle_frame()
                red_was_down = silver_was_down = False
                continue
            if silver_down:
                strip.fill(0)
                strip.show()
                ignite()
                while not switch_silver.value:  # wait for release
                    time.sleep(0.05)
                return
            # red press (acted on even if it was a quick tap)
            blast(BLAST_TIME)
            play_wav("crackle", loop=True)  # back to crackling
        red_was_down = not switch_red.value
        silver_was_down = not switch_silver.value
        crackle_frame()


def check_combo():
    """Returns True if this press was the two-button combo (fully handled)."""
    global mode
    deadline = time.monotonic() + COMBO_WINDOW
    while time.monotonic() < deadline and not both_pressed():
        time.sleep(0.01)
    if not both_pressed():
        return False  # single press: let the normal handlers deal with it
    start = time.monotonic()
    while both_pressed():
        if time.monotonic() - start >= COMBO_HOLD_TIME:
            enable.value = True
            charged, t = charge(CHARGE_TIME)  # returns once both are released
            if charged:
                blaster_mode()  # red fires; silver ignites; combo cancels
                return True
            fizzle(t, FIZZLE_TIME)
            mode = 0          # normal mode = blade off
            restore_blade()   # strip dark, power cut
            return True
        time.sleep(0.02)
    wait_for_release()  # combo abandoned early: swallow the release
    return True


# dummy = False
# Main program loop, repeats indefinitely
is_rainbow = False
TRIGGER_TIME = time.monotonic()  # Save initial time of hit
while True:

    # red_led.value = True
    blue_led.value = True

    if (not switch_silver.value or not switch_red.value) and check_combo():
        continue

    if not switch_red.value and mode == 0 and (time.monotonic() - TRIGGER_TIME) > 5:
        print("SHOWING BATTERY LEVEL")
        show_battery_gauge(strip)
    if not switch_red.value and mode > 0:
        COLOR = NEXT_COLOR
        COLOR_IDLE = (int(COLOR[0] / 2), int(COLOR[1] / 2), int(COLOR[2] / 2))
        COLOR_HIT = (255,255,255)
        COLOR_SWING = COLOR
        if COLOR == BLUE_COLOR:
            NEXT_COLOR = GREEN_COLOR
        elif COLOR == GREEN_COLOR:
            NEXT_COLOR = RED_COLOR
        elif COLOR == RED_COLOR:
            NEXT_COLOR = PURPLE_COLOR
        elif COLOR == PURPLE_COLOR:
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
        while not switch_red.value:  # Wait for button release
            if (time.monotonic() - TRIGGER_TIME) > EASTER_EGG_DELAY:
                if COLOR == PURPLE_COLOR:
                    COLOR = RAINBOW_COLOR
                    COLOR_HIT = RAINBOW_COLOR
                    COLOR_SWING = RAINBOW_COLOR
                    COLOR_IDLE = RAINBOW_COLOR
                    play_wav("rainbow")
                    fill_rainbow(1)
                elif COLOR == BLUE_COLOR:
                    SPARKLE_TYPE = "blue"
                    COLOR = SPARKLE_COLOR
                    COLOR_HIT = SPARKLE_COLOR
                    COLOR_SWING = SPARKLE_COLOR
                    COLOR_IDLE = SPARKLE_COLOR
                    if "tx_sound" in sparkle_data[SPARKLE_TYPE]:
                        play_wav(sparkle_data[SPARKLE_TYPE]["tx_sound"])
                    sparkle(1)
                elif COLOR == RED_COLOR:
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


    if not switch_silver.value:  # button pressed?
        #    if not dummy:
        dummy = True
        if mode == 0:  # If currently off...
            ignite()  # Power up, start the hum, mode = 1
        else:  # else is currently on...
            power("off", 0.5, True)  # Power down
            mode = 0  # OFF mode now
            enable.value = False
        while not switch_silver.value:  # Wait for button release
            time.sleep(0.2)  # to avoid repeated triggering

    elif mode >= 1:  # If not OFF mode...
        x, y, z = accel.acceleration  # Read accelerometer
        accel_total = x * x + z * z
        # (Y axis isn't needed for this, assuming Hallowing is mounted
        # sideways to stick.  Also, square root isn't needed, since we're
        # just comparing thresholds...use squared values instead, save math.)
        # if switch_red:
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
                # Check COLOR_IDLE (always holds the easter-egg marker),
                # not COLOR_ACTIVE, so marker colors never reach the strip
                if COLOR_IDLE == RAINBOW_COLOR:
                    fill_rainbow(mode)
                elif COLOR_IDLE == SPARKLE_COLOR:
                    sparkle(mode)
                elif COLOR_IDLE == PONG_COLOR:
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
