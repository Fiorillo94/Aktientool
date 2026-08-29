import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import re


# ============================================================
# KONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Aktien-Bewertungs-Tool",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Mein personalisiertes Aktien-Bewertungs-Tool")
st.caption(
    "Ticker · Firmenname · WKN · ISIN · Fundamentalanalyse · DCF"
)


# ============================================================
# HILFSFUNKTIONEN
# ============================================================

def safe_float(value):
    try:
        if value is None:
            return np.nan

        if pd.isna(value):
            return np.nan

        return float(value)

    except Exception:
        return np.nan


def safe_get(df, row, column, default=np.nan):

    try:

        if df is None or df.empty:
            return default

        if row not in df.index:
            return default

        if column not in df.columns:
            return default

        value = df.loc[row, column]

        if pd.notna(value):
            return float(value)

    except Exception:
        pass

    return default


def get_value(
    df,
    possible_rows,
    column,
    default=np.nan
):

    for row in possible_rows:

        value = safe_get(
            df,
            row,
            column,
            np.nan
        )

        if pd.notna(value):
            return value

    return default


def get_year_end_price(
    share,
    year
):

    try:

        start_date = f"{year}-12-20"
        end_date = f"{year + 1}-01-03"

        hist = share.history(
            start=start_date,
            end=end_date,
            auto_adjust=False
        )

        if hist.empty:
            return np.nan

        hist = hist[
            hist.index.date
            <= pd.Timestamp(
                f"{year}-12-31"
            ).date()
        ]

        if hist.empty:
            return np.nan

        return float(
            hist["Close"].dropna().iloc[-1]
        )

    except Exception:

        return np.nan


def calculate_multiple(
    price,
    fundamental
):

    if (
        pd.notna(price)
        and pd.notna(fundamental)
        and fundamental > 0
    ):

        return price / fundamental

    return np.nan


def growth_score(
    values,
    max_points
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

    oldest = values.iloc[-1]
    newest = values.iloc[0]

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
# AUTOMATISCHE TICKER-ERKENNUNG
# ============================================================

def normalize_input(user_input):

    value = (
        user_input
        .strip()
        .upper()
    )

    # --------------------------------------------------------
    # ISIN
    # --------------------------------------------------------

    if re.match(
        r"^[A-Z]{2}[A-Z0-9]{10}$",
        value
    ):

        # Bekannte deutsche ISINs
        german_isin_map = {

            "DE0005405104": "TSS.DE",

            # Beispiele
            "DE0007164600": "SAP.DE",
            "DE0007236101": "SIEMENS.DE",
            "DE0008404005": "ALV.DE",
            "DE0005190003": "BMW.DE",
            "DE0007100000": "MBG.DE",
            "DE0005557508": "DTE.DE",
            "DE0006231004": "IFX.DE",
            "DE000BASF111": "BAS.DE",
            "DE000A1EWWW0": "ADS.DE",
            "DE0007664039": "VOW3.DE"
        }

        if value in german_isin_map:

            return german_isin_map[value]


    # --------------------------------------------------------
    # WKN
    # --------------------------------------------------------

    if re.match(
        r"^[A-Z0-9]{6}$",
        value
    ):

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
            "766403": "VOW3.DE"
        }

        if value in wkn_map:

            return wkn_map[value]


    # --------------------------------------------------------
    # Bekannte deutsche Unternehmen
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
        "MERCEDES BENZ": "MBG.DE",
        "DEUTSCHE TELEKOM": "DTE.DE",
        "TELEKOM": "DTE.DE",
        "INFINEON": "IFX.DE",
        "BASF": "BAS.DE",
        "ADIDAS": "ADS.DE",
        "VOLKSWAGEN": "VOW3.DE",
        "VW": "VOW3.DE"
    }


    if value in company_map:

        return company_map[value]


    # --------------------------------------------------------
    # Bereits Yahoo-Ticker eingegeben
    # --------------------------------------------------------

    if "." in value:

        return value


    # --------------------------------------------------------
    # Deutscher Ticker ohne .DE
    # --------------------------------------------------------

    return f"{value}.DE"


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
    "Aktie suchen – Ticker, Firmenname, WKN oder ISIN",
    value="InnoTec TSS"
)


