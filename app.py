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
    page_title="Archétype Éducation — Pilotage OGEC & Enseignement Agricole | Cabinet QUINZE",
    page_icon="🎓",
    layout="wide"
)

# ==========================================
# RÉFÉRENTIEL & NORMES (FNOGEC / ÉDUCATION NATIONALE / MASA)
# ==========================================
def get_normes_etablissement(type_etab):
    if "1er degré" in type_etab:
        return {
            "type_court": "1er degré (École)",
            "regime": "Loi Debré (Art. L. 442-5 Code de l'éducation)",
            "financeur_principal": "Commune (Forfait communal obligatoire)",
            "forfait_ref_eleve": 880,
            "detail_forfait": "Moy. FNOGEC : 1 205 €/maternelle (vigilance < 1 300 €) | 645 €/élémentaire",
            "contrib_ref_eleve": 420,
            "taux_caf_cible": 6.5,
            "jours_treso_cible": 90,
            "poids_ms_cible": 48.0,
            "poids_fluides_cible": 18.0,
            "taux_internat_ref": 0,
        }
    elif "Collège" in type_etab:
        return {
            "type_court": "2nd degré (Collège)",
            "regime": "Loi Debré (Art. L. 442-9 Code de l'éducation)",
            "financeur_principal": "Département (Forfait externat) + État",
            "forfait_ref_eleve": 647,
            "detail_forfait": "Moy. FNOGEC part Département : 647 €/collégien (+ dotation État)",
            "contrib_ref_eleve": 580,
            "taux_caf_cible": 7.5,
            "jours_treso_cible": 90,
            "poids_ms_cible": 44.0,
            "poids_fluides_cible": 19.0,
            "taux_internat_ref": 5,
        }
    elif "Lycée GT" in type_etab:
        return {
            "type_court": "2nd degré (Lycée GT / Pro)",
            "regime": "Loi Debré (Art. L. 442-9 Code de l'éducation)",
            "financeur_principal": "Région (Forfait externat) + État",
            "forfait_ref_eleve": 803,
            "detail_forfait": "Moy. FNOGEC part Région : 803 €/lycéen (+ dotation État selon filière)",
            "contrib_ref_eleve": 690,
            "taux_caf_cible": 8.0,
            "jours_treso_cible": 90,
            "poids_ms_cible": 42.0,
            "poids_fluides_cible": 20.0,
            "taux_internat_ref": 12,
        }
    elif "Lycée Agricole" in type_etab:
        return {
            "type_court": "Lycée Agricole (Temps plein)",
            "regime": "Code rural Art. L. 813-8 (Tutelle MASA / CNEAP)",
            "financeur_principal": "État / MASA (Subvention fonctionnement) + Région & Taxe d'apprentissage",
            "forfait_ref_eleve": 2450,
            "detail_forfait": "Subvention fonctionnement MASA par filière (hors enseignants payés par MASA)",
            "contrib_ref_eleve": 720,
            "taux_caf_cible": 8.5,
            "jours_treso_cible": 75,
            "poids_ms_cible": 46.0,
            "poids_fluides_cible": 26.0,
            "taux_internat_ref": 65,
        }
    elif "Maison Familiale" in type_etab:
        return {
            "type_court": "MFR / Alternance",
            "regime": "Code rural Art. L. 813-9 (Rythme approprié / UNMFREO)",
            "financeur_principal": "État / MASA (Subvention globale) + Taxe d'apprentissage & Région",
            "forfait_ref_eleve": 4100,
            "detail_forfait": "Subvention globale MASA incluant la rémunération des moniteurs",
            "contrib_ref_eleve": 680,
            "taux_caf_cible": 8.0,
            "jours_treso_cible": 75,
            "poids_ms_cible": 64.0,
            "poids_fluides_cible": 22.0,
            "taux_internat_ref": 75,
        }
    else:
        return {
            "type_court": "Ensemble scolaire mixte",
            "regime": "Loi Debré multi-niveaux (École + Collège + Lycée)",
            "financeur_principal": "Multi-guichets (Commune + Département + Région + État)",
            "forfait_ref_eleve": 760,
            "detail_forfait": "Moyenne pondérée collectivités (1 205 € mat. / 645 € élém. / 647 € col. / 803 € lyc.)",
            "contrib_ref_eleve": 560,
            "taux_caf_cible": 7.5,
            "jours_treso_cible": 90,
            "poids_ms_cible": 45.0,
            "poids_fluides_cible": 19.0,
            "taux_internat_ref": 8,
        }


# ==========================================
# COMPOSANT PÉDAGOGIQUE (INFOBULLES & NORMES)
# ==========================================
def fiche_pedagogique(bouton_label, titre, definition, formule=None, normes=None, lecture_ogec=None):
    with st.popover(bouton_label):
        st.markdown(f"### {titre}")
        st.markdown(f"**En clair :** {definition}")
        if formule:
            st.markdown(f"**Mode de calcul (ANC 2018-06) :** `{formule}`")
        if normes:
            st.markdown("**Normes, moyennes nationales & seuils d'alerte :**")
            for n in normes:
                st.markdown(f"* {n}")
        if lecture_ogec:
            st.info(f"**Lecture Direction / Collectivité :** {lecture_ogec}")


# ==========================================
# LECTEUR AUTOMATIQUE DES BALANCES ASSOCIATIVES (ANC 2018-06)
# ==========================================
def _read_tabular_file(file_obj):
    name = getattr(file_obj, "name", "balance_ogec.csv")
    raw_bytes = file_obj.getvalue() if hasattr(file_obj, "getvalue") else file_obj.read()
    if name.lower().endswith((".xlsx", ".xls")):
        try:
            return pd.read_excel(io.BytesIO(raw_bytes))
        except Exception:
            return None
    for enc in ("utf-8", "latin-1", "cp1252"):
        for sep in (";", ",", "\t"):
            try:
                tmp = pd.read_csv(io.BytesIO(raw_bytes), sep=sep, encoding=enc)
                if tmp.shape[1] >= 2:
                    return tmp
            except Exception:
                continue
    return None


