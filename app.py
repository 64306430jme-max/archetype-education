import io
import re
import textwrap
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

st.set_page_config(
    page_title="Archétype Éducation — Pilotage & Audit | Cabinet QUINZE",
    page_icon="🎓",
    layout="wide"
)

# ==========================================
# RÉFÉRENTIEL & NORMES (ANC 2018-06)
# ==========================================
def get_normes_etablissement(type_etab):
    if "1er degré" in type_etab:
        return {"type_court": "1er degré", "financeur_principal": "Commune (Forfait communal)", "forfait_ref_eleve": 880, "contrib_ref_eleve": 420, "taux_caf_cible": 6.5, "jours_treso_cible": 90, "poids_ms_cible": 48.0, "poids_fluides_cible": 18.0, "taux_internat_ref": 0, "budget_pedago_cible": 70}
    elif "Collège" in type_etab:
        return {"type_court": "Collège", "financeur_principal": "Département (Forfait externat)", "forfait_ref_eleve": 647, "contrib_ref_eleve": 580, "taux_caf_cible": 7.5, "jours_treso_cible": 90, "poids_ms_cible": 44.0, "poids_fluides_cible": 19.0, "taux_internat_ref": 5, "budget_pedago_cible": 100}
    elif "Lycée GT" in type_etab:
        return {"type_court": "Lycée GT/Pro", "financeur_principal": "Région (Forfait externat)", "forfait_ref_eleve": 803, "contrib_ref_eleve": 690, "taux_caf_cible": 8.0, "jours_treso_cible": 90, "poids_ms_cible": 42.0, "poids_fluides_cible": 20.0, "taux_internat_ref": 12, "budget_pedago_cible": 130}
    elif "Agricole" in type_etab:
        return {"type_court": "Lycée Agricole", "financeur_principal": "MASA & Région", "forfait_ref_eleve": 2450, "contrib_ref_eleve": 720, "taux_caf_cible": 8.5, "jours_treso_cible": 75, "poids_ms_cible": 46.0, "poids_fluides_cible": 26.0, "taux_internat_ref": 65, "budget_pedago_cible": 150}
    elif "Maison Familiale" in type_etab:
        return {"type_court": "MFR / Alternance", "financeur_principal": "MASA & OPCO", "forfait_ref_eleve": 4100, "contrib_ref_eleve": 680, "taux_caf_cible": 8.0, "jours_treso_cible": 75, "poids_ms_cible": 64.0, "poids_fluides_cible": 22.0, "taux_internat_ref": 75, "budget_pedago_cible": 150}
    else:
        return {"type_court": "Ensemble mixte", "financeur_principal": "Commune + Dept + Région", "forfait_ref_eleve": 760, "contrib_ref_eleve": 560, "taux_caf_cible": 7.5, "jours_treso_cible": 90, "poids_ms_cible": 45.0, "poids_fluides_cible": 19.0, "taux_internat_ref": 8, "budget_pedago_cible": 110}

def fiche_pedagogique(bouton_label, titre, definition, formule=None, normes=None):
    with st.popover(bouton_label):
        st.markdown(f"### {titre}")
        st.markdown(f"**En clair :** {definition}")
        if formule:
            st.markdown(f"**Calcul :** `{formule}`")
        if normes:
            st.markdown("**Normes & Seuils :**")
            for n in normes:
                st.markdown(f"* {n}")

# ==========================================
# PARSER DE BALANCES (L'Ingestion)
# ==========================================
def _read_tabular_file(file_obj):
    name = getattr(file_obj, "name", "balance.csv")
    raw = file_obj.getvalue() if hasattr(file_obj, "getvalue") else file_obj.read()
    if name.lower().endswith((".xlsx", ".xls")):
        try: return pd.read_excel(io.BytesIO(raw))
        except: return None
    for enc in ("utf-8", "latin-1", "cp1252"):
        for sep in (";", ",", "\t"):
            try:
                tmp = pd.read_csv(io.BytesIO(raw), sep=sep, encoding=enc)
                if tmp.shape[1] >= 2: return tmp
            except: continue
    return None

def _to_num(series):
    return pd.to_numeric(series.astype(str).str.replace(r"[\xa0\s]", "", regex=True).str.replace(",", ".", regex=False), errors="coerce").fillna(0.0)

