import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Concrete Mix Designer Pro v6.0",
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
st.sidebar.title("⚙️ Configuración Materiales")

with st.sidebar.expander("🧱 Cementos y Polvos"):
    c_den = st.number_input("Densidad Cemento", value=2.85, step=0.01)
    c_cost = st.number_input("Costo Cemento (USD/kg)", value=0.175, format="%.4f")
    c_gwp = st.number_input("CO2 Cemento (kg/kg)", value=0.90)
    
    l_den = st.number_input("Densidad Limestone", value=2.711, step=0.01)
    l_cost = st.number_input("Costo Limestone (USD/kg)", value=0.040, format="%.4f")
    
    st.markdown("---")
    ex_p_name = st.text_input("Nombre Polvo Extra", value="Polvo X")
    ex_p_den = st.number_input(f"Densidad {ex_p_name}", value=2.20, step=0.01)
    ex_p_cost = st.number_input(f"Costo {ex_p_name} (USD/kg)", value=0.00, format="%.4f")
    ex_p_gwp = st.number_input(f"CO2 {ex_p_name} (kg/kg)", value=0.00)

with st.sidebar.expander("🏖️ Agregados y Agua"):
    s_den = st.number_input("Densidad Arena", value=2.65, step=0.01)
    s_cost = st.number_input("Costo Arena (USD/kg)", value=0.015, format="%.4f")
    w_den = st.number_input("Densidad Agua", value=1.00, step=0.01)

with st.sidebar.expander("🧪 Aditivos"):
    p_den = st.number_input("Densidad Plastificante (V1)", value=1.11, step=0.01)
    p_cost = st.number_input("Costo Plast. (USD/ml)", value=3.75)
    
    a_den = st.number_input("Densidad Acelerante (V2)", value=1.25, step=0.01)
    a_cost = st.number_input("Costo Acel. (USD/ml)", value=1.95)
    
    st.markdown("---")
    ex_a_name = st.text_input("Nombre Aditivo Extra (V3)", value="Aditivo X")
    ex_a_den = st.number_input(f"Densidad {ex_a_name}", value=1.10, step=0.01)
    ex_a_cost = st.number_input(f"Costo {ex_a_name} (USD/ml)", value=0.00)

# --- SIDEBAR: PARÁMETROS DE MEZCLA ---
st.sidebar.markdown("---")
st.sidebar.subheader("🧪 Parámetros de Diseño")
S_val = st.sidebar.slider("S (Fracción Arena)", 0.60, 0.99, 0.70, 0.01)
W_val = st.sidebar.slider("W (Agua/Polvo)", 0.00, 0.50, 0.25, 0.01)

st.sidebar.write("**Reparto de Polvos (Suma debe ser 100%):**")
C_val = st.sidebar.slider("% Cemento", 0.0, 1.0, 0.50, 0.05)
ExP_val = st.sidebar.slider(f"% {ex_p_name}", 0.0, 1.0, 0.0, 0.05)
L_val = max(0.0, 1.0 - C_val - ExP_val)
st.sidebar.caption(f"Limestone (Automático): {L_val:.2f}")

st.sidebar.write("**Volúmenes Aditivos (ml):**")
V1_val = st.sidebar.number_input("Plastificante (V1)", 0.0, 100.0, 2.5)
V2_val = st.sidebar.number_input("Acelerante (V2)", 0.0, 100.0, 0.0)
V3_val = st.sidebar.number_input(f"{ex_a_name} (V3)", 0.0, 100.0, 0.0)

target_ml = st.sidebar.number_input("Mezcla Total Objetivo (ml)", 100, 5000, 750)

# --- MOTOR DE CÁLCULO ---
def calcular_mezcla(S, W, C, ExP, V1, V2, V3, ml_objetivo):
    L = max(0.0, 1.0 - C - ExP)
    M_arena_base = 1000 
    
    # Masa de aditivos total para corrección de fórmula
    m_ads = (V1 * p_den) + (V2 * a_den) + (V3 * ex_a_den)
    
    M_polvo_base = ((M_arena_base * (1 - S) / S) - (0.4 * m_ads)) / (1 + W)
    M_agua_base = M_polvo_base * W - 0.6 * m_ads
    
    # Reparto de masas de polvos
    m_cem = M_polvo_base * C
    m_exp = M_polvo_base * ExP
    m_lim = M_polvo_base * L
    
    V_total_base = ( (m_cem / c_den) + (m_lim / l_den) + (m_exp / ex_p_den) +
                     (M_arena_base / s_den) + (M_agua_base / w_den) + V1 + V2 + V3 )
    
    K_lab = ml_objetivo / V_total_base
    masas_lab = {
        "Cemento": m_cem * K_lab, 
        "Limestone": m_lim * K_lab,
        ex_p_name: m_exp * K_lab,
        "Arena": M_arena_base * K_lab, 
        "Agua": M_agua_base * K_lab,
        "Aditivos": m_ads * K_lab
    }
    
    # Escala m3
    k_m3 = 1000000 / V_total_base
    costo_m3 = ( (m_cem * c_cost) + (m_lim * l_cost) + (m_exp * ex_p_cost) +
                 (M_arena_base * s_cost) + (V1 * p_cost) + (V2 * a_cost) + (V3 * ex_a_cost) ) * (k_m3 / 1000)
    
    co2_m3 = ( (m_cem * c_gwp) + (m_lim * 0.06) + (m_exp * ex_p_gwp) + (M_arena_base * 0.01) ) * (k_m3 / 1000)
    
    p_total = (0.05 * (100 - (costo_m3 - 100) / 1.5) + 0.1 * (100 - (co2_m3 - 200) / 3)) / 0.85
    return masas_lab, costo_m3, co2_m3, p_total

