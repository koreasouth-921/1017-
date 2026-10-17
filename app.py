import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="서울 연평균기온 분석", layout="wide")

# ─────────────────────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    # encoding='utf-8-sig' : BOM 처리
    # .str.strip()        : 날짜 열 앞쪽 탭 문자 제거
    df = pd.read_csv('seoul_temperature.csv', encoding='utf-8-sig')
    df['날짜'] = df['날짜'].str.strip()
    df['날짜'] = pd.to_datetime(df['날짜'])
    df['연도'] = df['날짜'].dt.year
    return df

df = load_data()

# ─────────────────────────────────────────────────────────
# 연도별 통계 집계
# ─────────────────────────────────────────────────────────
annual = df.groupby('연도').agg(
    연평균기온=('평균기온(℃)', 'mean'),
    평균최고기온=('최고기온(℃)', 'mean'),
    평균최저기온=('최저기온(℃)', 'mean'),
    관측일수=('날짜', 'count')
).reset_index()

# 관측일수 360일 미만인 해는 연평균 계산에서 제외
annual_valid = annual[annual['관측일수'] >= 360].sort_values('연도').reset_index(drop=True)

# 전체 연도 범위 생성 (결측 연도 표시용)
min_year = int(annual_valid['연도'].min())
max_year = int(annual_valid['연도'].max())
all_years = pd.DataFrame({'연도': range(min_year, max_year + 1)})

annual_full = all_years.merge(
    annual_valid[['연도', '연평균기온', '평균최고기온', '평균최저기온']],
    on='연도', how='left'
)

# 5년 이동평균 — 다섯 해 모두 값이 있을 때만 계산 (min_periods=5)
annual_full['5년_이동평균'] = (
    annual_full['연평균기온'].rolling(window=5, min_periods=5).mean()
)

# ─────────────────────────────────────────────────────────
# 사이드바 연도 범위 슬라이더
# ─────────────────────────────────────────────────────────
year_range = st.sidebar.slider(
    '연도 범위 선택',
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

# 선택 구간 필터링
mask = (annual_full['연도'] >= year_range[0]) & (annual_full['연도'] <= year_range[1])
selected = annual_full[mask]

# 선택 구간 통계
mean_avg  = selected['연평균기온'].mean()
mean_max  = selected['평균최고기온'].mean()
mean_min  = selected['평균최저기온'].mean()

# ─────────────────────────────────────────────────────────
# 그래프 생성
# ─────────────────────────────────────────────────────────
fig = go.Figure()

# 연평균기온 꺾은선 (결측 연도는 NaN → 선이 끊김)
fig.add_trace(go.Scatter(
    x=annual_full['연도'],
    y=annual_full['연평균기온'],
    mode='lines+markers',
    name='연평균기온',
    line=dict(color='#E63946', width=2),
    marker=dict(symbol='circle', size=4, color='#E63946'),
    connectgaps=False
))

# 5년 이동평균선 (결측 구간 포함 자동 단절)
fig.add_trace(go.Scatter(
    x=annual_full['연도'],
    y=annual_full['5년_이동평균'],
    mode='lines+markers',
    name='5년 이동평균',
    line=dict(color='#1D3557', width=2),
    marker=dict(symbol='circle', size=3, color='#1D3557'),
    connectgaps=False
))

fig.update_layout(
    title='서울 연평균기온 및 5년 이동평균',
    xaxis_title='연도',
    yaxis_title='기온 (℃)',
    hovermode='x unified',
    legend=dict(x=0.02, y=0.98, traceorder='normal'),
    margin=dict(l=50, r=30, t=60, b=50),
    height=500
)

# ─────────────────────────────────────────────────────────
# 화면 출력
# ─────────────────────────────────────────────────────────
st.title('서울 연평균기온 분석')

st.plotly_chart(fig, use_container_width=True)

st.subheader('선택 구간 통계')
col1, col2, col3 = st.columns(3)
with col1:
    st.metric('연평균기온', f'{mean_avg:.2f} ℃')
with col2:
    st.metric('평균 최고기온', f'{mean_max:.2f} ℃')
with col3:
    st.metric('평균 최저기온', f'{mean_min:.2f} ℃')

st.caption(f'선택 구간: {year_range[0]}년 ~ {year_range[1]}년 ({len(selected)}개 연도)')
