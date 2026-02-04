# 68R Approved Source Awareness App — Implementation Plan

## Overview
Single-page web app (index.html) optimized for iPhone Safari. Camera-first workflow for Army 68R Food Inspection Specialists to document subsistence products, check listing status, and escalate to FSO.

**Decision-support tool ONLY** — never makes approval/rejection/risk decisions.

---

## File Structure
```
Approved Source App/
├── index.html          ← Main app (HTML + embedded CSS + JS modules)
├── sw.js               ← Service worker for offline support
├── manifest.json       ← PWA manifest for Add to Home Screen
├── icons/
│   └── icon-192.png    ← App icon (placeholder)
│   └── icon-512.png    ← App icon (placeholder)
└── PLAN.md             ← This file
```

Single HTML file with clearly separated `<style>` and `<script>` sections for easy deployment (open in Safari, no build tools needed).

---

## Phase 1 — Core (This Build)
1. **Camera / Photo Upload UI**
   - Full-screen camera view as landing screen
   - Large circular capture button (Plantin-style)
   - "Upload from gallery" alternative button
   - UPC text input field (manual entry)
   - iPhone viewport meta tags + safe area handling

2. **Mock Product Result Cards**
   - Card-based UI with rounded corners, light shadows
   - Shows: product photo thumbnail, UPC (if entered), timestamp
   - Status badge using ONLY allowed phrases
   - Mock lookup that returns randomized allowed statuses
   - Disclaimer footer on every card

3. **Neutral Status Messaging**
   - Only these phrases: "Listed — approval status unknown", "Pending FSO review", "Mixed outcomes observed", "No prior submissions found"
   - Persistent disclaimer: "This tool does not authorize use or rejection of products."
   - No colors that imply good/bad (no green/red for statuses)

4. **Local-Only Storage (IndexedDB)**
   - Store submissions: photo blob, UPC, timestamp, notes, status displayed, escalation status
   - Full audit trail of what the app showed
   - Offline-first: everything works without network

---

## Phase 2 — Expand (Next Build)
1. **Submission History** — scrollable list of past submissions with photos
2. **Trend Signaling** — "Mixed outcomes observed" display (no counts, no locations)
3. **Escalation Markers** — "Document and contact FSO" workflow, "Pending FSO review" tagging
4. **Notes & Documentation** — free-text notes per submission
5. **After-Action Review** — exportable audit trail showing what Soldier observed, what app displayed, that no decision was issued, when escalation occurred

---

## Data Model (IndexedDB)

### Store: `submissions`
```
{
  id: auto-increment,
  photoBlob: Blob,
  photoDataUrl: string (thumbnail),
  upc: string | null,
  productDescription: string | null,
  timestamp: ISO string,
  statusDisplayed: string (one of 4 allowed phrases),
  notes: string | null,
  escalationStatus: "none" | "pending_fso" | "fso_notified",
  escalationTimestamp: ISO string | null,
  auditLog: [
    { action: string, timestamp: ISO string, detail: string }
  ]
}
```

---

## UI Screens / Views (Single Page, view-switching)

1. **Camera View** (default/home)
   - Camera preview area
   - Capture button (large, centered, circular)
   - Upload button (small, secondary)
   - UPC manual entry toggle
   - Disclaimer bar at bottom

2. **Result Card View**
   - Product photo (large)
   - Status badge (neutral colors: gray, blue, amber)
   - UPC if available
   - Timestamp
   - "Add Notes" button
   - "Document & Contact FSO" button
   - "New Scan" button
   - Disclaimer

3. **History View** (Phase 2)
   - Card list of past submissions
   - Filter by escalation status
   - Each card shows photo thumb, status, date

---

## Visual Design Tokens
- Background: #FAFAFA (off-white)
- Cards: #FFFFFF with 0 0 8px rgba(0,0,0,0.08) shadow
- Primary accent: #3478F6 (iOS blue)
- Status badge bg: #F0F0F0 (neutral gray)
- Escalation badge: #F5A623 (amber, not red)
- Text: #1C1C1E (near-black)
- Secondary text: #8E8E93
- Border radius: 16px (cards), 50% (buttons)
- Font: -apple-system, SF Pro (system font stack)

---

## Key Implementation Details

### Camera Access
- Use `navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })`
- Fallback to file input with `accept="image/*" capture="environment"`
- Canvas-based photo capture from video stream
- Compress to JPEG for storage

### iPhone Optimization
- `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`
- `<meta name="apple-mobile-web-app-capable" content="yes">`
- Safe area insets via `env(safe-area-inset-*)`
- Touch-optimized tap targets (min 44px)
- No hover states

### Offline / Storage
- Service worker caches app shell
- IndexedDB for all submission data
- No network calls in Phase 1 (all mock/local)
- Phase 2: sync queue for when connectivity returns

---

## What We Build Now (Phase 1 Deliverable)
A working single-page app with:
- Camera capture or photo upload
- UPC manual entry
- Mock status lookup returning neutral phrases
- Result card display
- Local IndexedDB storage of every submission
- Audit trail (what was shown, when)
- Disclaimer on every view
- Offline-capable via service worker
- iPhone-optimized PWA