m_lab, costo, co2, score = calcular_mezcla(S_val, W_val, C_val, ExP_val, V1_val, V2_val, V3_val, target_ml)

# --- INTERFAZ PRINCIPAL ---
st.title("🏗️ Concrete Optimizer Pro v6.0")

col1, col2, col3 = st.columns(3)
col1.metric("🏆 PUNTAJE TOTAL", f"{score:.2f}")
col2.metric("💵 COSTO USD/m³", f"${costo:.2f}")
col3.metric("🌱 CO₂ kg/m³", f"{co2:.2f}")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🔬 Receta de Laboratorio", "📊 Mapa de Calor (Optimización)", "📉 Granulometría Arena (ACI)"])

with tab1:
    st.subheader(f"Dosificación para {target_ml} ml")
    df_lab = pd.DataFrame({
        "Material": ["Cemento", "Limestone", ex_p_name, "Arena", "Agua", "Aditivos (Total)"],
        "Gramos (g)": [m_lab["Cemento"], m_lab["Limestone"], m_lab[ex_p_name], m_lab["Arena"], m_lab["Agua"], m_lab["Aditivos"]]
    })
    st.table(df_lab.style.format({"Gramos (g)": "{:.2f}"}))
    
    fig_pie = px.pie(df_lab, values='Gramos (g)', names='Material', title="Distribución de Masas", color_discrete_sequence=px.colors.qualitative.Safe)
    st.plotly_chart(fig_pie, use_container_width=True)

with tab2:
    st.subheader("Análisis de Sensibilidad: Fracción Arena (X) vs Agua/Polvo (Y)")
    
    # Ejes permutados según pedido
    s_range = np.linspace(0.60, 0.99, 40) # Eje X
    w_range = np.linspace(0.00, 0.50, 40) # Eje Y
    
    # Calculamos la matriz. Nota: En numpy/plotly, el primer índice suele ser las filas (Y) y el segundo columnas (X)
    z_score = np.zeros((len(w_range), len(s_range)))
    
    for i, w in enumerate(w_range):
        for j, s in enumerate(s_range):
            _, _, _, p_t = calcular_mezcla(s, w, C_val, ExP_val, V1_val, V2_val, V3_val, target_ml)
            z_score[i, j] = p_t
    
    fig_map = go.Figure(data=go.Contour(
        z=z_score, 
        x=s_range, # Ahora X es Arena
        y=w_range, # Ahora Y es Agua
        colorscale='Viridis',
        colorbar=dict(title="Puntaje"),
        hovertemplate='Frac. Arena (S): %{x:.2f}<br>Agua/Polvo (W): %{y:.2f}<br>Puntaje: %{z:.2f}<extra></extra>'
    ))
    
    # Punto actual (permutado)
    fig_map.add_trace(go.Scatter(x=[S_val], y=[W_val], mode='markers', marker=dict(color='white', size=12, symbol='circle-open', line=dict(width=3)), name='Mezcla Actual'))
    
    fig_map.update_layout(
        xaxis_title="Fracción de Arena (S)", 
        yaxis_title="Relación Agua / Polvo (W)", 
        height=600
    )
    st.plotly_chart(fig_map, use_container_width=True)

with tab3:
    st.subheader("Control Granulométrico (ACI)")
    masa_arena_total = m_lab["Arena"]
    
    tamices = [
        {"n": "N° 4", "min": 95, "max": 100},
        {"n": "N° 8", "min": 80, "max": 100},
        {"n": "N° 16", "min": 50, "max": 85},
        {"n": "N° 30", "min": 25, "max": 60},
        {"n": "N° 50", "min": 5, "max": 30},
        {"n": "N° 100", "min": 0, "max": 10},
    ]

    st.write(f"Masa de arena a repartir: **{masa_arena_total:.2f} g**")
    cols = st.columns(len(tamices))
    retenidos_ind = []
    for i, t in enumerate(tamices):
        val = cols[i].number_input(f"{t['n']}", 0.0, 100.0, 15.0, key=f"g2_{i}")
        retenidos_ind.append(val)
    
    acum = 0
    datos_aci = []
    for i, t in enumerate(tamices):
        m_r = masa_arena_total * (retenidos_ind[i] / 100)
        acum += retenidos_ind[i]
        pasa = 100 - acum
        datos_aci.append({
            "Tamiz": t["n"], "Masa Retenida (g)": round(m_r, 2),
            "% Pasa": round(pasa, 2), "Rango ACI": f"{t['min']}-{t['max']}%",
            "Estado": "✅" if t['min'] <= pasa <= t['max'] else "❌"
        })
    st.table(pd.DataFrame(datos_aci))

st.caption(f"Soporte para {ex_p_name} y {ex_a_name} activado. Ejes permutados en el Heatmap.")
