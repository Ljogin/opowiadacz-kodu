# Code Narrator 🎙️ (Streamlit)

Aplikacja, która opisuje, co robi kod źródłowy:
- tryb **Ogólny** (2–5 zdań),
- tryb **Szczegółowy** (po liniach / blokach z numerami),
- opcjonalny **podcast MP3** z opisem.

## Uruchomienie lokalne
1) Utwórz `.env`:
   OPENAI_API_KEY=sk-...

2) Zainstaluj zależności:
   pip install -r requirements.txt

3) Start:
   streamlit run app.py

## Deploy w Streamlit Community Cloud
- Połącz repozytorium.
- W **Secrets** dodaj:
  OPENAI_API_KEY = sk-...

## Bezpieczeństwo
- Nigdy nie zapisuj klucza w repozytorium.
- Korzystaj z `st.secrets` (chmura) albo `.env` (lokalnie).