def parse_balance_ogec(file_obj):
    name = getattr(file_obj, "name", "balance_2025.csv")
    ym = re.search(r"(20[1-3]\d)", name)
    annee = ym.group(1) if ym else None
    df = _read_tabular_file(file_obj)
    if df is None or df.empty: return None

    cols_l = {c: str(c).strip().lower() for c in df.columns}
    compte_col = next((c for c, cl in cols_l.items() if any(k in cl for k in ("compte", "article", "nature"))), df.columns[0])
    lib_col = next((c for c, cl in cols_l.items() if "libell" in cl or "intitul" in cl), None)
    deb_col = next((c for c, cl in cols_l.items() if "débit" in cl or "debit" in cl), None)
    cred_col = next((c for c, cl in cols_l.items() if "crédit" in cl or "credit" in cl), None)
    solde_col = next((c for c, cl in cols_l.items() if "solde" in cl or "montant" in cl), None)

    raw_c = df[compte_col].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    debits = _to_num(df[deb_col]) if deb_col else (_to_num(df[solde_col]).abs() if solde_col else pd.Series(0.0, index=df.index))
    credits = _to_num(df[cred_col]) if cred_col else (_to_num(df[solde_col]).abs() if solde_col else pd.Series(0.0, index=df.index))

    valid = raw_c.str.match(r"^\d{2,}$")
    if lib_col: valid = valid & ~df[lib_col].astype(str).str.lower().str.contains(r"\b(total|totaux)\b", regex=True)
    
    c_val, d_val, cr_val = raw_c[valid], debits[valid], credits[valid]
    norm_c = c_val.apply(lambda c: c.rstrip("0") if len(c.rstrip("0")) >= 2 else c[:2]) if (c_val.str.len().nunique()==1 and c_val.str.len().iloc[0]>=5) else c_val
    uniques = set(norm_c.unique())
    parents = {c for c in uniques if any(o != c and o.startswith(c) for o in uniques)}
    is_leaf = ~norm_c.isin(parents)

    comptes, debits, credits = c_val[is_leaf], d_val[is_leaf], cr_val[is_leaf]

    def sum_p(pref, side="debit"):
        m = comptes.apply(lambda x: any(x.startswith(p) for p in pref))
        return float(debits[m].sum() if side == "debit" else credits[m].sum())

    f_74 = sum_p(["74"], "credit")
    c_756 = sum_p(["756", "7061"], "credit")
    a_70 = sum_p(["70"], "credit") - sum_p(["7061"], "credit")
    aut_p = sum_p(["75", "76", "77", "78", "79"], "credit") - sum_p(["756"], "credit")
    loy = sum_p(["613"], "debit")
    ch_ext = max(0.0, sum_p(["60", "61", "62", "63"], "debit") - loy)
    ms = sum_p(["64"], "debit")
    aut_c = sum_p(["65", "67"], "debit")
    fin = sum_p(["66"], "debit")
    amo = sum_p(["68"], "debit")
    dette = sum_p(["164", "168"], "credit")
    remb = sum_p(["164", "168"], "debit")
    tres = sum_p(["512", "514", "53"], "debit")

    tp = f_74 + c_756 + max(0.0, a_70) + max(0.0, aut_p)
    tc = ch_ext + loy + ms + aut_c + fin + amo
    if tp <= 0 and tc <= 0: return None

    return {
        "annee": annee, "f_74": f_74, "c_756": c_756, "a_70": max(0.0, a_70), "aut_p": max(0.0, aut_p),
        "tp": tp, "ch_ext": ch_ext, "loy": loy, "ms": ms, "aut_c": aut_c, "fin": fin, "amo": amo,
        "tc": tc, "rn": tp - tc, "caf": (tp - tc) + amo, "dette": dette, "remb": remb, "tres": tres
    }

