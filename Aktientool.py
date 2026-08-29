```python
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time


# ============================================================
# STREAMLIT KONFIGURATION
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
    """Wandelt einen Wert sicher in float um."""
    try:
        if value is None or pd.isna(value):
            return np.nan
        return float(value)
    except Exception:
        return np.nan


def get_row_value(df, rows, column):
    """
    Sucht einen Finanzwert anhand mehrerer möglicher
    Yahoo-Finance-Bezeichnungen.
    """

    if df is None or df.empty:
        return np.nan

    for row in rows:

        try:

            if row in df.index and column in df.columns:

                value = df.loc[row, column]

                if pd.notna(value):
                    return float(value)

        except Exception:
            continue

    return np.nan


def clean_columns(df):
    """Bereinigt MultiIndex-Spalten von yfinance."""

    if df is None or df.empty:
        return df

    result = df.copy()

    if isinstance(result.columns, pd.MultiIndex):

        result.columns = [
            col[0] if isinstance(col, tuple) else col
            for col in result.columns
        ]

    return result


# ============================================================
# FIRMA / TICKER / WKN / ISIN
# ============================================================

COMPANY_MAP = {

    # ========================================================
    # DEUTSCHLAND
    # ========================================================

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

    "RHEINMETALL": "RHM.DE",

    "FRESENIUS": "FRE.DE",

    "E.ON": "EOAN.DE",

    "VONOVIA": "VNA.DE",

    "PUMA": "PUM.DE",

    "BEIERSDORF": "BEI.DE",

    "MERCK": "MRK.DE",

    "QIAGEN": "QIA.DE",

    # ========================================================
    # USA
    # ========================================================

    "APPLE": "AAPL",

    "MICROSOFT": "MSFT",

    "AMAZON": "AMZN",

    "ALPHABET": "GOOGL",
    "GOOGLE": "GOOGL",

    "META": "META",

    "NVIDIA": "NVDA",

    "TESLA": "TSLA",

    "PEPSICO": "PEP",
    "PEPSI": "PEP",

    "COCA COLA": "KO",
    "COCA-COLA": "KO",

    "MCDONALDS": "MCD",
    "MCDONALD'S": "MCD",

    "JOHNSON & JOHNSON": "JNJ",
    "JOHNSON JOHNSON": "JNJ",

    "PROCTER & GAMBLE": "PG",
    "PROCTER GAMBLE": "PG",

    "BERKSHIRE HATHAWAY": "BRK-B",

    "VISA": "V",

    "MASTERCARD": "MA",

    "JPMORGAN": "JPM",
    "JPMORGAN CHASE": "JPM",

    "EXXON": "XOM",
    "EXXON MOBIL": "XOM",

    "CHEVRON": "CVX",

    "COSTCO": "COST",

    "WALMART": "WMT",

    "MCDONALD'S": "MCD",

    "NIKE": "NKE",

    "ADOBE": "ADBE",

    "BROADCOM": "AVGO",

    "INTEL": "INTC",

    "AMD": "AMD"
}


# ============================================================
# WKN / ISIN
# ============================================================

IDENTIFIER_MAP = {

    # InnoTec TSS
    "540510": "TSS.DE",
    "DE0005405104": "TSS.DE",

    # SAP
    "716460": "SAP.DE",
    "DE0007164600": "SAP.DE",

    # Siemens
    "723610": "SIE.DE",
    "DE0007236101": "SIE.DE",

    # Allianz
    "840400": "ALV.DE",
    "DE0008404005": "ALV.DE",

    # BMW
    "519000": "BMW.DE",
    "DE0005190003": "BMW.DE",

    # Mercedes
    "710000": "MBG.DE",
    "DE0007100000": "MBG.DE",

    # Deutsche Telekom
    "555750": "DTE.DE",
    "DE0005557508": "DTE.DE",

    # Infineon
    "623100": "IFX.DE",
    "DE0006231004": "IFX.DE",

    # BASF
    "BASF11": "BAS.DE",
    "DE000BASF111": "BAS.DE",

    # Adidas
    "A1EWWW": "ADS.DE",
    "DE000A1EWWW0": "ADS.DE",

    # Volkswagen
    "766403": "VOW3.DE",
    "DE0007664039": "VOW3.DE",

    # Deutsche Bank
    "514000": "DBK.DE",
    "DE0005140008": "DBK.DE",

    # Commerzbank
    "CBK100": "CBK.DE",
    "DE000CBK1001": "CBK.DE",

    # Munich Re
    "843002": "MUV2.DE",
    "DE0008430026": "MUV2.DE",

    # Deutsche Post
    "555200": "DHL.DE",
    "DE0005552004": "DHL.DE"
}


def normalize_input(user_input):

    value = (
        user_input
        .strip()
        .upper()
    )

    # Firmenname
    if value in COMPANY_MAP:
        return COMPANY_MAP[value]

    # WKN / ISIN
    if value in IDENTIFIER_MAP:
        return IDENTIFIER_MAP[value]

    # Berkshire Hathaway
    if value in [
        "BRK.B",
        "BRK/B"
    ]:
        return "BRK-B"

    # Bereits vollständiger Yahoo-Ticker
    if "." in value:
        return value

    # Wichtig:
    # Normale Ticker NICHT automatisch verändern.
    #
    # PEP -> PEP
    # AAPL -> AAPL
    # MSFT -> MSFT

    return value


# ============================================================
# YAHOO-DATEN LADEN
# ============================================================

@st.cache_data(
    ttl=1800,
    show_spinner=False
)
def load_data(ticker_symbol):

    ticker = yf.Ticker(
        ticker_symbol
    )

    # --------------------------------------------------------
    # Historische Kurse
    # --------------------------------------------------------

    history = ticker.history(
        period="6y",
        interval="1d",
        auto_adjust=False
    )

    # --------------------------------------------------------
    # Fundamentaldaten
    # --------------------------------------------------------

    income_stmt = ticker.income_stmt

    balance_sheet = ticker.balance_sheet

    cashflow = ticker.cashflow

    # --------------------------------------------------------
    # Dividenden
    # --------------------------------------------------------

    try:

        dividends = ticker.dividends

    except Exception:

        dividends = pd.Series(
            dtype=float
        )

    return {
        "ticker": ticker,
        "history": history,
        "income_stmt": income_stmt,
        "balance_sheet": balance_sheet,
        "cashflow": cashflow,
        "dividends": dividends
    }


# ============================================================
# HISTORISCHER JAHRESENDKURS
# ============================================================

def get_year_end_price(
    history,
    year
):

    if (
        history is None
        or history.empty
    ):
        return np.nan

    try:

        data = history.copy()

        data.index = pd.to_datetime(
            data.index
        )

        # Zeitzone entfernen
        try:

            data.index = (
                data.index
                .tz_localize(None)
            )

        except Exception:
            pass

        year_data = data[
            data.index.year == year
        ]

        if year_data.empty:
            return np.nan

        close = (
            year_data["Close"]
            .dropna()
        )

        if close.empty:
            return np.nan

        return float(
            close.iloc[-1]
        )

    except Exception:

        return np.nan


# ============================================================
# MULTIPLE
# ============================================================

def multiple(
    price,
    per_share_value
):

    if (
        pd.notna(price)
        and pd.notna(per_share_value)
        and per_share_value > 0
    ):

        return (
            price
            / per_share_value
        )

    return np.nan


# ============================================================
# GRAHAM
# ============================================================

def graham_value(
    eps,
    bvps
):

    if (
        pd.notna(eps)
        and pd.notna(bvps)
        and eps > 0
        and bvps > 0
    ):

        return np.sqrt(
            22.5
            * eps
            * bvps
        )

    return np.nan


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
    years
):

    if (
        pd.isna(fcf)
        or fcf <= 0
        or pd.isna(shares)
        or shares <= 0
        or wacc <= terminal_growth
    ):

        return np.nan

    growth = (
        growth_rate / 100
    )

    discount = (
        wacc / 100
    )

    terminal = (
        terminal_growth / 100
    )

    pv = 0

    forecast = []

    for year in range(
        1,
        years + 1
    ):

        future_fcf = (
            fcf
            * (
                1 + growth
            ) ** year
        )

        forecast.append(
            future_fcf
        )

        pv += (
            future_fcf
            / (
                1 + discount
            ) ** year
        )

    terminal_fcf = (
        forecast[-1]
        * (
            1 + terminal
        )
    )

    terminal_value = (
        terminal_fcf
        / (
            discount
            - terminal
        )
    )

    terminal_pv = (
        terminal_value
        / (
            1 + discount
        ) ** years
    )

    enterprise_value = (
        pv
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
# WACHSTUMS-SCORE
# ============================================================

def growth_score(
    values,
    maximum
):

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
        (
            newest
            - oldest
        )
        / abs(oldest)
    ) * 100

    if growth >= 50:
        return maximum

    if growth >= 30:
        return maximum * 0.9

    if growth >= 15:
        return maximum * 0.8

    if growth >= 5:
        return maximum * 0.7

    if growth >= 0:
        return maximum * 0.55

    if growth >= -10:
        return maximum * 0.35

    if growth >= -25:
        return maximum * 0.15

    return 0


# ============================================================
# VALUATION SCORE
# ============================================================

def valuation_score(
    current,
    historical,
    maximum
):

    if (
        pd.isna(current)
        or pd.isna(historical)
        or current <= 0
        or historical <= 0
    ):
        return 0

    difference = (
        (
            historical
            - current
        )
        / historical
    ) * 100

    if difference >= 30:
        return maximum

    if difference >= 20:
        return maximum * 0.9

    if difference >= 10:
        return maximum * 0.8

    if difference >= 0:
        return maximum * 0.65

    if difference >= -10:
        return maximum * 0.45

    if difference >= -20:
        return maximum * 0.2

    return 0


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header(
    "⚙️ DCF-Annahmen"
)

forecast_years = st.sidebar.slider(
    "Prognosezeitraum",
    3,
    10,
    5
)

growth_rate = st.sidebar.slider(
    "FCF-Wachstum (%)",
    -10.0,
    30.0,
    8.0,
    0.5
)

wacc = st.sidebar.slider(
    "WACC (%)",
    5.0,
    15.0,
    9.0,
    0.25
)

terminal_growth = st.sidebar.slider(
    "Terminal Growth (%)",
    0.0,
    5.0,
    2.5,
    0.25
)

margin_of_safety = st.sidebar.slider(
    "Sicherheitsmarge (%)",
    0,
    50,
    20,
    5
)


# ============================================================
# EINGABE
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
        f"Erkannter Yahoo-Finance-Ticker: **{ticker_symbol}**"
    )


    # ========================================================
    # DATEN LADEN
    # ========================================================

    try:

        with st.spinner(
            f"Lade Daten für {ticker_symbol}..."
        ):

            data = load_data(
                ticker_symbol
            )

    except Exception as e:

        error_text = str(e).lower()

        if (
            "too many requests"
            in error_text
            or "rate limit"
            in error_text
            or "429"
            in error_text
        ):

            st.error(
                "⚠️ Yahoo Finance hat die Anfrage "
                "wegen eines Rate-Limits abgelehnt."
            )

            st.warning(
                "Bitte einige Minuten warten und "
                "danach die Seite neu laden."
            )

        else:

            st.error(
                "⚠️ Fehler beim Laden der Yahoo-Finance-Daten."
            )

            st.code(
                str(e)
            )

        st.stop()


    # ========================================================
    # DATEN
    # ========================================================

    ticker = data["ticker"]

    history = data["history"]

    financials = data["income_stmt"]

    balance_sheet = data["balance_sheet"]

    cashflow = data["cashflow"]

    dividends = data["dividends"]


    # ========================================================
    # KURSE PRÜFEN
    # ========================================================

    if (
        history is None
        or history.empty
    ):

        st.error(
            f"⚠️ Yahoo Finance liefert für "
            f"**{ticker_symbol}** keine historischen Kurse."
        )

        st.info(
            "Prüfe den Yahoo-Ticker. "
            "Beispiele: AAPL, PEP, SAP.DE, TSS.DE"
        )

        st.stop()


    close = (
        history["Close"]
        .dropna()
    )


    if close.empty:

        st.error(
            "⚠️ Keine Schlusskurse verfügbar."
        )

        st.stop()


    current_price = float(
        close.iloc[-1]
    )


    # ========================================================
    # INFO
    # ========================================================

    try:

        info = ticker.info

    except Exception:

        info = {}


    company_name = info.get(
        "longName",
        ticker_symbol
    )

    currency = info.get(
        "currency",
        "EUR"
        if ticker_symbol.endswith(".DE")
        else "USD"
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


    # ========================================================
    # KOPF
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


    # ========================================================
    # FINANZDATEN PRÜFEN
    # ========================================================

    if (
        financials is None
        or financials.empty
    ):

        st.warning(
            "⚠️ Yahoo Finance liefert für diesen Titel "
            "keine ausreichenden Jahres-Finanzdaten."
        )

        st.stop()


    # ========================================================
    # JAHRE
    # ========================================================

    years = list(
        financials.columns[:5]
    )


    rows = []


    # ========================================================
    # JAHRESSCHLEIFE
    # ========================================================

    for year in years:

        year_number = (
            pd.Timestamp(year).year
        )


        # ----------------------------------------------------
        # UMSATZ
        # ----------------------------------------------------

        revenue = get_row_value(
            financials,
            [
                "Total Revenue",
                "Operating Revenue"
            ],
            year
        )


        # ----------------------------------------------------
        # NETTOGEWINN
        # ----------------------------------------------------

        net_income = get_row_value(
            financials,
            [
                "Net Income",
                "Net Income Common Stockholders"
            ],
            year
        )


        # ----------------------------------------------------
        # EIGENKAPITAL
        # ----------------------------------------------------

        equity = get_row_value(
            balance_sheet,
            [
                "Stockholders Equity",
                "Common Stock Equity",
                "Total Equity Gross Minority Interest"
            ],
            year
        )


        # ----------------------------------------------------
        # SCHULDEN
        # ----------------------------------------------------

        debt = get_row_value(
            balance_sheet,
            [
                "Total Debt",
                "Total Debt And Capital Lease Obligation"
            ],
            year
        )


        # ----------------------------------------------------
        # CASH
        # ----------------------------------------------------

        cash = get_row_value(
            balance_sheet,
            [
                "Cash And Cash Equivalents",
                "Cash Cash Equivalents And Short Term Investments"
            ],
            year
        )


        # ----------------------------------------------------
        # FORDERUNGEN
        # ----------------------------------------------------

        receivables = get_row_value(
            balance_sheet,
            [
                "Receivables",
                "Accounts Receivable"
            ],
            year
        )


        # ----------------------------------------------------
        # UMLAUFVERMÖGEN
        # ----------------------------------------------------

        current_assets = get_row_value(
            balance_sheet,
            [
                "Current Assets"
            ],
            year
        )


        # ----------------------------------------------------
        # KURZFRISTIGE VERBINDLICHKEITEN
        # ----------------------------------------------------

        current_liabilities = get_row_value(
            balance_sheet,
            [
                "Current Liabilities"
            ],
            year
        )


        # ----------------------------------------------------
        # FREE CASHFLOW
        # ----------------------------------------------------

        fcf = get_row_value(
            cashflow,
            [
                "Free Cash Flow"
            ],
            year
        )


        # ----------------------------------------------------
        # FALLBACK FCF
        # ----------------------------------------------------

        if pd.isna(fcf):

            operating_cf = get_row_value(
                cashflow,
                [
                    "Operating Cash Flow",
                    "Total Cash From Operating Activities"
                ],
                year
            )

            capex = get_row_value(
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

                fcf = (
                    operating_cf
                    + capex
                )


        # ----------------------------------------------------
        # AKTIENANZAHL
        # ----------------------------------------------------

        shares = get_row_value(
            financials,
            [
                "Diluted Average Shares",
                "Basic Average Shares"
            ],
            year
        )


        if pd.isna(shares):

            shares = get_row_value(
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
            and shares > 0
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
            and shares > 0
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
            pd.notna(fcf)
            and pd.notna(shares)
            and shares > 0
        ):

            fcf_ps = (
                fcf
                / shares
            )

        else:

            fcf_ps = np.nan


        # ----------------------------------------------------
        # UMSATZ PRO AKTIE
        # ----------------------------------------------------

        if (
            pd.notna(revenue)
            and pd.notna(shares)
            and shares > 0
        ):

            revenue_ps = (
                revenue
                / shares
            )

        else:

            revenue_ps = np.nan


        # ====================================================
        # DIVIDENDE PRO AKTIE
        # ====================================================

        dividend_ps = 0.0


        if (
            dividends is not None
            and not dividends.empty
        ):

            try:

                divs = dividends.copy()

                divs.index = pd.to_datetime(
                    divs.index
                )

                try:

                    divs.index = (
                        divs.index
                        .tz_localize(None)
                    )

                except Exception:
                    pass

                year_dividends = divs[
                    divs.index.year
                    == year_number
                ]

                if not year_dividends.empty:

                    dividend_ps = float(
                        year_dividends.sum()
                    )

            except Exception:

                dividend_ps = 0.0


        # ====================================================
        # AUSSCHÜTTUNGSQUOTE 1
        #
        # Dividende je Aktie
        # ------------------
        # Gewinn je Aktie
        # ====================================================

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


        # ====================================================
        # AUSSCHÜTTUNGSQUOTE 2
        #
        # Dividende je Aktie
        # ------------------
        # FCF je Aktie
        # ====================================================

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


        # ====================================================
        # LIQUIDITÄT
        # ====================================================

        if (
            pd.notna(current_liabilities)
            and current_liabilities > 0
        ):

            liq1 = (
                cash
                / current_liabilities
            ) * 100

            liq2 = (
                (
                    cash
                    + receivables
                )
                / current_liabilities
            ) * 100

            liq3 = (
                current_assets
                / current_liabilities
            ) * 100

        else:

            liq1 = np.nan
            liq2 = np.nan
            liq3 = np.nan


        # ====================================================
        # FCF-MARGE
        # ====================================================

        if (
            pd.notna(fcf)
            and pd.notna(revenue)
            and revenue != 0
        ):

            fcf_margin = (
                fcf
                / revenue
            ) * 100

        else:

            fcf_margin = np.nan


        # ====================================================
        # ROE
        # ====================================================

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


        # ====================================================
        # DEBT / EQUITY
        # ====================================================

        if (
            pd.notna(debt)
            and pd.notna(equity)
            and equity > 0
        ):

            debt_equity = (
                debt
                / equity
            ) * 100

        else:

            debt_equity = np.nan


        # ====================================================
        # JAHRESENDKURS
        # ====================================================

        year_end_price = (
            get_year_end_price(
                history,
                year_number
            )
        )


        # ====================================================
        # HISTORISCHE MULTIPLES
        # ====================================================

        kgv = multiple(
            year_end_price,
            eps
        )

        kcv = multiple(
            year_end_price,
            fcf_ps
        )

        kbv = multiple(
            year_end_price,
            bvps
        )

        kuv = multiple(
            year_end_price,
            revenue_ps
        )


        # ====================================================
        # ZEILE
        # ====================================================

        rows.append({

            "Jahr":
                str(year_number),

            "Jahresendkurs":
                year_end_price,

            "Umsatz (Mrd.)":
                revenue / 1e9
                if pd.notna(revenue)
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
                fcf / 1e9
                if pd.notna(fcf)
                else np.nan,

            "EPS":
                eps,

            "Buchwert/Aktie":
                bvps,

            "FCF/Aktie":
                fcf_ps,

            "Umsatz/Aktie":
                revenue_ps,

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
                liq1,

            "Liquidität 2 (%)":
                liq2,

            "Liquidität 3 (%)":
                liq3
        })


    # ========================================================
    # DATAFRAME
    # ========================================================

    df = pd.DataFrame(
        rows
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
    # AKTUELLE KENNZAHLEN
    # ========================================================

    latest = df.iloc[0]


    current_eps = latest[
        "EPS"
    ]

    current_bvps = latest[
        "Buchwert/Aktie"
    ]

    current_fcf_ps = latest[
        "FCF/Aktie"
    ]

    current_revenue_ps = latest[
        "Umsatz/Aktie"
    ]


    current_kgv = multiple(
        current_price,
        current_eps
    )

    current_kcv = multiple(
        current_price,
        current_fcf_ps
    )

    current_kbv = multiple(
        current_price,
        current_bvps
    )

    current_kuv = multiple(
        current_price,
        current_revenue_ps
    )


    # ========================================================
    # HISTORISCHE DURCHSCHNITTSWERTE
    # ========================================================

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


    # ========================================================
    # BEWERTUNG
    # ========================================================

    st.subheader(
        "🔎 Aktuelle vs. historische Bewertung"
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

        "5-Jahres-Durchschnitt": [
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


    graham = graham_value(
        avg_eps,
        avg_bvps
    )


    if pd.notna(graham):

        difference = (
            (
                graham
                - current_price
            )
            / current_price
        ) * 100


        c1, c2, c3 = st.columns(3)


        with c1:

            st.metric(
                "Graham-Wert",
                f"{graham:.2f} {currency}"
            )


        with c2:

            st.metric(
                "Aktueller Kurs",
                f"{current_price:.2f} {currency}"
            )


        with c3:

            st.metric(
                "Abweichung",
                f"{difference:+.1f}%"
            )


        if current_price < graham:

            st.success(
                "Nach der Graham-Zahl liegt der "
                "aktuelle Kurs unter dem berechneten Wert."
            )

        else:

            st.warning(
                "Nach der Graham-Zahl liegt der "
                "aktuelle Kurs über dem berechneten Wert."
            )

    else:

        st.warning(
            "Graham-Wert kann nicht berechnet werden."
        )


    # ========================================================
    # DCF
    # ========================================================

    st.subheader(
        "💰 DCF-Bewertung"
    )


    latest_fcf = (
        latest["Free Cashflow (Mrd.)"]
        * 1e9
    )


    # --------------------------------------------------------
    # Aktienanzahl
    # --------------------------------------------------------

    shares_now = safe_float(
        info.get(
            "sharesOutstanding"
        )
    )


    if pd.isna(shares_now):

        latest_bs_column = (
            balance_sheet.columns[0]
            if (
                balance_sheet is not None
                and not balance_sheet.empty
            )
            else None
        )

        if latest_bs_column is not None:

            shares_now = get_row_value(
                balance_sheet,
                [
                    "Ordinary Shares Number",
                    "Share Issued"
                ],
                latest_bs_column
            )


    # --------------------------------------------------------
    # Netto-Schulden
    # --------------------------------------------------------

    net_debt = 0.0


    if (
        balance_sheet is not None
        and not balance_sheet.empty
    ):

        latest_bs_column = (
            balance_sheet.columns[0]
        )

        cash_now = get_row_value(
            balance_sheet,
            [
                "Cash And Cash Equivalents",
                "Cash Cash Equivalents And Short Term Investments"
            ],
            latest_bs_column
        )

        debt_now = get_row_value(
            balance_sheet,
            [
                "Total Debt",
                "Total Debt And Capital Lease Obligation"
            ],
            latest_bs_column
        )

        if (
            pd.notna(cash_now)
            and pd.notna(debt_now)
        ):

            net_debt = (
                debt_now
                - cash_now
            )


    dcf = calculate_dcf(
        latest_fcf,
        shares_now,
        net_debt,
        growth_rate,
        wacc,
        terminal_growth,
        forecast_years
    )


    if pd.notna(dcf):

        dcf_difference = (
            (
                dcf
                - current_price
            )
            / current_price
        ) * 100


        price_with_margin = (
            dcf
            * (
                1
                - margin_of_safety / 100
            )
        )


        c1, c2, c3 = st.columns(3)


        with c1:

            st.metric(
                "DCF-Wert",
                f"{dcf:.2f} {currency}"
            )


        with c2:

            st.metric(
                "Upside / Downside",
                f"{dcf_difference:+.1f}%"
            )


        with c3:

            st.metric(
                "DCF mit Sicherheitsmarge",
                f"{price_with_margin:.2f} {currency}"
            )

    else:

        st.warning(
            "DCF konnte nicht berechnet werden. "
            "Dafür werden positive FCF-Daten und "
            "eine gültige Aktienanzahl benötigt."
        )


    # ========================================================
    # DIVIDENDEN
    # ========================================================

    st.subheader(
        "💶 Dividendenanalyse"
    )


    dividend_table = df[
        [
            "Jahr",
            "Dividende/Aktie",
            "Ausschüttungsquote 1 (%)",
            "Ausschüttungsquote 2 (%)"
        ]
    ].copy()


    st.dataframe(
        dividend_table.style.format(
            precision=2,
            na_rep="-"
        ),
        use_container_width=True
    )


    # ========================================================
    # SCORE
    # ========================================================

    st.subheader(
        "🏆 Fundamentaler Score"
    )


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
    # FCF-MARGE
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

    else:

        score_roe = 0


    # --------------------------------------------------------
    # VERSCHULDUNG
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
    # LIQUIDITÄT
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
    # DIVIDENDE
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


    dividends_clean = (
        df["Dividende/Aktie"]
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .dropna()
    )


    if len(
        dividends_clean
    ) >= 2:

        if (
            dividends_clean.iloc[0]
            > dividends_clean.iloc[-1]
        ):

            score_dividend += 2


    score_dividend = min(
        score_dividend,
        5
    )


    # --------------------------------------------------------
    # HISTORISCHE BEWERTUNG
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
    # DCF SCORE
    # --------------------------------------------------------

    score_dcf = 0


    if pd.notna(dcf):

        dcf_diff = (
            (
                dcf
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


    # ========================================================
    # GESAMTSCORE
    # ========================================================

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
        max(
            normalized_score,
            0
        ),
        100
    )


    # ========================================================
    # RATING
    # ========================================================

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
    # ABSCHLIESSENDER HINWEIS
    # ========================================================

    st.divider()

    st.caption(
        "⚠️ Hinweis: Dieses Tool dient ausschließlich "
        "der Analyse und stellt keine Anlageberatung dar. "
        "Yahoo-Finance-Daten können verzögert, "
        "unvollständig oder fehlerhaft sein."
    )
```
