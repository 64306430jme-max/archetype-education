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
    page_title="Archétype Éducation — Audit & Pilotage Financier",
    page_icon="🎓",
    layout="wide"
)

# ==========================================
# RÉFÉRENTIEL & NORMES
# ==========================================
def get_normes_etablissement(type_etab):
    if "1er degré" in type_etab:
        return {"type_court": "1er degré", "taux_caf_cible": 6.5, "jours_treso": 90, "tx_internat": 0, "budget_pedago_cible": 70}
    elif "Collège" in type_etab:
        return {"type_court": "Collège", "taux_caf_cible": 7.5, "jours_treso": 90, "tx_internat": 5, "budget_pedago_cible": 100}
    elif "Lycée GT" in type_etab:
        return {"type_court": "Lycée GT/Pro", "taux_caf_cible": 8.0, "jours_treso": 90, "tx_internat": 12, "budget_pedago_cible": 130}
    elif "Agricole" in type_etab:
        return {"type_court": "Lycée Agricole", "taux_caf_cible": 8.5, "jours_treso": 75, "tx_internat": 65, "budget_pedago_cible": 150}
    elif "Maison Familiale" in type_etab:
        return {"type_court": "MFR / Alternance", "taux_caf_cible": 8.0, "jours_treso": 75, "tx_internat": 75, "budget_pedago_cible": 150}
    else:
        return {"type_court": "Ensemble mixte", "taux_caf_cible": 7.5, "jours_treso": 90, "tx_internat": 8, "budget_pedago_cible": 110}

def fiche_pedagogique(bouton_label, titre, definition, normes=None):
    with st.popover(bouton_label):
        st.markdown(f"### {titre}")
        st.markdown(f"**Analyse :** {definition}")
        if normes:
            st.markdown("**Seuils de vigilance :**")
            for n in normes:
                st.markdown(f"* {n}")

# ==========================================
# 1. BARRE LATÉRALE : PARAMÈTRES & SOUS-DÉTAILS
# ==========================================
st.sidebar.markdown("## 🎓 Archétype Éducation")
type_etab = st.sidebar.selectbox(
    "Profil de l'établissement",
    [
        "Ensemble scolaire mixte (École + Collège + Lycée)",
        "Lycée Agricole Temps Plein (CNEAP / MASA)",
        "Maison Familiale Rurale / Alternance (UNMFREO)",
        "2nd degré (Lycée GT / Pro)",
        "2nd degré (Collège)",
        "1er degré (École maternelle / élémentaire)"
    ]
)
is_agricole = ("Agricole" in type_etab) or ("Maison Familiale" in type_etab)
normes_etab = get_normes_etablissement(type_etab)
etablissement = st.sidebar.text_input("Nom de l'établissement", "Lycée Polyvalent Saint-Éloi")

activer_ufa_cfc = st.sidebar.checkbox("Intégrer UFA (Apprentissage) & CFC", value=(True if "Lycée" in type_etab or is_agricole else False))

st.sidebar.markdown("### 1. Macro-Données Scolaires")
eleves_tot = st.sidebar.number_input("Élèves formation initiale", min_value=1, value=650, step=10)
taux_internat = st.sidebar.slider("Taux d'internes / demi-pensionnaires (%)", 0, 100, int(normes_etab["tx_internat"]), 5)
internes_tot = int(round(eleves_tot * taux_internat / 100))

forfaits_m = st.sidebar.number_input("Forfaits / Subventions de fonctionnement (€)", value=750000.0, step=10000.0)
contrib_m = st.sidebar.number_input("Contributions familles (scolarité pure) (€)", value=450000.0, step=10000.0)
resto_m = st.sidebar.number_input("Facturation Restauration & Internat (€)", value=480000.0, step=10000.0)
ms_globale = st.sidebar.number_input("Masse Salariale globale (Asso) (€)", value=820000.0, step=10000.0)
ext_global = st.sidebar.number_input("Charges Externes globales (Achats, fluides...) (€)", value=510000.0, step=10000.0)

with st.sidebar.expander("🔍 Sous-détails analytiques (Le Scalpel)"):
    st.caption("Isolez les coûts pour analyser la restauration, l'énergie et la pédagogie.")
    achats_denrees = st.number_input("Dont Achats de denrées alimentaires (€)", value=180000.0, step=5000.0)
    ms_resto = st.number_input("Dont Salaires cuisine & surveillance internat (€)", value=140000.0, step=5000.0)
    fluides_tot = st.number_input("Dont Dépenses d'Énergie (Eau, Gaz, Élec) (€)", value=120000.0, step=5000.0)
    budget_pedago = st.number_input("Dont Budget Pédagogique (Fournitures, projets, intervenants) (€)", value=75000.0, step=5000.0)