def _to_num(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace("\xa0", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce"
    ).fillna(0.0)


def parse_balance_ogec(file_obj):
    name = getattr(file_obj, "name", "balance_2025.csv")
    year_match = re.search(r"(20[1-3]\d)", name)
    annee = year_match.group(1) if year_match else None

    df = _read_tabular_file(file_obj)
    if df is None or df.empty:
        return None

    cols_lower = {c: str(c).strip().lower() for c in df.columns}
    compte_col = next(
        (c for c, cl in cols_lower.items() if any(k in cl for k in ("compte", "article", "nature", "imputation"))),
        df.columns[0]
    )
    libelle_col = next(
        (c for c, cl in cols_lower.items() if any(k in cl for k in ("libell", "intitul", "désignation", "designation"))),
        None
    )

    debit_col = next((c for c, cl in cols_lower.items() if any(k in cl for k in ("débit", "debit"))), None)
    credit_col = next((c for c, cl in cols_lower.items() if any(k in cl for k in ("crédit", "credit"))), None)
    solde_col = next((c for c, cl in cols_lower.items() if any(k in cl for k in ("solde", "montant"))), None)

    raw_comptes = df[compte_col].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    debits = _to_num(df[debit_col]) if debit_col else (_to_num(df[solde_col]).abs() if solde_col else pd.Series(0.0, index=df.index))
    credits = _to_num(df[credit_col]) if credit_col else (_to_num(df[solde_col]).abs() if solde_col else pd.Series(0.0, index=df.index))

    is_numeric_code = raw_comptes.str.match(r"^\d{2,}$")
    if libelle_col is not None:
        lib_lower = df[libelle_col].astype(str).str.lower()
        is_not_total_label = ~lib_lower.str.contains(
            r"\b(?:sous[-\s]?total|total\s+g[ée]n[ée]ral|total\s+classe|totaux)\b",
            regex=True
        )
    else:
        is_not_total_label = pd.Series(True, index=df.index)

    valid_mask = is_numeric_code & is_not_total_label
    nb_lignes_ignorees = int((~valid_mask).sum())

    comptes_valides = raw_comptes[valid_mask]
    debits_valides = debits[valid_mask]
    credits_valides = credits[valid_mask]

    lengths = comptes_valides.str.len()
    fixed_width = (lengths.nunique() == 1 and lengths.iloc[0] >= 5) if len(lengths) > 0 else False
    if fixed_width:
        norm_codes = comptes_valides.apply(lambda c: c.rstrip("0") if len(c.rstrip("0")) >= 2 else c[:2])
    else:
        norm_codes = comptes_valides

    unique_norm = set(norm_codes.unique())
    parent_codes = {
        c for c in unique_norm
        if any(other != c and other.startswith(c) for other in unique_norm)
    }
    is_leaf = ~norm_codes.isin(parent_codes)
    nb_sous_totaux_filtres = int((~is_leaf).sum()) + nb_lignes_ignorees

    comptes = comptes_valides[is_leaf]
    debits = debits_valides[is_leaf]
    credits = credits_valides[is_leaf]

    def sum_prefix(prefixes, side="debit"):
        mask = comptes.apply(lambda x: any(x.startswith(p) for p in prefixes))
        return float(debits[mask].sum() if side == "debit" else credits[mask].sum())

    forfaits_74 = sum_prefix(["74"], "credit")
    contrib_756 = sum_prefix(["756", "7061"], "credit")
    activites_70 = sum_prefix(["70"], "credit") - sum_prefix(["7061"], "credit")
    autres_prod = sum_prefix(["75", "76", "77", "78", "79"], "credit") - sum_prefix(["756"], "credit")

    loyers_aep = sum_prefix(["613"], "debit")
    charges_ext = max(0.0, sum_prefix(["60", "61", "62", "63"], "debit") - loyers_aep)
    masse_sal = sum_prefix(["64"], "debit")
    autres_ch = sum_prefix(["65", "67"], "debit")
    charges_fin = sum_prefix(["66"], "debit")
    dot_amort = sum_prefix(["68"], "debit")

    dette_immo = sum_prefix(["164", "168"], "credit")
    remb_cap = sum_prefix(["164", "168"], "debit")
    treso_51 = sum_prefix(["512", "514", "53"], "debit")

    total_prod = forfaits_74 + contrib_756 + max(0.0, activites_70) + max(0.0, autres_prod)
    total_ch = charges_ext + loyers_aep + masse_sal + autres_ch + charges_fin + dot_amort

    if total_prod <= 0 and total_ch <= 0:
        return None

    res_net = total_prod - total_ch
    caf = res_net + dot_amort

    return {
        "fichier": name,
        "annee": annee,
        "forfaits_74": forfaits_74,
        "contrib_756": contrib_756,
        "activites_70": max(0.0, activites_70),
        "autres_prod": max(0.0, autres_prod),
        "total_prod": total_prod,
        "charges_ext": charges_ext,
        "loyers_aep": loyers_aep,
        "masse_sal": masse_sal,
        "autres_ch": autres_ch,
        "charges_fin": charges_fin,
        "dot_amort": dot_amort,
        "total_ch": total_ch,
        "res_net": res_net,
        "caf": caf,
        "dette_immo": dette_immo,
        "remb_cap": remb_cap,
        "treso_51": treso_51,
        "nb_sous_totaux_filtres": nb_sous_totaux_filtres,
    }


def generate_template_ogec_csv(is_agricole=False):
    if is_agricole:
        return (
            "Compte;Libellé;Débit;Crédit\n"
            "7411;Subvention de fonctionnement État / MASA (Art. L.813-8 / L.813-9);0;840000\n"
            "7412;Subventions Région, Taxe d'apprentissage & aides formation;0;190000\n"
            "7561;Contributions scolaires des familles;0;245000\n"
            "7062;Pension, internat, restauration & produits ateliers/exploitation;0;680000\n"
            "6061;Denrées internat, énergie/chauffage, fournitures ateliers;345000;0\n"
            "6132;Loyer immobilier versé à l'Association Propriétaire (AEP);45000;0\n"
            "6152;Maintenance plateaux techniques, assurances & entretien bâtiments;190000;0\n"
            "6411;Masse salariale association (vie scolaire, internat, ateliers/moniteurs);890000;0\n"
            "6511;Cotisations réseau (CNEAP / UNMFREO) et gestion courante;65000;0\n"
            "6611;Intérêts des emprunts immobiliers & matériels;74000;0\n"
            "6811;Dotations aux amortissements bâtiments, internat & matériels;260000;0\n"
            "1641;Emprunts bancaires (Amorti Débit / Encours Crédit);165000;1950000\n"
            "5121;Disponibilités bancaires au 31/12;410000;0\n"
        ).encode("utf-8")
    return (
        "Compte;Libellé;Débit;Crédit\n"
        "7411;Forfait communal (1er degré - Commune);0;310000\n"
        "7412;Forfait d'externat Collège (Département);0;300000\n"
        "7413;Forfait d'externat Lycée (Région);0;250000\n"
        "7561;Contributions des familles (scolarité);0;640000\n"
        "7062;Restauration scolaire, périscolaire et activités annexes;0;490000\n"
        "7541;Dons, mécénat et subventions privées;0;45000\n"
        "6061;Achats alimentation cantine, énergie, eau et fournitures;480000;0\n"
        "6132;Loyer immobilier versé à l'Association Propriétaire (AEP);85000;0\n"
        "6152;Entretien immobilier, maintenance et assurances;190000;0\n"
        "6411;Salaires et charges personnel OGEC (hors enseignants État);960000;0\n"
        "6511;Cotisations réseau (UDOGEC / UROGEC) et gestion courante;75000;0\n"
        "6611;Intérêts des emprunts immobiliers;68000;0\n"
        "6811;Dotations aux amortissements immobiliers et mobiliers;225000;0\n"
        "1641;Emprunts bancaires immobiliers (Amorti Débit / Encours Crédit);155000;1650000\n"
        "5121;Disponibilités bancaires au 31/12;460000;0\n"
    ).encode("utf-8")


# ==========================================
# MOTEUR D'ANALYSE PROSPECTIVE
# ==========================================
def generer_analyse_ogec(
    etablissement, type_etab, is_agricole, is_mfr, eleves_tot, eleves_2030,
    prod_init, caf_init, dette_init,
    prod_p, ch_p, res_p, caf_p, autofin_p, dette_p, treso_p, jours_treso_p,
    tx_eleves, tx_forfaits, delta_contrib_eur, tx_ms_epnl, tx_fluides,
    ppi_immo_m, tx_subv_immo, duree_pret_immo, regle_or_ok_2030
):
    taux_caf_2030 = (caf_p[-1] / prod_p[-1] * 100) if prod_p[-1] > 0 else 0.0
    min_jours = min(jours_treso_p)
    delta_eleves = eleves_2030 - eleves_tot

    if res_p[-1] < 0 or autofin_p[-1] < 0 or min_jours < 30:
        niveau = "critique"
        badge = "ALERTE ROUGE — DÉFICIT D'EXPLOITATION OU IMPASSE DE TRÉSORERIE (< 30 J)"
        couleur_hex = "#991b1b"
        fond_hex = "#fef2f2"
        bord_hex = "#fca5a5"
    elif taux_caf_2030 < 6.5 or min_jours < 60 or not regle_or_ok_2030:
        niveau = "vigilance"
        badge = "VIGILANCE RENFORCÉE — TENSION SUR LA CAF, LA RÈGLE D'OR OU LA TRÉSORERIE (< 60 J)"
        couleur_hex = "#92400e"
        fond_hex = "#fffbeb"
        bord_hex = "#fcd34d"
    else:
        niveau = "soutenable"
        badge = "TRAJECTOIRE SOUTENABLE — ÉQUILIBRE EXPLOITATION & PATRIMOINE VALIDÉ"
        couleur_hex = "#065f46"
        fond_hex = "#ecfdf5"
        bord_hex = "#6ee7b7"

    diag = [
        f"Résultat & CAF 2030 : Résultat net projeté à {res_p[-1]:+.2f} M€ et Capacité d'Autofinancement à {caf_p[-1]:.2f} M€ ({taux_caf_2030:.1f} % des produits) ; autofinancement net après dette à {autofin_p[-1]:+.2f} M€.",
        f"Effectifs & Liquidité : Évolution de {delta_eleves:+d} élèves d'ici 2030 ({eleves_2030} élèves) ; point bas de trésorerie à {min_jours} jours de charges décaissables (encours dette 2030 : {dette_p[-1]:.2f} M€)."
    ]

    if is_agricole:
        guichet_txt = "subventions MASA (Art. L. 813-9) et taxe d'apprentissage" if is_mfr else "dotations MASA (Art. L. 813-8) et aides Région/apprentissage"
        rh_txt = "moniteurs/formateurs et personnels de vie résidentielle" if is_mfr else "personnels internat, restauration et plateaux techniques"
        piliers = [
            f"1. Financements MASA, Région & Apprentissage : Sécuriser +{tx_forfaits:.1f} %/an sur les {guichet_txt} en valorisant les effectifs par filière ({eleves_2030} élèves en 2030).",
            f"2. Équilibre Internat, Loyers AEP & Plateaux : Indexer les tarifs de pension et contributions familles (+{int(delta_contrib_eur)} €/élève/an) pour couvrir les charges fixes d'hébergement, les amortissements et loyers immobiliers.",
            f"3. Masse Salariale & Charges Fixes : Contenir la dérive salariale ({rh_txt}) à +{tx_ms_epnl:.1f} %/an et déployer un plan de sobriété énergétique sur les internats (+{tx_fluides:.1f} %/an).",
            f"4. Investissement & Trésorerie : Mobiliser ≥ {tx_subv_immo} % de subventions Région/FEADER sur la PPI ({ppi_immo_m:.2f} M€/an sur {duree_pret_immo} ans) et lisser les acomptes MASA (point bas tréso : {min_jours} j)."
        ]
    else:
        piliers = [
            f"1. Dialogue Collectivités (Forfaits publics) : Indexer les forfaits publics (+{tx_forfaits:.1f} %/an) sur la base des coûts constatés dans l'enseignement public de référence.",
            f"2. Règle d'Or Immobilière (Amort. + Intérêts + Loyers AEP) : Calibrer la contribution des familles (+{int(delta_contrib_eur)} €/élève/an) pour couvrir intégralement l'ensemble des charges immobilières et locatives.",
            f"3. Masse Salariale EPNL & Fluides : Piloter la masse salariale de droit privé à +{tx_ms_epnl:.1f} %/an et maîtriser l'inflation énergétique/restauration à +{tx_fluides:.1f} %/an.",
            f"4. PPI Immobilière & Sécurité Trésorerie : Phraser la PPI ({ppi_immo_m:.2f} M€/an, prêts sur {duree_pret_immo} ans) pour maintenir la trésorerie au-dessus du seuil prudentiel FNOGEC (point bas : {min_jours} j vs cible 90-120 j)."
        ]

    return {
        "niveau": niveau,
        "badge": badge,
        "couleur_hex": couleur_hex,
        "fond_hex": fond_hex,
        "bord_hex": bord_hex,
        "diag": diag,
        "piliers": piliers
    }


# ==========================================
# GÉNÉRATEUR DE SYNTHÈSE PDF EXÉCUTIVE
# ==========================================
def _draw_box(ax, x, y, w, h, facecolor="#ffffff", edgecolor="#cbd5e1", lw=1.0, radius=0.012):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=facecolor, edgecolor=edgecolor, linewidth=lw,
        transform=ax.transAxes
    )
    ax.add_patch(box)


