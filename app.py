import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ACI Mortar Master Pro 2026", layout="wide")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f9 !important; }
    [data-testid="stSidebar"] label { color: white !important; font-weight: bold; }
    div[data-testid="stMetric"] {
        background-color: #1E3A8A !important;
        border: 2px solid #1E40AF !important;
        border-radius: 12px; padding: 15px;
    }
    div[data-testid="stMetricValue"] > div { color: white !important; font-size: 1.8rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: MATERIALES ---
st.sidebar.title("⚙️ Configuración")

with st.sidebar.expander("🧱 Polvos y Cementos"):
    c_den = st.number_input("Dens. Cemento", value=2.85)
    c_cost = st.number_input("Costo Cemento (USD/kg)", value=0.175, format="%.3f")
    c_gwp = st.number_input("GWP Cemento", value=0.90)
    l_den = st.number_input("Dens. Limestone", value=2.711)
    l_cost = st.number_input("Costo Limestone", value=0.040, format="%.3f")
    st.divider()
    ex_p_name = st.text_input("Nombre Polvo Extra", value="Fly Ash")
    ex_p_den = st.number_input(f"Dens. {ex_p_name}", value=2.20)
    ex_p_cost = st.number_input(f"Costo {ex_p_name}", value=0.150)
    ex_p_gwp = st.number_input(f"GWP {ex_p_name}", value=0.04)

with st.sidebar.expander("🧪 Aditivos y Factores"):
    st.write("**Factores de Corrección (Masa Aditivo)**")
    f_polvo = st.number_input("Factor que desplaza Polvo (Sólidos)", value=0.4, step=0.1)
    f_agua = st.number_input("Factor que aporta Agua (Líquidos)", value=0.6, step=0.1)
    
    st.divider()
    v1_name = st.text_input("Aditivo 1", value="Plastificante")
    v1_den = st.number_input(f"Dens. {v1_name}", value=1.11)
    v1_cost = st.number_input(f"Costo {v1_name} (USD/ml)", value=3.75)
    
    v2_name = st.text_input("Aditivo 2", value="Acelerante")
    v2_den = st.number_input(f"Dens. {v2_name}", value=1.25)
    v2_cost = st.number_input(f"Costo {v2_name} (USD/ml)", value=1.95)
    
    v3_name = st.text_input("Aditivo 3", value="Extra Aditivo")
    v3_den = st.number_input(f"Dens. {v3_name}", value=1.10)
    v3_cost = st.number_input(f"Costo {v3_name} (USD/ml)", value=0.00)

# --- ESCALAMIENTO Y DISEÑO ---
st.sidebar.divider()
st.sidebar.subheader("⚖️ Escalamiento de Muestra")
vol_referencia = st.sidebar.number_input("Volumen Referencia (100%) [ml]", value=1500)
porcentaje_escala = st.sidebar.slider("% de Mezcla (Batch Scale)", 10, 100, 60, 5)
vol_real = vol_referencia * (porcentaje_escala / 100)

st.sidebar.subheader("🧪 Parámetros de Diseño")
S_val = st.sidebar.slider("S (Fracción Arena)", 0.60, 0.99, 0.70, 0.01)
W_val = st.sidebar.slider("W (Agua/Polvo)", 0.00, 0.50, 0.25, 0.01)
C_val = st.sidebar.slider("% Cemento (mín 50%)", 0.50, 1.00, 0.50, 0.05)
ExP_val = st.sidebar.slider(f"% {ex_p_name}", 0.0, 0.50, 0.00, 0.05)

V1_val = st.sidebar.number_input(f"{v1_name} (ml)", 0.0, 50.0, 2.5)
V2_val = st.sidebar.number_input(f"{v2_name} (ml)", 0.0, 50.0, 0.0)
V3_val = st.sidebar.number_input(f"{v3_name} (ml)", 0.0, 50.0, 0.0)

# --- MOTOR DE CÁLCULO (Lógica Original Optimizada) ---
def engine(S, W, C, ExP, v1, v2, v3, ml_objetivo):
    # Masa de aditivos total (V * Densidad)
    m_ads = (v1 * v1_den) + (v2 * v2_den) + (v3 * v3_den)
    
    # Fórmulas del código base
    M_arena_base = 1000
    M_polvo_base = ((M_arena_base * (1 - S) / S) - (f_polvo * m_ads)) / (1 + W)
    M_agua_base = M_polvo_base * W - (f_agua * m_ads)
    
    L = max(0, 1.0 - C - ExP)
    m_cem = M_polvo_base * C
    m_exp = M_polvo_base * ExP
    m_lim = M_polvo_base * L
    
    # Volumen Total para K
    vol_t = (m_cem/c_den + m_lim/l_den + m_exp/ex_p_den + M_arena_base/2.65 + M_agua_base/1.0 + v1 + v2 + v3)
    k_lab = ml_objetivo / vol_t
    
    res_lab = {
        "Cemento": m_cem * k_lab, "Limestone": m_lim * k_lab, ex_p_name: m_exp * k_lab,
        "Arena": M_arena_base * k_lab, "Agua": M_agua_base * k_lab,
        "V1": v1 * k_lab, "V2": v2 * k_lab, "V3": v3 * k_lab
    }
    
    # Puntajes industriales (Escala 990L)
    k_990 = 990 / vol_t
    costo = ( (m_cem*k_990)*c_cost + (m_lim*k_990)*l_cost + (m_exp*k_990)*ex_p_cost + (M_arena_base*k_990)*0.015 + (v1*k_990)*v1_cost + (v2*k_990)*v2_cost + (v3*k_990)*v3_cost )
    co2 = ( (m_cem*k_990)*c_gwp + (m_lim*k_990)*0.06 + (M_arena_base*k_990)*0.01 + (v1*k_990)*2.1 )
    
    p_costo = 100 - (costo - 100) / 1.5
    p_co2 = 100 - (co2 - 200) / 3
    p_total = (0.05 * p_costo + 0.1 * p_co2) / 0.85
    
    return res_lab, costo, co2, p_total

# Cálculo inicial
m_lab, c_ind, g_ind, score = engine(S_val, W_val, C_val, ExP_val, V1_val, V2_val, V3_val, vol_real)

# --- INTERFAZ PRINCIPAL ---
st.title(f"🏗️ ACI Mortar Master - Caso {porcentaje_escala}%")
st.write(f"Preparando **{vol_real:.1f} ml** (escalado proporcional)")

c1, c2, c3 = st.columns(3)
c1.metric("🏆 PUNTAJE TOTAL", f"{score:.2f}")
c2.metric("💵 COSTO USD/m³", f"${c_ind:.2f}")
c3.metric("🌱 CO2 kg/m³", f"{g_ind:.2f}")

tab1, tab2, tab3 = st.tabs(["🔬 Receta para Laboratorio", "📊 Mapa de Calor (S vs W)", "📉 Granulometría ACI"])

with tab1:
    st.subheader(f"Cantidades para Batch de {vol_real:.1f} ml")
    df_receta = pd.DataFrame({
        "Material": ["Cemento", "Limestone Powder", ex_p_name, "Arena Natural", "Agua Destilada", v1_name, v2_name, v3_name],
        "Masa / Vol": [m_lab["Cemento"], m_lab["Limestone"], m_lab[ex_p_name], m_lab["Arena"], m_lab["Agua"], m_lab["V1"], m_lab["V2"], m_lab["V3"]],
        "Unidad": ["g", "g", "g", "g", "g", "ml", "ml", "ml"]
    })
    st.table(df_receta.style.format({"Masa / Vol": "{:.2f}"}))

with tab2:
    st.subheader("Análisis de Optimización: Arena (X) vs Agua (Y)")
    res = 35
    s_axis = np.linspace(0.60, 0.99, res)
    w_axis = np.linspace(0.00, 0.50, res)
    z_matrix = np.zeros((res, res))
    
    # Matriz para heatmap (W en filas, S en columnas)
    for i, w in enumerate(w_axis):
        for j, s in enumerate(s_axis):
            _, _, _, pt = engine(s, w, C_val, ExP_val, V1_val, V2_val, V3_val, vol_real)
            z_matrix[i, j] = pt
            
    fig_heat = go.Figure(data=go.Contour(
        z=z_matrix, x=s_axis, y=w_axis, 
        colorscale='Viridis', contours_showlines=True,
        hovertemplate='S (Arena): %{x:.2f}<br>W (Agua): %{y:.2f}<br>Puntaje: %{z:.2f}<extra></extra>'
    ))
    fig_heat.add_trace(go.Scatter(x=[S_val], y=[W_val], mode='markers', marker=dict(color='red', size=12, symbol='x'), name="Actual"))
    fig_heat.update_layout(xaxis_title="Fracción de Arena (S)", yaxis_title="Relación Agua/Polvo (W)")
    st.plotly_chart(fig_heat, use_container_width=True)

with tab3:
    st.subheader("Control Granulométrico ACI 211")
    m_arena_batch = m_lab["Arena"]
    st.write(f"Masa total de arena en este batch: **{m_arena_batch:.2f} g**")
    
    tamices = [
        {"id": "N° 4", "min": 95, "max": 100}, {"id": "N° 8", "min": 80, "max": 100},
        {"id": "N° 16", "min": 50, "max": 85}, {"id": "N° 30", "min": 25, "max": 60},
        {"id": "N° 50", "min": 5, "max": 30}, {"id": "N° 100", "min": 0, "max": 10}
    ]
    
    col_t1, col_t2 = st.columns([1, 2])
    with col_t1:
        st.write("**Retenidos Individuales (%)**")
        rets = []
        for i, t in enumerate(tamices):
            val = st.number_input(f"{t['id']}", 0.0, 100.0, 15.0, key=f"t_aci_{i}")
            rets.append(val)
            
    with col_t2:
        # Cálculos de cumplimiento
        acum = 0
        pasa_lista = []
        filas = []
        for i, t in enumerate(tamices):
            m_r = m_arena_batch * (rets[i]/100)
            acum += rets[i]
            pasa = 100 - acum
            pasa_lista.append(pasa)
            status = "✅" if t["min"] <= pasa <= t["max"] else "❌"
            filas.append({"Tamiz": t["id"], "Masa a Retener (g)": f"{m_r:.2f}", "% Pasa": f"{pasa:.1f}%", "Límites ACI": f"{t['min']}-{t['max']}%", "Estado": status})
        
        st.dataframe(pd.DataFrame(filas))

    # Gráfico ACI Restaurado
    fig_aci = go.Figure()
    ids = [t["id"] for t in tamices]
    fig_aci.add_trace(go.Scatter(x=ids, y=[t["max"] for t in tamices], name="Límite Superior", line=dict(color='red', dash='dash')))
    fig_aci.add_trace(go.Scatter(x=ids, y=[t["min"] for t in tamices], name="Límite Inferior", line=dict(color='red', dash='dash'), fill='tonexty'))
    fig_aci.add_trace(go.Scatter(x=ids, y=pasa_lista, name="Tu Mezcla", line=dict(color='blue', width=4), marker=dict(size=10)))
    
    fig_aci.update_layout(title="Curva Granulométrica vs Límites ACI", yaxis_title="% que Pasa", yaxis=dict(range=[0, 105]))
    st.plotly_chart(fig_aci, use_container_width=True)

st.caption("v8.0 - Full Features: Batch Proporcional + 3 Aditivos + Heatmap S/W + Granulometría ACI.")