# ==========================================
# GÉNÉRATEUR DE PDF
# ==========================================
def build_ogec_pdf(etab, type_e, eleves, internes, tp, tc, caf, rn, tres, j_treso, det, ro_ok, solde_ro, marg_ufa, marg_cfc, b_peda, df_proj):
    buf = io.BytesIO()
    fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0.915), 1, 0.085, facecolor="#0f172a", transform=ax.transAxes))
    ax.text(0.04, 0.962, "ARCHÉTYPE ÉDUCATION  |  SYNTHÈSE FINANCIÈRE & ANALYTIQUE", color="white", fontsize=10.5, fontweight="bold")
    ax.text(0.04, 0.932, f"ÉTABLISSEMENT : {etab.upper()}  •  {type_e.upper()} ({eleves} ÉLÈVES)", color="#cbd5e1", fontsize=8.0)

    tcaf = (caf / tp * 100) if tp > 0 else 0
    kpis = [
        ("CAPACITÉ AUTOFIN. (CAF)", f"{caf:.2f} M€", f"Taux CAF : {tcaf:.1f} %", "#059669" if tcaf >= 6.5 else "#d97706"),
        ("RÉSULTAT NET COMPTABLE", f"{rn:+.2f} M€", f"Trésorerie : {tres:.2f} M€", "#059669" if rn >= 0 else "#dc2626"),
        ("TRÉSORERIE DE SÉCURITÉ", f"{j_treso} jours", f"Cible : 90-120 jours", "#1d4ed8" if j_treso >= 60 else "#dc2626"),
        ("ENCOURS DETTE IMMO", f"{det:.2f} M€", f"Solde Règle d'Or : {solde_ro:+.2f} M€", "#0f172a"),
    ]
    for i, (kt, kv, ks, kc) in enumerate(kpis):
        kx = 0.04 + i * 0.233
        ax.add_patch(FancyBboxPatch((kx, 0.815), 0.218, 0.084, boxstyle="round,pad=0,rounding_size=0.012", facecolor="#f8fafc", edgecolor="#cbd5e1", transform=ax.transAxes))
        ax.text(kx + 0.012, 0.880, kt, fontsize=7.0, fontweight="bold", color="#475569")
        ax.text(kx + 0.012, 0.845, kv, fontsize=12.5, fontweight="bold", color=kc)
        ax.text(kx + 0.012, 0.823, ks, fontsize=6.8, color="#64748b")

    ax.add_patch(FancyBboxPatch((0.04, 0.515), 0.45, 0.285, boxstyle="round,pad=0,rounding_size=0.012", facecolor="#ffffff", edgecolor="#cbd5e1", transform=ax.transAxes))
    ax.add_patch(Rectangle((0.04, 0.762), 0.45, 0.038, facecolor="#1e293b", transform=ax.transAxes))
    ax.text(0.055, 0.775, "1. COMPTE DE RÉSULTAT CONSOLIDÉ", color="white", fontsize=8.5, fontweight="bold")
    
    rows = [
        ("Total Produits d'Exploitation", f"{tp:.2f} M€", True, "#1d4ed8"),
        ("Total Charges d'Exploitation (incl. Amort.)", f"-{tc:.2f} M€", True, "#475569"),
        ("= Résultat Net Comptable", f"{rn:+.2f} M€", True, "#059669" if rn >= 0 else "#dc2626"),
        ("= Capacité d'Autofinancement (CAF)", f"{caf:.2f} M€", True, "#b45309"),
    ]
    yp = 0.732
    for lbl, val, bld, col in rows:
        ax.add_patch(Rectangle((0.048, yp - 0.009), 0.434, 0.029, facecolor="#f1f5f9", transform=ax.transAxes))
        ax.text(0.055, yp, lbl, fontsize=7.8, fontweight="bold", color="#1e293b")
        ax.text(0.478, yp, val, ha="right", fontsize=8.0, fontweight="bold", color=col)
        yp -= 0.040

    ro_bg, ro_bd, ro_fg = ("#ecfdf5", "#6ee7b7", "#065f46") if ro_ok else ("#fffbeb", "#fcd34d", "#92400e")
    ax.add_patch(FancyBboxPatch((0.51, 0.695), 0.45, 0.105, boxstyle="round,pad=0,rounding_size=0.012", facecolor=ro_bg, edgecolor=ro_bd, transform=ax.transAxes))
    ax.text(0.525, 0.778, "2. ÉTANCHÉITÉ PATRIMONIALE & RÈGLE D'OR", fontsize=8.1, fontweight="bold", color=ro_fg)
    ax.text(0.525, 0.745, f"Solde (Contrib. Familles - [Amort. + Intérêts + Loyers AEP]) : {solde_ro:+.2f} M€", fontsize=7.6, fontweight="bold", color=ro_fg)
    ax.text(0.525, 0.715, "L'immobilier n'est pas subventionné par les forfaits publics." if ro_ok else "Alerte : Les forfaits publics subventionnent l'immobilier.", fontsize=7.0, color="#475569")

    ax.add_patch(FancyBboxPatch((0.51, 0.515), 0.45, 0.165, boxstyle="round,pad=0,rounding_size=0.012", facecolor="#f8fafc", edgecolor="#cbd5e1", transform=ax.transAxes))
    ax.add_patch(Rectangle((0.51, 0.642), 0.45, 0.038, facecolor="#1e293b", transform=ax.transAxes))
    ax.text(0.525, 0.655, "3. DIAGNOSTIC ANALYTIQUE (SCALPEL)", color="white", fontsize=8.5, fontweight="bold")
    ax.text(0.525, 0.615, f"• Budget Pédagogique direct : {b_peda:,.0f} € / élève".replace(","," "), fontsize=7.5, color="#1e293b")
    ax.text(0.525, 0.585, f"• Marge Apprentissage (UFA) : {marg_ufa:+.2f} M€", fontsize=7.5, fontweight="bold", color="#059669" if marg_ufa>=0 else "#dc2626")
    ax.text(0.525, 0.555, f"• Marge Formation Continue (CFC) : {marg_cfc:+.2f} M€", fontsize=7.5, fontweight="bold", color="#059669" if marg_cfc>=0 else "#dc2626")
    if marg_ufa > 0 > marg_cfc:
        ax.text(0.525, 0.525, "Alerte : Le déficit de la CFC ampute la rentabilité de l'UFA.", fontsize=7.2, color="#991b1b", fontweight="bold")

    ax.text(0.04, 0.485, "4. TRAJECTOIRE PROSPECTIVE QUINQUENNALE (2026-2030)", fontsize=8.4, fontweight="bold", color="#0f172a")
    tbl_ax = fig.add_axes([0.04, 0.335, 0.92, 0.140])
    tbl_ax.axis("off")
    t_data = [
        ["Produits d'exploitation (M€)"] + [f"{v:.2f}" for v in df_proj["Produits (M€)"]],
        ["Charges d'exploitation (M€)"] + [f"{v:.2f}" for v in df_proj["Charges (M€)"]],
        ["Capacité d'Autofinancement — CAF (M€)"] + [f"{v:.2f}" for v in df_proj["CAF (M€)"]],
        ["Trésorerie disponible au 31/12 (M€)"] + [f"{v:.2f}" for v in df_proj["Trésorerie (M€)"]],
    ]
    tbl = tbl_ax.table(cellText=t_data, colLabels=["Indicateurs"] + list(df_proj["Année"]), loc="center", cellLoc="center", colWidths=[0.42] + [0.116] * 5)
    tbl.set_fontsize(7.4)
    tbl.scale(1, 1.30)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor("#cbd5e1")
        if r == 0: cell.set_facecolor("#1e293b"); cell.get_text().set_color("white"); cell.get_text().set_weight("bold")
        elif c == 0: cell.get_text().set_ha("left")

    fig.savefig(buf, format="pdf")
    plt.close(fig)
    return buf.getvalue()


