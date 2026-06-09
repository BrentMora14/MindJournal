#!/usr/bin/env python3
"""
MindJournal – AI-Powered Cognitive Distortion Journal
Powered by Google Gemini 2.5 Flash with dual-key fallback.

Run with: streamlit run mindjournal.py
"""

import json
import os
from collections import Counter
from datetime import datetime

import streamlit as st
from google import genai
from google.genai import errors, types

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="MindJournal",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Lora:ital@0;1&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }

.main-title {
    font-family: 'Lora', serif;
    font-size: 2.4rem;
    font-weight: 400;
    color: #2d3748;
    line-height: 1.2;
    margin-bottom: 0;
}
.subtitle {
    color: #718096;
    font-size: 0.97rem;
    margin-top: 4px;
    margin-bottom: 24px;
    font-weight: 300;
    letter-spacing: 0.02em;
}
.distortion-card {
    background: #fff;
    border-radius: 14px;
    padding: 18px 20px;
    margin: 10px 0;
    border-left: 5px solid;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
}
.distortion-type {
    font-weight: 600;
    font-size: 0.92rem;
    margin-bottom: 8px;
    letter-spacing: 0.01em;
}
.distortion-quote {
    font-family: 'Lora', serif;
    font-style: italic;
    color: #4a5568;
    font-size: 0.88rem;
    border-left: 2px solid #e2e8f0;
    padding-left: 10px;
    margin: 8px 0 12px 0;
    line-height: 1.6;
}
.section-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: #a0aec0;
    margin-bottom: 4px;
}
.explanation-text {
    color: #4a5568;
    font-size: 0.87rem;
    margin-bottom: 10px;
    line-height: 1.65;
}
.reframe-box {
    background: #f0fff4;
    border-radius: 8px;
    padding: 11px 14px;
    margin-top: 4px;
    color: #276749;
    font-size: 0.87rem;
    line-height: 1.65;
}
.encouragement-box {
    background: linear-gradient(135deg, #ebf8ff 0%, #e9d8fd 100%);
    border-radius: 12px;
    padding: 18px 20px;
    margin: 14px 0;
    color: #2d3748;
    font-size: 0.93rem;
    line-height: 1.7;
}
.healthy-tag {
    display: inline-block;
    background: #c6f6d5;
    color: #22543d;
    border-radius: 20px;
    padding: 4px 13px;
    font-size: 0.79rem;
    margin: 3px 3px 3px 0;
    font-weight: 500;
}
.mood-badge {
    display: inline-block;
    border-radius: 20px;
    padding: 5px 15px;
    font-size: 0.83rem;
    font-weight: 600;
}
.stat-card {
    background: white;
    border-radius: 12px;
    padding: 20px 16px;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    margin-bottom: 8px;
}
.stat-number {
    font-size: 2.2rem;
    font-weight: 600;
    color: #4a5568;
    line-height: 1;
}
.stat-label {
    color: #a0aec0;
    font-size: 0.78rem;
    margin-top: 6px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.empty-state {
    background: #f7fafc;
    border-radius: 14px;
    padding: 40px 32px;
    text-align: center;
    color: #a0aec0;
}
.key-status {
    display: inline-block;
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-left: 6px;
}
.key-active    { background:#c6f6d5; color:#276749; }
.key-fallback  { background:#fefcbf; color:#975a16; }
.key-exhausted { background:#fed7d7; color:#c53030; }
.key-idle      { background:#e2e8f0; color:#4a5568; }
.disclaimer {
    font-size: 0.75rem;
    color: #a0aec0;
    line-height: 1.6;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────

GEMINI_MODEL = "gemini-2.5-flash"

DISTORTION_COLORS: dict[str, str] = {
    "Catastrophizing":              "#e53e3e",
    "All-or-Nothing Thinking":      "#dd6b20",
    "Mind Reading":                 "#805ad5",
    "Fortune Telling":              "#6b46c1",
    "Overgeneralization":           "#d69e2e",
    "Personalization":              "#c53030",
    "Mental Filter":                "#3182ce",
    "Should Statements":            "#2c7a7b",
    "Emotional Reasoning":          "#b83280",
    "Magnification / Minimization": "#718096",
    "Labeling":                     "#276749",
    "Jumping to Conclusions":       "#c05621",
    "Disqualifying the Positive":   "#4a5568",
    "Rumination":                   "#7b341e",
}

DISTORTION_DESCRIPTIONS: dict[str, str] = {
    "Catastrophizing":              "Expecting the worst possible outcome",
    "All-or-Nothing Thinking":      "Seeing only extremes — no middle ground",
    "Mind Reading":                 "Assuming you know others' negative thoughts",
    "Fortune Telling":              "Predicting a negative future as certain fact",
    "Overgeneralization":           "Broad conclusions from a single event",
    "Personalization":              "Taking excessive blame for external events",
    "Mental Filter":                "Focusing only on negatives, filtering out positives",
    "Should Statements":            "Rigid 'must/should/ought to' rules",
    "Emotional Reasoning":          "Treating feelings as objective facts",
    "Magnification / Minimization": "Inflating negatives, shrinking positives",
    "Labeling":                     "Harsh global labels instead of specific behavior",
    "Jumping to Conclusions":       "Negative conclusions without supporting evidence",
    "Disqualifying the Positive":   "Dismissing positive experiences as 'not counting'",
    "Rumination":                   "Dwelling on distress without moving forward",
}

MOOD_STYLES: dict[str, dict] = {
    "anxious":     {"bg": "#fed7d7", "fg": "#c53030", "emoji": "😰"},
    "depressed":   {"bg": "#bee3f8", "fg": "#2b6cb0", "emoji": "😔"},
    "angry":       {"bg": "#feebc8", "fg": "#c05621", "emoji": "😠"},
    "overwhelmed": {"bg": "#e9d8fd", "fg": "#6b46c1", "emoji": "😵"},
    "neutral":     {"bg": "#e2e8f0", "fg": "#4a5568", "emoji": "😐"},
    "mixed":       {"bg": "#fefcbf", "fg": "#975a16", "emoji": "🤔"},
    "hopeful":     {"bg": "#c6f6d5", "fg": "#276749", "emoji": "🌱"},
    "calm":        {"bg": "#e0f2fe", "fg": "#075985", "emoji": "😌"},
    "sad":         {"bg": "#dbeafe", "fg": "#1e40af", "emoji": "😢"},
}

SYSTEM_PROMPT = """You are a compassionate cognitive-behavioral therapist assistant. Analyze journal entries for cognitive distortions — unhealthy thought patterns linked to anxiety, depression, and other mental health challenges.

For each distortion found, provide:
1. The exact distortion type (from the list below — use the exact name)
2. A direct verbatim quote from the journal entry
3. A warm, empathetic 2–3 sentence explanation
4. A compassionate, grounded 2–3 sentence reframing suggestion

Return ONLY a valid JSON object with this exact structure:
{
  "overall_mood": "one of: anxious, depressed, angry, overwhelmed, neutral, mixed, hopeful, calm, sad",
  "distortions": [
    {
      "type": "exact distortion name from the list",
      "quote": "exact verbatim phrase from the journal entry",
      "explanation": "empathetic 2–3 sentence explanation",
      "reframe": "compassionate 2–3 sentence reframing suggestion"
    }
  ],
  "healthy_patterns": ["any positive or balanced thinking patterns observed — be specific"],
  "summary": "Warm 2–3 sentence overview of the emotional themes",
  "encouragement": "Personal, specific 1–2 sentence supportive message"
}

Cognitive distortions to identify (use these exact names):
- Catastrophizing: assuming the worst possible outcome will happen
- All-or-Nothing Thinking: seeing things in black and white with no middle ground
- Mind Reading: assuming you know what others think, usually negatively
- Fortune Telling: predicting a negative future as if it were certain fact
- Overgeneralization: drawing sweeping conclusions from a single event
- Personalization: taking excessive personal responsibility for external events
- Mental Filter: focusing exclusively on negatives while filtering out positives
- Should Statements: rigid internal rules using "should," "must," "ought to"
- Emotional Reasoning: concluding that because you feel something, it must be true
- Magnification / Minimization: exaggerating negatives or shrinking positives
- Labeling: applying harsh, global labels to yourself or others instead of describing behavior
- Jumping to Conclusions: drawing negative conclusions without sufficient evidence
- Disqualifying the Positive: dismissing positive experiences as exceptions that "don't count"
- Rumination: repetitively focusing on distress without working toward resolution

Guidelines:
- Be compassionate, non-judgmental, and clinically accurate
- Only flag distortions clearly supported by the text
- If none exist, return an empty distortions array
- Healthy patterns and encouragement must be specific to this entry, not generic"""

# ── Session state ─────────────────────────────────────────────────────────────

DEFAULTS = {
    "entries":              [],
    "current_analysis":     None,
    "current_entry_text":   "",
    # "idle" | "active" | "fallback" | "exhausted"
    "key1_status":          "idle",
    "key2_status":          "idle",
    "last_key_used":        None,   # "Primary" | "Secondary"
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Gemini helpers ────────────────────────────────────────────────────────────

def _is_quota_error(exc: Exception) -> bool:
    """Return True if the error is a quota / rate-limit exhaustion (HTTP 429)."""
    if isinstance(exc, errors.ClientError):
        # code == 429  OR  status contains RESOURCE_EXHAUSTED
        if exc.code == 429:
            return True
        if exc.status and "RESOURCE_EXHAUSTED" in str(exc.status).upper():
            return True
    # Fallback: inspect the string representation
    msg = str(exc).upper()
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg or "QUOTA" in msg


def _call_gemini(entry_text: str, api_key: str) -> dict:
    """Single Gemini call. Raises on any error."""
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=entry_text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.3,
        ),
    )
    raw = response.text.strip()
    # Strip stray markdown fences just in case
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def analyze_entry(entry_text: str, key1: str, key2: str) -> tuple[dict, str]:
    """
    Try key1 first.  On quota exhaustion (HTTP 429 / RESOURCE_EXHAUSTED),
    transparently fall back to key2.  Returns (analysis, label_of_key_used).
    Raises the last meaningful error if both keys fail.
    """
    candidates = [
        (k.strip(), lbl)
        for k, lbl in [(key1, "Primary"), (key2, "Secondary")]
        if k.strip()
    ]
    if not candidates:
        raise ValueError("Please enter at least one Gemini API key.")

    # Reset statuses to idle before a fresh run
    st.session_state.key1_status = "idle" if key1.strip() else "idle"
    st.session_state.key2_status = "idle" if key2.strip() else "idle"

    last_exc: Exception | None = None
    for idx, (key, label) in enumerate(candidates):
        status_var = "key1_status" if idx == 0 else "key2_status"
        st.session_state[status_var] = "active"
        try:
            result = _call_gemini(entry_text, key)
            st.session_state.last_key_used = label
            return result, label
        except errors.ClientError as exc:
            if _is_quota_error(exc):
                st.session_state[status_var] = "exhausted"
                last_exc = exc
                # Try next key
                if idx + 1 < len(candidates):
                    next_var = "key2_status"
                    st.session_state[next_var] = "fallback"
                continue   # ← fall through to next candidate
            # Non-quota client error (bad key, invalid request, etc.) — raise immediately
            st.session_state[status_var] = "idle"
            raise
        except Exception:
            st.session_state[status_var] = "idle"
            raise

    # Both keys exhausted
    raise errors.ClientError(
        429,
        {"error": {"message": "Both API keys have hit their quota limits. Please try again later.",
                   "status": "RESOURCE_EXHAUSTED"}},
    ) from last_exc

# ── Rendering helpers ─────────────────────────────────────────────────────────

def _key_status_badge(status: str) -> str:
    labels = {
        "idle":      ("IDLE",      "key-idle"),
        "active":    ("ACTIVE",    "key-active"),
        "fallback":  ("FALLBACK",  "key-fallback"),
        "exhausted": ("EXHAUSTED", "key-exhausted"),
    }
    text, cls = labels.get(status, ("IDLE", "key-idle"))
    return f"<span class='key-status {cls}'>{text}</span>"


def render_distortion_card(d: dict) -> None:
    color = DISTORTION_COLORS.get(d["type"], "#718096")
    st.markdown(f"""
    <div class="distortion-card" style="border-left-color:{color};">
        <div class="distortion-type" style="color:{color};">⚠&nbsp; {d['type']}</div>
        <div class="distortion-quote">"{d['quote']}"</div>
        <div class="section-label">What's happening</div>
        <div class="explanation-text">{d['explanation']}</div>
        <div class="section-label">💡 A healthier perspective</div>
        <div class="reframe-box">{d['reframe']}</div>
    </div>
    """, unsafe_allow_html=True)


def render_mood_badge(mood: str) -> str:
    s = MOOD_STYLES.get(mood, MOOD_STYLES["neutral"])
    return (
        f"<span class='mood-badge' style='background:{s['bg']};color:{s['fg']};'>"
        f"{s['emoji']}&nbsp; {mood.title()}</span>"
    )


def render_analysis_panel(analysis: dict) -> None:
    mood = analysis.get("overall_mood", "neutral")
    st.markdown(render_mood_badge(mood), unsafe_allow_html=True)
    st.markdown("")

    if summary := analysis.get("summary", ""):
        st.markdown(
            f"<div style='color:#4a5568;font-size:0.93rem;line-height:1.75;"
            f"margin-bottom:4px;'>{summary}</div>", unsafe_allow_html=True)

    if enc := analysis.get("encouragement", ""):
        st.markdown(
            f"<div class='encouragement-box'>💙&nbsp; {enc}</div>",
            unsafe_allow_html=True)

    patterns = analysis.get("healthy_patterns", [])
    if patterns:
        st.markdown("**✨ Healthy patterns noticed:**")
        tags = "".join(f"<span class='healthy-tag'>{p}</span>" for p in patterns)
        st.markdown(f"<div style='margin-bottom:12px;'>{tags}</div>",
                    unsafe_allow_html=True)

    distortions = analysis.get("distortions", [])
    st.markdown("---")
    if distortions:
        plural = "s" if len(distortions) != 1 else ""
        st.markdown(f"**⚠ {len(distortions)} cognitive distortion{plural} detected:**")
        for d in distortions:
            render_distortion_card(d)
    else:
        st.success(
            "✅ No cognitive distortions detected. Your thinking here appears "
            "balanced and grounded — that's worth noticing.")

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🌿 MindJournal")
    st.caption("Powered by Gemini 2.5 Flash")
    st.markdown("---")

    # ── API Keys ──
    st.markdown("### 🔑 API Keys")
    st.caption(
        "Enter one or both keys. If the primary key hits its quota, "
        "the app automatically retries with the secondary key."
    )

    key1_raw = st.text_input(
        "Primary Key",
        type="password",
        placeholder="AIza...",
        value=os.environ.get("GEMINI_API_KEY", ""),
        help="Your first Google AI Studio API key.",
    )
    k1_status_html = _key_status_badge(st.session_state.key1_status)
    st.markdown(
        f"<div style='font-size:0.8rem;color:#718096;margin-top:-8px;margin-bottom:8px;'>"
        f"Primary {k1_status_html}</div>",
        unsafe_allow_html=True,
    )

    key2_raw = st.text_input(
        "Secondary Key (fallback)",
        type="password",
        placeholder="AIza...",
        value=os.environ.get("GEMINI_API_KEY_2", ""),
        help="Used automatically if the primary key is quota-exhausted.",
    )
    k2_status_html = _key_status_badge(st.session_state.key2_status)
    st.markdown(
        f"<div style='font-size:0.8rem;color:#718096;margin-top:-8px;margin-bottom:8px;'>"
        f"Secondary {k2_status_html}</div>",
        unsafe_allow_html=True,
    )

    if st.session_state.last_key_used:
        used = st.session_state.last_key_used
        icon = "🟢" if used == "Primary" else "🟡"
        st.caption(f"{icon} Last request used **{used}** key")

    st.markdown("---")

    # ── Session stats ──
    entries = st.session_state.entries
    if entries:
        all_d = [d for e in entries for d in e["analysis"].get("distortions", [])]
        st.markdown("### 📊 Session Stats")
        col_a, col_b = st.columns(2)
        col_a.metric("Entries", len(entries))
        col_b.metric("Distortions", len(all_d))

        if all_d:
            top = Counter(d["type"] for d in all_d).most_common(3)
            st.markdown("**Most frequent:**")
            for name, count in top:
                c = DISTORTION_COLORS.get(name, "#718096")
                st.markdown(
                    f"<span style='color:{c};font-weight:600;font-size:0.81rem;'>■ {name}</span> "
                    f"<span style='color:#a0aec0;font-size:0.79rem;'>({count}×)</span>",
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        st.markdown("### 📖 History")
        for i, entry in enumerate(reversed(entries)):
            idx = len(entries) - 1 - i
            s    = MOOD_STYLES.get(entry["analysis"].get("overall_mood", "neutral"),
                                   MOOD_STYLES["neutral"])
            n_d  = len(entry["analysis"].get("distortions", []))
            lbl  = f"{s['emoji']} {entry['timestamp']}  ·  {n_d} found"
            if st.button(lbl, key=f"hist_{idx}", use_container_width=True):
                st.session_state.current_analysis     = entry["analysis"]
                st.session_state.current_entry_text   = entry["text"]
                st.rerun()

    st.markdown("---")
    st.markdown(
        "<div class='disclaimer'>"
        "💙 MindJournal is for personal reflection and psychoeducation. "
        "It does not replace professional mental health care. "
        "If you're struggling, please reach out to a qualified therapist or crisis line."
        "</div>",
        unsafe_allow_html=True,
    )

# ── Main content ──────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">🌿 MindJournal</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Write freely · Understand your thought patterns · Grow with compassion</div>',
    unsafe_allow_html=True,
)

if not key1_raw.strip() and not key2_raw.strip():
    st.info(
        "👈 Add at least one Gemini API key in the sidebar to get started. "
        "Get a free key at [aistudio.google.com](https://aistudio.google.com/apikey).",
        icon="🔑",
    )
    st.stop()

tab_journal, tab_insights, tab_guide = st.tabs(
    ["✍️ Journal", "📊 Insights", "📚 Reference Guide"]
)

# ── Tab: Journal ──────────────────────────────────────────────────────────────

with tab_journal:
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("### What's on your mind?")
        entry_text = st.text_area(
            label="",
            placeholder=(
                "Write about your day, thoughts, feelings, or worries…\n\n"
                "This is a private space — write as freely as you like.\n\n"
                "Example: 'I made a mistake at work today and I just know everyone "
                "thinks I'm incompetent. This always happens to me. I'll probably get "
                "fired — I can just feel it…'"
            ),
            height=340,
            value=st.session_state.current_entry_text,
            key="journal_input",
        )

        c1, c2 = st.columns([3, 1])
        with c1:
            analyze_btn = st.button(
                "🔍 Analyze for Cognitive Distortions",
                type="primary",
                use_container_width=True,
            )
        with c2:
            clear_btn = st.button("🗑 Clear", use_container_width=True)

        if clear_btn:
            st.session_state.current_analysis   = None
            st.session_state.current_entry_text = ""
            st.rerun()

        if analyze_btn:
            text = entry_text.strip()
            if not text:
                st.warning("Please write something in your journal first.")
            elif len(text) < 20:
                st.warning("Please write a bit more — at least a sentence or two.")
            else:
                with st.spinner("🧠 Reading your entry with care…"):
                    try:
                        analysis, key_used = analyze_entry(text, key1_raw, key2_raw)
                        st.session_state.current_analysis   = analysis
                        st.session_state.current_entry_text = text
                        st.session_state.entries.append({
                            "timestamp": datetime.now().strftime("%b %d, %H:%M"),
                            "text":      text,
                            "analysis":  analysis,
                            "key_used":  key_used,
                        })
                        if key_used == "Secondary":
                            st.toast(
                                "⚡ Primary key was quota-exhausted — used Secondary key.",
                                icon="🔄",
                            )
                        st.rerun()
                    except errors.ClientError as exc:
                        if _is_quota_error(exc):
                            st.error(
                                "🚫 Both API keys have hit their quota limits. "
                                "Please wait a moment or add a new key in the sidebar."
                            )
                        elif exc.code == 400:
                            st.error("Invalid API key. Please check your key(s) in the sidebar.")
                        else:
                            st.error(f"Gemini API error ({exc.code}): {exc.message}")
                    except json.JSONDecodeError:
                        st.error("The model returned an unexpected response. Please try again.")
                    except ValueError as exc:
                        st.warning(str(exc))
                    except Exception as exc:
                        st.error(f"Unexpected error: {exc}")

        if entry_text.strip():
            words = len(entry_text.split())
            st.caption(f"{words} word{'s' if words != 1 else ''}")

    with right:
        st.markdown("### Analysis")
        analysis = st.session_state.current_analysis
        if analysis:
            render_analysis_panel(analysis)
        else:
            st.markdown("""
            <div class="empty-state">
                <div style='font-size:2.8rem;margin-bottom:14px;'>🌱</div>
                <div style='font-size:0.98rem;font-weight:500;color:#718096;margin-bottom:6px;'>
                    Your analysis will appear here
                </div>
                <div style='font-size:0.85rem;color:#a0aec0;'>
                    Write a journal entry and click Analyze
                </div>
            </div>
            """, unsafe_allow_html=True)

# ── Tab: Insights ─────────────────────────────────────────────────────────────

with tab_insights:
    entries = st.session_state.entries
    if not entries:
        st.markdown("""
        <div class="empty-state">
            <div style='font-size:2.8rem;margin-bottom:14px;'>📊</div>
            <div style='font-size:0.98rem;font-weight:500;color:#718096;margin-bottom:6px;'>
                No data yet
            </div>
            <div style='font-size:0.85rem;color:#a0aec0;'>
                Insights appear after your first analyzed entry
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        all_d = [d for e in entries for d in e["analysis"].get("distortions", [])]
        entries_with_d = sum(1 for e in entries if e["analysis"].get("distortions"))

        # ── Stat cards ──
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""<div class="stat-card">
                <div class="stat-number">{len(entries)}</div>
                <div class="stat-label">Total Entries</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="stat-card">
                <div class="stat-number">{len(all_d)}</div>
                <div class="stat-label">Distortions Found</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            avg = round(len(all_d) / len(entries), 1)
            st.markdown(f"""<div class="stat-card">
                <div class="stat-number">{avg}</div>
                <div class="stat-label">Avg per Entry</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            clean_pct = round((len(entries) - entries_with_d) / len(entries) * 100)
            st.markdown(f"""<div class="stat-card">
                <div class="stat-number">{clean_pct}%</div>
                <div class="stat-label">Distortion-Free</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")
        ins_l, ins_r = st.columns([3, 2], gap="large")

        with ins_l:
            st.markdown("### Most Common Thought Patterns")
            if all_d:
                counts = Counter(d["type"] for d in all_d).most_common()
                max_val = counts[0][1]
                for name, count in counts:
                    color = DISTORTION_COLORS.get(name, "#718096")
                    pct   = int(count / max_val * 100)
                    st.markdown(f"""
                    <div style='margin:10px 0;'>
                        <div style='display:flex;align-items:center;
                                    justify-content:space-between;margin-bottom:5px;'>
                            <span style='color:{color};font-weight:600;
                                         font-size:0.85rem;'>{name}</span>
                            <span style='color:#a0aec0;font-size:0.82rem;
                                         font-weight:500;'>{count}×</span>
                        </div>
                        <div style='background:#edf2f7;border-radius:6px;height:9px;overflow:hidden;'>
                            <div style='background:{color};width:{pct}%;height:100%;
                                        border-radius:6px;'></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ No distortions recorded yet. Keep journaling!")

        with ins_r:
            st.markdown("### Mood History")
            for entry in reversed(entries[-10:]):
                mood  = entry["analysis"].get("overall_mood", "neutral")
                s     = MOOD_STYLES.get(mood, MOOD_STYLES["neutral"])
                n_d   = len(entry["analysis"].get("distortions", []))
                k_lbl = entry.get("key_used", "")
                key_tag = (
                    f" · <span style='color:#a0aec0;font-size:0.72rem;'>{k_lbl} key</span>"
                    if k_lbl else ""
                )
                st.markdown(f"""
                <div style='display:flex;align-items:center;padding:8px 12px;
                            background:{s["bg"]}22;border-radius:10px;
                            margin:5px 0;border:1px solid {s["bg"]};'>
                    <span style='font-size:1.3rem;margin-right:10px;'>{s['emoji']}</span>
                    <div>
                        <div style='font-size:0.85rem;font-weight:600;color:{s["fg"]};'>
                            {mood.title()}
                        </div>
                        <div style='font-size:0.75rem;color:#a0aec0;'>
                            {entry['timestamp']} · {n_d} distortion{'s' if n_d!=1 else ''}{key_tag}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ── Key usage breakdown ──
        key_usage = Counter(e.get("key_used", "Unknown") for e in entries)
        if len(key_usage) > 1:
            st.markdown("---")
            st.markdown("### Key Usage Breakdown")
            ku_cols = st.columns(len(key_usage))
            for col, (k_lbl, k_count) in zip(ku_cols, key_usage.items()):
                icon = "🟢" if k_lbl == "Primary" else "🟡"
                col.metric(f"{icon} {k_lbl}", f"{k_count} req")

# ── Tab: Reference Guide ──────────────────────────────────────────────────────

with tab_guide:
    st.markdown("### 📚 Cognitive Distortions Reference")
    st.markdown(
        "These are the 14 thought patterns MindJournal watches for. "
        "Recognizing them is the first step toward changing them."
    )
    st.markdown("")

    items = list(DISTORTION_COLORS.items())
    for i in range(0, len(items), 2):
        cols = st.columns(2, gap="medium")
        for j, col in enumerate(cols):
            if i + j < len(items):
                name, color = items[i + j]
                desc = DISTORTION_DESCRIPTIONS.get(name, "")
                with col:
                    st.markdown(f"""
                    <div style='background:white;border-radius:12px;padding:16px 18px;
                                border-left:4px solid {color};
                                box-shadow:0 2px 8px rgba(0,0,0,0.06);
                                margin-bottom:12px;min-height:90px;'>
                        <div style='font-weight:600;color:{color};
                                    font-size:0.9rem;margin-bottom:5px;'>{name}</div>
                        <div style='color:#718096;font-size:0.84rem;
                                    line-height:1.55;'>{desc}</div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🧠 About Cognitive Behavioral Therapy (CBT)")
    st.markdown("""
Cognitive distortions are systematic patterns of inaccurate thinking that can contribute to
anxiety, depression, and other mental health challenges. The concept was developed by psychiatrist
**Aaron Beck** and later expanded by **David Burns** in *Feeling Good* (1980).

**The core idea:** Our thoughts, feelings, and behaviors are interconnected. By identifying and
challenging distorted thoughts, we can shift our emotional experience and responses.

**How to use this journal:**
1. Write freely about whatever is on your mind
2. Let the AI identify any distorted thought patterns
3. Read the reframing suggestions with an open mind
4. Over time, notice which distortions appear most often — that's where to focus your growth

> 💙 *This tool is for psychoeducation and self-reflection. For persistent struggles with anxiety,
> depression, or other challenges, please work with a qualified mental health professional.*
    """)
