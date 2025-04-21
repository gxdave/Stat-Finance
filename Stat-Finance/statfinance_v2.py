import streamlit as st
import yfinance as yf
import pandas as pd
import random
import math

# === App-Konfiguration ===
st.set_page_config(page_title="Wahrscheinlichkeitsanalyse", layout="centered")
st.title("📊 Wahrscheinlichkeitsanalyse nach Musterbedingungen")

# === Eingabefelder ===
symbol = st.text_input("📈 Symbol (z. B. SPY, EURUSD=X, BTC-USD)", "EURUSD=X")
zeitraum = st.selectbox("🗓 Zeitraum", ["1y", "2y", "5y", "10y"])
anzahl_tage = st.slider("🔢 Anzahl Muster-Tage", 1, 5, 2)
muster_typ = st.selectbox("📋 Muster-Art", ["bullish", "bearish", "gemischt"])
zielrichtung = st.selectbox("🎯 Zielrichtung (nächster Tag)", ["bullish", "bearish"])

# === Analyse starten ===
if st.button("🔍 Analyse starten"):
    try:
        st.info("📡 Lade historische Daten...")
        df = yf.download(symbol, period=zeitraum)
        df = df.dropna()

        # === Vorbereitung: Kerzenanalyse ===
        df['Bullish'] = df['Close'] > df['Open']
        df['Bearish'] = df['Close'] < df['Open']

        # === Mustererkennung ===
        if muster_typ == "bullish":
            pattern_bool = df['Bullish']
        elif muster_typ == "bearish":
            pattern_bool = df['Bearish']
        elif muster_typ == "gemischt":
            random_pattern = [random.choice([True, False]) for _ in range(anzahl_tage)]
            st.write(f"🔁 Zufälliges gemischtes Muster: {['bullish' if x else 'bearish' for x in random_pattern]}")

            def match_muster(idx):
                if idx < anzahl_tage:
                    return False
                status = list(df.iloc[idx - anzahl_tage:idx]['Bullish'])
                return status == random_pattern

            pattern = [match_muster(i) for i in range(len(df))]
            pattern = pd.Series(pattern, index=df.index)
        else:
            pattern_bool = None

        if muster_typ in ["bullish", "bearish"]:
            pattern = pattern_bool.rolling(anzahl_tage).sum() == anzahl_tage

        # === Ziel definieren ===
        ziel = df['Bullish'].shift(-1) if zielrichtung == "bullish" else df['Bearish'].shift(-1)

        # === Relevante Fälle extrahieren ===
        relevante = ziel[pattern]

        if relevante.empty:
            st.warning("⚠️ Keine passenden Muster im gewählten Zeitraum gefunden.")
        else:
            wahrscheinlichkeit = relevante.mean()
            anzahl_treffer = relevante.sum()
            anzahl_faelle = relevante.count()

            if pd.isna(wahrscheinlichkeit) or math.isnan(float(wahrscheinlichkeit)):
                wahrscheinlichkeit = 0.0

            st.success(
                f"🎯 Wahrscheinlichkeit für **{zielrichtung}en** Tag nach {anzahl_tage} {muster_typ}-Tagen: **{float(wahrscheinlichkeit):.2%}**"
            )
            st.write(f"✔️ Treffer: {int(anzahl_treffer)} von {anzahl_faelle} Fällen")
            st.line_chart(df['Close'])

        # === Vergleich & Visualisierung basierend auf Eingabe-Muster ===
        st.subheader("📊 Vergleich basierend auf deiner Eingabe")

        ziel_bullish = df['Bullish'].shift(-1)
        ziel_bearish = df['Bearish'].shift(-1)
        ziel_neutral = df['Close'].shift(-1) == df['Open'].shift(-1)

        bullish_nach_muster = ziel_bullish[pattern]
        bearish_nach_muster = ziel_bearish[pattern]
        neutral_nach_muster = ziel_neutral[pattern]

        def safe_mean(series):
            try:
                val = float(series.mean())
                if pd.isna(val) or math.isnan(val):
                    return 0.0
                return val
            except:
                return 0.0

        bullish_wert = safe_mean(bullish_nach_muster)
        bearish_wert = safe_mean(bearish_nach_muster)
        neutral_wert = safe_mean(neutral_nach_muster)

        table_df = pd.DataFrame({
            "Nächster Tag bullish": [f"{bullish_wert:.2%}"],
            "Nächster Tag bearish": [f"{bearish_wert:.2%}"],
            "Keine Veränderung": [f"{neutral_wert:.2%}"]
        }, index=[f"Nach {anzahl_tage} {muster_typ}-Tagen"])
        st.table(table_df)

        st.subheader("📈 Visualisierung für dieses Muster")
        chart_data = pd.DataFrame({
            "Bullish": [bullish_wert],
            "Bearish": [bearish_wert],
            "Neutral": [neutral_wert],
        }, index=[f"Nach {anzahl_tage} {muster_typ}"])
        st.bar_chart(chart_data)

        # === Durchschnittliche Kursveränderung nach dem Signal ===
        st.subheader("📉 Durchschnittliche Kursveränderung nach Muster")

        close = df['Close']
        ret = (close.shift(-1) - close) / close * 100
        ret_nach_muster = ret[pattern]

        durchschnitt = safe_mean(ret_nach_muster)
        st.write(f"📈 Ø Veränderung (Close zu Close in %): **{durchschnitt:.2f}%**")
        st.line_chart(ret_nach_muster.dropna())

    except Exception as e:
        st.error(f"❌ Fehler während der Analyse: {e}")