prod_ufa, ch_ufa, prod_cfc, ch_cfc, apprentis_tot, stagiaires_tot = 0.0, 0.0, 0.0, 0.0, 0, 0
if activer_ufa_cfc:
    st.sidebar.markdown("### 2. Pôle UFA & CFC")
    apprentis_tot = st.sidebar.number_input("Effectif Apprentis (UFA)", value=120, step=5)
    prod_ufa = st.sidebar.number_input("Produits UFA (NPEC, Taxe app.) (€)", value=780000.0, step=10000.0)
    ch_ufa = st.sidebar.number_input("Charges directes UFA (€)", value=640000.0, step=10000.0)
    stagiaires_tot = st.sidebar.number_input("Stagiaires Formation Continue (CFC / an)", value=80, step=5)
    prod_cfc = st.sidebar.number_input("Produits CFC (€)", value=120000.0, step=10000.0)
    ch_cfc = st.sidebar.number_input("Charges directes CFC (€)", value=135000.0, step=10000.0)

st.sidebar.markdown("### 3. Patrimoine & Dette")
loyers_aep = st.sidebar.number_input("Loyers immobiliers versés à l'AEP (€)", value=65000.0, step=5000.0)
amort_m = st.sidebar.number_input("Dotations amortissements (681) (€)", value=180000.0, step=5000.0)
fin_m = st.sidebar.number_input("Intérêts des emprunts (66) (€)", value=45000.0, step=5000.0)
dette_m = st.sidebar.number_input("Encours de dette immobilière au 31/12 (€)", value=1250000.0, step=25000.0)
remb_m = st.sidebar.number_input("Remboursement annuel capital (€)", value=115000.0, step=5000.0)
treso_m = st.sidebar.number_input("Trésorerie globale disponible (€)", value=550000.0, step=10000.0)


# ==========================================
# CALCULS GLOBAUX & SCALPEL
# ==========================================
prod_scol = forfaits_m + contrib_m + resto_m
ch_scol = ms_globale + ext_global
total_prod = prod_scol + prod_ufa + prod_cfc
total_ch = ch_scol + ch_ufa + ch_cfc + loyers_aep + amort_m + fin_m
ch_dec = max(1.0, total_ch - amort_m)

res_net = total_prod - total_ch
caf = res_net + amort_m
autofin = caf - remb_m
j_treso = int(round((treso_m / ch_dec) * 365))

# Scalpel 1 : Restauration & Internat
quote_part_fluides = fluides_tot * 0.30 if fluides_tot > 0 else 0
charges_resto_directes = achats_denrees + ms_resto + quote_part_fluides
marge_resto = resto_m - charges_resto_directes

# Scalpel 2 : Immobilier & Dette
annuite_dette = remb_m + fin_m
poids_annuite = (annuite_dette / total_prod * 100) if total_prod > 0 else 0
cap_desend = (dette_m / caf) if caf > 0 else 99.9
ro_solde = contrib_m - (amort_m + fin_m + loyers_aep)
ro_ok = ro_solde >= 0

# Scalpel 3 & 4 : Charges Fixes, RH & Pédagogie
poids_fluides = (fluides_tot / total_ch * 100) if total_ch > 0 else 0
poids_ms = (ms_globale / total_ch * 100) if total_ch > 0 else 0
budget_pedago_par_eleve = budget_pedago / max(1, eleves_tot)
cible_pedago = normes_etab["budget_pedago_cible"]

# ==========================================
# AFFICHAGE PRINCIPAL (ONGLETS)
# ==========================================
st.title("Archétype Éducation — Audit Financier")
st.caption(f"{etablissement} • {normes_etab['type_court']} • {eleves_tot} Élèves • {internes_tot} Usagers Cantine/Internat")

onglets = st.tabs([
    "📊 Macro & UFA", 
    "🍽️ Restauration & Internat", 
    "🧱 Immobilier & Dette", 
    "⚙️ RH, Fixes & Pédagogie", 
    "🔮 Prospective", 
    "📑 Note PDF"
])

# --- ONGLET 1 : MACRO & UFA ---
with onglets[0]:
    st.subheader("Bilan Consolidé (Fonctionnement Général)")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Produits", f"{(total_prod/1e6):.2f} M€")
    k2.metric("Résultat Net", f"{(res_net/1e6):+.2f} M€")
    k3.metric("CAF", f"{(caf/1e6):.2f} M€", f"Taux CAF : {(caf/total_prod*100):.1f} %")
    k4.metric("Trésorerie", f"{j_treso} jours", f"{treso_m/1e6:.2f} M€")

    if activer_ufa_cfc:
        st.divider()
        st.subheader("Analyse de la Marge : Apprentissage & Formation Continue")
        m_ufa = prod_ufa - ch_ufa
        m_cfc = prod_cfc - ch_cfc
        c1, c2 = st.columns(2)
        c1.metric("Marge Nette UFA (Apprentissage)", f"{m_ufa:,.0f} €".replace(",", " "), f"Pour {apprentis_tot} apprentis")
        c2.metric("Marge Nette CFC (Formation Continue)", f"{m_cfc:,.0f} €".replace(",", " "), f"Pour {stagiaires_tot} stagiaires", delta_color="normal" if m_cfc>=0 else "inverse")
        if m_ufa > 0 > m_cfc:
            st.error(f"**Alerte :** Le déficit de la Formation Continue (-{abs(m_cfc):,.0f} €) détruit une partie de l'excédent dégagé par l'Apprentissage (+{m_ufa:,.0f} €).")

