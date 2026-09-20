import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np


# ============================================================
# STREAMLIT KONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Aktienanalyse",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Aktienanalyse")
st.caption(
    "Fundamentalanalyse mit historischen Kennzahlen, Bewertung, "
    "Dividenden, Liquidität und Branchenvergleich"
)


# ============================================================
# HILFSFUNKTIONEN
# ============================================================

def safe_float(value):
    try:
        if value is None:
            return np.nan

        if isinstance(value, pd.Series):
            if len(value) == 0:
                return np.nan
            value = value.iloc[0]

        if isinstance(value, pd.DataFrame):
            if value.empty:
                return np.nan
            value = value.iloc[0, 0]

        result = float(value)

        if np.isfinite(result):
            return result

        return np.nan

    except Exception:
        return np.nan


def get_row_value(df, row_names, column):
    if df is None or df.empty:
        return np.nan

    if isinstance(row_names, str):
        row_names = [row_names]

    for row_name in row_names:
        if row_name in df.index:
            try:
                return safe_float(df.loc[row_name, column])
            except Exception:
                pass

    return np.nan


def calculate_multiple(price, fundamental_value):
    price = safe_float(price)
    fundamental_value = safe_float(fundamental_value)

    if (
        pd.isna(price)
        or pd.isna(fundamental_value)
        or fundamental_value == 0
    ):
        return np.nan

    return price / fundamental_value


def get_year_end_price(history, year):
    """
    Ermittelt den letzten verfügbaren Börsenkurs
    des jeweiligen Kalenderjahres.
    """

    if history is None or history.empty:
        return np.nan

    try:
        hist = history.copy()

        if not isinstance(hist.index, pd.DatetimeIndex):
            hist.index = pd.to_datetime(hist.index)

        year_data = hist[hist.index.year == int(year)]

        if year_data.empty:
            return np.nan

        return safe_float(year_data["Close"].iloc[-1])

    except Exception:
        return np.nan


def calculate_graham(avg_eps, avg_book_value):
    avg_eps = safe_float(avg_eps)
    avg_book_value = safe_float(avg_book_value)

    if (
        pd.isna(avg_eps)
        or pd.isna(avg_book_value)
        or avg_eps <= 0
        or avg_book_value <= 0
    ):
        return np.nan

    return np.sqrt(22.5 * avg_eps * avg_book_value)


def calculate_dcf(
    current_fcf,
    growth_rate,
    wacc,
    terminal_growth,
    forecast_years
):
    current_fcf = safe_float(current_fcf)

    if (
        pd.isna(current_fcf)
        or current_fcf <= 0
        or wacc <= terminal_growth
    ):
        return np.nan

    try:
        value = 0

        for year in range(1, forecast_years + 1):
            future_fcf = current_fcf * ((1 + growth_rate) ** year)
            present_value = future_fcf / ((1 + wacc) ** year)
            value += present_value

        terminal_fcf = current_fcf * ((1 + growth_rate) ** forecast_years)

        terminal_value = (
            terminal_fcf * (1 + terminal_growth)
            / (wacc - terminal_growth)
        )

        terminal_present_value = (
            terminal_value
            / ((1 + wacc) ** forecast_years)
        )

        value += terminal_present_value

        return value

    except Exception:
        return np.nan


def calculate_growth_score(growth):
    if pd.isna(growth):
        return 0

    if growth >= 15:
        return 5
    elif growth >= 10:
        return 4
    elif growth >= 5:
        return 3
    elif growth >= 0:
        return 2
    else:
        return 1


def calculate_valuation_score(value):
    if pd.isna(value):
        return 0

    if value >= 80:
        return 5
    elif value >= 60:
        return 4
    elif value >= 40:
        return 3
    elif value >= 20:
        return 2
    else:
        return 1


# ============================================================
# LIQUIDITÄTS-AMPELFUNKTION
# ============================================================

def color_liquidity(value, liquidity_type):
    """
    Bewertung:

    Liquidität 1:
        < 20 %       = schwach
        20–30 %      = solide
        > 30 %       = stark

    Liquidität 2:
        < 100 %      = schwach
        100–120 %    = solide
        > 120 %      = stark

    Liquidität 3:
        < 120 %      = schwach
        120–150 %    = solide
        > 150 %      = stark
    """

    if pd.isna(value):
        return ""

    value = float(value)

    if liquidity_type == "L1":

        if value < 20:
            return (
                "background-color: #ffcccc;"
                "color: #990000;"
                "font-weight: bold;"
            )

        elif value <= 30:
            return (
                "background-color: #fff2cc;"
                "color: #7f6000;"
                "font-weight: bold;"
            )

        else:
            return (
                "background-color: #ccffcc;"
                "color: #006100;"
                "font-weight: bold;"
            )

    elif liquidity_type == "L2":

        if value < 100:
            return (
                "background-color: #ffcccc;"
                "color: #990000;"
                "font-weight: bold;"
            )

        elif value <= 120:
            return (
                "background-color: #fff2cc;"
                "color: #7f6000;"
                "font-weight: bold;"
            )

        else:
            return (
                "background-color: #ccffcc;"
                "color: #006100;"
                "font-weight: bold;"
            )

    elif liquidity_type == "L3":

        if value < 120:
            return (
                "background-color: #ffcccc;"
                "color: #990000;"
                "font-weight: bold;"
            )

        elif value <= 150:
            return (
                "background-color: #fff2cc;"
                "color: #7f6000;"
                "font-weight: bold;"
            )

        else:
            return (
                "background-color: #ccffcc;"
                "color: #006100;"
                "font-weight: bold;"
            )

    return ""