if user_input:

    ticker_symbol = normalize_input(
        user_input
    )

    st.info(
        f"🔎 Erkannter Yahoo-Finance-Ticker: "
        f"**{ticker_symbol}**"
    )


    try:

        # ====================================================
        # YAHOO FINANCE
        # ====================================================

        share = yf.Ticker(
            ticker_symbol
        )


        try:

            info = share.info

        except Exception:

            info = {}

        # Überprüfen, ob Daten geladen wurden
        if not info or 'longName' not in info:
            st.error("⚠️ Fehler: Kurse konnten von Yahoo Finance nicht abgerufen werden. Der Ticker ist evtl. temporär gesperrt oder unbekannt.")
        else:
            # Stammdaten auslesen
            company_name = info.get("longName", "Unbekannt")
            current_price = info.get("currentPrice", info.get("previousClose", np.nan))
            currency = info.get("currency", "EUR")
            
            st.success(f"### {company_name}")
            
            # Werte übersichtlich in Spalten anzeigen
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Aktueller Kurs", value=f"{current_price:.2f} {currency}" if pd.notna(current_price) else "N/A")
            with col2:
                st.metric(label="Währungsraum", value=currency)
            with col3:
                st.metric(label="Branche", value=info.get("industry", "N/A"))

    except Exception as e:
        st.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

        
        # ====================================================
        # PRÜFUNG AUF GÜLTIGEN TITEL
        # ====================================================

        if not info:

            st.error(
                "Yahoo Finance konnte für diesen Titel "
                "keine Stammdaten liefern."
            )

            st.stop()


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


        # ====================================================
        # KURS
        # ====================================================

        history = share.history(
            period="5d",
            auto_adjust=False
        )

        if history.empty:

            st.error(
                "Für diesen Titel konnte kein Kurs "
                "abgerufen werden."
            )

            st.stop()


        current_price = float(
            history[
                "Close"
            ].dropna().iloc[-1]
        )


        # ====================================================
        # UNTERNEHMENSINFORMATIONEN
        # ====================================================

        st.subheader(
            f"{company_name} ({ticker_symbol})"
        )


        col1, col2, col3, col4 = st.columns(4)


        with col1:

            st.metric(
                "Aktueller Kurs",
                f"{current_price:.2f} {currency}"
            )


        with col2:

            st.metric(
                "Börsenplatz",
                exchange
            )


        with col3:

            st.metric(
                "Sektor",
                sector
            )


        with col4:

            st.metric(
                "Branche",
                industry
            )


        if isin != "-":

            st.caption(
                f"ISIN: {isin}"
            )


        # ====================================================
        # NEBENWERT-WARNUNG
        # ====================================================

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
                "Handelsvolumen, Spreads und Datenqualität "
                "geringer sein. Automatische "
                "Branchenvergleiche sollten deshalb "
                "mit Vorsicht interpretiert werden."
            )


        # ====================================================
        # FINANZDATEN
        # ====================================================

        financials = share.financials

        balance_sheet = (
            share.balance_sheet
        )

        cashflow = share.cashflow


        if financials.empty:

            st.warning(
                "Yahoo Finance liefert keine "
                "historische Gewinn- und "
                "Verlustrechnung."
            )


        # ====================================================
        # DIVIDENDEN
        # ====================================================

        try:

            actions = share.actions

            if (
                actions is not None
                and not actions.empty
                and "Dividends"
                in actions.columns
            ):

                dividends = actions[
                    "Dividends"
                ]

                dividends = dividends[
                    dividends > 0
                ]

                dividends_by_year = (
                    dividends
                    .groupby(
                        dividends.index.year
                    )
                    .sum()
                )

            else:

                dividends_by_year = pd.Series(
                    dtype=float
                )

        except Exception:

            dividends_by_year = pd.Series(
                dtype=float
            )


        # ====================================================
        # HISTORISCHE JAHRE
        # ====================================================

        years = (
            financials.columns[:5]
            if not financials.empty
            else []
        )


        data_list = []


        # ====================================================
        # JAHRESSCHLEIFE
        # ====================================================

        for year in years:

            year_number = year.year


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


            free_cashflow = get_value(
                cashflow,
                [
                    "Free Cash Flow"
                ],
                year
            )


            # ----------------------------------------------
            # FCF FALLBACK
            # ----------------------------------------------

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


            # ----------------------------------------------
            # AKTIENANZAHL
            # ----------------------------------------------

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


            # ----------------------------------------------
            # EPS
            # ----------------------------------------------

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


            # ----------------------------------------------
            # BUCHWERT
            # ----------------------------------------------

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


            # ----------------------------------------------
            # FCF JE AKTIE
            # ----------------------------------------------

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


            # ----------------------------------------------
            # UMSATZ JE AKTIE
            # ----------------------------------------------

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


            # ----------------------------------------------
            # DIVIDENDE
            # ----------------------------------------------

            dividend_ps = (
                dividends_by_year.get(
                    year_number,
                    0
                )
            )


            # ----------------------------------------------
            # AUSSCHÜTTUNGSQUOTE 1
            # ----------------------------------------------

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


            # ----------------------------------------------
            # AUSSCHÜTTUNGSQUOTE 2
            # ----------------------------------------------

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


            # ----------------------------------------------
            # LIQUIDITÄT
            # ----------------------------------------------

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


            # ----------------------------------------------
            # FCF-MARGE
            # ----------------------------------------------

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


            # ----------------------------------------------
            # ROE
            # ----------------------------------------------

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


            # ----------------------------------------------
            # DEBT / EQUITY
            # ----------------------------------------------

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


            # ----------------------------------------------
            # JAHRESENDKURS
            # ----------------------------------------------

            year_end_price = (
                get_year_end_price(
                    share,
                    year_number
                )
            )


            # ----------------------------------------------
            # HISTORISCHE MULTIPLES
            # ----------------------------------------------

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


            # ----------------------------------------------
            # DATENSATZ
            # ----------------------------------------------

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


        df = pd.DataFrame(
            data_list
        )


        # ====================================================
        # HISTORISCHE DATEN
        # ====================================================

        if not df.empty:

            with st.expander(
                "📊 Historische Kennzahlen",
                expanded=True
            ):

                st.dataframe(
                    df.style.format(
                        precision=2,
                        na_rep="-"
                    ),
                    use_container_width=True
                )


        # ====================================================
        # HISTORISCHE MULTIPLES
        # ====================================================

        if not df.empty:

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

                "Ø 5 Jahre": [
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


        # ====================================================
        # DCF
        # ====================================================

        st.subheader(
            "💰 DCF-Bewertung"
        )


        try:

            ttm_cashflow = (
                share.ttm_cashflow
            )

        except Exception:

            ttm_cashflow = pd.DataFrame()


        ttm_fcf = np.nan


        if (
            ttm_cashflow is not None
            and not ttm_cashflow.empty
        ):

            for row in [
                "Free Cash Flow"
            ]:

                try:

                    if row in ttm_cashflow.index:

                        values = (
                            ttm_cashflow
                            .loc[row]
                            .dropna()
                        )

                        if not values.empty:

                            ttm_fcf = float(
                                values.iloc[0]
                            )

                            break

                except Exception:
                    pass


        # Fallback auf jüngstes Geschäftsjahr

        if (
            pd.isna(ttm_fcf)
            and not df.empty
        ):

            ttm_fcf = (
                latest[
                    "Free Cashflow (Mrd.)"
                ]
                * 1e9
            )


        shares_now = safe_float(
            info.get(
                "sharesOutstanding"
            )
        )


        if pd.isna(shares_now):

            try:

                shares_now = get_value(
                    balance_sheet,
                    [
                        "Ordinary Shares Number",
                        "Share Issued"
                    ],
                    balance_sheet.columns[0]
                )

            except Exception:

                shares_now = np.nan


        # ====================================================
        # NETTO-SCHULDEN
        # ====================================================

        current_cash = np.nan
        current_debt = np.nan


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

        else:

            net_debt = 0


        # ====================================================
        # DCF
        # ====================================================

        dcf_per_share = np.nan


        if (
            pd.notna(ttm_fcf)
            and ttm_fcf > 0
            and wacc > terminal_growth
            and pd.notna(shares_now)
            and shares_now > 0
        ):

            forecast_fcfs = []


            for year_number in range(
                1,
                forecast_years + 1
            ):

                future_fcf = (
                    ttm_fcf
                    * (
                        1
                        + growth_rate / 100
                    )
                    ** year_number
                )

                forecast_fcfs.append(
                    future_fcf
                )


            pv_fcfs = sum(

                fcf
                / (
                    1
                    + wacc / 100
                )
                ** year_number

                for year_number, fcf
                in enumerate(
                    forecast_fcfs,
                    start=1
                )
            )


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


            dcf_per_share = (
                equity_value
                / shares_now
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
                "DCF konnte nicht berechnet werden."
            )


        # ====================================================
        # GRAHAM
        # ====================================================

        st.subheader(
            "📐 Graham-Bewertung"
        )


        if not df.empty:

            avg_eps = (
                df["EPS"]
                .mean()
            )

            avg_bvps = (
                df["Buchwert/Aktie"]
                .mean()
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

                st.info(
                    "Graham-Bewertung nicht möglich."
                )


        # ====================================================
        # SCORE
        # ====================================================

        if not df.empty:

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


            # FCF-Marge

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


            # ROE

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


            # Verschuldung

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


            # Liquidität

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


            # Dividenden

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


            # Historische Bewertung

            score_historical = 0

            score_historical += (
                valuation_score(
                    current_kgv,
                    avg_kgv,
                    2.5
                )
            )

            score_historical += (
                valuation_score(
                    current_kcv,
                    avg_kcv,
                    2.5
                )
            )

            score_historical += (
                valuation_score(
                    current_kbv,
                    avg_kbv,
                    2.5
                )
            )

            score_historical += (
                valuation_score(
                    current_kuv,
                    avg_kuv,
                    2.5
                )
            )


            # DCF

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


            # ------------------------------------------------
            # Nebenwert: Branchenvergleich wird bewusst nicht
            # automatisch gewichtet, wenn keine verlässlichen
            # Peer-Daten vorhanden sind.
            # ------------------------------------------------

            score_industry = 0


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


            # Da der Branchenblock bei kleinen Nebenwerten
            # nicht zuverlässig verfügbar sein muss:
            #
            # Maximal erreichbare Punktzahl:
            # 90 statt 100.
            #
            # Anschließend auf 100 normalisieren.

            max_score = 90


            normalized_score = (
                total_score
                / max_score
            ) * 100


            normalized_score = min(
                100,
                normalized_score
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


        # ====================================================
        # SENSITIVITÄT
        # ====================================================

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


        # ====================================================
        # ZUSAMMENFASSUNG
        # ====================================================

        st.subheader(
            "🧭 Zusammenfassung"
        )


        if normalized_score >= 70:

            st.success(
                f"{company_name} erreicht "
                f"{normalized_score:.1f}/100 Punkte "
                f"und wird im Modell als "
                f"**{rating}** eingestuft."
            )

        elif normalized_score >= 55:

            st.info(
                f"{company_name} erreicht "
                f"{normalized_score:.1f}/100 Punkte. "
                f"Das Bild ist **{rating}**."
            )

        else:

            st.warning(
                f"{company_name} erreicht "
                f"{normalized_score:.1f}/100 Punkte "
                f"und wird als **{rating}** eingestuft."
            )


        st.caption(
            "⚠️ Die Berechnung ist ein quantitatives "
            "Bewertungsmodell und keine Anlageberatung. "
            "Gerade bei Nebenwerten können einzelne "
            "Yahoo-Finance-Daten fehlen oder zeitlich "
            "abweichen."
        )


    except Exception as e:

        st.error(
            "Fehler bei der Analyse."
        )

        st.exception(e)