# ==========================================
# BARRE LATÉRALE & INGESTION
# ==========================================
st.sidebar.markdown("## 🎓 Archétype Éducation")
type_etab = st.sidebar.selectbox(
    "Profil de l'établissement",
    ["Ensemble scolaire mixte (École + Collège + Lycée)", "Lycée Agricole Temps Plein (CNEAP / MASA)", "Maison Familiale Rurale / Alternance (UNMFREO)", "2nd degré (Lycée GT / Pro)", "2nd degré (Collège)", "1er degré (École maternelle / élémentaire)"]
)
is_agricole = ("Agricole" in type_etab) or ("Maison Familiale" in type_etab)
normes_etab = get_normes_etablissement(type_etab)
etablissement = st.sidebar.text_input("Nom de l'établissement", "Lycée Saint-Éloi")

activer_ufa_cfc = st.sidebar.checkbox("Intégrer UFA (Apprentissage) & CFC", value=(True if "Lycée" in type_etab or is_agricole else False))

st.sidebar.markdown("### 1. Ingestion Balances (ANC 2018-06)")
fichiers = st.sidebar.file_uploader("Glisser balances (.csv, .xlsx)", type=["csv", "xlsx", "xls"], accept_multiple_files=True)
balances_parsees = []
if fichiers:
    for f in fichiers:
        res_b = parse_balance_ogec(f)
        if res_b: balances_parsees.append(res_b)
