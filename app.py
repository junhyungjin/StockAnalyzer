import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(page_title="StockCompass AI", layout="wide", page_icon="🧭")

# 스타일 개선 (CSS)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 서비스 헤더
st.title("🧭 StockCompass AI")
st.markdown("#### 데이터로 정밀 진단하는 당신의 투자 나침반")
st.caption("성장성(PER) + 안정성(배당) + 시장 심리(뉴스)를 종합 분석하여 고점 여부를 판단합니다.")

# 3. 섹터 데이터베이스
SECTORS = {
    "미국 M7 (빅테크)": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"],
    "글로벌 반도체": ["NVDA", "AMD", "ASML", "TSM", "INTC", "MU", "AVGO"],
    "K-반도체 & 가전": ["005930.KS", "000660.KS", "066570.KS", "000990.KS"],
    "K-배터리 & 소재": ["373220.KS", "006400.KS", "051910.KS", "003670.KS", "247540.KQ"],
    "방산 & 우주항공": ["047810.KS", "012450.KS", "073190.KS", "LMT", "PLTR", "RTX"],
    "로봇 & AI": ["ISRG", "041510.KS", "220630.KQ", "TER", "PATH", "BOTZ"],
    "바이오 & 헬스케어": ["LLY", "NVO", "207940.KS", "068270.KS", "PFE", "JNJ"]
}

# 4. 핵심 기능 함수들
def analyze_sentiment(news_list):
    """뉴스 헤드라인 감성 분석"""
    if not news_list: return "😐 데이터 없음"
    pos_words = ['buy', 'growth', 'positive', 'up', 'increase', 'bull', 'strong', 'profit', 'beat', 'ahead']
    neg_words = ['sell', 'decline', 'negative', 'down', 'decrease', 'bear', 'weak', 'loss', 'risk', 'miss']
    score = 0
    for news in news_list:
        title = news.get('title', '').lower()
        score += sum(1 for pw in pos_words if pw in title)
        score -= sum(1 for nw in neg_words if nw in title)
    if score > 0: return "📈 긍정 (Bullish)"
    elif score < 0: return "📉 부정 (Bearish)"
    else: return "😐 중립 (Neutral)"

def get_safe_stock_data(ticker_symbol):
    """실패 없는 데이터 수집을 위한 안전 장치 로직"""
    try:
        stock = yf.Ticker(ticker_symbol)
        # .info 가 실패할 경우를 대비해 기본 데이터 우선 추출
        info = stock.info
        
        # 최소한 현재가 정보는 있어야 분석 가능
        current_price = info.get('currentPrice') or info.get('regularMarketPreviousClose')
        if not current_price:
            return None

        return {
            "티커": ticker_symbol,
            "기업명": info.get('shortName', ticker_symbol),
            "현재가": current_price,
            "PER": info.get('trailingPE', 0) or info.get('forwardPE', 0) or 0,
            "매출성장률(%)": (info.get('revenueGrowth', 0) or 0) * 100,
            "배당수익률(%)": (info.get('dividendYield', 0) or 0) * 100,
            "영업이익률(%)": (info.get('operatingMargins', 0) or 0) * 100,
            "시총(B)": round(info.get('marketCap', 0) / 1e9, 2) if info.get('marketCap') else 0,
            "뉴스": stock.news[:5] if hasattr(stock, 'news') else []
        }
    except Exception:
        return None

@st.cache_data(ttl=3600)
def fetch_all_sector_data(tickers):
    results = []
    failed = []
    for t in tickers:
        t = t.strip()
        data = get_safe_stock_data(t)
        if data:
            data['뉴스감성'] = analyze_sentiment(data['뉴스'])
            results.append(data)
        else:
            failed.append(t)
    return pd.DataFrame(results), failed

