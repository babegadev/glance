"""
Glance — Single Node Prototype
==================================
YD-RP2040: WS2812 NeoPixel on GPIO 23, USR button on GPIO 24.

Configure everything in the SETTINGS block below.
Press USR for a dopamine hit.
"""

import machine
import neopixel
import time
import math

# ╔═════════════════════════════════════════════════════════════════════════╗
# ║  SETTINGS — tweak these                                               ║
# ╚═════════════════════════════════════════════════════════════════════════╝

NEOPIXEL_PIN   = 23
BUTTON_PIN     = 24          # USR button
EXT_BUTTON_PIN = 2           # external trigger — short GPIO2 to GND

# Breathing
BPM            = 12          # breaths per minute at full life (normal resting human)
BPM_MIN        = 10           # slowest breathing before flatline
DECAY_SECONDS  = 4          # seconds from full life to flatline
MAX_BRIGHTNESS = 1.0         # global cap (0.0–1.0)
MIN_BRIGHTNESS = 0.1        # dimmest the breathing trough gets

# Colors (R, G, B)  — some presets:
#   Warm white: (255, 220, 180)   Cool white: (255, 255, 255)
#   Amber:      (255, 140, 20)    Candle:     (255, 100, 30)
MAIN_COLOR     = (255, 180, 107)   # resting breathe color
ACCENT_COLOR   = (100, 40, 255)    # button press color burst

# Animation
COLOR_SHIFT_MS = 8000        # total animation length after press

# ╔═════════════════════════════════════════════════════════════════════════╗
# ║  END SETTINGS                                                          ║
# ╚═════════════════════════════════════════════════════════════════════════╝

