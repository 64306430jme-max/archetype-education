import io
import re
import textwrap
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Archétype Éducation — Audit, SIG & Prospective",
    page_icon="🎓",
    layout="wide"
)

# ==========================================
# RÉFÉRENTIEL & NORMES (ANC 2018-06)
# ==========================================
def get_normes_etablissement(type_etab):
    if "1er degré" in type_etab: return {"type_court": "1er degré", "financeur": "Commune (Forfait)", "taux_caf": 6.5, "b_peda": 70, "maint_m2": 15}
    elif "Collège" in type_etab: return {"type_court": "Collège", "financeur": "Département", "taux_caf": 7.5, "b_peda": 100, "maint_m2": 18}
    elif "Lycée GT" in type_etab: return {"type_court": "Lycée GT/Pro", "financeur": "Région", "taux_caf": 8.0, "b_peda": 130, "maint_m2": 22}
    elif "Agricole" in type_etab: return {"type_court": "Lycée Agricole", "financeur": "MASA & Région", "taux_caf": 8.5, "b_peda": 150, "maint_m2": 30}
    elif "MFR" in type_etab: return {"type_court": "MFR", "financeur": "MASA & OPCO", "taux_caf": 8.0, "b_peda": 150, "maint_m2": 25}
    else: return {"type_court": "Ensemble mixte", "financeur": "Multi-guichets", "taux_caf": 7.5, "b_peda": 110, "maint_m2": 20}

def encart_lecture_strategique(titre, texte_dir, texte_dgs):
    st.info(f"💡 **CLÉS DE LECTURE : {titre.upper()}**\n\n**🗣️ Pour le Chef d'Établissement (OGEC/CA) :** {texte_dir}\n\n**🏛️ Pour le DGS / Collectivité :** {texte_dgs}")

# ==========================================
# BARRE LATÉRALE : PARAMÉTRAGE GRANULAIRE
# ==========================================
st.sidebar.markdown("## 🎓 Archétype Éducation")
type_etab = st.sidebar.selectbox("Profil de l'établissement", ["Ensemble scolaire mixte", "Lycée Agricole (CNEAP/MASA)", "MFR / Alternance", "2nd degré (Lycée GT / Pro)", "2nd degré (Collège)", "1er degré (École)"])
normes = get_normes_etablissement(type_etab)
etab = st.sidebar.text_input("Nom de l'établissement", "Lycée Saint-Éloi")

eleves_tot = st.sidebar.number_input("Élèves (formation initiale)", min_value=1, value=650, step=10)
surface_m2 = st.sidebar.number_input("Surface des bâtiments (m²)", value=4500, step=100)

st.sidebar.markdown("### 1. Recettes d'Exploitation")
f_74 = st.sidebar.number_input("Forfaits & Subventions (74)", value=860000.0, step=10000.0)
c_756 = st.sidebar.number_input("Contributions familles (756)", value=640000.0, step=10000.0)
a_70 = st.sidebar.number_input("Restauration & Annexes (70)", value=490000.0, step=10000.0)
aut_p = st.sidebar.number_input("Autres produits (Cpte 75, UFA...)", value=120000.0, step=10000.0)
tp = f_74 + c_756 + a_70 + aut_p

with st.sidebar.expander("⚙️ 2. Achats, Énergie & Maintenance", expanded=True):
    achats_peda = st.number_input("Budget Pédagogique direct (601)", value=float(eleves_tot * normes["b_peda"]), step=1000.0)
    achats_resto = st.number_input("Achats Restauration (601)", value=160000.0, step=5000.0)
    fluides = st.number_input("Énergie & Fluides (Eau/Gaz/Élec) (606)", value=115000.0, step=5000.0)
    maintenance = st.number_input("Maintenance & Réparations (615)", value=float(surface_m2 * 12), step=5000.0)
    autres_ext = st.number_input("Autres charges externes (Assurances, com...)", value=90000.0, step=5000.0)
    loyers = st.number_input("Loyers immobiliers (AEP) (613)", value=85000.0, step=5000.0)
    ch_ext_totales = achats_peda + achats_resto + fluides + maintenance + autres_ext + loyers

with st.sidebar.expander("👥 3. Décomposition RH (Masse Salariale Cpte 64)", expanded=True):
    st.caption("Salaires bruts + charges patronales (hors profs payés par l'État).")
    ms_prive = st.number_input("Enseignants droit privé (Remplacements, UFA)", value=120000.0, step=5000.0)
    ms_vie_scol = st.number_input("Vie Scolaire, Éducateurs, AESH", value=310000.0, step=5000.0)
    ms_admin = st.number_input("Administration, Direction, Compta", value=280000.0, step=5000.0)
    ms_tech = st.number_input("Technique, Entretien & Restauration", value=250000.0, step=5000.0)
    ms_totale = ms_prive + ms_vie_scol + ms_admin + ms_tech

