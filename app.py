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
from matplotlib.backends.backend_pdf import PdfPages

st.set_page_config(
    page_title="Archétype Éducation — Audit, Pilotage & Prospective",
    page_icon="🎓",
    layout="wide"
)

# ==========================================
# 1. RÉFÉRENTIEL & MOYENNES PAR STRATE (ANC 2018-06)
# ==========================================
def get_normes_etablissement(type_etab):
    if "1er degré" in type_etab:
        return {"type_court": "1er degré (École)", "strate": "Écoles sous contrat (Loi Debré)", "financeur": "Commune", "forfait_eleve": 880, "contrib_eleve": 420, "taux_ebe": 9.5, "taux_caf": 6.5, "jours_treso": 90, "poids_ms": 48.0, "poids_admin": 24.0, "b_peda": 70, "maint_m2": 15.0, "fluides_eleve": 145, "tx_internat": 0, "desend_moy": 5.2, "desend_max": 8.0}
    elif "Collège" in type_etab:
        return {"type_court": "2nd degré (Collège)", "strate": "Collèges sous contrat (Loi Debré)", "financeur": "Département", "forfait_eleve": 647, "contrib_eleve": 580, "taux_ebe": 10.5, "taux_caf": 7.5, "jours_treso": 90, "poids_ms": 44.0, "poids_admin": 26.0, "b_peda": 100, "maint_m2": 18.0, "fluides_eleve": 165, "tx_internat": 5, "desend_moy": 5.5, "desend_max": 8.0}
    elif "Lycée GT" in type_etab:
        return {"type_court": "2nd degré (Lycée GT/Pro)", "strate": "Lycées GT & Pro sous contrat", "financeur": "Région", "forfait_eleve": 803, "contrib_eleve": 690, "taux_ebe": 11.2, "taux_caf": 8.0, "jours_treso": 90, "poids_ms": 42.0, "poids_admin": 27.0, "b_peda": 130, "maint_m2": 22.0, "fluides_eleve": 190, "tx_internat": 12, "desend_moy": 5.8, "desend_max": 8.0}
    elif "Agricole" in type_etab:
        return {"type_court": "Lycée Agricole (MASA)", "strate": "Enseignement Agricole Temps Plein", "financeur": "MASA & Région", "forfait_eleve": 2450, "contrib_eleve": 720, "taux_ebe": 11.5, "taux_caf": 8.5, "jours_treso": 75, "poids_ms": 46.0, "poids_admin": 25.0, "b_peda": 150, "maint_m2": 28.0, "fluides_eleve": 260, "tx_internat": 65, "desend_moy": 6.0, "desend_max": 8.5}
    elif "MFR" in type_etab:
        return {"type_court": "MFR / Alternance", "strate": "Maisons Familiales Rurales (MASA)", "financeur": "MASA & OPCO", "forfait_eleve": 4100, "contrib_eleve": 680, "taux_ebe": 10.8, "taux_caf": 8.0, "jours_treso": 75, "poids_ms": 64.0, "poids_admin": 23.0, "b_peda": 150, "maint_m2": 24.0, "fluides_eleve": 240, "tx_internat": 75, "desend_moy": 5.5, "desend_max": 8.0}
    else:
        return {"type_court": "Ensemble mixte", "strate": "Ensembles scolaires multi-niveaux", "financeur": "Multi-guichets", "forfait_eleve": 760, "contrib_eleve": 560, "taux_ebe": 10.5, "taux_caf": 7.5, "jours_treso": 90, "poids_ms": 45.0, "poids_admin": 26.0, "b_peda": 110, "maint_m2": 20.0, "fluides_eleve": 175, "tx_internat": 8, "desend_moy": 5.6, "desend_max": 8.0}

def afficher_synthese_unique(titre, constat, points_appui, leviers_budget):
    st.markdown("---")
    with st.container(border=True):
        st.markdown(f"### Synthèse & Clés de lecture — {titre}")
        st.markdown(f"**1. Positionnement & Diagnostic :** {constat}")
        st.markdown(f"**2. Points d'appui pour l'établissement :** {points_appui}")
        st.markdown(f"**3. Arbitrages pour le budget prévisionnel :** {leviers_budget}")

def afficher_aide_pedagogique_onglet(titre_aide, points_cles):
    with st.expander(f"💡 Comprendre les indicateurs — {titre_aide}", expanded=False):
        for notion, explication in points_cles:
            st.markdown(f"* **{notion} :** {explication}")

# ==========================================
# 2. MOTEUR D'INGESTION BALANCES
# ==========================================
def _to_num(series):
    return pd.to_numeric(series.astype(str).str.replace(r"[\xa0\s]", "", regex=True).str.replace(",", ".", regex=False), errors="coerce").fillna(0.0)

