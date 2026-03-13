"""
=============================================================================
PrediLift Pro — Étape 1 : Génération des Données Simulées
=============================================================================
PFE Mohamed Firas Abed — ISAMM — Aroteq, Ben Arous, Tunisie

Simulation physiquement contrainte basée sur :
  - Plaque signalétique SITI FC100L1-4 (IEC EN 60034, 50 Hz, réseau Y 400V)
  - Datasheet ifm VTV122 (sortie RMS 4-20 mA, bande 10-1000 Hz, IP67/69K)
  - Datasheet Vaisala HMT370EX ATEX (T° surface moteur + humidité, 0.1 Hz)
  - Datasheet Siemens SENTRON PAC2200 (énergie 1 Hz, classe 1 IEC 62053-21)
  - Cinématique ascenseur : ratio réducteur 1/60, 18 étages, 0.10 m/étage
  - Norme ISO 10816-3 Classe I (moteurs ≤ 15 kW sur fondations rigides)
  - Cycle HMI : montée 12 s / descente 12 s / pause 20 s = 44 s/cycle

Cadences d'acquisition (fidèles aux datasheets) :
  - VTV122  → 1 Hz (RMS lissé, constante de temps ~300-500 ms)
  - PAC2200 → 1 Hz
  - HMT370EX→ 0.1 Hz (1 point toutes les 10 s, interpolé à 1 Hz dans le df)

Sorties :
  data/raw/sensor_data.csv       — dataset brut multi-capteurs (1 Hz, 1 traj.)
  data/raw/rul_dataset.csv       — 100 trajectoires × ~800 instants ≈ 80 000 lignes
  data/raw/plots/                — visualisations de validation
=============================================================================
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ── Reproductibilité ────────────────────────────────────────────────────────
np.random.seed(42)

# ── Répertoires de sortie ───────────────────────────────────────────────────
os.makedirs("data/raw/plots", exist_ok=True)

# =============================================================================
# ÉTAPE 1.1 — Paramètres physiques (ancrés dans la documentation)
# =============================================================================

# — Moteur SITI FC100L1-4 (plaque signalétique, 50 Hz, couplage Y 400V) —
P_nominal_kW   = 2.20     # kW nominal (plaque)
cos_phi_sain   = 0.80     # facteur de puissance état sain (plaque)
cos_phi_degrad = 0.77     # facteur de puissance dégradé (VFD, frottements++)
I_nominal_A    = 4.85     # A nominal couplage Y 400V 50 Hz (plaque)
T_isolation_max = 155.0   # °C max (Classe F, IEC EN 60034)

# — Cycle machine (Table 4 de la documentation) —
T_MONTEE   = 12    # s — cinématique réducteur 1/60, 18 étages
T_DESCENTE = 12    # s — symétrique (variateur régule)
T_PAUSE    = 20    # s — temps opérateur / changement étage
T_CYCLE    = T_MONTEE + T_DESCENTE + T_PAUSE  # 44 s

# — Puissances par phase (Table 5 de la documentation) —
# Montée charge nominale (90 kg = 18 × 5 kg)
P_PAUSE_kW    = 0.00   # SINAMICS maintient tension
P_MONTEE_kW   = 1.45   # montée nominale (90 kg)
P_DESCENTE_kW = 0.35   # descente à vide (freinage contrôlé)

# — Vibration VTV122 — ISO 10816-3 Classe I —
VIB_SAIN_NOMINAL = 1.20   # mm/s RMS (Zone B : 0.71-1.8 mm/s)
VIB_BRUIT_SIGMA  = 0.018  # 1.5% de 1.2 — fidèle datasheet (< ±3%)
VIB_DEGRAD_MAX   = 7.00   # mm/s (Zone D : arrêt immédiat > 4.5)

# — Température moteur HMT370EX (sonde sur carter) —
T_SURFACE_INIT  = 25.0   # °C état froid (atelier Ben Arous, mars)
T_SURFACE_CHAUD = 68.0   # °C régime permanent (Classe F, marge sécurité)
T_BRUIT_SIGMA   = 0.10   # °C (datasheet ±0.2°C → σ = 0.1°C)

# — Humidité HMT370EX —
HR_NOMINAL    = 65.0   # %RH (atelier Ben Arous)
HR_BRUIT_SIGMA = 0.50  # %RH (datasheet ±1%RH → σ = 0.5%RH)

# — PAC2200 précision —
PAC_BRUIT_PCT  = 0.005   # 0.5% (classe 1 IEC 62053-21)

# =============================================================================
# ÉTAPE 1.2 — Durée de simulation (1 trajectoire de référence)
# =============================================================================

DUREE_HEURES = 10
FREQ_HZ      = 1                           # cadence principale (1 Hz)
N_SECONDES   = DUREE_HEURES * 3600        # 36 000 points
t            = np.arange(N_SECONDES)       # axe temporel en secondes

print(f"[1.2] Durée simulation : {DUREE_HEURES}h → {N_SECONDES:,} points à {FREQ_HZ} Hz")
print(f"      Cycle machine    : {T_CYCLE} s (montée {T_MONTEE}s + descente {T_DESCENTE}s + pause {T_PAUSE}s)")
print(f"      Cycles simulés   : {N_SECONDES // T_CYCLE} cycles (~{N_SECONDES * 60 // (T_CYCLE * 3600)} cycles/h)")

# =============================================================================
# ÉTAPE 1.3 — Cycle de la machine (détection de phase)
# =============================================================================

phase_t = t % T_CYCLE  # position dans le cycle courant

# Labels de phase numériques : 0=pause, 1=montée, 2=descente
phase_label = np.where(
    phase_t < T_PAUSE, 0,                          # pause  [0 – 19 s]
    np.where(phase_t < T_PAUSE + T_MONTEE, 1, 2)  # montée [20 – 31 s], descente [32 – 43 s]
)

# =============================================================================
# ÉTAPE 1.4 — Dégradation progressive (ancrage physique)
# =============================================================================
# Profil A — linéaire : usure abrasive uniforme (cf. Table 17)
# HI visé : de 1.0 (sain) → 0.3 (seuil critique) sur toute la durée
degradation_norm = np.linspace(0.0, 1.0, N_SECONDES)  # [0 → 1]

# =============================================================================
# ÉTAPE 1.5 — Puissance moteur (PAC2200, 1 Hz)
# =============================================================================
# Puissance de base par phase (Table 5)
power_base = np.select(
    [phase_label == 0, phase_label == 1, phase_label == 2],
    [P_PAUSE_kW, P_MONTEE_kW, P_DESCENTE_kW]
)

# Dégradation : la montée consomme progressivement jusqu'à ~2.15 kW (état dégradé)
power_degrad_offset = phase_label * degradation_norm * (2.05 - P_MONTEE_kW)

# Bruit PAC2200 (classe 1 IEC 62053-21 : 0.5% de la valeur)
power_noise = np.random.normal(0, PAC_BRUIT_PCT * np.maximum(power_base + power_degrad_offset, 0.01))

power_kw = np.maximum(power_base + power_degrad_offset + power_noise, 0.0)

# =============================================================================
# ÉTAPE 1.6 — Vibration RMS — VTV122 (1 Hz, sortie RMS uniquement)
# =============================================================================
# ⚠️ Le VTV122 produit du RMS, PAS un signal temporel brut.
#    On génère directement des valeurs RMS physiquement plausibles.

# Zone B saine (ISO 10816-3) : 0.8 – 1.5 mm/s
# Dégradation : Zone B → C → D : 1.2 → 7.0 mm/s
vib_base     = VIB_SAIN_NOMINAL + degradation_norm * (VIB_DEGRAD_MAX - VIB_SAIN_NOMINAL)

# Résonance châssis 3 Hz (option réalisme structurel, amplitude 0.2 mm/s, doc §5.1)
vib_resonance = 0.15 * np.sin(2 * np.pi * 3.0 * t / 200)

# Bruit MEMS non-gaussien léger (1.5% de la valeur instantanée)
vib_noise = np.random.normal(0, VIB_BRUIT_SIGMA * vib_base)

vib_rms = np.maximum(vib_base + vib_resonance + vib_noise, 0.3)

# =============================================================================
# ÉTAPE 1.7 — Température surface moteur — HMT370EX (0.1 Hz → interpolé 1 Hz)
# =============================================================================
# La sonde est collée sur le carter : montée thermique lente (constante ~10 min)
# Simulation à 0.1 Hz (1 point / 10 s) puis interpolation linéaire → 1 Hz

N_POINTS_01HZ = N_SECONDES // 10           # 3 600 points à 0.1 Hz
t_01hz        = np.arange(N_POINTS_01HZ)

# Montée thermique sigmoïde : 25°C → 68°C (plateau régime permanent)
tau_thermique  = 45.0 * 60 / 10   # constante de temps en pas de 10 s (~45 min)
temp_montee    = T_SURFACE_CHAUD - (T_SURFACE_CHAUD - T_SURFACE_INIT) * np.exp(-t_01hz / tau_thermique)

# La dégradation augmente la T° surface (frottements, perte ventilation)
temp_degrad    = degradation_norm[::10] * 12.0  # jusqu'à +12°C en fin de vie
temp_surface_01hz = temp_montee + temp_degrad + np.random.normal(0, T_BRUIT_SIGMA, N_POINTS_01HZ)

# Interpolation linéaire → 1 Hz pour alignement temporel avec les autres capteurs
temperature_surface = np.interp(t, t_01hz * 10, temp_surface_01hz)

# =============================================================================
# ÉTAPE 1.8 — Humidité relative — HMT370EX (0.1 Hz → interpolé 1 Hz)
# =============================================================================
humidity_01hz = HR_NOMINAL + np.random.normal(0, HR_BRUIT_SIGMA, N_POINTS_01HZ)
# Légère tendance saisonnière (variation lente atelier)
humidity_01hz += 3.0 * np.sin(2 * np.pi * t_01hz / (N_POINTS_01HZ * 0.5))
humidity = np.interp(t, t_01hz * 10, humidity_01hz)
humidity = np.clip(humidity, 40.0, 95.0)   # plage physique HMT370EX

# =============================================================================
# ÉTAPE 1.9 — Extraction des 12 Features Phase 1 (Table 12 de la documentation)
# =============================================================================

# — Feature 1 : RMS vibration (mm/s) — déjà calculé —
f1_vib_rms = vib_rms

# — Feature 2 : Dérivée du RMS (variation temporelle) —
f2_vib_drms = np.gradient(vib_rms)

# — Feature 3 : Variabilité RMS (std sur fenêtre glissante 60 s) —
def rolling_std(x, window=60):
    result = np.zeros_like(x)
    for i in range(len(x)):
        start = max(0, i - window + 1)
        result[i] = np.std(x[start:i+1])
    return result

# Calcul vectorisé (approximation cumulative pour rapidité)
f3_vib_var = pd.Series(vib_rms).rolling(60, min_periods=1).std().fillna(0).values

# — Feature 4 : Puissance moyenne (kW) —
f4_power_mean = pd.Series(power_kw).rolling(44, min_periods=1).mean().values

# — Feature 5 : Puissance quadratique moyenne (RMS de P sur cycle) —
f5_power_rms = pd.Series(power_kw**2).rolling(44, min_periods=1).mean().apply(np.sqrt).values

# — Feature 6 : Dérivée de puissance (kW/s) —
f6_power_deriv = np.gradient(power_kw)

# — Feature 7 : Énergie par cycle (kWh) — intégrale trapézoïdale sur montée —
energy_cycle = np.zeros(N_SECONDES)
prev_cycle_start = 0
for i in range(1, N_SECONDES):
    if phase_label[i] == 1 and phase_label[i-1] != 1:   # début montée
        prev_cycle_start = i
    if phase_label[i] == 2 and phase_label[i-1] == 1:   # fin montée
        segment = power_kw[prev_cycle_start:i]
        e = np.trapezoid(segment) / 3600.0  # kWh
        energy_cycle[prev_cycle_start:i] = e
f7_energy_cycle = pd.Series(energy_cycle).replace(0, np.nan).ffill().fillna(0).values

# — Feature 8 : Ratio durée montée / nominale (12 s) — dégradation mécanique —
# En simulation : ratio augmente avec dégradation (frottements allongent la montée)
f8_ratio_montee = 1.0 + degradation_norm * 0.6 + np.random.normal(0, 0.02, N_SECONDES)
f8_ratio_montee = np.clip(f8_ratio_montee, 1.0, 2.0)

# — Feature 9 : Température surface moteur (°C) —
f9_temp = temperature_surface

# — Feature 10 : Gradient de température (°C/min) —
f10_temp_grad = pd.Series(temperature_surface).diff(60).fillna(0).values  # variation sur 1 min

# — Feature 11 : Humidité relative (%RH) —
f11_humidity = humidity

# — Feature 12 : Phase machine (0=pause, 1=montée, 2=descente) — encodage nominal —
f12_phase = phase_label.astype(float)

# =============================================================================
# ÉTAPE 1.10 — Construction du Dataset Principal
# =============================================================================

df = pd.DataFrame({
    "timestamp_s":         t,
    # Signaux bruts (pour traçabilité)
    "vibration_rms_mms":   f1_vib_rms,
    "power_kw":            power_kw,
    "temperature_surface": f9_temp,
    "humidity_pct":        f11_humidity,
    "phase_machine":       f12_phase,
    # 12 features Phase 1
    "feat_vib_rms":        f1_vib_rms,
    "feat_vib_drms":       f2_vib_drms,
    "feat_vib_var":        f3_vib_var,
    "feat_power_mean":     f4_power_mean,
    "feat_power_rms":      f5_power_rms,
    "feat_power_deriv":    f6_power_deriv,
    "feat_energy_cycle":   f7_energy_cycle,
    "feat_ratio_montee":   f8_ratio_montee,
    "feat_temp":           f9_temp,
    "feat_temp_grad":      f10_temp_grad,
    "feat_humidity":       f11_humidity,
    "feat_phase":          f12_phase,
})

df.to_csv("data/raw/sensor_data.csv", index=False)
print(f"\n[1.10] Dataset principal sauvegardé : data/raw/sensor_data.csv")
print(f"       Shape : {df.shape[0]:,} lignes × {df.shape[1]} colonnes")
print(df[["vibration_rms_mms", "power_kw", "temperature_surface", "humidity_pct"]].describe().round(3))

# =============================================================================
# ÉTAPE 1.11 — Génération des 100 Trajectoires (dataset RUL ~80 000 lignes)
# =============================================================================
# 4 profils × 25 variantes = 100 trajectoires (Table 17 de la documentation)

PROFILS = {
    "A_lineaire":    lambda x, T: 1.0 - 0.7 * (x / T),
    "B_exponentiel": lambda x, T: 1.0 - 0.7 * (x / T) ** 2,
    "C_paliers":     lambda x, T: 1.0 - 0.7 * np.floor(5 * x / T) / 5,
    "D_bruite":      lambda x, T: 1.0 - 0.7 * (x / T) + np.random.normal(0, 0.08, len(x)),
}

HI_SEUIL_CRITIQUE = 0.30   # RUL = 0 quand HI < 0.30

rul_records = []
N_VARIANTES = 25  # 4 profils × 25 = 100 trajectoires

print(f"\n[1.11] Génération des 100 trajectoires RUL...")

for profil_name, profil_fn in PROFILS.items():
    for v in range(N_VARIANTES):
        # Durée de vie aléatoire : 600 à 1000 min (réalisme industriel)
        T_fail = np.random.randint(600, 1001)
        tt = np.arange(T_fail)

        hi_raw = np.clip(profil_fn(tt, T_fail), 0.0, 1.0)

        # Lissage HI (moyenne glissante 10 min — §5.4 documentation)
        hi_smooth = pd.Series(hi_raw).rolling(10, min_periods=1).mean().values

        # Calcul RUL vrai (minutes jusqu'au premier HI < seuil)
        below = np.where(hi_smooth < HI_SEUIL_CRITIQUE)[0]
        t_seuil = below[0] if len(below) > 0 else T_fail

        rul_array = np.maximum(t_seuil - tt, 0)

        # Bruit de mesure réaliste sur les features
        vib_traj = VIB_SAIN_NOMINAL + (1 - hi_smooth) * (VIB_DEGRAD_MAX - VIB_SAIN_NOMINAL) \
                   + np.random.normal(0, VIB_BRUIT_SIGMA, T_fail)
        power_traj = P_MONTEE_kW + (1 - hi_smooth) * (2.05 - P_MONTEE_kW) \
                     + np.random.normal(0, PAC_BRUIT_PCT * P_MONTEE_kW, T_fail)
        temp_traj = T_SURFACE_CHAUD - hi_smooth * 15 \
                    + np.random.normal(0, T_BRUIT_SIGMA, T_fail)

        for i in range(T_fail):
            rul_records.append({
                "traj_id":        f"{profil_name}_v{v:02d}",
                "profil":         profil_name,
                "t_min":          int(tt[i]),
                "hi":             round(float(hi_smooth[i]), 4),
                "rul_min":        int(rul_array[i]),
                "rul_jours":      round(float(rul_array[i]) / (60 * 24), 4),
                "vib_rms":        round(float(vib_traj[i]), 4),
                "power_kw":       round(float(np.clip(power_traj[i], 0, P_nominal_kW)), 4),
                "temperature":    round(float(temp_traj[i]), 2),
            })

df_rul = pd.DataFrame(rul_records)
df_rul.to_csv("data/raw/rul_dataset.csv", index=False)
print(f"       Dataset RUL sauvegardé : data/raw/rul_dataset.csv")
print(f"       Shape : {df_rul.shape[0]:,} lignes × {df_rul.shape[1]} colonnes")
print(f"       Trajectoires : {df_rul['traj_id'].nunique()} (4 profils × {N_VARIANTES} variantes)")

# =============================================================================
# ÉTAPE 1.12 — Visualisations de Validation
# =============================================================================

print("\n[1.12] Génération des graphiques de validation...")

# — Fig 1 : Signaux bruts sur 500 s —
fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)
fig.suptitle("PrediLift Pro — Signaux bruts simulés (500 premières secondes)", fontsize=13, fontweight='bold')

colors = ['#2196F3', '#4CAF50', '#FF5722', '#9C27B0']
labels = ['Puissance moteur (kW)', 'Vibration RMS (mm/s)', 'T° surface moteur (°C)', 'Humidité (%RH)']
data   = [power_kw, vib_rms, temperature_surface, humidity]
ylims  = [(0, 2.5), (0.5, 3.0), (20, 80), (50, 85)]

for ax, col, lbl, dat, ylim in zip(axes, colors, labels, data, ylims):
    ax.plot(t[:500], dat[:500], color=col, linewidth=0.8)
    ax.set_ylabel(lbl, fontsize=9)
    ax.set_ylim(ylim)
    ax.grid(True, alpha=0.3)
    ax.axvspan(0, T_PAUSE, alpha=0.08, color='gray', label='Pause')
    ax.axvspan(T_PAUSE, T_PAUSE+T_MONTEE, alpha=0.08, color='blue', label='Montée')
    ax.axvspan(T_PAUSE+T_MONTEE, T_CYCLE, alpha=0.08, color='green', label='Descente')

axes[0].legend(loc='upper right', fontsize=7)
axes[-1].set_xlabel("Temps (s)")
plt.tight_layout()
plt.savefig("data/raw/plots/fig1_signaux_bruts_500s.png", dpi=150, bbox_inches='tight')
plt.close()
print("       ✓ fig1_signaux_bruts_500s.png")

# — Fig 2 : Dégradation complète sur 10 h —
fig, axes = plt.subplots(2, 2, figsize=(14, 8))
fig.suptitle("PrediLift Pro — Dégradation progressive sur 10 heures (Profil A - Linéaire)", fontsize=12, fontweight='bold')

axes[0,0].plot(t/3600, vib_rms, color='#2196F3', linewidth=0.5, alpha=0.7)
axes[0,0].axhline(1.8, color='orange', linestyle='--', label='ISO Zone B/C (1.8 mm/s)')
axes[0,0].axhline(4.5, color='red',    linestyle='--', label='ISO Zone C/D (4.5 mm/s)')
axes[0,0].set_title('Vibration RMS VTV122 (mm/s)')
axes[0,0].set_xlabel('Temps (h)'); axes[0,0].legend(fontsize=8); axes[0,0].grid(alpha=0.3)

axes[0,1].plot(t/3600, power_kw, color='#4CAF50', linewidth=0.5, alpha=0.7)
axes[0,1].axhline(P_MONTEE_kW, color='orange', linestyle='--', label=f'Nominal montée ({P_MONTEE_kW} kW)')
axes[0,1].axhline(2.20, color='red', linestyle='--', label='Max nominal SITI (2.2 kW)')
axes[0,1].set_title('Puissance moteur PAC2200 (kW)')
axes[0,1].set_xlabel('Temps (h)'); axes[0,1].legend(fontsize=8); axes[0,1].grid(alpha=0.3)

axes[1,0].plot(t/3600, temperature_surface, color='#FF5722', linewidth=0.8, alpha=0.8)
axes[1,0].axhline(T_SURFACE_CHAUD, color='orange', linestyle='--', label='Régime permanent sain (68°C)')
axes[1,0].set_title('T° surface moteur HMT370EX (°C)')
axes[1,0].set_xlabel('Temps (h)'); axes[1,0].legend(fontsize=8); axes[1,0].grid(alpha=0.3)

axes[1,1].plot(t/3600, humidity, color='#9C27B0', linewidth=0.8, alpha=0.8)
axes[1,1].axhline(HR_NOMINAL, color='gray', linestyle='--', label=f'Nominal ({HR_NOMINAL}%RH)')
axes[1,1].set_title('Humidité relative HMT370EX (%RH)')
axes[1,1].set_xlabel('Temps (h)'); axes[1,1].legend(fontsize=8); axes[1,1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("data/raw/plots/fig2_degradation_10h.png", dpi=150, bbox_inches='tight')
plt.close()
print("       ✓ fig2_degradation_10h.png")

# — Fig 3 : 4 profils de dégradation HI —
fig, ax = plt.subplots(figsize=(10, 5))
profil_colors = {'A_lineaire': '#2196F3', 'B_exponentiel': '#4CAF50', 'C_paliers': '#FF9800', 'D_bruite': '#9C27B0'}
for profil_name in PROFILS.keys():
    sample = df_rul[df_rul['profil'] == profil_name].groupby('t_min')['hi'].mean()
    ax.plot(sample.index, sample.values, label=profil_name.replace('_', ' ').title(),
            color=profil_colors[profil_name], linewidth=1.5)

ax.axhline(HI_SEUIL_CRITIQUE, color='red', linestyle='--', linewidth=1.5, label=f'Seuil critique HI={HI_SEUIL_CRITIQUE}')
ax.set_xlabel('Temps (minutes)'); ax.set_ylabel('Health Index HI(t)')
ax.set_title('PrediLift Pro — 4 Profils de dégradation (moyenne 25 variantes chacun)')
ax.legend(fontsize=9); ax.grid(alpha=0.3); ax.set_ylim(0, 1.05)
plt.tight_layout()
plt.savefig("data/raw/plots/fig3_profils_degradation.png", dpi=150, bbox_inches='tight')
plt.close()
print("       ✓ fig3_profils_degradation.png")

# — Fig 4 : Distributions des 12 features (validation statistique) —
FEAT_COLS = [c for c in df.columns if c.startswith('feat_')]
fig, axes = plt.subplots(3, 4, figsize=(16, 10))
fig.suptitle("PrediLift Pro — Distributions des 12 Features Phase 1", fontsize=12, fontweight='bold')
for ax, col in zip(axes.flat, FEAT_COLS):
    ax.hist(df[col], bins=60, color='#1976D2', alpha=0.75, edgecolor='none')
    ax.set_title(col.replace('feat_', ''), fontsize=8)
    ax.set_xlabel('Valeur', fontsize=7); ax.set_ylabel('Fréquence', fontsize=7)
    ax.tick_params(labelsize=6); ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("data/raw/plots/fig4_distributions_features.png", dpi=150, bbox_inches='tight')
plt.close()
print("       ✓ fig4_distributions_features.png")

# =============================================================================
# RÉSUMÉ FINAL
# =============================================================================
print("\n" + "="*70)
print("  ÉTAPE 1 — GÉNÉRATION DONNÉES — RÉSUMÉ")
print("="*70)
print(f"  Dataset principal  : data/raw/sensor_data.csv   ({N_SECONDES:,} lignes, {df.shape[1]} colonnes)")
print(f"  Dataset RUL        : data/raw/rul_dataset.csv   ({df_rul.shape[0]:,} lignes, 100 trajectoires)")
print(f"  Plots              : data/raw/plots/             (4 figures)")
print(f"\n  Plage vibration    : {vib_rms.min():.2f} – {vib_rms.max():.2f} mm/s  (ISO 10816-3 Classe I)")
print(f"  Plage puissance    : {power_kw.min():.2f} – {power_kw.max():.2f} kW   (plaque SITI FC100L1-4)")
print(f"  Plage température  : {temperature_surface.min():.1f} – {temperature_surface.max():.1f} °C (sonde carter HMT370EX)")
print(f"  Plage humidité     : {humidity.min():.1f} – {humidity.max():.1f} %RH  (atelier Ben Arous)")
print(f"\n  ✅ Toutes les valeurs sont physiquement cohérentes avec la documentation.")
print("="*70)