def build_ogec_pdf(
    etablissement, type_etab, is_agricole, eleves_tot, total_prod_m, total_forfaits_m, contrib_familles_m,
    restauration_m, autres_prod_m, masse_sal_m, charges_ext_m, loyers_aep_m, dot_amort_m, charges_fin_m,
    res_net_m, caf_m, remb_cap_m, autofin_m, dette_immo_m, treso_m, jours_treso,
    regle_or_ok, annees_proj, prod_p, ch_p, caf_p, treso_p, analyse_dict
):
    taux_caf = (caf_m / total_prod_m * 100) if total_prod_m > 0 else 0.0
    cout_eleve = int(round((masse_sal_m + charges_ext_m + loyers_aep_m + dot_amort_m + charges_fin_m) * 1e6 / max(1, eleves_tot)))
    bloc_immo_m = dot_amort_m + charges_fin_m + loyers_aep_m

    buf = io.BytesIO()
    fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.add_patch(Rectangle((0, 0.915), 1, 0.085, facecolor="#0f172a", transform=ax.transAxes))
    ax.add_patch(Rectangle((0, 0.911), 1, 0.004, facecolor="#d97706", transform=ax.transAxes))
    sous_titre_pdf = "ENSEIGNEMENT AGRICOLE SOUS CONTRAT (CODE RURAL)" if is_agricole else "DIAGNOSTIC ANC 2018-06 & PROSPECTIVE OGEC"
    ax.text(0.04, 0.962, f"ARCHÉTYPE ÉDUCATION  |  {sous_titre_pdf}",
            color="white", fontsize=10.5, fontweight="bold")
    ax.text(0.04, 0.932, f"ÉTABLISSEMENT : {etablissement.upper()}  •  {type_etab.upper()} ({eleves_tot} ÉLÈVES)",
            color="#cbd5e1", fontsize=8.0)

    kpis = [
        ("CAPACITÉ AUTOFIN. (CAF)", f"{caf_m:.2f} M€", f"Taux CAF : {taux_caf:.1f} % (Cible 6-8,5 %)", "#059669" if taux_caf >= 6.5 else "#d97706"),
        ("RÉSULTAT NET COMPTABLE", f"{res_net_m:+.2f} M€", f"Autofin. net : {autofin_m:+.2f} M€", "#059669" if res_net_m >= 0 else "#dc2626"),
        ("TRÉSORERIE NETTE", f"{treso_m:.2f} M€", f"Couverture : {jours_treso} j (Cible 90-120 j)", "#1d4ed8" if jours_treso >= 60 else "#dc2626"),
        ("ENCOURS DETTE IMMO", f"{dette_immo_m:.2f} M€", f"Coût association / élève : {cout_eleve:,} €".replace(",", " "), "#0f172a"),
    ]
    for i, (kt, kv, ks, kc) in enumerate(kpis):
        kx = 0.04 + i * 0.233
        _draw_box(ax, kx, 0.815, 0.218, 0.084, facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.0)
        ax.text(kx + 0.012, 0.880, kt, fontsize=7.0, fontweight="bold", color="#475569")
        ax.text(kx + 0.012, 0.845, kv, fontsize=12.5, fontweight="bold", color=kc)
        ax.text(kx + 0.012, 0.823, ks, fontsize=6.8, color="#64748b")

    _draw_box(ax, 0.04, 0.515, 0.45, 0.285, facecolor="#ffffff", edgecolor="#cbd5e1", lw=1.1)
    ax.add_patch(Rectangle((0.04, 0.762), 0.45, 0.038, facecolor="#1e293b", transform=ax.transAxes))
    ax.text(0.055, 0.775, "1. COMPTE DE RÉSULTAT & CAF (ANC 2018-06)", color="white", fontsize=8.5, fontweight="bold")

    lbl_subv = "Subventions MASA, Région & Apprentissage (74)" if is_agricole else "Forfaits publics (Commune/Dept/Région - 74)"
    lbl_act = "Familles, internat & ateliers/exploitation (756/70)" if is_agricole else "Contributions familles & restauration (756/70)"
    val_act = contrib_familles_m + restauration_m + autres_prod_m

    rows_cr = [
        (lbl_subv, f"{total_forfaits_m:.2f} M€", False, "#0f172a"),
        (lbl_act, f"{val_act:.2f} M€", False, "#0f172a"),
        ("= Total Produits d'Exploitation", f"{total_prod_m:.2f} M€", True, "#1d4ed8"),
        ("- Personnel association (64) & Charges ext. (60-63)", f"-{(masse_sal_m + charges_ext_m):.2f} M€", False, "#475569"),
        ("- Amort. (68), Intérêts (66) & Loyers AEP (613)", f"-{bloc_immo_m:.2f} M€", False, "#475569"),
        ("= Résultat Net Comptable", f"{res_net_m:+.2f} M€", True, "#059669" if res_net_m >= 0 else "#dc2626"),
        ("= Capacité d'Autofinancement (CAF)", f"{caf_m:.2f} M€", True, "#b45309"),
    ]
    yp = 0.732
    for lbl, val, bld, col in rows_cr:
        if bld:
            ax.add_patch(Rectangle((0.048, yp - 0.009), 0.434, 0.029, facecolor="#f1f5f9", transform=ax.transAxes))
        ax.text(0.055, yp, lbl, fontsize=7.3, fontweight="bold" if bld else "normal", color="#1e293b")
        ax.text(0.478, yp, val, ha="right", fontsize=7.8, fontweight="bold" if bld else "normal", color=col)
        yp -= 0.034

    ro_bg = "#ecfdf5" if regle_or_ok else "#fffbeb"
    ro_bd = "#6ee7b7" if regle_or_ok else "#fcd34d"
    ro_fg = "#065f46" if regle_or_ok else "#92400e"
    _draw_box(ax, 0.51, 0.695, 0.45, 0.105, facecolor=ro_bg, edgecolor=ro_bd, lw=1.1)
    titre_bloc2 = "2. COUVERTURE IMMOBILIÈRE & LOYERS AEP" if is_agricole else "2. VÉRIFICATION DE LA RÈGLE D'OR OGEC"
    ax.text(0.525, 0.778, titre_bloc2, fontsize=8.1, fontweight="bold", color=ro_fg)
    ax.text(0.525, 0.752, f"• Contributions familles ({contrib_familles_m:.2f} M€) vs Immo/Loyers AEP ({bloc_immo_m:.2f} M€)", fontsize=7.1, color="#1e293b")
    ax.text(0.525, 0.728, f"• Solde section patrimoniale : {(contrib_familles_m - bloc_immo_m):+.2f} M€", fontsize=7.3, fontweight="bold", color=ro_fg)
    pied_bloc2 = "• Étanchéité dotation pédagogique MASA / immobilier." if is_agricole else "• Les forfaits publics restent intégralement dédiés à l'externat."
    ax.text(0.525, 0.706, pied_bloc2, fontsize=7.0, color="#475569")

    ax1 = fig.add_axes([0.545, 0.525, 0.40, 0.145])
    ax1.plot(annees_proj, prod_p, marker="o", color="#2563eb", lw=2, label="Produits")
    ax1.plot(annees_proj, ch_p, marker="s", color="#dc2626", lw=2, label="Charges")
    ax1.set_xticks(annees_proj)
    ax1.tick_params(labelsize=7.0)
    ax1.grid(True, linestyle="--", alpha=0.4)
    ax1.legend(loc="upper left", fontsize=6.8)

    ax.text(0.04, 0.485, "3. TRAJECTOIRE PROSPECTIVE QUINQUENNALE (2026-2030)", fontsize=8.4, fontweight="bold", color="#0f172a")
    tbl_ax = fig.add_axes([0.04, 0.335, 0.92, 0.140])
    tbl_ax.axis("off")
    t_data = [
        ["Produits d'exploitation (M€)"] + [f"{v:.2f}" for v in prod_p],
        ["Charges d'exploitation incl. amort. (M€)"] + [f"{v:.2f}" for v in ch_p],
        ["Capacité d'Autofinancement — CAF (M€)"] + [f"{v:.2f}" for v in caf_p],
        ["Trésorerie disponible au 31/12 (M€)"] + [f"{v:.2f}" for v in treso_p],
    ]
    tbl = tbl_ax.table(cellText=t_data, colLabels=["Indicateurs"] + [str(a) for a in annees_proj], loc="center", cellLoc="center", colWidths=[0.42] + [0.116] * 5)
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(7.4)
    tbl.scale(1, 1.30)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor("#cbd5e1")
        if r == 0:
            cell.set_facecolor("#1e293b")
            cell.get_text().set_color("white")
            cell.get_text().set_weight("bold")
        elif c == 0:
            cell.get_text().set_ha("left")

    _draw_box(ax, 0.04, 0.056, 0.92, 0.265, facecolor=analyse_dict["fond_hex"], edgecolor=analyse_dict["bord_hex"], lw=1.1)
    ax.text(0.055, 0.303, f"FEUILLE DE ROUTE CA & DIALOGUE FINANCEURS : {analyse_dict['badge']}",
            fontsize=7.7, fontweight="bold", color=analyse_dict["couleur_hex"])
    all_lines = [f"• {d}" for d in analyse_dict["diag"]] + analyse_dict["piliers"]
    y_curr = 0.282
    for idx_l, raw_line in enumerate(all_lines):
        is_reco = idx_l >= 2
        for w_line in textwrap.wrap(raw_line, width=128):
            ax.text(0.055, y_curr, w_line, fontsize=6.85,
                    fontweight="bold" if is_reco else "normal",
                    color=analyse_dict["couleur_hex"] if is_reco else "#1e293b")
            y_curr -= 0.0145
        y_curr -= 0.0025

    ax.plot([0.04, 0.96], [0.042, 0.042], color="#cbd5e1", lw=0.8)
    ax.text(0.04, 0.025, "Archétype Éducation (Référentiel ANC 2018-06 / FNOGEC / Code rural)  •  Cabinet QUINZE", fontsize=7.6, color="#64748b")
    ax.text(0.96, 0.025, "Page 1/1", ha="right", fontsize=7.8, fontweight="bold", color="#475569")

    fig.savefig(buf, format="pdf")
    plt.close(fig)
    return buf.getvalue()


# ==========================================
# 1. BARRE LATÉRALE : PARAMÈTRES ÉTABLISSEMENT
# ==========================================
st.sidebar.markdown("## 🎓 Archétype Éducation")
st.sidebar.caption("Pilotage Établissements sous Contrat (ANC 2018-06)")

type_etab = st.sidebar.selectbox(
    "Profil & Tutelle de l'établissement",
    [
        "Ensemble scolaire mixte (École + Collège + Lycée — Loi Debré)",
        "1er degré (École maternelle / élémentaire — Loi Debré)",
        "2nd degré (Collège — Loi Debré)",
        "2nd degré (Lycée GT / Pro — Loi Debré)",
        "Lycée Agricole Temps Plein (Art. L. 813-8 Code rural — Tutelle MASA)",
        "Maison Familiale Rurale / Alternance (Art. L. 813-9 Code rural — Tutelle MASA)"
    ]
)
is_agricole = ("Agricole" in type_etab) or ("Maison Familiale" in type_etab)
is_mfr = ("Maison Familiale" in type_etab)
normes_etab = get_normes_etablissement(type_etab)
st.sidebar.caption(f"Cadre : **{normes_etab['regime']}**")

nom_defaut = (
    "MFR des Vallées (Alternance)" if is_mfr
    else ("Lycée Agricole Saint-Éloi (CNEAP)" if is_agricole else "OGEC Ensemble Scolaire Saint-Joseph")
)
etablissement = st.sidebar.text_input("Nom de l'association gestionnaire", nom_defaut, key=f"nom_{normes_etab['type_court']}")

st.sidebar.markdown("### 1. Ingestion Balance Associative")
fichiers_balances = st.sidebar.file_uploader(
    "Glisser vos balances ANC 2018-06 (.csv, .xlsx)",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=True,
    help="Exports Sage, EBP, Quadratus ou Assoconnect. Les sous-totaux hiérarchiques sont automatiquement filtrés."
)

st.sidebar.download_button(
    "📥 Télécharger un modèle (.csv)",
    data=generate_template_ogec_csv(is_agricole=is_agricole),
    file_name="Modele_Balance_Agricole_MASA.csv" if is_agricole else "Modele_Balance_OGEC_LoiDebre.csv",
    mime="text/csv",
    use_container_width=True
)

balances_parsees = []
if fichiers_balances:
    for f in fichiers_balances:
        res_b = parse_balance_ogec(f)
        if res_b is not None:
            balances_parsees.append(res_b)