# ---------------------------------------------------------------------------
# HARDWARE
# ---------------------------------------------------------------------------
np  = neopixel.NeoPixel(machine.Pin(NEOPIXEL_PIN), 1)
btn = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
ext = machine.Pin(EXT_BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

# ---------------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------------
last_press_ms  = time.ticks_ms()
press_time_ms  = 0
anim_phase     = "idle"       # idle | animating

# Track what the LED is actually showing right now
current_color  = MAIN_COLOR
current_scale  = 0.0
breath_phase   = 0.0          # 0.0–1.0, tracks where we are in the breath cycle
last_frame_ms  = time.ticks_ms()

# Snapshot of LED state at moment of button press
snap_color     = MAIN_COLOR
snap_scale     = 0.0

# ---------------------------------------------------------------------------
# COLOR MATH
# ---------------------------------------------------------------------------
def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (lerp(c1[0], c2[0], t),
            lerp(c1[1], c2[1], t),
            lerp(c1[2], c2[2], t))

def ease_in_out_sine(t):
    return -(math.cos(math.pi * t) - 1) / 2

# ---------------------------------------------------------------------------
# LED OUTPUT
# ---------------------------------------------------------------------------
def set_led(color, scale):
    """color: (r,g,b) 0–255, scale: 0–1."""
    np[0] = (
        min(255, int(color[0] * scale * MAX_BRIGHTNESS)),
        min(255, int(color[1] * scale * MAX_BRIGHTNESS)),
        min(255, int(color[2] * scale * MAX_BRIGHTNESS)),
    )
    np.write()

# ---------------------------------------------------------------------------
# BREATHING
# ---------------------------------------------------------------------------
def elapsed_seconds():
    return time.ticks_diff(time.ticks_ms(), last_press_ms) / 1000

def decay_fraction():
    return min(elapsed_seconds() / DECAY_SECONDS, 1.0)

def breath_params(frac):
    if frac >= 1.0:
        return (0, 0.0, 0.0)

    # Use a smooth curve instead of linear so the final fade is gentle
    # This spends more time in the bright range and fades slowly at the end
    alive = (1.0 - frac) ** 0.7

    bpm = BPM_MIN + (BPM - BPM_MIN) * alive
    ceiling = MIN_BRIGHTNESS + (1.0 - MIN_BRIGHTNESS) * alive
    floor   = MIN_BRIGHTNESS * alive
    return (bpm, ceiling, floor)

def breath_value(ceiling, floor, phase):
    if ceiling <= 0:
        return 0.0

    # Real human breathing pattern (from research):
    #   I:E ratio ~1:2, with a post-exhale rest pause.
    #
    #   Inhale   25%  — active, slightly faster rise
    #   Exhale   50%  — passive elastic recoil, slow and gentle
    #   Rest     25%  — quiet pause, nearly still, before next inhale

    if phase < 0.25:
        # Inhale
        t = phase / 0.25
        v = ease_in_out_sine(t)

    elif phase < 0.75:
        # Exhale — twice as long as inhale
        t = (phase - 0.25) / 0.50
        v = 1.0 - ease_in_out_sine(t)

    else:
        # Rest pause
        t = (phase - 0.75) / 0.25
        v = 0.04 * math.sin(t * math.pi)

    return floor + v * (ceiling - floor)

def final_fade_scale(frac):
    """In the last 10% of decay, smoothly multiply everything toward 0."""
    fade_start = 0.85
    if frac < fade_start:
        return 1.0
    t = (frac - fade_start) / (1.0 - fade_start)
    # Smooth S-curve to zero
    return (1.0 - ease_in_out_sine(t))

# ---------------------------------------------------------------------------
# BUTTON PRESS ANIMATION — blends from wherever we are
#
# Timeline:
#   0–2.0s       BLOOM     — from current state, drift into accent color
#   2.0–5.0s     HOLD      — accent breathes slowly, one deep breath
#   5.0–8.0s     DISSOLVE  — melt back into main color at current decay level
# ---------------------------------------------------------------------------
BLOOM_MS    = 2000
HOLD_MS     = 5000
# DISSOLVE runs until COLOR_SHIFT_MS

def button_animation(now):
    """Animate from snapshot state through accent and back."""
    global anim_phase

    elapsed = time.ticks_diff(now, press_time_ms)

    if elapsed > COLOR_SHIFT_MS:
        anim_phase = "idle"
        return None

    # --- PHASE 1: BLOOM (0 → 2s) ---
    # From wherever we were, drift smoothly into accent at full brightness
    if elapsed < BLOOM_MS:
        t = ease_in_out_sine(elapsed / BLOOM_MS)

        color = lerp_color(snap_color, ACCENT_COLOR, t)
        scale = lerp(snap_scale, 0.85, t)

        return (color, scale)

    # --- PHASE 2: HOLD (2s → 5s) ---
    # Breathe deeply in accent. Subtle drift keeps it alive.
    elif elapsed < HOLD_MS:
        t = (elapsed - BLOOM_MS) / (HOLD_MS - BLOOM_MS)

        breath = math.sin(t * math.pi) ** 2
        scale = 0.55 + 0.35 * breath

        # Gentle hue wander
        drift = math.sin(t * math.pi * 2) * 0.12
        color = lerp_color(ACCENT_COLOR, MAIN_COLOR, max(0, drift))

        return (color, scale)

    # --- PHASE 3: DISSOLVE (5s → 8s) ---
    # Melt back into main color, land at current breathing level
    else:
        t = ease_in_out_sine((elapsed - HOLD_MS) / (COLOR_SHIFT_MS - HOLD_MS))

        color = lerp_color(ACCENT_COLOR, MAIN_COLOR, t)

        # Land where normal breathing currently is
        frac = decay_fraction()
        bpm, ceiling, floor = breath_params(frac)
        fade = final_fade_scale(frac)
        target = breath_value(ceiling, floor, breath_phase) * fade
        scale = lerp(0.6, max(target, 0.1), t)

        return (color, scale)

# ---------------------------------------------------------------------------
# BUTTON HANDLER
# ---------------------------------------------------------------------------
last_btn_state = 1
last_ext_state = 1
debounce_ms    = 200
last_debounce  = 0

def check_button():
    global last_press_ms, press_time_ms, anim_phase
    global last_btn_state, last_ext_state, last_debounce
    global snap_color, snap_scale

    now = time.ticks_ms()
    if time.ticks_diff(now, last_debounce) < debounce_ms:
        return

    # Check both inputs — either one triggers
    btn_state = btn.value()
    ext_state = ext.value()

    btn_pressed = btn_state == 0 and last_btn_state == 1
    ext_pressed = ext_state == 0 and last_ext_state == 1

    last_btn_state = btn_state
    last_ext_state = ext_state

    if btn_pressed or ext_pressed:
        last_debounce = now
        snap_color = current_color
        snap_scale = current_scale
        last_press_ms = now
        press_time_ms = now
        anim_phase = "animating"

# ---------------------------------------------------------------------------
# BOOT — a slow, warm awakening
# ---------------------------------------------------------------------------
def first_breath():
    steps = 100
    for i in range(steps):
        t = i / steps
        scale = MIN_BRIGHTNESS + (0.4 - MIN_BRIGHTNESS) * (t ** 2)
        set_led(MAIN_COLOR, scale)
        time.sleep_ms(18)
    time.sleep_ms(150)

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():

    print("Life Wall — YD-RP2040")
    print(f"BPM: {BPM} | Decay: {DECAY_SECONDS}s")
    print(f"Buttons: USR (GPIO{BUTTON_PIN}) + EXT (GPIO{EXT_BUTTON_PIN} → GND)")
    print("Press USR for dopamine.\n")

    first_breath()

    global anim_phase, current_color, current_scale
    global breath_phase, last_frame_ms
    last_debug = time.ticks_ms()
    breath_count = 0
    prev_phase = 0.0

    while True:
        check_button()
        now = time.ticks_ms()
        dt_ms = time.ticks_diff(now, last_frame_ms)
        last_frame_ms = now

        # Advance breath phase based on current BPM
        frac = decay_fraction()
        bpm, ceiling, floor = breath_params(frac)

        if bpm > 0:
            period_ms = 60_000 / bpm
            breath_phase += dt_ms / period_ms
            if breath_phase >= 1.0:
                breath_phase -= 1.0

        # Debug: count breaths
        if breath_phase < prev_phase:
            breath_count += 1
        prev_phase = breath_phase
        if time.ticks_diff(now, last_debug) > 10_000:
            actual_bpm = breath_count * 6
            print(f"Target BPM: {bpm:.1f} | Actual: ~{actual_bpm} | phase: {breath_phase:.2f}")
            breath_count = 0
            last_debug = now

        # Button animation takes priority
        if anim_phase != "idle":
            result = button_animation(now)
            if result is not None:
                color, scale = result
                current_color = color
                current_scale = scale
                set_led(color, scale)
                time.sleep_ms(10)
                continue
            else:
                anim_phase = "idle"

        # Normal breathing
        fade = final_fade_scale(frac)

        if ceiling <= 0 and fade <= 0:
            current_color = MAIN_COLOR
            current_scale = 0.0
            np[0] = (0, 0, 0)
            np.write()
            time.sleep_ms(50)
        else:
            scale = breath_value(ceiling, floor, breath_phase) * fade
            current_color = MAIN_COLOR
            current_scale = scale
            set_led(MAIN_COLOR, scale)
            time.sleep_ms(15)

if __name__ == "__main__":
    main()
