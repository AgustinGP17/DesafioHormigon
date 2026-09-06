import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Concrete Mix Designer Pro + ACI",
    page_icon="🏗️",
    layout="wide",
)

# --- REPARACIÓN DE COLORES Y CONTRASTE (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f9 !important; }
    [data-testid="stSidebar"] label { color: #FFFFFF !important; font-weight: bold !important; text-shadow: 1px 1px 2px black; }
    div[data-testid="stMetric"] {
        background-color: #1E3A8A !important;
        border: 2px solid #1E40AF !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }
    div[data-testid="stMetricValue"] > div { color: #FFFFFF !important; font-size: 2.2rem !important; font-weight: 800 !important; }
    div[data-testid="stMetricLabel"] > div { color: #CBD5E1 !important; font-size: 1.1rem !important; font-weight: bold !important; }
    div[data-testid="stNumberInput"] label { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: CONFIGURACIÓN DE MATERIALES ---
st.sidebar.title("⚙️ Configuración")

with st.sidebar.expander("🧱 Cemento y Polvos"):
    c_den = st.number_input("Densidad Cemento", value=2.85, step=0.01)
    c_cost = st.number_input("Costo Cemento (USD/kg)", value=0.175, format="%.4f")
    c_gwp = st.number_input("CO2 Cemento (kg/kg)", value=0.90)
    l_den = st.number_input("Densidad Limestone", value=2.711, step=0.01)
    l_cost = st.number_input("Costo Limestone (USD/kg)", value=0.040, format="%.4f")

with st.sidebar.expander("🏖️ Agregados y Agua"):
    s_den = st.number_input("Densidad Arena", value=2.65, step=0.01)
    s_cost = st.number_input("Costo Arena (USD/kg)", value=0.015, format="%.4f")
    w_den = st.number_input("Densidad Agua", value=1.00, step=0.01)

with st.sidebar.expander("🧪 Aditivos"):
    p_den = st.number_input("Densidad Plastificante", value=1.11, step=0.01)
    p_cost = st.number_input("Costo Plast. (USD/ml)", value=3.75)
    a_den = st.number_input("Densidad Acelerante", value=1.25, step=0.01)
    a_cost = st.number_input("Costo Acel. (USD/ml)", value=1.95)

# --- SIDEBAR: PARÁMETROS DE MEZCLA ---
st.sidebar.markdown("---")
st.sidebar.subheader("🧪 Parámetros de Diseño")
S_val = st.sidebar.slider("S (Fracción Arena)", 0.60, 0.99, 0.70, 0.01)
W_val = st.sidebar.slider("W (Agua/Polvo)", 0.00, 0.50, 0.25, 0.01)
C_val = st.sidebar.slider("C (% Cemento)", 0.50, 1.00, 0.50, 0.05)
V1_val = st.sidebar.number_input("Vol. Plastificante (ml)", 0.0, 100.0, 2.5)
V2_val = st.sidebar.number_input("Vol. Acelerante (ml)", 0.0, 100.0, 0.0)
target_ml = st.sidebar.number_input("Mezcla Total (ml)", 100, 5000, 750)

# --- MOTOR DE CÁLCULO CORE ---
def calcular_mezcla(S, W, C, V1, V2, ml_objetivo):
    M_arena_base = 1000 
    den_p, den_a = p_den, a_den
    M_polvo_base = ((M_arena_base * (1 - S) / S) - (0.4 * (V1 * den_p + V2 * den_a))) / (1 + W)
    M_agua_base = M_polvo_base * W - 0.6 * (V1 * den_p + V2 * den_a)
    M_cemento_base = M_polvo_base * C
    M_CaCO3_base = M_polvo_base * (1 - C)
    
    V_total_base = ( (M_cemento_base / c_den) + (M_CaCO3_base / l_den) + 
                     (M_arena_base / s_den) + (M_agua_base / w_den) + V1 + V2 )
    
    K_lab = ml_objetivo / V_total_base
    masas_lab = {
        "Cemento": M_cemento_base * K_lab, "CaCO3": M_CaCO3_base * K_lab,
        "Arena": M_arena_base * K_lab, "Agua": M_agua_base * K_lab,
        "Aditivos": (V1 * den_p + V2 * den_a) * K_lab
    }
    
    k_m3 = 1000000 / V_total_base
    costo_m3 = ( (M_cemento_base * c_cost) + (M_CaCO3_base * l_cost) + 
                 (M_arena_base * s_cost) + (V1 * p_cost) + (V2 * a_cost) ) * (k_m3 / 1000)
    co2_m3 = ( (M_cemento_base * c_gwp) + (M_CaCO3_base * 0.06) + (M_arena_base * 0.01) ) * (k_m3 / 1000)
    p_total = (0.05 * (100 - (costo_m3 - 100) / 1.5) + 0.1 * (100 - (co2_m3 - 200) / 3)) / 0.85
    
    return masas_lab, costo_m3, co2_m3, p_total

# Ejecución inicial
m_lab, costo, co2, score = calcular_mezcla(S_val, W_val, C_val, V1_val, V2_val, target_ml)

# --- INTERFAZ PRINCIPAL ---
st.title("🏗️ Concrete Optimizer Pro")

col1, col2, col3 = st.columns(3)
col1.metric("🏆 PUNTAJE TOTAL", f"{score:.2f}")
col2.metric("💵 COSTO USD/m³", f"${costo:.2f}")
col3.metric("🌱 CO₂ kg/m³", f"{co2:.2f}")

st.markdown("---")

# --- TABS DE NAVEGACIÓN ---
tab1, tab2, tab3 = st.tabs(["🔬 Receta de Laboratorio", "📊 Mapa de Calor", "📉 Granulometría Arena (ACI)"])

# TAB 1: RECETA
with tab1:
    st.subheader(f"Dosificación para {target_ml} ml")
    df_lab = pd.DataFrame({
        "Material": ["Cemento", "Limestone", "Arena", "Agua", "Aditivos"],
        "Gramos (g)": [m_lab["Cemento"], m_lab["CaCO3"], m_lab["Arena"], m_lab["Agua"], m_lab["Aditivos"]]
    })
    st.table(df_lab.style.format({"Gramos (g)": "{:.2f}"}))
    
    fig_pie = px.pie(df_lab, values='Gramos (g)', names='Material', title="Distribución de la Mezcla")
    st.plotly_chart(fig_pie, use_container_width=True)

# TAB 2: MAPA DE CALOR (ANÁLISIS AGUA VS ARENA)
with tab2:
    st.subheader("Análisis de Sensibilidad: S vs W")
    
    # Rango de valores (los que pusiste: 0.60 a 0.99 y 0.00 a 0.50)
    s_range = np.linspace(0.60, 0.99, 40)
    w_range = np.linspace(0.00, 0.50, 40)
    
    # Calcular matriz de puntajes
    z_score = np.array([[calcular_mezcla(s, w, C_val, V1_val, V2_val, target_ml)[3] for w in w_range] for s in s_range])
    
    fig_map = go.Figure(data=go.Contour(
        z=z_score, x=w_range, y=s_range,
        colorscale='Viridis',
        colorbar=dict(title="Puntaje"),
        hovertemplate='Agua/Polvo: %{x:.2f}<br>Frac. Arena: %{y:.2f}<br>Puntaje: %{z:.2f}<extra></extra>'
    ))
    
    # Marcar posición actual con una X roja
    fig_map.add_trace(go.Scatter(x=[W_val], y=[S_val], mode='markers', marker=dict(color='red', size=15, symbol='x'), name='Mezcla Actual'))
    
    fig_map.update_layout(xaxis_title="Relación Agua / Polvo (W)", yaxis_title="Fracción de Arena (S)", height=600)
    st.plotly_chart(fig_map, use_container_width=True)

# TAB 3: GRANULOMETRÍA (EL EXTRA NUEVO)
with tab3:
    st.subheader("Control Granulométrico (ACI)")
    masa_arena_objetivo = m_lab["Arena"]
    st.info(f"Masa de arena a distribuir: **{masa_arena_objetivo:.2f} g** (calculada automáticamente)")

    tamices = [
        {"n": "N° 4 (4.75mm)", "min": 95, "max": 100},
        {"n": "N° 8 (2.36mm)", "min": 80, "max": 100},
        {"n": "N° 16 (1.18mm)", "min": 50, "max": 85},
        {"n": "N° 30 (600µm)", "min": 25, "max": 60},
        {"n": "N° 50 (300µm)", "min": 5, "max": 30},
        {"n": "N° 100 (150µm)", "min": 0, "max": 10},
    ]

    st.write("### 1. Define el % Retenido Individual por Matriz")
    cols = st.columns(len(tamices))
    retenidos_indiv = []
    for i, t in enumerate(tamices):
        # Valor por defecto sugerido para que sume 100 rápido
        val = cols[i].number_input(f"{t['n']}", 0.0, 100.0, 15.0, key=f"gran_{i}")
        retenidos_indiv.append(val)
    
    # Cálculo de masa retenida y % pasa
    acumulado_retenido = 0
    datos_aci = []
    for i, t in enumerate(tamices):
        m_ret = masa_arena_objetivo * (retenidos_indiv[i] / 100)
        acumulado_retenido += retenidos_indiv[i]
        pasa = 100 - acumulado_retenido
        
        cumple = t["min"] <= pasa <= t["max"]
        datos_aci.append({
            "Tamiz": t["n"],
            "Masa Retenida (g)": round(m_ret, 2),
            "% Pasa Real": round(pasa, 2),
            "Límite ACI": f"{t['min']}-{t['max']}%",
            "Estado": "✅" if cumple else "❌"
        })

    st.table(pd.DataFrame(datos_aci))

    # Gráfico Curva Granulométrica
    fig_gran = go.Figure()
    fig_gran.add_trace(go.Scatter(x=[t["n"] for t in tamices], y=[t["max"] for t in tamices], name="ACI Sup", line=dict(color='red', dash='dash')))
    fig_gran.add_trace(go.Scatter(x=[t["n"] for t in tamices], y=[t["min"] for t in tamices], name="ACI Inf", line=dict(color='red', dash='dash'), fill='tonexty'))
    fig_gran.add_trace(go.Scatter(x=[t["n"] for t in tamices], y=[d["% Pasa Real"] for d in datos_aci], name="Tu Arena", line=dict(color='blue', width=4)))
    
    fig_gran.update_layout(title="Curva Granulométrica vs ACI", yaxis_title="% Pasa", height=450)
    st.plotly_chart(fig_gran, use_container_width=True)

st.caption("v5.0 - Integración Completa: Receta + Heatmap + Granulometría ACI.")
