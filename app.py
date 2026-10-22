import streamlit as st
import numpy as np
import plotly.graph_objects as go

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="이원계 합금 상태도 및 레버 법칙 시뮬레이터",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 이원계 합금 상태도 & 레버 법칙 시뮬레이터")
st.markdown("""
신소재공학과 열역학/상변화 이론에 기반한 인터랙티브 시뮬레이터입니다.  
온도와 조성을 조절하여 현재 상(Phase)의 상태와 **레버 법칙(Lever Rule)**에 따른 고상/액상 분율을 확인하세요.
""")

st.sidebar.header("⚙️ 실험 조건 설정")

# ---------------------------------------------------------
# State Diagram Parameters Definition (가상의 A-B 공정 상태도)
# ---------------------------------------------------------
T_melt_A = 1000  # A 순금속 융점 (°C)
T_melt_B = 800   # B 순금속 융점 (°C)
T_eutectic = 500 # 공정 온도 (°C)
C_eutectic = 60  # 공정 조성 (wt% B)

C_alpha_max = 15 # 알파상 최대 고용도 (wt% B)
C_beta_max = 85  # 베타상 최대 고용도 (wt% B)

# ---------------------------------------------------------
# Sidebar Inputs
# ---------------------------------------------------------
composition = st.sidebar.slider(
    "전체 조성 $C_0$ (wt% B)",
    min_value=0.0,
    max_value=100.0,
    value=40.0,
    step=0.5
)

temperature = st.sidebar.slider(
    "온도 $T$ (°C)",
    min_value=200.0,
    max_value=1100.0,
    value=650.0,
    step=5.0
)

# ---------------------------------------------------------
# Dynamic Boundary Functions
# ---------------------------------------------------------
def get_liquidus_alpha(T):
    """Liquid - Liquid+Alpha 경계선"""
    if T < T_eutectic or T > T_melt_A:
        return None
    return C_eutectic * (T_melt_A - T) / (T_melt_A - T_eutectic)

def get_liquidus_beta(T):
    """Liquid - Liquid+Beta 경계선"""
    if T < T_eutectic or T > T_melt_B:
        return None
    return C_eutectic + (100 - C_eutectic) * (T - T_eutectic) / (T_melt_B - T_eutectic)

def get_solvus_alpha(T):
    """Alpha 고용 한계선"""
    if T > T_eutectic:
        return None
    return C_alpha_max * (T / T_eutectic)

def get_solvus_beta(T):
    """Beta 고용 한계선"""
    if T > T_eutectic:
        return None
    return 100 - (100 - C_beta_max) * (T / T_eutectic)

# ---------------------------------------------------------
# Phase & Lever Rule Calculation Logic
# ---------------------------------------------------------
phase_str = ""
w_alpha, w_beta, w_liquid = 0.0, 0.0, 0.0
c_alpha, c_beta, c_liquid = None, None, None

C_L_a = get_liquidus_alpha(temperature)
C_L_b = get_liquidus_beta(temperature)

if temperature > T_melt_A and temperature > T_melt_B:
    phase_str = "액상 (Liquid)"
    w_liquid = 100.0
