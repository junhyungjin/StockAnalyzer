import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="AI 주식 가치 분석기", layout="wide")

st.title("📈 미래 가치 기반 주식 고점 판단기")
st.markdown("매출 성장률과 미래 PER을 계산하여 현재 주가의 위치를 진단합니다.")

# 사이드바: 입력부
st.sidebar.header("🔍 기업 정보 입력")
ticker = st.sidebar.text_input("티커 입력 (예: TSLA, 005930.KS)", value="AAPL")

if ticker:
    try:
        data = yf.Ticker(ticker)
        info = data.info
        name = info.get('longName', 'Unknown')
        current_price = info.get('currentPrice', 0)
        currency = info.get('currency', 'USD')
        revenue = info.get('totalRevenue', 0)
        shares = info.get('sharesOutstanding', 1)

        st.subheader(f"[{name}] 분석 리포트")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("현재 주가", f"{current_price:,.2f} {currency}")
        col2.metric("현재 매출액", f"{revenue/100000000:,.1f} 억")
        col3.metric("발행 주식 수", f"{shares/1000000:,.1f} M")

        st.divider()

        # 사용자 시뮬레이션 입력
        st.sidebar.subheader("🚀 성장 가시성 설정")
        growth_rate = st.sidebar.slider("연평균 매출 성장률 (%)", 0, 100, 15) / 100
        margin = st.sidebar.slider("목표 순이익률 (%)", 1, 50, 10) / 100
        target_per = st.sidebar.number_input("5년 후 적정 PER", value=20)

        # 계산 로직
        future_rev = revenue * ((1 + growth_rate) ** 5)
        future_net_inc = future_rev * margin
        future_eps = future_net_inc / shares
        target_price = future_eps * target_per
        upside = ((target_price - current_price) / current_price) * 100
        forward_per = (current_price * shares) / future_net_inc

        # 결과 시각화
        c1, c2 = st.columns(2)
        
        with c1:
            st.write("### 📊 가치 평가 지표")
            res_df = pd.DataFrame({
                "항목": ["5년 후 예상 매출", "5년 후 예상 순이익", "5년 후 목표 주가", "5년 선행 PER", "예상 총 수익률"],
                "수치": [f"{future_rev/100000000:,.1f} 억", f"{future_net_inc/100000000:,.1f} 억", 
                        f"{target_price:,.2f} {currency}", f"{forward_per:.2f} 배", f"{upside:.2f} %"]
            })
            st.table(res_df)

        with c2:
            st.write("### ⚖️ 판단 결과")
            if upside > 50:
                st.success(f"**[강력 매수 추천]**\n\n현재 주가는 미래 가치 대비 매우 저렴합니다. 목표가까지 {upside:.1f}% 상승 여력이 있습니다.")
            elif 10 <= upside <= 50:
                st.info(f"**[매수/보유]**\n\n성장성이 주가에 반영 중이며, 완만한 상승이 기대됩니다.")
            elif -15 <= upside < 10:
                st.warning(f"**[보유/관망]**\n\n현재 주가는 이미 '적정가' 근처(고점 신호)입니다.")
            else:
                st.error(f"**[매도/주의]**\n\n주가가 미래 가치를 크게 앞질렀습니다. 역사적 고점일 가능성이 높습니다.")

        # 차트 추가
        fig = go.Figure()
        fig.add_trace(go.Bar(x=['현재가', '5년 후 목표가'], y=[current_price, target_price], marker_color=['gray', 'blue']))
        fig.update_layout(title="현재가 vs 5년 후 목표가 비교", ylabel=currency)
        st.plotly_chart(fig)

    except Exception as e:
        st.error(f"데이터를 불러올 수 없습니다. 티커를 확인하세요: {e}")
