import time
import math
import board
import digitalio
import usb_hid
import neopixel
import rotaryio
import busio

from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
import adafruit_ssd1306

# HID
cc = ConsumerControl(usb_hid.devices)

# Buttons
def setup_button(pin):
    btn = digitalio.DigitalInOut(pin)
    btn.direction = digitalio.Direction.INPUT
    btn.pull = digitalio.Pull.UP
    return btn

key1 = setup_button(board.D0)
key2 = setup_button(board.D1)
key3 = setup_button(board.D2)

# Encoder
encoder = rotaryio.IncrementalEncoder(board.D3, board.D4)
enc_btn = setup_button(board.D5)
last_position = encoder.position

# Neopixels
pixels = neopixel.NeoPixel(board.D6, 4, brightness=0.3, auto_write=True)

# OLED
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)

# Bongo Cat
bongo_frame = 0
last_bongo = 0

def draw_bongo():
    global bongo_frame, last_bongo
    if time.monotonic() - last_bongo > 0.2:
        bongo_frame = 1 - bongo_frame
        last_bongo = time.monotonic()

    oled.fill(0)
    oled.text(" ( ^_^ ) ", 30, 0, 1)

    if bongo_frame == 0:
        oled.text(" /|   |\\ ", 30, 12, 1)
    else:
        oled.text("  |   |  ", 30, 12, 1)

    oled.text(" /     \\ ", 30, 22, 1)
    oled.show()

# LED animation
def smooth_rainbow(step):
    for i in range(4):
        hue = (step + i * 20) % 255

        if hue < 85:
            r = int(hue * 3)
            g = int(255 - hue * 3)
            b = 0
        elif hue < 170:
            hue -= 85
            r = int(255 - hue * 3)
            g = 0
            b = int(hue * 3)
        else:
            hue -= 170
            r = 0
            g = int(hue * 3)
            b = int(255 - hue * 3)

        brightness = (math.sin(step * 0.05) + 1) / 2
        pixels[i] = (int(r * brightness),
                     int(g * brightness),
                     int(b * brightness))

# LED override
override_color = None
override_timer = 0

def trigger_led(color, duration=20):
    global override_color, override_timer
    override_color = color
    override_timer = duration

# Main loop
step = 0

while True:
    draw_bongo()

    if override_color:
        pixels.fill(override_color)
        override_timer -= 1
        if override_timer <= 0:
            override_color = None
    else:
        smooth_rainbow(step)
        step += 1

    if not key1.value:
        cc.send(ConsumerControlCode.PLAY_PAUSE)
        trigger_led((0, 255, 0))
        time.sleep(0.25)

    if not key2.value:
        cc.send(ConsumerControlCode.SCAN_PREVIOUS_TRACK)
        trigger_led((0, 0, 255))
        time.sleep(0.25)

    if not key3.value:
        cc.send(ConsumerControlCode.SCAN_NEXT_TRACK)
        trigger_led((255, 0, 0))
        time.sleep(0.25)

    position = encoder.position

    if position > last_position:
        cc.send(ConsumerControlCode.VOLUME_INCREMENT)
        trigger_led((255, 255, 0))

    elif position < last_position:
        cc.send(ConsumerControlCode.VOLUME_DECREMENT)
        trigger_led((255, 100, 0))

    last_position = position

    if not enc_btn.value:
        cc.send(ConsumerControlCode.MUTE)
        trigger_led((255, 0, 255))
        time.sleep(0.3)

    time.sleep(0.01)