elif temperature >= T_eutectic:
    # 단상 또는 2상 영역 (상부 영역)
    if C_L_a is not None and composition < (C_alpha_max * (temperature - T_eutectic)/(T_melt_A - T_eutectic) + C_alpha_max): # 알파 단상 근사
        c_a_bound = (C_alpha_max * (temperature - T_eutectic)/(T_melt_A - T_eutectic) + C_alpha_max)
        if composition <= C_L_a:
            phase_str = "액상 + $\\alpha$상 (Liquid + $\\alpha$)"
            c_alpha = C_L_a * (1 - (temperature - T_eutectic)/(T_melt_A - T_eutectic)) # 단순 선형 모델링
            c_liquid = C_L_a
            if c_liquid != c_alpha:
                w_liquid = max(0.0, min(100.0, (composition - c_alpha) / (c_liquid - c_alpha) * 100))
                w_alpha = 100.0 - w_liquid
        else:
            phase_str = "액상 (Liquid)"
            w_liquid = 100.0
    elif C_L_b is not None and composition >= C_L_b:
        phase_str = "액상 + $\\beta$상 (Liquid + $\\beta$)"
        c_liquid = C_L_b
        c_beta = C_L_b + (100 - C_L_b) * 0.5
        if c_beta != c_liquid:
            w_beta = max(0.0, min(100.0, (composition - c_liquid) / (c_beta - c_liquid) * 100))
            w_liquid = 100.0 - w_beta
    else:
        # Liquid + Alpha or Liquid + Beta 2상 영역 레버 법칙 처리
        if composition <= C_eutectic:
            c_liquid = C_L_a
            c_alpha = C_alpha_max * (temperature - T_eutectic) / (T_melt_A - T_eutectic)
            phase_str = "액상 + $\\alpha$상 (Liquid + $\\alpha$)"
            if c_liquid is not None and c_alpha is not None and c_liquid != c_alpha:
                w_liquid = (composition - c_alpha) / (c_liquid - c_alpha) * 100
                w_alpha = 100.0 - w_liquid
            else:
                phase_str = "액상 (Liquid)"
                w_liquid = 100.0
        else:
            c_liquid = C_L_b
            c_beta = 100 - (100 - C_beta_max) * (temperature - T_eutectic) / (T_melt_B - T_eutectic)
            phase_str = "액상 + $\\beta$상 (Liquid + $\\beta$)"
            if c_liquid is not None and c_beta is not None and c_beta != c_liquid:
                w_liquid = (c_beta - composition) / (c_beta - c_liquid) * 100
                w_beta = 100.0 - w_liquid
            else:
                phase_str = "액상 (Liquid)"
                w_liquid = 100.0
else:
    # T < T_eutectic (고상 영역)
    c_a_sol = get_solvus_alpha(temperature)
    c_b_sol = get_solvus_beta(temperature)
    
    if composition <= c_a_sol:
        phase_str = "단상 고상 ( $\\alpha$ Phase )"
        w_alpha = 100.0
    elif composition >= c_b_sol:
        phase_str = "단상 고상 ( $\\beta$ Phase )"
        w_beta = 100.0
    else:
        phase_str = "2상 고상 ( $\\alpha + \\beta$ Phase )"
        c_alpha = c_a_sol
        c_beta = c_b_sol
        if c_beta != c_alpha:
            w_beta = (composition - c_alpha) / (c_beta - c_alpha) * 100
            w_alpha = 100.0 - w_beta

# 오차로 인한 범위 제한 처리
w_liquid = max(0.0, min(100.0, w_liquid))
w_alpha = max(0.0, min(100.0, w_alpha))
w_beta = max(0.0, min(100.0, w_beta))

# ---------------------------------------------------------
# Layout Layout Setup (2 Columns)
# ---------------------------------------------------------
col1, col2 = st.columns([1.2, 1])

