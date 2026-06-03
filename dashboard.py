import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import warnings
warnings.filterwarnings("ignore")

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ventas vs Rentabilidad · Superstore",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── PALETTE ───────────────────────────────────────────────────────────────────────
BG     = "#F8FAFC"
CARD   = "#FFFFFF"
SALES  = "#2563EB"
PROFIT = "#14B8A6"
LOSS   = "#EF4444"
TEXT   = "#1E293B"
MUTED  = "#64748B"
BORDER = "#E2E8F0"
AMBER  = "#F59E0B"

# ── CSS ───────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
.stApp {{ background-color:{BG}; }}
.block-container {{ padding-top:1.5rem; padding-bottom:2rem; max-width:1400px; }}

[data-testid="stSidebar"] {{ background-color:#0F172A !important; }}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span {{ color:#94A3B8 !important; }}
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {{ color:white !important; font-size:0.88rem; }}
[data-testid="stSidebar"] hr {{ border-color:#1E293B; }}

.kpi-card {{
    background:{CARD}; border-radius:12px; padding:18px 20px;
    border:1px solid {BORDER}; box-shadow:0 1px 4px rgba(0,0,0,.05);
    margin-bottom:4px;
}}
.kpi-value {{ font-size:1.7rem; font-weight:800; color:{TEXT}; line-height:1; }}
.kpi-label {{ font-size:.71rem; color:{MUTED}; margin-top:5px; text-transform:uppercase; letter-spacing:.07em; font-weight:600; }}
.kpi-delta {{ font-size:.8rem; margin-top:6px; font-weight:500; }}

.section-header {{ font-size:1.35rem; font-weight:800; color:{TEXT}; border-left:4px solid {SALES}; padding-left:14px; margin:6px 0 20px 0; line-height:1.3; }}
.section-sub    {{ font-size:.84rem; color:{MUTED}; margin-top:-14px; margin-bottom:20px; padding-left:18px; }}

.chart-title   {{ font-size:.94rem; font-weight:700; color:{TEXT}; margin-bottom:2px; }}
.chart-caption {{ font-size:.77rem; color:{MUTED}; font-style:italic; margin-bottom:8px; line-height:1.45; }}

.cover-card {{ background:{CARD}; border-radius:16px; padding:52px 48px; border:1px solid {BORDER}; margin-bottom:24px; }}
.cover-title {{ font-size:2.55rem; font-weight:900; color:{TEXT}; line-height:1.1; }}
.cover-sub   {{ font-size:1.02rem; color:{MUTED}; margin-top:10px; line-height:1.5; }}

.story-step {{ background:{CARD}; border-radius:12px; padding:20px 24px; margin-bottom:14px; border:1px solid {BORDER}; }}
.tag {{ background:{BG}; border:1px solid {BORDER}; border-radius:6px; padding:3px 10px; font-size:.74rem; color:{MUTED}; display:inline-block; margin:2px; }}
</style>
""", unsafe_allow_html=True)

# ── DATA ──────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    import os
    for p in ["superstore.csv", "Storytelling/superstore.csv", "Sample - Superstore.csv"]:
        if os.path.exists(p):
            df = pd.read_csv(p, encoding="latin1")
            df.columns = [c.strip() for c in df.columns]
            df["Order Date"] = pd.to_datetime(df["Order Date"])
            df["Year"] = df["Order Date"].dt.year
            return df
    st.error("No se encontró superstore.csv. Colócalo en la misma carpeta que dashboard.py.")
    st.stop()

df_raw = load_data()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────────
SECTIONS = [
    "1. Portada Ejecutiva",
    "2. Contexto del Negocio",
    "3. Exploración Visual",
    "4. Storytelling",
    "5. Interactividad",
    "6. Conclusiones",
]

with st.sidebar:
    st.markdown("""
    <div style="padding:16px 0 10px;">
      <div style="font-size:1.05rem;font-weight:800;color:white;letter-spacing:-.01em;">&#128202; Superstore</div>
      <div style="font-size:.72rem;color:#64748B;margin-top:2px;">Dashboard Estratégico</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    section = st.radio("Sección", SECTIONS, label_visibility="collapsed")

    st.divider()
    st.markdown(
        '<div style="font-size:.7rem;color:#64748B;font-weight:700;text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px;">Filtros</div>',
        unsafe_allow_html=True,
    )

    years_all = sorted(df_raw["Year"].unique().tolist())
    sel_years = st.multiselect("Año", years_all, default=years_all)

    regs_all  = sorted(df_raw["Region"].unique().tolist())
    sel_regs  = st.multiselect("Región", regs_all, default=regs_all)

    cats_all  = sorted(df_raw["Category"].unique().tolist())
    sel_cats  = st.multiselect("Categoría", cats_all, default=cats_all)

    segs_all  = sorted(df_raw["Segment"].unique().tolist())
    sel_segs  = st.multiselect("Segmento", segs_all, default=segs_all)

    d_lo, d_hi = st.slider("Rango de descuento (%)", 0, 80, (0, 80), step=5, format="%d%%")

# ── APPLY FILTERS ─────────────────────────────────────────────────────────────────
df = df_raw.copy()
if sel_years: df = df[df["Year"].isin(sel_years)]
if sel_regs:  df = df[df["Region"].isin(sel_regs)]
if sel_cats:  df = df[df["Category"].isin(sel_cats)]
if sel_segs:  df = df[df["Segment"].isin(sel_segs)]
df = df[(df["Discount"] >= d_lo / 100) & (df["Discount"] <= d_hi / 100)]

# ── HELPERS ───────────────────────────────────────────────────────────────────────
def fmt_m(v):
    if abs(v) >= 1e6: return f"${v/1e6:.2f}M"
    if abs(v) >= 1e3: return f"${v/1e3:.1f}K"
    return f"${v:.0f}"

def kpi_html(label, value, delta=None, color=None):
    c = color or MUTED
    d = f'<div class="kpi-delta" style="color:{c};">{delta}</div>' if delta else ""
    return f'<div class="kpi-card"><div class="kpi-value">{value}</div><div class="kpi-label">{label}</div>{d}</div>'

LAYOUT = dict(
    plot_bgcolor="white", paper_bgcolor="white",
    margin=dict(l=8, r=8, t=36, b=8),
    font=dict(family="Inter, -apple-system, sans-serif", color=TEXT, size=12),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
    hoverlabel=dict(bgcolor="white", font_size=12),
)

def render_chart(title, caption, fig):
    st.markdown(f'<div class="chart-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chart-caption">{caption}</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════════════════════════════
# SECTION 1 – PORTADA EJECUTIVA
# ══════════════════════════════════════════════════════════════════════════════════
def render_portada():
    total_s = df["Sales"].sum()
    total_p = df["Profit"].sum()
    margin  = total_p / total_s * 100 if total_s else 0

    st.markdown(f"""
    <div class="cover-card">
      <div class="cover-title">Ventas vs Rentabilidad:<br>Análisis Estratégico de Superstore</div>
      <div class="cover-sub">Dashboard interactivo para identificar oportunidades comerciales y riesgos de rentabilidad</div>
      <hr style="border-color:{BORDER};margin:32px 0;">
      <div style="display:flex;gap:48px;align-items:flex-start;">
        <div style="min-width:160px;">
          <div style="font-size:.7rem;color:{MUTED};text-transform:uppercase;letter-spacing:.08em;font-weight:700;">Integrantes</div>
          <div style="margin-top:8px;color:{TEXT};font-size:.9rem;line-height:1.9;">Equipo de Análisis Estratégico</div>
        </div>
        <div style="flex:1;border-left:1px solid {BORDER};padding-left:32px;">
          <div style="font-size:.7rem;color:{MUTED};text-transform:uppercase;letter-spacing:.08em;font-weight:700;">Resumen Ejecutivo</div>
          <div style="margin-top:8px;color:{TEXT};font-size:.89rem;line-height:1.75;">
            Este dashboard analiza el desempeño comercial de Superstore a partir de ventas, utilidad,
            descuentos, categorías y regiones. El objetivo es identificar qué productos generan mayor valor,
            qué categorías son más rentables y cómo los descuentos impactan las ganancias. El análisis muestra
            que vender más no siempre significa ganar más, ya que algunas categorías con altos ingresos presentan
            márgenes bajos o pérdidas. A partir de estos hallazgos, se proponen acciones para mejorar la
            rentabilidad y enfocar la estrategia comercial.
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_html("Ventas Totales", fmt_m(total_s), "Ingresos del período", SALES), unsafe_allow_html=True)
    with c2:
        pc = PROFIT if total_p >= 0 else LOSS
        st.markdown(kpi_html("Utilidad Total", fmt_m(total_p), "Ganancia neta", pc), unsafe_allow_html=True)
    with c3:
        mc = PROFIT if margin > 15 else (LOSS if margin < 5 else MUTED)
        st.markdown(kpi_html("Margen General", f"{margin:.2f}%", "Utilidad / Ventas", mc), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_html("Órdenes Únicas", f"{df['Order ID'].nunique():,}", "Transacciones registradas", MUTED), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════════
# SECTION 2 – CONTEXTO
# ══════════════════════════════════════════════════════════════════════════════════
def render_contexto():
    st.markdown('<div class="section-header">Contexto del Negocio</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        tags = "".join(
            f'<span class="tag">{t}</span>'
            for t in ["Fechas", "Regiones", "Categorías", "Ventas", "Descuentos", "Utilidad", "Segmentos"]
        )
        st.markdown(f"""
        <div class="kpi-card" style="min-height:230px;">
          <div style="font-size:.95rem;font-weight:700;color:{TEXT};margin-bottom:10px;">¿Qué representa el dataset?</div>
          <div style="color:{MUTED};font-size:.88rem;line-height:1.75;">
            El conjunto de datos representa órdenes de venta de una empresa minorista
            estadounidense. Incluye información de fechas, regiones, clientes, categorías
            de producto, ventas, descuentos, cantidad vendida y utilidad generada.
          </div>
          <div style="margin-top:14px;">{tags}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="kpi-card" style="min-height:230px;">
          <div style="font-size:.95rem;font-weight:700;color:{TEXT};margin-bottom:10px;">Problema de Negocio</div>
          <div style="color:{MUTED};font-size:.88rem;line-height:1.75;">
            La empresa busca entender si sus ventas están generando rentabilidad real.
            El análisis investiga qué categorías y regiones tienen mejor desempeño,
            qué productos generan pérdidas y cómo los descuentos afectan las utilidades.
          </div>
          <div style="margin-top:16px;background:{BG};border-left:3px solid {SALES};
                      padding:10px 14px;border-radius:0 8px 8px 0;font-size:.83rem;
                      color:{TEXT};font-style:italic;line-height:1.5;">
            ¿La empresa está vendiendo de forma rentable o está sacrificando utilidad
            por descuentos y productos poco rentables?
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    yr_min = int(df_raw["Year"].min())
    yr_max = int(df_raw["Year"].max())
    stats = [
        ("Registros",      f"{len(df_raw):,}"),
        ("Período",        f"{yr_min}–{yr_max}"),
        ("Categorías",     f"{df_raw['Category'].nunique()}"),
        ("Regiones",       f"{df_raw['Region'].nunique()}"),
        ("Sub-Categorías", f"{df_raw['Sub-Category'].nunique()}"),
    ]
    for col, (label, val) in zip(st.columns(5), stats):
        with col:
            st.markdown(kpi_html(label, val), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════════
# SECTION 3 – EXPLORACIÓN VISUAL
# ══════════════════════════════════════════════════════════════════════════════════
def render_exploracion():
    st.markdown('<div class="section-header">Exploración Visual</div>', unsafe_allow_html=True)

    # KPIs
    total_s  = df["Sales"].sum()
    total_p  = df["Profit"].sum()
    margin   = total_p / total_s * 100 if total_s else 0
    avg_disc = df["Discount"].mean() * 100
    n_ord    = df["Order ID"].nunique()

    kpi_data = [
        ("Ventas Totales",  fmt_m(total_s),     "Ingresos del período",   SALES),
        ("Utilidad Total",  fmt_m(total_p),     "Ganancia neta",          PROFIT if total_p >= 0 else LOSS),
        ("Margen General",  f"{margin:.2f}%",   "Utilidad / Ventas",      PROFIT if margin > 15 else (LOSS if margin < 5 else MUTED)),
        ("Desc. Promedio",  f"{avg_disc:.2f}%", "Impacto en margen",      LOSS if avg_disc > 20 else MUTED),
        ("Órdenes",         f"{n_ord:,}",       "Transacciones",          MUTED),
    ]
    for col, (label, val, delta, clr) in zip(st.columns(5), kpi_data):
        with col:
            st.markdown(kpi_html(label, val, delta, clr), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráfica 1: Temporal
    df_t = df.copy()
    df_t["Month"] = df_t["Order Date"].dt.to_period("M").dt.to_timestamp()
    df_m = df_t.groupby("Month").agg(Sales=("Sales", "sum"), Profit=("Profit", "sum")).reset_index()

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=df_m["Month"], y=df_m["Sales"], name="Ventas",
        line=dict(color=SALES, width=2.5),
        fill="tozeroy", fillcolor="rgba(37,99,235,.07)",
    ))
    fig1.add_trace(go.Scatter(
        x=df_m["Month"], y=df_m["Profit"], name="Utilidad",
        line=dict(color=PROFIT, width=2.5),
        fill="tozeroy", fillcolor="rgba(20,184,166,.07)",
    ))
    fig1.update_layout(**LAYOUT, height=310,
        yaxis=dict(tickprefix="$", gridcolor="#F1F5F9", showgrid=True, zeroline=False),
        xaxis=dict(showgrid=False),
        hovermode="x unified",
    )
    render_chart(
        "Ventas y utilidad en el tiempo",
        "Las ventas muestran el volumen del negocio; la utilidad muestra si ese volumen realmente se convierte en ganancia.",
        fig1,
    )

    # Gráfica 2: Categorías
    df_cat = df.groupby("Category").agg(Sales=("Sales", "sum"), Profit=("Profit", "sum")).reset_index()

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        name="Ventas", x=df_cat["Category"], y=df_cat["Sales"],
        marker_color=SALES, opacity=.85,
        text=df_cat["Sales"].apply(fmt_m), textposition="outside",
    ))
    fig2.add_trace(go.Bar(
        name="Utilidad", x=df_cat["Category"], y=df_cat["Profit"],
        marker_color=[PROFIT if p >= 0 else LOSS for p in df_cat["Profit"]],
        text=df_cat["Profit"].apply(fmt_m), textposition="outside",
    ))
    fig2.update_layout(**LAYOUT, height=360,
        barmode="group",
        yaxis=dict(tickprefix="$", gridcolor="#F1F5F9", zeroline=False),
        xaxis=dict(showgrid=False),
    )
    render_chart(
        "Ventas altas no siempre significan mayor utilidad",
        "Furniture vende $742K pero genera apenas $18K de utilidad — margen de solo 2.5%. Technology y Office Supplies son mucho más eficientes.",
        fig2,
    )

    # Gráfica 3: Scatter Descuento vs Utilidad
    df_sc = df.copy()
    df_sc["Resultado"] = df_sc["Profit"].apply(lambda p: "Ganancia" if p >= 0 else "Pérdida")
    sample = df_sc.sample(min(len(df_sc), 2500), random_state=42) if len(df_sc) > 2500 else df_sc

    fig3 = px.scatter(
        sample, x="Discount", y="Profit",
        color="Resultado",
        color_discrete_map={"Ganancia": PROFIT, "Pérdida": LOSS},
        size="Sales", size_max=18,
        hover_data={
            "Product Name": True, "Category": True, "Region": True,
            "Sales": ":,.0f", "Profit": ":,.0f", "Discount": ":.0%",
            "Resultado": False,
        },
        opacity=.6,
    )
    fig3.add_hline(
        y=0, line_dash="dot", line_color=MUTED, line_width=1.5,
        annotation_text="Sin ganancia", annotation_position="top left",
        annotation_font_color=MUTED,
    )
    fig3.update_layout(**LAYOUT, height=420,
        xaxis=dict(tickformat=",.0%", showgrid=False, title="Descuento"),
        yaxis=dict(tickprefix="$", gridcolor="#F1F5F9", title="Utilidad"),
    )
    render_chart(
        "El costo oculto de los descuentos",
        "Cuando el descuento supera el 20%, la mayoría de las ventas terminan en pérdida. Cada punto hacia la derecha destruye margen.",
        fig3,
    )

    # Gráfica 4: Heatmap Región × Categoría
    df_h   = df.groupby(["Region", "Category"])["Profit"].sum().reset_index()
    df_piv = df_h.pivot(index="Region", columns="Category", values="Profit").fillna(0)
    df_piv = df_piv.loc[df_piv.sum(axis=1).sort_values(ascending=False).index]

    fig4 = go.Figure(go.Heatmap(
        z=df_piv.values,
        x=df_piv.columns.tolist(),
        y=df_piv.index.tolist(),
        colorscale=[[0.0, LOSS], [0.35, "#FCA5A5"], [0.5, "#F8FAFC"], [0.70, "#99F6E4"], [1.0, PROFIT]],
        zmid=0,
        text=[[fmt_m(v) for v in row] for row in df_piv.values],
        texttemplate="%{text}",
        textfont=dict(size=13),
        hoverongaps=False,
        colorbar=dict(title="Utilidad", tickprefix="$", thickness=14),
    ))
    fig4.update_layout(**LAYOUT, height=270,
        xaxis=dict(side="top", title=""),
        yaxis=dict(title=""),
        margin=dict(l=8, r=8, t=50, b=8),
    )
    render_chart(
        "¿Dónde se concentra la baja rentabilidad?",
        "Central tiene el margen más débil (7.9%). Furniture arrastra la rentabilidad en todas las regiones.",
        fig4,
    )

    # Gráfica 5: Subcategorías
    df_sub = df.groupby("Sub-Category")["Profit"].sum().reset_index().sort_values("Profit")
    df_sub["Color"] = df_sub["Profit"].apply(lambda p: LOSS if p < 0 else PROFIT)
    df_sub["Label"] = df_sub["Profit"].apply(fmt_m)

    fig5 = go.Figure(go.Bar(
        x=df_sub["Profit"], y=df_sub["Sub-Category"],
        orientation="h",
        marker_color=df_sub["Color"],
        text=df_sub["Label"],
        textposition="outside",
        cliponaxis=False,
    ))
    fig5.add_vline(x=0, line_color=MUTED, line_width=1.5, line_dash="dot")
    fig5.update_layout(**LAYOUT, height=450,
        xaxis=dict(tickprefix="$", showgrid=True, gridcolor="#F1F5F9", title="Utilidad"),
        yaxis=dict(showgrid=False, title=""),
        margin=dict(l=8, r=90, t=10, b=8),
    )
    render_chart(
        "Subcategorías que reducen la rentabilidad",
        "Tables (−$17.7K), Bookcases (−$3.5K) y Supplies (−$1.2K) destruyen valor activamente. Explican por qué Furniture tiene tan bajo margen.",
        fig5,
    )


# ══════════════════════════════════════════════════════════════════════════════════
# SECTION 4 – STORYTELLING
# ══════════════════════════════════════════════════════════════════════════════════
def render_storytelling():
    st.markdown('<div class="section-header">Storytelling</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">La historia que cuentan los datos</div>', unsafe_allow_html=True)

    steps = [
        (SALES,  "01", "📈", "Situación: El negocio vende bien",
         "Superstore presenta un alto volumen de ventas en diferentes categorías y regiones. Con $2.30M en ingresos y 5,009 órdenes procesadas, la operación es robusta y tiene presencia en todo el país."),
        (AMBER,  "02", "⚠️", "Hallazgo: No todo lo vendido se convierte en ganancia",
         "Furniture, a pesar de generar $742K en ventas, registra apenas $18K de utilidad — margen de solo 2.5%, muy por debajo del promedio de 12.47%. Vender mucho no es lo mismo que ganar mucho."),
        (LOSS,   "03", "🔍", "Evidencia: Descuentos y categorías explican el problema",
         "A medida que el descuento supera el 20%, las ventas frecuentemente generan pérdida. Subcategorías como Tables (−$17.7K), Bookcases (−$3.5K) y Supplies (−$1.2K) destruyen valor activamente."),
        (PROFIT, "04", "✅", "Recomendación: Enfocar en rentabilidad, no solo en volumen",
         "Limitar descuentos agresivos en Furniture, revisar subcategorías con pérdida estructural, y fortalecer categorías con mayor margen: Technology (17.4%) y Office Supplies (17.0%)."),
    ]

    for color, num, icon, title, body in steps:
        st.markdown(f"""
        <div class="story-step" style="border-left:5px solid {color};">
          <div style="display:flex;gap:16px;align-items:flex-start;">
            <div style="font-size:1.8rem;line-height:1;">{icon}</div>
            <div style="flex:1;">
              <div style="font-size:.67rem;font-weight:800;color:{color};text-transform:uppercase;letter-spacing:.12em;">Paso {num}</div>
              <div style="font-size:.96rem;font-weight:700;color:{TEXT};margin:4px 0 6px;">{title}</div>
              <div style="font-size:.87rem;color:{MUTED};line-height:1.65;">{body}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:#EFF6FF;border-radius:12px;padding:24px 28px;
                border:1px solid #BFDBFE;margin-top:6px;text-align:center;">
      <div style="font-size:.7rem;color:{SALES};text-transform:uppercase;letter-spacing:.12em;font-weight:800;margin-bottom:8px;">Pregunta central del negocio</div>
      <div style="font-size:1.05rem;font-weight:700;color:{TEXT};font-style:italic;line-height:1.5;">
        "¿La empresa está vendiendo de forma rentable o está sacrificando utilidad<br>por descuentos y productos poco rentables?"
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════════
# SECTION 5 – INTERACTIVIDAD
# ══════════════════════════════════════════════════════════════════════════════════
def render_interactividad():
    st.markdown('<div class="section-header">Interactividad</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="kpi-card" style="margin-bottom:20px;">
      <div style="font-size:.88rem;color:{MUTED};line-height:1.75;">
        Los filtros del sidebar permiten analizar el desempeño por año, región, categoría, segmento
        y nivel de descuento. Esto ayuda a identificar si los problemas de rentabilidad son generales
        o si se concentran en ciertos grupos específicos.
      </div>
    </div>
    """, unsafe_allow_html=True)

    filters_info = [
        ("📅", "Año",                "Multiselect", "Filtra por año para analizar tendencias temporales 2014–2017."),
        ("🗺️", "Región",             "Multiselect", "Aisla West, East, Central o South para análisis territorial."),
        ("📦", "Categoría",          "Multiselect", "Compara Technology, Office Supplies y Furniture individualmente."),
        ("👥", "Segmento",           "Multiselect", "Distingue Consumer, Corporate y Home Office."),
        ("🏷️", "Rango de Descuento", "Slider",      "Ajusta el rango (0–80%) para ver cómo distintos niveles afectan la rentabilidad."),
    ]

    for col, (icon, title, widget, desc) in zip(st.columns(5), filters_info):
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="text-align:center;min-height:210px;">
              <div style="font-size:1.7rem;margin-bottom:10px;">{icon}</div>
              <div style="font-size:.88rem;font-weight:700;color:{TEXT};margin-bottom:6px;">{title}</div>
              <div style="font-size:.74rem;color:{MUTED};line-height:1.5;margin-bottom:10px;">{desc}</div>
              <span style="background:{BG};border:1px solid {BORDER};border-radius:6px;
                           padding:3px 9px;font-size:.68rem;color:{MUTED};font-weight:600;">{widget}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:#F0FDF4;border-radius:10px;padding:14px 18px;
                border:1px solid #BBF7D0;margin-top:16px;">
      <div style="font-size:.84rem;color:#166534;line-height:1.5;">
        <strong>Prueba ahora:</strong> Usa los filtros del sidebar para explorar los datos en tiempo real.
        Todos los gráficos de <em>Exploración Visual</em> se actualizan automáticamente.
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════════
# SECTION 6 – CONCLUSIONES
# ══════════════════════════════════════════════════════════════════════════════════
def render_conclusiones():
    st.markdown('<div class="section-header">Conclusiones</div>', unsafe_allow_html=True)

    st.markdown(f'<div style="font-size:.95rem;font-weight:700;color:{TEXT};margin:0 0 12px;">3 Hallazgos Principales</div>', unsafe_allow_html=True)

    findings = [
        (PROFIT, "1", "Technology: la categoría más rentable",
         "Con $145K de utilidad y un margen de 17.4%, Technology es el motor de rentabilidad de Superstore. Priorizar su crecimiento es la apuesta más segura."),
        (LOSS,   "2", "Furniture: riesgo latente de rentabilidad",
         "Vende $742K pero genera apenas $18K de utilidad — margen de 2.5%. Subcategorías como Tables (−$17.7K) destruyen valor activamente."),
        (AMBER,  "3", "Los descuentos reducen la utilidad",
         "Los descuentos altos reducen la utilidad, especialmente cuando se combinan con categorías de bajo margen como Furniture."),
    ]

    for color, num, title, body in findings:
        st.markdown(f"""
        <div style="background:{CARD};border-radius:10px;padding:16px 20px;
                    margin-bottom:10px;border:1px solid {BORDER};
                    display:flex;gap:14px;align-items:flex-start;">
          <div style="width:30px;height:30px;border-radius:50%;background:{color}25;
                      color:{color};font-weight:800;font-size:.95rem;flex-shrink:0;
                      display:flex;align-items:center;justify-content:center;">{num}</div>
          <div>
            <div style="font-size:.93rem;font-weight:700;color:{TEXT};margin-bottom:4px;">{title}</div>
            <div style="font-size:.84rem;color:{MUTED};line-height:1.6;">{body}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f'<div style="font-size:.95rem;font-weight:700;color:{TEXT};margin:22px 0 12px;">2 Recomendaciones Accionables</div>', unsafe_allow_html=True)

    recs = [
        ("🚫", "Limitar descuentos agresivos",
         "Principalmente en Furniture y productos con historial de pérdida. Establecer un techo máximo (~15%) para categorías de menor margen."),
        ("🎯", "Priorizar categorías rentables",
         "Enfocar esfuerzos en Technology y Office Supplies. Revisar Tables, Bookcases y Supplies — reducir volumen o ajustar precios para recuperar margen."),
    ]

    for col, (icon, title, body) in zip(st.columns(2), recs):
        with col:
            st.markdown(f"""
            <div style="background:{CARD};border-radius:12px;padding:22px;
                        border:1px solid {BORDER};border-top:4px solid {PROFIT};">
              <div style="font-size:1.6rem;margin-bottom:10px;">{icon}</div>
              <div style="font-size:.93rem;font-weight:700;color:{TEXT};margin-bottom:6px;">{title}</div>
              <div style="font-size:.84rem;color:{MUTED};line-height:1.65;">{body}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f'<div style="font-size:.95rem;font-weight:700;color:{TEXT};margin:22px 0 10px;">Resumen por Categoría (datos filtrados)</div>', unsafe_allow_html=True)
    df_cat = df.groupby("Category").agg(Sales=("Sales", "sum"), Profit=("Profit", "sum")).reset_index()
    df_cat["Margen"] = (df_cat["Profit"] / df_cat["Sales"] * 100).round(1)
    df_cat["Sales"]  = df_cat["Sales"].apply(fmt_m)
    df_cat["Profit"] = df_cat["Profit"].apply(fmt_m)
    df_cat["Margen"] = df_cat["Margen"].apply(lambda x: f"{x:.1f}%")
    df_cat.columns = ["Categoría", "Ventas", "Utilidad", "Margen"]
    st.dataframe(df_cat, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════════
# ROUTING
# ══════════════════════════════════════════════════════════════════════════════════
{
    SECTIONS[0]: render_portada,
    SECTIONS[1]: render_contexto,
    SECTIONS[2]: render_exploracion,
    SECTIONS[3]: render_storytelling,
    SECTIONS[4]: render_interactividad,
    SECTIONS[5]: render_conclusiones,
}[section]()