balances_parsees.sort(key=lambda x: x["annee"] or x["fichier"])
source_reelle = len(balances_parsees) > 0

if source_reelle:
    total_st = sum(b.get("nb_sous_totaux_filtres", 0) for b in balances_parsees)
    st.sidebar.success(f"{len(balances_parsees)} balance(s) exploitée(s) • {total_st} sous-total(aux) écarté(s)")
    dern = balances_parsees[-1]
    def_forf_tot = dern["forfaits_74"]
    def_contrib = dern["contrib_756"] if dern["contrib_756"] > 0 else round(dern["total_prod"] * 0.22, 2)
    def_resto = dern["activites_70"]
    def_autres_p = dern["autres_prod"]
    def_ext = dern["charges_ext"]
    def_loyer = dern["loyers_aep"]
    def_ms = dern["masse_sal"]
    def_autres_c = dern["autres_ch"]
    def_fin = dern["charges_fin"]
    def_amort = dern["dot_amort"]
    def_dette = dern["dette_immo"] if dern["dette_immo"] > 0 else 1650000.0
    def_remb = dern["remb_cap"] if dern["remb_cap"] > 0 else 155000.0
    def_treso = dern["treso_51"] if dern["treso_51"] > 0 else 460000.0
elif is_mfr:
    def_forf_tot = 780000.0
    def_contrib = 130000.0
    def_resto = 290000.0
    def_autres_p = 145000.0
    def_ext = 285000.0
    def_loyer = 25000.0
    def_ms = 820000.0
    def_autres_c = 45000.0
    def_fin = 32000.0
    def_amort = 115000.0
    def_dette = 890000.0
    def_remb = 78000.0
    def_treso = 280000.0
elif is_agricole:
    def_forf_tot = 840000.0
    def_contrib = 245000.0
    def_resto = 680000.0
    def_autres_p = 190000.0
    def_ext = 535000.0
    def_loyer = 45000.0
    def_ms = 890000.0
    def_autres_c = 65000.0
    def_fin = 74000.0
    def_amort = 260000.0
    def_dette = 1950000.0
    def_remb = 165000.0
    def_treso = 410000.0
else:
    def_forf_tot = 860000.0
    def_contrib = 640000.0
    def_resto = 490000.0
    def_autres_p = 45000.0
    def_ext = 670000.0
    def_loyer = 85000.0
    def_ms = 960000.0
    def_autres_c = 75000.0
    def_fin = 68000.0
    def_amort = 225000.0
    def_dette = 1650000.0
    def_remb = 155000.0
    def_treso = 460000.0

k_suf = f"{normes_etab['type_court']}_{source_reelle}"

st.sidebar.markdown("### 2. Effectifs Élèves & Internat (Rentrée N)")
if "1er degré" in type_etab:
    eleves_1er = st.sidebar.number_input("Élèves Maternelle & Élémentaire", min_value=1, value=320, step=5, key=f"el1_{k_suf}")
    eleves_college, eleves_lycee = 0, 0
elif "Collège" in type_etab:
    eleves_1er = 0
    eleves_college = st.sidebar.number_input("Élèves Collège", min_value=1, value=450, step=5, key=f"elc_{k_suf}")
    eleves_lycee = 0
elif "Lycée GT" in type_etab:
    eleves_1er, eleves_college = 0, 0
    eleves_lycee = st.sidebar.number_input("Élèves Lycée GT / Pro", min_value=1, value=380, step=5, key=f"ell_{k_suf}")
elif is_mfr:
    eleves_1er, eleves_college = 0, 0
    eleves_lycee = st.sidebar.number_input("Jeunes en alternance (4e/3e, Bac Pro, BTSA)", min_value=1, value=190, step=5, key=f"elm_{k_suf}")
elif is_agricole:
    eleves_1er, eleves_college = 0, 0
    eleves_lycee = st.sidebar.number_input("Élèves & Étudiants (Bac Pro, Techno, BTSA)", min_value=1, value=340, step=5, key=f"ela_{k_suf}")
else:
    eleves_1er = st.sidebar.number_input("Élèves 1er degré (École)", min_value=0, value=380, step=5, key=f"el1m_{k_suf}")
    eleves_college = st.sidebar.number_input("Élèves Collège", min_value=0, value=460, step=5, key=f"elcm_{k_suf}")
    eleves_lycee = st.sidebar.number_input("Élèves Lycée", min_value=0, value=310, step=5, key=f"ellm_{k_suf}")

eleves_tot = max(1, eleves_1er + eleves_college + eleves_lycee)
taux_internat = st.sidebar.slider("Taux d'élèves internes (%)", 0, 100, int(normes_etab["taux_internat_ref"]), 5, key=f"int_{k_suf}")
st.sidebar.caption(f"Effectif total : **{eleves_tot:,} élèves** ({int(round(eleves_tot * taux_internat / 100))} internes)".replace(",", " "))

st.sidebar.markdown("### 3. Financements Publics & Familles (€)")
if is_agricole:
    forfait_commune = st.sidebar.number_input(
        "Subvention fonctionnement État / MASA (€)",
        min_value=0.0, value=float(def_forf_tot), step=10000.0, format="%.2f", key=f"masa_{k_suf}"
    )
    forfait_dept = st.sidebar.number_input(
        "Subventions Région & aides équipement/transport (€)",
        min_value=0.0, value=float(round(def_autres_p * 0.55, 2)), step=5000.0, format="%.2f", key=f"reg_ag_{k_suf}"
    )
    forfait_region = 0.0
    total_forfaits_eur = forfait_commune + forfait_dept
    contrib_familles_eur = st.sidebar.number_input(
        "Contributions scolaires des familles (hors pension) (€)",
        min_value=0.0, value=float(def_contrib), step=5000.0, format="%.2f", key=f"cf_ag_{k_suf}"
    )
    restauration_eur = st.sidebar.number_input(
        "Pension, internat, restauration & produits ateliers (€)",
        min_value=0.0, value=float(def_resto), step=10000.0, format="%.2f", key=f"rest_ag_{k_suf}"
    )
    autres_prod_eur = st.sidebar.number_input(
        "Taxe d'apprentissage, mécénat & produits annexes (€)",
        min_value=0.0, value=float(round(def_autres_p * 0.45, 2)), step=5000.0, format="%.2f", key=f"ta_ag_{k_suf}"
    )
else:
    if "1er degré" in type_etab:
        forfait_commune = st.sidebar.number_input("Forfait communal — Commune (€)", min_value=0.0, value=float(def_forf_tot if source_reelle else 285000.0), step=5000.0, format="%.2f", key=f"fc_{k_suf}")
        forfait_dept, forfait_region = 0.0, 0.0
    elif "Collège" in type_etab:
        forfait_commune = 0.0
        forfait_dept = st.sidebar.number_input("Forfait d'externat — Département (€)", min_value=0.0, value=float(def_forf_tot if source_reelle else 295000.0), step=5000.0, format="%.2f", key=f"fd_{k_suf}")
        forfait_region = 0.0
    elif "Lycée GT" in type_etab:
        forfait_commune, forfait_dept = 0.0, 0.0
        forfait_region = st.sidebar.number_input("Forfait d'externat — Région (€)", min_value=0.0, value=float(def_forf_tot if source_reelle else 305000.0), step=5000.0, format="%.2f", key=f"fr_{k_suf}")
    else:
        forfait_commune = st.sidebar.number_input("Forfait communal 1er degré — Commune (€)", min_value=0.0, value=float(round(def_forf_tot * 0.36, 2)), step=5000.0, format="%.2f", key=f"fcm_{k_suf}")
        forfait_dept = st.sidebar.number_input("Forfait d'externat Collège — Département (€)", min_value=0.0, value=float(round(def_forf_tot * 0.35, 2)), step=5000.0, format="%.2f", key=f"fdm_{k_suf}")
        forfait_region = st.sidebar.number_input("Forfait d'externat Lycée — Région (€)", min_value=0.0, value=float(round(def_forf_tot * 0.29, 2)), step=5000.0, format="%.2f", key=f"frm_{k_suf}")

    total_forfaits_eur = forfait_commune + forfait_dept + forfait_region
    contrib_familles_eur = st.sidebar.number_input("Contributions des familles — Scolarité (Cpte 756) (€)", min_value=0.0, value=float(def_contrib), step=10000.0, format="%.2f", key=f"cf_{k_suf}")
    restauration_eur = st.sidebar.number_input("Restauration, périscolaire & activités (Cpte 70) (€)", min_value=0.0, value=float(def_resto), step=10000.0, format="%.2f", key=f"rest_{k_suf}")
    autres_prod_eur = st.sidebar.number_input("Dons, mécénat & reprises fonds dédiés (€)", min_value=0.0, value=float(def_autres_p), step=5000.0, format="%.2f", key=f"autp_{k_suf}")

st.sidebar.markdown("### 4. Charges Association & Immobilier (€)")
lbl_ms_sidebar = "Masse salariale association (incl. moniteurs MFR)" if is_mfr else ("Personnel OGEC/CNEAP (hors enseignants MASA)" if is_agricole else "Personnel OGEC (Cpte 64 — hors enseignants État)")
masse_sal_eur = st.sidebar.number_input(lbl_ms_sidebar, min_value=0.0, value=float(def_ms), step=10000.0, format="%.2f", key=f"ms_{k_suf}")

lbl_ext_sidebar = "Internat, alimentation, fluides & ateliers (hors loyers)" if is_agricole else "Achats, cantine, fluides & entretien (hors loyers)"
charges_ext_eur = st.sidebar.number_input(lbl_ext_sidebar, min_value=0.0, value=float(def_ext), step=10000.0, format="%.2f", key=f"ext_{k_suf}")

loyers_aep_eur = st.sidebar.number_input(
    "Loyer immobilier versé à l'AEP / propriétaire (Cpte 613)",
    min_value=0.0, value=float(def_loyer), step=5000.0, format="%.2f", key=f"loy_{k_suf}",
    help="Loyer versé à l'association propriétaire des murs (AEP) ou à un bailleur privé."
)

autres_ch_eur = st.sidebar.number_input("Cotisations réseau & gestion courante (Cpte 65)", min_value=0.0, value=float(def_autres_c), step=5000.0, format="%.2f", key=f"autc_{k_suf}")
charges_fin_eur = st.sidebar.number_input("Intérêts des emprunts immobiliers (Cpte 66)", min_value=0.0, value=float(def_fin), step=5000.0, format="%.2f", key=f"fin_{k_suf}")
dot_amort_eur = st.sidebar.number_input("Dotations aux amortissements (Cpte 681)", min_value=0.0, value=float(def_amort), step=5000.0, format="%.2f", key=f"amo_{k_suf}")

