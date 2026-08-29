{\rtf1\ansi\ansicpg1252\cocoartf2761
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fmodern\fcharset0 Courier;}
{\colortbl;\red255\green255\blue255;\red0\green0\blue0;}
{\*\expandedcolortbl;;\cssrgb\c0\c0\c0;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\deftab720
\pard\pardeftab720\partightenfactor0

\f0\fs26 \cf0 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 import streamlit as st\
import yfinance as yf\
import pandas as pd\
import numpy as np\
\
\
# ============================================================\
# STREAMLIT KONFIGURATION\
# ============================================================\
\
st.set_page_config(\
    page_title="Aktien-Bewertungs-Tool",\
    page_icon="\uc0\u55357 \u56520 ",\
    layout="wide"\
)\
\
st.title("\uc0\u55357 \u56520  Mein personalisiertes Aktien-Bewertungs-Tool")\
st.caption(\
    "Fundamentalanalyse \'b7 Historische Bewertung \'b7 Branchenvergleich \'b7 DCF"\
)\
\
\
# ============================================================\
# HILFSFUNKTIONEN\
# ============================================================\
\
def safe_get(df, row, column, default=np.nan):\
    """Sicheres Auslesen eines Datenpunkts."""\
    try:\
        if df is not None and not df.empty:\
            if row in df.index and column in df.columns:\
                value = df.loc[row, column]\
\
                if pd.notna(value):\
                    return float(value)\
    except Exception:\
        pass\
\
    return default\
\
\
def get_value(df, possible_rows, column, default=np.nan):\
    """Probiert mehrere Yahoo-Finance-Bezeichnungen."""\
    for row in possible_rows:\
        value = safe_get(\
            df,\
            row,\
            column,\
            np.nan\
        )\
\
        if pd.notna(value):\
            return value\
\
    return default\
\
\
def clean_number(value):\
    """Konvertiert Zahlen sicher nach float."""\
    try:\
        if value is None:\
            return np.nan\
\
        if isinstance(value, str):\
            value = value.replace(",", "")\
\
        return float(value)\
\
    except Exception:\
        return np.nan\
\
\
def get_year_end_price(share, year):\
    """\
    Letzter verf\'fcgbarer Schlusskurs bis einschlie\'dflich 31.12.\
    """\
    try:\
\
        start_date = f"\{year\}-12-20"\
        end_date = f"\{year + 1\}-01-03"\
\
        hist = share.history(\
            start=start_date,\
            end=end_date,\
            auto_adjust=False\
        )\
\
        if hist.empty:\
            return np.nan\
\
        cutoff = pd.Timestamp(\
            f"\{year\}-12-31"\
        ).date()\
\
        hist = hist[\
            hist.index.date <= cutoff\
        ]\
\
        if hist.empty:\
            return np.nan\
\
        return float(\
            hist["Close"].iloc[-1]\
        )\
\
    except Exception:\
        return np.nan\
\
\
def growth_score(values, max_points):\
    """\
    Bewertet das Wachstum vom \'e4ltesten zum j\'fcngsten\
    verf\'fcgbaren Wert.\
    """\
\
    values = pd.Series(\
        values\
    ).replace(\
        [np.inf, -np.inf],\
        np.nan\
    ).dropna()\
\
    if len(values) < 2:\
        return 0\
\
    oldest = values.iloc[-1]\
    newest = values.iloc[0]\
\
    if oldest <= 0:\
        return 0\
\
    growth = (\
        (newest - oldest)\
        / abs(oldest)\
    ) * 100\
\
    if growth >= 50:\
        return max_points\
\
    elif growth >= 30:\
        return max_points * 0.90\
\
    elif growth >= 15:\
        return max_points * 0.80\
\
    elif growth >= 5:\
        return max_points * 0.70\
\
    elif growth >= 0:\
        return max_points * 0.55\
\
    elif growth >= -10:\
        return max_points * 0.35\
\
    elif growth >= -25:\
        return max_points * 0.15\
\
    else:\
        return 0\
\
\
def valuation_score(\
    current_multiple,\
    historical_multiple,\
    max_points\
):\
    """\
    Je niedriger das aktuelle Multiple gegen\'fcber\
    dem historischen Durchschnitt, desto h\'f6her der Score.\
    """\
\
    if (\
        pd.isna(current_multiple)\
        or pd.isna(historical_multiple)\
        or current_multiple <= 0\
        or historical_multiple <= 0\
    ):\
        return 0\
\
    discount = (\
        (historical_multiple - current_multiple)\
        / historical_multiple\
    ) * 100\
\
    if discount >= 30:\
        return max_points\
\
    elif discount >= 20:\
        return max_points * 0.90\
\
    elif discount >= 10:\
        return max_points * 0.80\
\
    elif discount >= 0:\
        return max_points * 0.65\
\
    elif discount >= -10:\
        return max_points * 0.45\
\
    elif discount >= -20:\
        return max_points * 0.20\
\
    else:\
        return 0\
\
\
def calculate_current_multiple(\
    price,\
    fundamental\
):\
    if (\
        pd.notna(price)\
        and pd.notna(fundamental)\
        and fundamental > 0\
    ):\
        return price / fundamental\
\
    return np.nan\
\
\
def format_number(value, decimals=2):\
    if pd.isna(value):\
        return "-"\
\
    return f"\{value:,.\{decimals\}f\}"\
\
\
def get_latest_ttm_value(\
    ttm_df,\
    possible_rows\
):\
    """\
    Holt einen TTM-Wert aus yfinance.\
    """\
    if ttm_df is None or ttm_df.empty:\
        return np.nan\
\
    for row in possible_rows:\
\
        try:\
\
            if row in ttm_df.index:\
\
                value = ttm_df.loc[row]\
\
                if isinstance(value, pd.Series):\
\
                    value = value.dropna()\
\
                    if not value.empty:\
                        return float(value.iloc[0])\
\
                else:\
\
                    return float(value)\
\
        except Exception:\
            pass\
\
    return np.nan\
\
\
# ============================================================\
# SIDEBAR \'96 DCF ANNAHMEN\
# ============================================================\
\
st.sidebar.header("\uc0\u9881 \u65039  DCF-Annahmen")\
\
forecast_years = st.sidebar.slider(\
    "DCF-Prognosezeitraum",\
    min_value=3,\
    max_value=10,\
    value=5\
)\
\
growth_rate = st.sidebar.slider(\
    "FCF-Wachstum im Prognosezeitraum (%)",\
    min_value=-10.0,\
    max_value=30.0,\
    value=8.0,\
    step=0.5\
)\
\
wacc = st.sidebar.slider(\
    "WACC / Diskontierungszins (%)",\
    min_value=5.0,\
    max_value=15.0,\
    value=9.0,\
    step=0.25\
)\
\
terminal_growth = st.sidebar.slider(\
    "Terminal Growth (%)",\
    min_value=0.0,\
    max_value=5.0,\
    value=2.5,\
    step=0.25\
)\
\
margin_of_safety = st.sidebar.slider(\
    "Sicherheitsmarge (%)",\
    min_value=0,\
    max_value=50,\
    value=20,\
    step=5\
)\
\
peer_count = st.sidebar.slider(\
    "Anzahl Branchen-Peers",\
    min_value=3,\
    max_value=10,\
    value=5\
)\
\
\
# ============================================================\
# BENUTZEREINGABE\
# ============================================================\
\
ticker_symbol = st.text_input(\
    "Aktiensymbol / Ticker",\
    value="AAPL"\
).upper().strip()\
\
\
if ticker_symbol:\
\
    try:\
\
        # ====================================================\
        # TICKER\
        # ====================================================\
\
        share = yf.Ticker(\
            ticker_symbol\
        )\
\
\
        # ====================================================\
        # ALLGEMEINE INFORMATIONEN\
        # ====================================================\
\
        info = \{\}\
\
        try:\
            info = share.info\
        except Exception:\
            info = \{\}\
\
\
        company_name = info.get(\
            "longName",\
            ticker_symbol\
        )\
\
        sector = info.get(\
            "sector",\
            "Nicht verf\'fcgbar"\
        )\
\
        industry = info.get(\
            "industry",\
            "Nicht verf\'fcgbar"\
        )\
\
        currency = info.get(\
            "currency",\
            "USD"\
        )\
\
\
        # ====================================================\
        # AKTUELLER KURS\
        # ====================================================\
\
        current_history = share.history(\
            period="5d",\
            auto_adjust=False\
        )\
\
        if current_history.empty:\
            st.error(\
                "Es konnte kein Aktienkurs abgerufen werden."\
            )\
            st.stop()\
\
        current_price = float(\
            current_history["Close"].dropna().iloc[-1]\
        )\
\
\
        # ====================================================\
        # HEADER\
        # ====================================================\
\
        st.subheader(\
            f"\{company_name\} (\{ticker_symbol\})"\
        )\
\
        col1, col2, col3, col4 = st.columns(4)\
\
        with col1:\
            st.metric(\
                "Aktueller Kurs",\
                f"\{current_price:.2f\} \{currency\}"\
            )\
\
        with col2:\
            st.metric(\
                "Sektor",\
                sector\
            )\
\
        with col3:\
            st.metric(\
                "Branche",\
                industry\
            )\
\
        with col4:\
            st.metric(\
                "Marktkapitalisierung",\
                (\
                    f"\{info.get('marketCap') / 1e9:.1f\} Mrd."\
                    if isinstance(\
                        info.get("marketCap"),\
                        (int, float)\
                    )\
                    else "-"\
                )\
            )\
\
\
        # ====================================================\
        # FINANZDATEN\
        # ====================================================\
\
        financials = share.financials\
        balance_sheet = share.balance_sheet\
        cashflow = share.cashflow\
\
\
        # ====================================================\
        # TTM DATEN\
        # ====================================================\
\
        try:\
            ttm_income = share.ttm_income_stmt\
        except Exception:\
            ttm_income = pd.DataFrame()\
\
        try:\
            ttm_cashflow = share.ttm_cashflow\
        except Exception:\
            ttm_cashflow = pd.DataFrame()\
\
\
        # ====================================================\
        # DIVIDENDEN\
        # ====================================================\
\
        try:\
\
            actions = share.actions\
\
            if (\
                actions is not None\
                and not actions.empty\
                and "Dividends" in actions.columns\
            ):\
\
                dividends = actions[\
                    "Dividends"\
                ].copy()\
\
                dividends = dividends[\
                    dividends > 0\
                ]\
\
                dividends_by_year = (\
                    dividends\
                    .groupby(\
                        dividends.index.year\
                    )\
                    .sum()\
                )\
\
            else:\
\
                dividends_by_year = pd.Series(\
                    dtype=float\
                )\
\
        except Exception:\
\
            dividends_by_year = pd.Series(\
                dtype=float\
            )\
\
\
        # ====================================================\
        # HISTORISCHE JAHRE\
        # ====================================================\
\
        if financials is None or financials.empty:\
\
            st.error(\
                "Yahoo Finance hat keine historischen "\
                "Finanzdaten f\'fcr diesen Titel geliefert."\
            )\
\
            st.stop()\
\
\
        years = financials.columns[:5]\
\
        data_list = []\
\
\
        # ====================================================\
        # JAHRESSCHLEIFE\
        # ====================================================\
\
        for year in years:\
\
            year_number = year.year\
\
\
            # ------------------------------------------------\
            # UMSATZ\
            # ------------------------------------------------\
\
            sales = get_value(\
                financials,\
                [\
                    "Total Revenue",\
                    "Operating Revenue"\
                ],\
                year\
            )\
\
\
            # ------------------------------------------------\
            # NETTOGEWINN\
            # ------------------------------------------------\
\
            net_income = get_value(\
                financials,\
                [\
                    "Net Income",\
                    "Net Income Common Stockholders"\
                ],\
                year\
            )\
\
\
            # ------------------------------------------------\
            # EIGENKAPITAL\
            # ------------------------------------------------\
\
            equity = get_value(\
                balance_sheet,\
                [\
                    "Stockholders Equity",\
                    "Common Stock Equity",\
                    "Total Equity Gross Minority Interest"\
                ],\
                year\
            )\
\
\
            # ------------------------------------------------\
            # AKTIVA\
            # ------------------------------------------------\
\
            total_assets = get_value(\
                balance_sheet,\
                [\
                    "Total Assets"\
                ],\
                year\
            )\
\
\
            # ------------------------------------------------\
            # SCHULDEN\
            # ------------------------------------------------\
\
            total_debt = get_value(\
                balance_sheet,\
                [\
                    "Total Debt",\
                    "Total Debt And Capital Lease Obligation"\
                ],\
                year\
            )\
\
\
            # ------------------------------------------------\
            # CASH\
            # ------------------------------------------------\
\
            cash = get_value(\
                balance_sheet,\
                [\
                    "Cash And Cash Equivalents",\
                    "Cash Cash Equivalents And Short Term Investments"\
                ],\
                year\
            )\
\
\
            # ------------------------------------------------\
            # FORDERUNGEN\
            # ------------------------------------------------\
\
            receivables = get_value(\
                balance_sheet,\
                [\
                    "Receivables",\
                    "Accounts Receivable"\
                ],\
                year\
            )\
\
\
            # ------------------------------------------------\
            # CURRENT ASSETS\
            # ------------------------------------------------\
\
            current_assets = get_value(\
                balance_sheet,\
                [\
                    "Current Assets"\
                ],\
                year\
            )\
\
\
            # ------------------------------------------------\
            # CURRENT LIABILITIES\
            # ------------------------------------------------\
\
            current_liabilities = get_value(\
                balance_sheet,\
                [\
                    "Current Liabilities"\
                ],\
                year\
            )\
\
\
            # ------------------------------------------------\
            # FREE CASHFLOW\
            # ------------------------------------------------\
\
            free_cashflow = get_value(\
                cashflow,\
                [\
                    "Free Cash Flow"\
                ],\
                year\
            )\
\
\
            # Falls Yahoo keinen FCF liefert:\
            # CFO - CapEx\
            if pd.isna(free_cashflow):\
\
                operating_cf = get_value(\
                    cashflow,\
                    [\
                        "Operating Cash Flow",\
                        "Total Cash From Operating Activities"\
                    ],\
                    year\
                )\
\
                capex = get_value(\
                    cashflow,\
                    [\
                        "Capital Expenditure"\
                    ],\
                    year\
                )\
\
                if (\
                    pd.notna(operating_cf)\
                    and pd.notna(capex)\
                ):\
\
                    free_cashflow = (\
                        operating_cf\
                        + capex\
                    )\
\
\
            # ------------------------------------------------\
            # AKTIENANZAHL\
            # ------------------------------------------------\
\
            shares_outstanding = get_value(\
                financials,\
                [\
                    "Diluted Average Shares",\
                    "Basic Average Shares"\
                ],\
                year\
            )\
\
\
            if pd.isna(\
                shares_outstanding\
            ):\
\
                shares_outstanding = get_value(\
                    balance_sheet,\
                    [\
                        "Ordinary Shares Number",\
                        "Share Issued"\
                    ],\
                    year\
                )\
\
\
            # ------------------------------------------------\
            # EPS\
            # ------------------------------------------------\
\
            if (\
                pd.notna(net_income)\
                and pd.notna(shares_outstanding)\
                and shares_outstanding != 0\
            ):\
\
                eps = (\
                    net_income\
                    / shares_outstanding\
                )\
\
            else:\
\
                eps = np.nan\
\
\
            # ------------------------------------------------\
            # BUCHWERT JE AKTIE\
            # ------------------------------------------------\
\
            if (\
                pd.notna(equity)\
                and pd.notna(shares_outstanding)\
                and shares_outstanding != 0\
            ):\
\
                bvps = (\
                    equity\
                    / shares_outstanding\
                )\
\
            else:\
\
                bvps = np.nan\
\
\
            # ------------------------------------------------\
            # FCF JE AKTIE\
            # ------------------------------------------------\
\
            if (\
                pd.notna(free_cashflow)\
                and pd.notna(shares_outstanding)\
                and shares_outstanding != 0\
            ):\
\
                fcf_per_share = (\
                    free_cashflow\
                    / shares_outstanding\
                )\
\
            else:\
\
                fcf_per_share = np.nan\
\
\
            # ------------------------------------------------\
            # UMSATZ JE AKTIE\
            # ------------------------------------------------\
\
            if (\
                pd.notna(sales)\
                and pd.notna(shares_outstanding)\
                and shares_outstanding != 0\
            ):\
\
                sales_per_share = (\
                    sales\
                    / shares_outstanding\
                )\
\
            else:\
\
                sales_per_share = np.nan\
\
\
            # ------------------------------------------------\
            # DIVIDENDE JE AKTIE\
            # ------------------------------------------------\
\
            dividend_per_share = (\
                dividends_by_year.get(\
                    year_number,\
                    0\
                )\
            )\
\
\
            # ------------------------------------------------\
            # AUSSCH\'dcTTUNGSQUOTE 1\
            # ------------------------------------------------\
\
            if (\
                pd.notna(eps)\
                and eps > 0\
            ):\
\
                payout_ratio_1 = (\
                    dividend_per_share\
                    / eps\
                ) * 100\
\
            else:\
\
                payout_ratio_1 = np.nan\
\
\
            # ------------------------------------------------\
            # AUSSCH\'dcTTUNGSQUOTE 2\
            # ------------------------------------------------\
\
            if (\
                pd.notna(fcf_per_share)\
                and fcf_per_share > 0\
            ):\
\
                payout_ratio_2 = (\
                    dividend_per_share\
                    / fcf_per_share\
                ) * 100\
\
            else:\
\
                payout_ratio_2 = np.nan\
\
\
            # ------------------------------------------------\
            # LIQUIDIT\'c4T\
            # ------------------------------------------------\
\
            if (\
                pd.notna(current_liabilities)\
                and current_liabilities != 0\
            ):\
\
                liq_1 = (\
                    cash\
                    / current_liabilities\
                ) * 100\
\
                liq_2 = (\
                    (cash + receivables)\
                    / current_liabilities\
                ) * 100\
\
                liq_3 = (\
                    current_assets\
                    / current_liabilities\
                ) * 100\
\
            else:\
\
                liq_1 = np.nan\
                liq_2 = np.nan\
                liq_3 = np.nan\
\
\
            # ------------------------------------------------\
            # FCF-MARGE\
            # ------------------------------------------------\
\
            if (\
                pd.notna(free_cashflow)\
                and pd.notna(sales)\
                and sales != 0\
            ):\
\
                fcf_margin = (\
                    free_cashflow\
                    / sales\
                ) * 100\
\
            else:\
\
                fcf_margin = np.nan\
\
\
            # ------------------------------------------------\
            # ROE\
            # ------------------------------------------------\
\
            if (\
                pd.notna(net_income)\
                and pd.notna(equity)\
                and equity > 0\
            ):\
\
                roe = (\
                    net_income\
                    / equity\
                ) * 100\
\
            else:\
\
                roe = np.nan\
\
\
            # ------------------------------------------------\
            # DEBT / EQUITY\
            # ------------------------------------------------\
\
            if (\
                pd.notna(total_debt)\
                and pd.notna(equity)\
                and equity > 0\
            ):\
\
                debt_to_equity = (\
                    total_debt\
                    / equity\
                ) * 100\
\
            else:\
\
                debt_to_equity = np.nan\
\
\
            # ------------------------------------------------\
            # NETTO-SCHULDEN\
            # ------------------------------------------------\
\
            if (\
                pd.notna(total_debt)\
                and pd.notna(cash)\
            ):\
\
                net_debt = (\
                    total_debt - cash\
                )\
\
            else:\
\
                net_debt = np.nan\
\
\
            # ------------------------------------------------\
            # HISTORISCHER JAHRESENDKURS\
            # ------------------------------------------------\
\
            year_end_price = (\
                get_year_end_price(\
                    share,\
                    year_number\
                )\
            )\
\
\
            # ------------------------------------------------\
            # HISTORISCHE MULTIPLES\
            # ------------------------------------------------\
\
            kgv = calculate_current_multiple(\
                year_end_price,\
                eps\
            )\
\
            kcv = calculate_current_multiple(\
                year_end_price,\
                fcf_per_share\
            )\
\
            kbv = calculate_current_multiple(\
                year_end_price,\
                bvps\
            )\
\
            kuv = calculate_current_multiple(\
                year_end_price,\
                sales_per_share\
            )\
\
\
            # ------------------------------------------------\
            # DATENSATZ\
            # ------------------------------------------------\
\
            data_list.append(\{\
\
                "Jahr":\
                    year.strftime("%Y"),\
\
                "Jahresendkurs":\
                    year_end_price,\
\
                "Umsatz (Mrd.)":\
                    sales / 1e9\
                    if pd.notna(sales)\
                    else np.nan,\
\
                "Nettogewinn (Mrd.)":\
                    net_income / 1e9\
                    if pd.notna(net_income)\
                    else np.nan,\
\
                "Eigenkapital (Mrd.)":\
                    equity / 1e9\
                    if pd.notna(equity)\
                    else np.nan,\
\
                "Free Cashflow (Mrd.)":\
                    free_cashflow / 1e9\
                    if pd.notna(free_cashflow)\
                    else np.nan,\
\
                "EPS":\
                    eps,\
\
                "Buchwert/Aktie":\
                    bvps,\
\
                "FCF/Aktie":\
                    fcf_per_share,\
\
                "Umsatz/Aktie":\
                    sales_per_share,\
\
                "Dividende/Aktie":\
                    dividend_per_share,\
\
                "Aussch\'fcttungsquote 1 (%)":\
                    payout_ratio_1,\
\
                "Aussch\'fcttungsquote 2 (%)":\
                    payout_ratio_2,\
\
                "FCF-Marge (%)":\
                    fcf_margin,\
\
                "ROE (%)":\
                    roe,\
\
                "Debt/Equity (%)":\
                    debt_to_equity,\
\
                "Netto-Schulden (Mrd.)":\
                    net_debt / 1e9\
                    if pd.notna(net_debt)\
                    else np.nan,\
\
                "KGV":\
                    kgv,\
\
                "KCV":\
                    kcv,\
\
                "KBV":\
                    kbv,\
\
                "KUV":\
                    kuv,\
\
                "Liquidit\'e4t 1 (%)":\
                    liq_1,\
\
                "Liquidit\'e4t 2 (%)":\
                    liq_2,\
\
                "Liquidit\'e4t 3 (%)":\
                    liq_3\
            \})\
\
\
        df = pd.DataFrame(\
            data_list\
        )\
\
\
        # ====================================================\
        # HISTORISCHE TABELLE\
        # ====================================================\
\
        with st.expander(\
            "\uc0\u55357 \u56522  Historische Kennzahlen",\
            expanded=False\
        ):\
\
            st.dataframe(\
                df.style.format(\
                    precision=2,\
                    na_rep="-"\
                ),\
                use_container_width=True\
            )\
\
\
        # ====================================================\
        # HISTORISCHE BEWERTUNG\
        # ====================================================\
\
        st.subheader(\
            "\uc0\u55357 \u56590  Historische Bewertung"\
        )\
\
        avg_kgv = df["KGV"].replace(\
            [np.inf, -np.inf],\
            np.nan\
        ).mean()\
\
        avg_kcv = df["KCV"].replace(\
            [np.inf, -np.inf],\
            np.nan\
        ).mean()\
\
        avg_kbv = df["KBV"].replace(\
            [np.inf, -np.inf],\
            np.nan\
        ).mean()\
\
        avg_kuv = df["KUV"].replace(\
            [np.inf, -np.inf],\
            np.nan\
        ).mean()\
\
\
        col1, col2, col3, col4 = st.columns(4)\
\
        with col1:\
            st.metric(\
                "\'d8 KGV",\
                format_number(avg_kgv)\
            )\
\
        with col2:\
            st.metric(\
                "\'d8 KCV",\
                format_number(avg_kcv)\
            )\
\
        with col3:\
            st.metric(\
                "\'d8 KBV",\
                format_number(avg_kbv)\
            )\
\
        with col4:\
            st.metric(\
                "\'d8 KUV",\
                format_number(avg_kuv)\
            )\
\
\
        # ====================================================\
        # AKTUELLE MULTIPLES\
        # ====================================================\
\
        latest = df.iloc[0]\
\
        current_eps = latest["EPS"]\
        current_bvps = latest["Buchwert/Aktie"]\
        current_fcf_per_share = latest["FCF/Aktie"]\
        current_sales_per_share = latest["Umsatz/Aktie"]\
\
\
        current_kgv = calculate_current_multiple(\
            current_price,\
            current_eps\
        )\
\
        current_kcv = calculate_current_multiple(\
            current_price,\
            current_fcf_per_share\
        )\
\
        current_kbv = calculate_current_multiple(\
            current_price,\
            current_bvps\
        )\
\
        current_kuv = calculate_current_multiple(\
            current_price,\
            current_sales_per_share\
        )\
\
\
        valuation_rows = []\
\
        for name, current, average in [\
\
            ("KGV", current_kgv, avg_kgv),\
            ("KCV", current_kcv, avg_kcv),\
            ("KBV", current_kbv, avg_kbv),\
            ("KUV", current_kuv, avg_kuv)\
\
        ]:\
\
            if (\
                pd.notna(current)\
                and pd.notna(average)\
                and average > 0\
            ):\
\
                difference = (\
                    (average - current)\
                    / average\
                ) * 100\
\
            else:\
\
                difference = np.nan\
\
\
            valuation_rows.append(\{\
\
                "Kennzahl": name,\
                "Aktuell": current,\
                "\'d8 5 Jahre": average,\
                "Abweichung (%)": difference\
            \})\
\
\
        valuation_df = pd.DataFrame(\
            valuation_rows\
        )\
\
\
        st.dataframe(\
            valuation_df.style.format(\
                precision=2,\
                na_rep="-"\
            ),\
            use_container_width=True\
        )\
\
\
        # ====================================================\
        # DCF\
        # ====================================================\
\
        st.subheader(\
            "\uc0\u55357 \u56496  DCF-Bewertung"\
        )\
\
        st.write(\
            "Der DCF verwendet nach M\'f6glichkeit den aktuellen "\
            "TTM-Free-Cashflow. Dieser wird \'fcber mehrere Jahre "\
            "hochgerechnet und anschlie\'dfend auf den heutigen "\
            "Wert abgezinst."\
        )\
\
\
        # ----------------------------------------------------\
        # TTM FCF\
        # ----------------------------------------------------\
\
        ttm_fcf = get_latest_ttm_value(\
            ttm_cashflow,\
            [\
                "Free Cash Flow"\
            ]\
        )\
\
\
        # Fallback: historisch j\'fcngster FCF\
        if pd.isna(ttm_fcf):\
\
            ttm_fcf = latest[\
                "Free Cashflow (Mrd.)"\
            ] * 1e9\
\
\
        # ----------------------------------------------------\
        # TTM AKTIEN\
        # ----------------------------------------------------\
\
        try:\
\
            shares_now = info.get(\
                "sharesOutstanding",\
                np.nan\
            )\
\
            shares_now = clean_number(\
                shares_now\
            )\
\
        except Exception:\
\
            shares_now = np.nan\
\
\
        if pd.isna(shares_now):\
\
            shares_now = get_value(\
                balance_sheet,\
                [\
                    "Ordinary Shares Number"\
                ],\
                balance_sheet.columns[0]\
            )\
\
\
        # ----------------------------------------------------\
        # NETTO-SCHULDEN AKTUELL\
        # ----------------------------------------------------\
\
        current_cash = get_value(\
            balance_sheet,\
            [\
                "Cash And Cash Equivalents",\
                "Cash Cash Equivalents And Short Term Investments"\
            ],\
            balance_sheet.columns[0]\
        )\
\
        current_debt = get_value(\
            balance_sheet,\
            [\
                "Total Debt",\
                "Total Debt And Capital Lease Obligation"\
            ],\
            balance_sheet.columns[0]\
        )\
\
\
        if (\
            pd.notna(current_cash)\
            and pd.notna(current_debt)\
        ):\
\
            current_net_debt = (\
                current_debt - current_cash\
            )\
\
        else:\
\
            current_net_debt = 0\
\
\
        # ----------------------------------------------------\
        # DCF BERECHNUNG\
        # ----------------------------------------------------\
\
        dcf_value = np.nan\
        dcf_value_per_share = np.nan\
\
        if (\
            pd.notna(ttm_fcf)\
            and ttm_fcf > 0\
            and wacc > terminal_growth\
        ):\
\
            forecast_fcfs = []\
\
            base_fcf = ttm_fcf\
\
            for year_number in range(\
                1,\
                forecast_years + 1\
            ):\
\
                future_fcf = (\
                    base_fcf\
                    * (\
                        1 + growth_rate / 100\
                    ) ** year_number\
                )\
\
                forecast_fcfs.append(\
                    future_fcf\
                )\
\
\
            # Barwert der Forecast-FCFs\
            present_value_fcfs = 0\
\
            for year_number, future_fcf in enumerate(\
                forecast_fcfs,\
                start=1\
            ):\
\
                pv = (\
                    future_fcf\
                    / (\
                        1 + wacc / 100\
                    ) ** year_number\
                )\
\
                present_value_fcfs += pv\
\
\
            # Terminal Value\
            final_fcf = forecast_fcfs[-1]\
\
            terminal_value = (\
                final_fcf\
                * (\
                    1\
                    + terminal_growth / 100\
                )\
            ) / (\
                wacc / 100\
                - terminal_growth / 100\
            )\
\
\
            terminal_pv = (\
                terminal_value\
                / (\
                    1 + wacc / 100\
                ) ** forecast_years\
            )\
\
\
            # Enterprise Value\
            enterprise_value = (\
                present_value_fcfs\
                + terminal_pv\
            )\
\
\
            # Equity Value\
            equity_value = (\
                enterprise_value\
                - current_net_debt\
            )\
\
\
            if (\
                pd.notna(shares_now)\
                and shares_now > 0\
            ):\
\
                dcf_value_per_share = (\
                    equity_value\
                    / shares_now\
                )\
\
                dcf_value = (\
                    equity_value\
                )\
\
\
        # ----------------------------------------------------\
        # DCF AUSGABE\
        # ----------------------------------------------------\
\
        if pd.notna(\
            dcf_value_per_share\
        ):\
\
            dcf_upside = (\
                (\
                    dcf_value_per_share\
                    - current_price\
                )\
                / current_price\
            ) * 100\
\
\
            dcf_target_with_margin = (\
                dcf_value_per_share\
                * (\
                    1\
                    - margin_of_safety / 100\
                )\
            )\
\
\
            col1, col2, col3 = st.columns(3)\
\
            with col1:\
\
                st.metric(\
                    "DCF fairer Wert",\
                    f"\{dcf_value_per_share:.2f\} "\
                    f"\{currency\}"\
                )\
\
            with col2:\
\
                st.metric(\
                    "DCF Upside/Downside",\
                    f"\{dcf_upside:+.1f\}%"\
                )\
\
            with col3:\
\
                st.metric(\
                    "Fairer Wert mit Sicherheitsmarge",\
                    f"\{dcf_target_with_margin:.2f\} "\
                    f"\{currency\}"\
                )\
\
\
            st.write(\
                f"**TTM-Free-Cashflow:** "\
                f"\{ttm_fcf / 1e9:.2f\} Mrd. \{currency\}"\
            )\
\
            st.write(\
                f"**FCF-Wachstum:** "\
                f"\{growth_rate:.1f\}% p.a."\
            )\
\
            st.write(\
                f"**WACC:** "\
                f"\{wacc:.2f\}%"\
            )\
\
            st.write(\
                f"**Terminal Growth:** "\
                f"\{terminal_growth:.2f\}%"\
            )\
\
\
            if dcf_upside >= 30:\
\
                st.success(\
                    "Der DCF signalisiert eine deutliche "\
                    "Unterbewertung."\
                )\
\
            elif dcf_upside >= 10:\
\
                st.success(\
                    "Der DCF signalisiert eine moderate "\
                    "Unterbewertung."\
                )\
\
            elif dcf_upside >= -10:\
\
                st.info(\
                    "Der DCF sieht die Aktie ungef\'e4hr "\
                    "fair bewertet."\
                )\
\
            elif dcf_upside >= -25:\
\
                st.warning(\
                    "Der DCF signalisiert eine moderate "\
                    "\'dcberbewertung."\
                )\
\
            else:\
\
                st.error(\
                    "Der DCF signalisiert eine deutliche "\
                    "\'dcberbewertung."\
                )\
\
        else:\
\
            st.warning(\
                "Der DCF konnte nicht berechnet werden. "\
                "M\'f6gliche Gr\'fcnde sind ein negativer/fehlender "\
                "FCF oder ungeeignete WACC-/Terminal-Growth-"\
                "Annahmen."\
            )\
\
\
        # ====================================================\
        # BRANCHENVERGLEICH\
        # ====================================================\
\
        st.subheader(\
            "\uc0\u55356 \u57325  Branchenvergleich"\
        )\
\
        peer_data = []\
\
        try:\
\
            industry_key = info.get(\
                "industryKey"\
            )\
\
            if industry_key:\
\
                industry_obj = yf.Industry(\
                    industry_key\
                )\
\
                top_companies = (\
                    industry_obj.top_companies\
                )\
\
                if (\
                    top_companies is not None\
                    and not top_companies.empty\
                ):\
\
                    peer_symbols = []\
\
                    for symbol in top_companies.index:\
\
                        symbol = str(\
                            symbol\
                        ).upper()\
\
                        if symbol != ticker_symbol:\
\
                            peer_symbols.append(\
                                symbol\
                            )\
\
                        if len(peer_symbols) >= peer_count:\
\
                            break\
\
\
                    # Aktuelle Aktie ebenfalls aufnehmen\
                    comparison_symbols = [\
                        ticker_symbol\
                    ] + peer_symbols\
\
\
                    for symbol in comparison_symbols:\
\
                        try:\
\
                            peer = yf.Ticker(\
                                symbol\
                            )\
\
                            peer_info = peer.info\
\
                            peer_price_data = (\
                                peer.history(\
                                    period="5d",\
                                    auto_adjust=False\
                                )\
                            )\
\
                            if (\
                                peer_price_data.empty\
                            ):\
                                continue\
\
                            peer_price = float(\
                                peer_price_data[\
                                    "Close"\
                                ].dropna().iloc[-1]\
                            )\
\
\
                            peer_eps = clean_number(\
                                peer_info.get(\
                                    "trailingEps"\
                                )\
                            )\
\
                            peer_revenue = clean_number(\
                                peer_info.get(\
                                    "totalRevenue"\
                                )\
                            )\
\
                            peer_market_cap = clean_number(\
                                peer_info.get(\
                                    "marketCap"\
                                )\
                            )\
\
                            peer_book_value = clean_number(\
                                peer_info.get(\
                                    "bookValue"\
                                )\
                            )\
\
                            peer_fcf = clean_number(\
                                peer_info.get(\
                                    "freeCashflow"\
                                )\
                            )\
\
\
                            peer_shares = clean_number(\
                                peer_info.get(\
                                    "sharesOutstanding"\
                                )\
                            )\
\
\
                            peer_kgv = (\
                                peer_price / peer_eps\
                                if (\
                                    pd.notna(peer_eps)\
                                    and peer_eps > 0\
                                )\
                                else np.nan\
                            )\
\
\
                            peer_kbv = (\
                                peer_price / peer_book_value\
                                if (\
                                    pd.notna(peer_book_value)\
                                    and peer_book_value > 0\
                                )\
                                else np.nan\
                            )\
\
\
                            if (\
                                pd.notna(peer_fcf)\
                                and pd.notna(peer_shares)\
                                and peer_shares > 0\
                            ):\
\
                                peer_fcf_ps = (\
                                    peer_fcf\
                                    / peer_shares\
                                )\
\
                                peer_kcv = (\
                                    peer_price\
                                    / peer_fcf_ps\
                                    if peer_fcf_ps > 0\
                                    else np.nan\
                                )\
\
                            else:\
\
                                peer_kcv = np.nan\
\
\
                            if (\
                                pd.notna(peer_revenue)\
                                and pd.notna(peer_shares)\
                                and peer_shares > 0\
                            ):\
\
                                peer_sales_ps = (\
                                    peer_revenue\
                                    / peer_shares\
                                )\
\
                                peer_kuv = (\
                                    peer_price\
                                    / peer_sales_ps\
                                    if peer_sales_ps > 0\
                                    else np.nan\
                                )\
\
                            else:\
\
                                peer_kuv = np.nan\
\
\
                            peer_data.append(\{\
\
                                "Ticker":\
                                    symbol,\
\
                                "KGV":\
                                    peer_kgv,\
\
                                "KCV":\
                                    peer_kcv,\
\
                                "KBV":\
                                    peer_kbv,\
\
                                "KUV":\
                                    peer_kuv\
                            \})\
\
\
                        except Exception:\
                            continue\
\
\
        except Exception:\
            pass\
\
\
        if peer_data:\
\
            peers_df = pd.DataFrame(\
                peer_data\
            )\
\
\
            # Branchenmittelwerte\
            industry_avg_kgv = peers_df[\
                "KGV"\
            ].replace(\
                [np.inf, -np.inf],\
                np.nan\
            ).mean()\
\
            industry_avg_kcv = peers_df[\
                "KCV"\
            ].replace(\
                [np.inf, -np.inf],\
                np.nan\
            ).mean()\
\
            industry_avg_kbv = peers_df[\
                "KBV"\
            ].replace(\
                [np.inf, -np.inf],\
                np.nan\
            ).mean()\
\
            industry_avg_kuv = peers_df[\
                "KUV"\
            ].replace(\
                [np.inf, -np.inf],\
                np.nan\
            ).mean()\
\
\
            st.write(\
                f"**Branche:** \{industry\}"\
            )\
\
\
            st.dataframe(\
                peers_df.style.format(\
                    precision=2,\
                    na_rep="-"\
                ),\
                use_container_width=True\
            )\
\
\
            industry_comparison = pd.DataFrame(\{\
\
                "Kennzahl": [\
                    "KGV",\
                    "KCV",\
                    "KBV",\
                    "KUV"\
                ],\
\
                "Aktie": [\
                    current_kgv,\
                    current_kcv,\
                    current_kbv,\
                    current_kuv\
                ],\
\
                "Branchenvergleich": [\
                    industry_avg_kgv,\
                    industry_avg_kcv,\
                    industry_avg_kbv,\
                    industry_avg_kuv\
                ]\
            \})\
\
\
            st.dataframe(\
                industry_comparison.style.format(\
                    precision=2,\
                    na_rep="-"\
                ),\
                use_container_width=True\
            )\
\
\
        else:\
\
            industry_avg_kgv = np.nan\
            industry_avg_kcv = np.nan\
            industry_avg_kbv = np.nan\
            industry_avg_kuv = np.nan\
\
            st.info(\
                "F\'fcr diese Aktie konnten keine geeigneten "\
                "Branchen-Peers geladen werden."\
            )\
\
\
        # ====================================================\
        # FUNDAMENTALES SCORING \'96 100 PUNKTE\
        # ====================================================\
\
        st.subheader(\
            "\uc0\u55356 \u57286  Fundamentaler Gesamtscore \'96 100 Punkte"\
        )\
\
\
        # ----------------------------------------------------\
        # 1. UMSATZWACHSTUM \'96 10\
        # ----------------------------------------------------\
\
        score_revenue = growth_score(\
            df["Umsatz (Mrd.)"],\
            10\
        )\
\
\
        # ----------------------------------------------------\
        # 2. EPS-WACHSTUM \'96 10\
        # ----------------------------------------------------\
\
        score_eps = growth_score(\
            df["EPS"],\
            10\
        )\
\
\
        # ----------------------------------------------------\
        # 3. FCF-WACHSTUM \'96 10\
        # ----------------------------------------------------\
\
        score_fcf = growth_score(\
            df["Free Cashflow (Mrd.)"],\
            10\
        )\
\
\
        # ----------------------------------------------------\
        # 4. FCF-MARGE \'96 10\
        # ----------------------------------------------------\
\
        current_fcf_margin = latest[\
            "FCF-Marge (%)"\
        ]\
\
\
        if pd.notna(\
            current_fcf_margin\
        ):\
\
            if current_fcf_margin >= 25:\
                score_fcf_margin = 10\
\
            elif current_fcf_margin >= 20:\
                score_fcf_margin = 9\
\
            elif current_fcf_margin >= 15:\
                score_fcf_margin = 8\
\
            elif current_fcf_margin >= 10:\
                score_fcf_margin = 6\
\
            elif current_fcf_margin >= 5:\
                score_fcf_margin = 4\
\
            elif current_fcf_margin >= 0:\
                score_fcf_margin = 2\
\
            else:\
                score_fcf_margin = 0\
\
        else:\
\
            score_fcf_margin = 0\
\
\
        # ----------------------------------------------------\
        # 5. ROE \'96 10\
        # ----------------------------------------------------\
\
        current_roe = latest[\
            "ROE (%)"\
        ]\
\
\
        if pd.notna(current_roe):\
\
            if current_roe >= 25:\
                score_roe = 10\
\
            elif current_roe >= 20:\
                score_roe = 9\
\
            elif current_roe >= 15:\
                score_roe = 8\
\
            elif current_roe >= 10:\
                score_roe = 6\
\
            elif current_roe >= 5:\
                score_roe = 4\
\
            elif current_roe >= 0:\
                score_roe = 2\
\
            else:\
                score_roe = 0\
\
        else:\
\
            score_roe = 0\
\
\
        # ----------------------------------------------------\
        # 6. VERSCHULDUNG \'96 10\
        # ----------------------------------------------------\
\
        current_de = latest[\
            "Debt/Equity (%)"\
        ]\
\
\
        if pd.notna(current_de):\
\
            if current_de <= 20:\
                score_debt = 10\
\
            elif current_de <= 50:\
                score_debt = 9\
\
            elif current_de <= 100:\
                score_debt = 7\
\
            elif current_de <= 150:\
                score_debt = 5\
\
            elif current_de <= 250:\
                score_debt = 3\
\
            else:\
                score_debt = 0\
\
        else:\
\
            score_debt = 0\
\
\
        # ----------------------------------------------------\
        # 7. LIQUIDIT\'c4T \'96 5\
        # ----------------------------------------------------\
\
        current_liq = latest[\
            "Liquidit\'e4t 3 (%)"\
        ]\
\
\
        if pd.notna(current_liq):\
\
            if current_liq >= 200:\
                score_liquidity = 5\
\
            elif current_liq >= 150:\
                score_liquidity = 4\
\
            elif current_liq >= 100:\
                score_liquidity = 3\
\
            elif current_liq >= 75:\
                score_liquidity = 1\
\
            else:\
                score_liquidity = 0\
\
        else:\
\
            score_liquidity = 0\
\
\
        # ----------------------------------------------------\
        # 8. DIVIDENDEN \'96 5\
        # ----------------------------------------------------\
\
        score_dividend = 0\
\
        payout_values = (\
            df[\
                "Aussch\'fcttungsquote 1 (%)"\
            ]\
            .replace(\
                [np.inf, -np.inf],\
                np.nan\
            )\
            .dropna()\
        )\
\
\
        if not payout_values.empty:\
\
            latest_payout = (\
                payout_values.iloc[0]\
            )\
\
            if 20 <= latest_payout <= 60:\
\
                score_dividend += 3\
\
            elif 10 <= latest_payout <= 75:\
\
                score_dividend += 2\
\
            elif 0 <= latest_payout <= 100:\
\
                score_dividend += 1\
\
\
        dividend_values = (\
            df[\
                "Dividende/Aktie"\
            ]\
            .replace(\
                [np.inf, -np.inf],\
                np.nan\
            )\
        )\
\
\
        valid_dividends = (\
            dividend_values[\
                dividend_values > 0\
            ]\
        )\
\
\
        if len(valid_dividends) >= 2:\
\
            oldest_dividend = (\
                valid_dividends.iloc[-1]\
            )\
\
            newest_dividend = (\
                valid_dividends.iloc[0]\
            )\
\
            if (\
                oldest_dividend > 0\
                and newest_dividend > oldest_dividend\
            ):\
\
                if (\
                    newest_dividend\
                    >= oldest_dividend * 1.25\
                ):\
\
                    score_dividend += 2\
\
                elif (\
                    newest_dividend\
                    > oldest_dividend\
                ):\
\
                    score_dividend += 1\
\
\
        score_dividend = min(\
            score_dividend,\
            5\
        )\
\
\
        # ----------------------------------------------------\
        # 9. HISTORISCHE BEWERTUNG \'96 10\
        # ----------------------------------------------------\
\
        score_historical = 0\
\
        score_historical += valuation_score(\
            current_kgv,\
            avg_kgv,\
            2.5\
        )\
\
        score_historical += valuation_score(\
            current_kcv,\
            avg_kcv,\
            2.5\
        )\
\
        score_historical += valuation_score(\
            current_kbv,\
            avg_kbv,\
            2.5\
        )\
\
        score_historical += valuation_score(\
            current_kuv,\
            avg_kuv,\
            2.5\
        )\
\
\
        # ----------------------------------------------------\
        # 10. BRANCHENBEWERTUNG \'96 10\
        # ----------------------------------------------------\
\
        score_industry = 0\
\
        score_industry += valuation_score(\
            current_kgv,\
            industry_avg_kgv,\
            2.5\
        )\
\
        score_industry += valuation_score(\
            current_kcv,\
            industry_avg_kcv,\
            2.5\
        )\
\
        score_industry += valuation_score(\
            current_kbv,\
            industry_avg_kbv,\
            2.5\
        )\
\
        score_industry += valuation_score(\
            current_kuv,\
            industry_avg_kuv,\
            2.5\
        )\
\
\
        # ----------------------------------------------------\
        # 11. DCF \'96 10\
        # ----------------------------------------------------\
\
        score_dcf = 0\
\
        if pd.notna(\
            dcf_value_per_share\
        ):\
\
            dcf_discount = (\
                (\
                    dcf_value_per_share\
                    - current_price\
                )\
                / current_price\
            ) * 100\
\
\
            if dcf_discount >= 30:\
\
                score_dcf = 10\
\
            elif dcf_discount >= 20:\
\
                score_dcf = 9\
\
            elif dcf_discount >= 10:\
\
                score_dcf = 8\
\
            elif dcf_discount >= 0:\
\
                score_dcf = 7\
\
            elif dcf_discount >= -10:\
\
                score_dcf = 5\
\
            elif dcf_discount >= -20:\
\
                score_dcf = 3\
\
            else:\
\
                score_dcf = 0\
\
\
        # ====================================================\
        # GESAMTSCORE\
        # ====================================================\
\
        total_score = (\
            score_revenue\
            + score_eps\
            + score_fcf\
            + score_fcf_margin\
            + score_roe\
            + score_debt\
            + score_liquidity\
            + score_dividend\
            + score_historical\
            + score_industry\
            + score_dcf\
        )\
\
\
        total_score = max(\
            0,\
            min(\
                100,\
                total_score\
            )\
        )\
\
\
        # ====================================================\
        # RATING\
        # ====================================================\
\
        if total_score >= 85:\
\
            rating = "Sehr attraktiv"\
\
        elif total_score >= 70:\
\
            rating = "Attraktiv"\
\
        elif total_score >= 55:\
\
            rating = "Neutral / leicht attraktiv"\
\
        elif total_score >= 40:\
\
            rating = "Eher unattraktiv"\
\
        else:\
\
            rating = "Unattraktiv"\
\
\
        # ====================================================\
        # SCORE ANZEIGE\
        # ====================================================\
\
        st.divider()\
\
        col1, col2 = st.columns(2)\
\
        with col1:\
\
            st.metric(\
                "\uc0\u55356 \u57286  Gesamtscore",\
                f"\{total_score:.1f\} / 100"\
            )\
\
        with col2:\
\
            st.metric(\
                "Einsch\'e4tzung",\
                rating\
            )\
\
\
        # ====================================================\
        # SCORE-TABELLE\
        # ====================================================\
\
        score_df = pd.DataFrame(\{\
\
            "Kriterium": [\
\
                "Umsatzwachstum",\
                "EPS-Wachstum",\
                "FCF-Wachstum",\
                "FCF-Marge",\
                "ROE",\
                "Verschuldung",\
                "Liquidit\'e4t",\
                "Dividendenqualit\'e4t",\
                "Historische Bewertung",\
                "Branchenbewertung",\
                "DCF-Bewertung"\
            ],\
\
            "Punkte": [\
\
                score_revenue,\
                score_eps,\
                score_fcf,\
                score_fcf_margin,\
                score_roe,\
                score_debt,\
                score_liquidity,\
                score_dividend,\
                score_historical,\
                score_industry,\
                score_dcf\
            ],\
\
            "Maximum": [\
\
                10,\
                10,\
                10,\
                10,\
                10,\
                10,\
                5,\
                5,\
                10,\
                10,\
                10\
            ]\
        \})\
\
\
        score_df["Erf\'fcllung"] = (\
            score_df["Punkte"]\
            / score_df["Maximum"]\
            * 100\
        )\
\
\
        st.dataframe(\
            score_df.style.format(\
                \{\
                    "Punkte": "\{:.1f\}",\
                    "Maximum": "\{:.0f\}",\
                    "Erf\'fcllung": "\{:.1f\}%"\
                \}\
            ),\
            use_container_width=True\
        )\
\
\
        # ====================================================\
        # GRAHAM\
        # ====================================================\
\
        st.subheader(\
            "\uc0\u55357 \u56528  Graham-Bewertung"\
        )\
\
        avg_eps = df[\
            "EPS"\
        ].mean()\
\
        avg_bvps = df[\
            "Buchwert/Aktie"\
        ].mean()\
\
\
        if (\
            pd.notna(avg_eps)\
            and pd.notna(avg_bvps)\
            and avg_eps > 0\
            and avg_bvps > 0\
        ):\
\
            graham_value = np.sqrt(\
                22.5\
                * avg_eps\
                * avg_bvps\
            )\
\
            graham_discount = (\
                (\
                    graham_value\
                    - current_price\
                )\
                / current_price\
            ) * 100\
\
\
            col1, col2, col3 = st.columns(3)\
\
            with col1:\
\
                st.metric(\
                    "Graham-Wert",\
                    f"\{graham_value:.2f\} "\
                    f"\{currency\}"\
                )\
\
            with col2:\
\
                st.metric(\
                    "Aktueller Kurs",\
                    f"\{current_price:.2f\} "\
                    f"\{currency\}"\
                )\
\
            with col3:\
\
                st.metric(\
                    "Abweichung",\
                    f"\{graham_discount:+.1f\}%"\
                )\
\
        else:\
\
            st.info(\
                "Der Graham-Wert konnte nicht berechnet werden."\
            )\
\
\
        # ====================================================\
        # DCF SENSITIVIT\'c4TSANALYSE\
        # ====================================================\
\
        if pd.notna(\
            ttm_fcf\
        ) and ttm_fcf > 0:\
\
            st.subheader(\
                "\uc0\u55356 \u57263  DCF-Sensitivit\'e4tsanalyse"\
            )\
\
            st.write(\
                "Der faire Wert wird f\'fcr verschiedene "\
                "WACC- und Wachstumsannahmen dargestellt."\
            )\
\
\
            wacc_values = [\
                max(5.0, wacc - 1.0),\
                wacc,\
                wacc + 1.0\
            ]\
\
            growth_values = [\
                max(-5.0, growth_rate - 2.0),\
                growth_rate,\
                growth_rate + 2.0\
            ]\
\
\
            sensitivity = []\
\
\
            for growth in growth_values:\
\
                row = []\
\
                for discount_rate in wacc_values:\
\
                    if (\
                        discount_rate\
                        <= terminal_growth\
                    ):\
\
                        row.append(\
                            np.nan\
                        )\
\
                        continue\
\
\
                    forecast = []\
\
                    for year_number in range(\
                        1,\
                        forecast_years + 1\
                    ):\
\
                        future_fcf = (\
                            ttm_fcf\
                            * (\
                                1\
                                + growth / 100\
                            ) ** year_number\
                        )\
\
                        forecast.append(\
                            future_fcf\
                        )\
\
\
                    pv_fcfs = sum(\
\
                        fcf\
                        / (\
                            1\
                            + discount_rate / 100\
                        ) ** year_number\
\
                        for year_number, fcf\
                        in enumerate(\
                            forecast,\
                            start=1\
                        )\
                    )\
\
\
                    terminal_fcf = (\
                        forecast[-1]\
                        * (\
                            1\
                            + terminal_growth / 100\
                        )\
                    )\
\
\
                    terminal_value = (\
                        terminal_fcf\
                        / (\
                            discount_rate / 100\
                            - terminal_growth / 100\
                        )\
                    )\
\
\
                    terminal_pv = (\
                        terminal_value\
                        / (\
                            1\
                            + discount_rate / 100\
                        ) ** forecast_years\
                    )\
\
\
                    enterprise_value = (\
                        pv_fcfs\
                        + terminal_pv\
                    )\
\
\
                    equity_value = (\
                        enterprise_value\
                        - current_net_debt\
                    )\
\
\
                    if (\
                        pd.notna(shares_now)\
                        and shares_now > 0\
                    ):\
\
                        fair_value = (\
                            equity_value\
                            / shares_now\
                        )\
\
                    else:\
\
                        fair_value = np.nan\
\
\
                    row.append(\
                        fair_value\
                    )\
\
\
                sensitivity.append(\
                    row\
                )\
\
\
            sensitivity_df = pd.DataFrame(\
\
                sensitivity,\
\
                index=[\
                    f"\{g:.1f\}% Wachstum"\
                    for g in growth_values\
                ],\
\
                columns=[\
                    f"\{w:.2f\}% WACC"\
                    for w in wacc_values\
                ]\
            )\
\
\
            st.dataframe(\
                sensitivity_df.style.format(\
                    "\{:.2f\}"\
                ),\
                use_container_width=True\
            )\
\
\
        # ====================================================\
        # ABSCHLIESSENDE EINSCH\'c4TZUNG\
        # ====================================================\
\
        st.subheader(\
            "\uc0\u55358 \u56813  Zusammenfassung"\
        )\
\
\
        summary_points = []\
\
\
        if total_score >= 70:\
\
            summary_points.append(\
                "Das fundamentale Gesamtbild ist positiv."\
            )\
\
        elif total_score >= 55:\
\
            summary_points.append(\
                "Das fundamentale Gesamtbild ist gemischt."\
            )\
\
        else:\
\
            summary_points.append(\
                "Das fundamentale Gesamtbild ist eher schwach."\
            )\
\
\
        if (\
            pd.notna(dcf_value_per_share)\
            and dcf_value_per_share > current_price\
        ):\
\
            summary_points.append(\
                "Der DCF liegt \'fcber dem aktuellen Aktienkurs."\
            )\
\
        elif pd.notna(\
            dcf_value_per_share\
        ):\
\
            summary_points.append(\
                "Der DCF liegt unter dem aktuellen Aktienkurs."\
            )\
\
\
        if valid_dividends.size > 0:\
\
            summary_points.append(\
                "Es wurden historische Dividendenzahlungen "\
                "ber\'fccksichtigt."\
            )\
\
\
        for point in summary_points:\
\
            st.write(\
                f"\'95 \{point\}"\
            )\
\
\
        st.caption(\
            "Hinweis: Dieses Tool ist ein quantitatives "\
            "Bewertungsmodell und keine Anlageberatung. "\
            "Insbesondere DCF-Ergebnisse reagieren stark "\
            "auf Wachstums-, WACC- und Terminal-Growth-"\
            "Annahmen."\
        )\
\
\
    except Exception as e:\
\
        st.error(\
            "Fehler beim Laden oder Verarbeiten der Daten."\
        )\
\
        st.exception(e)\
}