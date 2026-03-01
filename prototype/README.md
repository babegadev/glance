# Prototype

A single-node proof of concept for the decay and breathing mechanism. No custom PCB, no enclosure — just the core interaction running on a YD-RP2040.

## Hardware

**YD-RP2040** — used because it has a built-in NeoPixel LED (GPIO 23) and a user button (GPIO 24), so no wiring needed to test the core loop. The NeoPixel uses the WS2812B protocol, same as the LEDs planned for the final hardware.

There's also an external trigger input on GPIO 2 — short it to GND to simulate a press without using the onboard button.

## What it tests

- Breathing animation that slows and dims as time passes since last press
- Flatline behavior when the decay window expires
- Button press → revive animation (bloom, hold, dissolve back to main color)
- Boot animation

## Settings

Everything is configurable at the top of `main.py`:

| Setting | Default | What it does |
|---|---|---|
| `BPM` | 12 | Breathing rate at full life |
| `BPM_MIN` | 10 | Slowest breath before flatline |
| `DECAY_SECONDS` | 4 | Time from full life to flatline |
| `MAX_BRIGHTNESS` | 1.0 | Global brightness cap |
| `MAIN_COLOR` | warm white | Resting color |
| `ACCENT_COLOR` | purple | Button press burst color |

`DECAY_SECONDS` is set low (4s) for fast iteration. In production, this would be days.

## Running it

Copy `main.py` to the root of the YD-RP2040 via Thonny or `mpremote`. It runs on boot.
