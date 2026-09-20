import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np


# ============================================================
# STREAMLIT KONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Mein personalisiertes Aktien-Bewertungs-Tool",
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
    try:
        if value is None or pd.isna(value):
            return np.nan
        return float(value)
    except Exception:
        return np.nan


def get_row_value(df, rows, column):
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


def calculate_multiple(price, value_per_share):
    if (
        pd.notna(price)
        and pd.notna(value_per_share)
        and value_per_share > 0
    ):
        return price / value_per_share

    return np.nan


def get_year_end_price(history, year):
    """
    Letzter verfügbarer Börsenkurs des jeweiligen Jahres.
    Dadurch wird nicht künstlich der 31.12. verwendet,
    wenn dieser kein Börsentag war.
    """

    if history is None or history.empty:
        return np.nan

    try:
        data = history.copy()

        data.index = pd.to_datetime(data.index)

        try:
            data.index = data.index.tz_localize(None)
        except Exception:
            pass

        year_data = data[
            data.index.year == year
        ]

        if year_data.empty:
            return np.nan

        close = year_data["Close"].dropna()

        if close.empty:
            return np.nan

        return float(close.iloc[-1])

    except Exception:
        return np.nan


def calculate_graham(eps, bvps):

    if (
        pd.notna(eps)
        and pd.notna(bvps)
        and eps > 0
        and bvps > 0
    ):
        return np.sqrt(
            22.5 * eps * bvps
        )

    return np.nan


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
    ):
        return np.nan

    growth = growth_rate / 100
    discount = wacc / 100
    terminal = terminal_growth / 100

    if discount <= terminal:
        return np.nan

    pv = 0
    forecast = []

    for year in range(1, years + 1):

        future_fcf = (
            fcf * (1 + growth) ** year
        )

        forecast.append(future_fcf)

        pv += (
            future_fcf
            / (1 + discount) ** year
        )

    terminal_fcf = (
        forecast[-1] * (1 + terminal)
    )

    terminal_value = (
        terminal_fcf
        / (discount - terminal)
    )

    terminal_pv = (
        terminal_value
        / (1 + discount) ** years
    )

    enterprise_value = (
        pv + terminal_pv
    )

    equity_value = (
        enterprise_value - net_debt
    )

    return equity_value / shares