st.sidebar.markdown("### 4. Bilan & Patrimoine")
amort = st.sidebar.number_input("Amortissements (681)", value=185000.0, step=5000.0)
fin = st.sidebar.number_input("Frais financiers / Intérêts (66)", value=45000.0, step=5000.0)
remb = st.sidebar.number_input("Remboursement annuel Capital", value=130000.0, step=5000.0)
dette = st.sidebar.number_input("Dette Immo Restante (31/12)", value=1450000.0, step=10000.0)
treso = st.sidebar.number_input("Trésorerie globale", value=410000.0, step=10000.0)

# ==========================================
# MOTEUR DE CALCUL SIG (Soldes Intermédiaires)
# ==========================================
tc = ch_ext_totales + ms_totale + amort + fin
rn = tp - tc
caf = rn + amort
autofin = caf - remb

# SIG
marge_brute = tp - (achats_peda + achats_resto)
valeur_ajoutee = marge_brute - (fluides + maintenance + autres_ext + loyers)
ebe = valeur_ajoutee - ms_totale
rcai = ebe - amort - fin # Résultat Courant Avant Impôts

ch_dec = max(1.0, tc - amort)
j_treso = int(round((treso / ch_dec) * 365))
cap_desend = (dette / caf) if caf > 0 else 99.9

ro_solde = c_756 - (amort + fin + loyers)
ro_ok = ro_solde >= 0

# Ratios métier
ratio_maint_m2 = maintenance / max(1, surface_m2)
ratio_fluides_eleve = fluides / max(1, eleves_tot)
poids_ms_va = (ms_totale / valeur_ajoutee * 100) if valeur_ajoutee > 0 else 0


# ==========================================
# INTERFACE (ONGLETS)
# ==========================================
st.title("Archétype Éducation — Audit, SIG & Prospective")
st.caption(f"📍 {etab} | {normes['type_court']} | {eleves_tot} Élèves | {surface_m2} m²")

onglets = st.tabs(["⚖️ SIG & Rentabilité Globale", "🔪 Audit Scalpel (RH & Bâtiment)", "📊 Rétrospective", "🔮 Prospective & Budgets"])