def parse_balance_ogec(file_obj):
    name = getattr(file_obj, "name", "balance.csv")
    ym = re.search(r"(20[1-3]\d)", name)
    annee = ym.group(1) if ym else None
    
    raw = file_obj.getvalue() if hasattr(file_obj, "getvalue") else file_obj.read()
    df = None
    if name.lower().endswith((".xlsx", ".xls")):
        try: df = pd.read_excel(io.BytesIO(raw))
        except: pass
    else:
        for enc in ("utf-8", "latin-1", "cp1252"):
            for sep in (";", ",", "\t"):
                try:
                    tmp = pd.read_csv(io.BytesIO(raw), sep=sep, encoding=enc)
                    if tmp.shape[1] >= 2:
                        df = tmp
                        break
                except: continue
            if df is not None: break
            
    if df is None or df.empty: return None

    cols_l = {c: str(c).strip().lower() for c in df.columns}
    compte_col = next((c for c, cl in cols_l.items() if any(k in cl for k in ("compte", "article", "nature"))), df.columns[0])
    deb_col = next((c for c, cl in cols_l.items() if "débit" in cl or "debit" in cl), None)
    cred_col = next((c for c, cl in cols_l.items() if "crédit" in cl or "credit" in cl), None)
    solde_col = next((c for c, cl in cols_l.items() if "solde" in cl or "montant" in cl), None)

    raw_c = df[compte_col].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    debits = _to_num(df[deb_col]) if deb_col else (_to_num(df[solde_col]).abs() if solde_col else pd.Series(0.0, index=df.index))
    credits = _to_num(df[cred_col]) if cred_col else (_to_num(df[solde_col]).abs() if solde_col else pd.Series(0.0, index=df.index))

    valid = raw_c.str.match(r"^\d{2,}$")
    c_val, d_val, cr_val = raw_c[valid], debits[valid], credits[valid]
    norm_c = c_val.apply(lambda c: c.rstrip("0") if len(c.rstrip("0")) >= 2 else c[:2]) if (c_val.str.len().nunique() == 1 and c_val.str.len().iloc[0] >= 5) else c_val
    uniques = set(norm_c.unique())
    parents = {c for c in uniques if any(o != c and o.startswith(c) for o in uniques)}
    is_leaf = ~norm_c.isin(parents)
    comptes, debits, credits = c_val[is_leaf], d_val[is_leaf], cr_val[is_leaf]

    def sum_p(pref, side="debit"):
        m = comptes.apply(lambda x: any(x.startswith(p) for p in pref))
        return float(debits[m].sum() if side == "debit" else credits[m].sum())

    f_74 = sum_p(["74"], "credit")
    c_756 = sum_p(["756", "7061"], "credit")
    a_70 = max(0.0, sum_p(["70"], "credit") - sum_p(["7061"], "credit"))
    aut_p = max(0.0, sum_p(["75", "76", "77", "78", "79"], "credit") - sum_p(["756"], "credit"))

    ach_60 = sum_p(["60"], "debit")
    loy_613 = sum_p(["613"], "debit")
    maint_615 = sum_p(["615"], "debit")
    aut_ext = max(0.0, sum_p(["61", "62", "63", "65", "67"], "debit") - loy_613 - maint_615)
    ms_64 = sum_p(["64"], "debit")
    fin_66 = sum_p(["66"], "debit")
    amo_68 = sum_p(["68"], "debit")
    dette_16 = sum_p(["164", "168"], "credit")
    remb_16 = sum_p(["164", "168"], "debit")
    tres_51 = sum_p(["512", "514", "53"], "debit")

    tp = f_74 + c_756 + a_70 + aut_p
    tc = ach_60 + loy_613 + maint_615 + aut_ext + ms_64 + fin_66 + amo_68
    if tp <= 0 and tc <= 0: return None

    return {
        "fichier": name, "annee": annee,
        "f_74": f_74, "c_756": c_756, "a_70": a_70, "aut_p": aut_p, "tp": tp,
        "ach_60": ach_60, "loy_613": loy_613, "maint_615": maint_615, "aut_ext": aut_ext,
        "ms_64": ms_64, "fin_66": fin_66, "amo_68": amo_68, "tc": tc,
        "rn": tp - tc, "caf": (tp - tc) + amo_68,
        "dette": dette_16, "remb": remb_16, "tres": tres_51
    }

# ==========================================
# 3. BARRE LATÉRALE : INGESTION & PARAMÉTRAGE
# ==========================================
st.sidebar.markdown("## 🎓 Archétype Éducation")
type_etab = st.sidebar.selectbox(
    "Profil & Tutelle de l'établissement",
    [
        "Ensemble scolaire mixte (École + Collège + Lycée)",
        "2nd degré (Lycée GT / Pro — Loi Debré)",
        "2nd degré (Collège — Loi Debré)",
        "1er degré (École maternelle / élémentaire)",
        "Lycée Agricole Temps Plein (Art. L. 813-8 MASA)",
        "MFR / Alternance (Art. L. 813-9 MASA)"
    ]
)
is_agricole = ("Agricole" in type_etab) or ("MFR" in type_etab)
normes = get_normes_etablissement(type_etab)
etab = st.sidebar.text_input("Nom de l'établissement", "Lycée Polyvalent Saint-Éloi")

c_sb1, c_sb2 = st.sidebar.columns(2)
eleves_tot = c_sb1.number_input("Élèves (initial)", min_value=1, value=650, step=10)
surface_m2 = c_sb2.number_input("Surface bâtie (m²)", min_value=100, value=4800, step=100)
taux_internat = st.sidebar.slider("Taux demi-pensionnaires / internes (%)", 0, 100, int(normes["tx_internat"]), 5)
internes_tot = int(round(eleves_tot * taux_internat / 100))

st.sidebar.markdown("### 1. Ingestion Balances (2021-2025)")
fichiers = st.sidebar.file_uploader("Importer balances comptables", type=["csv", "xlsx", "xls"], accept_multiple_files=True)
balances_parsees = []
if fichiers:
    for f in fichiers:
        rb = parse_balance_ogec(f)
        if rb: balances_parsees.append(rb)
