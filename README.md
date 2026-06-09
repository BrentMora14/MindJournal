# 🌿 MindJournal

AI-powered journaling app that detects cognitive distortions using **Google Gemini 2.5 Flash**, with automatic dual-key fallback when quota is exhausted.

---

## Setup

```bash
pip install -r requirements.txt
streamlit run mindjournal.py
```

Get a free Gemini API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

## API Key Fallback

Enter two keys in the sidebar. If the **Primary** key hits its rate/quota limit (HTTP 429), the app instantly retries with the **Secondary** key — no interruption. Each key shows a live status badge: `IDLE` → `ACTIVE` → `EXHAUSTED` / `FALLBACK`.

You can also set keys via environment variables:

```bash
export GEMINI_API_KEY="AIza..."
export GEMINI_API_KEY_2="AIza..."
streamlit run mindjournal.py
```

## Features

- **14 cognitive distortions** detected per entry
- **Compassionate reframes** for each distortion found
- **Mood tracking** across entries
- **Insights dashboard** with frequency charts and mood history
- **Key usage breakdown** showing how often each key was used
- **Reference guide** explaining all 14 distortions

## Distortions Detected

Catastrophizing · All-or-Nothing Thinking · Mind Reading · Fortune Telling ·
Overgeneralization · Personalization · Mental Filter · Should Statements ·
Emotional Reasoning · Magnification/Minimization · Labeling ·
Jumping to Conclusions · Disqualifying the Positive · Rumination

---

> 💙 For personal reflection only. Not a substitute for professional mental health care.
