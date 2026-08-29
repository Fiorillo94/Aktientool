import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import re


# ============================================================
# SEITENKONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Mein Aktien-Bewertungs-Tool",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Mein personalisiertes Aktien-Bewertungs-Tool")
st.caption(
    "Fundamentalanalyse · Graham · DCF · historische Bewertung · Dividenden"
)


# ============================================================
# HILFSFUNKTIONEN
# ============================================================

def safe_float(value):
    """Versucht einen Wert sicher in float umzuwandeln."""
    try:
        if value is None or pd.isna(value):
            return np.nan
        return float(value)
    except Exception:
        return np.nan


def get_value(df, possible_rows, column, default=np.nan):
    """
    Sucht einen Wert anhand mehrerer möglicher Zeilennamen.
    Das ist wichtig, weil Yahoo Finance die Bezeichnungen
    einzelner Finanzdaten gelegentlich verändert.
    """

    if df is None or df.empty:
        return default

    for row in possible_rows:

        try:

            if row in df.index and column in df.columns:

                value = df.loc[row, column]

                if pd.notna(value):
                    return float(value)

        except Exception:
            pass

    return default


def normalize_input(user_input):
    """
    Wandelt Firmenname, WKN, ISIN oder Ticker
    in einen Yahoo-Finance-Ticker um.
    """

    value = user_input.strip().upper()

    # --------------------------------------------------------
    # Bekannte deutsche Aktien
    # --------------------------------------------------------

    company_map = {

        "INNOTEC TSS": "TSS.DE",
        "INNOTEC": "TSS.DE",
        "TSS": "TSS.DE",

        "SAP": "SAP.DE",
        "SIEMENS": "SIE.DE",
        "ALLIANZ": "ALV.DE",
        "BMW": "BMW.DE",
        "MERCEDES": "MBG.DE",
        "MERCEDES-BENZ": "MBG.DE",
        "MERCEDES BENZ": "MBG.DE",
        "DEUTSCHE TELEKOM": "DTE.DE",
        "TELEKOM": "DTE.DE",
        "INFINEON": "IFX.DE",
        "BASF": "BAS.DE",
        "ADIDAS": "ADS.DE",
        "VOLKSWAGEN": "VOW3.DE",
        "VW": "VOW3.DE",
        "DEUTSCHE BANK": "DBK.DE",
        "COMMERZBANK": "CBK.DE",
        "MUNICH RE": "MUV2.DE",
        "MÜNCHENER RÜCK": "MUV2.DE",
        "DEUTSCHE POST": "DHL.DE",
        "HEIDELBERG MATERIALS": "HEI.DE",
        "CONTINENTAL": "CON.DE",
        "HENKEL": "HEN3.DE",
        "RHEINMETALL": "RHM.DE"
    }

    if value in company_map:
        return company_map[value]


    # --------------------------------------------------------
    # ISIN
    # --------------------------------------------------------

    isin_map = {

        "DE0005405104": "TSS.DE",
        "DE0007164600": "SAP.DE",
        "DE0007236101": "SIE.DE",
        "DE0008404005": "ALV.DE",
        "DE0005190003": "BMW.DE",
        "DE0007100000": "MBG.DE",
        "DE0005557508": "DTE.DE",
        "DE0006231004": "IFX.DE",
        "DE000BASF111": "BAS.DE",
        "DE000A1EWWW0": "ADS.DE",
        "DE0007664039": "VOW3.DE",
        "DE0005140008": "DBK.DE",
        "DE000CBK1001": "CBK.DE",
        "DE0008430026": "MUV2.DE",
        "DE0005552004": "DHL.DE"
    }

    if value in isin_map:
        return isin_map[value]


    # --------------------------------------------------------
    # WKN
    # --------------------------------------------------------

    wkn_map = {

        "540510": "TSS.DE",
        "716460": "SAP.DE",
        "723610": "SIE.DE",
        "840400": "ALV.DE",
        "519000": "BMW.DE",
        "710000": "MBG.DE",
        "555750": "DTE.DE",
        "623100": "IFX.DE",
        "BASF11": "BAS.DE",
        "A1EWWW": "ADS.DE",
        "766403": "VOW3.DE",
        "514000": "DBK.DE",
        "CBK100": "CBK.DE",
        "843002": "MUV2.DE",
        "555200": "DHL.DE"
    }

    if value in wkn_map:
        return wkn_map[value]


    # --------------------------------------------------------
    # Bereits vollständiger Yahoo-Ticker
    # --------------------------------------------------------

    if "." in value:
        return value


    # --------------------------------------------------------
    # Deutscher Ticker ohne Börsenkürzel
    # --------------------------------------------------------

    return f"{value}.DE"


# ============================================================
# HISTORISCHE JAHRESENDKURSE
# ============================================================

