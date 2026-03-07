---
paths:
  - "frontend/src/**/*.{jsx,js,css}"
---

# Frontend React / CSS Rules

## React Conventions
- Functional components only — no class components
- ES6+ syntax always
- One component per file, PascalCase filename: `VideoCard.jsx`
- Custom hooks: camelCase starting with `use`: `useApi.js`

## File Naming
```
Components:  PascalCase.jsx   → VideoCard.jsx
Pages:       PascalCase.jsx   → DailyDigest.jsx
Services:    camelCase.js     → dailyDigestApi.js
Hooks:       useCamelCase.js  → useVideoStatus.js
CSS:         SameAsComponent  → DailyDigest.css
```

## CSS Class Naming
- All pipeline pages use `vn-*` prefix classes from `ViralNews.css`
  - Shared layout: `vn-layout`, `vn-left`, `vn-right`, `vn-header`, `vn-section`
  - Shared buttons: `vn-btn-primary`, `vn-btn-secondary`, `vn-btn-generate-video`
  - Shared forms: `vn-select`, `vn-search`, `vn-tts-grid`, `vn-tts-card`
- Each page has its own CSS for page-specific styles: `BookReview.css`, `DailyDigest.css`
- **Never add page-specific styles to `ViralNews.css`**
- Import both: `import './ViralNews.css'; import './PageName.css';`

## API Services
- All API calls go through `frontend/src/services/*.js`
- Never call `fetch()` directly from components
- Always handle loading and error states in the component

## Component Structure
```jsx
// Import order: react → icons → local services → local components → styles
import { useState, useEffect } from 'react';
import { Download } from 'lucide-react';
import { fetchVideo } from '../services/videoApi';
import './ComponentName.css';

export function ComponentName({ prop1, prop2 }) {
    // 1. state declarations
    // 2. effects
    // 3. event handlers
    // 4. return JSX
}
```

## State Management
- Local UI state: `useState`
- Cross-component state: React Context (`context/ProjectContext.jsx`)
- No Redux or external state libraries
- Server state: fetch in services, store in local state

## Design System (Deep Navy — v2)

### Color Tokens — Always use CSS variables, NEVER hardcode hex values

| Token | Value | Usage |
|---|---|---|
| `--surface-page` | `#080c14` | Page backgrounds |
| `--surface-sidebar` | `#0a0f1c` | Sidebar background |
| `--surface-card` | `#0e1629` | Card/panel surfaces |
| `--surface-card-hover` | `#111e36` | Card hover state |
| `--border-card` | `#1e2a42` | Card borders (use as `border-color`) |
| `--border-card-hover` | `#2d3f5e` | Hovered card borders |
| `--border-focus` | `rgba(99,102,241,0.5)` | Input focus ring border |
| `--text-heading` | `#f0f4fc` | Page titles, card headings |
| `--text-primary` | `#e8edf7` | Main body text |
| `--text-secondary` | `#8fa4c9` | Supporting text |
| `--text-muted` | `#4a5f80` | Placeholder / timestamp text |
| `--text-label` | `#3e5a8a` | Uppercase section labels |

### Gradient Tokens — Use for all buttons and brand elements

| Token | Usage |
|---|---|
| `--gradient-indigo` | Primary CTA buttons |
| `--gradient-blue` | Action buttons (refresh, search) |
| `--gradient-orange` | Fire/viral/analyze actions |
| `--gradient-violet` | Generate video / book actions |
| `--gradient-success` | Accept / approve actions |
| `--gradient-brand` | Brand icon, sidebar active item |

### Glow Shadow Tokens — Add to buttons on `:hover`

| Token | Pair with gradient |
|---|---|
| `--shadow-glow-primary` | `--gradient-indigo` |
| `--shadow-glow-blue` | `--gradient-blue` |
| `--shadow-glow-orange` | `--gradient-orange` |
| `--shadow-glow-success` | `--gradient-success` |

### Button Pattern
```css
.my-btn {
    background: var(--gradient-indigo);
    color: white;
    box-shadow: 0 2px 10px rgba(99,102,241,0.2);
    transition: all 0.2s;
}
.my-btn:hover:not(:disabled) {
    box-shadow: var(--shadow-glow-primary);
    transform: translateY(-1px);
}
.my-btn:disabled { opacity: 0.45; cursor: not-allowed; }
```

### Card Pattern
```css
.my-card {
    background: var(--surface-card);
    border: 1px solid var(--border-card);
    border-radius: 12px;
    transition: border-color 0.15s, box-shadow 0.15s, transform 0.15s;
}
.my-card:hover {
    border-color: var(--border-card-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
```

### Input Pattern
```css
.my-input {
    background: var(--surface-card);
    border: 1px solid var(--border-card);
    color: var(--text-primary);
    border-radius: 8px;
}
.my-input:focus {
    border-color: var(--border-focus);
    box-shadow: 0 0 0 3px var(--color-primary-ring);
    outline: none;
}
.my-input::placeholder { color: var(--text-muted); }
```

### Section Label Pattern
```css
.section-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-label);
}
```

### Critical Rules
- ❌ **NEVER** hardcode hex colors in component CSS — always use `var(--token-name)`
- ❌ **NEVER** use white or light grey backgrounds (`#fff`, `#f9fafb`, `rgba(255,255,255,0.7)`)
- ✅ Use `var(--surface-page)` for the darkest layer, `var(--surface-card)` for panels
- ✅ All buttons that trigger AI/generation actions MUST use a gradient + glow pattern
- ✅ Section label text MUST use `var(--text-label)` with `text-transform: uppercase`
