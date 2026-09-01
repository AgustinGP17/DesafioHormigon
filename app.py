import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Concrete Mix Designer Pro",
    page_icon="🏗️",
    layout="wide",
)

# --- REPARACIÓN DE COLORES Y CONTRASTE (CSS) ---
st.markdown("""
    <style>
    /* 1. FONDO DE LA APP */
    .main { 
        background-color: #f4f7f9 !important; 
    }
    
    /* 2. SIDEBAR (PANEL IZQUIERDO) - LETRAS SIEMPRE BLANCAS */
    [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
        font-weight: bold !important;
        text-shadow: 1px 1px 2px black;
    }

    /* 3. TARJETAS DE MÉTRICAS (LOS 3 PUNTAJES) */
    /* Forzamos un fondo oscuro con letras blancas para que NO haya pérdida de contraste */
    div[data-testid="stMetric"] {
        background-color: #1E3A8A !important; /* Azul Marino Intenso */
        border: 2px solid #1E40AF !important;
        padding: 20px !important;
        border-radius: 15px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
    }
    
    /* EL NÚMERO GRANDE */
    div[data-testid="stMetricValue"] > div {
        color: #FFFFFF !important; /* Blanco Puro */
        font-size: 2.2rem !important;
        font-weight: 800 !important;
    }
    
    /* EL TÍTULO DE ARRIBA DEL NÚMERO */
    div[data-testid="stMetricLabel"] > div {
        color: #CBD5E1 !important; /* Gris Claro Azulado */
        font-size: 1.1rem !important;
        font-weight: bold !important;
        text-transform: uppercase;
    }

    /* Arreglo para los inputs de número en el sidebar */
    div[data-testid="stNumberInput"] label {
        color: white !important;
    }
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

# --- DICCIONARIO Y CÁLCULOS ---
materiales = {
    "Portland Cement": {"densidad": c_den, "costo": c_cost, "gwp": c_gwp},
    "Limestone Powder": {"densidad": l_den, "costo": l_cost, "gwp": 0.06},
    "Natural Sand": {"densidad": s_den, "costo": s_cost, "gwp": 0.01},
    "Water": {"densidad": w_den, "costo": 0.0025, "gwp": 0.00},
    "Plastificante": {"densidad": p_den, "costo": p_cost, "gwp": 2.1},
    "Acelerante": {"densidad": a_den, "costo": a_cost, "gwp": 1.1}
}

def calcular_mezcla(S, W, C, V1, V2, ml_objetivo):
    M_arena_base = 1000 
    den_p, den_a = materiales["Plastificante"]["densidad"], materiales["Acelerante"]["densidad"]
    M_polvo_base = ((M_arena_base * (1 - S) / S) - (0.4 * (V1 * den_p + V2 * den_a))) / (1 + W)
    M_agua_base = M_polvo_base * W - 0.6 * (V1 * den_p + V2 * den_a)
    M_cemento_base = M_polvo_base * C
    M_CaCO3_base = M_polvo_base * (1 - C)
    V_total_base = ( (M_cemento_base / materiales["Portland Cement"]["densidad"]) + 
                     (M_CaCO3_base / materiales["Limestone Powder"]["densidad"]) + 
                     (M_arena_base / materiales["Natural Sand"]["densidad"]) + 
                     (M_agua_base / materiales["Water"]["densidad"]) + V1 + V2 )
    K_lab = ml_objetivo / V_total_base
    masas_lab = {
        "Cemento": M_cemento_base * K_lab, "CaCO3": M_CaCO3_base * K_lab,
        "Arena": M_arena_base * K_lab, "Agua": M_agua_base * K_lab,
        "Aditivos": (V1 * den_p + V2 * den_a) * K_lab
    }
    k_m3 = 990 / ml_objetivo
    m_m3 = {k: v * k_m3 for k, v in masas_lab.items()}
    costo_m3 = (m_m3["Cemento"]*materiales["Portland Cement"]["costo"] + m_m3["CaCO3"]*materiales["Limestone Powder"]["costo"] + 
                m_m3["Arena"]*materiales["Natural Sand"]["costo"] + V1*k_m3*materiales["Plastificante"]["costo"] + V2*k_m3*materiales["Acelerante"]["costo"])
    co2_m3 = (m_m3["Cemento"]*materiales["Portland Cement"]["gwp"] + m_m3["CaCO3"]*0.06 + m_m3["Arena"]*0.01 + V1*k_m3*2.1 + V2*k_m3*1.1)
    p_total = (0.05 * (100 - (costo_m3 - 100) / 1.5) + 0.1 * (100 - (co2_m3 - 200) / 3)) / 0.85
    return masas_lab, costo_m3, co2_m3, p_total

m_lab, costo, co2, score = calcular_mezcla(S_val, W_val, C_val, V1_val, V2_val, target_ml)

# --- INTERFAZ PRINCIPAL ---
st.title("🏗️ Concrete Optimizer Pro")

# LAS 3 MÉTRICAS CRÍTICAS
col1, col2, col3 = st.columns(3)
col1.metric("🏆 PUNTAJE TOTAL", f"{score:.2f}")
col2.metric("💵 COSTO USD/m³", f"${costo:.2f}")
col3.metric("🌱 CO₂ kg/m³", f"{co2:.2f}")

st.markdown("---")

tab1, tab2 = st.tabs(["🔬 Receta Laboratorio", "📊 Gráficos de Análisis"])

with tab1:
    st.subheader(f"Dosificación para {target_ml} ml")
    df_lab = pd.DataFrame({
        "Material": ["Cemento", "Limestone", "Arena", "Agua", "Aditivos"],
        "Gramos (g)": [m_lab["Cemento"], m_lab["CaCO3"], m_lab["Arena"], m_lab["Agua"], m_lab["Aditivos"]]
    })
    st.table(df_lab.style.format({"Gramos (g)": "{:.2f}"}))

with tab2:
    st.subheader("Análisis Visual")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig1 = px.pie(df_lab, values='Gramos (g)', names='Material', title="Distribución de la Mezcla")
        st.plotly_chart(fig1, use_container_width=True)
    with col_g2:
        st.info(f"Escalado industrial: {(990/target_ml):.2f}x")
        st.write(f"Plastificante: {V1_val} ml | Acelerante: {V2_val} ml")

st.caption("Ajuste de contraste v3.0 - Soporte total para legibilidad extrema.")