balances_parsees.sort(key=lambda x: x["annee"] or x["fichier"])
source_reelle = len(balances_parsees) > 0

# Valeurs par défaut
if source_reelle:
    dern = balances_parsees[-1]
    d_f74 = dern["f_74"]
    d_c756 = dern["c_756"] if dern["c_756"] > 0 else dern["tp"] * 0.22
    d_a70 = dern["a_70"]
    d_autp = dern["aut_p"]
    d_ext = dern["ch_ext"]
    d_loy = dern["loy"]
    d_ms = dern["ms"]
    d_autc = dern["aut_c"]
    d_fin = dern["fin"]
    d_amo = dern["amo"]
    d_det = dern["dette"] if dern["dette"] > 0 else 1650000.0
    d_remb = dern["remb"] if dern["remb"] > 0 else 155000.0
    d_tres = dern["tres"] if dern["tres"] > 0 else 460000.0
else:
    d_f74, d_c756, d_a70, d_autp = 860000.0, 640000.0, 490000.0, 45000.0
    d_ext, d_loy, d_ms, d_autc = 670000.0, 85000.0, 960000.0, 75000.0
    d_fin, d_amo, d_det, d_remb, d_tres = 68000.0, 225000.0, 1650000.0, 155000.0, 460000.0
    if is_agricole:
        d_f74, d_c756, d_a70 = 840000.0, 245000.0, 680000.0
        d_ext, d_ms = 535000.0, 890000.0

st.sidebar.markdown("### 2. Données Scolaires & Internat")
eleves_tot = st.sidebar.number_input("Élèves formation initiale", min_value=1, value=650, step=10)
taux_internat = st.sidebar.slider("Taux d'internes / demi-pensionnaires (%)", 0, 100, int(normes_etab["taux_internat_ref"]), 5)
internes_tot = int(round(eleves_tot * taux_internat / 100))

st.sidebar.markdown("### 3. Produits & Charges Globaux")
f_74_m = st.sidebar.number_input("Forfaits / Subv. publiques (Cpte 74) (€)", value=float(d_f74), step=10000.0)
c_756_m = st.sidebar.number_input("Contributions familles (Cpte 756) (€)", value=float(d_c756), step=10000.0)
a_70_m = st.sidebar.number_input("Restauration & Annexes (Cpte 70) (€)", value=float(d_a70), step=10000.0)
ext_m = st.sidebar.number_input("Achats & Fluides (60-62) (€)", value=float(d_ext), step=10000.0)
ms_m = st.sidebar.number_input("Masse Salariale globale (64) (€)", value=float(d_ms), step=10000.0)

with st.sidebar.expander("🔍 L'Audit au Scalpel (Détails)"):
    st.caption("Isolez les coûts pour l'onglet Scalpel analytique.")
    achats_denrees = st.number_input("Dont Achats denrées alimentaires (€)", value=float(round(ext_m * 0.25)), step=5000.0)
    ms_resto = st.number_input("Dont Salaires cuisine & surveillance (€)", value=float(round(ms_m * 0.12)), step=5000.0)
    fluides_tot = st.number_input("Dont Énergie (Eau, Gaz, Élec) (€)", value=float(round(ext_m * 0.20)), step=5000.0)
    budget_pedago = st.number_input("Dont Achats Pédagogiques directs (€)", value=float(round(eleves_tot * normes_etab["budget_pedago_cible"])), step=5000.0)

prod_ufa, ch_ufa, prod_cfc, ch_cfc, apprentis_tot, stagiaires_tot = 0.0, 0.0, 0.0, 0.0, 0, 0
if activer_ufa_cfc:
    st.sidebar.markdown("### 4. Pôle UFA & CFC")
    st.caption("Les montants saisis ici s'ajoutent aux totaux globaux si vous n'avez pas importé de balance.")
    apprentis_tot = st.sidebar.number_input("Effectif Apprentis (UFA)", value=120, step=5)
    prod_ufa = st.sidebar.number_input("Produits UFA (NPEC, Taxe app.) (€)", value=780000.0, step=10000.0)
    ch_ufa = st.sidebar.number_input("Charges directes UFA (€)", value=640000.0, step=10000.0)
    stagiaires_tot = st.sidebar.number_input("Stagiaires FC (CFC / an)", value=80, step=5)
    prod_cfc = st.sidebar.number_input("Produits CFC (€)", value=120000.0, step=10000.0)
    ch_cfc = st.sidebar.number_input("Charges directes CFC (€)", value=135000.0, step=10000.0)

