# Hardware

## Form factor

Hexagonal pucks, ~70mm flat-to-flat, ~15–20mm thick. Flat-top orientation — flat edges on top and bottom, pointy on the sides. Nodes are all identical and fully interchangeable.

The cluster grows in any direction. Add a node when you start something new, pull one off when you let it go.

## Enclosure

Goal is for it to read as art before it reads as tech. Options being explored:

- Frosted/translucent resin — light diffuses evenly through the whole body
- Wood veneer face with light bleeding through the grain
- Matte white or warm grey with soft edge glow
- Brushed aluminum frame with frosted acrylic face

No visible screws, seams, or components from the front.

## Lighting

The whole hex should glow, not just a point. Options:

- **Full-body diffusion** — LED(s) centered inside a translucent shell, node itself is the light source
- **Edge glow** — LEDs around the perimeter, light bleeds inward, darker center
- **Underglow bleed** — LEDs on the back, light spills onto the wall behind the node. When the cluster is healthy, the whole wall section is bathed in soft light
- **Hybrid** — full-body diffusion + underglow. Node glows and casts light on the wall

When a node flatlines, the dark gap in the honeycomb is the signal. No badge, no alert — just absence.

## Button

The node should look like a solid seamless object. Options:

- **Whole-body press** — spring-mounted front plate, ~1–2mm travel, the entire face is the button
- **Magnetic press** — front plate held by magnets with a small gap, press clicks it inward against a switch, magnets return it
- **Hidden microswitch** — slightly recessed center area flexes inward when pressed

Whole-body or magnetic press are preferred — both keep the seamless look and feel more satisfying.

## Labels

- **Backlit cutout** — icon cut through an opaque top layer, backed by the diffuser. Glows when alive, invisible when flatlined. The label only exists when the habit does.
- **Color coding** — each node a distinct color, no text. You learn the map.
- Likely a hybrid of both: color for recognition at a distance, icon for up close.

## Mounting

### Wall mount

A laser-cut steel backing plate mounts to the wall (2–4 hidden screws). Nodes snap to it magnetically — no individual fasteners. The cluster can be rearranged freely without touching the wall.

A **Powerizer** — a small magnetic accessory — snaps onto any free edge of any node. One USB-C cable in, done.

### Desktop stand

A low-profile wedge (~15° tilt) holds the cluster at a comfortable viewing angle. Weighted base (cast concrete, steel-filled resin, or a hidden weight bar) so it doesn't tip when a node is pressed. Powerizer is built into the back of the stand — USB-C in, power feeds up through the bottom row of nodes.

Same nodes work in both modes.

---

## Electronics (per node)

| Component | Part | Notes |
|---|---|---|
| MCU | ATtiny1614 | Real I2C, 16KB flash, 5V native, UPDI programming |
| Crystal | 32.768kHz, 12.5pF | Sleep-based timekeeping, no external RTC |
| LED | SK6812 ×2 | WS2812B-compatible, better low-brightness uniformity |
| Schottky diode | BAT54C (dual SOT-23) ×3 | Power OR-ing, reverse protection, backfeed prevention |
| PTC fuse | Bourns MF-MSMF110 ×6 | Per-edge overcurrent protection, self-resetting |
| DIP switch | DIP-6 | 3 switches for decay speed (8 presets), 3 for color (8 options) |
| Magnets | N52 neodymium disc, 6×3mm ×12 | 2 per edge — alignment, hold force, orientation enforcement |
| Edge contacts | Gold-plated PCB pads | VCC + GND per edge, 12 contacts total |
| Decoupling caps | 100nF MLCC 0402 ×4 | — |
| Load caps | 12pF MLCC 0402 ×2 | Crystal load capacitance |
| PCB | Custom hex, 2-layer | KiCad, fabricated at JLCPCB |

No LDO — 5V rail throughout. Power comes in exclusively through edge contacts.

## Power architecture

One cable powers the whole cluster. Nodes have no USB-C port — power enters via a **Powerizer** accessory that snaps onto any free edge. From there it flows node to node through magnetic edge contacts.

### Edge contact layout

Every edge is identical:

```
[ magnet ][ VCC (top) | GND (bottom) ][ magnet ]
```

VCC and GND are stacked vertically (not side by side) so face-to-face mirroring never crosses the rails.

### Schottky OR-ing

All 6 edge VCC inputs go through a Schottky diode before joining the internal rail:

```
Edge 0–5 VCC ──[D1–D6]──┬── VCC Rail ──► MCU, LEDs
USB-C VBUS   ──[D7]─────┘   (Powerizer only)

Edge 0–5 GND ──[PTC fuse each]──── GND Rail
```

This lets multiple edges receive power simultaneously, blocks reverse current, and prevents backfeed into neighboring nodes.

**Components:** BAT54C (dual Schottky, SOT-23) — 3 packages per node covers all 6 edges. Bourns MF-MSMF110 PTC fuses, 150mA hold / 300mA trip.

### Magnet polarity

Alternating N-S-N-S-N-S clockwise from the top edge:

```
        top [N]
upper-left [S]   [S] upper-right
lower-left [N]   [N] lower-right
        bottom [S]
```

In a hex tessellation, opposing edges are always 3 positions apart — which in an alternating pattern are always opposite polarity. So touching edges always attract, in all 6 neighbor positions. Nodes rotated by 60°, 180°, or 300° repel — making wrong placement physically impossible.

## Powerizer

A standalone accessory. No MCU, no LED.

| Component | Part |
|---|---|
| USB-C connector | Power-only, 2-pin |
| Magnets | N52 disc, 6×3mm ×2 |
| Contact pins | Pogo pins, VCC + GND |
| Enclosure | Flat puck or half-hex, FDM or cast |

The desktop stand has a Powerizer built into its back face. The wall mount Powerizer is a separate snap-on puck.

## Cost estimate (qty 50–100)

| Scenario | Per-node cost |
|---|---|
| Electronics only | ~$4.50 |
| + FDM enclosure | ~$5.50 |
| + Resin print enclosure | ~$7.00 |
| + Cast resin enclosure | ~$10.00+ |

Costs drop ~20–30% at qty 500+, primarily from PCB and magnet bulk pricing.

Each node draws ~100–200mA peak. A 2A USB-C supply handles 10–15 nodes comfortably.