# --- ONGLET 2 : RESTAURATION & INTERNAT ---
with onglets[1]:
    r1, r2 = st.columns([0.9, 0.1])
    with r1:
        st.subheader("Audit Analytique : Hébergement & Restauration")
    with r2:
        fiche_pedagogique("ℹ️", "Marge Restauration / Internat", "Les services annexes (cantine, internat) doivent s'autofinancer. S'ils sont déficitaires, la dotation pédagogique est illégalement déviée pour financer les repas.", ["Couverture cible : ≥ 100%", "Le prix du repas doit couvrir les achats + salaires cuisiniers + énergie."])
    
    df_resto = pd.DataFrame([
        {"Poste": "Achats de denrées alimentaires", "Montant (€)": achats_denrees},
        {"Poste": "Salaires (Cuisine & Surveillance interne)", "Montant (€)": ms_resto},
        {"Poste": "Quote-part Fluides (Énergie cantine/internat)", "Montant (€)": quote_part_fluides}
    ])
    
    c_r1, c_r2 = st.columns([1, 1])
    with c_r1:
        st.markdown(f"**Recettes facturées aux familles : {resto_m:,.0f} €**".replace(",", " "))
        st.dataframe(df_resto, hide_index=True, use_container_width=True)
        tx_couverture = (resto_m / charges_resto_directes * 100) if charges_resto_directes > 0 else 0
        if marge_resto >= 0:
            st.success(f"**Service excédentaire (+{marge_resto:,.0f} €) :** Le tarif couvre {tx_couverture:.1f}% des charges directes. Pas de subventionnement croisé.")
        else:
            st.error(f"**Déficit d'exploitation (-{abs(marge_resto):,.0f} €) :** Les recettes ne couvrent que {tx_couverture:.1f}% des charges directes. La pédagogie subventionne la cantine/internat.")
    
    with c_r2:
        st.bar_chart(pd.DataFrame({
            "Indicateur": ["Recettes Familles", "Charges Directes Cumulées"],
            "Montant (€)": [resto_m, charges_resto_directes]
        }).set_index("Indicateur"), color="#f59e0b")

# --- ONGLET 3 : IMMOBILIER & DETTE ---
with onglets[2]:
    i1, i2 = st.columns([0.9, 0.1])
    with i1:
        st.subheader("Patrimoine, Règle d'Or & Endettement")
    with i2:
        fiche_pedagogique("ℹ️", "Indicateurs Patrimoniaux", "Mesure la capacité de l'établissement à entretenir ses murs sans s'asphyxier financièrement.", ["Capacité de désendettement : < 8 ans", "L'annuité ne doit pas dépasser la CAF."])

    col_i1, col_i2, col_i3 = st.columns(3)
    col_i1.metric("Capacité de Désendettement", f"{cap_desend:.1f} ans", "Cible bancaire : < 8 ans", delta_color="normal" if cap_desend < 8 else "inverse")
    col_i2.metric("Poids de l'Annuité (Capital + Intérêts)", f"{poids_annuite:.1f} %", "Des produits d'exploitation")
    col_i3.metric("Marge d'Autofinancement Net", f"{(autofin):,.0f} €".replace(",", " "), "CAF après remboursement dette")
    
    st.divider()
    st.markdown("#### Vérification de la Règle d'Or Immobilière")
    if ro_ok:
        st.success(f"**Règle d'Or respectée (+{ro_solde:,.0f} €) :** Les contributions des familles ({contrib_m:,.0f} €) couvrent largement le bloc Amortissements + Intérêts + Loyers AEP ({(amort_m + fin_m + loyers_aep):,.0f} €).")
    else:
        st.warning(f"**Tension Règle d'Or ({ro_solde:,.0f} €) :** Le bloc immobilier n'est pas couvert par les contributions familles. Manque : {int(round(abs(ro_solde)/eleves_tot))} € / élève.")