balances_parsees.sort(key=lambda x: x["annee"] or x["fichier"])
source_reelle = len(balances_parsees) > 0

if source_reelle:
    dern = balances_parsees[-1]
    d_f74, d_c756, d_a70, d_autp = dern["f_74"], (dern["c_756"] if dern["c_756"] > 0 else dern["tp"]*0.22), dern["a_70"], dern["aut_p"]
    d_ach, d_loy, d_maint, d_ext, d_ms = dern["ach_60"], dern["loy_613"], dern["maint_615"], dern["aut_ext"], dern["ms_64"]
    d_fin, d_amo = dern["fin_66"], dern["amo_68"]
    d_det = dern["dette"] if dern["dette"] > 0 else 1550000.0
    d_remb = dern["remb"] if dern["remb"] > 0 else 145000.0
    d_tres = dern["tres"] if dern["tres"] > 0 else 440000.0
else:
    d_f74, d_c756 = float(eleves_tot * normes["forfait_eleve"]), float(eleves_tot * normes["contrib_eleve"])
    d_a70, d_autp = float(internes_tot * 780 + 45000), 45000.0
    d_ach, d_loy = float(eleves_tot * normes["b_peda"] + internes_tot * 290), 85000.0
    d_maint, d_ext = float(surface_m2 * normes["maint_m2"]), float(eleves_tot * 240)
    d_ms = float(eleves_tot * 1450)
    d_fin, d_amo, d_det, d_remb, d_tres = 52000.0, 195000.0, 1550000.0, 145000.0, 440000.0

st.sidebar.markdown("### 2. Recettes & Pôle Hors Contrat")
f_74 = st.sidebar.number_input("Forfaits & Subv. (74) (€)", value=float(d_f74), step=10000.0)
c_756 = st.sidebar.number_input("Contributions familles (756) (€)", value=float(d_c756), step=10000.0)
a_70 = st.sidebar.number_input("Restauration, internat (70) (€)", value=float(d_a70), step=10000.0)
aut_p = st.sidebar.number_input("Autres produits (75/78) (€)", value=float(d_autp), step=5000.0)

activer_ufa_cfc = st.sidebar.checkbox("Intégrer UFA (Apprentissage) & CFC", value=(True if "Lycée" in type_etab or is_agricole else False))
prod_ufa, ch_ufa, prod_cfc, ch_cfc, app_tot, stag_tot = 0.0, 0.0, 0.0, 0.0, 0, 0
if activer_ufa_cfc:
    with st.sidebar.expander("🎓 Détail UFA & CFC", expanded=True):
        app_tot = st.number_input("Effectif apprentis (UFA)", value=110, step=5)
        prod_ufa = st.number_input("Produits UFA (€)", value=740000.0, step=10000.0)
        ch_ufa = st.number_input("Charges UFA (€)", value=610000.0, step=10000.0)
        stag_tot = st.number_input("Stagiaires (CFC)", value=75, step=5)
        prod_cfc = st.number_input("Produits CFC (€)", value=115000.0, step=5000.0)
        ch_cfc = st.number_input("Charges CFC (€)", value=132000.0, step=5000.0)

with st.sidebar.expander("👥 3. Granularité RH (Compte 64)", expanded=True):
    ms_prive = st.number_input("Enseignants droit privé (Rempl., hors contrat)", value=float(round(d_ms * 0.14)), step=5000.0)
    ms_vie_scol = st.number_input("Vie scolaire, éducateurs, AESH", value=float(round(d_ms * 0.34)), step=5000.0)
    ms_admin = st.number_input("Administration, direction, compta", value=float(round(d_ms * 0.27)), step=5000.0)
    ms_tech = st.number_input("Technique, entretien, restauration", value=float(round(d_ms * 0.25)), step=5000.0)
    ms_totale = ms_prive + ms_vie_scol + ms_admin + ms_tech

with st.sidebar.expander("⚙️ 4. Achats & Maintenance", expanded=True):
    ach_peda = st.number_input("Budget pédagogique direct (601/606)", value=float(eleves_tot * normes["b_peda"]), step=2000.0)
    ach_resto = st.number_input("Achats denrées restauration (601)", value=float(max(0.0, d_ach - eleves_tot * normes["b_peda"])), step=5000.0)
    maint_615 = st.number_input("Maintenance bâtiments (615)", value=float(d_maint), step=5000.0)
    fluides_606 = st.number_input("Énergie & fluides (606)", value=float(round(d_ext * 0.55)), step=5000.0)
    autres_ext = st.number_input("Autres charges externes (Assur...)", value=float(round(d_ext * 0.45)), step=5000.0)
    loyers_613 = st.number_input("Loyers immobiliers (AEP) (613)", value=float(d_loy), step=5000.0)

st.sidebar.markdown("### 5. Patrimoine & Dette")
amort_68 = st.sidebar.number_input("Amortissements (681) (€)", value=float(d_amo), step=5000.0)
fin_66 = st.sidebar.number_input("Intérêts emprunts (66) (€)", value=float(d_fin), step=2000.0)
dette_16 = st.sidebar.number_input("Dette immobilière 31/12 (€)", value=float(d_det), step=25000.0)
remb_16 = st.sidebar.number_input("Remboursement annuel capital (€)", value=float(d_remb), step=5000.0)
treso_51 = st.sidebar.number_input("Trésorerie disponible (€)", value=float(d_tres), step=10000.0)