# ============================================================
# UNTERNEHMEN / TICKER
# ============================================================

COMPANY_MAP = {

    # Deutschland
    "SAP": "SAP.DE",
    "SIEMENS": "SIE.DE",
    "ALLIANZ": "ALV.DE",
    "BASF": "BAS.DE",
    "BMW": "BMW.DE",
    "MERCEDES": "MBG.DE",
    "MERCEDES-BENZ": "MBG.DE",
    "VOLKSWAGEN": "VOW3.DE",
    "VW": "VOW3.DE",
    "ADIDAS": "ADS.DE",
    "DEUTSCHE BANK": "DBK.DE",
    "DEUTSCHE TELEKOM": "DTE.DE",
    "MUNICH RE": "MUV2.DE",
    "MÜNCHENER RÜCK": "MUV2.DE",
    "HENKEL": "HEN3.DE",
    "COVESTRO": "1COV.DE",

    # InnoTec TSS
    "INNOTEC TSS": "TSS.DE",
    "INNOTEC": "TSS.DE",
    "TSS": "TSS.DE",

    # USA
    "APPLE": "AAPL",
    "MICROSOFT": "MSFT",
    "ALPHABET": "GOOGL",
    "GOOGLE": "GOOGL",
    "AMAZON": "AMZN",
    "META": "META",
    "TESLA": "TSLA",
    "COCA COLA": "KO",
    "COCA-COLA": "KO",
    "PEPSI": "PEP",
    "JOHNSON & JOHNSON": "JNJ",
    "JOHNSON AND JOHNSON": "JNJ",
    "MCDONALDS": "MCD",
    "MCDONALD'S": "MCD",
    "NIKE": "NKE",
    "WALMART": "WMT",
    "PROCTER & GAMBLE": "PG",
    "PROCTER AND GAMBLE": "PG",
    "FORD": "F",
    "GENERAL MOTORS": "GM",

    # Japan
    "TOYOTA": "7203.T",
    "TOYOTA MOTOR": "7203.T",
    "TOYOTA MOTOR CORPORATION": "7203.T",
    "TOM": "7203.T",

    # weitere
    "SONY": "6758.T",
    "HONDA": "7267.T",
    "NISSAN": "7201.T",
}


# ============================================================
# WKN / ISIN
# ============================================================

IDENTIFIER_MAP = {

    # InnoTec TSS
    "540510": "TSS.DE",
    "DE0005405104": "TSS.DE",

    # Toyota
    "853510": "7203.T",
    "JP3633400001": "7203.T",

    # Apple
    "865985": "AAPL",
    "US0378331005": "AAPL",

    # Microsoft
    "870747": "MSFT",
    "US5949181045": "MSFT",

    # Alphabet
    "A14Y6F": "GOOGL",
    "US02079K3059": "GOOGL",

    # Amazon
    "906866": "AMZN",
    "US0231351067": "AMZN",

    # Coca Cola
    "850663": "KO",
    "US1912161007": "KO",

    # Pepsi
    "851995": "PEP",
    "US7134481081": "PEP",
}


def normalize_input(user_input):
    value = user_input.strip()

    if not value:
        return None

    upper = value.upper()

    # Direkter Treffer Firmenname
    if upper in COMPANY_MAP:
        return COMPANY_MAP[upper]

    # WKN / ISIN
    if upper in IDENTIFIER_MAP:
        return IDENTIFIER_MAP[upper]

    # Direkter Yahoo-Ticker
    return upper


# ============================================================
# BRANCHEN-PEERS
# ============================================================

INDUSTRY_PEERS = {

    "7203.T": [
        "7267.T",
        "7201.T",
        "005380.KS",
        "F",
        "GM"
    ],

    "TSS.DE": [
        "S92.DE",
        "KSB3.DE",
        "MLP.DE"
    ],

    "AAPL": [
        "MSFT",
        "GOOGL",
        "META"
    ],

    "MSFT": [
        "AAPL",
        "GOOGL",
        "ORCL"
    ],

    "SAP.DE": [
        "ORCL",
        "CRM",
        "ADBE"
    ],

    "PEP": [
        "KO",
        "MNST",
        "KDP"
    ],

    "KO": [
        "PEP",
        "KDP",
        "MNST"
    ]
}


