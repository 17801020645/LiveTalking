---
name: LiveTalking
description: Dark broadcast gallery for a dual-role digital-human control plane
---

<!-- SEED: established with the user before implementation; re-run /impeccable document once there's code to capture the actual tokens and components. -->

# Design System: LiveTalking

## Overview

**Creative North Star: "The Glass Control Deck" as a broadcast gallery**

Operators sit in a dim machine room and watch live avatars the way a gallery watches previews: framed monitors, tally lights, a thin rail. The wall is matte near-black; glass sits on the bezels, not as a pale SaaS card stack. Electric Indigo is the only brand wash. Green and red are tally, never decoration.

Density is plush: large corners, generous padding, real lift. Motion is gallery grammar—tally snap, a monitor taking program—not bounce or generic hover glow.

**Key Characteristics:**
- Dark matte wall, frost glass on frames
- Preview monitors as the reusable signature object
- Electric Indigo as the single brand accent
- Tally lights for live / idle / fault
- Plush scale: thick bezels, large type for counts, strong but local shadows

## Colors

Restrained: near-black neutrals plus one accent. The physical scene is a dim GPU room, so the system is dark.

### Primary
- **Electric Indigo** (#4361ee / #3f37c9): brand wash on the rail, program tally, and the one active frame. Rarity is the point.

### Neutral
- **Gallery Wall** (#111318): page ground, the black wall behind monitors.
- **Program Paper** (#f8fafc): ink on dark frames and count numerals when they must read as lit glass.
- Remaining steps: `[to be resolved during implementation]`

### Named Rules
**The Tally Rule.** Green and red are lamps on a bezel. They are not brand colors and not pastel badges.

**The One Wash Rule.** Electric Indigo is the only chromatic brand field. If a screen is mostly indigo, the wash has leaked.

## Typography

**Display Font:** condensed instrument caps for counts and tally labels `[face to be resolved during implementation; must cover Chinese UI]`
**Body Font:** a Chinese workhorse grotesque for tasks and nav `[face to be resolved during implementation]`
**Label/Mono Font:** `[to be resolved during implementation]` — only if a readout needs measured digits.

**Character:** Gallery labels, not marketing display. Counts read like tally numerals; sentences stay quiet.

### Hierarchy
- **Display**: the three home counts, large enough to read across a desk.
- **Title**: monitor names (待处理订单 / 活跃连麦 / 生成中).
- **Body**: helper lines and the live-console link.
- **Label**: tally text, username, rail items.

### Named Rules
**The No-Inter-Hero Rule.** Inter is not the display face. Body may fall back to a system stack only until the Chinese workhorse is locked.

## Layout

A thin left rail, not a 240px indigo slab. The main field is a gallery wall: important work lives in framed monitors that share one rhythm. On a narrow screen the wall stacks to a single column of monitors; the rail becomes a short strip. Exact grid and breakpoints: `[to be resolved during implementation]`.

## Elevation & Depth

Layered frost on a dark wall. Frames sit forward with real shadow; the wall stays flat. Glass is a coating on the bezel, not a white floating card on a pastel wash.

### Named Rules
**The Wall-Is-Flat Rule.** The page ground does not lift. Only a monitor frame, a toast, or a pressed control casts shadow.

## Shapes

Plush: large-radius monitor corners, thick bezels, pill tally lamps. No hairline SaaS cards. Exact radii: `[to be resolved during implementation]`.

## Do's and Don'ts

### Do:
- **Do** put the job inside a framed preview with a tally lamp.
- **Do** keep Electric Indigo rare and the wall dark.
- **Do** size the three counts so they work as program numbers.
- **Do** use frost and lift only on frames and pressed controls.

### Don't:
- **Don't** ship the current light cool-paper dashboard (Inter, 240px indigo sidebar, nested glass cards) as this world.
- **Don't** scatter neon, void-scrollers, or poster noise over the task.
- **Don't** turn green/red into brand stripes.
- **Don't** invent customers, testimonials, or metrics the product does not have.
