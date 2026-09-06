import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ACI Mortar Designer - Proporcional", layout="wide")

# --- CSS PARA CONTRASTE ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f9 !important; }
    [data-testid="stSidebar"] label { color: white !important; font-weight: bold; }
    div[data-testid="stMetric"] {
        background-color: #1E3A8A !important;
        border: 2px solid #1E40AF !important;
        border-radius: 12px;
        padding: 15px;
    }
    div[data-testid="stMetricValue"] > div { color: #FFFFFF !important; font-size: 1.8rem !important; }
    div[data-testid="stMetricLabel"] > div { color: #CBD5E1 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: MATERIALES ---
st.sidebar.title("🛠️ Configuración Base")

with st.sidebar.expander("🧱 Propiedades de Polvos"):
    c_den = st.number_input("Dens. Cemento", value=2.85)
    c_cost = st.number_input("Costo Cemento (USD/kg)", value=0.175, format="%.3f")
    c_gwp = st.number_input("GWP Cemento", value=0.90)
    l_den = st.number_input("Dens. Limestone", value=2.711)
    l_cost = st.number_input("Costo Limestone", value=0.040, format="%.3f")
    st.divider()
    ex_p_name = st.text_input("Polvo Extra", value="Fly Ash")
    ex_p_den = st.number_input(f"Dens. {ex_p_name}", value=2.20)
    ex_p_cost = st.number_input(f"Costo {ex_p_name}", value=0.150)

with st.sidebar.expander("🧪 Aditivos y Factores"):
    s_den = st.number_input("Dens. Arena", value=2.65)
    s_cost = st.number_input("Costo Arena", value=0.015)
    st.info("Factores de corrección por aditivos:")
    f_polvo = st.slider("Factor Polvo (0.4 en tu código)", 0.0, 1.0, 0.4, 0.1)
    f_agua = st.slider("Factor Agua (0.6 en tu código)", 0.0, 1.0, 0.6, 0.1)
    st.divider()
    v1_den = st.number_input("Dens. Plastificante (V1)", value=1.11)
    v1_cost = st.number_input("Costo V1", value=3.75)
    v2_den = st.number_input("Dens. Acelerante (V2)", value=1.25)
    v2_cost = st.number_input("Costo V2", value=1.95)

# --- ESCALAMIENTO DE LA MUESTRA ---
st.sidebar.divider()
st.sidebar.subheader("⚖️ Escalamiento de Muestra")
vol_referencia = st.sidebar.number_input("Volumen Referencia (100%) [ml]", value=1000)
porcentaje_escala = st.sidebar.slider("% de Mezcla a Realizar (Caso %)", 10, 100, 60, 5)
vol_real = vol_referencia * (porcentaje_escala / 100)

# --- PARÁMETROS DE DISEÑO ---
st.sidebar.subheader("🧪 Diseño de Mezcla")
S_val = st.sidebar.slider("S (Fracción Arena)", 0.60, 0.99, 0.70, 0.01)
W_val = st.sidebar.slider("W (Agua/Polvo)", 0.00, 0.50, 0.25, 0.01)
C_val = st.sidebar.slider("% Cemento (mín 50%)", 0.50, 1.00, 0.50, 0.05)
ExP_val = st.sidebar.slider(f"% {ex_p_name}", 0.0, 0.50, 0.00, 0.05)

V1_val = st.sidebar.number_input("V1 ml", 0.0, 50.0, 2.5)
V2_val = st.sidebar.number_input("V2 ml", 0.0, 50.0, 0.0)

# --- MOTOR DE CÁLCULO ---
def calcular_motor(S, W, C, ExP, v1, v2, ml_objetivo):
    m_ads = (v1 * v1_den) + (v2 * v2_den)
    M_arena_base = 1000
    
    # Aplicación de los factores configurables (f_polvo y f_agua)
    M_polvo_base = ((M_arena_base * (1 - S) / S) - (f_polvo * m_ads)) / (1 + W)
    M_agua_base = M_polvo_base * W - (f_agua * m_ads)
    
    L = max(0, 1.0 - C - ExP)
    m_cem = M_polvo_base * C
    m_exp = M_polvo_base * ExP
    m_lim = M_polvo_base * L
    
    vol_teorico = (m_cem/c_den + m_lim/l_den + m_exp/ex_p_den + M_arena_base/s_den + M_agua_base/1.0 + v1 + v2)
    k_lab = ml_objetivo / vol_teorico
    
    res_lab = {
        "Cemento": m_cem * k_lab, "Limestone": m_lim * k_lab, ex_p_name: m_exp * k_lab,
        "Arena": M_arena_base * k_lab, "Agua": M_agua_base * k_lab, 
        "V1": v1 * k_lab, "V2": v2 * k_lab
    }
    
    # Puntajes (Siempre sobre escala industrial de 990L para que la comparación sea justa)
    k_990 = 990 / vol_teorico
    costo = ( (m_cem*k_990)*c_cost + (m_lim*k_990)*l_cost + (m_exp*k_990)*ex_p_cost + (M_arena_base*k_990)*s_cost + (v1*k_990)*v1_cost + (v2*k_990)*v2_cost )
    co2 = ( (m_cem*k_990)*c_gwp + (m_lim*k_990)*0.06 + (M_arena_base*k_990)*0.01 + (v1*k_990)*2.1 )
    
    p_costo = 100 - (costo - 100) / 1.5
    p_co2 = 100 - (co2 - 200) / 3
    p_total = (0.05 * p_costo + 0.1 * p_co2) / 0.85
    
    return res_lab, costo, co2, p_total

# Ejecución
m_lab, cost_ind, co2_ind, score = calcular_motor(S_val, W_val, C_val, ExP_val, V1_val, V2_val, vol_real)

# --- INTERFAZ ---
st.title(f"🏗️ Diseño Proporcional: Caso {porcentaje_escala}%")
st.write(f"Preparando **{vol_real:.1f} ml** (escalado de una muestra de {vol_referencia} ml)")

col1, col2, col3 = st.columns(3)
col1.metric("🏆 PUNTAJE (IND)", f"{score:.2f}")
col2.metric("💵 COSTO/m³", f"${cost_ind:.2f}")
col3.metric("🌱 CO2/m³", f"{co2_ind:.2f}")

tab1, tab2, tab3 = st.tabs(["📋 Receta del Caso", "📊 Mapa de Optimización", "📉 Granulometría"])

with tab1:
    st.subheader(f"Masas para preparar {vol_real:.1f} ml")
    df_receta = pd.DataFrame({
        "Material": ["Cemento", "Limestone", ex_p_name, "Arena", "Agua", "V1 (Plast)", "V2 (Acel)"],
        "Cantidad": [m_lab["Cemento"], m_lab["Limestone"], m_lab[ex_p_name], m_lab["Arena"], m_lab["Agua"], m_lab["V1"], m_lab["V2"]],
        "Unidad": ["g", "g", "g", "g", "g", "ml", "ml"]
    })
    st.table(df_receta.style.format({"Cantidad": "{:.2f}"}))
    st.warning(f"⚠️ Estas masas son solo para el {porcentaje_escala}% de la muestra total.")

with tab2:
    st.subheader("Mapa de Calor: Arena (X) vs Agua (Y)")
    res = 30
    s_ax = np.linspace(0.60, 0.99, res)
    w_ax = np.linspace(0.00, 0.50, res)
    z = np.array([[calcular_motor(s, w, C_val, ExP_val, V1_val, V2_val, vol_real)[3] for s in s_ax] for w in w_ax])
    
    fig = go.Figure(data=go.Contour(z=z, x=s_ax, y=w_ax, colorscale='Turbo'))
    fig.add_trace(go.Scatter(x=[S_val], y=[W_val], mode='markers', marker=dict(color='white', size=12, symbol='x')))
    fig.update_layout(xaxis_title="Fracción Arena (S)", yaxis_title="Agua/Polvo (W)")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Granulometría para el Caso Seleccionado")
    m_arena_caso = m_lab["Arena"]
    st.write(f"Masa de arena para este batch: **{m_arena_caso:.2f} g**")
    
    tamices = ["N° 4", "N° 8", "N° 16", "N° 30", "N° 50", "N° 100"]
    cols = st.columns(6)
    rets = [cols[i].number_input(f"% {tamices[i]}", 0, 100, 15, key=f"gr_{i}") for i in range(6)]
    
    acum = 0
    tabla_g = []
    for i, t in enumerate(tamices):
        m_r = m_arena_caso * (rets[i]/100)
        acum += rets[i]
        tabla_g.append([t, f"{m_r:.2f}g", f"{100-acum:.1f}%"])
    
    st.table(pd.DataFrame(tabla_g, columns=["Tamiz", "Masa a Retener", "% Pasa"]))

st.caption("v7.0 - Soporte para Batch Proporcional (40%/60%) y factores de aditivo configurables.")