# ============================================================
# DATEN LADEN
# ============================================================

@st.cache_data(ttl=1800)
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
    dividends = ticker.dividends

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

@st.cache_data(ttl=3600)
def get_peer_metrics(peer_tickers):

    results = []

    for peer in peer_tickers:

        try:

            ticker = yf.Ticker(peer)

            income = ticker.income_stmt
            balance = ticker.balance_sheet
            cashflow = ticker.cashflow

            if income is None or income.empty:
                continue

            if balance is None or balance.empty:
                continue

            latest_year = income.columns[0]

            revenue = get_row_value(
                income,
                ["Total Revenue", "Operating Revenue"],
                latest_year
            )

            net_income = get_row_value(
                income,
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

            debt = get_row_value(
                balance,
                [
                    "Total Debt",
                    "Total Debt And Capital Lease Obligation"
                ],
                latest_year
            )

            if cashflow is not None and not cashflow.empty:

                fcf = get_row_value(
                    cashflow,
                    ["Free Cash Flow"],
                    latest_year
                )

                if pd.isna(fcf):

                    operating_cf = get_row_value(
                        cashflow,
                        [
                            "Operating Cash Flow",
                            "Total Cash From Operating Activities"
                        ],
                        latest_year
                    )

                    capex = get_row_value(
                        cashflow,
                        [
                            "Capital Expenditure",
                            "Capital Expenditures"
                        ],
                        latest_year
                    )

                    if not pd.isna(operating_cf):

                        if pd.isna(capex):
                            capex = 0

                        fcf = operating_cf + capex

            else:
                fcf = np.nan

            shares = get_row_value(
                income,
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

            price = np.nan

            try:
                hist = ticker.history(
                    period="5d",
                    interval="1d",
                    auto_adjust=False
                )

                if not hist.empty:
                    price = safe_float(hist["Close"].iloc[-1])

            except Exception:
                pass

            eps = (
                net_income / shares
                if (
                    not pd.isna(net_income)
                    and not pd.isna(shares)
                    and shares != 0
                )
                else np.nan
            )

            book_value = (
                equity / shares
                if (
                    not pd.isna(equity)
                    and not pd.isna(shares)
                    and shares != 0
                )
                else np.nan
            )

            fcf_per_share = (
                fcf / shares
                if (
                    not pd.isna(fcf)
                    and not pd.isna(shares)
                    and shares != 0
                )
                else np.nan
            )

            revenue_per_share = (
                revenue / shares
                if (
                    not pd.isna(revenue)
                    and not pd.isna(shares)
                    and shares != 0
                )
                else np.nan
            )

            fcf_margin = (
                fcf / revenue * 100
                if (
                    not pd.isna(fcf)
                    and not pd.isna(revenue)
                    and revenue != 0
                )
                else np.nan
            )

            roe = (
                net_income / equity * 100
                if (
                    not pd.isna(net_income)
                    and not pd.isna(equity)
                    and equity != 0
                )
                else np.nan
            )

            debt_equity = (
                debt / equity * 100
                if (
                    not pd.isna(debt)
                    and not pd.isna(equity)
                    and equity != 0
                )
                else np.nan
            )

            kgv = calculate_multiple(price, eps)
            kbv = calculate_multiple(price, book_value)
            kcv = calculate_multiple(price, fcf_per_share)
            kuv = calculate_multiple(price, revenue_per_share)

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

    if not results:
        return pd.DataFrame()

    return pd.DataFrame(results)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙️ DCF-Annahmen")

forecast_years = st.sidebar.slider(
    "Prognosejahre",
    min_value=3,
    max_value=10,
    value=5
)

fcf_growth = st.sidebar.number_input(
    "FCF-Wachstum (%)",
    min_value=-50.0,
    max_value=100.0,
    value=5.0,
    step=0.5
) / 100

wacc = st.sidebar.number_input(
    "WACC (%)",
    min_value=1.0,
    max_value=30.0,
    value=8.0,
    step=0.5
) / 100

terminal_growth = st.sidebar.number_input(
    "Terminal-Wachstum (%)",
    min_value=0.0,
    max_value=10.0,
    value=2.0,
    step=0.5
) / 100

margin_of_safety = st.sidebar.number_input(
    "Sicherheitsmarge (%)",
    min_value=0.0,
    max_value=50.0,
    value=20.0,
    step=5.0
) / 100


# ============================================================
# AKTIENSUCHE
# ============================================================

user_input = st.text_input(
    "🔎 Aktie suchen – Ticker, Firmenname, WKN oder ISIN",
    value="Toyota Motor"
)

ticker_symbol = normalize_input(user_input)

if not ticker_symbol:
    st.warning("Bitte eine Aktie eingeben.")
    st.stop()


# ============================================================
# DATEN LADEN
# ============================================================

try:

    with st.spinner("Lade Finanzdaten von Yahoo Finance ..."):
        data = load_data(ticker_symbol)

except Exception as e:

    st.error(
        "Die Daten konnten nicht geladen werden. "
        "Yahoo Finance könnte momentan eine Anfragebegrenzung aktiv haben."
    )

    st.exception(e)
    st.stop()


history = data["history"]
income_stmt = data["income_stmt"]
balance_sheet = data["balance_sheet"]
cashflow = data["cashflow"]
dividends = data["dividends"]


if income_stmt is None or income_stmt.empty:
    st.error("Keine Gewinn- und Verlustrechnung verfügbar.")
    st.stop()

if balance_sheet is None or balance_sheet.empty:
    st.error("Keine Bilanzdaten verfügbar.")
    st.stop()


# ============================================================
# TICKER-INFORMATIONEN
# ============================================================

ticker = yf.Ticker(ticker_symbol)

try:

    info = ticker.info

except Exception:

    info = {}


company_name = info.get(
    "longName",
    info.get("shortName", ticker_symbol)
)

exchange = info.get("exchange", "–")
sector = info.get("sector", "–")
industry = info.get("industry", "–")


# ============================================================
# AKTUELLE KURSDATEN
# ============================================================

current_price = np.nan

try:

    if history is not None and not history.empty:
        current_price = safe_float(
            history["Close"].iloc[-1]
        )

except Exception:
    pass


# ============================================================
# KOPFBEREICH
# ============================================================

st.header(company_name)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Aktueller Kurs",
        (
            f"{current_price:.2f}"
            if not pd.isna(current_price)
            else "–"
        )
    )

with col2:
    st.metric("Yahoo-Ticker", ticker_symbol)

with col3:
    st.metric("Börse", exchange)

with col4:
    st.metric("Branche", industry)


if sector != "–":
    st.caption(f"Sektor: {sector}")


# ============================================================
# HISTORISCHE JAHRE
# ============================================================

financial_years = list(income_stmt.columns[:5])

if not financial_years:
    st.error("Keine historischen Geschäftsjahre verfügbar.")
    st.stop()


# ============================================================
# HISTORISCHE DATEN
# ============================================================

historical_rows = []
share_rows = []
payout_rows = []
liquidity_rows = []
quality_rows = []
valuation_rows = []


for year_column in financial_years:

    try:
        year = pd.Timestamp(year_column).year
    except Exception:
        continue


    # --------------------------------------------------------
    # GuV
    # --------------------------------------------------------

    revenue = get_row_value(
        income_stmt,
        [
            "Total Revenue",
            "Operating Revenue"
        ],
        year_column
    )

    net_income = get_row_value(
        income_stmt,
        [
            "Net Income",
            "Net Income Common Stockholders"
        ],
        year_column
    )


    # --------------------------------------------------------
    # Bilanz
    # --------------------------------------------------------

    equity = get_row_value(
        balance_sheet,
        [
            "Stockholders Equity",
            "Common Stock Equity",
            "Total Equity Gross Minority Interest"
        ],
        year_column
    )

    debt = get_row_value(
        balance_sheet,
        [
            "Total Debt",
            "Total Debt And Capital Lease Obligation"
        ],
        year_column
    )

    cash = get_row_value(
        balance_sheet,
        [
            "Cash And Cash Equivalents",
            "Cash Cash Equivalents And Short Term Investments"
        ],
        year_column
    )

    receivables = get_row_value(
        balance_sheet,
        [
            "Receivables",
            "Accounts Receivable"
        ],
        year_column
    )

    current_assets = get_row_value(
        balance_sheet,
        [
            "Current Assets",
            "Total Current Assets"
        ],
        year_column
    )

    current_liabilities = get_row_value(
        balance_sheet,
        [
            "Current Liabilities",
            "Total Current Liabilities"
        ],
        year_column
    )


    # --------------------------------------------------------
    # Free Cashflow
    # --------------------------------------------------------

    fcf = get_row_value(
        cashflow,
        [
            "Free Cash Flow"
        ],
        year_column
    )

    if pd.isna(fcf):

        operating_cf = get_row_value(
            cashflow,
            [
                "Operating Cash Flow",
                "Total Cash From Operating Activities"
            ],
            year_column
        )

        capex = get_row_value(
            cashflow,
            [
                "Capital Expenditure",
                "Capital Expenditures"
            ],
            year_column
        )

        if not pd.isna(operating_cf):

            if pd.isna(capex):
                capex = 0

            fcf = operating_cf + capex


    # --------------------------------------------------------
    # Aktienanzahl
    # --------------------------------------------------------

    shares = get_row_value(
        income_stmt,
        [
            "Diluted Average Shares",
            "Basic Average Shares"
        ],
        year_column
    )

    if pd.isna(shares):

        shares = get_row_value(
            balance_sheet,
            [
                "Ordinary Shares Number",
                "Share Issued"
            ],
            year_column
        )


    # --------------------------------------------------------
    # EPS
    # --------------------------------------------------------

    eps = np.nan

    if (
        not pd.isna(net_income)
        and not pd.isna(shares)
        and shares != 0
    ):
        eps = net_income / shares


    # --------------------------------------------------------
    # Kennzahlen je Aktie
    # --------------------------------------------------------

    book_value_per_share = np.nan
    revenue_per_share = np.nan
    fcf_per_share = np.nan

    if (
        not pd.isna(equity)
        and not pd.isna(shares)
        and shares != 0
    ):
        book_value_per_share = equity / shares

    if (
        not pd.isna(revenue)
        and not pd.isna(shares)
        and shares != 0
    ):
        revenue_per_share = revenue / shares

    if (
        not pd.isna(fcf)
        and not pd.isna(shares)
        and shares != 0
    ):
        fcf_per_share = fcf / shares


    # --------------------------------------------------------
    # Dividende
    # --------------------------------------------------------

    dividend_per_share = np.nan

    try:

        if dividends is not None and not dividends.empty:

            divs = dividends.copy()

            if not isinstance(divs.index, pd.DatetimeIndex):
                divs.index = pd.to_datetime(divs.index)

            year_dividends = divs[
                divs.index.year == year
            ]

            if not year_dividends.empty:
                dividend_per_share = safe_float(
                    year_dividends.sum()
                )

    except Exception:
        pass


    # --------------------------------------------------------
    # Ausschüttungsquoten
    # --------------------------------------------------------

    payout_eps = np.nan
    payout_fcf = np.nan

    if (
        not pd.isna(dividend_per_share)
        and not pd.isna(eps)
        and eps != 0
    ):
        payout_eps = (
            dividend_per_share / eps * 100
        )

    if (
        not pd.isna(dividend_per_share)
        and not pd.isna(fcf_per_share)
        and fcf_per_share != 0
    ):
        payout_fcf = (
            dividend_per_share
            / fcf_per_share
            * 100
        )


    # --------------------------------------------------------
    # Liquidität
    # --------------------------------------------------------

    liquidity_1 = np.nan
    liquidity_2 = np.nan
    liquidity_3 = np.nan

    if (
        not pd.isna(cash)
        and not pd.isna(current_liabilities)
        and current_liabilities != 0
    ):
        liquidity_1 = (
            cash
            / current_liabilities
            * 100
        )

    if (
        not pd.isna(cash)
        and not pd.isna(receivables)
        and not pd.isna(current_liabilities)
        and current_liabilities != 0
    ):
        liquidity_2 = (
            (cash + receivables)
            / current_liabilities
            * 100
        )

    if (
        not pd.isna(current_assets)
        and not pd.isna(current_liabilities)
        and current_liabilities != 0
    ):
        liquidity_3 = (
            current_assets
            / current_liabilities
            * 100
        )


    # --------------------------------------------------------
    # FCF-Marge
    # --------------------------------------------------------

    fcf_margin = np.nan

    if (
        not pd.isna(fcf)
        and not pd.isna(revenue)
        and revenue != 0
    ):
        fcf_margin = (
            fcf / revenue * 100
        )


    # --------------------------------------------------------
    # ROE
    # --------------------------------------------------------

    roe = np.nan

    if (
        not pd.isna(net_income)
        and not pd.isna(equity)
        and equity != 0
    ):
        roe = (
            net_income / equity * 100
        )


    # --------------------------------------------------------
    # Debt / Equity
    # --------------------------------------------------------

    debt_equity = np.nan

    if (
        not pd.isna(debt)
        and not pd.isna(equity)
        and equity != 0
    ):
        debt_equity = (
            debt / equity * 100
        )


    # --------------------------------------------------------
    # Jahresendkurs
    # --------------------------------------------------------

    year_end_price = get_year_end_price(
        history,
        year
    )


    # --------------------------------------------------------
    # Historische Multiples
    # --------------------------------------------------------

    kgv = calculate_multiple(
        year_end_price,
        eps
    )

    kbv = calculate_multiple(
        year_end_price,
        book_value_per_share
    )

    kcv = calculate_multiple(
        year_end_price,
        fcf_per_share
    )

    kuv = calculate_multiple(
        year_end_price,
        revenue_per_share
    )


    # --------------------------------------------------------
    # Tabellenzeilen
    # --------------------------------------------------------

    historical_rows.append({
        "Jahr": year,
        "Umsatz (Mrd.)": (
            revenue / 1e9
            if not pd.isna(revenue)
            else np.nan
        ),
        "Eigenkapital (Mrd.)": (
            equity / 1e9
            if not pd.isna(equity)
            else np.nan
        ),
        "Free Cashflow (Mrd.)": (
            fcf / 1e9
            if not pd.isna(fcf)
            else np.nan
        ),
        "EPS": eps,
        "Jahresendkurs": year_end_price
    })


    share_rows.append({
        "Jahr": year,
        "Buchwert/Aktie": book_value_per_share,
        "Umsatz/Aktie": revenue_per_share,
        "Dividende/Aktie": dividend_per_share,
        "Free Cashflow/Aktie": fcf_per_share
    })


    payout_rows.append({
        "Jahr": year,
        "Ausschüttungsquote 1 (%)": payout_eps,
        "Ausschüttungsquote 2 (%)": payout_fcf
    })


    liquidity_rows.append({
        "Jahr": year,
        "Liquidität 1 (%)": liquidity_1,
        "Liquidität 2 (%)": liquidity_2,
        "Liquidität 3 (%)": liquidity_3
    })


    quality_rows.append({
        "Jahr": year,
        "FCF-Marge (%)": fcf_margin,
        "ROE (%)": roe,
        "Debt/Equity (%)": debt_equity
    })


    valuation_rows.append({
        "Jahr": year,
        "KGV": kgv,
        "KBV": kbv,
        "KCV": kcv,
        "KUV": kuv
    })


# ============================================================
# DATAFRAMES
# ============================================================

historical_df = pd.DataFrame(historical_rows)
share_df = pd.DataFrame(share_rows)
payout_df = pd.DataFrame(payout_rows)
liquidity_df = pd.DataFrame(liquidity_rows)
quality_df = pd.DataFrame(quality_rows)
valuation_df = pd.DataFrame(valuation_rows)


# ============================================================
# TABELLE 1
# ============================================================

st.subheader("1. Umsatz, Eigenkapital, Free Cashflow, EPS und Jahresendkurs")

if not historical_df.empty:

    display_df = historical_df.copy()

    st.dataframe(
        display_df.style.format({
            "Umsatz (Mrd.)": "{:.2f}",
            "Eigenkapital (Mrd.)": "{:.2f}",
            "Free Cashflow (Mrd.)": "{:.2f}",
            "EPS": "{:.2f}",
            "Jahresendkurs": "{:.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TABELLE 2
# ============================================================

st.subheader("2. Kennzahlen je Aktie")

if not share_df.empty:

    st.dataframe(
        share_df.style.format({
            "Buchwert/Aktie": "{:.2f}",
            "Umsatz/Aktie": "{:.2f}",
            "Dividende/Aktie": "{:.2f}",
            "Free Cashflow/Aktie": "{:.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TABELLE 3
# ============================================================

st.subheader("3. Ausschüttungsquoten")

if not payout_df.empty:

    st.dataframe(
        payout_df.style.format({
            "Ausschüttungsquote 1 (%)": "{:.1f} %",
            "Ausschüttungsquote 2 (%)": "{:.1f} %"
        }),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TABELLE 4 – LIQUIDITÄT MIT AMPEL
# ============================================================

st.subheader("4. Liquidität")

if not liquidity_df.empty:

    liquidity_display = liquidity_df.copy()

    # --------------------------------------------------------
    # Styling
    # --------------------------------------------------------

    styled_liquidity = (
        liquidity_display.style

        .map(
            lambda value: color_liquidity(
                value,
                "L1"
            ),
            subset=["Liquidität 1 (%)"]
        )

        .map(
            lambda value: color_liquidity(
                value,
                "L2"
            ),
            subset=["Liquidität 2 (%)"]
        )

        .map(
            lambda value: color_liquidity(
                value,
                "L3"
            ),
            subset=["Liquidität 3 (%)"]
        )

        .format({
            "Liquidität 1 (%)": "{:.1f} %",
            "Liquidität 2 (%)": "{:.1f} %",
            "Liquidität 3 (%)": "{:.1f} %"
        })
    )

    st.dataframe(
        styled_liquidity,
        use_container_width=True,
        hide_index=True
    )

    st.markdown(
        """
**Bewertung der Liquidität**

🔴 **Schwach** &nbsp;&nbsp;
🟡 **Solide** &nbsp;&nbsp;
🟢 **Stark**

| Kennzahl | 🔴 Schwach | 🟡 Solide | 🟢 Stark |
|---|---:|---:|---:|
| Liquidität 1. Grades | < 20 % | 20–30 % | > 30 % |
| Liquidität 2. Grades | < 100 % | 100–120 % | > 120 % |
| Liquidität 3. Grades | < 120 % | 120–150 % | > 150 % |
"""
    )


# ============================================================
# PEER AUS SIDEBAR
# ============================================================

default_peers = INDUSTRY_PEERS.get(
    ticker_symbol,
    []
)

peer_text_default = ", ".join(default_peers)

peer_text = st.sidebar.text_input(
    "Branchenvergleich – Peer-Ticker",
    value=peer_text_default,
    help=(
        "Yahoo-Ticker durch Komma getrennt. "
        "Beispiel: AAPL, MSFT, GOOGL"
    )
)

peer_tickers = [
    x.strip().upper()
    for x in peer_text.split(",")
    if x.strip()
]


# ============================================================
# PEER-DATEN LADEN
# ============================================================

peer_df = pd.DataFrame()

if peer_tickers:

    with st.spinner("Berechne Branchenvergleich ..."):

        try:
            peer_df = get_peer_metrics(
                tuple(peer_tickers)
            )

        except Exception:
            peer_df = pd.DataFrame()


# ============================================================
# BRANCHENDURCHSCHNITT
# ============================================================

peer_avg = {}

if not peer_df.empty:

    for col in [
        "FCF-Marge (%)",
        "ROE (%)",
        "Debt/Equity (%)",
        "KGV",
        "KBV",
        "KCV",
        "KUV"
    ]:

        if col in peer_df.columns:

            peer_avg[col] = safe_float(
                peer_df[col].mean()
            )


# ============================================================
# TABELLE 5
# ============================================================

st.subheader(
    "5. FCF-Marge, ROE und Debt/Equity"
)

if not quality_df.empty:

    quality_display = quality_df.copy()

    if peer_avg:

        quality_display["Branchen-Ø FCF-Marge"] = peer_avg.get(
            "FCF-Marge (%)",
            np.nan
        )

        quality_display["Branchen-Ø ROE"] = peer_avg.get(
            "ROE (%)",
            np.nan
        )

        quality_display["Branchen-Ø Debt/Equity"] = peer_avg.get(
            "Debt/Equity (%)",
            np.nan
        )

    format_dict = {
        "FCF-Marge (%)": "{:.1f} %",
        "ROE (%)": "{:.1f} %",
        "Debt/Equity (%)": "{:.1f} %"
    }

    if "Branchen-Ø FCF-Marge" in quality_display.columns:
        format_dict["Branchen-Ø FCF-Marge"] = "{:.1f} %"

    if "Branchen-Ø ROE" in quality_display.columns:
        format_dict["Branchen-Ø ROE"] = "{:.1f} %"

    if "Branchen-Ø Debt/Equity" in quality_display.columns:
        format_dict["Branchen-Ø Debt/Equity"] = "{:.1f} %"

    st.dataframe(
        quality_display.style.format(format_dict),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TABELLE 6
# ============================================================

st.subheader("6. Historische Bewertung")

if not valuation_df.empty:

    valuation_display = valuation_df.copy()

    if peer_avg:

        valuation_display["Branchen-Ø KGV"] = peer_avg.get(
            "KGV",
            np.nan
        )

        valuation_display["Branchen-Ø KBV"] = peer_avg.get(
            "KBV",
            np.nan
        )

        valuation_display["Branchen-Ø KCV"] = peer_avg.get(
            "KCV",
            np.nan
        )

        valuation_display["Branchen-Ø KUV"] = peer_avg.get(
            "KUV",
            np.nan
        )

    format_dict = {
        "KGV": "{:.2f}",
        "KBV": "{:.2f}",
        "KCV": "{:.2f}",
        "KUV": "{:.2f}"
    }

    if "Branchen-Ø KGV" in valuation_display.columns:
        format_dict["Branchen-Ø KGV"] = "{:.2f}"

    if "Branchen-Ø KBV" in valuation_display.columns:
        format_dict["Branchen-Ø KBV"] = "{:.2f}"

    if "Branchen-Ø KCV" in valuation_display.columns:
        format_dict["Branchen-Ø KCV"] = "{:.2f}"

    if "Branchen-Ø KUV" in valuation_display.columns:
        format_dict["Branchen-Ø KUV"] = "{:.2f}"

    st.dataframe(
        valuation_display.style.format(format_dict),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# AKTUELLE BEWERTUNG
# ============================================================

st.subheader("📊 Aktuelle Bewertung")

if not historical_df.empty and not share_df.empty:

    latest_hist = historical_df.iloc[0]
    latest_share = share_df.iloc[0]

    current_eps = safe_float(
        latest_hist["EPS"]
    )

    current_book_value = safe_float(
        latest_share["Buchwert/Aktie"]
    )

    current_fcf_per_share = safe_float(
        latest_share["Free Cashflow/Aktie"]
    )

    current_revenue_per_share = safe_float(
        latest_share["Umsatz/Aktie"]
    )

    current_kgv = calculate_multiple(
        current_price,
        current_eps
    )

    current_kbv = calculate_multiple(
        current_price,
        current_book_value
    )

    current_kcv = calculate_multiple(
        current_price,
        current_fcf_per_share
    )

    current_kuv = calculate_multiple(
        current_price,
        current_revenue_per_share
    )

    valuation_cols = st.columns(4)

    with valuation_cols[0]:

        st.metric(
            "Aktuelles KGV",
            (
                f"{current_kgv:.2f}"
                if not pd.isna(current_kgv)
                else "–"
            )
        )

    with valuation_cols[1]:

        st.metric(
            "Aktuelles KBV",
            (
                f"{current_kbv:.2f}"
                if not pd.isna(current_kbv)
                else "–"
            )
        )

    with valuation_cols[2]:

        st.metric(
            "Aktuelles KCV",
            (
                f"{current_kcv:.2f}"
                if not pd.isna(current_kcv)
                else "–"
            )
        )

    with valuation_cols[3]:

        st.metric(
            "Aktuelles KUV",
            (
                f"{current_kuv:.2f}"
                if not pd.isna(current_kuv)
                else "–"
            )
        )


# ============================================================
# GRAHAM-BEWERTUNG
# ============================================================

st.subheader("🧮 Graham-Bewertung")

if not historical_df.empty and not share_df.empty:

    eps_values = pd.to_numeric(
        historical_df["EPS"],
        errors="coerce"
    ).dropna()

    book_values = pd.to_numeric(
        share_df["Buchwert/Aktie"],
        errors="coerce"
    ).dropna()

    if not eps_values.empty and not book_values.empty:

        avg_eps = eps_values.mean()
        avg_book_value = book_values.mean()

        graham_value = calculate_graham(
            avg_eps,
            avg_book_value
        )

        if not pd.isna(graham_value):

            graham_margin_price = (
                graham_value
                * (1 - margin_of_safety)
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Graham-Wert",
                    f"{graham_value:.2f}"
                )

            with col2:
                st.metric(
                    "Sicherheitsmarge",
                    f"{margin_of_safety * 100:.0f} %"
                )

            with col3:
                st.metric(
                    "Graham-Wert nach Sicherheitsmarge",
                    f"{graham_margin_price:.2f}"
                )


# ============================================================
# DCF
# ============================================================

st.subheader("💰 DCF-Bewertung")

if not historical_df.empty:

    latest_fcf = safe_float(
        historical_df.iloc[0]["Free Cashflow (Mrd.)"]
    )

    if not pd.isna(latest_fcf):

        # Rückrechnung von Mrd. auf absoluten Wert
        latest_fcf_absolute = latest_fcf * 1e9

        dcf_value = calculate_dcf(
            latest_fcf_absolute,
            fcf_growth,
            wacc,
            terminal_growth,
            forecast_years
        )

        if not pd.isna(dcf_value):

            st.metric(
                "Unternehmenswert nach DCF",
                f"{dcf_value / 1e9:.2f} Mrd."
            )

            st.caption(
                f"Annahmen: FCF-Wachstum "
                f"{fcf_growth * 100:.1f} %, "
                f"WACC {wacc * 100:.1f} %, "
                f"Terminal Growth "
                f"{terminal_growth * 100:.1f} %"
            )


# ============================================================
# DIVIDENDENANALYSE
# ============================================================

st.subheader("💶 Dividendenanalyse")

if not share_df.empty:

    dividend_values = pd.to_numeric(
        share_df["Dividende/Aktie"],
        errors="coerce"
    ).dropna()

    if not dividend_values.empty:

        latest_dividend = dividend_values.iloc[0]

        dividend_yield = np.nan

        if (
            not pd.isna(current_price)
            and current_price != 0
        ):
            dividend_yield = (
                latest_dividend
                / current_price
                * 100
            )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Dividende/Aktie",
                f"{latest_dividend:.2f}"
            )

        with col2:

            st.metric(
                "Dividendenrendite",
                (
                    f"{dividend_yield:.2f} %"
                    if not pd.isna(dividend_yield)
                    else "–"
                )
            )


# ============================================================
# FUNDAMENTAL SCORE
# ============================================================

st.subheader("⭐ Fundamentale Kennzahlen")

score_values = []

if not quality_df.empty:

    latest_quality = quality_df.iloc[0]

    fcf_margin_latest = safe_float(
        latest_quality["FCF-Marge (%)"]
    )

    roe_latest = safe_float(
        latest_quality["ROE (%)"]
    )

    debt_equity_latest = safe_float(
        latest_quality["Debt/Equity (%)"]
    )

    if not pd.isna(fcf_margin_latest):
        score_values.append(
            calculate_growth_score(
                fcf_margin_latest
            )
        )

    if not pd.isna(roe_latest):
        score_values.append(
            calculate_growth_score(
                roe_latest
            )
        )

    if not pd.isna(debt_equity_latest):

        if debt_equity_latest < 50:
            score_values.append(5)

        elif debt_equity_latest < 100:
            score_values.append(4)

        elif debt_equity_latest < 150:
            score_values.append(3)

        elif debt_equity_latest < 200:
            score_values.append(2)

        else:
            score_values.append(1)


if score_values:

    fundamental_score = (
        sum(score_values)
        / len(score_values)
    )

    if fundamental_score >= 4.5:
        score_label = "Sehr attraktiv"

    elif fundamental_score >= 3.5:
        score_label = "Attraktiv"

    elif fundamental_score >= 2.5:
        score_label = "Ausgeglichen"

    elif fundamental_score >= 1.5:
        score_label = "Schwach"

    else:
        score_label = "Sehr schwach"

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Fundamentaler Score",
            f"{fundamental_score:.1f} / 5"
        )

    with col2:
        st.metric(
            "Einordnung",
            score_label
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
    "Branchen-Durchschnittswerte basieren auf den in der Seitenleiste "
    "hinterlegten Vergleichsunternehmen."
)