dette_immo_eur = st.sidebar.number_input("Encours emprunts immobiliers au 31/12 (€)", min_value=0.0, value=float(def_dette), step=25000.0, format="%.2f", key=f"det_{k_suf}")
remb_cap_eur = st.sidebar.number_input("Remboursement annuel capital dette (€)", min_value=0.0, value=float(def_remb), step=5000.0, format="%.2f", key=f"remb_{k_suf}")
treso_init_eur = st.sidebar.number_input("Trésorerie disponible au 31/12 (€)", min_value=0.0, value=float(def_treso), step=10000.0, format="%.2f", key=f"tres_{k_suf}")
etp_asso = st.sidebar.number_input("Effectifs salariés association (ETP)", min_value=1, value=21 if is_mfr else 26, step=1, key=f"etp_{k_suf}")

# Agrégats & Ratios N
total_prod_eur = total_forfaits_eur + contrib_familles_eur + restauration_eur + autres_prod_eur
total_ch_eur = masse_sal_eur + charges_ext_eur + loyers_aep_eur + autres_ch_eur + charges_fin_eur + dot_amort_eur
charges_decaissables_eur = max(1.0, total_ch_eur - dot_amort_eur)

res_net_eur = total_prod_eur - total_ch_eur
caf_eur = res_net_eur + dot_amort_eur
autofin_net_eur = caf_eur - remb_cap_eur

total_prod_m = total_prod_eur / 1e6
total_forfaits_m = total_forfaits_eur / 1e6
contrib_familles_m = contrib_familles_eur / 1e6
restauration_m = restauration_eur / 1e6
autres_prod_m = autres_prod_eur / 1e6
masse_sal_m = masse_sal_eur / 1e6
charges_ext_m = charges_ext_eur / 1e6
loyers_aep_m = loyers_aep_eur / 1e6
autres_ch_m = autres_ch_eur / 1e6
charges_fin_m = charges_fin_eur / 1e6
dot_amort_m = dot_amort_eur / 1e6
total_ch_m = total_ch_eur / 1e6
res_net_m = res_net_eur / 1e6
caf_m = caf_eur / 1e6
remb_cap_m = remb_cap_eur / 1e6
autofin_m = autofin_net_eur / 1e6
dette_immo_m = dette_immo_eur / 1e6
treso_m = treso_init_eur / 1e6

taux_caf = (caf_eur / total_prod_eur * 100) if total_prod_eur > 0 else 0.0
taux_dep_public = (total_forfaits_eur / total_prod_eur * 100) if total_prod_eur > 0 else 0.0
poids_ms = (masse_sal_eur / total_ch_eur * 100) if total_ch_eur > 0 else 0.0
poids_fluides = (charges_ext_eur / total_ch_eur * 100) if total_ch_eur > 0 else 0.0
jours_treso_init = int(round((treso_init_eur / charges_decaissables_eur) * 365))
cap_desend_ogec = (dette_immo_eur / caf_eur) if caf_eur > 0 else 99.9

# Règle d'Or Immobilière complète (Amortissements + Intérêts + Loyers AEP)
charges_immo_fin_eur = dot_amort_eur + charges_fin_eur + loyers_aep_eur
solde_regle_or_eur = contrib_familles_eur - charges_immo_fin_eur
regle_or_ok = solde_regle_or_eur >= 0

forfait_moy_eleve = int(round(total_forfaits_eur / eleves_tot))
contrib_moy_eleve = int(round(contrib_familles_eur / eleves_tot))
cout_complet_eleve = int(round(total_ch_eur / eleves_tot))

# Historique 2021-2025
if len(balances_parsees) >= 2:
    annees_retro = [b["annee"] or f"Ex.{i+1}" for i, b in enumerate(balances_parsees)]
    prod_hist = [round(b["total_prod"] / 1e6, 2) for b in balances_parsees]
    ch_hist = [round(b["total_ch"] / 1e6, 2) for b in balances_parsees]
    ms_hist = [round(b["masse_sal"] / 1e6, 2) for b in balances_parsees]
    caf_hist = [round(b["caf"] / 1e6, 2) for b in balances_parsees]
    res_hist = [round(b["res_net"] / 1e6, 2) for b in balances_parsees]
else:
    annees_retro = ["2021", "2022", "2023", "2024", "2025"]
    prod_hist = [round(total_prod_m * 0.89, 2), round(total_prod_m * 0.92, 2), round(total_prod_m * 0.95, 2), round(total_prod_m * 0.98, 2), round(total_prod_m, 2)]
    ch_hist = [round(total_ch_m * 0.84, 2), round(total_ch_m * 0.88, 2), round(total_ch_m * 0.93, 2), round(total_ch_m * 0.97, 2), round(total_ch_m, 2)]
    ms_hist = [round(masse_sal_m * 0.85, 2), round(masse_sal_m * 0.89, 2), round(masse_sal_m * 0.93, 2), round(masse_sal_m * 0.97, 2), round(masse_sal_m, 2)]
    res_hist = [round(p - c, 2) for p, c in zip(prod_hist, ch_hist)]
    caf_hist = [round(r + dot_amort_m, 2) for r in res_hist]

n_int = max(1, len(annees_retro) - 1)
tcma_prod = ((prod_hist[-1] / prod_hist[0]) ** (1 / n_int) - 1) * 100 if prod_hist[0] > 0 else 0.0
tcma_ch = ((ch_hist[-1] / ch_hist[0]) ** (1 / n_int) - 1) * 100 if ch_hist[0] > 0 else 0.0
tcma_ms = ((ms_hist[-1] / ms_hist[0]) ** (1 / n_int) - 1) * 100 if ms_hist[0] > 0 else 0.0


# ==========================================
# 2. EN-TÊTE EXÉCUTIF & LEXIQUE RÉGLEMENTAIRE
# ==========================================
col_t, col_lex, col_pdf = st.columns([3.2, 1.1, 1.2])

with col_t:
    st.title("Archétype Éducation — Pilotage & Prospective")
    badge_src = "Balances ANC 2018-06 certifiées (Anti-double-comptage actif)" if source_reelle else "Référentiel ANC 2018-06 • Observatoire FNOGEC & Code rural"
    st.caption(f"{etablissement} • {normes_etab['type_court']} ({eleves_tot} élèves) • {badge_src}")

with col_lex:
    st.write("")
    with st.popover("📖 Lexique & Normes", use_container_width=True):
        st.markdown("## 📖 Guide Pédagogique & Normes Sectorielles")
        st.markdown("### 1. Deux régimes juridiques et financiers distincts")
        st.markdown("""
- **Enseignement sous contrat Éducation Nationale (Loi Debré — OGEC) :** Les enseignants sont rémunérés directement par l'État. Les collectivités versent un **forfait obligatoire** par principe de parité avec l'école publique : **Commune** en maternelle/élémentaire (moyenne FNOGEC : **1 205 €/maternelle** et **645 €/élémentaire**), **Département** en collège (**647 €** hors part État), **Région** en lycée (**803 €** hors part État).
- **Enseignement Agricole Temps Plein (Code rural Art. L. 813-8 — CNEAP) :** Tutelle du **Ministère de l'Agriculture (MASA)** qui rémunère les enseignants contractuels de droit public et verse une subvention annuelle de fonctionnement par élève selon la filière. La Région intervient sur l'investissement et les équipements.
- **Maisons Familiales Rurales / Alternance (Code rural Art. L. 813-9 — UNMFREO) :** L'association recrute et paie directement ses formateurs (*moniteurs*) sous contrat de droit privé, financés par une subvention globale MASA par élève et par journée de présence.
        """)
        st.markdown("### 2. Ratios clés de pilotage & Montage AEP (ANC 2018-06)")
        st.markdown("""
- **Capacité d'Autofinancement (CAF) :** `Résultat net + Dotations aux amortissements`. **Cible sectorielle : 6 % à 8,5 % des produits** pour absorber le remboursement en capital de la dette immobilière et le renouvellement des matériels.
- **Trésorerie de sécurité :** Contrairement à une commune qui perçoit ses recettes chaque mois par douzièmes, un établissement encaisse les contributions familles et les acomptes publics de façon fractionnée. **Recommandation prudentielle FNOGEC : 90 à 120 jours de charges décaissables** (vigilance sous 60 jours, alerte sous 30 jours).
- **Règle d'Or OGEC & Loyers AEP :** Les contributions des familles (compte 756) doivent couvrir les amortissements immobiliers (681), les intérêts d'emprunts (66) **ainsi que les loyers versés à l'association propriétaire des murs (AEP — compte 613)** afin que les subventions publiques restent 100 % dédiées au fonctionnement pédagogique.
        """)

onglets = st.tabs([
    "📊 Rétrospective",
    "⚖️ Diagnostic & Normes",
    "🔮 Prospective 2026-2030",
    "🏛️ Parité & Charges Fixes",
    "📝 Note CA & Financeurs"
])

# ------------------------------------------
# ONGLET 1 : RÉTROSPECTIVE
# ------------------------------------------
with onglets[0]:
    rh_1, rh_2 = st.columns([0.92, 0.08])
    with rh_1:
        st.subheader("Dynamique financière passée (2021-2025)")
    with rh_2:
        fiche_pedagogique(
            "ℹ️",
            "TCMA & Effet de Ciseau en établissement scolaire",
            "Le TCMA (Taux de Croissance Annuel Moyen) compare la vitesse d'évolution des ressources (forfaits publics, familles, internat) à celle des charges.",
            "Effet de ciseau = TCMA Charges - TCMA Produits",
            [
                "Trajectoire équilibrée : TCMA Produits ≥ TCMA Charges.",
                "Alerte ciseau : Lorsque les charges d'énergie, de restauration et la masse salariale EPNL progressent plus vite que l'indexation des forfaits publics, la CAF s'érode."
            ],
            "Cet indicateur permet de documenter objectivement le décalage entre l'inflation réelle subie par l'établissement et la revalorisation des dotations publiques."
        )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("TCMA Produits Exploitation", f"+{tcma_prod:.2f} % / an")
    k2.metric(
        "TCMA Charges Exploitation",
        f"+{tcma_ch:.2f} % / an",
        f"{tcma_ch - tcma_prod:+.2f} pts vs Produits",
        delta_color="inverse"
    )
    k3.metric(
        "TCMA Masse Salariale (Cpte 64)",
        f"+{tcma_ms:.2f} % / an",
        f"Poids : {poids_ms:.1f} % (Norme : {normes_etab['poids_ms_cible']:.0f}%)"
    )
    k4.metric(
        "CAF Dernier Exercice",
        f"{caf_m:.2f} M€",
        f"Taux de CAF : {taux_caf:.1f} % (Cible ≥ {normes_etab['taux_caf_cible']:.1f}%)"
    )

    st.divider()
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("1. Effet de ciseau (Produits vs Charges)")
        st.line_chart(pd.DataFrame({
            "Exercice": annees_retro,
            "Produits (M€)": prod_hist,
            "Charges (M€)": ch_hist
        }).set_index("Exercice"))

    with g2:
        st.subheader("2. Évolution du Résultat Net & de la CAF")
        st.line_chart(pd.DataFrame({
            "Exercice": annees_retro,
            "CAF (M€)": caf_hist,
            "Résultat Net (M€)": res_hist
        }).set_index("Exercice"))