# ==========================================
# 4. CALCULS DU MOTEUR FINANCIER & SCALPEL
# ==========================================
if source_reelle:
    tp = f_74 + c_756 + a_70 + aut_p
    ch_achats = ach_peda + ach_resto
    ch_ext_hors_achats = maint_615 + fluides_606 + autres_ext + loyers_613
    tc = ch_achats + ch_ext_hors_achats + ms_totale + fin_66 + amort_68
else:
    tp = f_74 + c_756 + a_70 + aut_p + prod_ufa + prod_cfc
    ch_achats = ach_peda + ach_resto
    ch_ext_hors_achats = maint_615 + fluides_606 + autres_ext + loyers_613
    tc = ch_achats + ch_ext_hors_achats + ms_totale + fin_66 + amort_68 + ch_ufa + ch_cfc

rn = tp - tc
caf = rn + amort_68
autofin_net = caf - remb_16
tcaf = (caf / tp * 100) if tp > 0 else 0.0

marge_brute = tp - ch_achats
valeur_ajoutee = marge_brute - ch_ext_hors_achats
ebe = valeur_ajoutee - ms_totale
tebe = (ebe / tp * 100) if tp > 0 else 0.0

ch_dec = max(1.0, tc - amort_68)
j_treso = int(round((treso_51 / ch_dec) * 365))
cap_desend = (dette_16 / caf) if caf > 0 else 99.9
ro_solde = c_756 - (amort_68 + fin_66 + loyers_613)
ro_ok = ro_solde >= 0

forfait_eleve_reel = f_74 / max(1, eleves_tot)
contrib_eleve_reel = c_756 / max(1, eleves_tot)
maint_m2 = maint_615 / max(1, surface_m2)
fluides_eleve = fluides_606 / max(1, eleves_tot)
b_peda_eleve = ach_peda / max(1, eleves_tot)
poids_ms_tp = (ms_totale / tp * 100) if tp > 0 else 0.0
poids_admin_ms = (ms_admin / ms_totale * 100) if ms_totale > 0 else 0.0

ch_resto_directes = ach_resto + (ms_tech * 0.45) + (fluides_606 * 0.25)
marge_resto = a_70 - ch_resto_directes
tx_couv_resto = (a_70 / ch_resto_directes * 100) if ch_resto_directes > 0 else 100.0

marge_ufa = prod_ufa - ch_ufa
marge_cfc = prod_cfc - ch_cfc

s_caf = min(30, max(0, int(round((tcaf / normes["taux_caf"]) * 25))))
s_ro = 25 if ro_ok else max(0, int(round(25 + (ro_solde / max(1.0, c_756)) * 60)))
s_treso = min(25, max(0, int(round((j_treso / normes["jours_treso"]) * 22))))
s_det = 20 if cap_desend <= normes["desend_moy"] else (14 if cap_desend <= normes["desend_max"] else (6 if cap_desend <= 11 else 0))
health_score = min(100, s_caf + s_ro + s_treso + s_det)

# ==========================================
# 5. INTERFACE & GUIDE PÉDAGOGIQUE (Haut de page)
# ==========================================
st.title("Archétype Éducation — Audit, Pilotage & Prospective")
badge_src = "Balances certifiées" if source_reelle else "Modèle calibré Observatoire"
st.caption(f"Établissement : **{etab}** • {normes['type_court']} • {eleves_tot} élèves • {surface_m2} m² • {badge_src}")

with st.expander("📖 Guide pédagogique (Spécial Conseil d'Administration & Chef d'établissement)", expanded=False):
    st.markdown("Ce guide traduit les termes comptables (norme associative ANC 2018-06) en repères concrets de gestion :")
    gp_c1, gp_c2, gp_c3 = st.columns(3)
    with gp_c1:
        st.markdown("**1. La Règle d'Or Patrimoniale**")
        st.markdown(
            "La loi interdit d'utiliser l'argent public (forfaits) pour acheter ou rénover des murs. "
            "**En clair :** les *contributions des familles* (756) doivent couvrir à elles seules l'usure comptable des bâtiments (*amortissements*), les *intérêts* et les *loyers*. "
            "Si ce solde est négatif, l'école pioche dans son fonctionnement quotidien pour payer l'immobilier."
        )
    with gp_c2:
        st.markdown("**2. EBE, CAF et Autofinancement**")
        st.markdown(
            "* **EBE :** ce que l'école gagne sur son activité courante avant de payer les banques et l'usure des bâtiments.\\n"
            "* **CAF (Capacité d'Autofinancement) :** la trésorerie dégagée sur l'année. Cible saine : **7 à 8 %** des recettes.\\n"
            "* **Autofinancement Net :** ce qu'il reste réellement dans la caisse une fois l'échéance annuelle de prêt remboursée à la banque."
        )
    with gp_c3:
        st.markdown("**3. Spécificités des profils (MFR, Agricole, Internat)**")
        st.markdown(
            "* **MFR :** les formateurs sont salariés de l'association (contrairement aux profs payés par l'État ailleurs). La masse salariale y est logiquement très élevée (> 60 %).\\n"
            "* **Lycées Agricoles :** le poids de l'internat (souvent 40 à 60 % des élèves) et des plateaux techniques (exploitations) gonfle les coûts de maintenance et d'énergie."
        )

