---
name: LiveTalking
description: Dark broadcast gallery for a dual-role digital-human control plane
colors:
  gallery-wall: "#111318"
  program-paper: "#f8fafc"
  electric-indigo: "#4361ee"
  indigo-deep: "#3f37c9"
  bezel: "#16181f"
  screen: "#07080c"
  ink-quiet: "#c5cdd8"
  tally-live: "#22c55e"
  tally-fault: "#ef4444"
  tally-idle: "#8d95a3"
  tally-warn: "#f59e0b"
typography:
  display:
    fontFamily: "Barlow Condensed, Noto Sans SC, sans-serif"
    fontSize: "5.25rem"
    fontWeight: 700
    lineHeight: 0.9
    letterSpacing: "-0.03em"
  body:
    fontFamily: "Noto Sans SC, Source Han Sans SC, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  title:
    fontFamily: "Noto Sans SC, Source Han Sans SC, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "normal"
rounded:
  sm: "8px"
  md: "10px"
  lg: "22px"
spacing:
  sm: "8px"
  md: "16px"
  lg: "28px"
components:
  button-primary:
    backgroundColor: "{colors.electric-indigo}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: "8px 16px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink-quiet}"
    rounded: "{rounded.sm}"
    padding: "8px 12px"
  monitor-frame:
    backgroundColor: "{colors.bezel}"
    textColor: "{colors.program-paper}"
    rounded: "{rounded.lg}"
    padding: "22px 18px 20px"
  nav-link-active:
    backgroundColor: "rgba(67, 97, 238, 0.16)"
    textColor: "{colors.program-paper}"
    rounded: "{rounded.md}"
    padding: "11px 12px"
---

# Design System: LiveTalking

## Overview

**Creative North Star: "The Glass Control Deck" as a broadcast gallery**

Operators sit in a dim machine room and watch live avatars the way a gallery watches previews: framed monitors, tally lights, a thin rail. The wall is matte near-black; glass sits on the bezels, not as a pale SaaS card stack. Electric Indigo is the only brand wash. Green and red are tally, never decoration.

Density is plush: large corners, generous padding, real lift. Motion is gallery grammar—tally snap, a monitor taking program—not bounce or generic hover glow.

These tokens come from the shipped `.gallery` scope in `frontend/src/styles.css`. Light `:root` leftovers (`--bg: #f0f4fc`, 240px indigo sidebar) are not this world.

**Key Characteristics:**
- Dark matte wall, frost glass on frames
- Preview monitors as the reusable signature object
- Electric Indigo as the single brand accent
- Tally lights for live / idle / fault
- Plush scale: thick bezels, large type for counts, strong but local shadows

## Colors

Restrained: near-black neutrals plus one accent. The physical scene is a dim GPU room, so the system is dark. Normative values live on `.gallery`, not `:root`.

### Primary
- **Electric Indigo** (`#4361ee` / `#3f37c9`): brand wash on the rail, program tally, and the one active frame. Rarity is the point.

### Neutral
- **Gallery Wall** (`#111318`): page ground, the black wall behind monitors.
- **Program Paper** (`#f8fafc`): ink on dark frames and count numerals when they must read as lit glass.
- **Bezel** (`#16181f`): monitor chassis.
- **Screen** (`#07080c`): live/preview well.
- **Ink Quiet** (`#c5cdd8`): captions, rail idle, helper copy.

### Tally
- Live `#22c55e`, fault `#ef4444`, idle `#8d95a3`, warn `#f59e0b`. Program state may use Indigo instead of green.

### Named Rules
**The Tally Rule.** Green and red are lamps on a bezel. They are not brand colors and not pastel badges.

**The One Wash Rule.** Electric Indigo is the only chromatic brand field. If a screen is mostly indigo, the wash has leaked.

**The Gallery Scope Rule.** Document and extend `.gallery` tokens. Do not promote `:root` cool-paper (`#f0f4fc`) or the 240px indigo slab into this system.

## Typography

**Display Font:** Barlow Condensed for home counts; fall back to Noto Sans SC so CJK still renders.
**Body Font:** Noto Sans SC / Source Han Sans SC for tasks, nav, and forms.
**Label/Mono Font:** tabular nums on counts (`font-variant-numeric: tabular-nums`). No separate mono face.

**Character:** Gallery labels, not marketing display. Counts read like tally numerals; sentences stay quiet.

### Hierarchy
- **Display**: the three home counts (`5.25rem` / `4.25rem` under 900px).
- **Title**: monitor names (待处理订单 / 活跃连麦 / 生成中) at `1.05rem` / 600.
- **Body**: helper lines and the live-console link.
- **Label**: tally text, username, rail items (`0.9rem` rail, `0.85rem` captions).

### Named Rules
**The No-Inter-Hero Rule.** Inter is not the display face. Body may fall back to a system stack only until the Chinese workhorse is locked.

## Layout

A thin left rail (`168px`), not a 240px indigo slab. The main field is a gallery wall: important work lives in framed monitors that share one rhythm. Admin home is a three-column wall (`max-width: 1080px`, `gap: 22px`). On a narrow screen (`max-width: 900px`) the wall stacks to a single column of monitors; the rail becomes a short strip.

## Elevation & Depth

Layered frost on a dark wall. Frames sit forward with `0 18px 40px rgba(0, 0, 0, 0.45)` and a 18px backdrop blur; the wall stays flat. Glass is a coating on the bezel, not a white floating card on a pastel wash. Program frames add an Indigo ring.

### Named Rules
**The Wall-Is-Flat Rule.** The page ground does not lift. Only a monitor frame, a toast, or a pressed control casts shadow.

## Shapes

Plush: monitor corners `22px`, thick bezels, pill tally lamps (`10px` circles). Controls use `8px`; rail items `10px`. No hairline SaaS cards.

## Components

- **Monitor / monitor-panel:** signature object. Tally lamp + monitor name + body. Program / fault / idle via tally and bezel ring.
- **Primary button:** Indigo fill, `8px` radius, white label.
- **Ghost button:** no fill, quiet ink; hover to paper.
- **Rail nav:** quiet until exact-active, then a local Indigo wash.
- **Field:** stacked label + dark input (`#0c0e14`) with a faint white border.
- **Focus:** `.gallery :focus-visible` is a 2px Indigo ring, 3px offset.

## Do's and Don'ts

### Do:
- **Do** put the job inside a framed preview with a tally lamp.
- **Do** keep Electric Indigo rare and the wall dark.
- **Do** size the three counts so they work as program numbers.
- **Do** use frost and lift only on frames and pressed controls.

### Don't:
- **Don't** ship the leftover light cool-paper dashboard (`:root --bg #f0f4fc`, Inter, 240px indigo sidebar, nested glass cards) as this world.
- **Don't** scatter neon, void-scrollers, or poster noise over the task.
- **Don't** turn green/red into brand stripes.
- **Don't** invent customers, testimonials, or metrics the product does not have.
