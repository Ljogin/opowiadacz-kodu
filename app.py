import os
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ──────────────────────────────────────────────────────────────────────────────
# Konfiguracja strony
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Code Narrator 🎙️", page_icon="🧠", layout="centered")
st.title("🧠🎙️ Code Narrator — opowiadam, co robi Twój kod")

st.caption(
    "Wklej kod źródłowy, wybierz poziom opisu, a ja wygeneruję opis tekstowy — "
    "i (opcjonalnie) wersję audio w formie mini-podcastu."
)

# ──────────────────────────────────────────────────────────────────────────────
# Klucz API — najpierw Streamlit Secrets, potem .env, potem zmienne środowiska
# ──────────────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = None
try:
    if "OPENAI_API_KEY" in st.secrets:
        OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except Exception:
    pass

if not OPENAI_API_KEY:
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.error(
        "Brak `OPENAI_API_KEY`. Dodaj klucz w **Streamlit Secrets** "
        "lub lokalnie w pliku `.env`."
    )
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# ──────────────────────────────────────────────────────────────────────────────
# UI — wejścia użytkownika
# ──────────────────────────────────────────────────────────────────────────────
with st.form("code_form", clear_on_submit=False):
    code = st.text_area(
        "💾 Kod źródłowy",
        height=260,
        placeholder="Wklej tutaj kod (Python, JS, Java, C#, itp.)",
    )

    detail = st.radio(
        "🎯 Poziom szczegółowości",
        options=["Ogólny", "Szczegółowy"],
        horizontal=True,
        index=0,
    )

    make_audio = st.checkbox("🔊 Wygeneruj też wersję audio (mp3)")

    voice = st.selectbox(
        "🎤 Głos (dla wersji audio)",
        options=["alloy", "verse", "amber", "aria"],
        index=0,
        help="Działa z modelem TTS `tts-1`.",
        disabled=not make_audio,
    )

    submitted = st.form_submit_button("✨ Opisz ten kod", type="primary")

# ──────────────────────────────────────────────────────────────────────────────
# Prompty pomocnicze
# ──────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "Jesteś asystentem, który klarownie objaśnia kod dla uczniów szkoły średniej."
    " Używaj prostego języka, lecz zachowuj fachową terminologię, kiedy to pomaga."
)

def build_user_prompt(code_text: str, level: str) -> str:
    header = (
        "Zadanie: wytłumacz, co robi poniższy kod.\n"
        "Jeśli pojawią się potencjalne błędy/logika brzegowa, wspomnij o tym krótko na końcu.\n\n"
    )
    if level == "Ogólny":
        spec = (
            "📌 **Tryb OGÓLNY**: opisz w 2–5 zdaniach, jaki jest cel i ogólne działanie programu."
            " Nie cytuj kodu; streszczaj. Dodaj ewentualne zastosowania/przykład użycia.\n\n"
        )
    else:
        spec = (
            "📌 **Tryb SZCZEGÓŁOWY**: opisz krok po kroku z numerami linii."
            " Grupuj linie w bloki, gdy to ma sens (np. 1–5: importy, 6–12: definicja funkcji)."
            " Dla każdego bloku podaj zwięzłe, rzeczowe wyjaśnienie. Nie kopiuj całych linii kodu.\n\n"
        )
    fenced = f"```code\n{code_text}\n```"
    return header + spec + fenced

# ──────────────────────────────────────────────────────────────────────────────
# Funkcje modeli
# ──────────────────────────────────────────────────────────────────────────────
def generate_text_summary(code_text: str, level: str) -> str:
    """Używa GPT-4o-mini do wygenerowania opisu kodu w PL."""
    prompt = build_user_prompt(code_text, level)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + " Odpowiadaj po polsku."},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content.strip()

def synthesize_speech(text: str, voice_name: str) -> Path:
    """
    Generuje MP3 z użyciem `tts-1` i zwraca ścieżkę do pliku tymczasowego.
    """
    mp3_path = Path(tempfile.mkstemp(suffix=".mp3")[1])

    # Streaming do pliku — kompatybilne ze Streamlit Cloud
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice=voice_name,
        input=text,
        format="mp3",
    ) as stream:
        stream.stream_to_file(str(mp3_path))

    return mp3_path

# ──────────────────────────────────────────────────────────────────────────────
# Logika główna
# ──────────────────────────────────────────────────────────────────────────────
if submitted:
    if not code or code.strip() == "":
        st.warning("Wklej najpierw kod źródłowy.")
        st.stop()

    with st.spinner("🔎 Analizuję kod i tworzę opis…"):
        try:
            description = generate_text_summary(code, detail)
        except Exception as e:
            st.error(f"Nie udało się wygenerować opisu: {e}")
            st.stop()

    st.subheader("📄 Opis kodu")
    st.write(description)

    if make_audio:
        with st.spinner("🎧 Generuję wersję audio…"):
            try:
                mp3_file = synthesize_speech(description, voice)
                audio_bytes = Path(mp3_file).read_bytes()
                st.audio(audio_bytes, format="audio/mp3")
                st.download_button(
                    label="⬇️ Pobierz opis jako MP3",
                    data=audio_bytes,
                    file_name="opis_kodu.mp3",
                    mime="audio/mpeg",
                )
            except Exception as e:
                st.error(f"Nie udało się wygenerować audio: {e}")

# Stopka
st.markdown("---")
st.caption(
    "Technologie: Streamlit · OpenAI `gpt-4o-mini` (opis) · OpenAI `tts-1` (audio). "
    "Nigdy nie commituj klucza API do repozytorium."
)