st.sidebar.markdown("### 5. Patrimoine & Dette")
loyers_aep = st.sidebar.number_input("Loyers immobiliers versés AEP (613)", value=float(d_loy), step=5000.0)
amort_m = st.sidebar.number_input("Amortissements (681)", value=float(d_amo), step=5000.0)
fin_m = st.sidebar.number_input("Intérêts emprunts (66)", value=float(d_fin), step=5000.0)
dette_m = st.sidebar.number_input("Encours dette immo au 31/12", value=float(d_det), step=25000.0)
remb_m = st.sidebar.number_input("Remboursement annuel capital", value=float(d_remb), step=5000.0)
treso_m = st.sidebar.number_input("Trésorerie disponible", value=float(d_tres), step=10000.0)

# ==========================================
# CALCULS MOTEUR
# ==========================================
if source_reelle:
    # La balance contient déjà tout, on ne double-compte pas l'UFA
    tp_global = f_74_m + c_756_m + a_70_m + d_autp
    tc_global = ext_m + loyers_aep + ms_m + d_autc + fin_m + amort_m
else:
    # Saisie manuelle, on additionne
    tp_global = f_74_m + c_756_m + a_70_m + d_autp + prod_ufa + prod_cfc
    tc_global = ext_m + loyers_aep + ms_m + d_autc + fin_m + amort_m + ch_ufa + ch_cfc

rn_global = tp_global - tc_global
caf_globale = rn_global + amort_m
ch_dec = max(1.0, tc_global - amort_m)
j_treso = int(round((treso_m / ch_dec) * 365))
autofin = caf_globale - remb_m

# Règle d'Or
ro_solde = c_756_m - (amort_m + fin_m + loyers_aep)
ro_ok = ro_solde >= 0
cap_desend = (dette_m / caf_globale) if caf_globale > 0 else 99.9

# Marge Resto
qp_fluides = fluides_tot * 0.30 if fluides_tot > 0 else 0
ch_resto = achats_denrees + ms_resto + qp_fluides
marge_resto = a_70_m - ch_resto

# Pédagogie
b_pedago_eleve = budget_pedago / max(1, eleves_tot)

# ==========================================
# INTERFACE (ONGLETS)
# ==========================================
st.title("Archétype Éducation — Pilotage & Audit")
c_titre, c_lex = st.columns([3, 1])
with c_titre:
    badge = "Balances ANC 2018-06 certifiées" if source_reelle else "Référentiel Observatoire"
    st.caption(f"{etablissement} • {normes_etab['type_court']} • {eleves_tot} Élèves • {badge}")
with c_lex:
    st.write("")
    fiche_pedagogique("📖 Lexique & Normes", "Ratios ANC 2018-06", "Règle d'Or = Familles (756) - [Amort.(68) + Int.(66) + Loyers(613)]", [f"CAF cible : {normes_etab['taux_caf_cible']}%", f"Trésorerie cible : {normes_etab['jours_treso_cible']} jours"])

onglets = st.tabs(["📊 Rétrospective", "⚖️ Diagnostic Global", "🔪 Le Scalpel Analytique", "🔮 Prospective", "📑 Synthèse PDF"])

