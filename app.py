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

# --- CORRECCIÓN DE COLORES E INVISIBILIDAD (CSS) ---
st.markdown("""
    <style>
    /* 1. ARREGLAR LETRAS INVISIBLES EN EL SIDEBAR (PANEL IZQUIERDO) */
    [data-testid="stSidebar"] label {
        color: #FFFFFF !important; /* Forzamos blanco para que se vea en el fondo oscuro */
        font-weight: bold;
        font-size: 1rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5); /* Sombra para máxima legibilidad */
    }
    
    /* 2. ARREGLAR LETRAS EN EL CUERPO PRINCIPAL */
    .main label {
        color: #1f2937 !important; /* Gris muy oscuro para el fondo claro */
    }

    /* 3. ESTILO DE LAS TARJETAS DE NÚMEROS (METRICS) */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 2px solid #3b82f6; /* Borde azul para que resalte */
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    div[data-testid="stMetricValue"] > div {
        color: #111827 !important; /* Negro intenso para los números */
        font-size: 2rem !important;
    }
    
    div[data-testid="stMetricLabel"] > div {
        color: #374151 !important; /* Gris oscuro para el título del número */
        font-weight: bold !important;
    }

    /* Estilo para los expanders del sidebar */
    .streamlit-expanderHeader {
        color: white !important;
        background-color: rgba(255,255,255,0.1);
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: CONFIGURACIÓN DE MATERIALES ---
st.sidebar.markdown("## ⚙️ 1. Materiales")

with st.sidebar.expander("🧱 Portland Cement"):
    c_den = st.number_input("Densidad (C)", value=2.85, step=0.01, key="c1")
    c_cost = st.number_input("Costo USD/kg (C)", value=0.175, format="%.4f", key="c2")
    c_gwp = st.number_input("GWP KgCO2/kg (C)", value=0.90, key="c3")

with st.sidebar.expander("🪨 Limestone Powder"):
    l_den = st.number_input("Densidad (L)", value=2.711, step=0.01, key="l1")
    l_cost = st.number_input("Costo USD/kg (L)", value=0.040, format="%.4f", key="l2")
    l_gwp = st.number_input("GWP KgCO2/kg (L)", value=0.06, key="l3")

with st.sidebar.expander("🏖️ Natural Sand"):
    s_den = st.number_input("Densidad (S)", value=2.65, step=0.01, key="s1")
    s_cost = st.number_input("Costo USD/kg (S)", value=0.015, format="%.4f", key="s2")
    s_gwp = st.number_input("GWP KgCO2/kg (S)", value=0.01, key="s3")

with st.sidebar.expander("💧 Water"):
    w_den = st.number_input("Densidad (W)", value=1.00, step=0.01, key="w1")
    w_cost = st.number_input("Costo USD/kg (W)", value=0.0025, format="%.4f", key="w2")
    w_gwp = st.number_input("GWP KgCO2/kg (W)", value=0.00, key="w3")

with st.sidebar.expander("🧪 Aditivos (P y A)"):
    p_den = st.number_input("Densidad Plastificante", value=1.11, step=0.01)
    p_cost = st.number_input("Costo USD/ml Plast.", value=3.75)
    a_den = st.number_input("Densidad Acelerante", value=1.25, step=0.01)
    a_cost = st.number_input("Costo USD/ml Acel.", value=1.95)

materiales = {
    "Portland Cement": {"densidad": c_den, "costo": c_cost, "gwp": c_gwp},
    "Limestone Powder": {"densidad": l_den, "costo": l_cost, "gwp": l_gwp},
    "Natural Sand": {"densidad": s_den, "costo": s_cost, "gwp": s_gwp},
    "Water": {"densidad": w_den, "costo": w_cost, "gwp": w_gwp},
    "Plastificante": {"densidad": p_den, "costo": p_cost, "gwp": 2.1},
    "Acelerante": {"densidad": a_den, "costo": a_cost, "gwp": 1.1}
}

# --- SIDEBAR: VARIABLES DE LA MEZCLA ---
st.sidebar.markdown("## 🧪 2. Parámetros de la Mezcla")
S_val = st.sidebar.slider("S - Fracción de Arena", 0.60, 0.99, 0.70, 0.01)
W_val = st.sidebar.slider("W - Relación Agua/Polvo", 0.00, 0.50, 0.25, 0.01)
C_val = st.sidebar.slider("C - Fracción de Cemento", 0.50, 1.00, 0.50, 0.05)
V1_val = st.sidebar.number_input("V1 - Plastificante (ml)", 0.0, 100.0, 2.5)
V2_val = st.sidebar.number_input("V2 - Acelerante (ml)", 0.0, 100.0, 0.0)
target_ml = st.sidebar.number_input("Volumen a fabricar (ml)", 100, 5000, 750)

# --- FUNCIONES DE CÁLCULO ---
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
        "Cemento": M_cemento_base * K_lab,
        "CaCO3": M_CaCO3_base * K_lab,
        "Arena": M_arena_base * K_lab,
        "Agua": M_agua_base * K_lab,
        "Aditivo_Masa": (V1 * den_p + V2 * den_a) * K_lab
    }
    
    k_m3 = 990 / ml_objetivo
    masas_m3 = {k: v * k_m3 for k, v in masas_lab.items()}
    v1_m3, v2_m3 = V1 * k_m3, V2 * k_m3
    
    costo_m3 = (masas_m3["Cemento"] * materiales["Portland Cement"]["costo"] +
                masas_m3["CaCO3"] * materiales["Limestone Powder"]["costo"] +
                masas_m3["Arena"] * materiales["Natural Sand"]["costo"] +
                masas_m3["Agua"] * materiales["Water"]["costo"] +
                v1_m3 * materiales["Plastificante"]["costo"] +
                v2_m3 * materiales["Acelerante"]["costo"])
    
    co2_m3 = (masas_m3["Cemento"] * materiales["Portland Cement"]["gwp"] +
               masas_m3["CaCO3"] * materiales["Limestone Powder"]["gwp"] +
               masas_m3["Arena"] * materiales["Natural Sand"]["gwp"] +
               masas_m3["Agua"] * materiales["Water"]["gwp"] +
               v1_m3 * materiales["Plastificante"]["gwp"] +
               v2_m3 * materiales["Acelerante"]["gwp"])
    
    p_costo = 100 - (costo_m3 - 100) / 1.5
    p_co2 = 100 - (co2_m3 - 200) / 3
    p_total = (0.05 * p_costo + 0.1 * p_co2) / 0.85
    
    return masas_lab, masas_m3, costo_m3, co2_m3, p_total

# --- EJECUCIÓN ---
m_lab, m_m3, costo, co2, score = calcular_mezcla(S_val, W_val, C_val, V1_val, V2_val, target_ml)

# --- INTERFAZ PRINCIPAL ---
st.title("🏗️ Concrete Optimizer Pro")
st.write("Ajusta los materiales y parámetros en el panel izquierdo.")

# Fila de métricas
col1, col2, col3 = st.columns(3)
col1.metric("🏆 Puntaje Total", f"{score:.2f}")
col2.metric("💵 Costo (USD/m³)", f"${costo:.2f}")
col3.metric("🌱 CO₂ (kg/m³)", f"{co2:.2f}")

st.markdown("---")

# Pestañas
t1, t2, t3 = st.tabs(["🔬 Receta Laboratorio", "📊 Escala Industrial", "🗺️ Mapa de Optimización"])

with t1:
    st.subheader(f"Cantidades exactas para {target_ml} ml")
    df_lab = pd.DataFrame({
        "Componente": ["Cemento", "Limestone (CaCO3)", "Arena", "Agua", "Aditivos"],
        "Gramos (g)": [m_lab["Cemento"], m_lab["CaCO3"], m_lab["Arena"], m_lab["Agua"], m_lab["Aditivo_Masa"]]
    })
    st.table(df_lab.style.format({"Gramos (g)": "{:.2f}"}))
    st.info(f"💡 Medir {V1_val} ml de Plastificante y {V2_val} ml de Acelerante.")

with t2:
    st.subheader("Masa total por cada metro cúbico (kg)")
    df_m3 = pd.DataFrame({
        "Material": ["Cemento", "CaCO3", "Arena", "Agua"],
        "Masa (kg)": [m_m3["Cemento"], m_m3["CaCO3"], m_m3["Arena"], m_m3["Agua"]]
    })
    fig = px.bar(df_m3, x="Material", y="Masa (kg)", color="Material", text_auto='.1f')
    st.plotly_chart(fig, use_container_width=True)

with t3:
    st.subheader("Simulación S vs W")
    # Reducción de matriz para velocidad
    s_arr = np.linspace(0.60, 0.99, 15)
    w_arr = np.linspace(0.00, 0.50, 15)
    z = np.zeros((len(w_arr), len(s_arr)))
    for i, w in enumerate(w_arr):
        for j, s in enumerate(s_arr):
            _, _, _, _, p = calcular_mezcla(s, w, C_val, V1_val, V2_val, target_ml)
            z[i, j] = p
    fig_h = go.Figure(data=go.Heatmap(z=z, x=s_arr, y=w_arr, colorscale='Viridis'))
    fig_h.update_layout(xaxis_title="S (Arena)", yaxis_title="W (Agua/Polvo)")
    st.plotly_chart(fig_h, use_container_width=True)

st.caption("Version 2.1 - Arreglo de contraste visual para Modo Oscuro/Claro.")