# ------------------------------------------
# ONGLET 2 : DIAGNOSTIC ANC 2018-06 & NORMES SECTORIELLES
# ------------------------------------------
with onglets[1]:
    dg_1, dg_2 = st.columns([0.92, 0.08])
    with dg_1:
        st.subheader("1. Formation du Résultat & Capacité d'Autofinancement (ANC 2018-06)")
    with dg_2:
        fiche_pedagogique(
            "ℹ️",
            "Lecture du Compte de Résultat Associatif (ANC 2018-06)",
            "Contrairement aux collectivités locales qui votent un budget en deux sections (fonctionnement et investissement), l'association présente un compte de résultat unique intégrant l'usure du patrimoine (amortissements) et les loyers immobiliers versés à l'AEP.",
            "CAF = Résultat Net + Dotations aux Amortissements (Cpte 681)",
            [
                f"Taux de CAF recommandé ({normes_etab['type_court']}) : ≥ {normes_etab['taux_caf_cible']:.1f} % des produits d'exploitation.",
                "Autofinancement net : CAF - Remboursement en capital des emprunts. Doit rester positif pour financer les travaux courants sans puiser dans la trésorerie."
            ],
            "Un résultat net proche de zéro n'est pas forcément alarmant si les dotations aux amortissements (charge non décaissée) permettent de dégager une CAF suffisante pour rembourser les emprunts."
        )

    lbl_p1 = "+ Subventions MASA, Région & aides (Cpte 74)" if is_agricole else "+ Forfaits publics d'externat / communal (Cpte 74)"
    lbl_p3 = "+ Internat, pension, ateliers & taxe d'apprentissage (70/754)" if is_agricole else "+ Restauration, périscolaire, activités & dons (70/754)"
    lbl_c1 = "- Masse salariale association (64) & Internat/Fluides/Ateliers (60-65)" if is_agricole else "- Personnel OGEC (Cpte 64) & Achats / Fluides (60-65)"

    df_sig_asso = pd.DataFrame([
        {
            "Poste du Compte de Résultat (ANC 2018-06)": lbl_p1,
            "Montant": f"{total_forfaits_m:.2f} M€",
            "Part (%)": f"{taux_dep_public:.1f} %",
            "Affectation réglementaire": normes_etab["financeur_principal"]
        },
        {
            "Poste du Compte de Résultat (ANC 2018-06)": "+ Contributions des familles — Scolarité (Cpte 756)",
            "Montant": f"{contrib_familles_m:.2f} M€",
            "Part (%)": f"{(contrib_familles_m / total_prod_m * 100):.1f} %",
            "Affectation réglementaire": "Couverture patrimoine immobilier, loyers AEP & caractère propre"
        },
        {
            "Poste du Compte de Résultat (ANC 2018-06)": lbl_p3,
            "Montant": f"{(restauration_m + autres_prod_m):.2f} M€",
            "Part (%)": f"{((restauration_m + autres_prod_m) / total_prod_m * 100):.1f} %",
            "Affectation réglementaire": "Activités annexes & hébergement à équilibrer par les tarifs"
        },
        {
            "Poste du Compte de Résultat (ANC 2018-06)": "= TOTAL PRODUITS D'EXPLOITATION",
            "Montant": f"{total_prod_m:.2f} M€",
            "Part (%)": "100.0 %",
            "Affectation réglementaire": f"Soit {int(round(total_prod_eur / eleves_tot)):,} € / élève".replace(",", " ")
        },
        {
            "Poste du Compte de Résultat (ANC 2018-06)": lbl_c1,
            "Montant": f"- {(masse_sal_m + charges_ext_m + autres_ch_m):.2f} M€",
            "Part (%)": f"{((masse_sal_m + charges_ext_m + autres_ch_m) / total_prod_m * 100):.1f} %",
            "Affectation réglementaire": f"Effectifs salariés association : {etp_asso} ETP"
        },
        {
            "Poste du Compte de Résultat (ANC 2018-06)": "- Amortissements (681), Intérêts dette (66) & Loyers AEP (613)",
            "Montant": f"- {(dot_amort_m + charges_fin_m + loyers_aep_m):.2f} M€",
            "Part (%)": f"{((dot_amort_m + charges_fin_m + loyers_aep_m) / total_prod_m * 100):.1f} %",
            "Affectation réglementaire": f"Dont loyer immobilier AEP : {loyers_aep_m:.2f} M€ / an"
        },
        {
            "Poste du Compte de Résultat (ANC 2018-06)": "= RÉSULTAT NET COMPTABLE",
            "Montant": f"{res_net_m:+.2f} M€",
            "Part (%)": f"{(res_net_m / total_prod_m * 100):+.1f} %",
            "Affectation réglementaire": "Affecté aux réserves associatives par l'Assemblée Générale"
        },
        {
            "Poste du Compte de Résultat (ANC 2018-06)": "= CAPACITÉ D'AUTOFINANCEMENT (CAF = Résultat + Amort.)",
            "Montant": f"{caf_m:.2f} M€",
            "Part (%)": f"{taux_caf:.1f} %",
            "Affectation réglementaire": f"Autofinancement net après capital dette ({remb_cap_m:.2f} M€) : {autofin_m:+.2f} M€"
        }
    ])
    st.dataframe(df_sig_asso, hide_index=True, use_container_width=True)

    st.divider()
    st.subheader(f"2. Positionnement aux Normes & Moyennes ({normes_etab['type_court']})")

    df_normes = pd.DataFrame([
        {
            "Indicateur de Pilotage": "Financement public moyen par élève",
            "Établissement": f"{forfait_moy_eleve:,} € / élève".replace(",", " "),
            "Repère / Moyenne Nationale": f"{normes_etab['forfait_ref_eleve']:,} € / élève ({normes_etab['detail_forfait']})".replace(",", " "),
            "Statut": "Conforme / Supérieur" if forfait_moy_eleve >= normes_etab["forfait_ref_eleve"] else "Sous la moyenne"
        },
        {
            "Indicateur de Pilotage": "Taux de Capacité d'Autofinancement (CAF / Produits)",
            "Établissement": f"{taux_caf:.1f} %",
            "Repère / Moyenne Nationale": f"Cible : ≥ {normes_etab['taux_caf_cible']:.1f} % (Vigilance < 5,0 %)",
            "Statut": "Sain" if taux_caf >= normes_etab["taux_caf_cible"] else "À renforcer"
        },
        {
            "Indicateur de Pilotage": "Couverture de Trésorerie (en jours de charges décaissables)",
            "Établissement": f"{jours_treso_init} jours ({treso_m:.2f} M€)",
            "Repère / Moyenne Nationale": f"Cible prudentielle : {normes_etab['jours_treso_cible']}-120 jours (Alerte < 30 j)",
            "Statut": "Confortable" if jours_treso_init >= normes_etab["jours_treso_cible"] else ("Vigilance" if jours_treso_init >= 45 else "Alerte liquidité")
        },
        {
            "Indicateur de Pilotage": "Poids de la Masse Salariale Association (Cpte 64 / Charges)",
            "Établissement": f"{poids_ms:.1f} %",
            "Repère / Moyenne Nationale": f"Moyenne profil : ~{normes_etab['poids_ms_cible']:.0f} %",
            "Statut": "Maîtrisé" if poids_ms <= normes_etab["poids_ms_cible"] + 3 else "Rigidité élevée"
        },
        {
            "Indicateur de Pilotage": "Poids des Charges Fixes Externes (Fluides, Internat, Maintenance)",
            "Établissement": f"{poids_fluides:.1f} %",
            "Repère / Moyenne Nationale": f"Moyenne profil : ~{normes_etab['poids_fluides_cible']:.0f} % (Taux internat : {taux_internat}%)",
            "Statut": "Dans la norme" if poids_fluides <= normes_etab["poids_fluides_cible"] + 3 else "Tension charges fixes"
        },
        {
            "Indicateur de Pilotage": "Capacité de Désendettement Immobilier (Dette / CAF)",
            "Établissement": f"{cap_desend_ogec:.1f} ans",
            "Repère / Moyenne Nationale": "Norme bancaire : < 8 ans (Alerte > 10 ans)",
            "Statut": "Soutenable" if cap_desend_ogec <= 8.0 else "Sous surveillance"
        }
    ])
    st.dataframe(df_normes, hide_index=True, use_container_width=True)

    st.divider()
    ro_h1, ro_h2 = st.columns([0.92, 0.08])
    with ro_h1:
        titre_ro = "3. Étanchéité Pédagogique, Loyers AEP & Couverture Patrimoniale" if is_agricole else "3. Vérification de la Règle d'Or OGEC (Amortissements, Intérêts & Loyers AEP)"
        st.subheader(titre_ro)
    with ro_h2:
        fiche_pedagogique(
            "ℹ️",
            "La Règle d'Or : couvrir les amortissements, emprunts et loyers AEP par les familles",
            "Les subventions publiques de fonctionnement sont strictement affectées au fonctionnement pédagogique et matériel. Lorsque les murs appartiennent à une association propriétaire distincte (AEP), le loyer immobilier versé (compte 613) doit également être couvert par la contribution des familles.",
            "Solde Règle d'Or = Contributions familles (756) - [Amort. (681) + Intérêts (66) + Loyers AEP (613)]",
            [
                "Solde ≥ 0 € : Les familles financent intégralement l'amortissement des bâtiments, les intérêts d'emprunts et les loyers versés à l'AEP.",
                "Solde < 0 € : Les dotations publiques ou excédents d'internat/cantine subventionnent indirectement l'immobilier, ce qui fragilise la structure en cas de contrôle."
            ],
            "Cet indicateur permet de justifier auprès des parents d'élèves et de l'AEP le montant de la contribution familiale annuelle."
        )

    c_ro1, c_ro2 = st.columns([1.2, 1.0])
    with c_ro1:
        if regle_or_ok:
            st.success(
                f"**Équilibre patrimonial respecté (+{solde_regle_or_eur:,.0f} € d'excédent) :**\n\n".replace(",", " ") +
                f"* Les contributions des familles (**{contrib_familles_eur:,.0f} €**) couvrent intégralement les dotations aux amortissements (**{dot_amort_eur:,.0f} €**), les intérêts (**{charges_fin_eur:,.0f} €**) et les loyers immobiliers AEP (**{loyers_aep_eur:,.0f} €**).\n".replace(",", " ") +
                "* Les financements publics restent intégralement dédiés à la mission éducative."
            )
        else:
            st.warning(
                f"**Insuffisance de couverture immobilière ({solde_regle_or_eur:,.0f} €) :**\n\n".replace(",", " ") +
                f"* Le bloc immobilier et locatif (**{charges_immo_fin_eur:,.0f} €**, dont **{loyers_aep_eur:,.0f} €** de loyers AEP) dépasse les contributions des familles (**{contrib_familles_eur:,.0f} €**).\n".replace(",", " ") +
                f"* **Ajustement cible :** Il manque **{int(round(abs(solde_regle_or_eur) / eleves_tot))} € par élève et par an** sur la contribution familiale pour équilibrer la section immobilière."
            )

    with c_ro2:
        st.bar_chart(pd.DataFrame({
            "Bloc": ["Contributions Familles (756)", "Amort. + Intérêts + Loyers AEP"],
            "Montant (M€)": [round(contrib_familles_m, 2), round(charges_immo_fin_eur / 1e6, 2)]
        }).set_index("Bloc"), color="#2563eb")