# --- ONGLET 1 : RÉTROSPECTIVE ---
with onglets[0]:
    st.subheader("Dynamique Financière 2021-2025")
    if len(balances_parsees) >= 2:
        ans_r = [b["annee"] or f"Ex.{i+1}" for i, b in enumerate(balances_parsees)]
        p_r = [b["tp"]/1e6 for b in balances_parsees]
        c_r = [b["tc"]/1e6 for b in balances_parsees]
        caf_r = [b["caf"]/1e6 for b in balances_parsees]
    else:
        ans_r = ["2021", "2022", "2023", "2024", "2025"]
        tp_m = tp_global / 1e6
        tc_m = tc_global / 1e6
        p_r = [round(tp_m * 0.89, 2), round(tp_m * 0.92, 2), round(tp_m * 0.95, 2), round(tp_m * 0.98, 2), round(tp_m, 2)]
        c_r = [round(tc_m * 0.84, 2), round(tc_m * 0.88, 2), round(tc_m * 0.93, 2), round(tc_m * 0.97, 2), round(tc_m, 2)]
        caf_r = [p - c + (amort_m/1e6) for p, c in zip(p_r, c_r)]
    
    n_int = max(1, len(ans_r) - 1)
    tcma_p = ((p_r[-1] / p_r[0])**(1/n_int) - 1)*100 if p_r[0]>0 else 0
    tcma_c = ((c_r[-1] / c_r[0])**(1/n_int) - 1)*100 if c_r[0]>0 else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("TCMA Produits", f"+{tcma_p:.2f} % / an")
    k2.metric("TCMA Charges", f"+{tcma_c:.2f} % / an", f"Effet Ciseau : {tcma_c - tcma_p:+.2f} pts", delta_color="inverse")
    k3.metric("Dernière CAF", f"{caf_r[-1]:.2f} M€", f"{(caf_r[-1]/p_r[-1]*100):.1f} %")

    g1, g2 = st.columns(2)
    with g1:
        st.line_chart(pd.DataFrame({"Année": ans_r, "Produits (M€)": p_r, "Charges (M€)": c_r}).set_index("Année"))
    with g2:
        st.bar_chart(pd.DataFrame({"Année": ans_r, "CAF (M€)": caf_r}).set_index("Année"), color="#d97706")

