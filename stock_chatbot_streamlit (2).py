
import streamlit as st
import requests
import os
import datetime
import matplotlib.pyplot as plt
import pandas as pd
from streamlit.components.v1 import html

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "your_finnhub_api_key_here")

def fetch_stock_data(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol.upper()}&token={FINNHUB_API_KEY}"
    try:
        r = requests.get(url, timeout=10).json()
        if r.get("c"):
            return {"price": r["c"], "high": r["h"], "low": r["l"], "prevClose": r["pc"]}, None
        return None, f"No data for {symbol}"
    except Exception as e:
        return None, str(e)

def fetch_historical_prices(symbol):
    end = int(datetime.datetime.now().timestamp())
    start = int((datetime.datetime.now() - datetime.timedelta(days=30)).timestamp())
    url = f"https://finnhub.io/api/v1/stock/candle?symbol={symbol.upper()}&resolution=D&from={start}&to={end}&token={FINNHUB_API_KEY}"
    try:
        data = requests.get(url, timeout=10).json()
        if data.get("c"):
            return data, None
        return None, "No historical data found."
    except Exception as e:
        return None, str(e)

def fetch_company_profile(symbol):
    url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol.upper()}&token={FINNHUB_API_KEY}"
    try:
        data = requests.get(url, timeout=10).json()
        return data if data.get("name") else None, None
    except Exception as e:
        return None, str(e)

def fetch_company_news(symbol):
    today = datetime.date.today()
    one_month_ago = today - datetime.timedelta(days=30)
    url = f"https://finnhub.io/api/v1/company-news?symbol={symbol.upper()}&from={one_month_ago}&to={today}&token={FINNHUB_API_KEY}"
    try:
        return requests.get(url, timeout=10).json()[:5]
    except Exception:
        return []

def search_symbol_by_name(name):
    url = f"https://finnhub.io/api/v1/search?q={name}&token={FINNHUB_API_KEY}"
    try:
        r = requests.get(url, timeout=10).json()
        return r.get("result", [])[0]["symbol"] if r.get("result") else None
    except Exception:
        return None

def explain_term(query):
    q = query.lower()
    terms = {
        "nasdaq": "NASDAQ is an American stock exchange focused on technology companies.",
        "nyse": "NYSE is the New York Stock Exchange, one of the largest in the world.",
        "stock": "A stock represents ownership in a company.",
        "dividend": "A dividend is a portion of earnings shared with shareholders.",
        "market cap": "Market cap is the total value of all a company’s shares."
    }
    for key, explanation in terms.items():
        if key in q:
            return explanation
    return None

# Streamlit UI
st.set_page_config(page_title="Stock Chatbot", layout="centered")
st.title("📊 Ultimate Stock Chatbot")
st.write("Ask about **stock tickers** (e.g., AAPL), **company names** (e.g., Tesla), or **finance terms** (e.g., 'dividend').")
query = st.text_input("Your question:")
notify = st.toggle("🔔 Notify me if price drops below $100")

if query:
    explanation = explain_term(query)
    if explanation:
        st.info(explanation)
    else:
        symbol = search_symbol_by_name(query)
        if symbol:
            quote, quote_error = fetch_stock_data(symbol)
            profile, profile_error = fetch_company_profile(symbol)
            history, hist_error = fetch_historical_prices(symbol)
            news = fetch_company_news(symbol)

            if quote:
                st.success(f"✅ {symbol.upper()} — {profile['name'] if profile else symbol.upper()}")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Current Price", f"${quote['price']:.2f}")
                    st.caption(f"High: ${quote['high']:.2f}, Low: ${quote['low']:.2f}")
                with col2:
                    st.metric("Prev Close", f"${quote['prevClose']:.2f}")
                    if profile and profile.get("logo"):
                        st.image(profile["logo"], width=80)

                if profile:
                    st.markdown(f"**Exchange**: {profile.get('exchange', 'N/A')}")
                    st.markdown(f"**Industry**: {profile.get('finnhubIndustry', 'N/A')}")
                    st.markdown(f"**Website**: [{profile.get('weburl')}]({profile.get('weburl')})")

                # Historical chart
                if history:
                    st.subheader("📉 Price (Last 30 Days)")
                    df = pd.DataFrame({"Date": pd.to_datetime(history["t"], unit="s"), "Close": history["c"]})
                    fig, ax = plt.subplots()
                    ax.plot(df["Date"], df["Close"])
                    ax.set_title(f"{symbol.upper()} Closing Prices")
                    st.pyplot(fig)
                elif hist_error:
                    st.warning(hist_error)

                if notify and quote["price"] < 100:
                    st.error("🔔 Alert: Price dropped below $100!")

                if news:
                    st.subheader("📰 Recent News")
                    for article in news:
                        st.markdown(f"[{article['headline']}]({article['url']})")
                else:
                    st.caption("No recent news found.")
            elif quote_error:
                st.error(f"Quote error: {quote_error}")
        else:
            st.warning("Symbol or company not recognized.")
