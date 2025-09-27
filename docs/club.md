# Club/Education Cog — Detailed Documentation

This document explains what the **Club/Education** cog does, how it works, and how to use its commands in your Discord server.

**Source file (add link as needed):** [cogs/club.py](cogs/club.py)

---

## What this cog provides (high level)

- **/links** — Sends a neat embed with curated ARC @ UCF and amateur‑radio links (site, wiki, shack page, GitHub, study/testing, and operating references).  
- **/exam** — Shows quick facts for FCC exam **levels** (Technician, General, Extra), plus optional study links when you ask for them.

This cog is aimed at **education and onboarding**: helping members find resources fast and understand how to prepare for exams.

---

## Commands in detail

### 1) `/links`
**What it does:**  
Posts a single embed titled **“ARC Useful Links”** with grouped sections. Each section contains list items formatted as `` `Title` – URL `` so users can skim visually and click through.

**Sections & examples (from the code’s `LINKS` mapping):**
- **Club & Wiki**: ARC @ UCF website, ARC/CECS wiki, ARC Shack page, ARC GitHub.  
- **Study & Testing**: ARC testing info, ARC General study guide, ARRL question pools, ARRL “Getting Your Technician License.”  
- **Operating Reference**: ARC frequencies, UCF repeaters, band plans.

**Behavior:**
- Sends a **non‑ephemeral** message (visible to the channel).  
- Uses a single `discord.Embed` and adds a field for each category.

**Typical usage:**
```text
/links
```

---

### 2) `/exam`
**What it does:**  
Displays a compact **exam summary** for a chosen level and optionally appends a **Study** section with recommended links.

**Parameters:**
- `level` (string, required): accepts **tech | general | extra** (case‑insensitive).  
- `study_guide` (boolean, optional): when **true**, adds a “Study” field with helpful links tailored to the chosen level.

**What you’ll see in the embed:**
- **Title**: “Technician Exam” / “General Exam” / “Extra Exam” (based on your input).  
- **Fields**:  
  - *Element*: FCC written element number (2, 3, or 4).  
  - *Questions*: total count (35 for Tech/General; 50 for Extra).  
  - *Passing*: threshold shown as a friendly fraction (e.g., 26/35 for Tech/General, 37/50 for Extra).  
  - *Official FCC info*: a direct link to the FCC’s amateur testing/examinations page.  
- **Optional “Study” field** (when `study_guide=true`):  
  - Always includes **ARRL Question Pools** and **ARC: Amateur radio testing** page.  
  - If level is **tech**, includes **ARRL: Getting Your Technician License**.  
  - If level is **general**, includes **ARC: General study guide** (the General Element 3 page).

**Input validation:**
- If `level` is not one of the allowed values, the bot replies **ephemerally** with:  
  `Levels: tech, general, extra`

**Typical usage:**
```text
/exam level: tech
/exam level: general study_guide: true
/exam level: extra study_guide: true
```

---

## How it works under the hood

### Static data structures
- **`LINKS`**: a dictionary mapping **category names** to a list of **(Title, URL)** pairs. These are rendered into an embed by category, so it’s easy to add/remove links later by editing the mapping.  
- **`EXAMS`**: a dictionary holding per‑level metadata: FCC **element number**, **total questions**, and a human‑readable **passing threshold**.

> **Why embed fields?**  
> Using fields gives a clean, scannable layout where each category (or fact group) stays visually separated and readable on desktop and mobile.

### Embeds and responses
- The cog creates a `discord.Embed`, then uses `embed.add_field` to add content in sections.  
- For `/links` and `/exam`, the cog sends **non‑ephemeral** responses by default, so the channel can see them.  
- The `/exam` command performs a small **parameter check** before building the embed, ensuring users get quick feedback if they mistype the level.

### Setup function
- The module exposes an async `setup(bot)` that registers the cog with your bot. Keep this pattern to stay compatible with modern `discord.py` extensions loading.

---

## Extending this cog

- **Add more study links**: insert new `(Title, URL)` pairs to the `LINKS` mapping under the right category.  
- **Add new categories**: create another key in `LINKS` (e.g., “Licensing & Clubs”) and populate it with pairs.  
- **Localize or customize**: rename categories or titles to match your club’s branding, or point to your own resources.  
- **Extra exam helpers**: expand `EXAMS` with additional fields (e.g., time limits, fees, or scheduling details) and add another embed field to show them.

---

## Quick reference

- **Commands**: `/links`, `/exam`  
- **Defaults**: public (non‑ephemeral) replies  
- **Validation**: `level` must be one of **tech**, **general**, **extra**  
- **Where to change links**: edit the `LINKS` mapping  
- **Where to change exam facts**: edit the `EXAMS` mapping

---

## Example screenshots (suggested)
- `/links` output showing grouped categories  
- `/exam level: general study_guide: true` showing “Study” field

(You can paste screenshots here later.)

---

## Changelog notes (suggested)
- v1: Initial cog that provides `/links` and `/exam` with study guide toggle.