# ------------------------------------------
# ONGLET 3 : PROSPECTIVE 2026-2030
# ------------------------------------------
with onglets[2]:
    pr_1, pr_2 = st.columns([0.92, 0.08])
    with pr_1:
        st.subheader("Simulateur Prospectif 2026-2030 — Effectifs, Dotations Publics & PPI Immobilière")
    with pr_2:
        fiche_pedagogique(
            "ℹ️",
            "Modélisation quinquennale (2026-2030)",
            "Ce simulateur projette sur cinq ans l'impact combiné de la démographie scolaire, de l'indexation des dotations publiques, de l'inflation des charges fixes (internat, énergie, loyers AEP, salaires) et des projets immobiliers.",
            "Trésorerie point bas = Trésorerie fin d'année - Portage des acomptes publics",
            [
                "Sensibilité effectifs : une baisse d'effectifs réduit mécaniquement les forfaits publics et les contributions familles dès la rentrée suivante, alors que les charges fixes (chauffage, loyer AEP, entretien) restent rigides.",
                "Amortissements induits : chaque million d'euros investi génère environ 40 à 50 k€/an de dotations aux amortissements supplémentaires pendant 20 à 25 ans."
            ],
            "Testez le scénario 'Fil de l'eau' pour mesurer l'impact d'une stagnation des forfaits publics face à l'inflation."
        )

    sc_ogec = st.radio(
        "Scénarios préconfigurés pour le Conseil d'Administration :",
        [
            "Scénario 3 : Trajectoire d'Équilibre (Indexation financements + Règle d'Or)",
            "Scénario 1 : Fil de l'eau (Inflation charges fixes sans revalorisation)",
            "Scénario 2 : Plan Immobilier & Plateaux Techniques (Rénovation énergétique)"
        ],
        horizontal=True
    )

    if "Scénario 1" in sc_ogec:
        p_el, p_forf, p_fam, p_resto, p_ms, p_fl, p_ppi, p_subv, p_dur = (0.0, 1.1, 0.0, 1.5, 3.6, 3.0, 0.15, 10, 15)
    elif "Scénario 2" in sc_ogec:
        p_el, p_forf, p_fam, p_resto, p_ms, p_fl, p_ppi, p_subv, p_dur = (1.0, 2.0, 45.0, 2.5, 3.0, 1.8, 0.65, 30 if is_agricole else 20, 20)
    else:
        p_el, p_forf, p_fam, p_resto, p_ms, p_fl, p_ppi, p_subv, p_dur = (0.5, 2.3, 25.0, 2.2, 2.5, 1.5, 0.30, 25 if is_agricole else 15, 18)

    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown("**1. Effectifs & Financements Publics**")
        tx_eleves = st.slider("Évolution annuelle des effectifs élèves (%)", -3.0, 4.0, float(p_el), 0.1)
        lbl_sl_forf = "Revalorisation subventions MASA/Région (%/an)" if is_agricole else "Revalorisation forfaits publics (%/an)"
        tx_forfaits = st.slider(lbl_sl_forf, 0.0, 5.0, float(p_forf), 0.1)
        delta_contrib_eur = st.slider("Hausse contribution familles (€/élève/an)", 0.0, 100.0, float(p_fam), 5.0)
        lbl_sl_rest = "Indexation tarifs internat/pension (%/an)" if is_agricole else "Revalorisation tarifs cantine/annexes (%/an)"
        tx_resto = st.slider(lbl_sl_rest, 0.0, 5.0, float(p_resto), 0.1)

    with s2:
        st.markdown("**2. Charges Association & Charges Fixes**")
        lbl_sl_ms = "Évolution masse salariale (%/an)" if is_agricole else "Évolution masse salariale EPNL (%/an)"
        tx_ms_epnl = st.slider(lbl_sl_ms, 1.0, 5.5, float(p_ms), 0.1)
        lbl_sl_fl = "Évolution internat, fluides & loyers AEP (%/an)" if is_agricole else "Évolution fluides, cantine & loyers AEP (%/an)"
        tx_fluides = st.slider(lbl_sl_fl, 0.5, 5.5, float(p_fl), 0.1)
        delai_forfaits_mois = st.slider("Délai moyen encaissement soldes publics (mois)", 2, 10, 5, 1)

    with s3:
        st.markdown("**3. PPI Immobilière & Emprunts**")
        ppi_immo_m = st.slider("Investissements immobiliers & équipements (M€/an)", 0.05, 2.00, float(p_ppi), 0.05)
        lbl_sl_subv = "Subventions Région / FEADER / ADEME (%)" if is_agricole else "Subventions Région / ADEME / Fonds privés (%)"
        tx_subv_immo = st.slider(lbl_sl_subv, 0, 60, int(p_subv), 5)
        duree_pret_immo = st.slider("Durée nouveaux emprunts immobiliers (ans)", 10, 25, int(p_dur), 1)

    annees_proj = [2026, 2027, 2028, 2029, 2030]
    prod_p, ch_p, res_p, caf_p, autofin_p, dette_p, treso_p, jours_treso_p, eleves_p = [], [], [], [], [], [], [], [], []
    regle_or_p = []

    cur_el = float(eleves_tot)
    cur_forf = total_forfaits_m
    cur_contrib_unitaire = contrib_familles_eur / eleves_tot
    cur_resto = restauration_m + autres_prod_m
    cur_ms = masse_sal_m
    cur_ext = charges_ext_m + autres_ch_m
    cur_loyer = loyers_aep_m
    cur_amort = dot_amort_m
    cur_dette = dette_immo_m
    cur_treso = treso_m
    remb_hist_an = remb_cap_m

    for yr in annees_proj:
        cur_el = cur_el * (1 + tx_eleves / 100.0)
        el_int = int(round(cur_el))

        cur_forf = cur_forf * (1 + tx_eleves / 100.0) * (1 + tx_forfaits / 100.0)
        cur_contrib_unitaire += delta_contrib_eur
        cur_contrib_tot = (cur_contrib_unitaire * el_int) / 1e6
        cur_resto = cur_resto * (1 + tx_eleves / 100.0) * (1 + tx_resto / 100.0)
        cur_prod = cur_forf + cur_contrib_tot + cur_resto

        cur_ms = cur_ms * (1 + tx_ms_epnl / 100.0)
        cur_ext = cur_ext * (1 + tx_fluides / 100.0)
        cur_loyer = cur_loyer * (1 + tx_fluides / 100.0)
        cur_amort = cur_amort + (ppi_immo_m * 0.04)
        cur_fin = cur_dette * 0.036
        cur_ch = cur_ms + cur_ext + cur_loyer + cur_amort + cur_fin

        cur_res = cur_prod - cur_ch
        cur_caf = cur_res + cur_amort

        besoin_emprunt = max(0.0, ppi_immo_m * (1 - tx_subv_immo / 100.0))
        amort_nouv_dette = besoin_emprunt / float(duree_pret_immo)
        remb_tot = min(cur_dette, remb_hist_an) + amort_nouv_dette
        cur_autofin = cur_caf - remb_tot

        cur_dette = max(0.0, cur_dette - min(cur_dette, remb_hist_an) + besoin_emprunt - amort_nouv_dette)
        cur_treso = cur_treso + cur_autofin
        portage_public = cur_forf * 0.30 * (delai_forfaits_mois / 12.0)
        treso_point_bas = max(0.0, cur_treso - portage_public)
        ch_dec_an = max(0.1, cur_ch - cur_amort)
        j_treso = int(round((treso_point_bas / ch_dec_an) * 365))

        prod_p.append(round(cur_prod, 2))
        ch_p.append(round(cur_ch, 2))
        res_p.append(round(cur_res, 2))
        caf_p.append(round(cur_caf, 2))
        autofin_p.append(round(cur_autofin, 2))
        dette_p.append(round(cur_dette, 2))
        treso_p.append(round(cur_treso, 2))
        jours_treso_p.append(j_treso)
        eleves_p.append(el_int)
        regle_or_p.append(cur_contrib_tot >= (cur_amort + cur_fin + cur_loyer))

    analyse_ogec = generer_analyse_ogec(
        etablissement, type_etab, is_agricole, is_mfr, eleves_tot, eleves_p[-1],
        total_prod_m, caf_m, dette_immo_m,
        prod_p, ch_p, res_p, caf_p, autofin_p, dette_p, treso_p, jours_treso_p,
        tx_eleves, tx_forfaits, delta_contrib_eur, tx_ms_epnl, tx_fluides,
        ppi_immo_m, tx_subv_immo, duree_pret_immo, regle_or_p[-1]
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Résultat Net 2030", f"{res_p[-1]:+.2f} M€", f"CAF 2030 : {caf_p[-1]:.2f} M€")
    m2.metric("Autofinancement Net 2030", f"{autofin_p[-1]:+.2f} M€", "Après remboursement dette immo")
    m3.metric(
        "Point Bas Trésorerie",
        f"{min(jours_treso_p)} jours",
        f"Cible FNOGEC : 90-120 j (Alerte < 30 j)",
        delta_color="normal" if min(jours_treso_p) >= 60 else "inverse"
    )
    m4.metric("Effectifs 2030", f"{eleves_p[-1]:,} élèves".replace(",", " "), f"{eleves_p[-1] - eleves_tot:+d} élèves vs N")

    st.divider()
    gp1, gp2 = st.columns(2)
    with gp1:
        st.subheader("Produits vs Charges d'Exploitation (M€)")
        st.line_chart(pd.DataFrame({
            "Année": [str(a) for a in annees_proj],
            "Produits (M€)": prod_p,
            "Charges (M€)": ch_p
        }).set_index("Année"))

    with gp2:
        st.subheader("CAF, Dette Immobilière & Trésorerie (M€)")
        st.bar_chart(pd.DataFrame({
            "Année": [str(a) for a in annees_proj],
            "CAF (M€)": caf_p,
            "Dette Immo (M€)": dette_p,
            "Trésorerie (M€)": treso_p
        }).set_index("Année"))

    st.dataframe(pd.DataFrame({
        "Exercice": [str(a) for a in annees_proj],
        "Élèves": eleves_p,
        "Produits (M€)": prod_p,
        "Charges (M€)": ch_p,
        "Résultat (M€)": res_p,
        "CAF (M€)": caf_p,
        "Autofin. Net (M€)": autofin_p,
        "Dette Immo (M€)": dette_p,
        "Tréso point bas (j)": jours_treso_p
    }), hide_index=True, use_container_width=True)

    st.divider()
    st.subheader(f"🧭 Feuille de Route Stratégique — {analyse_ogec['badge']}")
    txt_reco = (
        f"**Diagnostic quinquennal :**\n"
        f"* {analyse_ogec['diag'][0]}\n"
        f"* {analyse_ogec['diag'][1]}\n\n"
        f"**Les 4 leviers d'action :**\n"
        f"* {analyse_ogec['piliers'][0]}\n"
        f"* {analyse_ogec['piliers'][1]}\n"
        f"* {analyse_ogec['piliers'][2]}\n"
        f"* {analyse_ogec['piliers'][3]}"
    )
    if analyse_ogec["niveau"] == "critique":
        st.error(txt_reco)
    elif analyse_ogec["niveau"] == "vigilance":
        st.warning(txt_reco)
    else:
        st.success(txt_reco)

# ------------------------------------------
# ONGLET 4 : PARITÉ & CHARGES FIXES
# ------------------------------------------
with onglets[3]:
    pa_1, pa_2 = st.columns([0.92, 0.08])
    with pa_1:
        titre_ong4 = "Analyse par Élève, Internat & Soutenabilité des Charges Fixes" if is_agricole else "Analyse par Élève & Calculette de Parité Public / Privé"
        st.subheader(titre_ong4)
    with pa_2:
        fiche_pedagogique(
            "ℹ️",
            "Principe de parité et structure des coûts par élève",
            "Pour les établissements Loi Debré, le forfait public doit couvrir les mêmes dépenses de fonctionnement matériel et personnel non enseignant que dans l'enseignement public de référence. Pour les établissements agricoles, la subvention MASA est fixée par filière et complétée par les ressources d'internat et la taxe d'apprentissage.",
            "Écart annuel = (Coût de référence par élève - Financement public perçu) × Effectifs",
            [
                "Observatoire FNOGEC : 1 205 €/élève en maternelle, 645 €/élève en élémentaire, 647 €/collégien (part Département), 803 €/lycéen (part Région).",
                "Enseignement agricole : le taux d'internat (souvent > 60 %) et l'entretien des plateaux techniques génèrent des charges fixes incompressibles même en cas de légère baisse d'effectifs."
            ],
            "Cette calculette sert de support chiffré lors des commissions de concertation avec les élus ou les autorités académiques."
        )

    p1, p2, p3 = st.columns(3)
    p1.metric(
        "Financement Public / Élève",
        f"{forfait_moy_eleve:,} € / an".replace(",", " "),
        f"Repère national : {normes_etab['forfait_ref_eleve']:,} € / élève".replace(",", " ")
    )
    p2.metric(
        "Contribution Famille / Élève",
        f"{contrib_moy_eleve:,} € / an".replace(",", " "),
        f"Repère national : {normes_etab['contrib_ref_eleve']:,} € / élève".replace(",", " ")
    )
    p3.metric(
        "Coût Complet Association / Élève",
        f"{cout_complet_eleve:,} € / an".replace(",", " "),
        "Hors rémunération enseignants État/MASA" if not is_mfr else "Incl. rémunération moniteurs MFR"
    )

    st.divider()
    if is_agricole:
        st.markdown("#### 🚜 Analyse du Point Mort Internat & Plateaux Techniques")
        col_ag1, col_ag2 = st.columns([1, 1.3])
        with col_ag1:
            cout_interne_ref = st.number_input(
                "Coût complet d'hébergement & restauration par interne (€ / an)",
                min_value=800,
                max_value=6000,
                value=2650,
                step=50
            )
        with col_ag2:
            nb_internes = int(round(eleves_tot * taux_internat / 100))
            cout_tot_internat = nb_internes * cout_interne_ref
            solde_internat = restauration_eur - cout_tot_internat
            if solde_internat >= 0:
                st.success(
                    f"**Équilibre hébergement & restauration (+{solde_internat:,.0f} €) :**\n\n".replace(",", " ") +
                    f"Pour **{nb_internes} internes** ({taux_internat} % de l'effectif), les recettes de pension et d'exploitation (**{restauration_eur:,.0f} €**) couvrent les charges directes estimées (**{cout_tot_internat:,.0f} €**).".replace(",", " ")
                )
            else:
                st.warning(
                    f"**Déficit d'équilibre internat / ateliers ({solde_internat:,.0f} €) :**\n\n".replace(",", " ") +
                    f"Les recettes de pension et d'exploitation (**{restauration_eur:,.0f} €**) sont inférieures au coût complet estimé pour **{nb_internes} internes** (**{cout_tot_internat:,.0f} €**). Ce déficit pèse directement sur la dotation pédagogique MASA.".replace(",", " ")
                )
    else:
        st.markdown("#### 🏛️ Calculette de Parité — Comparaison avec le Coût d'un Élève du Public")
        col_par1, col_par2 = st.columns([1, 1.3])
        with col_par1:
            cout_public_ref = st.number_input(
                "Coût de référence constaté dans le public (€ / élève / an)",
                min_value=200,
                max_value=4000,
                value=int(normes_etab["forfait_ref_eleve"] + 130),
                step=20,
                help="Coût moyen de fonctionnement matériel et personnel non enseignant d'un élève dans l'établissement public de référence."
            )
        with col_par2:
            ecart_parite_eleve = cout_public_ref - forfait_moy_eleve
            enjeu_parite_tot = ecart_parite_eleve * eleves_tot
            if ecart_parite_eleve > 0:
                st.info(
                    f"**Écart de parité constaté : -{ecart_parite_eleve} € / élève / an**\n\n"
                    f"Le forfait versé ({forfait_moy_eleve} €) est inférieur au coût public de référence ({cout_public_ref} €). "
                    f"Sur **{eleves_tot} élèves**, le manque à gagner annuel pour l'OGEC s'élève à **{enjeu_parite_tot:,.0f} € / an**.".replace(",", " ")
                )
            else:
                st.success(
                    f"**Parité atteinte (+{abs(ecart_parite_eleve)} € / élève / an) :**\n\n"
                    f"Le forfait public perçu ({forfait_moy_eleve} €) couvre le coût de référence ({cout_public_ref} €)."
                )

# ------------------------------------------
# ONGLET 5 : NOTE DE SYNTHÈSE CA & FINANCEURS
# ------------------------------------------
with onglets[4]:
    st.subheader("Note de Synthèse Financière (Prête pour Conseil d'Administration ou Collectivité)")
    note_texte = f"""NOTE DE CADRAGE FINANCIER — {etablissement.upper()}
Périmètre : {type_etab} ({eleves_tot} élèves scolarisés | Taux d'internat : {taux_internat} %)
Référentiel comptable : Plan Comptable des Associations (Règlement ANC n° 2018-06)

1. ÉQUILIBRE D'EXPLOITATION & CAPACITÉ D'AUTOFINANCEMENT (EXERCICE CLOS)
- Produits d'exploitation : {total_prod_m:.2f} M€, dont {total_forfaits_m:.2f} M€ de financements publics ({taux_dep_public:.1f} % des produits, soit {forfait_moy_eleve} €/élève) et {contrib_familles_m:.2f} M€ de contributions des familles ({contrib_moy_eleve} €/élève).
- Charges d'exploitation : {total_ch_m:.2f} M€, portées à {poids_ms:.1f} % par les charges de personnel de l'association ({masse_sal_m:.2f} M€ pour {etp_asso} ETP) et à {poids_fluides:.1f} % par les charges fixes externes (énergie, restauration/internat, maintenance).
- Résultat net comptable : {res_net_m:+.2f} M€ | Capacité d'Autofinancement (CAF) : {caf_m:.2f} M€ ({taux_caf:.1f} % des produits, cible sectorielle ≥ {normes_etab['taux_caf_cible']:.1f} %).

2. COUVERTURE PATRIMONIALE, LOYERS AEP & TRÉSORERIE DE SÉCURITÉ
- Les charges liées au patrimoine immobilier et à son financement (dotations aux amortissements de {dot_amort_m:.2f} M€, intérêts d'emprunts de {charges_fin_m:.2f} M€ et loyers immobiliers versés à l'AEP de {loyers_aep_m:.2f} M€, soit {charges_immo_fin_eur/1e6:.2f} M€ au total) sont couvertes à hauteur de {contrib_familles_m:.2f} M€ par les contributions des familles (solde : {solde_regle_or_eur:+,.0f} €).
- L'encours de dette immobilière s'établit à {dette_immo_m:.2f} M€ (capacité de désendettement : {cap_desend_ogec:.1f} ans) pour une trésorerie disponible de {treso_m:.2f} M€ ({jours_treso_init} jours de charges décaissables, cible prudentielle : {normes_etab['jours_treso_cible']}-120 jours).

3. TRAJECTOIRE PROSPECTIVE 2026-2030
- À l'horizon 2030 ({eleves_p[-1]} élèves projetés), le résultat net s'établit à {res_p[-1]:+.2f} M€ et la CAF à {caf_p[-1]:.2f} M€, permettant de soutenir une enveloppe d'investissement de {ppi_immo_m:.2f} M€/an tout en maintenant un point bas de trésorerie à {min(jours_treso_p)} jours.
""".replace(",", " ")
    st.text_area("Texte généré automatiquement (copier-coller vers Word / PDF) :", value=note_texte, height=360)

pdf_ogec_bytes = build_ogec_pdf(
    etablissement, type_etab, is_agricole, eleves_tot, total_prod_m, total_forfaits_m, contrib_familles_m,
    restauration_m, autres_prod_m, masse_sal_m, charges_ext_m, loyers_aep_m, dot_amort_m, charges_fin_m,
    res_net_m, caf_m, remb_cap_m, autofin_m, dette_immo_m, treso_m, jours_treso_init,
    regle_or_ok, annees_proj, prod_p, ch_p, caf_p, treso_p, analyse_ogec
)

with col_pdf:
    st.write("")
    st.download_button(
        "📑 Synthèse PDF (1 p.)",
        data=pdf_ogec_bytes,
        file_name=f"Synthese_Education_{etablissement.replace(' ', '_')}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )
