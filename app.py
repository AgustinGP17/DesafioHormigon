import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Concrete Optimizer Pro + ACI Granulometry", layout="wide")

# --- CSS PARA ESTILO Y CONTRASTE ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f9 !important; }
    [data-testid="stMetric"] {
        background-color: #1E3A8A !important;
        color: white !important;
        border-radius: 15px !important;
        padding: 15px !important;
    }
    div[data-testid="stMetricValue"] > div { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE CÁLCULO DE MEZCLA (Simplificada para el ejemplo) ---
with st.sidebar:
    st.title("⚙️ Parámetros de Mezcla")
    S_val = st.slider("S (Fracción Arena)", 0.60, 0.99, 0.70, 0.01)
    W_val = st.slider("W (Agua/Polvo)", 0.10, 0.50, 0.25, 0.01)
    C_val = st.slider("C (% Cemento)", 0.50, 1.00, 0.50, 0.05)
    target_ml = st.number_input("Mezcla Total (ml)", 100, 5000, 750)

# Simulación de cálculo de masas (Basado en tu fórmula anterior)
def obtener_masa_arena(S, W, C, ml):
    # Simplificación para obtener la masa de arena dinámica
    M_arena_base = 1000
    M_polvo_base = (M_arena_base * (1 - S) / S) / (1 + W)
    V_total_base = (M_polvo_base*C/2.85 + M_polvo_base*(1-C)/2.7 + M_arena_base/2.65 + M_polvo_base*W/1.0)
    K_lab = ml / V_total_base
    return M_arena_base * K_lab

masa_arena_total = obtener_masa_arena(S_val, W_val, C_val, target_ml)

# --- INTERFAZ PRINCIPAL ---
st.title("🏗️ Concrete Optimizer Pro + ACI Analysis")

tab1, tab2, tab3 = st.tabs(["🔬 Receta y Heatmap", "📉 Granulometría (ACI)", "📊 Análisis de Sensibilidad"])

with tab1:
    st.subheader("Resumen de Mezcla")
    col1, col2 = st.columns(2)
    col1.metric("Masa de Arena Total", f"{masa_arena_total:.2f} g")
    st.info("Configura la granulometría en la siguiente pestaña para desglosar esta masa.")

# --- NUEVA PESTAÑA: GRANULOMETRÍA ---
with tab2:
    st.subheader("Análisis Granulométrico de la Arena")
    st.write(f"Masa total a distribuir: **{masa_arena_total:.2f} g**")

    # Definición de Tamices y Límites ACI (según tu foto)
    tamices = [
        {"nombre": "N° 4 (4.75mm)", "min": 95, "max": 100},
        {"nombre": "N° 8 (2.36mm)", "min": 80, "max": 100},
        {"nombre": "N° 16 (1.18mm)", "min": 50, "max": 85},
        {"nombre": "N° 30 (600µm)", "min": 25, "max": 60},
        {"nombre": "N° 50 (300µm)", "min": 5, "max": 30},
        {"nombre": "N° 100 (150µm)", "min": 0, "max": 10},
    ]

    st.markdown("### 1. Ingreso de Retenidos Individuales (%)")
    st.caption("Ingresa cuánto porcentaje se queda en cada 'matriz' (tamiz).")

    cols = st.columns(len(tamices))
    retenidos_pct = []

    # Generar inputs para cada tamiz
    for i, t in enumerate(tamices):
        val = cols[i].number_input(f"{t['nombre']}", min_value=0.0, max_value=100.0, value=10.0 if i < 5 else 5.0, key=f"t{i}")
        retenidos_pct.append(val)

    # El resto es el "Fondo" (Pan)
    suma_pct = sum(retenidos_pct)
    fines_pct = max(0.0, 100.0 - suma_pct)
    
    if suma_pct > 100:
        st.error(f"⚠️ ¡Error! La suma de porcentajes es {suma_pct}%, excede el 100%.")
    
    # Cálculos de granulometría
    datos_grafico = []
    acumulado_retenido = 0
    
    for i, t in enumerate(tamices):
        m_retenida = masa_arena_total * (retenidos_pct[i] / 100)
        acumulado_retenido += retenidos_pct[i]
        pasa_pct = 100 - acumulado_retenido
        
        # Validación ACI
        cumple = t["min"] <= pasa_pct <= t["max"]
        status = "✅" if cumple else "❌"
        
        datos_grafico.append({
            "Tamiz": t["nombre"],
            "Masa Retenida (g)": round(m_retenida, 2),
            "% Retenido Indiv.": retenidos_pct[i],
            "% Pasa Real": round(pasa_pct, 2),
            "Límite ACI": f"{t['min']}-{t['max']}%",
            "Estado": status
        })

    # Mostrar Tabla de Resultados
    df_gran = pd.DataFrame(datos_grafico)
    st.table(df_gran)
    
    st.write(f"**Fondo (Finos < N°100):** {masa_arena_total * (fines_pct/100):.2f} g ({fines_pct:.2f}%)")

    # Gráfico de Curva Granulométrica
    st.markdown("### 2. Curva Granulométrica vs Límites ACI")
    
    fig_curva = go.Figure()

    # Líneas de límites ACI
    nombres_tamices = [t["nombre"] for t in tamices]
    min_aci = [t["min"] for t in tamices]
    max_aci = [t["max"] for t in tamices]
    pasa_real = [d["% Pasa Real"] for d in datos_grafico]

    fig_curva.add_trace(go.Scatter(x=nombres_tamices, y=max_aci, name="Límite Superior ACI", line=dict(color='red', dash='dash')))
    fig_curva.add_trace(go.Scatter(x=nombres_tamices, y=min_aci, name="Límite Inferior ACI", line=dict(color='red', dash='dash'), fill='tonexty'))
    fig_curva.add_trace(go.Scatter(x=nombres_tamices, y=pasa_real, name="Tu Arena", line=dict(color='blue', width=4), marker=dict(size=10)))

    fig_curva.update_layout(
        title="Curva de Distribución de Partículas",
        yaxis_title="% que pasa",
        xaxis_title="Tamiz",
        yaxis=dict(range=[0, 105]),
        height=500
    )
    st.plotly_chart(fig_curva, use_container_width=True)

# --- PESTAÑA 3: MAPA DE CALOR (TU CÓDIGO ANTERIOR MEJORADO) ---
with tab3:
    st.subheader("Optimización de Parámetros S y W")
    # ... (Aquí va el código del heatmap que envié antes)
    st.info("Esta sección permite ver cómo influye la relación Agua/Polvo en el costo y puntaje.")