# ------------------------------------------
# ONGLET 1 : RÉTROSPECTIVE (Comprendre la trajectoire)
# ------------------------------------------
onglets = st.tabs([
    "📊 1. Rétrospective (Trajectoire passée)",
    "⚖️ 2. Situation à date (TBI & Constat)",
    "🔪 3. Scalpel (Choix prévisionnels)",
    "🔮 4. Prospective (Projet à 5 ans)"
])

with onglets[0]:
    st.subheader("D'où venons-nous ? Comprendre la trajectoire passée")
    afficher_aide_pedagogique_onglet("Dynamique passée & Salaires", [
        ("TCMA (Taux de Croissance Annuel Moyen)", "C'est le rythme moyen d'augmentation par an entre 2021 et 2025. Si les charges montent plus vite que les produits, on subit un « effet ciseau » qui détruit la trésorerie."),
        ("GVT & Mesures Nationales", "Hausses salariales subies (ancienneté, hausse du point d'indice, SMIC)."),
        ("Effet Volume (Le vrai levier)", "Part de la hausse des salaires qui relève de vos choix (créations de postes, remplacements d'absents). Une gestion saine vise un effet volume proche de 0.")
    ])

    if len(balances_parsees) >= 2:
        ans_r = [b["annee"] or f"Ex.{i+1}" for i, b in enumerate(balances_parsees)]
        p_r = [b["tp"]/1e6 for b in balances_parsees]
        c_r = [b["tc"]/1e6 for b in balances_parsees]
        ms_r = [b["ms_64"]/1e6 for b in balances_parsees]
        caf_r = [b["caf"]/1e6 for b in balances_parsees]
        aut_r = [(b["caf"] - (b["remb"] if b["remb"]>0 else remb_16))/1e6 for b in balances_parsees]
    else:
        ans_r = ["2021", "2022", "2023", "2024", "2025"]
        tp_m, tc_m, ms_m, caf_m = tp/1e6, tc/1e6, ms_totale/1e6, caf/1e6
        p_r = [round(tp_m*0.87, 2), round(tp_m*0.90, 2), round(tp_m*0.93, 2), round(tp_m*0.97, 2), round(tp_m, 2)]
        c_r = [round(tc_m*0.81, 2), round(tc_m*0.86, 2), round(tc_m*0.91, 2), round(tc_m*0.96, 2), round(tc_m, 2)]
        ms_r = [round(ms_m*0.82, 2), round(ms_m*0.87, 2), round(ms_m*0.92, 2), round(ms_m*0.96, 2), round(ms_m, 2)]
        caf_r = [round(p - c + (amort_68/1e6)*0.92, 2) for p, c in zip(p_r[:-1], c_r[:-1])] + [round(caf_m, 2)]
        aut_r = [round(cf - (remb_16/1e6), 2) for cf in caf_r]

    tcma_p = ((p_r[-1]/p_r[0])**(1/(len(ans_r)-1)) - 1)*100
    tcma_c = ((c_r[-1]/c_r[0])**(1/(len(ans_r)-1)) - 1)*100
    tcma_ms = ((ms_r[-1]/ms_r[0])**(1/(len(ans_r)-1)) - 1)*100
    ciseau = tcma_c - tcma_p

    kr1, kr2, kr3, kr4 = st.columns(4)
    kr1.metric("TCMA Produits", f"+{tcma_p:.2f} % / an", "Rythme des recettes")
    kr2.metric("TCMA Charges", f"+{tcma_c:.2f} % / an", f"Effet ciseau : {ciseau:+.2f} pts", delta_color="inverse" if ciseau > 0 else "normal")
    kr3.metric("TCMA Masse Salariale", f"+{tcma_ms:.2f} % / an", f"Poids : {poids_ms_tp:.1f} % (Moy. {normes['poids_ms']} %)")
    kr4.metric("Évolution CAF", f"{caf_r[-1]:.2f} M€", f"Variation : {(caf_r[-1]-caf_r[0]):+.2f} M€")

    cg1, cg2 = st.columns(2)
    with cg1:
        st.markdown("**1. Effet de ciseau (Produits vs Charges en M€)**")
        st.line_chart(pd.DataFrame({"Exercice": ans_r, "Produits": p_r, "Charges": c_r}).set_index("Exercice"))
    with cg2:
        st.markdown("**2. Érosion de la CAF & Autofinancement net (M€)**")
        st.line_chart(pd.DataFrame({"Exercice": ans_r, "CAF": caf_r, "Autofin. Net": aut_r}).set_index("Exercice"))

    st.markdown("**3. Décomposition de la dérive salariale interne (Compte 64)**")
    cd1, cd2, cd3 = st.columns(3)
    gvt_pt = cd1.slider("GVT Mécanique (Ancienneté subie)", 0.5, 2.5, 1.2, 0.1)
    conv_pt = cd2.slider("Mesures Nationales (EEPNL/SMIC subis)", 0.5, 3.5, 1.6, 0.1)
    vol_pt = round(tcma_ms - gvt_pt - conv_pt, 2)
    cd3.metric("Effet Volume (Vos choix RH locaux)", f"{vol_pt:+.2f} pts / an", "Norme cible : <= +0,30 pt/an", delta_color="inverse" if vol_pt > 0.3 else "normal")

    afficher_synthese_unique(
        "Rétrospective & Compréhension de la trajectoire",
        f"L'établissement subit un effet ciseau de {ciseau:+.2f} pts/an (les charges augmentant plus vite que les recettes). Le taux de CAF est de {tcaf:.1f} % contre {normes['taux_caf']} % attendus pour ce type d'établissement.",
        f"Sur la dérive salariale constatée (+{tcma_ms:.2f} %/an), {(gvt_pt+conv_pt):.2f} pts sont totalement indépendants de votre volonté (vieillissement et revalorisations conventionnelles).",
        f"La part relevant de l'organisation locale (effet volume) est de {vol_pt:+.2f} pts/an. Un redressement budgétaire implique de stabiliser cet effet volume en gelant les créations de postes et en optimisant les remplacements courts."
    )

