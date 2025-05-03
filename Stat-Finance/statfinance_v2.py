import streamlit as st
import yfinance as yf
import pandas as pd
import random
import math

# === App-Konfiguration ===
st.set_page_config(page_title="Wahrscheinlichkeitsanalyse", layout="centered")
st.title("📊 Wahrscheinlichkeitsanalyse nach Musterbedingungen")

# === Einführung & Anleitung ===
st.markdown("""
# 📘 Anleitung zur Wahrscheinlichkeitsanalyse

Diese App analysiert historische Kursdaten und berechnet die Wahrscheinlichkeit für eine bullishe oder bearishe Folge-Kerze – basierend auf einem benutzerdefinierten Muster vergangener Tage.

**So funktioniert's:**
- Wähle ein Symbol (z. B. EURUSD=X, SPY).
- Lege Zeitraum und Zeitintervall fest (z. B. Daily, Weekly, Monthly).
- Erstelle dein individuelles Candle-Muster (z. B. 2x Bullish + 1x Bearish).
- Die App zeigt dir, wie oft danach deine Zielrichtung eingetreten ist.
---
""")

# === Eingabefelder ===
symbol = st.text_input("📈 Symbol (z. B. SPY, EURUSD=X, BTC-USD)", "EURUSD=X")
zeitraum = st.selectbox("🗓 Zeitraum", ["1y", "2y", "5y", "10y"])
zeitintervall = st.selectbox("🕒 Zeitintervall", ["Daily", "Weekly", "Monthly"])
intervall_map = {
    "Daily": "1d",
    "Weekly": "1wk",
    "Monthly": "1mo"
}
intervall = intervall_map[zeitintervall]
zielrichtung = st.selectbox("🎯 Zielrichtung (nächste Candle)", ["bullish", "bearish"])

# === Dynamische Musterkette ===
if "musterliste" not in st.session_state:
    st.session_state["musterliste"] = []

musterliste = st.session_state.musterliste
st.markdown("## ➕ Muster erstellen")

if st.button("➕ Neue Bedingung hinzufügen"):
    st.session_state.musterliste.append({"typ": "bullish", "anzahl": 1})

for i, eintrag in enumerate(st.session_state.musterliste):
    col1, col2, col3 = st.columns([4, 2, 1])
    with col1:
        st.session_state.musterliste[i]["typ"] = st.selectbox(
            f"Muster {i+1}", ["bullish", "bearish"], key=f"typ_{i}"
        )
    with col2:
        st.session_state.musterliste[i]["anzahl"] = st.number_input(
            f"Anzahl", min_value=1, max_value=5, value=1, key=f"anzahl_{i}"
        )
    with col3:
        if st.button("❌", key=f"del_{i}"):
            st.session_state.musterliste.pop(i)
            st.experimental_rerun()

# === Analyse starten ===
if st.button("🔍 Analyse starten") and st.session_state.musterliste:
    try:
        st.info("📡 Lade historische Daten...")
        df = yf.download(symbol, period=zeitraum, interval=intervall)
        df = df.dropna()

        df['Bullish'] = df['Close'] > df['Open']
        df['Bearish'] = df['Close'] < df['Open']

        # Muster in Liste umwandeln (True = Bullish, False = Bearish)
        muster_bool = []
        for eintrag in st.session_state.musterliste:
            muster_bool.extend([True if eintrag["typ"] == "bullish" else False] * eintrag["anzahl"])

        def match_muster(idx):
            if idx < len(muster_bool):
                return False
            status = list(df.iloc[idx - len(muster_bool):idx]['Bullish'])
            return status == muster_bool

        pattern = [match_muster(i) for i in range(len(df))]
        pattern = pd.Series(pattern, index=df.index)

        ziel = df['Bullish'].shift(-1) if zielrichtung == "bullish" else df['Bearish'].shift(-1)
        relevante = ziel[pattern]

        if relevante.empty:
            st.warning("⚠️ Keine passenden Muster im gewählten Zeitraum gefunden.")
        else:
            wahrscheinlichkeit = relevante.mean()
            anzahl_treffer = relevante.sum()
            anzahl_faelle = relevante.count()

            # Definiere 'muster_typ' basierend auf dem Muster
            muster_typ = "Bullish" if any(e["typ"] == "bullish" for e in st.session_state.musterliste) else "Bearish"

            st.success(
                f"🎯 Wahrscheinlichkeit für eine **{zielrichtung}e** Candle nach {len(musterliste)} {muster_typ}-Candle(n): **{float(wahrscheinlichkeit):.2%}**"
            )
            st.write(f"✔️ Treffer: {int(anzahl_treffer)} von {anzahl_faelle} Fällen")
            st.line_chart(df['Close'])

            # === Vergleichswahrscheinlichkeiten ===
            ziel_bullish = df['Bullish'].shift(-1)
            ziel_bearish = df['Bearish'].shift(-1)
            ziel_neutral = df['Close'].shift(-1) == df['Open'].shift(-1)

            bullish_nach_muster = ziel_bullish[pattern]
            bearish_nach_muster = ziel_bearish[pattern]
            neutral_nach_muster = ziel_neutral[pattern]

            def safe_mean(series):
                try:
                    val = float(series.mean())
                    return 0.0 if pd.isna(val) or math.isnan(val) else val
                except:
                    return 0.0

            bullish_wert = safe_mean(bullish_nach_muster)
            bearish_wert = safe_mean(bearish_nach_muster)
            neutral_wert = safe_mean(neutral_nach_muster)

            st.subheader("📊 Vergleich basierend auf deinem Muster")
            table_df = pd.DataFrame({
                "Nächste Candle bullish": [f"{bullish_wert:.2%}"],
                "Nächste Candle bearish": [f"{bearish_wert:.2%}"],
                "Keine Veränderung": [f"{neutral_wert:.2%}"]
            }, index=["Muster-Auswertung"])
            st.table(table_df)

            chart_data = pd.DataFrame({
                "Bullish": [bullish_wert],
                "Bearish": [bearish_wert],
                "Neutral": [neutral_wert],
            }, index=["Muster"])
            st.bar_chart(chart_data)

            # === Durchschnittliche Kursveränderung ===
            st.subheader("📉 Durchschnittliche Kursveränderung nach Muster")
            ret = (df['Close'].shift(-1) - df['Close']) / df['Close'] * 100
            ret_nach_muster = ret[pattern]
            durchschnitt = safe_mean(ret_nach_muster)
            st.write(f"📈 Ø Veränderung (Close zu Close in %): **{durchschnitt:.2f}%**")
            st.line_chart(ret_nach_muster.dropna())

    except Exception as e:
        st.error(f"❌ Fehler während der Analyse: {e}")
