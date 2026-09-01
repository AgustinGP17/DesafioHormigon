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

# --- ESTILO PERSONALIZADO ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { border: 1px solid #e0e0e0; padding: 15px; border-radius: 10px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: CONFIGURACIÓN DE MATERIALES ---
st.sidebar.header("⚙️ 1. Propiedades de Materiales")
st.sidebar.info("Ajusta las densidades, costos y GWP aquí.")

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

# Creamos el diccionario dinámico con los valores de los inputs
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
S = st.sidebar.slider("S - Fracción de Arena", 0.60, 0.99, 0.70, 0.01, help="Porcentaje de arena respecto a la masa total.")
W = st.sidebar.slider("W - Relación Agua/Polvo", 0.00, 0.50, 0.25, 0.01)
C = st.sidebar.slider("C - Fracción de Cemento en Polvo", 0.50, 1.00, 0.50, 0.05)
V1 = st.sidebar.number_input("V1 - Plastificante (ml)", 0.0, 100.0, 2.5)
V2 = st.sidebar.number_input("V2 - Acelerante (ml)", 0.0, 100.0, 0.0)
target_ml = st.sidebar.number_input("Volumen a fabricar (ml)", 100, 5000, 750)

# --- LÓGICA DE CÁLCULO (Basada en tu código original) ---
def calcular_todo(S, W, C, V1, V2, ml_objetivo):
    # Masa de arena base para el cálculo de K
    M_arena_base = 1000 
    
    # Masas iniciales (Lógica original)
    den_p = materiales["Plastificante"]["densidad"]
    den_a = materiales["Acelerante"]["densidad"]
    
    M_polvo_base = ((M_arena_base * (1 - S) / S) - (0.4 * (V1 * den_p + V2 * den_a))) / (1 + W)
    M_agua_base = M_polvo_base * W - 0.6 * (V1 * den_p + V2 * den_a)
    M_cemento_base = M_polvo_base * C
    M_CaCO3_base = M_polvo_base * (1 - C)
    
    # Volumen inicial para encontrar K
    V_total_base = ( (M_cemento_base / materiales["Portland Cement"]["densidad"]) + 
                     (M_CaCO3_base / materiales["Limestone Powder"]["densidad"]) + 
                     (M_arena_base / materiales["Natural Sand"]["densidad"]) + 
                     (M_agua_base / materiales["Water"]["densidad"]) + V1 + V2 )
    
    # Factor de escala
    K_lab = ml_objetivo / V_total_base
    
    # Masas finales para el laboratorio (g)
    masas_lab = {
        "Cemento": M_cemento_base * K_lab,
        "CaCO3": M_CaCO3_base * K_lab,
        "Arena": M_arena_base * K_lab,
        "Agua": M_agua_base * K_lab,
        "Aditivo_Masa": (V1 * den_p + V2 * den_a) * K_lab
    }
    
    # Escalado a 1 m3 (utilizando factor 990 para estandarizar según tu código)
    k_m3 = 990 / ml_objetivo
    masas_m3 = {k: v * k_m3 for k, v in masas_lab.items()}
    v1_m3 = V1 * k_m3
    v2_m3 = V2 * k_m3
    
    # Cálculos Económicos y Ambientales (por m3)
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
    
    # Puntajes (Fórmulas originales)
    p_costo = 100 - (costo_m3 - 100) / 1.5
    p_co2 = 100 - (co2_m3 - 200) / 3
    p_total = (0.05 * p_costo + 0.1 * p_co2) / 0.85
    
    return masas_lab, masas_m3, costo_m3, co2_m3, p_total, [v1_m3, v2_m3]

# Ejecutar cálculos
m_lab, m_m3, costo, co2, score, v_ads = calcular_todo(S, W, C, V1, V2, target_ml)

# --- DISEÑO DE LA APP ---
st.title("🏗️ Optimizador de Mezclas de Hormigón")
st.markdown("---")

# Fila 1: Métricas principales
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Puntaje de Mezcla", f"{score:.2f} pts")
with c2:
    st.metric("Costo por m³", f"${costo:.2f} USD")
with c3:
    st.metric("Huella CO₂", f"{co2:.2f} kg/m³")

# Fila 2: Tabs
tab1, tab2, tab3 = st.tabs(["📋 Receta de Laboratorio", "🚛 Dosificación Industrial (m³)", "📈 Análisis S vs W"])

with tab1:
    st.subheader(f"Cantidades para {target_ml} ml de mezcla")
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        df_lab = pd.DataFrame({
            "Componente": ["Cemento", "Limestone (CaCO3)", "Arena Natural", "Agua", "Aditivos"],
            "Cantidad (gramos)": [m_lab["Cemento"], m_lab["CaCO3"], m_lab["Arena"], m_lab["Agua"], m_lab["Aditivo_Masa"]]
        })
        st.table(df_lab.style.format({"Cantidad (gramos)": "{:.2f}"}))
    
    with col_b:
        st.info(f"**Volumen Aditivos:**\n\nPlastificante: {V1:.2f} ml\n\nAcelerante: {V2:.2f} ml")

with tab2:
    st.subheader("Dosificación para 1 m³ de Hormigón")
    df_m3 = pd.DataFrame({
        "Material": ["Cemento", "Limestone", "Arena", "Agua"],
        "Masa (kg)": [m_m3["Cemento"], m_m3["CaCO3"], m_m3["Arena"], m_m3["Agua"]]
    })
    
    fig_m3 = px.bar(df_m3, x='Material', y='Masa (kg)', color='Material', text_auto='.2f',
                    title="Distribución de Masas (kg) por metro cúbico")
    st.plotly_chart(fig_m3, use_container_width=True)
    
    st.write(f"**Volumen de Aditivos por m³:** Plastificante: {v_ads[0]:.2f} L | Acelerante: {v_ads[1]:.2f} L")

with tab3:
    st.subheader("Matriz de Optimización (Mapa de Calor)")
    st.write("Cómo varía el **Puntaje Total** según la Arena (S) y el Agua (W)")
    
    # Generar matriz para el gráfico
    s_vec = np.linspace(0.60, 0.99, 30)
    w_vec = np.linspace(0.00, 0.50, 30)
    z = np.zeros((len(w_vec), len(s_vec)))
    
    for i, w_val in enumerate(w_vec):
        for j, s_val in enumerate(s_vec):
            _, _, _, _, p_t, _ = calcular_todo(s_val, w_val, C, V1, V2, target_ml)
            z[i, j] = p_t
            
    fig_heat = go.Figure(data=go.Heatmap(
        z=z, x=s_vec, y=w_vec, colorscale='RdYlGn',
        hovertemplate='S (Arena): %{x}<br>W (Agua): %{y}<br>Puntaje: %{z:.2f}<extra></extra>'
    ))
    fig_heat.update_layout(xaxis_title="S - Fracción de Arena", yaxis_title="W - Relación Agua/Polvo")
    st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("---")
st.caption("Herramienta desarrollada para pruebas interactivas de laboratorio de materiales.")