def get_year_end_price(history, year):

    try:

        if history is None or history.empty:
            return np.nan


        hist = history.copy()


        # ----------------------------------------------------
        # MultiIndex von yfinance entfernen
        # ----------------------------------------------------

        if isinstance(
            hist.columns,
            pd.MultiIndex
        ):

            hist.columns = (
                hist.columns
                .get_level_values(0)
            )


        if "Close" not in hist.columns:
            return np.nan


        # ----------------------------------------------------
        # Daten des jeweiligen Jahres
        # ----------------------------------------------------

        year_data = hist[
            hist.index.year == year
        ]


        if year_data.empty:
            return np.nan


        close_prices = (
            year_data["Close"]
            .dropna()
        )


        if close_prices.empty:
            return np.nan


        # Letzter verfügbarer Börsenkurs
        # des Jahres
        return float(
            close_prices.iloc[-1]
        )


    except Exception:

        return np.nan


# ============================================================
# MULTIPLE
# ============================================================

def calculate_multiple(price, value):

    if (
        pd.notna(price)
        and pd.notna(value)
        and value > 0
    ):

        return price / value

    return np.nan


# ============================================================
# GROWTH SCORE
# ============================================================

def growth_score(values, max_points):

    values = (
        pd.Series(values)
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .dropna()
    )


    if len(values) < 2:
        return 0


    newest = values.iloc[0]
    oldest = values.iloc[-1]


    if oldest <= 0:
        return 0


    growth = (
        (newest - oldest)
        / abs(oldest)
    ) * 100


    if growth >= 50:
        return max_points

    elif growth >= 30:
        return max_points * 0.90

    elif growth >= 15:
        return max_points * 0.80

    elif growth >= 5:
        return max_points * 0.70

    elif growth >= 0:
        return max_points * 0.55

    elif growth >= -10:
        return max_points * 0.35

    elif growth >= -25:
        return max_points * 0.15

    return 0


# ============================================================
# VALUATION SCORE
# ============================================================

def valuation_score(
    current_multiple,
    historical_multiple,
    max_points
):

    if (
        pd.isna(current_multiple)
        or pd.isna(historical_multiple)
        or current_multiple <= 0
        or historical_multiple <= 0
    ):

        return 0


    discount = (
        (
            historical_multiple
            - current_multiple
        )
        / historical_multiple
    ) * 100


    if discount >= 30:
        return max_points

    elif discount >= 20:
        return max_points * 0.90

    elif discount >= 10:
        return max_points * 0.80

    elif discount >= 0:
        return max_points * 0.65

    elif discount >= -10:
        return max_points * 0.45

    elif discount >= -20:
        return max_points * 0.20

    return 0


# ============================================================
# YAHOO FINANCE DATEN LADEN
# ============================================================

@st.cache_data(
    ttl=3600,
    show_spinner=False
)
def load_market_data(ticker_symbol):

    share = yf.Ticker(
        ticker_symbol
    )


    # --------------------------------------------------------
    # Historische Kurse
    # EIN Request für sechs Jahre
    # --------------------------------------------------------

    history = yf.download(
        ticker_symbol,
        period="6y",
        interval="1d",
        auto_adjust=False,
        actions=False,
        progress=False,
        threads=False
    )


    # --------------------------------------------------------
    # Finanzdaten
    # --------------------------------------------------------

    financials = share.financials

    balance_sheet = share.balance_sheet

    cashflow = share.cashflow


    # --------------------------------------------------------
    # Dividenden
    # --------------------------------------------------------

    try:

        actions = share.actions

        if (
            actions is not None
            and not actions.empty
            and "Dividends" in actions.columns
        ):

            dividends = actions[
                "Dividends"
            ]

        else:

            dividends = pd.Series(
                dtype=float
            )

    except Exception:

        dividends = pd.Series(
            dtype=float
        )


    return {
        "history": history,
        "financials": financials,
        "balance_sheet": balance_sheet,
        "cashflow": cashflow,
        "dividends": dividends
    }


# ============================================================
# DCF
# ============================================================

def calculate_dcf(
    fcf,
    shares,
    net_debt,
    growth_rate,
    wacc,
    terminal_growth,
    forecast_years
):

    if (
        pd.isna(fcf)
        or fcf <= 0
        or pd.isna(shares)
        or shares <= 0
        or wacc <= terminal_growth
    ):

        return np.nan


    forecast_fcfs = []


    for year in range(
        1,
        forecast_years + 1
    ):

        future_fcf = (
            fcf
            * (
                1
                + growth_rate / 100
            )
            ** year
        )

        forecast_fcfs.append(
            future_fcf
        )


    # --------------------------------------------------------
    # Barwert der prognostizierten FCFs
    # --------------------------------------------------------

    pv_fcfs = sum(

        future_fcf
        / (
            1
            + wacc / 100
        )
        ** year

        for year, future_fcf
        in enumerate(
            forecast_fcfs,
            start=1
        )
    )


    # --------------------------------------------------------
    # Terminal Value
    # --------------------------------------------------------

    terminal_fcf = (
        forecast_fcfs[-1]
        * (
            1
            + terminal_growth / 100
        )
    )


    terminal_value = (
        terminal_fcf
        / (
            wacc / 100
            - terminal_growth / 100
        )
    )


    terminal_pv = (
        terminal_value
        / (
            1
            + wacc / 100
        )
        ** forecast_years
    )


    enterprise_value = (
        pv_fcfs
        + terminal_pv
    )


    equity_value = (
        enterprise_value
        - net_debt
    )


    return (
        equity_value
        / shares
    )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header(
    "⚙️ DCF-Annahmen"
)