# --- ONGLET 2 : DIAGNOSTIC GLOBAL ---
with onglets[1]:
    st.subheader("Compte de Résultat Consolidé (ANC 2018-06)")
    df_sig = pd.DataFrame([
        {"Poste": "Forfaits / Subv (74)", "Montant": f"{f_74_m/1e6:.2f} M€", "Part (%)": f"{f_74_m/tp_global*100:.1f} %"},
        {"Poste": "Familles (756)", "Montant": f"{c_756_m/1e6:.2f} M€", "Part (%)": f"{c_756_m/tp_global*100:.1f} %"},
        {"Poste": "Activité annexes (70/754)", "Montant": f"{(a_70_m+d_autp+prod_ufa+prod_cfc)/1e6:.2f} M€", "Part (%)": f"{(a_70_m+d_autp+prod_ufa+prod_cfc)/tp_global*100:.1f} %"},
        {"Poste": "= TOTAL PRODUITS", "Montant": f"{tp_global/1e6:.2f} M€", "Part (%)": "100.0 %"},
        {"Poste": "- Achats & Salaires", "Montant": f"-{(ext_m+ms_m+d_autc+ch_ufa+ch_cfc)/1e6:.2f} M€", "Part (%)": f"{(ext_m+ms_m+d_autc+ch_ufa+ch_cfc)/tp_global*100:.1f} %"},
        {"Poste": "- Immobilier (Amort, Int, Loyers)", "Montant": f"-{(amort_m+fin_m+loyers_aep)/1e6:.2f} M€", "Part (%)": f"{(amort_m+fin_m+loyers_aep)/tp_global*100:.1f} %"},
        {"Poste": "= RÉSULTAT NET", "Montant": f"{rn_global/1e6:+.2f} M€", "Part (%)": "-"},
        {"Poste": "= CAPACITÉ D'AUTOFINANCEMENT", "Montant": f"{caf_globale/1e6:.2f} M€", "Part (%)": f"{caf_globale/tp_global*100:.1f} %"}
    ])
    st.dataframe(df_sig, hide_index=True, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Trésorerie", f"{j_treso} jours", f"Cible : {normes_etab['jours_treso_cible']}", delta_color="normal" if j_treso >= 60 else "inverse")
    c2.metric("Capacité de Désendettement", f"{cap_desend:.1f} ans", "Cible < 8 ans", delta_color="normal" if cap_desend < 8 else "inverse")
    c3.metric("Autofinancement Net", f"{autofin/1e6:+.2f} M€", "Après remboursement dette")

# --- ONGLET 3 : LE SCALPEL ANALYTIQUE ---
with onglets[2]:
    st.subheader("Analyses Isolées (Centres de Profit / Coût)")
    
    # Règle d'Or
    st.markdown("#### 1. Règle d'Or Patrimoniale")
    if ro_ok: st.success(f"✅ L'immobilier est financé par les familles (Solde : +{ro_solde:,.0f} €)")
    else: st.error(f"❌ Tension immobilière : les contributions ne couvrent pas l'amortissement, les intérêts et les loyers AEP (Déficit : {ro_solde:,.0f} €)")

    # Pédagogie
    st.markdown("#### 2. Effort Pédagogique")
    col_p1, col_p2 = st.columns([1, 2])
    col_p1.metric("Budget Pédago. / Élève", f"{b_pedago_eleve:,.0f} €".replace(",", " "), f"Cible moy : ~{normes_etab['budget_pedago_cible']} €", delta_color="normal" if b_pedago_eleve >= normes_etab["budget_pedago_cible"] else "inverse")
    if b_pedago_eleve < normes_etab["budget_pedago_cible"]: col_p2.warning("La qualité pédagogique est potentiellement sacrifiée au profit des charges fixes.")

    # Restauration
    st.markdown("#### 3. Restauration & Internat")
    col_r1, col_r2 = st.columns([1, 2])
    tx_couv = (a_70_m / ch_resto * 100) if ch_resto > 0 else 0
    col_r1.metric("Marge Directe Restauration", f"{marge_resto:,.0f} €".replace(",", " "), f"Taux couverture : {tx_couv:.1f}%")
    if marge_resto < 0: col_r2.error("La cantine/internat détruit de la valeur et est subventionnée par le budget scolaire.")
    
    # UFA / CFC
    if activer_ufa_cfc:
        st.markdown("#### 4. Pôle UFA & CFC")
        col_u1, col_u2 = st.columns(2)
        m_ufa = prod_ufa - ch_ufa
        m_cfc = prod_cfc - ch_cfc
        col_u1.metric("Marge Nette Apprentissage", f"{m_ufa:,.0f} €".replace(",", " "))
        col_u2.metric("Marge Nette Formation Continue", f"{m_cfc:,.0f} €".replace(",", " "), delta_color="normal" if m_cfc>=0 else "inverse")
        if m_ufa > 0 > m_cfc: st.warning("Le déficit de la FC vient annuler la rentabilité de l'Apprentissage.")

# --- ONGLET 4 : PROSPECTIVE ---
with onglets[3]:
    st.subheader("Simulateur Quinquennal 2026-2030")
    s1, s2, s3 = st.columns(3)
    tx_el = s1.slider("Évolution annuelle effectifs élèves (%)", -3.0, 4.0, 0.5)
    tx_forf = s1.slider("Revalorisation Forfaits Publics (%/an)", 0.0, 5.0, 2.0)
    tx_ch = s2.slider("Inflation des charges fixes et Salaires (%/an)", 1.0, 6.0, 3.0)
    ppi_m = s3.slider("Plan Pluriannuel d'Investissement (M€/an)", 0.0, 2.0, 0.3)

    ans = ["2026", "2027", "2028", "2029", "2030"]
    p_p, p_c, p_caf, p_t = [], [], [], []
    c_p, c_c, c_tres = tp_global, tc_global, treso_m
    
    for _ in ans:
        c_p = c_p * (1 + tx_el/100) * (1 + tx_forf/100)
        c_c = c_c * (1 + tx_ch/100) + (ppi_m * 1e6 * 0.04)
        c_caf = (c_p - c_c) + amort_m + (ppi_m * 1e6 * 0.04)
        c_tres = c_tres + c_caf - remb_m - (ppi_m * 1e6 * 0.5)
        
        p_p.append(c_p/1e6); p_c.append(c_c/1e6); p_caf.append(c_caf/1e6); p_t.append(c_tres/1e6)

    df_proj = pd.DataFrame({"Année": ans, "Produits (M€)": p_p, "Charges (M€)": p_c, "CAF (M€)": p_caf, "Trésorerie (M€)": p_t})
    st.dataframe(df_proj, hide_index=True, use_container_width=True)

# --- ONGLET 5 : PDF ---
with onglets[4]:
    st.subheader("Note de Synthèse & Export")
    pdf_bytes = build_ogec_pdf(etablissement, type_etab, eleves_tot, internes_tot, tp_global/1e6, tc_global/1e6, caf_globale/1e6, rn_global/1e6, treso_m/1e6, j_treso, dette_m/1e6, ro_ok, ro_solde/1e6, (prod_ufa-ch_ufa)/1e6, (prod_cfc-ch_cfc)/1e6, b_pedago_eleve, df_proj)
    st.download_button("📑 Télécharger la Synthèse Complète (PDF)", data=pdf_bytes, file_name=f"Synthese_{etablissement.replace(' ','_')}.pdf", mime="application/pdf", type="primary", use_container_width=True)
