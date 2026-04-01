# KMSBot UI/UX Style Guide & Constraints

> **MANDATORY**: All UI/UX changes to this project — color, font, spacing, layout, or visual style — MUST follow this guide.  
> Any agent or developer making frontend changes should read this file first.

---

## 1. Token System

All visual values live in **`frontend/src/theme.css`** (single source of truth).  
`frontend/src/index.css` imports it via `@import './theme.css'` and contains only structure/layout CSS.

### Rule: No bare values in component CSS
- ✅ `color: var(--text-1)`  
- ✅ `background: var(--accent-muted)`  
- ❌ `color: #1A2333`  
- ❌ `font-size: 14px`  
- ❌ `border-radius: 6px`  

Exceptions (acceptable bare values): `font-size: 13px` on `.related-docs__item`, `gap: 6px` on `.source-list__items`, `margin: 6px 0 0` in debug panels — these are mid-scale values with no direct token mapping.

---

## 2. Active Skin: "Manulife Light"

### Color Palette

| Token | Value | Usage |
|---|---|---|
| `--bg-base` | `#F4F7FA` | Page background |
| `--bg-surface` | `#FFFFFF` | Cards, sidebar, inputs |
| `--bg-elevated` | `#EEF2F6` | Hover backgrounds |
| `--bg-hover` | `#E8F4EE` | Nav hover state |
| `--bg-active` | `#D6EFE2` | Active state |
| `--border-subtle` | `#EBF0F5` | Dividers |
| `--border-default` | `#D8E2EC` | Card borders |
| `--border-strong` | `#B8CADA` | Focused borders |
| `--accent` | `#00A758` | Manulife Green — buttons, active states |
| `--accent-hover` | `#008F4B` | Button hover |
| `--accent-muted` | `rgba(0,167,88,0.10)` | Chip/tag backgrounds |
| `--color-link` | `#00592D` | Links |
| `--color-success` | `#00A758` | Success status |
| `--color-danger` | `#C62828` | Error/danger |
| `--color-warning` | `#F57C00` | Warning |
| `--color-info` | `#0277BD` | Info |
| `--text-1` | `#1A2333` | Primary text |
| `--text-2` | `#5C6B7A` | Secondary text |
| `--text-3` | `#9AAAB8` | Muted/disabled text |

### Typography

| Token | Value |
|---|---|
| `--font-display` | "Nunito Sans" — headings, titles |
| `--font-body` | "Nunito Sans" — body text, UI labels |
| `--font-mono` | "JetBrains Mono" — code, status badges, version |

Font is loaded in `frontend/index.html` via Google Fonts. To change fonts, update **both** the `<link>` tag in `index.html` AND the `--font-*` tokens in `theme.css`.

### Type Scale

`--text-xs` (11px) → `--text-sm` (12px) → `--text-base` (14px) → `--text-md` (16px) → `--text-lg` (18px) → `--text-xl` (22px) → `--text-2xl` (28px)

### Spacing

4px grid: `--space-1` (4px) through `--space-12` (48px).

---

## 3. Switching Skins

1. Duplicate `theme.css` → e.g. `theme.dark.css`
2. Modify the `:root` values in the new file
3. In `index.css`, change `@import './theme.css'` → `@import './theme.dark.css'`

For runtime skin switching (future), load the theme file dynamically via JS or use a `[data-theme]` attribute on `<html>` with separate `:root[data-theme="dark"]` blocks.

---

## 4. Component Conventions

### File locations
- Global tokens: `frontend/src/theme.css`
- Global structure + base styles: `frontend/src/index.css`
- Feature CSS: co-located with component (`features/chat/ChatPage.css`)

### Naming: BEM
```
.block {}
.block__element {}
.block--modifier {}
.block__element--modifier {}
```
Examples: `.admin-card__title`, `.sidebar__link--active`, `.status-badge--running`

### Layout
- Sidebar width: `var(--sidebar-width)` (260px)  
- Logo: height `var(--logo-height)` (24px), border-radius `var(--logo-border-radius)` (7px)
- Gear button: `var(--gear-btn-size)` (32px)  
- Admin progress bar: `var(--progress-height)` (3px)

---

## 5. Chat Header Background

The chat header uses `header-bg.webp` (stored in `frontend/public/`).  
A `::before` overlay (`var(--header-bg-overlay)`, default `rgba(255,255,255,0.82)`) ensures text readability.  
Adjust `--header-bg-overlay` in `theme.css` to control image visibility.

---

## 6. Status Color Mapping

| Status | CSS class | Color token |
|---|---|---|
| ok / success | `status-badge--ok` | `--color-success` |
| running | `status-badge--running` | `--accent` (green, pulsing) |
| degraded | `status-badge--degraded` | `--color-warning` |
| error | `status-badge--error` | `--color-danger` |
| idle | `status-badge--idle` | `--text-2` |