# ------------------------------------------
# ONGLET 2 : TBI (Situation à date)
# ------------------------------------------
with onglets[1]:
    st.subheader("Où en est-on ? Tableau de bord exécutif et positionnement")
    afficher_aide_pedagogique_onglet("Analyse de l'année en cours (SIG & Bilan)", [
        ("Health Score (/100)", "Si la note est < 70, la trajectoire actuelle marque un infléchissement négatif (tension sur la trésorerie ou incapacité à payer l'emprunt avec la CAF générée)."),
        ("Colonne Moyenne / Norme", "Permet de vérifier si le forfait versé par la collectivité ou les salaires payés sont dans les clous de ce qui se fait ailleurs dans la même strate.")
    ])

    hs1, hs2 = st.columns([1, 2.5])
    with hs1: st.metric("HEALTH SCORE ACTUEL", f"{health_score} / 100", "Sain >= 70 | Alerte < 45")
    with hs2:
        if health_score >= 70: st.success(f"**Aucun infléchissement majeur :** L'établissement maintient une CAF de {tcaf:.1f} % (cible {normes['taux_caf']} %) et respecte la Règle d'Or.")
        else: st.error(f"**Infléchissement constaté :** L'EBE ({tebe:.1f} % vs {normes['taux_ebe']} % attendus) ne permet plus de générer la CAF requise. Ajustements nécessaires au prochain EPRD.")

    c_sig1, c_sig2 = st.columns([1.45, 1])
    with c_sig1:
        st.markdown("**Cascade des SIG (D'où vient la performance de l'année ?)**")
        df_sig = pd.DataFrame([
            {"SIG": "Produits d'Exploitation", "Montant": f"{tp:,.0f} €", "% Prod": "100%", "Norme": "Base 100 %"},
            {"SIG": "- Achats (Pédagogie + Denrées)", "Montant": f"-{ch_achats:,.0f} €", "% Prod": f"{ch_achats/tp*100:.1f} %", "Norme": "12 - 18 %"},
            {"SIG": "- Ext., Maintenance, Fluides", "Montant": f"-{ch_ext_hors_achats:,.0f} €", "% Prod": f"{ch_ext_hors_achats/tp*100:.1f} %", "Norme": "18 - 25 %"},
            {"SIG": "= VALEUR AJOUTÉE (VA)", "Montant": f"{valeur_ajoutee:,.0f} €", "% Prod": f"{valeur_ajoutee/tp*100:.1f} %", "Norme": "55 - 65 %"},
            {"SIG": "- Masse Salariale Interne (64)", "Montant": f"-{ms_totale:,.0f} €", "% Prod": f"{poids_ms_tp:.1f} %", "Norme": f"Moy. {normes['poids_ms']} %"},
            {"SIG": "= EBE (Excédent Brut)", "Montant": f"{ebe:,.0f} €", "% Prod": f"{tebe:.1f} %", "Norme": f"Moy. {normes['taux_ebe']} %"},
            {"SIG": "= CAPACITÉ D'AUTOFINANCEMENT", "Montant": f"{caf:,.0f} €", "% Prod": f"{tcaf:.1f} %", "Norme": f"Cible {normes['taux_caf']} %"},
            {"SIG": "- Remboursement Capital Dette", "Montant": f"-{remb_16:,.0f} €", "% Prod": f"{remb_16/tp*100:.1f} %", "Norme": "4 - 8 %"},
            {"SIG": "= AUTOFINANCEMENT NET", "Montant": f"{autofin_net:+,.0f} €", "% Prod": "-", "Norme": "Norme >= 0 €"},
        ])
        st.dataframe(df_sig, hide_index=True, use_container_width=True)

    with c_sig2:
        st.markdown("**Indicateurs Patrimoniaux & Comparatif**")
        st.metric("Trésorerie de Sécurité", f"{j_treso} jours", f"Moyenne : {normes['jours_treso']} jours", delta_color="normal" if j_treso >= 60 else "inverse")
        st.metric("Règle d'Or Immobilière", f"{ro_solde:+,.0f} €", "Norme légale : >= 0 €", delta_color="normal" if ro_ok else "inverse")
        df_bench = pd.DataFrame([
            {"Indicateur": "Forfait public / élève", "Établissement": f"{forfait_eleve_reel:,.0f} €", "Norme Profil": f"{normes['forfait_eleve']:,.0f} €"},
            {"Indicateur": "Contrib. familles / élève", "Établissement": f"{contrib_eleve_reel:,.0f} €", "Norme Profil": f"{normes['contrib_eleve']:,.0f} €"},
        ])
        st.dataframe(df_bench, hide_index=True, use_container_width=True)

    afficher_synthese_unique(
        "Situation à date (TBI)",
        f"L'établissement clôture l'exercice avec un Autofinancement Net de {autofin_net:+,.0f} € après remboursement de ses prêts. L'EBE ressort à {tebe:.1f} % (contre {normes['taux_ebe']} % en moyenne sectorielle).",
        f"Le forfait versé par la collectivité représente {forfait_eleve_reel:,.0f} €/élève (contre {normes['forfait_eleve']} € en moyenne), constituant une base opposable pour négocier la future convention.",
        f"L'objectif immédiat pour l'année en cours est {'de sanctuariser ce matelas pour investir.' if autofin_net >= 0 else 'de corriger ce déficit d autofinancement avant d envisager de nouveaux travaux.'}"
    )