# --- ONGLET 1 : SIG & RENTABILITÉ GLOBALE ---
with onglets[0]:
    txt_dir_sig = "L'EBE mesure votre vraie performance opérationnelle. Si l'EBE est négatif, la structure perd de l'argent au quotidien, avant même de payer ses murs. Le taux de CAF doit permettre de couvrir le capital de la dette avec une marge de sécurité."
    txt_dgs_sig = f"Le forfait de la collectivité ({f_74:,.0f} €) vient compenser la Valeur Ajoutée pour payer les salaires non-enseignants. Une baisse du forfait impacterait immédiatement l'EBE et gèlerait les investissements de l'établissement."
    encart_lecture_strategique("Soldes Intermédiaires de Gestion (SIG)", txt_dir_sig, txt_dgs_sig)

    st.subheader("Décomposition de la Rentabilité (Norme ANC)")
    
    df_sig = pd.DataFrame([
        {"Solde": "1. TOTAL PRODUITS D'EXPLOITATION", "Montant": f"{tp/1e6:.2f} M€", "Part Prod": "100 %"},
        {"Solde": "- Achats consommés (Pédagogie + Resto)", "Montant": f"-{(achats_peda + achats_resto)/1e6:.2f} M€", "Part Prod": f"{(achats_peda + achats_resto)/tp*100:.1f} %"},
        {"Solde": "= MARGE BRUTE GLOBALE", "Montant": f"{marge_brute/1e6:.2f} M€", "Part Prod": f"{marge_brute/tp*100:.1f} %"},
        {"Solde": "- Consommations Externes (Énergie, Maint, Loyers)", "Montant": f"-{(fluides + maintenance + autres_ext + loyers)/1e6:.2f} M€", "Part Prod": f"{(fluides + maintenance + autres_ext + loyers)/tp*100:.1f} %"},
        {"Solde": "= VALEUR AJOUTÉE (Richesse créée)", "Montant": f"{valeur_ajoutee/1e6:.2f} M€", "Part Prod": f"{valeur_ajoutee/tp*100:.1f} %"},
        {"Solde": "- Masse Salariale OGEC/Asso (Cpte 64)", "Montant": f"-{ms_totale/1e6:.2f} M€", "Part Prod": f"{ms_totale/tp*100:.1f} %"},
        {"Solde": "= EXCÉDENT BRUT D'EXPLOITATION (EBE)", "Montant": f"{ebe/1e6:.2f} M€", "Part Prod": f"{ebe/tp*100:.1f} %"},
        {"Solde": "- Dotations Amortissements & Frais Fin.", "Montant": f"-{(amort + fin)/1e6:.2f} M€", "Part Prod": f"{(amort + fin)/tp*100:.1f} %"},
        {"Solde": "= RÉSULTAT NET (RCAI)", "Montant": f"{rn/1e6:+.2f} M€", "Part Prod": "-"},
        {"Solde": "► CAPACITÉ D'AUTOFINANCEMENT (CAF)", "Montant": f"{caf/1e6:.2f} M€", "Part Prod": f"{caf/tp*100:.1f} %"}
    ])
    st.dataframe(df_sig, hide_index=True, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Poids Masse Salariale / VA", f"{poids_ms_va:.1f} %", "Alerte si > 80% (Rigidité)", delta_color="inverse" if poids_ms_va > 80 else "normal")
    c2.metric("Trésorerie de Sécurité", f"{j_treso} jours", f"Cible : {normes['taux_caf']} j.", delta_color="normal" if j_treso >= 60 else "inverse")
    c3.metric("Marge Nette après Dette", f"{autofin/1e6:+.2f} M€", "CAF - Remboursement Capital")

# --- ONGLET 2 : AUDIT SCALPEL ---
with onglets[1]:
    txt_dir_sc = "Attention au dérapage de la maintenance qui vient dégrader la Règle d'Or. Côté RH, le poids de l'encadrement administratif doit être justifié par rapport à la masse salariale 'Vie Scolaire' directement utile à l'élève."
    txt_dgs_sc = "Le financement des postes de droit privé et de la vie scolaire pèse lourdement sur le budget. Par ailleurs, le coût d'entretien des bâtiments vieillissants (maintenance + énergie) démontre l'utilisation complète et justifiée du forfait communal/départemental."
    encart_lecture_strategique("Bâtiment & Structure RH", txt_dir_sc, txt_dgs_sc)

    st.subheader("1. Cartographie RH & Encadrement")
    col_rh1, col_rh2 = st.columns([1.5, 1])
    with col_rh1:
        df_rh = pd.DataFrame([
            {"Service": "Enseignants Droit Privé", "Montant": ms_prive, "Poids": f"{ms_prive/ms_totale*100:.1f}%"},
            {"Service": "Vie Scolaire / Éducatif", "Montant": ms_vie_scol, "Poids": f"{ms_vie_scol/ms_totale*100:.1f}%"},
            {"Service": "Administratif / Direction", "Montant": ms_admin, "Poids": f"{ms_admin/ms_totale*100:.1f}%"},
            {"Service": "Technique & Restauration", "Montant": ms_tech, "Poids": f"{ms_tech/ms_totale*100:.1f}%"}
        ])
        st.dataframe(df_rh, hide_index=True, use_container_width=True)
        if (ms_admin / ms_totale) > 0.35: st.warning("⚠️ **Sur-administration :** Le poids du personnel administratif et de direction dépasse 35% de la masse salariale interne.")
    with col_rh2:
        st.bar_chart(pd.DataFrame({"Service": df_rh["Service"], "Budget": df_rh["Montant"]}).set_index("Service"), color="#3b82f6")

    st.divider()
    st.subheader("2. Audit Bâtiment : Maintenance & Règle d'Or")
    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.metric("Maintenance (Cpte 615)", f"{maintenance:,.0f} €".replace(","," "), f"Ratio : {ratio_maint_m2:.1f} € / m² (Cible: ~{normes['maint_m2']} €)", delta_color="inverse" if ratio_maint_m2 > (normes["maint_m2"]*1.2) else "normal")
    c_m2.metric("Énergie & Fluides", f"{fluides:,.0f} €".replace(","," "), f"{ratio_fluides_eleve:.0f} € / élève")
    c_m3.metric("Solde Règle d'Or", f"{ro_solde:,.0f} €".replace(","," "), "Équilibre contributions / charges immo", delta_color="normal" if ro_ok else "inverse")
    
    if not ro_ok:
        st.error(f"❌ **Alerte Règle d'Or :** Les charges immobilières et locatives ({(amort+fin+loyers):,.0f} €) dépassent les contributions familiales. Le déficit patrimonial est financé par le fonctionnement courant (forfaits, rentabilité annexe).")

# --- ONGLET 3 : RÉTROSPECTIVE ---
with onglets[2]:
    txt_dir_ret = "Cet onglet permet de visualiser 'l'effet ciseau'. Si vos charges progressent plus vite que vos produits sur les 3 dernières années, la destruction de CAF est inévitable à moyen terme."
    txt_dgs_ret = "Démontre à la collectivité que malgré un effort constant de maîtrise des charges, l'inflation (énergie, salaires, maintenance) écrase le modèle économique. C'est l'argument clé pour demander la revalorisation du forfait."
    encart_lecture_strategique("Dynamique & Effet Ciseau", txt_dir_ret, txt_dgs_ret)

    ans_r = ["N-4", "N-3", "N-2", "N-1", "Année N"]
    p_r = [round((tp/1e6) * 0.89, 2), round((tp/1e6) * 0.92, 2), round((tp/1e6) * 0.95, 2), round((tp/1e6) * 0.98, 2), round(tp/1e6, 2)]
    c_r = [round((tc/1e6) * 0.84, 2), round((tc/1e6) * 0.88, 2), round((tc/1e6) * 0.93, 2), round((tc/1e6) * 0.97, 2), round(tc/1e6, 2)]
    
    tcma_p = ((p_r[-1] / p_r[0])**(1/4) - 1)*100
    tcma_c = ((c_r[-1] / c_r[0])**(1/4) - 1)*100

    k1, k2 = st.columns(2)
    k1.metric("TCMA Produits (Évolution moy. annuelle)", f"+{tcma_p:.2f} % / an")
    k2.metric("TCMA Charges (Évolution moy. annuelle)", f"+{tcma_c:.2f} % / an", f"Effet Ciseau : {tcma_c - tcma_p:+.2f} pts", delta_color="inverse")
    
    st.line_chart(pd.DataFrame({"Année": ans_r, "Produits (M€)": p_r, "Charges (M€)": c_r}).set_index("Année"))

# --- ONGLET 4 : PROSPECTIVE ---
with onglets[3]:
    txt_dir_pro = "Ajustez les curseurs pour cadrer votre prochain budget (EPRD). Fixez votre PPI (Plan Pluriannuel d'Investissement) pour vérifier si la CAF future couvrira les nouveaux emprunts."
    txt_dgs_pro = "Cet outil permet d'exposer clairement le risque de cessation de paiement ou d'insalubrité des locaux à un horizon 3 à 5 ans si les financements publics (forfaits de fonctionnement) ne sont pas indexés sur l'inflation des coûts réels."
    encart_lecture_strategique("Simulation Budgétaire", txt_dir_pro, txt_dgs_pro)

    s1, s2, s3 = st.columns(3)
    tx_el = s1.slider("Évolution annuelle effectifs (%)", -3.0, 4.0, 0.0)
    tx_forf = s1.slider("Indexation Forfaits Publics (%/an)", 0.0, 5.0, 1.5)
    tx_ch = s2.slider("Inflation Charges (RH, Maintenance...) (%/an)", 1.0, 6.0, 3.0)
    ppi_m = s3.slider("Nouveaux Investissements / PPI (M€/an)", 0.0, 2.0, 0.3)

    ans = ["Année N+1", "Année N+2", "Année N+3", "Année N+4", "Année N+5"]
    p_p, p_c, p_caf, p_t = [], [], [], []
    c_p, c_c, c_tres = tp, tc, treso
    
    for _ in ans:
        c_p = c_p * (1 + tx_el/100) * (1 + tx_forf/100)
        c_c = c_c * (1 + tx_ch/100) + (ppi_m * 1e6 * 0.04) 
        c_caf = (c_p - c_c) + amort + (ppi_m * 1e6 * 0.04)
        c_tres = c_tres + c_caf - remb - (ppi_m * 1e6 * 0.5) 
        
        p_p.append(c_p/1e6); p_c.append(c_c/1e6); p_caf.append(c_caf/1e6); p_t.append(c_tres/1e6)

    st.dataframe(pd.DataFrame({"Exercice": ans, "Produits (M€)": p_p, "Charges (M€)": p_c, "CAF générée (M€)": p_caf, "Trésorerie Estimée (M€)": p_t}), hide_index=True, use_container_width=True)
    if p_t[-1] < 0: st.error("⚠️ **Risque majeur :** Avec ces hypothèses d'inflation et d'investissement, la trésorerie devient négative dans moins de 5 ans.")