# --- ONGLET 4 : CHARGES FIXES, RH & PÉDAGOGIE ---
with onglets[3]:
    st.subheader("Analyse de l'Effort Pédagogique et des Charges Incompressibles")
    c_f1, c_f2, c_f3 = st.columns(3)
    
    with c_f1:
        st.markdown("#### Budget Pédagogique")
        st.metric("Budget Pédago. / Élève", f"{budget_pedago_par_eleve:,.0f} €".replace(",", " "), f"Cible observatoire : ~{cible_pedago} €", delta_color="normal" if budget_pedago_par_eleve >= cible_pedago else "inverse")
        if budget_pedago_par_eleve < cible_pedago * 0.8:
            st.error(f"⚠️ **Alerte Qualité :** Avec {budget_pedago_par_eleve:,.0f} €/élève (contre ~{cible_pedago} € en moyenne nationale), l'établissement sous-investit dans le matériel pédagogique et les sorties pour équilibrer le reste de ses charges.")
        elif budget_pedago_par_eleve >= cible_pedago:
            st.success("✅ Excellent niveau d'investissement pédagogique direct.")
        else:
            st.info("🔄 Effort pédagogique légèrement sous la moyenne mais acceptable.")
            
    with c_f2:
        st.markdown("#### Facture Énergétique (Fluides)")
        st.metric("Poids des Fluides", f"{poids_fluides:.1f} %", f"{fluides_tot:,.0f} € au total".replace(",", " "), delta_color="inverse" if poids_fluides > 10 else "normal")
        if poids_fluides > 12:
            st.warning("⚠️ **Alerte Énergie :** Facture très élevée. Un audit thermique est recommandé.")

    with c_f3:
        st.markdown("#### Rigidité Salariale")
        st.metric("Poids Masse Salariale (Asso)", f"{poids_ms:.1f} %", f"{ms_globale:,.0f} € au total".replace(",", " "), delta_color="inverse" if poids_ms > 55 else "normal")
        if poids_ms > 50:
            st.warning("⚠️ **Vigilance RH :** Forte rigidité structurelle.")

# --- ONGLET 5 : PROSPECTIVE ---
with onglets[4]:
    st.subheader("Simulateur Quinquennal 2026-2030")
    s1, s2, s3 = st.columns(3)
    tx_el = s1.slider("Évolution annuelle effectifs élèves (%)", -3.0, 4.0, 0.5)
    tx_forf = s1.slider("Revalorisation Forfaits Publics (%/an)", 0.0, 5.0, 2.0)
    tx_ch = s2.slider("Inflation des charges fixes et Salaires (%/an)", 1.0, 6.0, 3.0)
    ppi_m = s3.slider("Plan Pluriannuel d'Investissement (M€/an)", 0.0, 2.0, 0.3)

    ans = ["2026", "2027", "2028", "2029", "2030"]
    p_p, p_c, p_caf, p_t = [], [], [], []
    c_p, c_c, c_tres = total_prod, total_ch, treso_m
    
    for _ in ans:
        c_p = c_p * (1 + tx_el/100) * (1 + tx_forf/100)
        c_c = c_c * (1 + tx_ch/100) + (ppi_m * 1e6 * 0.04)
        c_caf = (c_p - c_c) + amort_m + (ppi_m * 1e6 * 0.04)
        c_tres = c_tres + c_caf - remb_m - (ppi_m * 1e6 * 0.5)
        
        p_p.append(c_p/1e6)
        p_c.append(c_c/1e6)
        p_caf.append(c_caf/1e6)
        p_t.append(c_tres/1e6)

    st.dataframe(pd.DataFrame({"Année": ans, "Produits (M€)": p_p, "Charges (M€)": p_c, "CAF (M€)": p_caf, "Trésorerie (M€)": p_t}), hide_index=True, use_container_width=True)

# --- ONGLET 6 : PDF ---
with onglets[5]:
    st.subheader("Note de Synthèse & Recommandations")
    note = f"""AUDIT FINANCIER — {etablissement.upper()}

1. ÉQUILIBRE GLOBAL
La Capacité d'Autofinancement (CAF) s'établit à {caf/1e6:.2f} M€, soit un taux de {(caf/total_prod*100):.1f} %. La trésorerie de sécurité représente {j_treso} jours.

2. PÔLES ANALYTIQUES (LE SCALPEL)
- Pédagogie : Le budget pédagogique direct s'élève à {budget_pedago_par_eleve:,.0f} € / élève (Norme de référence : ~{cible_pedago} €).
- Restauration / Internat : {'Excédentaire' if marge_resto >= 0 else 'Déficitaire, la cantine est subventionnée par le budget enseignement'}. Marge directe = {marge_resto:,.0f} €.
- Immobilier : Règle d'Or {'respectée' if ro_ok else 'non respectée'}. La capacité de désendettement est de {cap_desend:.1f} ans.
- Charges Fixes : Les fluides représentent {poids_fluides:.1f} % du budget ({"Alerte" if poids_fluides > 12 else "Maîtrisé"}).
"""
    st.text_area("Copier pour votre rapport :", note, height=250)