forecast_years = st.sidebar.slider(
    "Prognosezeitraum",
    min_value=3,
    max_value=10,
    value=5
)


growth_rate = st.sidebar.slider(
    "FCF-Wachstum (%)",
    min_value=-10.0,
    max_value=30.0,
    value=8.0,
    step=0.5
)


wacc = st.sidebar.slider(
    "WACC (%)",
    min_value=5.0,
    max_value=15.0,
    value=9.0,
    step=0.25
)


terminal_growth = st.sidebar.slider(
    "Terminal Growth (%)",
    min_value=0.0,
    max_value=5.0,
    value=2.5,
    step=0.25
)


margin_of_safety = st.sidebar.slider(
    "Sicherheitsmarge (%)",
    min_value=0,
    max_value=50,
    value=20,
    step=5
)


# ============================================================
# AKTIEN-EINGABE
# ============================================================

user_input = st.text_input(
    "🔎 Aktie suchen – Ticker, Firmenname, WKN oder ISIN",
    value="InnoTec TSS"
)


if user_input:

    ticker_symbol = normalize_input(
        user_input
    )


    st.info(
        f"Erkannter Yahoo-Finance-Ticker: "
        f"**{ticker_symbol}**"
    )


    # ========================================================
    # DATEN LADEN
    # ========================================================

    try:

        with st.spinner(
            "Lade Finanzdaten..."
        ):

            data = load_market_data(
                ticker_symbol
            )


    except Exception as e:

        error_text = str(e).lower()


        if (
            "too many requests"
            in error_text
            or "rate limited"
            in error_text
            or "429"
            in error_text
        ):

            st.error(
                "⚠️ Yahoo Finance hat die Anfrage "
                "vorübergehend wegen zu vieler "
                "Anfragen blockiert."
            )

            st.info(
                "Bitte einige Minuten warten. "
                "Die Anwendung verwendet Caching, "
                "damit zukünftige Analysen weniger "
                "Anfragen verursachen."
            )

        else:

            st.error(
                "⚠️ Fehler beim Laden der Yahoo-Finance-Daten."
            )

            st.exception(e)


        st.stop()


    # ========================================================
    # DATEN AUSLESEN
    # ========================================================

    history = data["history"]

    financials = data["financials"]

    balance_sheet = data["balance_sheet"]

    cashflow = data["cashflow"]

    dividends = data["dividends"]


    # ========================================================
    # KURS PRÜFEN
    # ========================================================

    if history is None or history.empty:

        st.error(
            "⚠️ Kurse konnten von Yahoo Finance "
            "nicht abgerufen werden."
        )

        st.stop()


    if isinstance(
        history.columns,
        pd.MultiIndex
    ):

        history.columns = (
            history.columns
            .get_level_values(0)
        )


    if "Close" not in history.columns:

        st.error(
            "⚠️ Yahoo Finance hat keine "
            "Schlusskurse geliefert."
        )

        st.stop()


    close_prices = (
        history["Close"]
        .dropna()
    )


    if close_prices.empty:

        st.error(
            "⚠️ Keine gültigen Kurse vorhanden."
        )

        st.stop()


    current_price = float(
        close_prices.iloc[-1]
    )


    # ========================================================
    # UNTERNEHMENSINFORMATIONEN
    # ========================================================

    # info wird bewusst erst hier abgefragt
    # und nicht zum grundlegenden Laden benötigt.

    try:

        share = yf.Ticker(
            ticker_symbol
        )

        info = share.info

    except Exception:

        info = {}


    company_name = info.get(
        "longName",
        ticker_symbol
    )


    currency = info.get(
        "currency",
        "EUR"
    )


    exchange = info.get(
        "exchange",
        "-"
    )


    sector = info.get(
        "sector",
        "-"
    )


    industry = info.get(
        "industry",
        "-"
    )


    isin = info.get(
        "isin",
        "-"
    )


    # ========================================================
    # UNTERNEHMENSKOPF
    # ========================================================

    st.subheader(
        f"{company_name} ({ticker_symbol})"
    )


    c1, c2, c3, c4 = st.columns(4)


    with c1:

        st.metric(
            "Aktueller Kurs",
            f"{current_price:.2f} {currency}"
        )


    with c2:

        st.metric(
            "Börsenplatz",
            exchange
        )


    with c3:

        st.metric(
            "Sektor",
            sector
        )


    with c4:

        st.metric(
            "Branche",
            industry
        )


    if isin != "-":

        st.caption(
            f"ISIN: {isin}"
        )


    # ========================================================
    # NEBENWERT-WARNUNG
    # ========================================================

    market_cap = safe_float(
        info.get(
            "marketCap"
        )
    )


    if (
        pd.notna(market_cap)
        and market_cap < 1_000_000_000
    ):

        st.warning(
            "⚠️ Dieser Titel ist ein kleinerer "
            "Nebenwert. Bei solchen Aktien können "
            "Handelsvolumen, Spreads und die "
            "Datenqualität geringer sein."
        )


    # ========================================================
    # HISTORISCHE JAHRE
    # ========================================================

    if financials is None or financials.empty:

        st.error(
            "Yahoo Finance liefert keine "
            "Gewinn- und Verlustrechnung."
        )

        st.stop()


    years = financials.columns[:5]


    data_list = []


    # ========================================================
    # JAHRESSCHLEIFE
    # ========================================================

    for year in years:

        year_number = year.year


        # ----------------------------------------------------
        # GUV
        # ----------------------------------------------------

        sales = get_value(
            financials,
            [
                "Total Revenue",
                "Operating Revenue"
            ],
            year
        )


        net_income = get_value(
            financials,
            [
                "Net Income",
                "Net Income Common Stockholders"
            ],
            year
        )


        # ----------------------------------------------------
        # BILANZ
        # ----------------------------------------------------

        equity = get_value(
            balance_sheet,
            [
                "Stockholders Equity",
                "Common Stock Equity",
                "Total Equity Gross Minority Interest"
            ],
            year
        )


        total_debt = get_value(
            balance_sheet,
            [
                "Total Debt",
                "Total Debt And Capital Lease Obligation"
            ],
            year
        )


        cash = get_value(
            balance_sheet,
            [
                "Cash And Cash Equivalents",
                "Cash Cash Equivalents And Short Term Investments"
            ],
            year
        )


        receivables = get_value(
            balance_sheet,
            [
                "Receivables",
                "Accounts Receivable"
            ],
            year
        )


        current_assets = get_value(
            balance_sheet,
            [
                "Current Assets"
            ],
            year
        )


        current_liabilities = get_value(
            balance_sheet,
            [
                "Current Liabilities"
            ],
            year
        )


        # ----------------------------------------------------
        # CASHFLOW
        # ----------------------------------------------------

        free_cashflow = get_value(
            cashflow,
            [
                "Free Cash Flow"
            ],
            year
        )


        # ----------------------------------------------------
        # FALLBACK FÜR FREE CASHFLOW
        # ----------------------------------------------------

        if pd.isna(
            free_cashflow
        ):

            operating_cf = get_value(
                cashflow,
                [
                    "Operating Cash Flow",
                    "Total Cash From Operating Activities"
                ],
                year
            )


            capex = get_value(
                cashflow,
                [
                    "Capital Expenditure"
                ],
                year
            )


            if (
                pd.notna(operating_cf)
                and pd.notna(capex)
            ):

                free_cashflow = (
                    operating_cf
                    + capex
                )


        # ----------------------------------------------------
        # AKTIENANZAHL
        # ----------------------------------------------------

        shares = get_value(
            financials,
            [
                "Diluted Average Shares",
                "Basic Average Shares"
            ],
            year
        )


        if pd.isna(shares):

            shares = get_value(
                balance_sheet,
                [
                    "Ordinary Shares Number",
                    "Share Issued"
                ],
                year
            )


        # ----------------------------------------------------
        # EPS
        # ----------------------------------------------------

        if (
            pd.notna(net_income)
            and pd.notna(shares)
            and shares != 0
        ):

            eps = (
                net_income
                / shares
            )

        else:

            eps = np.nan


        # ----------------------------------------------------
        # BUCHWERT PRO AKTIE
        # ----------------------------------------------------

        if (
            pd.notna(equity)
            and pd.notna(shares)
            and shares != 0
        ):

            bvps = (
                equity
                / shares
            )

        else:

            bvps = np.nan


        # ----------------------------------------------------
        # FCF PRO AKTIE
        # ----------------------------------------------------

        if (
            pd.notna(free_cashflow)
            and pd.notna(shares)
            and shares != 0
        ):

            fcf_ps = (
                free_cashflow
                / shares
            )

        else:

            fcf_ps = np.nan


        # ----------------------------------------------------
        # UMSATZ PRO AKTIE
        # ----------------------------------------------------

        if (
            pd.notna(sales)
            and pd.notna(shares)
            and shares != 0
        ):

            sales_ps = (
                sales
                / shares
            )

        else:

            sales_ps = np.nan


        # ----------------------------------------------------
        # DIVIDENDE PRO AKTIE
        # ----------------------------------------------------

        if (
            dividends is not None
            and not dividends.empty
        ):

            try:

                year_dividends = (
                    dividends[
                        dividends.index.year
                        == year_number
                    ]
                )

                dividend_ps = (
                    year_dividends.sum()
                )

            except Exception:

                dividend_ps = 0

        else:

            dividend_ps = 0


        # ----------------------------------------------------
        # AUSSCHÜTTUNGSQUOTE 1
        #
        # Dividende je Aktie
        # ------------------
        # Gewinn je Aktie
        # ----------------------------------------------------

        if (
            pd.notna(eps)
            and eps > 0
        ):

            payout_1 = (
                dividend_ps
                / eps
            ) * 100

        else:

            payout_1 = np.nan


        # ----------------------------------------------------
        # AUSSCHÜTTUNGSQUOTE 2
        #
        # Dividende je Aktie
        # ------------------
        # FCF je Aktie
        # ----------------------------------------------------

        if (
            pd.notna(fcf_ps)
            and fcf_ps > 0
        ):

            payout_2 = (
                dividend_ps
                / fcf_ps
            ) * 100

        else:

            payout_2 = np.nan


        # ----------------------------------------------------
        # LIQUIDITÄTSGRADE
        # ----------------------------------------------------

        if (
            pd.notna(current_liabilities)
            and current_liabilities != 0
        ):

            liq_1 = (
                cash
                / current_liabilities
            ) * 100


            liq_2 = (
                (
                    cash
                    + receivables
                )
                / current_liabilities
            ) * 100


            liq_3 = (
                current_assets
                / current_liabilities
            ) * 100

        else:

            liq_1 = np.nan
            liq_2 = np.nan
            liq_3 = np.nan


        # ----------------------------------------------------
        # FCF-MARGE
        # ----------------------------------------------------

        if (
            pd.notna(free_cashflow)
            and pd.notna(sales)
            and sales != 0
        ):

            fcf_margin = (
                free_cashflow
                / sales
            ) * 100

        else:

            fcf_margin = np.nan


        # ----------------------------------------------------
        # ROE
        # ----------------------------------------------------

        if (
            pd.notna(net_income)
            and pd.notna(equity)
            and equity > 0
        ):

            roe = (
                net_income
                / equity
            ) * 100

        else:

            roe = np.nan


        # ----------------------------------------------------
        # DEBT / EQUITY
        # ----------------------------------------------------

        if (
            pd.notna(total_debt)
            and pd.notna(equity)
            and equity > 0
        ):

            debt_equity = (
                total_debt
                / equity
            ) * 100

        else:

            debt_equity = np.nan


        # ----------------------------------------------------
        # HISTORISCHER JAHRESENDKURS
        # ----------------------------------------------------

        year_end_price = (
            get_year_end_price(
                history,
                year_number
            )
        )


        # ----------------------------------------------------
        # HISTORISCHE BEWERTUNG
        # ----------------------------------------------------

        kgv = calculate_multiple(
            year_end_price,
            eps
        )


        kcv = calculate_multiple(
            year_end_price,
            fcf_ps
        )


        kbv = calculate_multiple(
            year_end_price,
            bvps
        )


        kuv = calculate_multiple(
            year_end_price,
            sales_ps
        )


        # ----------------------------------------------------
        # DATENSATZ
        # ----------------------------------------------------

        data_list.append({

            "Jahr":
                year.strftime("%Y"),

            "Jahresendkurs":
                year_end_price,

            "Umsatz (Mrd.)":
                sales / 1e9
                if pd.notna(sales)
                else np.nan,

            "Nettogewinn (Mrd.)":
                net_income / 1e9
                if pd.notna(net_income)
                else np.nan,

            "Eigenkapital (Mrd.)":
                equity / 1e9
                if pd.notna(equity)
                else np.nan,

            "Free Cashflow (Mrd.)":
                free_cashflow / 1e9
                if pd.notna(free_cashflow)
                else np.nan,

            "EPS":
                eps,

            "Buchwert/Aktie":
                bvps,

            "FCF/Aktie":
                fcf_ps,

            "Umsatz/Aktie":
                sales_ps,

            "Dividende/Aktie":
                dividend_ps,

            "Ausschüttungsquote 1 (%)":
                payout_1,

            "Ausschüttungsquote 2 (%)":
                payout_2,

            "FCF-Marge (%)":
                fcf_margin,

            "ROE (%)":
                roe,

            "Debt/Equity (%)":
                debt_equity,

            "KGV":
                kgv,

            "KCV":
                kcv,

            "KBV":
                kbv,

            "KUV":
                kuv,

            "Liquidität 1 (%)":
                liq_1,

            "Liquidität 2 (%)":
                liq_2,

            "Liquidität 3 (%)":
                liq_3
        })


    # ========================================================
    # DATAFRAME
    # ========================================================

    df = pd.DataFrame(
        data_list
    )


    # ========================================================
    # HISTORISCHE TABELLE
    # ========================================================

    st.subheader(
        "📊 Historische Kennzahlen"
    )


    st.dataframe(
        df.style.format(
            precision=2,
            na_rep="-"
        ),
        use_container_width=True
    )


    # ========================================================
    # HISTORISCHE BEWERTUNG
    # ========================================================

    st.subheader(
        "🔎 Historische Bewertung"
    )


    avg_kgv = (
        df["KGV"]
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .mean()
    )


    avg_kcv = (
        df["KCV"]
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .mean()
    )


    avg_kbv = (
        df["KBV"]
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .mean()
    )


    avg_kuv = (
        df["KUV"]
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .mean()
    )


    latest = df.iloc[0]


    current_kgv = calculate_multiple(
        current_price,
        latest["EPS"]
    )


    current_kcv = calculate_multiple(
        current_price,
        latest["FCF/Aktie"]
    )


    current_kbv = calculate_multiple(
        current_price,
        latest["Buchwert/Aktie"]
    )


    current_kuv = calculate_multiple(
        current_price,
        latest["Umsatz/Aktie"]
    )


    valuation_df = pd.DataFrame({

        "Kennzahl": [
            "KGV",
            "KCV",
            "KBV",
            "KUV"
        ],

        "Aktuell": [
            current_kgv,
            current_kcv,
            current_kbv,
            current_kuv
        ],

        "Ø historische 5 Jahre": [
            avg_kgv,
            avg_kcv,
            avg_kbv,
            avg_kuv
        ]
    })


    st.dataframe(
        valuation_df.style.format(
            precision=2,
            na_rep="-"
        ),
        use_container_width=True
    )


    # ========================================================
    # GRAHAM
    # ========================================================

    st.subheader(
        "📐 Bewertung nach Benjamin Graham"
    )


    avg_eps = (
        df["EPS"].mean()
    )


    avg_bvps = (
        df["Buchwert/Aktie"].mean()
    )


    if (
        pd.notna(avg_eps)
        and pd.notna(avg_bvps)
        and avg_eps > 0
        and avg_bvps > 0
    ):

        graham_value = np.sqrt(
            22.5
            * avg_eps
            * avg_bvps
        )


        graham_difference = (
            (
                graham_value
                - current_price
            )
            / current_price
        ) * 100


        c1, c2, c3 = st.columns(3)


        with c1:

            st.metric(
                "Graham-Wert",
                f"{graham_value:.2f} "
                f"{currency}"
            )


        with c2:

            st.metric(
                "Aktueller Kurs",
                f"{current_price:.2f} "
                f"{currency}"
            )


        with c3:

            st.metric(
                "Abweichung",
                f"{graham_difference:+.1f}%"
            )


    else:

        st.warning(
            "Graham-Zahl kann nicht berechnet werden, "
            "weil EPS oder Buchwert nicht positiv sind."
        )


    # ========================================================
    # DCF
    # ========================================================

    st.subheader(
        "💰 DCF-Bewertung"
    )


    # --------------------------------------------------------
    # Jüngster FCF
    # --------------------------------------------------------

    ttm_fcf = np.nan


    try:

        if not df.empty:

            ttm_fcf = (
                latest[
                    "Free Cashflow (Mrd.)"
                ]
                * 1e9
            )

    except Exception:

        pass


    # --------------------------------------------------------
    # Aktienanzahl
    # --------------------------------------------------------

    shares_now = safe_float(
        info.get(
            "sharesOutstanding"
        )
    )


    if pd.isna(shares_now):

        try:

            if (
                balance_sheet is not None
                and not balance_sheet.empty
            ):

                latest_bs = (
                    balance_sheet.columns[0]
                )


                shares_now = get_value(
                    balance_sheet,
                    [
                        "Ordinary Shares Number",
                        "Share Issued"
                    ],
                    latest_bs
                )

        except Exception:

            shares_now = np.nan


    # --------------------------------------------------------
    # Netto-Schulden
    # --------------------------------------------------------

    net_debt = 0


    try:

        if (
            balance_sheet is not None
            and not balance_sheet.empty
        ):

            latest_bs = (
                balance_sheet.columns[0]
            )


            current_cash = get_value(
                balance_sheet,
                [
                    "Cash And Cash Equivalents",
                    "Cash Cash Equivalents And Short Term Investments"
                ],
                latest_bs
            )


            current_debt = get_value(
                balance_sheet,
                [
                    "Total Debt",
                    "Total Debt And Capital Lease Obligation"
                ],
                latest_bs
            )


            if (
                pd.notna(current_cash)
                and pd.notna(current_debt)
            ):

                net_debt = (
                    current_debt
                    - current_cash
                )

    except Exception:

        net_debt = 0


    # --------------------------------------------------------
    # DCF berechnen
    # --------------------------------------------------------

    dcf_per_share = calculate_dcf(
        ttm_fcf,
        shares_now,
        net_debt,
        growth_rate,
        wacc,
        terminal_growth,
        forecast_years
    )


    if pd.notna(
        dcf_per_share
    ):

        dcf_upside = (
            (
                dcf_per_share
                - current_price
            )
            / current_price
        ) * 100


        dcf_margin_price = (
            dcf_per_share
            * (
                1
                - margin_of_safety / 100
            )
        )


        c1, c2, c3 = st.columns(3)


        with c1:

            st.metric(
                "DCF fairer Wert",
                f"{dcf_per_share:.2f} "
                f"{currency}"
            )


        with c2:

            st.metric(
                "Upside / Downside",
                f"{dcf_upside:+.1f}%"
            )


        with c3:

            st.metric(
                "Wert mit Sicherheitsmarge",
                f"{dcf_margin_price:.2f} "
                f"{currency}"
            )


    else:

        st.warning(
            "DCF konnte nicht berechnet werden. "
            "Dafür werden ein positiver FCF, eine "
            "gültige Aktienanzahl und WACC > "
            "Terminal Growth benötigt."
        )


    # ========================================================
    # FUNDAMENTALER SCORE
    # ========================================================

    st.subheader(
        "🏆 Fundamentaler Score"
    )


    # --------------------------------------------------------
    # Wachstum
    # --------------------------------------------------------

    score_revenue = growth_score(
        df["Umsatz (Mrd.)"],
        10
    )


    score_eps = growth_score(
        df["EPS"],
        10
    )


    score_fcf = growth_score(
        df["Free Cashflow (Mrd.)"],
        10
    )


    # --------------------------------------------------------
    # FCF-Marge
    # --------------------------------------------------------

    fcf_margin = latest[
        "FCF-Marge (%)"
    ]


    if pd.isna(fcf_margin):

        score_fcf_margin = 0

    elif fcf_margin >= 25:

        score_fcf_margin = 10

    elif fcf_margin >= 20:

        score_fcf_margin = 9

    elif fcf_margin >= 15:

        score_fcf_margin = 8

    elif fcf_margin >= 10:

        score_fcf_margin = 6

    elif fcf_margin >= 5:

        score_fcf_margin = 4

    elif fcf_margin >= 0:

        score_fcf_margin = 2

    else:

        score_fcf_margin = 0


    # --------------------------------------------------------
    # ROE
    # --------------------------------------------------------

    roe = latest[
        "ROE (%)"
    ]


    if pd.isna(roe):

        score_roe = 0

    elif roe >= 25:

        score_roe = 10

    elif roe >= 20:

        score_roe = 9

    elif roe >= 15:

        score_roe = 8

    elif roe >= 10:

        score_roe = 6

    elif roe >= 5:

        score_roe = 4

    elif roe >= 0:

        score_roe = 2

    else:

        score_roe = 0


    # --------------------------------------------------------
    # Verschuldung
    # --------------------------------------------------------

    debt_equity = latest[
        "Debt/Equity (%)"
    ]


    if pd.isna(debt_equity):

        score_debt = 0

    elif debt_equity <= 20:

        score_debt = 10

    elif debt_equity <= 50:

        score_debt = 9

    elif debt_equity <= 100:

        score_debt = 7

    elif debt_equity <= 150:

        score_debt = 5

    elif debt_equity <= 250:

        score_debt = 3

    else:

        score_debt = 0


    # --------------------------------------------------------
    # Liquidität
    # --------------------------------------------------------

    liquidity = latest[
        "Liquidität 3 (%)"
    ]


    if pd.isna(liquidity):

        score_liquidity = 0

    elif liquidity >= 200:

        score_liquidity = 5

    elif liquidity >= 150:

        score_liquidity = 4

    elif liquidity >= 100:

        score_liquidity = 3

    elif liquidity >= 75:

        score_liquidity = 1

    else:

        score_liquidity = 0


    # --------------------------------------------------------
    # Dividendenqualität
    # --------------------------------------------------------

    score_dividend = 0


    payout = latest[
        "Ausschüttungsquote 1 (%)"
    ]


    if (
        pd.notna(payout)
        and 20 <= payout <= 60
    ):

        score_dividend += 3

    elif (
        pd.notna(payout)
        and 10 <= payout <= 75
    ):

        score_dividend += 2

    elif (
        pd.notna(payout)
        and 0 <= payout <= 100
    ):

        score_dividend += 1


    dividend_values = (
        df[
            "Dividende/Aktie"
        ]
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .dropna()
    )


    if len(
        dividend_values
    ) >= 2:

        if (
            dividend_values.iloc[0]
            > dividend_values.iloc[-1]
        ):

            score_dividend += 2


    score_dividend = min(
        score_dividend,
        5
    )


    # --------------------------------------------------------
    # Historische Bewertung
    # --------------------------------------------------------

    score_historical = 0


    score_historical += valuation_score(
        current_kgv,
        avg_kgv,
        2.5
    )


    score_historical += valuation_score(
        current_kcv,
        avg_kcv,
        2.5
    )


    score_historical += valuation_score(
        current_kbv,
        avg_kbv,
        2.5
    )


    score_historical += valuation_score(
        current_kuv,
        avg_kuv,
        2.5
    )


    # --------------------------------------------------------
    # DCF Score
    # --------------------------------------------------------

    score_dcf = 0


    if pd.notna(
        dcf_per_share
    ):

        dcf_diff = (
            (
                dcf_per_share
                - current_price
            )
            / current_price
        ) * 100


        if dcf_diff >= 30:

            score_dcf = 10

        elif dcf_diff >= 20:

            score_dcf = 9

        elif dcf_diff >= 10:

            score_dcf = 8

        elif dcf_diff >= 0:

            score_dcf = 7

        elif dcf_diff >= -10:

            score_dcf = 5

        elif dcf_diff >= -20:

            score_dcf = 3


    # --------------------------------------------------------
    # Gesamt
    # --------------------------------------------------------

    total_score = (
        score_revenue
        + score_eps
        + score_fcf
        + score_fcf_margin
        + score_roe
        + score_debt
        + score_liquidity
        + score_dividend
        + score_historical
        + score_dcf
    )


    max_score = 90


    normalized_score = (
        total_score
        / max_score
    ) * 100


    normalized_score = min(
        100,
        normalized_score
    )


    # --------------------------------------------------------
    # Bewertung
    # --------------------------------------------------------

    if normalized_score >= 85:

        rating = "Sehr attraktiv"

    elif normalized_score >= 70:

        rating = "Attraktiv"

    elif normalized_score >= 55:

        rating = "Neutral"

    elif normalized_score >= 40:

        rating = "Eher unattraktiv"

    else:

        rating = "Unattraktiv"


    # ========================================================
    # SCORE ANZEIGE
    # ========================================================

    c1, c2 = st.columns(2)


    with c1:

        st.metric(
            "Gesamtscore",
            f"{normalized_score:.1f} / 100"
        )


    with c2:

        st.metric(
            "Einschätzung",
            rating
        )


    score_table = pd.DataFrame({

        "Kriterium": [

            "Umsatzwachstum",
            "EPS-Wachstum",
            "FCF-Wachstum",
            "FCF-Marge",
            "ROE",
            "Verschuldung",
            "Liquidität",
            "Dividendenqualität",
            "Historische Bewertung",
            "DCF"
        ],

        "Punkte": [

            score_revenue,
            score_eps,
            score_fcf,
            score_fcf_margin,
            score_roe,
            score_debt,
            score_liquidity,
            score_dividend,
            score_historical,
            score_dcf
        ],

        "Maximum": [

            10,
            10,
            10,
            10,
            10,
            10,
            5,
            5,
            10,
            10
        ]
    })


    st.dataframe(
        score_table.style.format(
            precision=1
        ),
        use_container_width=True
    )


    # ========================================================
    # DCF SENSITIVITÄT
    # ========================================================

    if (
        pd.notna(ttm_fcf)
        and ttm_fcf > 0
        and pd.notna(shares_now)
        and shares_now > 0
    ):

        st.subheader(
            "🎯 DCF-Sensitivitätsanalyse"
        )


        sensitivity = []


        wacc_values = [

            max(
                5,
                wacc - 1
            ),

            wacc,

            wacc + 1
        ]


        growth_values = [

            growth_rate - 2,

            growth_rate,

            growth_rate + 2
        ]


        for growth in growth_values:

            row = []


            for discount in wacc_values:

                if (
                    discount
                    <= terminal_growth
                ):

                    row.append(
                        np.nan
                    )

                    continue


                fcfs = [

                    ttm_fcf
                    * (
                        1
                        + growth / 100
                    )
                    ** year

                    for year in range(
                        1,
                        forecast_years + 1
                    )
                ]


                pv = sum(

                    fcf
                    / (
                        1
                        + discount / 100
                    )
                    ** year

                    for year, fcf
                    in enumerate(
                        fcfs,
                        start=1
                    )
                )


                terminal = (

                    fcfs[-1]
                    * (
                        1
                        + terminal_growth / 100
                    )
                    / (
                        discount / 100
                        - terminal_growth / 100
                    )
                )


                terminal_pv = (

                    terminal
                    / (
                        1
                        + discount / 100
                    )
                    ** forecast_years
                )


                equity_value = (
                    pv
                    + terminal_pv
                    - net_debt
                )


                fair_value = (
                    equity_value
                    / shares_now
                )


                row.append(
                    fair_value
                )


            sensitivity.append(
                row
            )


        sensitivity_df = pd.DataFrame(

            sensitivity,

            index=[
                f"{g:.1f}% Wachstum"
                for g in growth_values
            ],

            columns=[
                f"{w:.2f}% WACC"
                for w in wacc_values
            ]
        )


        st.dataframe(
            sensitivity_df.style.format(
                "{:.2f}"
            ),
            use_container_width=True
        )


    # ========================================================
    # ABSCHLUSS
    # ========================================================

    st.subheader(
        "🧭 Zusammenfassung"
    )


    if normalized_score >= 70:

        st.success(
            f"**{company_name}** erreicht "
            f"**{normalized_score:.1f}/100 Punkte** "
            f"und wird im Modell als "
            f"**{rating}** eingestuft."
        )

    elif normalized_score >= 55:

        st.info(
            f"**{company_name}** erreicht "
            f"**{normalized_score:.1f}/100 Punkte**. "
            f"Das Modell bewertet die Aktie als "
            f"**{rating}**."
        )

    else:

        st.warning(
            f"**{company_name}** erreicht "
            f"**{normalized_score:.1f}/100 Punkte** "
            f"und wird als "
            f"**{rating}** eingestuft."
        )


    st.caption(
        "⚠️ Hinweis: Dieses Tool dient ausschließlich "
        "der Analyse und stellt keine Anlageberatung dar. "
        "Insbesondere bei kleineren Nebenwerten können "
        "Daten von Yahoo Finance unvollständig oder "
        "zeitlich verzögert sein."
    )
