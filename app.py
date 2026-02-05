import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# 1. 페이지 설정 및 서비스 명칭 적용
st.set_page_config(page_title="StockCompass AI", layout="wide", page_icon="🧭")

# 서비스 헤더
st.title("🧭 StockCompass AI")
st.markdown("#### 데이터로 정밀 진단하는 당신의 투자 나침반")
st.caption("성장성(PER) + 안정성(배당) + 시장 심리(뉴스)를 종합 분석하여 고점 여부를 판단합니다.")

# 2. 섹터 데이터베이스
SECTORS = {
    "미국 M7 (빅테크)": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"],
    "글로벌 반도체": ["NVDA", "AMD", "ASML", "TSM", "INTC", "MU", "AVGO"],
    "K-반도체 & 가전": ["005930.KS", "000660.KS", "066570.KS", "000990.KS"],
    "K-배터리 & 소재": ["373220.KS", "006400.KS", "051910.KS", "003670.KS", "247540.KQ"],
    "방산 & 우주항공": ["047810.KS", "012450.KS", "073190.KS", "LMT", "PLTR", "RTX"],
    "로봇 & AI": ["ISRG", "041510.KS", "220630.KQ", "TER", "PATH", "BOTZ"],
    "바이오 & 헬스케어": ["LLY", "NVO", "207940.KS", "068270.KS", "PFE", "JNJ"]
}

# 3. 뉴스 감성 분석 로직
def analyze_sentiment(news_list):
    pos_words = ['buy', 'growth', 'positive', 'up', 'increase', 'bull', 'strong', 'profit', 'beat']
    neg_words = ['sell', 'decline', 'negative', 'down', 'decrease', 'bear', 'weak', 'loss', 'risk', 'miss']
    
    score = 0
    for news in news_list:
        title = news['title'].lower()
        score += sum(1 for pw in pos_words if pw in title)
        score -= sum(1 for nw in neg_words if nw in title)
    
    if score > 0: return "📈 긍정 (Bullish)"
    elif score < 0: return "📉 부정 (Bearish)"
    else: return "😐 중립 (Neutral)"

# 4. 종합 데이터 수집 함수
@st.cache_data(ttl=3600)
def fetch_all_data(tickers):
    results = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            news = stock.news[:5]
            
            results.append({
                "티커": t,
                "기업명": info.get('shortName', t),
                "현재가": info.get('currentPrice'),
                "PER": info.get('trailingPE', 0),
                "매출성장률(%)": info.get('revenueGrowth', 0) * 100,
                "배당수익률(%)": (info.get('dividendYield', 0) * 100) if info.get('dividendYield') else 0,
                "영업이익률(%)": (info.get('operatingMargins', 0) * 100) if info.get('operatingMargins') else 0,
                "뉴스감성": analyze_sentiment(news),
                "시총(B)": round(info.get('marketCap', 0) / 1e9, 2)
            })
        except: continue
    return pd.DataFrame(results)

# 5. 사이드바 컨트롤
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1491/1491258.png", width=100)
st.sidebar.header("설정 패널")
selected_name = st.sidebar.selectbox("🎯 분석 섹터 선택", list(SECTORS.keys()))
custom_tickers = st.sidebar.text_area("📝 종목 편집", value=", ".join(SECTORS[selected_name]))

# 6. 실행 및 결과 출력
if st.sidebar.button("🔍 나침반 가동"):
    df = fetch_all_data([x.strip() for x in custom_tickers.split(",")])

    if not df.empty:
        avg_per = df[df['PER'] > 0]['PER'].mean()
        
        # 상단 요약 요약
        st.subheader(f"📍 {selected_name} 섹터 정밀 진단")
        m1, m2, m3 = st.columns(3)
        m1.metric("섹터 평균 PER", f"{avg_per:.1f}배")
        m2.metric("최고 배당주", df.loc[df['배당수익률(%)'].idxmax(), '티커'])
        m3.metric("최고 성장주", df.loc[df['매출성장률(%)'].idxmax(), '티커'])

        # 메인 시각화: PER vs 배당수익률 (안전성 맵)
        st.divider()
        st.write("### 🧭 가치 & 안전성 매트릭스")
        fig = px.scatter(df, x="PER", y="배당수익률(%)", size="시총(B)",
                         text="티커", color="뉴스감성",
                         color_discrete_map={"📈 긍정 (Bullish)": "#2ecc71", "📉 부정 (Bearish)": "#e74c3c", "😐 중립 (Neutral)": "#95a5a6"},
                         template="plotly_dark")
        
        fig.add_vline(x=avg_per, line_dash="dash", line_color="white", annotation_text="평균 PER")
        st.plotly_chart(fig, use_container_width=True)
        
        

        # 데이터 테이블 및 AI 진단
        st.subheader("📋 상세 분석 데이터")
        st.dataframe(df.style.background_gradient(subset=['배당수익률(%)'], cmap='Greens')
                         .background_gradient(subset=['매출성장률(%)'], cmap='Blues'))

        st.divider()
        st.subheader("💡 StockCompass AI의 최종 제언")
        
        for _, row in df.iterrows():
            with st.expander(f"🔍 {row['이름']} ({row['티커']}) 심층 진단"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**심리 상태:** {row['뉴스감성']}")
                    st.write(f"**밸류에이션:** {'상대적 고평가' if row['PER'] > avg_per else '상대적 저평가'}")
                with c2:
                    # 예측 로직
                    if "긍정" in row['뉴스감성'] and row['PER'] < avg_per:
                        st.success("✅ **[매수 적기]** 뉴스 흐름이 좋고 업계 평균보다 저렴합니다.")
                    elif "부정" in row['뉴스감성'] and row['PER'] > avg_per:
                        st.error("🚨 **[고점 주의]** 뉴스는 부정적인데 주가는 거품이 끼어 있습니다.")
                    elif row['배당수익률(%)'] > 4:
                        st.info("💎 **[배당 매력]** 주가 변동과 관계없이 배당 수익이 탄탄한 구간입니다.")
                    else:
                        st.warning("⚠️ **[관망 추천]** 뚜렷한 방향성이 보이지 않는 중립 구간입니다.")
    else:
        st.error("데이터를 불러오지 못했습니다.")
