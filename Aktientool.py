                industry_score_candidates.append(0)

if industry_score_candidates:
    industry_valuation_points = float(np.mean(industry_score_candidates))
add_score_component("Branchenbewertung", industry_valuation_points)


# 11) DCF: bewertet, ob der DCF-Wert über dem aktuellen Kurs liegt
dcf_points = np.nan
if not pd.isna(dcf_upside_pct):
    dcf_points = (
        10 if dcf_upside_pct >= 50 else
        9 if dcf_upside_pct >= 30 else
        8 if dcf_upside_pct >= 20 else
        6 if dcf_upside_pct >= 0 else
        3 if dcf_upside_pct >= -20 else
        0
    )
add_score_component("DCF-Bewertung", dcf_points)


# Score wird anhand der tatsächlich verfügbaren Komponenten skaliert.
available_weight = sum(
    score_weights[name] for name in score_components
)
earned_points = sum(score_components.values())

if available_weight > 0:
    fundamental_score_100 = earned_points / available_weight * 100

    if fundamental_score_100 >= 80:
        score_label = "Sehr attraktiv"
    elif fundamental_score_100 >= 65:
        score_label = "Attraktiv"
    elif fundamental_score_100 >= 50:
        score_label = "Ausgeglichen"
    elif fundamental_score_100 >= 35:
        score_label = "Schwach"
    else:
        score_label = "Sehr schwach"

    score_cols = st.columns(3)

    with score_cols[0]:
        st.metric(
            "Fundamentaler Score",
            f"{fundamental_score_100:.1f} / 100"
        )

    with score_cols[1]:
        st.metric("Einordnung", score_label)

    with score_cols[2]:
        st.metric(
            "Datenabdeckung",
            f"{available_weight} / 100 Punkte"
        )

    score_table = pd.DataFrame([
        {
            "Kriterium": name,
            "Punkte": round(points, 1),
            "Max. Punkte": score_weights[name],
            "Erfüllung (%)": round(
                points / score_weights[name] * 100, 1
            )
        }
        for name, points in score_components.items()
    ])

    st.dataframe(
        score_table.style.format({
            "Punkte": "{:.1f}",
            "Max. Punkte": "{:.0f}",
            "Erfüllung (%)": "{:.1f} %"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Nicht verfügbare Kennzahlen werden aus der Bewertung ausgelassen. "
        "Der Score wird auf die verfügbaren Gewichtungspunkte normiert. "
        "Ein hoher Score ist keine Kaufempfehlung."
    )

else:
    st.info(
        "Der fundamentale Score konnte wegen fehlender Finanzdaten "
        "nicht berechnet werden."
    )


# ============================================================
# BRANCHENVERGLEICH ANZEIGEN
# ============================================================

if not peer_df.empty:

    st.subheader("🏭 Unternehmen im Branchenvergleich")

    peer_display = peer_df.copy()

    st.dataframe(
        peer_display.style.format({
            "FCF-Marge (%)": "{:.1f} %",
            "ROE (%)": "{:.1f} %",
            "Debt/Equity (%)": "{:.1f} %",
            "KGV": "{:.2f}",
            "KBV": "{:.2f}",
            "KCV": "{:.2f}",
            "KUV": "{:.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# HINWEISE
# ============================================================

st.divider()

st.caption(
    "Hinweis: Die Daten stammen von Yahoo Finance. "
    "Historische Jahresendkurse entsprechen dem letzten verfügbaren "
    "Börsenhandelstag des jeweiligen Kalenderjahres. "
