import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import math, random
from datetime import datetime, timedelta

st.set_page_config(
    page_title="PrediTeq — SuperAdmin",
    page_icon="⚙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════ SESSION STATE ══════════════════
def _init(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

_init("lang", "FR")
_init("dark_mode", False)
_init("active_panel", None)
_init("edit_index", None)
_init("active_tab", "map")
_init("sel_machine", None)
_init("report_text", None)
_init("machines", [
    {
        "id": "AscSITI-01", "client": "Aroteq R&D", "city": "Ben Arous",
        "lat": 36.7541, "lon": 10.2317,
        "hi": 0.82, "rul": 47, "rul_ci": 4, "status": "OK",
        "model": "SITI FC100L1-4", "floors": 18,
        "vib_rms": 1.3, "current": 4.21, "temp": 23.4,
        "last_upd": "2026-03-05 08:42", "anomalies_24h": 1, "cycles_today": 82
    },
    {
        "id": "AscSITI-02", "client": "Industrie Centrale", "city": "Tunis",
        "lat": 36.8190, "lon": 10.1658,
        "hi": 0.48, "rul": 18, "rul_ci": 3, "status": "SURVEILLANCE",
        "model": "SITI FC100L1-4", "floors": 18,
        "vib_rms": 3.1, "current": 4.68, "temp": 27.1,
        "last_upd": "2026-03-05 09:15", "anomalies_24h": 7, "cycles_today": 74
    },
    {
        "id": "AscSITI-03", "client": "LogiStock Sfax", "city": "Sfax",
        "lat": 34.7394, "lon": 10.7600,
        "hi": 0.19, "rul": 4, "rul_ci": 1, "status": "URGENCE",
        "model": "SITI FC100L1-4", "floors": 18,
        "vib_rms": 6.8, "current": 4.97, "temp": 31.2,
        "last_upd": "2026-03-05 07:58", "anomalies_24h": 23, "cycles_today": 61
    },
])

# ══════════════════ TRANSLATIONS ══════════════════
T = {
    "subtitle":     {"FR":"Vue SuperAdmin — Gestion du Parc","EN":"SuperAdmin View — Fleet Management"},
    "total":        {"FR":"Machines totales","EN":"Total machines"},
    "ok_pct":       {"FR":"Opérationnel","EN":"Operational"},
    "surv_pct":     {"FR":"Surveillance","EN":"Surveillance"},
    "urg_pct":      {"FR":"Critique","EN":"Critical"},
    "machine_list": {"FR":"Parc machines","EN":"Machine fleet"},
    "hi":           {"FR":"Indice de Santé","EN":"Health Index"},
    "rul_lbl":      {"FR":"RUL estimé","EN":"Estimated RUL"},
    "days":         {"FR":"jours","EN":"days"},
    "last_upd":     {"FR":"Mise à jour","EN":"Last update"},
    "ok_lbl":       {"FR":"Opérationnel","EN":"Operational"},
    "surv_lbl":     {"FR":"Surveillance","EN":"Surveillance"},
    "urg_lbl":      {"FR":"Critique","EN":"Critical"},
    "click_hint":   {"FR":"Cliquez sur un marqueur pour les détails","EN":"Click a marker for details"},
    "map_title":    {"FR":"Déploiement Tunisie — 2026","EN":"Tunisia Deployment — 2026"},
    "sel_mach":     {"FR":"Machine sélectionnée","EN":"Selected machine"},
    "vibration":    {"FR":"Vibration Moteur","EN":"Motor Vibration"},
    "current_lbl":  {"FR":"Courant Moteur","EN":"Motor Current"},
    "temp_lbl":     {"FR":"Température Moteur","EN":"Motor Temperature"},
    "open_maps":    {"FR":"Voir sur Maps","EN":"View on Maps"},
    "status_lbl":   {"FR":"Statut","EN":"Status"},
    "manage_btn":   {"FR":"Gérer les machines","EN":"Manage machines"},
    "add_mach":     {"FR":"Ajouter une machine","EN":"Add a machine"},
    "edit_mach":    {"FR":"Modifier","EN":"Edit"},
    "del_mach":     {"FR":"Supprimer","EN":"Delete"},
    "confirm_del":  {"FR":"Confirmer la suppression ?","EN":"Confirm deletion?"},
    "save":         {"FR":"Enregistrer","EN":"Save"},
    "cancel":       {"FR":"Annuler","EN":"Cancel"},
    "close":        {"FR":"Fermer","EN":"Close"},
    "saved_ok":     {"FR":"Machine enregistrée.","EN":"Machine saved."},
    "del_ok":       {"FR":"Machine supprimée.","EN":"Machine deleted."},
    "add_ok":       {"FR":"Machine ajoutée.","EN":"Machine added."},
    "gps_tip":      {"FR":"Google Maps → clic droit → copier les coordonnées.","EN":"Google Maps → right-click → copy coordinates."},
    "sys_active":   {"FR":"Système actif","EN":"System active"},
    "tab_map":      {"FR":"Carte","EN":"Map"},
    "tab_op":       {"FR":"Opérateur","EN":"Operator"},
    "tab_adm":      {"FR":"Admin","EN":"Admin"},
    "tab_rep":      {"FR":"Rapports IA","EN":"AI Reports"},
    "tab_alt":      {"FR":"Alertes","EN":"Alerts"},
    "op_sel":       {"FR":"Sélectionner une machine","EN":"Select a machine"},
    "op_live":      {"FR":"Données temps réel","EN":"Live data"},
    "op_hist":      {"FR":"Historique 6 hres","EN":"6h History"},
    "op_hi_trend":  {"FR":"Évolution Health Index — 7 jours","EN":"Health Index Trend — 7 days"},
    "op_cycles":    {"FR":"Cycles aujourd'hui","EN":"Cycles today"},
    "op_anom":      {"FR":"Anomalies 24h","EN":"Anomalies 24h"},
    "realtime":     {"FR":"Temps Réel","EN":"Real Time"},
    "adm_rep":      {"FR":"Rapport IA","EN":"AI Report"},
    "adm_gen":      {"FR":"Générer rapport","EN":"Generate report"},
    "adm_pdf":      {"FR":"Exporter PDF","EN":"Export PDF"},
    "adm_anom":     {"FR":"Historique anomalies","EN":"Anomaly history"},
    "adm_thresh":   {"FR":"Seuils d'alerte","EN":"Alert thresholds"},
    "adm_hi_urg":   {"FR":"HI seuil critique","EN":"Critical HI threshold"},
    "adm_shap":     {"FR":"Features influentes","EN":"Key Features"},
    "rep_weekly":   {"FR":"Rapport Hebdomadaire","EN":"Weekly Report"},
    "rep_monthly":  {"FR":"Rapport Mensuel","EN":"Monthly Report"},
    "rep_gen":      {"FR":"Générer","EN":"Generate"},
    "alt_title":    {"FR":"Alertes email — automatiques","EN":"Email alerts — automatic"},
    "alt_desc":     {"FR":"Les alertes sont déclenchées automatiquement par le pipeline ML selon les seuils HI et RUL. Aucune action manuelle requise.","EN":"Alerts are triggered automatically by the ML pipeline based on HI and RUL thresholds. No manual action required."},
    "alt_log":      {"FR":"Journal des alertes récentes","EN":"Recent alert log"},
    "alt_boss":     {"FR":"Email responsable","EN":"Manager email"},
    "alt_admin":    {"FR":"Email technicien supérieur","EN":"Senior technician email"},
    "alt_cond":     {"FR":"Conditions de déclenchement automatique","EN":"Automatic trigger conditions"},
    "alt_save":     {"FR":"Enregistrer","EN":"Save"},
    "id_exists":    {"FR":"Cet identifiant existe déjà.","EN":"This ID already exists."},
    "no_machines":  {"FR":"Aucune machine enregistrée.","EN":"No machines registered."},
    "sec_info":     {"FR":"Informations machine","EN":"Machine information"},
    "sec_gps":      {"FR":"Localisation GPS","EN":"GPS Location"},
    "sec_sensors":  {"FR":"Données capteurs","EN":"Sensor data"},
    "field_id":     {"FR":"Identifiant machine","EN":"Machine ID"},
    "field_client": {"FR":"Nom du client","EN":"Client name"},
    "field_city":   {"FR":"Ville","EN":"City"},
    "field_lat":    {"FR":"Latitude GPS","EN":"GPS Latitude"},
    "field_lon":    {"FR":"Longitude GPS","EN":"GPS Longitude"},
    "field_model":  {"FR":"Modèle","EN":"Model"},
    "field_floors": {"FR":"Niveaux","EN":"Floors"},
    "field_status": {"FR":"Statut","EN":"Status"},
    "field_hi":     {"FR":"Indice de Santé (0–1)","EN":"Health Index (0–1)"},
    "field_rul":    {"FR":"RUL estimé (jours)","EN":"Estimated RUL (days)"},
    "field_ci":     {"FR":"Intervalle confiance (±j)","EN":"Confidence interval (±d)"},
    "field_vib":    {"FR":"Vibration RMS (mm/s)","EN":"Vibration RMS (mm/s)"},
    "field_cur":    {"FR":"Courant (A)","EN":"Current (A)"},
    "field_temp":   {"FR":"Température (°C)","EN":"Temperature (°C)"},
    "manage_title": {"FR":"Gestion du parc machines","EN":"Machine fleet management"},
}

def t(k):
    return T.get(k, {}).get(st.session_state.lang, k)

STATUS_CFG = {
    "OK":           {"color":"#0d9488","gradient":"linear-gradient(135deg,#0f766e,#0d9488)","border":"rgba(13,148,136,0.4)","pill_bg":"rgba(13,148,136,0.15)","folium_color":"green","dot":"#0d9488","td":"#2dd4bf","tl":"#0f766e"},
    "SURVEILLANCE": {"color":"#f59e0b","gradient":"linear-gradient(135deg,#d97706,#fbbf24)","border":"rgba(245,158,11,0.4)","pill_bg":"rgba(245,158,11,0.12)","folium_color":"orange","dot":"#f59e0b","td":"#fbbf24","tl":"#92400e"},
    "URGENCE":      {"color":"#f43f5e","gradient":"linear-gradient(135deg,#be123c,#f43f5e)","border":"rgba(244,63,94,0.4)","pill_bg":"rgba(244,63,94,0.12)","folium_color":"red","dot":"#f43f5e","td":"#fb7185","tl":"#9f1239"},
}
SL_FR = {"Opérationnel":"OK","Surveillance":"SURVEILLANCE","Critique":"URGENCE"}
SL_EN = {"Operational":"OK","Surveillance":"SURVEILLANCE","Critical":"URGENCE"}
SD_FR = {"OK":"Opérationnel","SURVEILLANCE":"Surveillance","URGENCE":"Critique"}
SD_EN = {"OK":"Operational","SURVEILLANCE":"Surveillance","URGENCE":"Critical"}

def get_opts():
    return SL_FR if st.session_state.lang == "FR" else SL_EN

def s_disp(s):
    return SD_FR[s] if st.session_state.lang == "FR" else SD_EN[s]

# ══════════════════ THEME ══════════════════
dk = st.session_state.dark_mode

def scol(cfg):
    return cfg["td"] if dk else cfg["tl"]

if dk:
    BG="#0a1628"; SB="#0d1f2d"; CARD="rgba(13,31,45,0.95)"
    TP="#f8fffe"; TS="#cbd5e1"; TD="#94a3b8"
    B="rgba(255,255,255,0.07)"; BH="rgba(255,255,255,0.12)"
    SF="rgba(255,255,255,0.04)"; SF2="rgba(255,255,255,0.08)"
    IB="rgba(255,255,255,0.05)"; DIV="rgba(255,255,255,0.06)"
    HDR="linear-gradient(135deg,#0d2137 0%,#0d3d38 50%,#093530 100%)"
    HB="rgba(13,148,136,0.22)"; TL="#14b8a6"
    BC="#14b8a6"; BB="rgba(13,148,136,0.10)"; BBD="rgba(13,148,136,0.28)"; BH2="rgba(13,148,136,0.20)"
    KT="#14b8a6"; KO="#2dd4bf"; KS="#fbbf24"; KU="#fb7185"; KL="#cbd5e1"
    HT="rgba(255,255,255,0.08)"
    PB="rgba(13,31,45,0)"; PG="rgba(255,255,255,0.05)"; PT="#94a3b8"
    GAUGE_TRACK="#1e3a4a"; CARD_BG="#0d1f2d"; NEEDLE_COL="#e2e8f0"
    GAUGE_PANEL_BG="#0d1f2d"; GAUGE_PANEL_BORDER="#1e3a4a"; GAUGE_TEXT="#f8fffe"; GAUGE_SUBTEXT="#94a3b8"
else:
    BG="#f0f4f8"; SB="#ffffff"; CARD="rgba(255,255,255,0.97)"
    TP="#0f172a"; TS="#334155"; TD="#64748b"
    B="rgba(15,23,42,0.09)"; BH="rgba(15,23,42,0.15)"
    SF="rgba(15,23,42,0.03)"; SF2="rgba(15,23,42,0.06)"
    IB="#ffffff"; DIV="rgba(15,23,42,0.07)"
    HDR="linear-gradient(135deg,#134e4a 0%,#0f766e 50%,#0d9488 100%)"
    HB="rgba(13,148,136,0.3)"; TL="#0d9488"
    BC="#0f766e"; BB="rgba(13,148,136,0.08)"; BBD="rgba(13,148,136,0.25)"; BH2="rgba(13,148,136,0.15)"
    KT="#0f766e"; KO="#0f766e"; KS="#92400e"; KU="#9f1239"; KL="#334155"
    HT="#e2e8f0"
    PB="rgba(255,255,255,0)"; PG="rgba(15,23,42,0.05)"; PT="#64748b"
    GAUGE_TRACK="#dde3ea"; CARD_BG="#ffffff"; NEEDLE_COL="#334155"
    GAUGE_PANEL_BG="#ffffff"; GAUGE_PANEL_BORDER="#e2e8f0"; GAUGE_TEXT="#0f172a"; GAUGE_SUBTEXT="#64748b"

CS = "0 4px 24px rgba(0,0,0,0.3)" if dk else "0 2px 16px rgba(0,0,0,0.06)"
CH = "0 16px 48px rgba(0,0,0,0.4)" if dk else "0 10px 28px rgba(0,0,0,0.12)"
BL = "backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);" if dk else ""

# ══════════════════ CSS ══════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
html,body,[class*="css"]{{font-family:'Sora',sans-serif!important;background:{BG}!important;color:{TP}!important;}}
::-webkit-scrollbar{{width:3px;}};::-webkit-scrollbar-thumb{{background:rgba(13,148,136,.35);border-radius:99px;}}
section[data-testid="stSidebar"]{{background:{SB}!important;border-right:1px solid {BH}!important;}}
section[data-testid="stSidebar"] *{{color:{TP}!important;}}
section[data-testid="stSidebar"] .stButton>button{{background:{BB}!important;border:1px solid {BBD}!important;color:{BC}!important;font-family:'Sora',sans-serif!important;font-size:.72rem!important;font-weight:600!important;border-radius:12px!important;padding:.5rem 1rem!important;width:100%!important;transition:all .2s!important;}}
section[data-testid="stSidebar"] .stButton>button:hover{{background:{BH2}!important;border-color:{TL}!important;}}
.main .block-container{{background:{BG};padding-top:1.4rem;max-width:1540px;overflow-x:hidden;isolation:isolate;}}
.stApp{{background:{BG}!important;}}
iframe{{display:block!important;border:0!important;background:transparent!important;}}
.plh{{background:{HDR};border:1px solid {HB};border-radius:20px;padding:2rem 2.5rem;margin-bottom:1.4rem;display:flex;align-items:center;justify-content:space-between;position:relative;overflow:hidden;box-shadow:0 8px 48px rgba(0,0,0,{'.45' if dk else '.18'});}}
.plh::before{{content:'';position:absolute;top:-80px;right:-80px;width:320px;height:320px;background:radial-gradient(circle,rgba(255,255,255,.06) 0%,transparent 65%);pointer-events:none;}}
.plh-logo{{font-size:2.5rem;font-weight:800;color:#fff;letter-spacing:-1.5px;line-height:1;position:relative;z-index:2;}}
.plh-logo span{{color:#5eead4;}}
.plh-tag{{font-size:.82rem;color:rgba(255,255,255,.9);letter-spacing:3px;text-transform:uppercase;margin-top:7px;font-weight:500;position:relative;z-index:2;}}
.plh-right{{display:flex;flex-direction:column;align-items:flex-end;gap:8px;position:relative;z-index:2;}}
.plh-badge{{background:rgba(255,255,255,.2);border:1px solid rgba(255,255,255,.45);border-radius:10px;padding:.35rem 1.2rem;font-size:.74rem;font-family:'JetBrains Mono',monospace;color:#ffffff;letter-spacing:2px;text-transform:uppercase;font-weight:700;}}
.plh-time{{font-family:'JetBrains Mono',monospace;font-size:.78rem;color:#ffffff;letter-spacing:1px;font-weight:600;text-shadow:0 1px 4px rgba(0,0,0,0.3);}}
.online-dot{{display:inline-block;width:6px;height:6px;background:#5eead4;border-radius:50%;box-shadow:0 0 8px rgba(94,234,212,.8);margin-right:5px;animation:blink 2.5s infinite;}}
@keyframes blink{{0%,100%{{opacity:1;}}50%{{opacity:.35;}}}}
.kpi-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:1.6rem;}}
.kc{{background:{CARD};border:1px solid {B};border-radius:18px;padding:1.5rem 1.6rem;position:relative;overflow:hidden;{BL}transition:transform .2s,box-shadow .2s;box-shadow:{CS};}}
.kc:hover{{transform:translateY(-4px);box-shadow:{CH};}}
.kc::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;border-radius:18px 18px 0 0;}}
.kc.tot::before{{background:linear-gradient(90deg,{TL},#5eead4);}}
.kc.ok_::before{{background:linear-gradient(90deg,#0f766e,#0d9488);}}
.kc.sv_::before{{background:linear-gradient(90deg,#d97706,#fbbf24);}}
.kc.ur_::before{{background:linear-gradient(90deg,#be123c,#f43f5e);}}
.kc-lbl{{font-size:.7rem;color:{KL};letter-spacing:2.5px;text-transform:uppercase;font-weight:700;}}
.kc-val{{font-family:'JetBrains Mono',monospace;font-size:2.8rem;font-weight:600;line-height:1;margin-bottom:.2rem;}}
.kc.tot .kc-val{{color:{KT};}} .kc.ok_ .kc-val{{color:{KO};}} .kc.sv_ .kc-val{{color:{KS};}} .kc.ur_ .kc-val{{color:{KU};}}
.hs{{background:{CARD};border:1px solid {B};border-radius:14px;padding:1rem 1.6rem;margin-bottom:1.1rem;display:flex;align-items:center;justify-content:space-between;{BL}box-shadow:{CS};}}
.hs-lbl{{font-size:.6rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};font-family:'JetBrains Mono',monospace;font-weight:600;}}
.hs-track{{flex:1;margin:0 1.5rem;background:{HT};border-radius:99px;height:6px;overflow:hidden;}}
.hs-fill{{height:100%;border-radius:99px;background:linear-gradient(90deg,#f43f5e 0%,#f59e0b 40%,#0d9488 75%,#0d9488 100%);}}
.hs-score{{font-family:'JetBrains Mono',monospace;font-size:1.2rem;font-weight:700;}}
.det{{background:{CARD};border:1px solid {B};border-radius:16px;padding:1.3rem 1.5rem;{BL}box-shadow:{CS};height:100%;}}
.det-lbl{{font-size:.67rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};margin-bottom:9px;font-family:'JetBrains Mono',monospace;font-weight:600;}}
.det-val{{font-family:'JetBrains Mono',monospace;font-size:2.4rem;font-weight:600;line-height:1;}}
.det-sub{{font-size:.8rem;color:{TS};margin-top:5px;line-height:1.6;font-weight:500;}}
.det-dim{{font-size:.72rem;color:{TD};margin-top:3px;}}
.mc{{background:{SF};border:1px solid {B};border-radius:14px;padding:.95rem 1.05rem;margin-bottom:.55rem;border-left:2px solid;transition:all .18s;}}
.mc:hover{{background:{SF2};transform:translateX(3px);}}
.mc-id{{font-family:'JetBrains Mono',monospace;font-size:.88rem;font-weight:600;color:{TP};}}
.mc-cli{{font-size:.78rem;color:{TS};margin:2px 0 9px;}}
.mc-row{{display:flex;justify-content:space-between;align-items:center;font-size:.76rem;color:{TD};margin-top:3px;}}
.mc-row strong{{font-family:'JetBrains Mono',monospace;font-weight:600;font-size:.76rem;}}
.hi-tr{{background:{HT};border-radius:99px;height:3px;width:100%;margin-top:5px;overflow:hidden;}}
.hi-fi{{height:100%;border-radius:99px;}}
.spill{{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:99px;font-size:.68rem;font-weight:700;letter-spacing:.8px;text-transform:uppercase;margin-top:7px;border:1px solid;}}
.sdot{{width:5px;height:5px;border-radius:50%;display:inline-block;}}
.sb-logo{{font-size:1.5rem;font-weight:800;color:{TP};padding:.3rem 0 .1rem;letter-spacing:-.5px;}}
.sb-logo span{{color:{TL};}}
.sb-tag{{font-size:.65rem;color:{TD};letter-spacing:2.5px;text-transform:uppercase;margin-bottom:.8rem;}}
.slbl{{font-size:.67rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};margin-bottom:.7rem;font-weight:600;font-family:'JetBrains Mono',monospace;}}
.mgmt-panel,.form-panel{{background:{CARD};border:1px solid {B};border-top:2px solid {TL};border-radius:20px;padding:1.8rem 2rem;margin-bottom:1.4rem;{BL}box-shadow:{CS};}}
.form-sec{{font-size:.67rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};font-weight:600;font-family:'JetBrains Mono',monospace;margin-bottom:.8rem;padding-bottom:.5rem;border-bottom:1px solid {B};}}
.gps-tip{{background:{'rgba(13,148,136,0.08)' if dk else 'rgba(13,148,136,0.06)'};border:1px solid {'rgba(13,148,136,0.25)' if dk else 'rgba(13,148,136,0.2)'};border-radius:10px;padding:.65rem 1rem;font-size:.8rem;color:{'#2dd4bf' if dk else '#0f766e'};margin-bottom:1rem;line-height:1.6;font-weight:500;}}
.mach-row{{background:{SF};border:1px solid {B};border-radius:14px;padding:1rem 1.2rem;margin-bottom:.6rem;border-left:3px solid;}}
div[data-testid="stNumberInput"] input,div[data-testid="stTextInput"] input{{background:{IB}!important;border:1px solid {BH}!important;color:{TP}!important;border-radius:10px!important;font-weight:500!important;}}
div[data-testid="stNumberInput"] label,div[data-testid="stTextInput"] label,div[data-testid="stSelectbox"] label{{font-size:.68rem!important;color:{TS}!important;font-weight:600!important;}}
div[data-testid="stSelectbox"]>div>div{{background:{IB}!important;border:1px solid {BH}!important;color:{TP}!important;border-radius:10px!important;}}
div[data-testid="stSelectbox"]>div>div>div{{color:{TP}!important;}}
.stButton>button{{background:{BB}!important;border:1px solid {BBD}!important;color:{BC}!important;font-family:'Sora',sans-serif!important;font-size:.73rem!important;font-weight:600!important;border-radius:11px!important;padding:.45rem 1.1rem!important;transition:all .2s!important;}}
.stButton>button:hover{{background:{BH2}!important;border-color:{TL}!important;}}
.footer{{font-family:'JetBrains Mono',monospace;font-size:.52rem;color:{TD};text-align:center;margin-top:2.5rem;letter-spacing:2px;text-transform:uppercase;padding-top:1.5rem;border-top:1px solid {DIV};}}
div[data-testid="stMetric"]{{display:none;}}
.leaflet-control-attribution{{display:none!important;}}
</style>
""", unsafe_allow_html=True)

# ══════════════════ HELPER FUNCTIONS ══════════════════

def make_hi_chart(hi_series, status_color):
    now = datetime.now()
    ts = [now - timedelta(hours=7 * 24 - i * 6) for i in range(len(hi_series))]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ts, y=hi_series, mode="lines",
        line=dict(color=status_color, width=2.5, shape="spline"),
        fill="tozeroy", fillcolor="rgba(13,148,136,0.07)",
        hovertemplate="HI: %{y:.2f}<extra></extra>",
    ))
    fig.add_hline(
        y=0.3, line_dash="dot", line_color="#f43f5e", line_width=1.5,
        annotation_text="0.30 — Urgence", annotation_font=dict(size=9, color="#f43f5e")
    )
    fig.add_hline(
        y=0.6, line_dash="dot", line_color="#f59e0b", line_width=1.5,
        annotation_text="0.60 — Surveillance", annotation_font=dict(size=9, color="#f59e0b")
    )
    fig.update_layout(
        height=210, margin=dict(t=20, b=20, l=36, r=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickfont=dict(size=9, color=PT), zeroline=False),
        yaxis=dict(range=[0, 1.05], showgrid=True, gridcolor=PG, tickfont=dict(size=9, color=PT), zeroline=False),
        showlegend=False,
    )
    return fig

def make_shap_chart(features, values):
    colors = ["#f43f5e" if v > 0.25 else ("#f59e0b" if v > 0.12 else TL) for v in values]
    fig = go.Figure(go.Bar(
        x=values, y=features, orientation='h',
        marker_color=colors,
        text=[f"{v:.3f}" for v in values],
        textposition="outside",
        textfont=dict(size=10, color=TD, family="JetBrains Mono"),
    ))
    fig.update_layout(
        height=260, margin=dict(t=8, b=8, l=8, r=55),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor=PG, tickfont=dict(size=9, color=PT), zeroline=False),
        yaxis=dict(tickfont=dict(size=10, color=TS), zeroline=False),
        showlegend=False,
    )
    return fig

def gen_hi(base, n=28):
    hi = min(base + 0.15, 1.0)
    out = []
    for _ in range(n):
        hi = max(0, min(1, hi - random.uniform(0.003, 0.007) + random.gauss(0, 0.004)))
        out.append(round(hi, 3))
    out[-1] = base
    return out

def gen_sensor(base, n=9, flat_noise=0.02, final_drop=0.0):
    out = []
    for _ in range(max(1, n - 3)):
        out.append(round(base + random.uniform(-flat_noise, flat_noise), 2))
    out.append(round(base, 2))
    out.append(round(base - final_drop * 0.5, 2))
    out.append(round(base - final_drop, 2))
    return out[:n]

def hex_to_rgba(hex_color, alpha=0.08):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

def make_simple_sensor_chart(values, title, y_max, line_color="#0d9488"):
    now = datetime.now()
    times = [now - timedelta(minutes=(len(values) - 1 - i) * 90) for i in range(len(values))]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times,
        y=values,
        mode="lines",
        line=dict(color=line_color, width=2.5),
        fill="tozeroy",
        fillcolor=hex_to_rgba(line_color, 0.08),
        hovertemplate="%{y:.1f}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center",
                   font=dict(size=13, color=TP, family="Sora")),
        height=190,
        margin=dict(t=36, b=20, l=35, r=15),
        paper_bgcolor=GAUGE_PANEL_BG,
        plot_bgcolor=GAUGE_PANEL_BG,
        showlegend=False,
        xaxis=dict(
            showgrid=True,
            gridcolor=GAUGE_PANEL_BORDER,
            zeroline=False,
            tickfont=dict(size=9, color=GAUGE_SUBTEXT),
            tickformat="%H:%M"
        ),
        yaxis=dict(
            range=[0, y_max],
            showgrid=True,
            gridcolor=GAUGE_PANEL_BORDER,
            zeroline=False,
            tickfont=dict(size=9, color=GAUGE_SUBTEXT),
        ),
    )
    return fig


def simple_gauge_card(value, max_val, title, unit, arc_color):
    value = max(0.0, min(float(value), float(max_val)))
    pct   = value / max_val

    vw, vh = 300, 180
    cx, cy = 150, 140
    R      = 110
    stroke = 20

    def pt(svg_angle_deg, r=R):
        a = math.radians(svg_angle_deg)
        return cx + r * math.cos(a), cy + r * math.sin(a)

    def arc_stroke(a_start, a_end, r=R):
        x1, y1 = pt(a_start, r)
        x2, y2 = pt(a_end,   r)
        diff = (a_end - a_start) % 360
        large = 1 if diff > 180 else 0
        return f"M{x1:.3f},{y1:.3f} A{r},{r} 0 {large},1 {x2:.3f},{y2:.3f}"

    track_path        = arc_stroke(180, 360)
    needle_svg_angle  = 180.0 + pct * 180.0
    value_path        = arc_stroke(180, needle_svg_angle) if pct > 0.005 else ""

    needle_len        = R - 14
    tip_x,  tip_y     = pt(needle_svg_angle, needle_len)
    back_x, back_y    = pt(needle_svg_angle + 180, 15)

    lx0, ly0 = pt(182, R + 20)
    lxm, lym = pt(358, R + 20)

    val_text = f"{value:.1f} {unit}"

    html = f"""<!DOCTYPE html>
<html><head>
<style>
  html,body{{margin:0;padding:0;background:{GAUGE_PANEL_BG};font-family:'Sora',Arial,sans-serif;}}
  .gwrap{{background:{GAUGE_PANEL_BG};padding:4px 4px 2px 4px;text-align:center;}}
  .gtitle{{font-size:12px;font-weight:700;color:{GAUGE_TEXT};letter-spacing:1.5px;text-transform:uppercase;margin-bottom:0;}}
  .gval{{font-family:'JetBrains Mono',monospace;font-size:21px;font-weight:700;color:{arc_color};margin-top:-10px;padding-bottom:2px;}}
</style>
</head><body>
<div class="gwrap">
  <div class="gtitle">{title}</div>
  <svg viewBox="0 0 {vw} {vh}" style="width:100%;display:block;overflow:visible;">
    <path d="{track_path}" fill="none" stroke="{GAUGE_TRACK}" stroke-width="{stroke}" stroke-linecap="butt"/>
    {f'<path d="{value_path}" fill="none" stroke="{arc_color}" stroke-width="{stroke}" stroke-linecap="butt"/>' if value_path else ''}
    <text x="{lx0:.1f}" y="{ly0:.1f}" text-anchor="middle" font-size="11" fill="{GAUGE_SUBTEXT}" font-family="JetBrains Mono,monospace">0</text>
    <text x="{lxm:.1f}" y="{lym:.1f}" text-anchor="middle" font-size="11" fill="{GAUGE_SUBTEXT}" font-family="JetBrains Mono,monospace">{int(max_val)}</text>
    <line x1="{cx}" y1="{cy}" x2="{tip_x:.2f}" y2="{tip_y:.2f}" stroke="rgba(0,0,0,0.12)" stroke-width="3.5" stroke-linecap="round" transform="translate(1.5,1.5)"/>
    <line x1="{cx}" y1="{cy}" x2="{back_x:.2f}" y2="{back_y:.2f}" stroke="{NEEDLE_COL}" stroke-width="2.5" stroke-linecap="round" opacity="0.35"/>
    <line x1="{cx}" y1="{cy}" x2="{tip_x:.2f}" y2="{tip_y:.2f}" stroke="{NEEDLE_COL}" stroke-width="2.5" stroke-linecap="round"/>
    <circle cx="{cx}" cy="{cy}" r="7" fill="{GAUGE_PANEL_BG}" stroke="{NEEDLE_COL}" stroke-width="2"/>
    <circle cx="{cx}" cy="{cy}" r="3.5" fill="{arc_color}"/>
  </svg>
  <div class="gval">{val_text}</div>
</div>
</body></html>"""
    return html


def gen_report(m, rtype, lang):
    period = ("hebdomadaire" if rtype == "weekly" else "mensuel") if lang == "FR" else ("weekly" if rtype == "weekly" else "monthly")
    s_txt = {
        "OK":("bon état de fonctionnement","good working condition"),
        "SURVEILLANCE":("sous surveillance active","under active monitoring"),
        "URGENCE":("état critique","critical condition")
    }[m["status"]]
    reco  = {
        "OK":("Aucune action requise. Contrôle dans 30 jours.","No action required. Check in 30 days."),
        "SURVEILLANCE":("Planifier une inspection dans les 7 jours.","Schedule inspection within 7 days."),
        "URGENCE":("ARRET PREVENTIF RECOMMANDE. Inspection immédiate.","PREVENTIVE SHUTDOWN RECOMMENDED. Immediate inspection.")
    }[m["status"]]

    if lang == "FR":
        return f"""RAPPORT DE MAINTENANCE {period.upper()} — {m['id']}
Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} [MODE DEMO]

SYNTHESE
Machine {m['id']} ({m['client']} — {m['city']}) : {s_txt[0]}
Indice de Santé : {int(m['hi']*100)}%  |  RUL : {m['rul']} ± {m['rul_ci']} jours

INDICATEURS
  Vibration RMS  : {m['vib_rms']:.1f} mm/s
  Courant moteur : {m['current']:.2f} A
  Température    : {m['temp']:.1f} °C
  Anomalies 24h  : {m['anomalies_24h']}
  Cycles         : {m['cycles_today']}

RECOMMANDATION
{reco[0]}

---
PrediTeq Pro · Aroteq © 2026"""
    else:
        return f"""MAINTENANCE {period.upper()} REPORT — {m['id']}
Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} [DEMO MODE]

SUMMARY
Machine {m['id']} ({m['client']} — {m['city']}) : {s_txt[1]}
Health Index: {int(m['hi']*100)}%  |  RUL: {m['rul']} ± {m['rul_ci']} days

INDICATORS
  Vibration RMS  : {m['vib_rms']:.1f} mm/s
  Motor current  : {m['current']:.2f} A
  Temperature    : {m['temp']:.1f} °C
  Anomalies 24h  : {m['anomalies_24h']}
  Cycles         : {m['cycles_today']}

RECOMMENDATION
{reco[1]}

---
PrediTeq Pro · Aroteq © 2026"""

# ══════════════════ SIDEBAR ══════════════════
with st.sidebar:
    st.markdown(
        f'<div class="sb-logo">Predi<span>Teq</span></div><div class="sb-tag">SuperAdmin · Aroteq</div>',
        unsafe_allow_html=True
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("EN" if st.session_state.lang == "FR" else "FR", key="lang_btn"):
            st.session_state.lang = "EN" if st.session_state.lang == "FR" else "FR"
            st.rerun()
    with c2:
        if st.button("Clair" if dk else "Sombre", key="mode_btn"):
            st.session_state.dark_mode = not dk
            st.rerun()

    st.markdown(f"<hr style='border:none;border-top:1px solid {DIV};margin:.9rem 0;'>", unsafe_allow_html=True)
    is_open = st.session_state.active_panel is not None
    if st.button(("Fermer " if is_open else "+ ") + t("manage_btn"), key="manage_btn"):
        st.session_state.active_panel = None if is_open else "list"
        st.session_state.edit_index = None
        st.rerun()

    st.markdown(f"<hr style='border:none;border-top:1px solid {DIV};margin:.9rem 0;'>", unsafe_allow_html=True)
    st.markdown(f'<div class="slbl">{t("machine_list")}</div>', unsafe_allow_html=True)

    DIV_VAR = DIV
    for m in st.session_state.machines:
        cfg = STATUS_CFG[m["status"]]
        hi_pct = int(m["hi"] * 100)
        sl = {"OK": t("ok_lbl"), "SURVEILLANCE": t("surv_lbl"), "URGENCE": t("urg_lbl")}
        sc = scol(cfg)
        st.markdown(f"""<div class="mc" style="border-left-color:{cfg['color']};">
            <div class="mc-id">{m['id']}</div><div class="mc-cli">{m['client']} · {m['city']}</div>
            <div class="mc-row"><span>{t('hi')}</span><strong style="color:{cfg['color']};">{hi_pct}%</strong></div>
            <div class="hi-tr"><div class="hi-fi" style="width:{hi_pct}%;background:{cfg['gradient']};"></div></div>
            <div class="mc-row" style="margin-top:5px;"><span>RUL</span><strong style="color:{cfg['color']};">{m['rul']} ± {m['rul_ci']} {t('days')}</strong></div>
            <span class="spill" style="background:{cfg['pill_bg']};color:{sc};border-color:{cfg['border']};"><span class="sdot" style="background:{cfg['dot']};"></span>{sl[m['status']]}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown(f"<hr style='border:none;border-top:1px solid {DIV_VAR};margin:.9rem 0;'>", unsafe_allow_html=True)

# ══════════════════ HEADER ══════════════════
MACHINES = st.session_state.machines
now_str = datetime.now().strftime('%d %b %Y &nbsp;&middot;&nbsp; %H:%M')
st.markdown(f"""<div class="plh">
  <div><div class="plh-logo">Predi<span>Teq</span></div><div class="plh-tag">{t('subtitle')}</div></div>
  <div class="plh-right"><div class="plh-badge">SUPERADMIN</div><div class="plh-time">{now_str}</div>
  <div style="font-size:.74rem;color:rgba(255,255,255,.95);font-weight:600;"><span class="online-dot"></span>{t('sys_active')}</div></div>
</div>""", unsafe_allow_html=True)

# ══════════════════ FORM HELPER ══════════════════
def machine_form(m=None, kp="form"):
    opts = get_opts()
    default_s = s_disp(m["status"]) if m else list(opts.keys())[0]

    st.markdown(f'<div class="form-sec">— {t("sec_info")}</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        fid = st.text_input(t("field_id"), value=m["id"] if m else "", key=f"{kp}_id")
    with c2:
        fcli = st.text_input(t("field_client"), value=m["client"] if m else "", key=f"{kp}_cli")
    with c3:
        fcity = st.text_input(t("field_city"), value=m["city"] if m else "", key=f"{kp}_city")

    c4, c5, c6 = st.columns(3)
    with c4:
        fmod = st.text_input(t("field_model"), value=m.get("model", "SITI FC100L1-4") if m else "SITI FC100L1-4", key=f"{kp}_model")
    with c5:
        ffl = st.number_input(t("field_floors"), value=int(m["floors"]) if m else 10, min_value=1, max_value=100, key=f"{kp}_floors")
    with c6:
        fsd = st.selectbox(t("field_status"), list(opts.keys()), index=list(opts.keys()).index(default_s), key=f"{kp}_status")
        fst = opts[fsd]

    st.markdown(f'<div class="form-sec" style="margin-top:1.2rem;">— {t("sec_gps")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="gps-tip">{t("gps_tip")}</div>', unsafe_allow_html=True)
    c7, c8 = st.columns(2)
    with c7:
        flat = st.number_input(t("field_lat"), value=float(m["lat"]) if m else 36.0, format="%.6f", step=0.0001, key=f"{kp}_lat")
    with c8:
        flon = st.number_input(t("field_lon"), value=float(m["lon"]) if m else 10.0, format="%.6f", step=0.0001, key=f"{kp}_lon")

    st.markdown(f'<div class="form-sec" style="margin-top:1.2rem;">— {t("sec_sensors")}</div>', unsafe_allow_html=True)
    s1, s2, s3, s4, s5 = st.columns(5)
    with s1:
        fhi = st.number_input(t("field_hi"), value=float(m["hi"]) if m else 0.80, min_value=0.0, max_value=1.0, step=0.01, format="%.2f", key=f"{kp}_hi")
    with s2:
        frul = st.number_input(t("field_rul"), value=int(m["rul"]) if m else 30, min_value=0, max_value=365, key=f"{kp}_rul")
    with s3:
        fci = st.number_input(t("field_ci"), value=int(m["rul_ci"]) if m else 3, min_value=0, max_value=30, key=f"{kp}_ci")
    with s4:
        fvib = st.number_input(t("field_vib"), value=float(m["vib_rms"]) if m else 1.5, step=0.1, format="%.1f", key=f"{kp}_vib")
    with s5:
        fcur = st.number_input(t("field_cur"), value=float(m["current"]) if m else 4.0, step=0.01, format="%.2f", key=f"{kp}_cur")

    t1, _ = st.columns([1, 3])
    with t1:
        ftmp = st.number_input(t("field_temp"), value=float(m["temp"]) if m else 25.0, step=0.1, format="%.1f", key=f"{kp}_temp")

    return {
        "id": fid.strip(), "client": fcli.strip(), "city": fcity.strip(),
        "lat": flat, "lon": flon, "hi": fhi, "rul": frul, "rul_ci": fci, "status": fst,
        "model": fmod.strip(), "floors": ffl, "vib_rms": fvib, "current": fcur, "temp": ftmp,
        "anomalies_24h": 0, "cycles_today": 80,
        "last_upd": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

# ══════════════════ MANAGEMENT PANELS ══════════════════
if st.session_state.active_panel == "list":
    st.markdown(f'<div class="mgmt-panel"><div style="font-size:1.1rem;font-weight:700;color:{TP};margin-bottom:4px;">+ {t("manage_title")}</div></div>', unsafe_allow_html=True)
    for i, m in enumerate(MACHINES):
        cfg = STATUS_CFG[m["status"]]
        hi_pct = int(m["hi"] * 100)
        sc = scol(cfg)
        sl = {"OK": t("ok_lbl"), "SURVEILLANCE": t("surv_lbl"), "URGENCE": t("urg_lbl")}

        ci, ch, ca = st.columns([4, 3, 2])
        with ci:
            st.markdown(f"""<div class="mach-row" style="border-left-color:{cfg['color']};">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div><div style="font-family:'JetBrains Mono',monospace;font-size:.96rem;font-weight:700;color:{TP};">{m['id']}</div>
                <div style="font-size:.84rem;color:{TS};">{m['client']}</div>
                <div style="font-size:.76rem;color:{TD};">{m['city']}</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:.7rem;color:{TD};">GPS {m['lat']:.4f}, {m['lon']:.4f}</div></div>
                <span class="spill" style="background:{cfg['pill_bg']};color:{sc};border-color:{cfg['border']};"><span class="sdot" style="background:{cfg['dot']};"></span>{sl[m['status']]}</span>
              </div></div>""", unsafe_allow_html=True)
        with ch:
            st.markdown(f"""<div style="background:{SF};border:1px solid {B};border-radius:14px;padding:1rem 1.2rem;">
              <div style="font-size:.67rem;color:{TD};letter-spacing:2px;text-transform:uppercase;font-family:'JetBrains Mono',monospace;margin-bottom:5px;font-weight:600;">{t('hi')}</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.6rem;font-weight:700;color:{cfg['color']};">{hi_pct}%</div>
              <div style="background:{HT};border-radius:99px;height:4px;margin-top:8px;overflow:hidden;">
                  <div style="width:{hi_pct}%;height:100%;background:{cfg['gradient']};border-radius:99px;"></div></div>
              <div style="font-size:.77rem;color:{TS};margin-top:6px;">RUL: {m['rul']} ± {m['rul_ci']} {t('days')}</div></div>""", unsafe_allow_html=True)
        with ca:
            st.markdown("<div style='height:.2rem;'></div>", unsafe_allow_html=True)
            if st.button(t("edit_mach"), key=f"edit_{i}"):
                st.session_state.active_panel = "edit"
                st.session_state.edit_index = i
                st.rerun()
            st.markdown("<div style='height:.3rem;'></div>", unsafe_allow_html=True)
            if st.button(t("del_mach"), key=f"del_{i}"):
                st.session_state[f"cdel_{i}"] = True
                st.rerun()
            if st.session_state.get(f"cdel_{i}", False):
                st.warning(t("confirm_del"))
                y, n_ = st.columns(2)
                with y:
                    if st.button("Oui", key=f"yes_{i}"):
                        st.session_state.machines.pop(i)
                        st.session_state[f"cdel_{i}"] = False
                        st.success(t("del_ok"))
                        st.rerun()
                with n_:
                    if st.button("Non", key=f"no_{i}"):
                        st.session_state[f"cdel_{i}"] = False
                        st.rerun()
        st.markdown(f"<hr style='border:none;border-top:1px solid {DIV};margin:.2rem 0;'>", unsafe_allow_html=True)

    a, c_, _ = st.columns([1.5, 1.2, 5])
    with a:
        if st.button(f"+ {t('add_mach')}", key="go_add"):
            st.session_state.active_panel = "add"
            st.rerun()
    with c_:
        if st.button(t("close"), key="close_list"):
            st.session_state.active_panel = None
            st.rerun()
    st.markdown(f"<hr style='border:none;border-top:1px solid {DIV};margin:.5rem 0 1.4rem;'>", unsafe_allow_html=True)

elif st.session_state.active_panel == "edit":
    idx = st.session_state.edit_index
    m = MACHINES[idx]
    st.markdown(f'<div class="form-panel"><div style="font-size:1.1rem;font-weight:700;color:{TP};margin-bottom:1rem;">{t("edit_mach")} — {m["id"]}</div></div>', unsafe_allow_html=True)
    res = machine_form(m=m, kp=f"edit_{idx}")
    cs, cc, _ = st.columns([1.2, 1.2, 5])
    with cs:
        if st.button(t("save"), key="save_edit"):
            if not res["id"]:
                st.error("ID requis.")
            else:
                st.session_state.machines[idx] = res
                st.session_state.active_panel = "list"
                st.session_state.edit_index = None
                st.success(t("saved_ok"))
                st.rerun()
    with cc:
        if st.button(t("cancel"), key="cancel_edit"):
            st.session_state.active_panel = "list"
            st.session_state.edit_index = None
            st.rerun()
    st.markdown(f"<hr style='border:none;border-top:1px solid {DIV};margin:.5rem 0 1.4rem;'>", unsafe_allow_html=True)

elif st.session_state.active_panel == "add":
    st.markdown(f'<div class="form-panel"><div style="font-size:1.1rem;font-weight:700;color:{TP};margin-bottom:1rem;">+ {t("add_mach")}</div></div>', unsafe_allow_html=True)
    res = machine_form(m=None, kp="add_new")
    cs, cc, _ = st.columns([1.2, 1.2, 5])
    with cs:
        if st.button(t("save"), key="save_add"):
            existing = [x["id"] for x in st.session_state.machines]
            if not res["id"]:
                st.error("ID requis.")
            elif res["id"] in existing:
                st.error(t("id_exists"))
            else:
                st.session_state.machines.append(res)
                st.session_state.active_panel = "list"
                st.success(t("add_ok"))
                st.rerun()
    with cc:
        if st.button(t("cancel"), key="cancel_add"):
            st.session_state.active_panel = "list"
            st.rerun()
    st.markdown(f"<hr style='border:none;border-top:1px solid {DIV};margin:.5rem 0 1.4rem;'>", unsafe_allow_html=True)

if not MACHINES:
    st.info(t("no_machines"))
    st.stop()

# ══════════════════ KPIs ══════════════════
n = len(MACHINES)
nok   = sum(1 for m in MACHINES if m["status"] == "OK")
nsurv = sum(1 for m in MACHINES if m["status"] == "SURVEILLANCE")
nurg  = sum(1 for m in MACHINES if m["status"] == "URGENCE")

st.markdown(f"""<div class="kpi-row">
  <div class="kc tot"><div class="kc-lbl" style="margin-bottom:.6rem;">{t('total')}</div><div class="kc-val">{n}</div>
    <div style="font-size:.78rem;color:{TD};margin-top:.5rem;font-family:'JetBrains Mono',monospace;">machines actives</div></div>
  <div class="kc ok_"><div class="kc-lbl" style="margin-bottom:.6rem;">{t('ok_pct')}</div><div class="kc-val">{round(nok/n*100)}%</div>
    <div style="background:{HT};border-radius:99px;height:3px;margin-top:.7rem;overflow:hidden;"><div style="width:{round(nok/n*100)}%;height:100%;background:linear-gradient(90deg,#0f766e,#0d9488);border-radius:99px;"></div></div>
    <div style="font-size:.78rem;color:{TD};margin-top:.4rem;font-family:'JetBrains Mono',monospace;">{nok} / {n}</div></div>
  <div class="kc sv_"><div class="kc-lbl" style="margin-bottom:.6rem;">{t('surv_pct')}</div><div class="kc-val">{round(nsurv/n*100)}%</div>
    <div style="background:{HT};border-radius:99px;height:3px;margin-top:.7rem;overflow:hidden;"><div style="width:{round(nsurv/n*100)}%;height:100%;background:linear-gradient(90deg,#d97706,#fbbf24);border-radius:99px;"></div></div>
    <div style="font-size:.78rem;color:{TD};margin-top:.4rem;font-family:'JetBrains Mono',monospace;">{nsurv} / {n}</div></div>
  <div class="kc ur_"><div class="kc-lbl" style="margin-bottom:.6rem;">{t('urg_pct')}</div><div class="kc-val">{round(nurg/n*100)}%</div>
    <div style="background:{HT};border-radius:99px;height:3px;margin-top:.7rem;overflow:hidden;"><div style="width:{round(nurg/n*100)}%;height:100%;background:linear-gradient(90deg,#be123c,#f43f5e);border-radius:99px;"></div></div>
    <div style="font-size:.78rem;color:{TD};margin-top:.4rem;font-family:'JetBrains Mono',monospace;">{nurg} / {n}</div></div>
</div>""", unsafe_allow_html=True)

avg_hi = round(sum(m["hi"] for m in MACHINES) / n * 100)
avg_rul = round(sum(m["rul"] for m in MACHINES) / n)
hic = "#0d9488" if avg_hi >= 60 else ("#f59e0b" if avg_hi >= 30 else "#f43f5e")
hil = t("ok_lbl") if avg_hi >= 60 else (t("surv_lbl") if avg_hi >= 30 else t("urg_lbl"))

st.markdown(f"""<div class="hs">
  <div><div class="hs-lbl">Santé globale du parc</div>
  <div style="font-size:.82rem;color:{TS};margin-top:3px;">RUL moyen · {avg_rul} {t('days')}</div></div>
  <div class="hs-track"><div class="hs-fill" style="width:{avg_hi}%;"></div></div>
  <div style="text-align:right;"><div class="hs-score" style="color:{hic};">{avg_hi}%</div>
  <div style="font-size:.7rem;color:{TD};margin-top:2px;font-family:'JetBrains Mono',monospace;letter-spacing:1px;text-transform:uppercase;">{hil}</div></div>
</div>""", unsafe_allow_html=True)

# ══════════════════ NAVBAR ══════════════════
TAB_KEYS   = ["map", "operator", "admin", "reports", "alerts"]
TAB_LABELS = [t("tab_map"), t("tab_op"), t("tab_adm"), t("tab_rep"), t("tab_alt")]
TAB_ICONS  = {"map": "🗺", "operator": "🛠", "admin": "✦", "reports": "≣", "alerts": "⚠"}

active = st.session_state.active_tab

nav_styles = ""
for key in TAB_KEYS:
    is_active = key == active
    if is_active:
        nav_styles += f"""
        div[data-testid="stHorizontalBlock"] div#navpill_{key} button {{
            background: {TL} !important;
            color: #ffffff !important;
            border: 1.5px solid {TL} !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 14px rgba(13,148,136,0.35) !important;
        }}"""
    else:
        nav_styles += f"""
        div[data-testid="stHorizontalBlock"] div#navpill_{key} button {{
            background: transparent !important;
            color: {TS} !important;
            border: 1.5px solid {B} !important;
            font-weight: 500 !important;
            box-shadow: none !important;
        }}
        div[data-testid="stHorizontalBlock"] div#navpill_{key} button:hover {{
            background: {BB} !important;
            color: {TL} !important;
            border-color: {BBD} !important;
        }}"""

st.markdown(f"""<style>
  {nav_styles}
  div[data-testid="stHorizontalBlock"]:has(div[id^="navpill_"]) {{
    display: flex !important;
    justify-content: center !important;
    background: {CARD} !important;
    border: 1px solid {B} !important;
    border-radius: 99px !important;
    padding: .35rem .45rem !important;
    box-shadow: {CS} !important;
    gap: .3rem !important;
    margin-bottom: 1.4rem !important;
  }}
  div[data-testid="stHorizontalBlock"]:has(div[id^="navpill_"]) > div {{
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 0 !important;
  }}
  div[data-testid="stHorizontalBlock"] div[id^="navpill_"] button {{
    border-radius: 99px !important;
    font-family: 'Sora', sans-serif !important;
    font-size: .83rem !important;
    padding: .5rem 1.3rem !important;
    width: auto !important;
    white-space: nowrap !important;
    transition: all .22s ease !important;
    letter-spacing: .2px !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
  }}
  div[data-testid="stHorizontalBlock"] div[id^="navpill_"] button p {{
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    margin: 0 !important;
  }}
  div[data-testid="stHorizontalBlock"] div[id^="navpill_"] button svg {{
    flex-shrink: 0 !important;
  }}
</style>""", unsafe_allow_html=True)

nav_cols = st.columns(len(TAB_KEYS))
for i, (key, label) in enumerate(zip(TAB_KEYS, TAB_LABELS)):
    with nav_cols[i]:
        st.markdown(f'<div id="navpill_{key}">', unsafe_allow_html=True)
        if st.button(f"{TAB_ICONS[key]} {label}", key=f"nav_{key}"):
            st.session_state.active_tab = key
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:.2rem;'></div>", unsafe_allow_html=True)

tab = st.session_state.active_tab

# ════════════════════════════════════════════
# TAB: MAP
# ════════════════════════════════════════════
if tab == "map":
    st.markdown(f"""<div style="background:{CARD};border:1px solid {B};border-radius:20px;padding:1.3rem;box-shadow:{CS};margin-bottom:1.1rem;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
        <div style="display:flex;align-items:center;gap:12px;">
          <div style="font-size:.67rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};font-family:'JetBrains Mono',monospace;font-weight:600;">— {t('map_title')}</div>
          <span style="background:{BB};border:1px solid {BBD};border-radius:99px;padding:2px 10px;font-size:.7rem;font-family:'JetBrains Mono',monospace;color:{TL};font-weight:700;">{n} sites</span>
        </div>
        <div style="font-size:.76rem;color:{TD};font-style:italic;">{t('click_hint')}</div>
      </div></div>""", unsafe_allow_html=True)

    if dk:
        m_map = folium.Map(location=[35.8, 9.8], zoom_start=7, tiles="CartoDB dark_matter", width="100%")
    else:
        m_map = folium.Map(location=[35.8, 9.8], zoom_start=7, tiles=None, width="100%")
        folium.TileLayer(
            tiles="https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
            attr="Google Maps", name="Google Maps", max_zoom=20,
            subdomains=["mt0", "mt1", "mt2", "mt3"]
        ).add_to(m_map)

    m_map.get_root().html.add_child(folium.Element(
        "<style>.leaflet-control-attribution{display:none!important;}.leaflet-control-zoom{border:none!important;border-radius:10px!important;overflow:hidden;}</style>"
    ))

    for machine in MACHINES:
        scfg = STATUS_CFG[machine["status"]]
        sl   = {"OK": t("ok_lbl"), "SURVEILLANCE": t("surv_lbl"), "URGENCE": t("urg_lbl")}
        hi_pct = int(machine["hi"] * 100)
        gmaps  = f"https://maps.google.com/?q={machine['lat']},{machine['lon']}"
        pbg = '#0d1f2d' if dk else '#fff'
        ptxt = '#f0fafa' if dk else '#0f172a'
        psub = '#4a6275' if dk else '#64748b'
        pgrid = 'rgba(255,255,255,0.04)' if dk else '#f8fafc'
        pbord = 'rgba(255,255,255,0.07)' if dk else '#e2e8f0'
        pdiv = 'rgba(255,255,255,0.06)' if dk else '#f1f5f9'

        popup_html = f"""<div style="font-family:system-ui,sans-serif;background:{pbg};color:{ptxt};border-radius:16px;overflow:hidden;min-width:268px;max-width:280px;box-shadow:0 12px 40px rgba(0,0,0,{'.65' if dk else '.14'});border:1px solid {pbord};">
          <div style="background:{scfg['gradient']};padding:14px 17px 12px;">
            <div style="font-size:15px;font-weight:700;color:#fff;">{machine['id']}</div>
            <div style="font-size:11px;color:rgba(255,255,255,.72);margin-top:3px;">{machine['client']} · {machine['city']}</div></div>
          <div style="padding:14px 17px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
              <span style="font-size:10px;color:{psub};font-weight:600;letter-spacing:1.5px;text-transform:uppercase;">{t('hi')}</span>
              <span style="font-family:monospace;font-size:14px;font-weight:700;color:{scfg['color']};">{hi_pct}%</span></div>
            <div style="background:{pgrid};border-radius:99px;height:4px;margin-bottom:13px;overflow:hidden;">
              <div style="width:{hi_pct}%;height:100%;background:{scfg['gradient']};border-radius:99px;"></div></div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:12px;">
              <div style="background:{pgrid};border:1px solid {pbord};border-radius:10px;padding:8px 10px;">
                <div style="font-size:8px;color:{psub};letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;font-weight:700;">RUL</div>
                <div style="font-family:monospace;font-size:13px;font-weight:700;color:{scfg['color']};">{machine['rul']} <span style="font-size:9px;opacity:.6;">± {machine['rul_ci']} {t('days')}</span></div></div>
              <div style="background:{pgrid};border:1px solid {pbord};border-radius:10px;padding:8px 10px;">
                <div style="font-size:8px;color:{psub};letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;font-weight:700;">{t('status_lbl')}</div>
                <div style="font-size:11px;font-weight:700;color:{scfg['color']};">{sl[machine['status']]}</div></div>
              <div style="background:{pgrid};border:1px solid {pbord};border-radius:10px;padding:8px 10px;">
                <div style="font-size:8px;color:{psub};letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;font-weight:700;">{t('vibration')}</div>
                <div style="font-family:monospace;font-size:12px;font-weight:600;">{machine['vib_rms']} <span style="font-size:9px;opacity:.6;">mm/s</span></div></div>
              <div style="background:{pgrid};border:1px solid {pbord};border-radius:10px;padding:8px 10px;">
                <div style="font-size:8px;color:{psub};letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;font-weight:700;">{t('current_lbl')}</div>
                <div style="font-family:monospace;font-size:12px;font-weight:600;">{machine['current']} <span style="font-size:9px;opacity:.6;">A</span></div></div>
            </div>
            <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
              <span style="font-size:11px;color:{psub};font-weight:600;">{t('temp_lbl')}</span>
              <span style="font-family:monospace;font-size:11px;font-weight:600;">{machine['temp']} °C</span></div>
            <div style="border-top:1px solid {pdiv};margin:9px 0;"></div>
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <span style="font-size:9px;color:{psub};">{t('last_upd')}: {machine['last_upd']}</span>
              <a href="{gmaps}" target="_blank" style="font-size:9.5px;color:{BC};text-decoration:none;font-weight:700;background:{BB};border:1px solid {BBD};border-radius:8px;padding:4px 11px;">{t('open_maps')}</a>
            </div></div></div>"""

        tooltip_html = f"<b style='font-family:monospace;font-size:12px;color:{scfg['color']};'>{machine['id']}</b><br><span style='font-size:10.5px;color:#64748b;'>{machine['city']} · HI {hi_pct}% · RUL {machine['rul']}j</span>"

        if machine["status"] == "URGENCE":
            folium.CircleMarker(
                location=[machine["lat"], machine["lon"]], radius=28,
                color="#f43f5e", fill=True, fill_color="#f43f5e",
                fill_opacity=0.06, weight=1.5, opacity=0.22
            ).add_to(m_map)

        folium.Marker(
            location=[machine["lat"], machine["lon"]],
            popup=folium.Popup(popup_html, max_width=290),
            tooltip=folium.Tooltip(tooltip_html, sticky=True),
            icon=folium.Icon(color=scfg["folium_color"], icon="industry", prefix="fa"),
        ).add_to(m_map)

    map_data = st_folium(m_map, width="100%", height=520, returned_objects=["last_object_clicked_popup"])

    if map_data and map_data.get("last_object_clicked_popup"):
        matched = next((m for m in MACHINES if m["id"] in str(map_data["last_object_clicked_popup"])), None)
        if matched:
            scfg = STATUS_CFG[matched["status"]]
            sl   = {"OK": t("ok_lbl"), "SURVEILLANCE": t("surv_lbl"), "URGENCE": t("urg_lbl")}
            hi_pct = int(matched["hi"] * 100)
            sc = scol(scfg)
            gmaps = f"https://maps.google.com/?q={matched['lat']},{matched['lon']}"

            st.markdown(f'<div class="slbl" style="margin-top:.4rem;">— {t("sel_mach")}</div>', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.markdown(f"""<div class="det" style="border-top:2px solid {scfg['color']};">
                    <div class="det-lbl">Machine</div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:1.1rem;font-weight:700;color:{TP};margin-bottom:6px;">{matched['id']}</div>
                    <div class="det-sub">{matched['model']}</div>
                    <div class="det-sub">{matched['client']} · {matched['city']}</div></div>""", unsafe_allow_html=True)

            with c2:
                st.markdown(f"""<div class="det" style="border-top:2px solid {scfg['color']};">
                    <div class="det-lbl">{t('hi')}</div>
                    <div class="det-val" style="color:{scfg['color']};">{hi_pct}<span style="font-size:1.1rem;opacity:.45;">%</span></div>
                    <div style="background:{HT};border-radius:99px;height:4px;margin-top:10px;overflow:hidden;"><div style="width:{hi_pct}%;height:100%;background:{scfg['gradient']};border-radius:99px;"></div></div>
                    <div class="det-sub" style="margin-top:9px;">{t('vibration')}: {matched['vib_rms']} mm/s</div>
                    <div class="det-sub">{t('temp_lbl')}: {matched['temp']} °C</div></div>""", unsafe_allow_html=True)

            with c3:
                st.markdown(f"""<div class="det" style="border-top:2px solid {scfg['color']};">
                    <div class="det-lbl">{t('rul_lbl')}</div>
                    <div class="det-val" style="color:{scfg['color']};">{matched['rul']}<span style="font-size:1rem;opacity:.45;"> {t('days')}</span></div>
                    <div class="det-dim">± {matched['rul_ci']} {t('days')}</div>
                    <div class="det-sub" style="margin-top:9px;">{t('current_lbl')}: {matched['current']} A</div></div>""", unsafe_allow_html=True)

            with c4:
                st.markdown(f"""<div class="det" style="border-top:2px solid {scfg['color']};">
                    <div class="det-lbl">{t('status_lbl')}</div>
                    <div style="margin-top:10px;"><span class="spill" style="background:{scfg['pill_bg']};color:{sc};border-color:{scfg['border']};font-size:.76rem;padding:6px 14px;"><span class="sdot" style="background:{scfg['dot']};"></span>{sl[matched['status']]}</span></div>
                    <div class="det-dim" style="margin-top:12px;">{t('last_upd')}</div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:.74rem;color:{TS};margin-top:3px;">{matched['last_upd']}</div>
                    <div style="margin-top:11px;"><a href="{gmaps}" target="_blank" style="font-size:.76rem;color:{BC};text-decoration:none;font-weight:700;border:1px solid {BBD};border-radius:8px;padding:5px 12px;background:{BB};">{t('open_maps')}</a></div></div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════
# TAB: OPERATOR
# ════════════════════════════════════════════
elif tab == "operator":
    ids = [m["id"] for m in MACHINES]
    if "op_sel_machine" not in st.session_state or st.session_state.op_sel_machine not in ids:
        st.session_state.op_sel_machine = ids[0]

    col_sel, _ = st.columns([2, 5])
    with col_sel:
        sel = st.selectbox(
            t("op_sel"),
            ids,
            index=ids.index(st.session_state.op_sel_machine),
            key="op_sel_box_v2"
        )
        st.session_state.op_sel_machine = sel

    m = next(x for x in MACHINES if x["id"] == sel)
    cfg = STATUS_CFG[m["status"]]
    sl = {"OK": t("ok_lbl"), "SURVEILLANCE": t("surv_lbl"), "URGENCE": t("urg_lbl")}
    hi_pct = int(m["hi"] * 100)

    st.markdown(f"""<div style="background:{cfg['gradient']};border-radius:16px;padding:1.2rem 1.6rem;margin-bottom:1.2rem;display:flex;align-items:center;justify-content:space-between;">
      <div><div style="font-size:1.4rem;font-weight:800;color:#fff;">{m['id']}</div>
      <div style="font-size:.85rem;color:rgba(255,255,255,.8);margin-top:3px;">{m['client']} · {m['city']}</div></div>
      <div style="text-align:right;">
        <span style="background:rgba(255,255,255,.2);border:1px solid rgba(255,255,255,.4);border-radius:99px;padding:5px 16px;font-size:.8rem;font-weight:700;color:#fff;">{sl[m['status']]}</span>
        <div style="font-size:.72rem;color:rgba(255,255,255,.7);margin-top:6px;">{t('last_upd')}: {m['last_upd']}</div>
      </div></div>""", unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="det" style="border-top:3px solid {cfg['color']};">
            <div class="det-lbl">{t('hi')}</div>
            <div class="det-val" style="color:{cfg['color']};">{hi_pct}<span style="font-size:1.2rem;opacity:.5;">%</span></div>
            <div style="background:{HT};border-radius:99px;height:5px;margin-top:10px;overflow:hidden;">
                <div style="width:{hi_pct}%;height:100%;background:{cfg['gradient']};border-radius:99px;"></div></div></div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="det" style="border-top:3px solid {cfg['color']};">
            <div class="det-lbl">{t('rul_lbl')}</div>
            <div class="det-val" style="color:{cfg['color']};">{m['rul']}<span style="font-size:1rem;opacity:.5;"> {t('days')}</span></div>
            <div class="det-dim">± {m['rul_ci']} {t('days')}</div></div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="det" style="border-top:3px solid {cfg['color']};">
            <div class="det-lbl">{t('op_cycles')}</div>
            <div class="det-val" style="color:{cfg['color']};">{m['cycles_today']}</div></div>""", unsafe_allow_html=True)
    with k4:
        ac = "#f43f5e" if m["anomalies_24h"] > 10 else "#f59e0b" if m["anomalies_24h"] > 3 else cfg["color"]
        st.markdown(f"""<div class="det" style="border-top:3px solid {ac};">
            <div class="det-lbl">{t('op_anom')}</div>
            <div class="det-val" style="color:{ac};">{m['anomalies_24h']}</div></div>""", unsafe_allow_html=True)

    st.markdown(
        f'<div style="margin-top:1.4rem;font-size:.67rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};margin-bottom:.8rem;font-weight:600;font-family:JetBrains Mono,monospace;">— {t("op_live")}</div>',
        unsafe_allow_html=True
    )

    vib_h  = gen_sensor(m["vib_rms"],  n=9, flat_noise=0.08, final_drop=0.20)
    cur_h  = gen_sensor(m["current"],  n=9, flat_noise=0.03, final_drop=0.10)
    temp_h = gen_sensor(m["temp"],     n=9, flat_noise=0.10, final_drop=4.50)

    col_v, col_c, col_t = st.columns(3)

    with col_v:
        st.plotly_chart(
            make_simple_sensor_chart(vib_h, t("vibration"), 15, line_color="#0d9488"),
            use_container_width=True, config={"displayModeBar": False}
        )
        components.html(
            simple_gauge_card(m["vib_rms"], 15, t("vibration"), "mm/s", arc_color="#0d9488"),
            height=220, scrolling=False
        )

    with col_c:
        st.plotly_chart(
            make_simple_sensor_chart(cur_h, t("current_lbl"), 10, line_color="#f59e0b"),
            use_container_width=True, config={"displayModeBar": False}
        )
        components.html(
            simple_gauge_card(m["current"], 10, t("current_lbl"), "A", arc_color="#f59e0b"),
            height=220, scrolling=False
        )

    with col_t:
        st.plotly_chart(
            make_simple_sensor_chart(temp_h, t("temp_lbl"), 100, line_color="#f43f5e"),
            use_container_width=True, config={"displayModeBar": False}
        )
        components.html(
            simple_gauge_card(m["temp"], 100, t("temp_lbl"), "°C", arc_color="#f43f5e"),
            height=220, scrolling=False
        )

    st.markdown(
        f'<div style="margin-top:.8rem;font-size:.67rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};margin-bottom:.7rem;font-weight:600;font-family:JetBrains Mono,monospace;">— {t("op_hi_trend")}</div>',
        unsafe_allow_html=True
    )
    st.plotly_chart(
        make_hi_chart(gen_hi(m["hi"]), cfg["color"]),
        use_container_width=True,
        config={"displayModeBar": False}
    )

# ════════════════════════════════════════════
# TAB: ADMIN
# ════════════════════════════════════════════
elif tab == "admin":
    ids = [m["id"] for m in MACHINES]
    if "adm_sel_machine" not in st.session_state or st.session_state.adm_sel_machine not in ids:
        st.session_state.adm_sel_machine = ids[0]

    col_sel, _ = st.columns([2, 5])
    with col_sel:
        sel = st.selectbox(t("op_sel"), ids, index=ids.index(st.session_state.adm_sel_machine), key="adm_sel_box_v2")
        st.session_state.adm_sel_machine = sel

    m = next(x for x in MACHINES if x["id"] == sel)
    cfg = STATUS_CFG[m["status"]]
    col_l, col_r = st.columns([1.2, 1])

    with col_l:
        st.markdown(f'<div style="background:{CARD};border:1px solid {B};border-radius:20px;padding:1.4rem 1.6rem;box-shadow:{CS};margin-bottom:1.1rem;"><div style="font-size:.67rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};font-family:JetBrains Mono,monospace;font-weight:600;margin-bottom:1rem;">— {t("adm_rep")}</div></div>', unsafe_allow_html=True)
        b1, b2, _ = st.columns([1.8, 1.8, 3])
        with b1:
            if st.button(t("adm_gen"), key="adm_gen_btn"):
                st.session_state.report_text = gen_report(m, "weekly", st.session_state.lang)
                st.rerun()
        with b2:
            if st.button(t("adm_pdf"), key="adm_pdf_btn"):
                st.toast("Export PDF — intégrer WeasyPrint / FPDF2")

        if st.session_state.report_text:
            st.markdown(
                f'<div style="background:{"rgba(13,148,136,0.06)" if dk else "rgba(13,148,136,0.04)"};border:1px solid {"rgba(13,148,136,0.2)" if dk else "rgba(13,148,136,0.15)"};border-radius:16px;padding:1.4rem 1.6rem;margin-top:.8rem;">'
                f'<pre style="white-space:pre-wrap;font-family:Sora,sans-serif;font-size:.84rem;margin:0;color:{TS};">{st.session_state.report_text}</pre></div>',
                unsafe_allow_html=True
            )

        st.markdown(f"<div style='height:.8rem;'></div>", unsafe_allow_html=True)

        SEV_COL = {"LOW":"#0d9488","MED":"#f59e0b","HIGH":"#f97316","CRIT":"#f43f5e"}
        feats   = ["RMS_mean","current_mean","temp_derivative","power_cycle","ratio_duree","hi_std","corr_T_P"]
        anom_count = min(m["anomalies_24h"], 7)
        anom_rows = ""

        if anom_count == 0:
            anom_rows = f'<div style="font-size:.82rem;color:{TD};padding:.5rem 0;">Aucune anomalie détectée dans les 24h.</div>'

        for i in range(anom_count):
            ts_a  = (datetime.now() - timedelta(hours=i * 3 + random.randint(0, 2))).strftime("%Y-%m-%d %H:%M")
            feat  = random.choice(feats)
            score = round(random.uniform(-0.35, -0.08), 3)
            sev   = random.choice(["HIGH","CRIT"] if m["status"] == "URGENCE" else ["MED","HIGH"] if m["status"] == "SURVEILLANCE" else ["LOW"])
            c_s   = SEV_COL[sev]
            anom_rows += f"""<div style="display:flex;justify-content:space-between;align-items:center;padding:.5rem .8rem;background:{SF};border:1px solid {B};border-left:3px solid {c_s};border-radius:10px;margin-bottom:.3rem;">
              <span style="font-family:'JetBrains Mono',monospace;font-size:.73rem;color:{TD};">{ts_a}</span>
              <span style="font-size:.77rem;color:{TS};">{feat}</span>
              <span style="font-family:'JetBrains Mono',monospace;font-size:.73rem;color:{c_s};">score={score}</span>
              <span style="background:{c_s}20;color:{c_s};border:1px solid {c_s}40;border-radius:6px;padding:1px 8px;font-size:.67rem;font-weight:700;">{sev}</span>
            </div>"""

        st.markdown(
            f'<div style="background:{CARD};border:1px solid {B};border-radius:20px;padding:1.4rem 1.6rem;box-shadow:{CS};">'
            f'<div style="font-size:.67rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};font-family:JetBrains Mono,monospace;font-weight:600;margin-bottom:1rem;">— {t("adm_anom")}</div>'
            f'{anom_rows}</div>', unsafe_allow_html=True
        )

    with col_r:
        st.markdown(f'<div style="background:{CARD};border:1px solid {B};border-radius:20px;padding:1.4rem 1.6rem;box-shadow:{CS};margin-bottom:1.1rem;"><div style="font-size:.67rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};font-family:JetBrains Mono,monospace;font-weight:600;margin-bottom:1rem;">— {t("adm_thresh")}</div></div>', unsafe_allow_html=True)
        tk = f"thr_{m['id']}"
        if tk not in st.session_state:
            st.session_state[tk] = {"hi_urg":0.30,"hi_surv":0.60,"rul_urg":7,"rul_surv":30}
        thr   = st.session_state[tk]
        hi_u  = st.slider(t("adm_hi_urg"), 0.10, 0.50, thr["hi_urg"], 0.01, key=f"{tk}_hiu", format="%.2f")
        hi_s  = st.slider("HI surveillance", 0.30, 0.80, thr["hi_surv"], 0.01, key=f"{tk}_his", format="%.2f")
        rul_u = st.slider("RUL urgence (j)", 1, 14, thr["rul_urg"], 1, key=f"{tk}_rulu")
        rul_s = st.slider("RUL surveillance (j)", 7, 60, thr["rul_surv"], 1, key=f"{tk}_ruls")
        st.markdown(f"""<div style="background:{SF};border:1px solid {B};border-radius:12px;padding:.8rem 1rem;margin:.8rem 0;font-size:.8rem;color:{TS};line-height:2;">
          <div><span style="color:#f43f5e;font-weight:700;">Urgence</span> — HI &lt; {hi_u:.2f} OU RUL &lt; {rul_u}j → email automatique</div>
          <div><span style="color:#f59e0b;font-weight:700;">Surveillance</span> — HI &lt; {hi_s:.2f} OU RUL &lt; {rul_s}j → email hebdomadaire</div>
          <div><span style="color:#0d9488;font-weight:700;">OK</span> — aucun email</div>
        </div>""", unsafe_allow_html=True)
        if st.button(t("adm_thresh"), key="save_thr"):
            st.session_state[tk] = {"hi_urg":hi_u,"hi_surv":hi_s,"rul_urg":rul_u,"rul_surv":rul_s}
            st.success("Seuils enregistrés.")

        st.markdown(f"<div style='height:.8rem;'></div>", unsafe_allow_html=True)
        shap_f = ["RMS_mean","current_mean","temp_deriv","power_cycle","ratio_duree","hi_std","corr_T_P","RMS_var","dRMS_dt","energy_cyc"]
        shap_v = sorted([round(random.uniform(0.01, 0.42), 3) for _ in shap_f], reverse=True)
        st.markdown(
            f'<div style="background:{CARD};border:1px solid {B};border-radius:20px;padding:1.4rem 1.6rem;box-shadow:{CS};">'
            f'<div style="font-size:.67rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};font-family:JetBrains Mono,monospace;font-weight:600;margin-bottom:.8rem;">— {t("adm_shap")}</div>',
            unsafe_allow_html=True
        )
        st.plotly_chart(make_shap_chart(shap_f[::-1], shap_v[::-1]), use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════
# TAB: AI REPORTS
# ════════════════════════════════════════════
elif tab == "reports":
    st.markdown(f'<div style="font-size:.67rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};font-family:JetBrains Mono,monospace;font-weight:600;margin-bottom:.8rem;">— Rapports IA — Grok API (xAI)</div>', unsafe_allow_html=True)
    ids_all = ["— Toutes les machines —"] + [m["id"] for m in MACHINES]
    cm, ct, cb, _ = st.columns([2, 1.5, 1.2, 3])

    with cm:
        rep_m = st.selectbox(t("op_sel"), ids_all, key="rep_m_sel")
    with ct:
        rep_t = st.selectbox("Type", [t("rep_weekly"), t("rep_monthly")], key="rep_t_sel")
    with cb:
        st.markdown("<div style='height:1.7rem;'></div>", unsafe_allow_html=True)
        if st.button(t("rep_gen"), key="rep_gen_btn"):
            rtype = "weekly" if t("rep_weekly") in rep_t else "monthly"
            if "—" in rep_m:
                st.session_state.report_text = "\n\n" + ("=" * 60 + "\n\n").join(gen_report(x, rtype, st.session_state.lang) for x in MACHINES)
            else:
                mx = next(x for x in MACHINES if x["id"] == rep_m)
                st.session_state.report_text = gen_report(mx, rtype, st.session_state.lang)
            st.rerun()

    if st.session_state.report_text:
        st.markdown(
            f'<div style="background:{"rgba(13,148,136,0.06)" if dk else "rgba(13,148,136,0.04)"};border:1px solid {"rgba(13,148,136,0.2)" if dk else "rgba(13,148,136,0.15)"};border-radius:16px;padding:1.4rem 1.6rem;margin-top:.8rem;">'
            f'<pre style="white-space:pre-wrap;font-family:Sora,sans-serif;font-size:.84rem;margin:0;color:{TS};">{st.session_state.report_text}</pre></div>',
            unsafe_allow_html=True
        )
        dl1, dl2, _ = st.columns([1.2, 1.2, 5])
        with dl1:
            if st.button("Effacer", key="clear_rep"):
                st.session_state.report_text = None
                st.rerun()
        with dl2:
            st.download_button(
                "Télécharger .txt",
                st.session_state.report_text,
                file_name=f"prediteq_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )

    st.markdown(f'<div style="height:.8rem;"></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:.67rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};font-family:JetBrains Mono,monospace;font-weight:600;margin-bottom:.6rem;margin-top:.4rem;">— Génération rapide par machine</div>', unsafe_allow_html=True)
    for mx in MACHINES:
        mc = STATUS_CFG[mx["status"]]
        cr, bw, bm = st.columns([4, 1, 1])
        with cr:
            st.markdown(f"""<div style="background:{SF};border:1px solid {B};border-left:3px solid {mc['color']};border-radius:12px;padding:.75rem 1.1rem;display:flex;align-items:center;justify-content:space-between;">
              <div><div style="font-family:'JetBrains Mono',monospace;font-size:.9rem;font-weight:700;color:{TP};">{mx['id']}</div>
              <div style="font-size:.78rem;color:{TS};">{mx['client']} · {mx['city']}</div></div>
              <span style="font-family:'JetBrains Mono',monospace;font-size:.9rem;font-weight:700;color:{mc['color']};">HI {int(mx['hi']*100)}% · RUL {mx['rul']}j</span></div>""", unsafe_allow_html=True)
        with bw:
            if st.button("Hebdo", key=f"rw_{mx['id']}"):
                st.session_state.report_text = gen_report(mx, "weekly", st.session_state.lang)
                st.rerun()
        with bm:
            if st.button("Mensuel", key=f"rm_{mx['id']}"):
                st.session_state.report_text = gen_report(mx, "monthly", st.session_state.lang)
                st.rerun()

# ════════════════════════════════════════════
# TAB: ALERTS
# ════════════════════════════════════════════
elif tab == "alerts":
    al, ar = st.columns([1.2, 1])

    with al:
        st.markdown(
            f'<div style="font-size:.67rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};font-family:JetBrains Mono,monospace;font-weight:600;margin-bottom:.6rem;">— {t("alt_title")}</div>'
            f'<div style="font-size:.84rem;color:{TS};margin-bottom:1rem;line-height:1.7;">{t("alt_desc")}</div>',
            unsafe_allow_html=True
        )
        boss = st.text_input(t("alt_boss"), value="saber.abeda@aro-teq.com", key="boss_email")
        admin_email = st.text_input(t("alt_admin"), value="firasabed007@gmail.com", key="admin_email")

        st.markdown(
            f'<div style="font-size:.67rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};font-family:JetBrains Mono,monospace;font-weight:600;margin:.8rem 0 .5rem;">— {t("alt_cond")}</div>'
            f'<div style="background:{SF};border:1px solid {B};border-radius:12px;padding:.9rem 1.1rem;font-size:.82rem;color:{TS};line-height:2.1;">'
            f'<div><span style="color:#f43f5e;font-weight:700;">Urgence</span> — HI &lt; 0.30 <strong>OU</strong> RUL &lt; 7j · email responsable + technicien · max 1×/24h</div>'
            f'<div><span style="color:#f59e0b;font-weight:700;">Surveillance</span> — 0.30 ≤ HI &lt; 0.60 <strong>OU</strong> 7j ≤ RUL &lt; 30j · email récapitulatif hebdomadaire</div>'
            f'<div><span style="color:#0d9488;font-weight:700;">OK</span> — HI ≥ 0.60 <strong>ET</strong> RUL ≥ 30j · aucun email</div></div>'
            f'<div style="font-size:.72rem;color:{TD};margin:.6rem 0 .5rem;">Envoi automatique par le pipeline ML · Gmail SMTP</div>',
            unsafe_allow_html=True
        )
        if st.button(t("alt_save"), key="save_alt"):
            st.success("Configuration enregistrée.")
        st.markdown("<div style='height:.7rem;'></div>", unsafe_allow_html=True)

        status_rows = ""
        for mx in MACHINES:
            mc = STATUS_CFG[mx["status"]]
            email_action = {"OK":"Aucun email","SURVEILLANCE":"Email hebdomadaire planifié","URGENCE":"Email envoyé — responsable + technicien"}[mx["status"]]
            status_rows += f"""<div style="display:flex;align-items:center;gap:.8rem;padding:.6rem .9rem;background:{SF};border:1px solid {B};border-left:3px solid {mc['color']};border-radius:10px;margin-bottom:.35rem;">
              <div style="flex:1;"><div style="font-family:'JetBrains Mono',monospace;font-size:.83rem;font-weight:700;color:{TP};">{mx['id']} <span style="font-weight:400;color:{TD};">— {mx['client']}</span></div>
              <div style="font-size:.76rem;color:{TS};">{email_action}</div></div>
              <span style="font-family:'JetBrains Mono',monospace;font-size:.78rem;color:{mc['color']};">HI {int(mx['hi']*100)}% · RUL {mx['rul']}j</span>
            </div>"""
        st.markdown(f'<div style="font-size:.67rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};font-family:JetBrains Mono,monospace;font-weight:600;margin-bottom:.5rem;">— Statut alerte actuel</div>{status_rows}', unsafe_allow_html=True)

    with ar:
        log = [
            {"ts":"2026-03-05 07:58","machine":"AscSITI-03","type":"URGENCE","msg":"HI=0.19 < 0.30 · RUL=4j · Déclenchement automatique pipeline ML"},
            {"ts":"2026-03-04 14:22","machine":"AscSITI-02","type":"SURVEILLANCE","msg":"HI=0.48 · RUL=18j · Email récapitulatif hebdomadaire"},
            {"ts":"2026-03-03 09:15","machine":"AscSITI-03","type":"URGENCE","msg":"HI=0.24 · RUL=6j · Déclenchement automatique pipeline ML"},
            {"ts":"2026-03-02 16:40","machine":"AscSITI-02","type":"SURVEILLANCE","msg":"RUL=22j · Seuil surveillance atteint"},
            {"ts":"2026-03-01 11:05","machine":"AscSITI-01","type":"OK","msg":"HI=0.85 · Aucune alerte"},
            {"ts":"2026-02-28 08:30","machine":"AscSITI-03","type":"URGENCE","msg":"HI=0.29 · Première alerte critique"},
        ]
        ALT_COLORS = {"URGENCE":"#f43f5e","SURVEILLANCE":"#f59e0b","OK":"#0d9488"}
        ALT_BG     = {"URGENCE":"rgba(244,63,94,.06)","SURVEILLANCE":"rgba(245,158,11,.05)","OK":"rgba(13,148,136,.04)"}
        ALT_BORDER = {"URGENCE":"rgba(244,63,94,.2)","SURVEILLANCE":"rgba(245,158,11,.18)","OK":"rgba(13,148,136,.15)"}
        log_rows = ""
        for row in log:
            c = ALT_COLORS[row["type"]]
            bg = ALT_BG[row["type"]]
            bd = ALT_BORDER[row["type"]]
            log_rows += f"""<div style="display:flex;align-items:flex-start;gap:.8rem;padding:.7rem 1rem;border-radius:10px;margin-bottom:.4rem;border:1px solid {bd};background:{bg};">
              <div style="flex:1;"><div style="display:flex;justify-content:space-between;">
                <span style="font-family:'JetBrains Mono',monospace;font-size:.8rem;font-weight:700;color:{c};">{row['machine']}</span>
                <span style="font-family:'JetBrains Mono',monospace;font-size:.72rem;color:{TD};">{row['ts']}</span></div>
                <div style="font-size:.78rem;color:{TS};margin-top:2px;">{row['msg']}</div></div></div>"""
        nu = sum(1 for r in log if r["type"] == "URGENCE")
        ns = sum(1 for r in log if r["type"] == "SURVEILLANCE")
        st.markdown(
            f'<div style="font-size:.67rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};font-family:JetBrains Mono,monospace;font-weight:600;margin-bottom:.5rem;">— {t("alt_log")}</div>'
            f'{log_rows}<div style="height:.8rem;"></div>'
            f'<div style="font-size:.67rem;letter-spacing:2.5px;text-transform:uppercase;color:{TD};font-family:JetBrains Mono,monospace;font-weight:600;margin-bottom:.5rem;">— Statistiques (30 derniers jours)</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:.8rem;">'
            f'<div style="background:{SF};border:1px solid {B};border-radius:12px;padding:.9rem;text-align:center;"><div style="font-family:JetBrains Mono,monospace;font-size:2rem;font-weight:700;color:#f43f5e;">{nu}</div><div style="font-size:.72rem;color:{TD};margin-top:3px;letter-spacing:1px;text-transform:uppercase;">Urgences</div></div>'
            f'<div style="background:{SF};border:1px solid {B};border-radius:12px;padding:.9rem;text-align:center;"><div style="font-family:JetBrains Mono,monospace;font-size:2rem;font-weight:700;color:#f59e0b;">{ns}</div><div style="font-size:.72rem;color:{TD};margin-top:3px;letter-spacing:1px;text-transform:uppercase;">Surveillances</div></div>'
            f'</div>', unsafe_allow_html=True
        )

# ── FOOTER ──
st.markdown(f"""<div class="footer">
  Aroteq © 2026 &nbsp;·&nbsp; PrediTeq Pro &nbsp;·&nbsp; Tous droits réservés
</div>""", unsafe_allow_html=True)


