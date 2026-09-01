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

# --- ESTILO PERSONALIZADO (CSS MEJORADO PARA LEGIBILIDAD) ---
st.markdown("""
    <style>
    /* Fondo general de la app */
    .main { background-color: #f0f2f6; }
    
    /* Estilo de las métricas (los números grandes) */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 2px solid #dfe3e8;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Color de los números (Valor de la métrica) */
    div[data-testid="stMetricValue"] > div {
        color: #1f2937 !important; /* Gris muy oscuro, casi negro */
        font-weight: 800;
    }
    
    /* Color de las etiquetas de las métricas */
    div[data-testid="stMetricLabel"] > div {
        color: #4b5563 !important; /* Gris medio */
        font-size: 1rem;
        font-weight: 600;
    }

    /* Estilo de los sliders y controles */
    .stSlider label, .stNumberInput label {
        color: #1f2937 !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: CONFIGURACIÓN DE MATERIALES ---
st.sidebar.header("⚙️ 1. Propiedades de Materiales")
st.sidebar.info("Ajusta densidades y costos aquí.")

with st.sidebar.expander("Portland Cement"):
    c_den = st.number_input("Densidad (C)", value=2.85, step=0.01)
    c_cost = st.number_input("Costo USD/kg (C)", value=0.175, format="%.4f")
    c_gwp = st.number_input("GWP KgCO2/kg (C)", value=0.90)

with st.sidebar.expander("Limestone Powder"):
    l_den = st.number_input("Densidad (L)", value=2.711, step=0.01)
    l_cost = st.number_input("Costo USD/kg (L)", value=0.040, format="%.4f")
    l_gwp = st.number_input("GWP KgCO2/kg (L)", value=0.06)

with st.sidebar.expander("Natural Sand"):
    s_den = st.number_input("Densidad (S)", value=2.65, step=0.01)
    s_cost = st.number_input("Costo USD/kg (S)", value=0.015, format="%.4f")
    s_gwp = st.number_input("GWP KgCO2/kg (S)", value=0.01)

with st.sidebar.expander("Water"):
    w_den = st.number_input("Densidad (W)", value=1.00, step=0.01)
    w_cost = st.number_input("Costo USD/kg (W)", value=0.0025, format="%.4f")
    w_gwp = st.number_input("GWP KgCO2/kg (W)", value=0.00)

with st.sidebar.expander("Plastificante"):
    p_den = st.number_input("Densidad (P)", value=1.11, step=0.01)
    p_cost = st.number_input("Costo USD/ml (P)", value=3.75, format="%.2f")
    p_gwp = st.number_input("GWP KgCO2/ml (P)", value=2.1)

with st.sidebar.expander("Acelerante"):
    a_den = st.number_input("Densidad (A)", value=1.25, step=0.01)
    a_cost = st.number_input("Costo USD/ml (A)", value=1.95, format="%.2f")
    a_gwp = st.number_input("GWP KgCO2/ml (A)", value=1.1)

materiales = {
    "Portland Cement": {"densidad": c_den, "costo": c_cost, "gwp": c_gwp},
    "Limestone Powder": {"densidad": l_den, "costo": l_cost, "gwp": l_gwp},
    "Natural Sand": {"densidad": s_den, "costo": s_cost, "gwp": s_gwp},
    "Water": {"densidad": w_den, "costo": w_cost, "gwp": w_gwp},
    "Plastificante": {"densidad": p_den, "costo": p_cost, "gwp": p_gwp},
    "Acelerante": {"densidad": a_den, "costo": a_cost, "gwp": a_gwp}
}

# --- SIDEBAR: VARIABLES DE LA MEZCLA ---
st.sidebar.header("🧪 2. Parámetros de la Mezcla")
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
    
    # Masa Polvo inicial
    M_polvo_base = ((M_arena_base * (1 - S) / S) - (0.4 * (V1 * den_p + V2 * den_a))) / (1 + W)
    M_agua_base = M_polvo_base * W - 0.6 * (V1 * den_p + V2 * den_a)
    M_cemento_base = M_polvo_base * C
    M_CaCO3_base = M_polvo_base * (1 - C)
    
    # Volumen Base
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
st.markdown("Los cálculos se actualizan automáticamente al cambiar los parámetros.")

# Métricas con nuevo estilo visual
col1, col2, col3 = st.columns(3)
col1.metric("🏆 Puntaje Total", f"{score:.2f} pts")
col2.metric("💵 Costo por m³", f"${costo:.2f} USD")
col3.metric("🌱 Huella de CO₂", f"{co2:.2f} kg/m³")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🧪 Muestra Lab", "📊 Análisis Industrial", "🗺️ Matriz S vs W"])

with tab1:
    st.subheader(f"Dosificación para {target_ml} ml")
    df_lab = pd.DataFrame({
        "Componente": ["Cemento", "Limestone (CaCO3)", "Arena", "Agua", "Aditivos (Masa)"],
        "Peso (gramos)": [m_lab["Cemento"], m_lab["CaCO3"], m_lab["Arena"], m_lab["Agua"], m_lab["Aditivo_Masa"]]
    })
    st.dataframe(df_lab.style.format({"Peso (gramos)": "{:.2f}"}), use_container_width=True)
    st.success(f"Utilizar: {V1_val} ml de Plastificante y {V2_val} ml de Acelerante.")

with tab2:
    st.subheader("Análisis por Metro Cúbico")
    c_left, c_right = st.columns(2)
    
    with c_left:
        # Gráfico de barras de masas m3
        df_plot = pd.DataFrame({
            "Mat": ["Cem", "Lime", "Sand", "Water"],
            "Kg": [m_m3["Cemento"], m_m3["CaCO3"], m_m3["Arena"], m_m3["Agua"]]
        })
        fig = px.bar(df_plot, x="Mat", y="Kg", text_auto='.0f', title="Masa por componente (Kg/m³)")
        st.plotly_chart(fig, use_container_width=True)
        
    with c_right:
        # Gráfico de torta
        fig_pie = px.pie(df_plot, values='Kg', names='Mat', title="Distribución de la mezcla")
        st.plotly_chart(fig_pie, use_container_width=True)

with tab3:
    st.subheader("Optimización de S y W")
    # Generar matriz rápida
    s_arr = np.linspace(0.60, 0.99, 20)
    w_arr = np.linspace(0.00, 0.50, 20)
    res = np.zeros((len(w_arr), len(s_arr)))
    
    for i, w in enumerate(w_arr):
        for j, s in enumerate(s_arr):
            _, _, _, _, p = calcular_mezcla(s, w, C_val, V1_val, V2_val, target_ml)
            res[i, j] = p
            
    fig_h = go.Figure(data=go.Heatmap(z=res, x=s_arr, y=w_arr, colorscale='RdYlGn'))
    fig_h.update_layout(xaxis_title="S (Arena)", yaxis_title="W (Agua/Polvo)", height=500)
    st.plotly_chart(fig_h, use_container_width=True)

st.markdown("---")
st.caption("Creado para equipos de ingeniería - Control de materiales y sostenibilidad.")