# ------------------------------------------
# ONGLET 3 : SCALPEL (Choix prévisionnels)
# ------------------------------------------
with onglets[2]:
    st.subheader("Où faire ses choix ? Les indicateurs de pilotage pour l'EPRD")
    afficher_aide_pedagogique_onglet("Comment lire ces centres de coûts ?", [
        ("Administration (%)", "Permet de vérifier si le back-office ne coûte pas trop cher par rapport au terrain (Vie scolaire)."),
        ("Taux de couverture Restauration", "Une restauration équilibrée (100 %) signifie que vous ne prenez pas sur l'argent de la pédagogie pour payer les repas ou l'internat."),
        ("UFA vs CFC", "Permet de s'assurer qu'une activité hors-contrat (formation continue) ne brûle pas l'argent généré par l'apprentissage.")
    ])

    st.markdown("#### 1. Structure de l'encadrement RH")
    crh1, crh2 = st.columns([1.45, 1])
    with crh1:
        df_rh = pd.DataFrame([
            {"Service (Hors profs État)": "Profs privés / hors contrat", "Montant": f"{ms_prive:,.0f} €", "Poids": f"{ms_prive/max(1,ms_totale)*100:.1f} %"},
            {"Service (Hors profs État)": "Vie scolaire & AESH", "Montant": f"{ms_vie_scol:,.0f} €", "Poids": f"{ms_vie_scol/max(1,ms_totale)*100:.1f} %"},
            {"Service (Hors profs État)": "Administration & Direction", "Montant": f"{ms_admin:,.0f} €", "Poids": f"{poids_admin_ms:.1f} % (Moy. {normes['poids_admin']} %)"},
            {"Service (Hors profs État)": "Technique & Restauration", "Montant": f"{ms_tech:,.0f} €", "Poids": f"{ms_tech/max(1,ms_totale)*100:.1f} %"},
        ])
        st.dataframe(df_rh, hide_index=True, use_container_width=True)
    with crh2:
        st.bar_chart(pd.DataFrame({"Service": ["Profs", "Vie Scolaire", "Admin", "Technique"], "Montant": [ms_prive, ms_vie_scol, ms_admin, ms_tech]}).set_index("Service"), color="#1d4ed8")

    st.divider()

    cs1, cs2 = st.columns(2)
    with cs1:
        st.markdown("#### 2. Restauration & Internat")
        st.metric("Marge sur coûts directs", f"{marge_resto:+,.0f} €", f"Couverture : {tx_couv_resto:.1f} % (Cible 100%)", delta_color="normal" if marge_resto >= 0 else "inverse")
        if marge_resto < 0:
            st.error(f"**Action requise au CA :** La pension perd {abs(marge_resto):,.0f} €. Il faut augmenter les tarifs de **+{abs(marge_resto)/max(1,internes_tot):,.0f} €/famille/an** au prochain vote.")

    with cs2:
        st.markdown("#### 3. Effort Pédagogique Direct")
        st.metric("Budget Pédagogique / Élève", f"{b_peda_eleve:,.0f} € / élève", f"Moy. {normes['type_court']} : {normes['b_peda']} €", delta_color="normal" if b_peda_eleve >= normes["b_peda"]*0.85 else "inverse")
        if b_peda_eleve < normes["b_peda"]*0.85:
            st.warning("Vous dépensez moins pour la pédagogie que la moyenne de votre strate.")

    afficher_synthese_unique(
        "Indicateurs de pilotage annuel (Le Scalpel)",
        f"L'administration pèse {poids_admin_ms:.1f} % de la masse salariale (moyenne : {normes['poids_admin']} %). La maintenance bâtiment coûte {maint_m2:.1f} €/m².",
        f"La restauration/internat couvre ses charges à {tx_couv_resto:.1f} % ({marge_resto:+,.0f} €) et l'effort pédagogique est de {b_peda_eleve:,.0f} €/élève.",
        "Pour le budget de la rentrée prochaine : utiliser ces ratios pour justifier au CA la révision de la tarification cantine ou la non-remplacement d'un départ administratif."
    )