# 5. 사이드바 UI
st.sidebar.header("🎯 분석 설정")
selected_name = st.sidebar.selectbox("섹터 선택", list(SECTORS.keys()))
ticker_input = st.sidebar.text_area("종목 편집 (쉼표 구분)", value=", ".join(SECTORS[selected_name]))

# 6. 메인 실행 로직
if st.sidebar.button("🔍 나침반 가동"):
    ticker_list = [x.strip() for x in ticker_input.split(",") if x.strip()]
    
    with st.spinner('실시간 시장 데이터를 분석 중입니다...'):
        df, failed_list = fetch_all_sector_data(ticker_list)

    if failed_list:
        st.warning(f"⚠️ 일부 데이터를 가져오지 못했습니다: {', '.join(failed_list)}")
        st.caption("팁: 한국 주식은 종목코드 뒤에 .KS(코스피) 또는 .KQ(코스닥)를 붙여주세요.")

    if not df.empty:
        # 요약 메트릭
        avg_per = df[df['PER'] > 0]['PER'].mean()
        avg_div = df['배당수익률(%)'].mean()
        
        st.subheader(f"📍 {selected_name} 섹터 정밀 리포트")
        col1, col2, col3 = st.columns(3)
        col1.metric("섹터 평균 PER", f"{avg_per:.1f}배")
        col2.metric("평균 배당수익률", f"{avg_div:.2f}%")
        col3.metric("분석 종목 수", f"{len(df)}개")

        # 시각화: PER vs 배당수익률 (뉴스 감성 포함)
        st.divider()
        st.write("### 🧭 가치 & 안전성 매트릭스")
        
        
        
        fig = px.scatter(df, x="PER", y="배당수익률(%)", size="시총(B)",
                         text="티커", color="뉴스감성",
                         color_discrete_map={
                             "📈 긍정 (Bullish)": "#2ecc71", 
                             "📉 부정 (Bearish)": "#e74c3c", 
                             "😐 중립 (Neutral)": "#95a5a6",
                             "😐 데이터 없음": "#34495e"
                         },
                         template="plotly_dark",
                         hover_name="기업명")
        
        fig.add_vline(x=avg_per, line_dash="dash", line_color="orange", annotation_text="평균 PER")
        st.plotly_chart(fig, use_container_width=True)

        # 상세 데이터 테이블
        st.subheader("📋 상세 분석 시트")
        st.dataframe(df.drop(columns=['뉴스']).style.background_gradient(subset=['배당수익률(%)'], cmap='Greens')
                         .background_gradient(subset=['매출성장률(%)'], cmap='Blues'))

        # 종목별 AI 진단
        st.divider()
        st.subheader("💡 StockCompass AI 최종 진단")
        
        for _, row in df.iterrows():
            with st.expander(f"🔍 {row['기업명']} ({row['티커']}) 심층 분석"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**현재가:** {row['현재가']:,}")
                    st.write(f"**PER:** {row['PER']:.2f} (평균 대비 {'높음' if row['PER'] > avg_per else '낮음'})")
                    st.write(f"**뉴스 감성:** {row['뉴스감성']}")
                with c2:
                    # 복합 진단 로직
                    if "긍정" in row['뉴스감성'] and row['PER'] < avg_per:
                        st.success("✨ **[강력 추천]** 호재가 있고 밸류에이션이 낮습니다. 매수 기회입니다.")
                    elif row['PER'] > avg_per * 1.5 and "부정" in row['뉴스감성']:
                        st.error("🚨 **[고점 경고]** 주가는 비싼데 뉴스는 부정적입니다. 단기 고점일 확률이 높습니다.")
                    elif row['배당수익률(%)'] > 3.5:
                        st.info("💎 **[안전 자산]** 배당 수익률이 높아 하락장에서 방어력이 좋습니다.")
                    else:
                        st.warning("😐 **[관망]** 뚜렷한 매수/매도 신호가 없는 중립 구간입니다.")
    else:
        st.error("데이터 로딩에 실패했습니다. 모든 티커가 유효한지 확인해주세요.")
