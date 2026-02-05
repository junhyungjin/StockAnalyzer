import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="AI 주식 종합 진단기", layout="wide")

# 1. 섹터 DB 업데이트
SECTORS = {
    "미국 M7 (빅테크)": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"],
    "글로벌 반도체": ["NVDA", "AMD", "ASML", "TSM", "INTC", "MU", "AVGO"],
    "K-반도체 & 가전": ["005930.KS", "000660.KS", "066570.KS", "000990.KS"],
    "K-배터리 & 소재": ["373220.KS", "006400.KS", "051910.KS", "003670.KS", "247540.KQ"],
    "방산 & 우주항공": ["047810.KS", "012450.KS", "073190.KS", "LMT", "PLTR", "RTX"],
    "바이오 & 헬스케어": ["LLY", "NVO", "207940.KS", "068270.KS", "PFE", "JNJ"]
}

# 2. 뉴스 감성 분석 함수 (단순 단어 매칭 방식)
def analyze_sentiment(news_list):
    pos_words = ['buy', 'growth', 'positive', 'up', 'increase', 'bull', 'strong', 'profit']
    neg_words = ['sell', 'decline', 'negative', 'down', 'decrease', 'bear', 'weak', 'loss', 'risk']
    
    score = 0
    for news in news_list:
        title = news['title'].lower()
        for pw in pos_words:
            if pw in title: score += 1
        for nw in neg_words:
            if nw in title: score -= 1
    
    if score > 0: return "📈 긍정 (Bullish)"
    elif score < 0: return "📉 부정 (Bearish)"
    else: return "😐 중립 (Neutral)"

# 3. 데이터 수집 함수 (배당 포함)
@st.cache_data(ttl=3600)
def fetch_comprehensive_data(tickers):
    results = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            news = stock.news[:5] # 최신 뉴스 5개
            
            results.append({
                "티커": t,
                "이름": info.get('shortName', t),
                "현재가": info.get('currentPrice'),
                "PER": info.get('trailingPE', 0),
                "매출성장률(%)": info.get('revenueGrowth', 0) * 100,
                "배당수익률(%)": info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                "영업이익률(%)": info.get('operatingMargins', 0) * 100,
                "뉴스감성": analyze_sentiment(news),
                "시총(B)": round(info.get('marketCap', 0) / 1e9, 2)
            })
        except: continue
    return pd.DataFrame(results)

# 4. 메인 화면
st.title("🤖 AI 주식 종합 진단 & 뉴스 분석")

selected_name = st.sidebar.selectbox("섹터 선택", list(SECTORS.keys()))
custom_tickers = st.sidebar.text_input("티커 수정", value=", ".join(SECTORS[selected_name]))

if st.sidebar.button("🚀 종합 분석 실행"):
    df = fetch_comprehensive_data([x.strip() for x in custom_tickers.split(",")])

    if not df.empty:
        # 상단 요약 카드
        avg_div = df['배당수익률(%)'].mean()
        st.subheader(f"📊 {selected_name} 섹터 분석 결과")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("섹터 평균 배당률", f"{avg_div:.2f}%")
        m2.metric("최고 배당주", df.loc[df['배당수익률(%)'].idxmax(), '티커'])
        m3.metric("최고 성장주", df.loc[df['매출성장률(%)'].idxmax(), '티커'])

        # 차트: PER vs 배당 (배당주의 안전성 확인)
        st.divider()
        st.subheader("💰 배당 수익률 vs 주가 수준")
        fig = px.scatter(df, x="PER", y="배당수익률(%)", size="시총(B)",
                         text="티커", color="뉴스감성",
                         color_discrete_map={"📈 긍정 (Bullish)": "green", "📉 부정 (Bearish)": "red", "😐 중립 (Neutral)": "gray"},
                         title="PER이 낮고 배당이 높은 종목(상단 왼쪽)이 안전한 투자처입니다.")
        st.plotly_chart(fig, use_container_width=True)

        

        # 데이터 테이블
        st.subheader("📝 상세 분석 시트")
        st.dataframe(df.style.background_gradient(subset=['배당수익률(%)'], cmap='Greens')
                         .background_gradient(subset=['매출성장률(%)'], cmap='Blues'))

        # 뉴스 예측 기반 추천
        st.divider()
        st.subheader("📰 AI 뉴스 기반 주가 예측")
        for _, row in df.iterrows():
            with st.expander(f"{row['이름']} ({row['티커']}) 진단"):
                col_a, col_b = st.columns(2)
                col_a.write(f"**현재 감성:** {row['뉴스감성']}")
                col_a.write(f"**배당 메리트:** {'높음' if row['배당수익률(%)'] > 3 else '낮음 또는 성장주'}")
                
                # 예측 로직
                if "긍정" in row['뉴스감성'] and row['PER'] < 20:
                    col_b.success("🚀 예측: 단기적 우상향 가능성 높음 (호재 + 저PER)")
                elif "부정" in row['뉴스감성'] and row['PER'] > 50:
                    col_b.error("🚨 예측: 조정 가능성 매우 높음 (악재 + 고PER 고점)")
                else:
                    col_b.info("😐 예측: 기간 조정 및 횡보 예상")
    else:
        st.error("데이터 로딩 실패")