# ------------------------------------------
# ONGLET 4 : PROSPECTIVE (Projet à 5 ans)
# ------------------------------------------
with onglets[3]:
    st.subheader("Où allons-nous ? Le projet financier à 5 ans")
    afficher_aide_pedagogique_onglet("Tester les investissements", [
        ("PPI (Plan Pluriannuel)", "Travaux lourds prévus sur les 5 prochaines années (rénovation thermique, sécurité)."),
        ("OPEX induits", "Nouveaux frais de fonctionnement (chauffage, nettoyage) liés aux nouveaux bâtiments."),
        ("Condition de vote", "Un PPI n'est votable que si, à la fin des 5 ans, la trésorerie reste positive et le désendettement sous les 8 ans.")
    ])

    sp1, sp2, sp3, sp4 = st.columns(4)
    with sp1:
        st.markdown("**Hypothèses Fonctionnement**")
        tx_ms_proj = st.slider("Évolution Salaires (%/an)", 0.5, 5.0, 2.2, 0.1)
        tx_ext_proj = st.slider("Inflation Énergie/Achats (%/an)", 0.5, 5.0, 1.8, 0.1)
    with sp2:
        st.markdown("**Hypothèses Recettes**")
        tx_el_proj = st.slider("Évolution Effectifs élèves (%/an)", -3.0, 4.0, 0.5, 0.1)
        tx_forf_proj = st.slider("Hausse Forfaits/Familles (%/an)", 0.0, 5.0, 2.0, 0.1)
    with sp3:
        st.markdown("**Projet d'Investissement (PPI)**")
        ppi_annuel = st.slider("Enveloppe Travaux (M€/an)", 0.0, 2.5, 0.35, 0.05)
        taux_subv_ppi = st.slider("Subventions obtenues (%)", 0, 70, 30, 5)
    with sp4:
        st.markdown("**Impacts & Dette**")
        opex_ppi_pct = st.slider("OPEX induits travaux (%)", -2.0, 5.0, 1.5, 0.5)
        duree_emprunt = st.selectbox("Durée emprunts futurs", [15, 20, 25], index=1)

    ans_p = ["2026", "2027", "2028", "2029", "2030"]
    ppi_reel = ppi_annuel * 0.85
    subv_ppi_an = ppi_reel * (taux_subv_ppi / 100.0)
    emprunt_ppi_an = max(0.0, (ppi_reel - subv_ppi_an) * 0.65)
    autofin_ppi_an = max(0.0, (ppi_reel - subv_ppi_an) * 0.35)

    p_list, c_list, caf_list, det_list, des_list, tr_list = [], [], [], [], [], []
    curr_p, curr_ms, curr_autres_ch = tp/1e6, ms_totale/1e6, (ch_achats + ch_ext_hors_achats + (0 if source_reelle else ch_ufa + ch_cfc))/1e6
    curr_amo, curr_fin, curr_det, curr_remb, curr_treso = amort_68/1e6, fin_66/1e6, dette_16/1e6, remb_16/1e6, treso_51/1e6
    opex_cumul = 0.0

    for _ in ans_p:
        curr_p *= (1 + tx_el_proj/100.0) * (1 + tx_forf_proj/100.0)
        curr_ms *= (1 + tx_ms_proj/100.0)
        curr_autres_ch *= (1 + tx_ext_proj/100.0)
        opex_cumul += ppi_reel * (opex_ppi_pct / 100.0)
        curr_amo += ppi_reel / 20.0
        curr_fin += emprunt_ppi_an * 0.035

        tot_c_opex = curr_ms + curr_autres_ch + opex_cumul + curr_amo + curr_fin
        curr_caf = (curr_p - tot_c_opex) + curr_amo
        curr_det = max(0.0, curr_det - curr_remb + emprunt_ppi_an)
        curr_treso += curr_caf - (curr_remb + emprunt_ppi_an/duree_emprunt) - autofin_ppi_an
        
        p_list.append(round(curr_p, 2)); c_list.append(round(tot_c_opex, 2))
        caf_list.append(round(curr_caf, 2)); det_list.append(round(curr_det, 2))
        des_list.append(round(curr_det/max(0.01, curr_caf), 1)); tr_list.append(round(curr_treso, 2))

    df_proj = pd.DataFrame({"Année": ans_p, "Produits (M€)": p_list, "Charges+OPEX (M€)": c_list, "CAF (M€)": caf_list, "Dette (M€)": det_list, "Désendettement (ans)": des_list, "Trésorerie (M€)": tr_list})
    
    kp1, kp2, kp3, kp4 = st.columns(4)
    kp1.metric("CAF en 2030", f"{caf_list[-1]:.2f} M€", f"Taux : {(caf_list[-1]/p_list[-1]*100):.1f} %")
    kp2.metric("Désendettement 2030", f"{des_list[-1]:.1f} ans", "Seuil max : 8 ans", delta_color="normal" if des_list[-1] <= 8 else "inverse")
    kp3.metric("Dette en 2030", f"{det_list[-1]:.2f} M€")
    kp4.metric("Trésorerie 2030", f"{tr_list[-1]:.2f} M€", "Condition absolue : > 0", delta_color="normal" if tr_list[-1] > 0 else "inverse")

    gp_c1, gp_c2 = st.columns(2)
    with gp_c1:
        st.markdown("**Cadrage Fonctionnement (Produits vs Charges)**")
        st.line_chart(df_proj.set_index("Année")[["Produits (M€)", "Charges+OPEX (M€)"]])
    with gp_c2:
        st.markdown("**Cadrage Sécurité (CAF & Trésorerie)**")
        st.line_chart(df_proj.set_index("Année")[["CAF (M€)", "Trésorerie (M€)"]])

    afficher_synthese_unique(
        "Projet Financier à 5 ans",
        f"Avec un programme de travaux de {ppi_reel:.2f} M€/an, la trésorerie atteindrait {tr_list[-1]:.2f} M€ en 2030, et la capacité de désendettement serait de {des_list[-1]:.1f} ans.",
        f"Ce scénario suppose d'obtenir {taux_subv_ppi} % de subventions et de limiter l'évolution salariale à +{tx_ms_proj:.1f} %/an.",
        f"Si la trésorerie 2030 devient négative ou le désendettement dépasse 8 ans, le CA devra au choix : reporter les travaux, relever la contribution des familles, ou réduire drastiquement l'effet volume RH actuel."
    )