def calculate_growth_score(values, maximum):

    values = (
        pd.Series(values)
        .replace([np.inf, -np.inf], np.nan)
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
        return maximum
    elif growth >= 30:
        return maximum * 0.9
    elif growth >= 15:
        return maximum * 0.8
    elif growth >= 5:
        return maximum * 0.7
    elif growth >= 0:
        return maximum * 0.55
    elif growth >= -10:
        return maximum * 0.35
    elif growth >= -25:
        return maximum * 0.15

    return 0


def calculate_valuation_score(
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
        (historical - current)
        / historical
    ) * 100

    if difference >= 30:
        return maximum
    elif difference >= 20:
        return maximum * 0.9
    elif difference >= 10:
        return maximum * 0.8
    elif difference >= 0:
        return maximum * 0.65
    elif difference >= -10:
        return maximum * 0.45
    elif difference >= -20:
        return maximum * 0.2

    return 0


# ============================================================
# FIRMEN- UND TICKER-ZUORDNUNGEN
# ============================================================

COMPANY_MAP = {

    # Deutschland
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

    # USA
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
    "NIKE": "NKE",
    "ADOBE": "ADBE",
    "BROADCOM": "AVGO",
    "INTEL": "INTC",
    "AMD": "AMD",

    # Japan
    "TOYOTA": "7203.T",
    "TOYOTA MOTOR": "7203.T",
    "TOYOTA MOTOR CORPORATION": "7203.T",
    "TOM": "7203.T",

    "HONDA": "7267.T",
    "NISSAN": "7201.T",

    # weitere bekannte japanische Aktien
    "SONY": "6758.T",
    "PANASONIC": "6752.T"
}


IDENTIFIER_MAP = {

    # InnoTec TSS
    "540510": "TSS.DE",
    "DE0005405104": "TSS.DE",

    # Toyota
    "853510": "7203.T",
    "JP3633400001": "7203.T",

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

    # Mercedes-Benz
    "710000": "MBG.DE",
    "DE0007100000": "MBG.DE",

    # Deutsche Telekom
    "555750": "DTE.DE",
    "DE0005557508": "DTE.DE",

    # Infineon
    "623100": "IFX.DE",
    "DE0006231004": "IFX.DE",

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

    if value in COMPANY_MAP:
        return COMPANY_MAP[value]

    if value in IDENTIFIER_MAP:
        return IDENTIFIER_MAP[value]

    if value in ["BRK.B", "BRK/B"]:
        return "BRK-B"

    if "." in value:
        return value

    return value


# ============================================================
# BRANCHEN-PEERS
#
# Diese Liste kann jederzeit erweitert/geändert werden.
# ============================================================

INDUSTRY_PEERS = {

    # Toyota / Automobil
    "7203.T": [
        "7267.T",   # Honda
        "7201.T",   # Nissan
        "005380.KS", # Hyundai
        "F",        # Ford
        "GM"        # General Motors
    ],

    # InnoTec TSS / Industrie
    "TSS.DE": [
        "S92.DE",
        "KSB3.DE",
        "MLP.DE"
    ],

    # Apple
    "AAPL": [
        "MSFT",
        "GOOGL",
        "META"
    ],

    # Microsoft
    "MSFT": [
        "AAPL",
        "GOOGL",
        "ORCL"
    ],

    # SAP
    "SAP.DE": [
        "ORCL",
        "CRM",
        "ADBE"
    ],

    # Pepsi
    "PEP": [
        "KO",
        "MNST",
        "KDP"
    ],

    # Coca-Cola
    "KO": [
        "PEP",
        "KDP",
        "MNST"
    ]
}


# ============================================================
# DATEN LADEN
#
# Wichtig:
# Das yf.Ticker-Objekt wird NICHT gecacht.
# ============================================================

@st.cache_data(
    ttl=1800,
    show_spinner=False
)
def load_data(ticker_symbol):

    ticker = yf.Ticker(ticker_symbol)

    history = ticker.history(
        period="6y",
        interval="1d",
        auto_adjust=False
    )

    income_stmt = ticker.income_stmt

    balance_sheet = ticker.balance_sheet

    cashflow = ticker.cashflow

    try:
        dividends = ticker.dividends
    except Exception:
        dividends = pd.Series(dtype=float)

    return {
        "history": history,
        "income_stmt": income_stmt,
        "balance_sheet": balance_sheet,
        "cashflow": cashflow,
        "dividends": dividends
    }


# ============================================================
# PEER-DATEN
# ============================================================

@st.cache_data(
    ttl=3600,
    show_spinner=False
)
def get_peer_metrics(peer_tickers):

    results = []

    for peer in peer_tickers:

        try:

            ticker = yf.Ticker(peer)

            financials = ticker.income_stmt
            balance = ticker.balance_sheet
            cashflow = ticker.cashflow

            if (
                financials is None
                or financials.empty
            ):
                continue

            latest_year = financials.columns[0]

            revenue = get_row_value(
                financials,
                [
                    "Total Revenue",
                    "Operating Revenue"
                ],
                latest_year
            )

            net_income = get_row_value(
                financials,
                [
                    "Net Income",
                    "Net Income Common Stockholders"
                ],
                latest_year
            )

            equity = get_row_value(
                balance,
                [
                    "Stockholders Equity",
                    "Common Stock Equity",
                    "Total Equity Gross Minority Interest"
                ],
                latest_year
            )

            fcf = get_row_value(
                cashflow,
                [
                    "Free Cash Flow"
                ],
                latest_year
            )

            shares = get_row_value(
                financials,
                [
                    "Diluted Average Shares",
                    "Basic Average Shares"
                ],
                latest_year
            )

            if pd.isna(shares):

                shares = get_row_value(
                    balance,
                    [
                        "Ordinary Shares Number",
                        "Share Issued"
                    ],
                    latest_year
                )

            if (
                pd.notna(net_income)
                and pd.notna(shares)
                and shares > 0
            ):
                eps = net_income / shares
            else:
                eps = np.nan

            if (
                pd.notna(equity)
                and pd.notna(shares)
                and shares > 0
            ):
                bvps = equity / shares
            else:
                bvps = np.nan

            if (
                pd.notna(fcf)
                and pd.notna(shares)
                and shares > 0
            ):
                fcf_ps = fcf / shares
            else:
                fcf_ps = np.nan

            if (
                pd.notna(revenue)
                and pd.notna(shares)
                and shares > 0
            ):
                revenue_ps = revenue / shares
            else:
                revenue_ps = np.nan

            # aktueller Kurs
            history = ticker.history(
                period="5d",
                interval="1d",
                auto_adjust=False
            )

            if (
                history is not None
                and not history.empty
            ):
                price = float(
                    history["Close"].dropna().iloc[-1]
                )
            else:
                price = np.nan

            kgv = calculate_multiple(
                price,
                eps
            )

            kcv = calculate_multiple(
                price,
                fcf_ps
            )

            kbv = calculate_multiple(
                price,
                bvps
            )

            kuv = calculate_multiple(
                price,
                revenue_ps
            )

            fcf_margin = (
                fcf / revenue * 100
                if (
                    pd.notna(fcf)
                    and pd.notna(revenue)
                    and revenue != 0
                )
                else np.nan
            )

            roe = (
                net_income / equity * 100
                if (
                    pd.notna(net_income)
                    and pd.notna(equity)
                    and equity > 0
                )
                else np.nan
            )

            debt = get_row_value(
                balance,
                [
                    "Total Debt",
                    "Total Debt And Capital Lease Obligation"
                ],
                latest_year
            )

            debt_equity = (
                debt / equity * 100
                if (
                    pd.notna(debt)
                    and pd.notna(equity)
                    and equity > 0
                )
                else np.nan
            )

            results.append({
                "Ticker": peer,
                "FCF-Marge (%)": fcf_margin,
                "ROE (%)": roe,
                "Debt/Equity (%)": debt_equity,
                "KGV": kgv,
                "KBV": kbv,
                "KCV": kcv,
                "KUV": kuv
            })

        except Exception:
            continue

    return pd.DataFrame(results)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙️ DCF-Annahmen")

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
# AKTIE EINGEBEN
# ============================================================

user_input = st.text_input(
    "🔎 Aktie suchen – Ticker, Firmenname, WKN oder ISIN",
    value="Toyota Motor"
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
            f"Lade Daten für {ticker_symbol}..."
        ):

            data = load_data(
                ticker_symbol
            )

    except Exception as e:

        error_text = str(e).lower()

        if (
            "too many requests" in error_text
            or "rate limit" in error_text
            or "429" in error_text
        ):

            st.error(
                "⚠️ Yahoo Finance hat die Anfrage "
                "wegen eines Rate-Limits abgelehnt."
            )

        else:

            st.error(
                "⚠️ Fehler beim Laden der Yahoo-Finance-Daten."
            )

            st.code(str(e))

        st.stop()


    history = data["history"]
    financials = data["income_stmt"]
    balance_sheet = data["balance_sheet"]
    cashflow = data["cashflow"]
    dividends = data["dividends"]

    ticker = yf.Ticker(
        ticker_symbol
    )


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

        st.stop()


    close = history["Close"].dropna()

    if close.empty:

        st.error(
            "⚠️ Keine Schlusskurse verfügbar."
        )

        st.stop()


    current_price = float(
        close.iloc[-1]
    )


    # ========================================================
    # UNTERNEHMENSINFO
    # ========================================================

    try:
        info = ticker.info
    except Exception:
        info = {}


    company_name = info.get(
        "longName",
        info.get(
            "shortName",
            ticker_symbol
        )
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
            "⚠️ Keine ausreichenden Finanzdaten verfügbar."
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

        year_number = pd.Timestamp(
            year
        ).year


        revenue = get_row_value(
            financials,
            [
                "Total Revenue",
                "Operating Revenue"
            ],
            year
        )


        net_income = get_row_value(
            financials,
            [
                "Net Income",
                "Net Income Common Stockholders"
            ],
            year
        )


        equity = get_row_value(
            balance_sheet,
            [
                "Stockholders Equity",
                "Common Stock Equity",
                "Total Equity Gross Minority Interest"
            ],
            year
        )


        debt = get_row_value(
            balance_sheet,
            [
                "Total Debt",
                "Total Debt And Capital Lease Obligation"
            ],
            year
        )


        cash = get_row_value(
            balance_sheet,
            [
                "Cash And Cash Equivalents",
                "Cash Cash Equivalents And Short Term Investments"
            ],
            year
        )


        receivables = get_row_value(
            balance_sheet,
            [
                "Receivables",
                "Accounts Receivable"
            ],
            year
        )


        current_assets = get_row_value(
            balance_sheet,
            [
                "Current Assets"
            ],
            year
        )


        current_liabilities = get_row_value(
            balance_sheet,
            [
                "Current Liabilities"
            ],
            year
        )


        fcf = get_row_value(
            cashflow,
            [
                "Free Cash Flow"
            ],
            year
        )


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
                    operating_cf + capex
                )


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


        # EPS
        if (
            pd.notna(net_income)
            and pd.notna(shares)
            and shares > 0
        ):
            eps = net_income / shares
        else:
            eps = np.nan


        # Buchwert/Aktie
        if (
            pd.notna(equity)
            and pd.notna(shares)
            and shares > 0
        ):
            bvps = equity / shares
        else:
            bvps = np.nan


        # FCF/Aktie
        if (
            pd.notna(fcf)
            and pd.notna(shares)
            and shares > 0
        ):
            fcf_ps = fcf / shares
        else:
            fcf_ps = np.nan


        # Umsatz/Aktie
        if (
            pd.notna(revenue)
            and pd.notna(shares)
            and shares > 0
        ):
            revenue_ps = revenue / shares
        else:
            revenue_ps = np.nan


        # ====================================================
        # DIVIDENDE
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
                        divs.index.tz_localize(None)
                    )
                except Exception:
                    pass

                year_dividends = divs[
                    divs.index.year == year_number
                ]

                if not year_dividends.empty:

                    dividend_ps = float(
                        year_dividends.sum()
                    )

            except Exception:

                dividend_ps = 0.0


        # ====================================================
        # AUSSCHÜTTUNGSQUOTEN
        # ====================================================

        if (
            pd.notna(eps)
            and eps > 0
        ):
            payout_1 = (
                dividend_ps / eps
            ) * 100
        else:
            payout_1 = np.nan


        if (
            pd.notna(fcf_ps)
            and fcf_ps > 0
        ):
            payout_2 = (
                dividend_ps / fcf_ps
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
                cash / current_liabilities
            ) * 100

            liq2 = (
                (cash + receivables)
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
                fcf / revenue
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
                net_income / equity
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
                debt / equity
            ) * 100
        else:
            debt_equity = np.nan


        # ====================================================
        # JAHRESENDKURS
        # ====================================================

        year_end_price = get_year_end_price(
            history,
            year_number
        )


        # ====================================================
        # HISTORISCHE MULTIPLES
        # ====================================================

        kgv = calculate_multiple(
            year_end_price,
            eps
        )

        kbv = calculate_multiple(
            year_end_price,
            bvps
        )

        kcv = calculate_multiple(
            year_end_price,
            fcf_ps
        )

        kuv = calculate_multiple(
            year_end_price,
            revenue_ps
        )


        rows.append({

            "Jahr": str(year_number),

            "Umsatz (Mrd.)":
                revenue / 1e9
                if pd.notna(revenue)
                else np.nan,

            "Eigenkapital (Mrd.)":
                equity / 1e9
                if pd.notna(equity)
                else np.nan,

            "Free Cashflow (Mrd.)":
                fcf / 1e9
                if pd.notna(fcf)
                else np.nan,

            "EPS": eps,

            "Jahresendkurs":
                year_end_price,

            "Buchwert/Aktie":
                bvps,

            "Umsatz/Aktie":
                revenue_ps,

            "Dividende/Aktie":
                dividend_ps,

            "Free Cashflow/Aktie":
                fcf_ps,

            "Ausschüttungsquote 1 (%)":
                payout_1,

            "Ausschüttungsquote 2 (%)":
                payout_2,

            "Liquidität 1 (%)":
                liq1,

            "Liquidität 2 (%)":
                liq2,

            "Liquidität 3 (%)":
                liq3,

            "FCF-Marge (%)":
                fcf_margin,

            "ROE (%)":
                roe,

            "Debt/Equity (%)":
                debt_equity,

            "KGV":
                kgv,

            "KBV":
                kbv,

            "KCV":
                kcv,

            "KUV":
                kuv
        })


    df = pd.DataFrame(rows)


    # ========================================================
    # TABELLE 1
    # ========================================================

    st.subheader(
        "1️⃣ Umsatz, Eigenkapital, Free Cashflow, EPS und Kurs"
    )

    table1 = df[
        [
            "Jahr",
            "Umsatz (Mrd.)",
            "Eigenkapital (Mrd.)",
            "Free Cashflow (Mrd.)",
            "EPS",
            "Jahresendkurs"
        ]
    ]

    st.dataframe(
        table1.style.format(
            precision=2,
            na_rep="-"
        ),
        use_container_width=True
    )


    # ========================================================
    # TABELLE 2
    # ========================================================

    st.subheader(
        "2️⃣ Werte je Aktie und Dividende"
    )

    table2 = df[
        [
            "Jahr",
            "Buchwert/Aktie",
            "Umsatz/Aktie",
            "Dividende/Aktie",
            "Free Cashflow/Aktie"
        ]
    ]

    st.dataframe(
        table2.style.format(
            precision=2,
            na_rep="-"
        ),
        use_container_width=True
    )


    # ========================================================
    # TABELLE 3
    # ========================================================

    st.subheader(
        "3️⃣ Ausschüttungsquoten"
    )

    table3 = df[
        [
            "Jahr",
            "Ausschüttungsquote 1 (%)",
            "Ausschüttungsquote 2 (%)"
        ]
    ]

    st.dataframe(
        table3.style.format(
            precision=2,
            na_rep="-"
        ),
        use_container_width=True
    )


    # ========================================================
    # TABELLE 4
    # ========================================================

    st.subheader(
        "4️⃣ Liquidität"
    )

    table4 = df[
        [
            "Jahr",
            "Liquidität 1 (%)",
            "Liquidität 2 (%)",
            "Liquidität 3 (%)"
        ]
    ]

    st.dataframe(
        table4.style.format(
            precision=2,
            na_rep="-"
        ),
        use_container_width=True
    )


    # ========================================================
    # BRANCHENVERGLEICH
    # ========================================================

    st.subheader(
        "5️⃣ Profitabilität und Verschuldung – Branchenvergleich"
    )


    # Peer-Unternehmen bestimmen

    peer_tickers = INDUSTRY_PEERS.get(
        ticker_symbol,
        []
    )


    # Möglichkeit zur manuellen Anpassung
    default_peers = ", ".join(
        peer_tickers
    )


    peer_input = st.text_input(
        "Vergleichsunternehmen für den Branchenvergleich "
        "(Yahoo-Ticker, durch Komma getrennt)",
        value=default_peers,
        help=(
            "Die Unternehmen werden für den Durchschnitt "
            "der Branche verwendet. "
            "Beispiel Toyota: 7267.T, 7201.T, 005380.KS, F, GM"
        )
    )


    peer_tickers = [
        x.strip().upper()
        for x in peer_input.split(",")
        if x.strip()
    ]


    if peer_tickers:

        with st.spinner(
            "Branchenvergleich wird geladen..."
        ):

            peer_df = get_peer_metrics(
                tuple(peer_tickers)
            )

    else:

        peer_df = pd.DataFrame()


    # ========================================================
    # BRANCHENDURCHSCHNITT
    # ========================================================

    if (
        peer_df is not None
        and not peer_df.empty
    ):

        industry_avg = {

            "FCF-Marge (%)":
                peer_df["FCF-Marge (%)"]
                .replace(
                    [np.inf, -np.inf],
                    np.nan
                )
                .mean(),

            "ROE (%)":
                peer_df["ROE (%)"]
                .replace(
                    [np.inf, -np.inf],
                    np.nan
                )
                .mean(),

            "Debt/Equity (%)":
                peer_df["Debt/Equity (%)"]
                .replace(
                    [np.inf, -np.inf],
                    np.nan
                )
                .mean()
        }

    else:

        industry_avg = {
            "FCF-Marge (%)": np.nan,
            "ROE (%)": np.nan,
            "Debt/Equity (%)": np.nan
        }


    # ========================================================
    # TABELLE 5
    # ========================================================

    table5 = df[
        [
            "Jahr",
            "FCF-Marge (%)",
            "ROE (%)",
            "Debt/Equity (%)"
        ]
    ].copy()


    # Branchen-Durchschnitt als zusätzliche Spalten

    table5[
        "Branche Ø FCF-Marge (%)"
    ] = industry_avg[
        "FCF-Marge (%)"
    ]


    table5[
        "Branche Ø ROE (%)"
    ] = industry_avg[
        "ROE (%)"
    ]


    table5[
        "Branche Ø Debt/Equity (%)"
    ] = industry_avg[
        "Debt/Equity (%)"
    ]


    st.dataframe(
        table5.style.format(
            precision=2,
            na_rep="-"
        ),
        use_container_width=True
    )


    if (
        peer_df is not None
        and not peer_df.empty
    ):

        st.caption(
            "Branchen-Durchschnitt berechnet aus: "
            + ", ".join(peer_tickers)
        )

    else:

        st.warning(
            "Für den Branchenvergleich konnten keine "
            "ausreichenden Vergleichsdaten geladen werden."
        )


    # ========================================================
    # TABELLE 6
    # ========================================================

    st.subheader(
        "6️⃣ Historische Bewertung – KGV, KBV, KCV und KUV"
    )


    table6 = df[
        [
            "Jahr",
            "KGV",
            "KBV",
            "KCV",
            "KUV"
        ]
    ].copy()


    # Optional zusätzlich Branchenvergleich
    # für Bewertung

    if (
        peer_df is not None
        and not peer_df.empty
    ):

        table6[
            "Branche Ø KGV"
        ] = (
            peer_df["KGV"]
            .replace(
                [np.inf, -np.inf],
                np.nan
            )
            .mean()
        )

        table6[
            "Branche Ø KBV"
        ] = (
            peer_df["KBV"]
            .replace(
                [np.inf, -np.inf],
                np.nan
            )
            .mean()
        )

        table6[
            "Branche Ø KCV"
        ] = (
            peer_df["KCV"]
            .replace(
                [np.inf, -np.inf],
                np.nan
            )
            .mean()
        )

        table6[
            "Branche Ø KUV"
        ] = (
            peer_df["KUV"]
            .replace(
                [np.inf, -np.inf],
                np.nan
            )
            .mean()
        )


    st.dataframe(
        table6.style.format(
            precision=2,
            na_rep="-"
        ),
        use_container_width=True
    )


    # ========================================================
    # AKTUELLE BEWERTUNG
    # ========================================================

    st.subheader(
        "🔎 Aktuelle Bewertung"
    )


    latest = df.iloc[0]


    current_eps = latest["EPS"]
    current_bvps = latest["Buchwert/Aktie"]
    current_fcf_ps = latest["Free Cashflow/Aktie"]
    current_revenue_ps = latest["Umsatz/Aktie"]


    current_kgv = calculate_multiple(
        current_price,
        current_eps
    )

    current_kbv = calculate_multiple(
        current_price,
        current_bvps
    )

    current_kcv = calculate_multiple(
        current_price,
        current_fcf_ps
    )

    current_kuv = calculate_multiple(
        current_price,
        current_revenue_ps
    )


    c1, c2, c3, c4 = st.columns(4)


    with c1:
        st.metric(
            "Aktuelles KGV",
            f"{current_kgv:.2f}"
            if pd.notna(current_kgv)
            else "-"
        )


    with c2:
        st.metric(
            "Aktuelles KBV",
            f"{current_kbv:.2f}"
            if pd.notna(current_kbv)
            else "-"
        )


    with c3:
        st.metric(
            "Aktuelles KCV",
            f"{current_kcv:.2f}"
            if pd.notna(current_kcv)
            else "-"
        )


    with c4:
        st.metric(
            "Aktuelles KUV",
            f"{current_kuv:.2f}"
            if pd.notna(current_kuv)
            else "-"
        )


    # ========================================================
    # GRAHAM
    # ========================================================

    st.subheader(
        "📐 Bewertung nach Benjamin Graham"
    )


    avg_eps = df["EPS"].mean()
    avg_bvps = df["Buchwert/Aktie"].mean()


    graham = calculate_graham(
        avg_eps,
        avg_bvps
    )


    if pd.notna(graham):

        difference = (
            (graham - current_price)
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

    else:

        st.warning(
            "Graham-Wert kann nicht berechnet werden, "
            "weil EPS oder Buchwert nicht positiv sind."
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
                debt_now - cash_now
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
            (dcf - current_price)
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
            "DCF konnte nicht berechnet werden."
        )


    # ========================================================
    # DIVIDENDENANALYSE
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
    ]


    st.dataframe(
        dividend_table.style.format(
            precision=2,
            na_rep="-"
        ),
        use_container_width=True
    )


    # ========================================================
    # FUNDAMENTALER SCORE
    # ========================================================

    st.subheader(
        "🏆 Fundamentaler Score"
    )


    score_revenue = calculate_growth_score(
        df["Umsatz (Mrd.)"],
        10
    )

    score_eps = calculate_growth_score(
        df["EPS"],
        10
    )

    score_fcf = calculate_growth_score(
        df["Free Cashflow (Mrd.)"],
        10
    )


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


    roe = latest["ROE (%)"]


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


    if len(dividends_clean) >= 2:

        if (
            dividends_clean.iloc[0]
            > dividends_clean.iloc[-1]
        ):
            score_dividend += 2


    score_dividend = min(
        score_dividend,
        5
    )


    score_historical = 0


    score_historical += calculate_valuation_score(
        current_kgv,
        df["KGV"].replace(
            [np.inf, -np.inf],
            np.nan
        ).mean(),
        2.5
    )


    score_historical += calculate_valuation_score(
        current_kcv,
        df["KCV"].replace(
            [np.inf, -np.inf],
            np.nan
        ).mean(),
        2.5
    )


    score_historical += calculate_valuation_score(
        current_kbv,
        df["KBV"].replace(
            [np.inf, -np.inf],
            np.nan
        ).mean(),
        2.5
    )


    score_historical += calculate_valuation_score(
        current_kuv,
        df["KUV"].replace(
            [np.inf, -np.inf],
            np.nan
        ).mean(),
        2.5
    )


    score_dcf = 0


    if pd.notna(dcf):

        dcf_diff = (
            (dcf - current_price)
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
        total_score / max_score
    ) * 100


    normalized_score = min(
        max(
            normalized_score,
            0
        ),
        100
    )


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
    # HINWEIS
    # ========================================================

    st.divider()

    st.caption(
        "⚠️ Hinweis: Dieses Tool dient ausschließlich "
        "der Analyse und stellt keine Anlageberatung dar. "
        "Yahoo-Finance-Daten können verzögert, "
        "unvollständig oder fehlerhaft sein."
    )