with col1:
    st.subheader("📈 이원계 공정 상태도 (Phase Diagram)")
    
    fig = go.Figure()

    # 액상선/고상선 등 경계 선 그리기
    # 1. Liquidus Alpha (Melting A to Eutectic)
    fig.add_trace(go.Scatter(x=[0, C_eutectic], y=[T_melt_A, T_eutectic], mode='lines', line=dict(color='blue', width=2), name='Liquidus'))
    # 2. Liquidus Beta (Melting B to Eutectic)
    fig.add_trace(go.Scatter(x=[100, C_eutectic], y=[T_melt_B, T_eutectic], mode='lines', line=dict(color='blue', width=2), showlegend=False))
    # 3. Solidus / Solvus Alpha
    fig.add_trace(go.Scatter(x=[0, C_alpha_max, 0], y=[T_melt_A, T_eutectic, 0], mode='lines', line=dict(color='green', width=2), name='Solvus/Solidus'))
    # 4. Solidus / Solvus Beta
    fig.add_trace(go.Scatter(x=[100, C_beta_max, 100], y=[T_melt_B, T_eutectic, 0], mode='lines', line=dict(color='green', width=2), showlegend=False))
    # 5. Eutectic Line
    fig.add_trace(go.Scatter(x=[C_alpha_max, C_beta_max], y=[T_eutectic, T_eutectic], mode='lines', line=dict(color='red', width=2, dash='dash'), name='Eutectic Line (500°C)'))

    # 영역 텍스트 표기
    fig.add_annotation(x=50, y=900, text="<b>Liquid</b>", showarrow=False, font=dict(size=14))
    fig.add_annotation(x=5, y=300, text="<b>α</b>", showarrow=False, font=dict(size=14))
    fig.add_annotation(x=95, y=300, text="<b>β</b>", showarrow=False, font=dict(size=14))
    fig.add_annotation(x=50, y=300, text="<b>α + β</b>", showarrow=False, font=dict(size=14))

    # 타이 라인 (Tie-line) 표시 (2상 영역일 때)
    if (w_liquid > 0 and w_alpha > 0 and c_liquid is not None and c_alpha is not None):
        fig.add_trace(go.Scatter(x=[c_alpha, c_liquid], y=[temperature, temperature], mode='lines+markers', line=dict(color='orange', width=3), name='Tie-line'))
    elif (w_liquid > 0 and w_beta > 0 and c_liquid is not None and c_beta is not None):
        fig.add_trace(go.Scatter(x=[c_liquid, c_beta], y=[temperature, temperature], mode='lines+markers', line=dict(color='orange', width=3), name='Tie-line'))
    elif (w_alpha > 0 and w_beta > 0 and c_alpha is not None and c_beta is not None):
        fig.add_trace(go.Scatter(x=[c_alpha, c_beta], y=[temperature, temperature], mode='lines+markers', line=dict(color='orange', width=3), name='Tie-line'))

    # 현재 상태 좌표 표시 (Red Point)
    fig.add_trace(go.Scatter(
        x=[composition], y=[temperature],
        mode='markers',
        marker=dict(size=12, color='red', symbol='cross'),
        name=f'현재 상태 ({composition} wt%, {temperature}°C)'
    ))

    fig.update_layout(
        xaxis_title="조성 Composition (wt% B)",
        yaxis_title="온도 Temperature (°C)",
        xaxis=dict(range=[0, 100]),
        yaxis=dict(range=[0, 1100]),
        height=500,
        margin=dict(l=20, r=20, t=30, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 레버 법칙(Lever Rule) 분석 결과")
    
    st.info(f"**현재 관찰되는 상:** {phase_str}")
    
    st.markdown("#### 상 분율 (Phase Fraction)")
    st.progress(int(w_liquid), text=f"액상 (Liquid): {w_liquid:.1f}%")
    st.progress(int(w_alpha), text=f"α 고상 (Alpha): {w_alpha:.1f}%")
    st.progress(int(w_beta), text=f"β 고상 (Beta): {w_beta:.1f}%")

    st.markdown("---")
    st.markdown("#### 📐 각 상의 조성 (Phase Composition)")
    
    col_a, col_b, col_l = st.columns(3)
    with col_a:
        st.metric("α상 조성", f"{c_alpha:.1f} wt% B" if c_alpha is not None else "-")
    with col_b:
        st.metric("β상 조성", f"{c_beta:.1f} wt% B" if c_beta is not None else "-")
    with col_l:
        st.metric("액상 조성", f"{c_liquid:.1f} wt% B" if c_liquid is not None else "-")

    # 수식 안내
    with st.expander("💡 레버 법칙 계산 수식 보기"):
        st.latex(r"W_L = \frac{C_0 - C_\alpha}{C_L - C_\alpha}")
        st.latex(r"W_\alpha = \frac{C_L - C_0}{C_L - C_\alpha}")
        st.caption("※ $C_0$: 전체 조성, $C_L$: 액상선 조성, $C_a$: 고상선 조성")
