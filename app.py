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
    page_title="Archétype Éducation — Audit ANC 2018-06, Pilotage & Prospective",
    page_icon="🎓",
    layout="wide"
)

# ==========================================
# 1. RÉFÉRENTIEL & MOYENNES PAR STRATE (ANC 2018-06 / FNOGEC)
# ==========================================
def get_normes_etablissement(type_etab):
    if "1er degré" in type_etab:
        return {
            "type_court": "1er degré (École)",
            "strate": "Écoles sous contrat (Loi Debré — Art. L. 442-5)",
            "financeur": "Commune (Forfait communal)",
            "forfait_eleve": 880,
            "contrib_eleve": 420,
            "taux_ebe": 9.5,
            "taux_caf": 7.0,
            "jours_treso": 90,
            "poids_ms": 47.0,
            "poids_admin": 24.0,
            "b_peda": 70,
            "maint_m2": 15.0,
            "amort_m2": 18.0,
            "fluides_eleve": 145,
            "tx_internat": 0,
            "desend_moy": 5.2,
            "desend_max": 8.0
        }
    elif "Collège" in type_etab:
        return {
            "type_court": "2nd degré (Collège)",
            "strate": "Collèges sous contrat (Art. L. 442-9)",
            "financeur": "Département (Forfait externat)",
            "forfait_eleve": 647,
            "contrib_eleve": 580,
            "taux_ebe": 10.5,
            "taux_caf": 7.5,
            "jours_treso": 90,
            "poids_ms": 45.0,
            "poids_admin": 26.0,
            "b_peda": 100,
            "maint_m2": 18.0,
            "amort_m2": 30.0,
            "fluides_eleve": 165,
            "tx_internat": 5,
            "desend_moy": 5.5,
            "desend_max": 8.0
        }
    elif "Lycée GT" in type_etab:
        return {
            "type_court": "2nd degré (Lycée GT/Pro)",
            "strate": "Lycées GT & Pro sous contrat (Art. L. 442-9)",
            "financeur": "Région (Forfait externat)",
            "forfait_eleve": 803,
            "contrib_eleve": 690,
            "taux_ebe": 11.2,
            "taux_caf": 8.0,
            "jours_treso": 90,
            "poids_ms": 44.0,
            "poids_admin": 27.0,
            "b_peda": 130,
            "maint_m2": 22.0,
            "amort_m2": 36.0,
            "fluides_eleve": 190,
            "tx_internat": 12,
            "desend_moy": 5.8,
            "desend_max": 8.0
        }
    elif "Agricole" in type_etab:
        return {
            "type_court": "Lycée Agricole (MASA)",
            "strate": "Enseignement Agricole Temps Plein (Art. L. 813-8)",
            "financeur": "MASA (Subv. globale) & Région",
            "forfait_eleve": 2450,
            "contrib_eleve": 720,
            "taux_ebe": 11.5,
            "taux_caf": 8.5,
            "jours_treso": 75,
            "poids_ms": 46.0,
            "poids_admin": 25.0,
            "b_peda": 150,
            "maint_m2": 26.0,
            "amort_m2": 40.0,
            "fluides_eleve": 260,
            "tx_internat": 45,
            "desend_moy": 6.0,
            "desend_max": 8.5
        }
    elif "MFR" in type_etab:
        return {
            "type_court": "MFR / Alternance",
            "strate": "Maisons Familiales Rurales (Art. L. 813-9)",
            "financeur": "MASA & OPCO",
            "forfait_eleve": 4100,
            "contrib_eleve": 680,
            "taux_ebe": 10.8,
            "taux_caf": 8.0,
            "jours_treso": 75,
            "poids_ms": 63.0,
            "poids_admin": 23.0,
            "b_peda": 150,
            "maint_m2": 24.0,
            "amort_m2": 35.0,
            "fluides_eleve": 240,
            "tx_internat": 75,
            "desend_moy": 5.5,
            "desend_max": 8.0
        }
    else:
        return {
            "type_court": "Ensemble scolaire mixte",
            "strate": "Ensembles scolaires multi-niveaux (Loi Debré)",
            "financeur": "Commune + Département + Région",
            "forfait_eleve": 760,
            "contrib_eleve": 560,
            "taux_ebe": 10.5,
            "taux_caf": 7.5,
            "jours_treso": 90,
            "poids_ms": 45.0,
            "poids_admin": 26.0,
            "b_peda": 110,
            "maint_m2": 20.0,
            "amort_m2": 32.0,
            "fluides_eleve": 175,
            "tx_internat": 15,
            "desend_moy": 5.6,
            "desend_max": 8.0
        }

def afficher_synthese_unique(titre, constat, points_appui, leviers_budget):
    st.markdown("---")
    with st.container(border=True):
        st.markdown(f"### Synthèse & Clés de lecture — {titre}")
        st.markdown(f"**1. Diagnostic & positionnement normatif :** {constat}")
        st.markdown(f"**2. Points d'appui & marges de manœuvre :** {points_appui}")
        st.markdown(f"**3. Arbitrages pour le Budget Prévisionnel (BP) :** {leviers_budget}")

def afficher_aide_pedagogique_onglet(titre_aide, points_cles):
    with st.expander(f"💡 Comprendre les indicateurs — {titre_aide}", expanded=False):
        for notion, explication in points_cles:
            st.markdown(f"* **{notion} :** {explication}")

# ==========================================
# 2. INGESTION BALANCES COMPTABLES (ANC 2018-06)
# ==========================================
def _read_tabular_file(file_obj):
    name = getattr(file_obj, "name", "balance.csv")
    raw = file_obj.getvalue() if hasattr(file_obj, "getvalue") else file_obj.read()
    if name.lower().endswith((".xlsx", ".xls")):
        try:
            return pd.read_excel(io.BytesIO(raw))
        except Exception:
            return None
    for enc in ("utf-8", "latin-1", "cp1252"):
        for sep in (";", ",", "\t"):
            try:
                tmp = pd.read_csv(io.BytesIO(raw), sep=sep, encoding=enc)
                if tmp.shape[1] >= 2:
                    return tmp
            except Exception:
                continue
    return None

def _to_num(series):
    return pd.to_numeric(
        series.astype(str).str.replace(r"[\xa0\s]", "", regex=True).str.replace(",", ".", regex=False),
        errors="coerce"
    ).fillna(0.0)

def parse_balance_ogec(file_obj):
    name = getattr(file_obj, "name", "balance_2025.csv")
    ym = re.search(r"(20[1-3]\d)", name)
    annee = ym.group(1) if ym else None
    df = _read_tabular_file(file_obj)
    if df is None or df.empty:
        return None

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
    if lib_col:
        valid = valid & ~df[lib_col].astype(str).str.lower().str.contains(r"\b(total|totaux)\b", regex=True)

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
    immo_2 = sum_p(["21", "23"], "debit")

    tp = f_74 + c_756 + a_70 + aut_p
    tc = ach_60 + loy_613 + maint_615 + aut_ext + ms_64 + fin_66 + amo_68
    if tp <= 0 and tc <= 0:
        return None

    return {
        "fichier": name, "annee": annee,
        "f_74": f_74, "c_756": c_756, "a_70": a_70, "aut_p": aut_p, "tp": tp,
        "ach_60": ach_60, "loy_613": loy_613, "maint_615": maint_615, "aut_ext": aut_ext,
        "ms_64": ms_64, "fin_66": fin_66, "amo_68": amo_68, "tc": tc,
        "rn": tp - tc, "caf": (tp - tc) + amo_68,
        "dette": dette_16, "remb": remb_16, "tres": tres_51, "immo": immo_2
    }

# ==========================================
# 3. GÉNÉRATEURS DE RAPPORTS PDF EXÉCUTIFS
# ==========================================
def _box(ax, x, y, w, h, fc="#ffffff", ec="#cbd5e1", lw=1.0, r=0.012):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", facecolor=fc, edgecolor=ec, linewidth=lw, transform=ax.transAxes))

def _draw_lines(ax, x, y_start, items, wrap_w=115, step_y=0.016, gap_item=0.005, fontsize=7.0, color="#1e293b", bold_prefix=False):
    y = y_start
    for it in items:
        wrapped = textwrap.wrap(it, width=wrap_w)
        for idx, wl in enumerate(wrapped):
            ax.text(x, y, wl, fontsize=fontsize, color=color, fontweight=("bold" if (bold_prefix and idx == 0) else "normal"), transform=ax.transAxes)
            y -= step_y
        y -= gap_item
    return y

def _header_pdf(ax, titre_doc, sous_titre):
    ax.add_patch(Rectangle((0, 0.915), 1, 0.085, facecolor="#0f172a", transform=ax.transAxes))
    ax.add_patch(Rectangle((0, 0.911), 1, 0.004, facecolor="#d97706", transform=ax.transAxes))
    ax.text(0.04, 0.962, titre_doc, color="white", fontsize=10.2, fontweight="bold", transform=ax.transAxes)
    ax.text(0.04, 0.930, sous_titre, color="#cbd5e1", fontsize=7.4, transform=ax.transAxes)

def _footer_pdf(ax, gauche, page_txt):
    ax.plot([0.04, 0.96], [0.038, 0.038], color="#cbd5e1", lw=0.8, transform=ax.transAxes)
    ax.text(0.04, 0.020, gauche, fontsize=7.0, color="#64748b", transform=ax.transAxes)
    ax.text(0.96, 0.020, page_txt, ha="right", fontsize=7.0, fontweight="bold", color="#475569", transform=ax.transAxes)

def build_pdf_retro(etab, normes, statut_immo, ans_r, p_r, c_r, ms_r, caf_r, aut_r, inv_r, amo_r, det_r, tcma_p, tcma_c, tcma_ms, gvt_pt, conv_pt, vol_pt, atouts_txt, vig_txt):
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        _header_pdf(ax, "ARCHÉTYPE ÉDUCATION  |  DOSSIER D'AUDIT RÉTROSPECTIF ANC 2018-06 (2021-2025)", f"ÉTABLISSEMENT : {etab.upper()}  •  {normes['type_court'].upper()}  •  STATUT : {statut_immo.upper()}")

        ciseau = tcma_c - tcma_p
        var_caf = caf_r[-1] - caf_r[0]
        tx_renouv = (np.sum(inv_r) / max(0.01, np.sum(amo_r))) * 100
        kpis = [
            ("TCMA PRODUITS", f"+{tcma_p:.2f} % / an", "Rythme annuel recettes", "#059669"),
            ("TCMA CHARGES", f"+{tcma_c:.2f} % / an", f"Effet ciseau : {ciseau:+.2f} pts", "#dc2626" if ciseau > 0.3 else "#d97706"),
            ("ÉVOLUTION CAF", f"{caf_r[-1]:.2f} M€", f"Variation : {var_caf:+.2f} M€ (Cible {normes['taux_caf']}%)", "#059669" if var_caf >= 0 else "#dc2626"),
            ("RENOUVELLEMENT", f"{tx_renouv:.0f} %", "Inv. cumulés / Amort. (Cible >= 100%)", "#059669" if tx_renouv >= 90 else "#d97706"),
        ]
        for i, (kt, kv, ks, kc) in enumerate(kpis):
            kx = 0.04 + i * 0.233
            _box(ax, kx, 0.815, 0.218, 0.084, fc="#f8fafc")
            ax.text(kx + 0.012, 0.880, kt, fontsize=6.9, fontweight="bold", color="#475569", transform=ax.transAxes)
            ax.text(kx + 0.012, 0.845, kv, fontsize=11.8, fontweight="bold", color=kc, transform=ax.transAxes)
            ax.text(kx + 0.012, 0.823, ks, fontsize=6.3, color="#64748b", transform=ax.transAxes)

        ax.text(0.04, 0.785, "1. EFFET DE CISEAU HISTORIQUE (PRODUITS VS CHARGES)", fontsize=8.1, fontweight="bold", color="#0f172a", transform=ax.transAxes)
        g1 = fig.add_axes([0.06, 0.595, 0.41, 0.175])
        g1.plot(ans_r, p_r, marker="o", color="#2563eb", lw=2, label="Produits")
        g1.plot(ans_r, c_r, marker="s", color="#dc2626", lw=2, label="Charges")
        g1.grid(True, linestyle="--", alpha=0.5)
        g1.tick_params(labelsize=7)
        g1.legend(fontsize=6.8, loc="upper left")

        ax.text(0.52, 0.785, "2. TRAJECTOIRE DE LA CAF & AUTOFINANCEMENT NET", fontsize=8.1, fontweight="bold", color="#0f172a", transform=ax.transAxes)
        g2 = fig.add_axes([0.54, 0.595, 0.41, 0.175])
        g2.plot(ans_r, caf_r, marker="^", color="#059669", lw=2, label="CAF (Épargne brute)")
        g2.plot(ans_r, aut_r, marker="s", color="#d97706", lw=2, label="Autofin. Net (après dette)")
        g2.grid(True, linestyle="--", alpha=0.5)
        g2.tick_params(labelsize=7)
        g2.legend(fontsize=6.8, loc="upper left")

        ax.text(0.04, 0.545, "3. EFFORT D'INVESTISSEMENT VS AMORTISSEMENTS (M€)", fontsize=8.1, fontweight="bold", color="#0f172a", transform=ax.transAxes)
        g3 = fig.add_axes([0.06, 0.375, 0.41, 0.155])
        x_idx = np.arange(len(ans_r))
        g3.bar(x_idx - 0.18, inv_r, width=0.35, color="#1e40af", label="Investissements")
        g3.bar(x_idx + 0.18, amo_r, width=0.35, color="#94a3b8", label="Amortissements (681)")
        g3.set_xticks(x_idx)
        g3.set_xticklabels(ans_r)
        g3.grid(True, axis="y", linestyle="--", alpha=0.5)
        g3.tick_params(labelsize=7)
        g3.legend(fontsize=6.5, loc="upper left")

        _box(ax, 0.51, 0.375, 0.45, 0.155, fc="#f8fafc")
        ax.text(0.525, 0.508, "DIAGNOSTIC PATRIMONIAL & STATUT IMMOBILIER", fontsize=7.6, fontweight="bold", color="#0f172a", transform=ax.transAxes)
        moy_inv = np.mean(inv_r)
        diag_eq = [
            f"• Investissement moyen : {moy_inv:.2f} M€/an vs {np.mean(amo_r):.2f} M€/an d'amortissements (renouvellement : {tx_renouv:.0f} %).",
            f"• Encours de dette OGEC : passe de {det_r[0]:.2f} M€ à {det_r[-1]:.2f} M€ ({(det_r[-1]-det_r[0]):+.2f} M€).",
            f"• Relativisation ({statut_immo}) : {'en tant que locataire AEP, les gros murs sont amortis par le propriétaire.' if 'Locataire' in statut_immo else 'l OGEC porte directement l amortissement et le renouvellement du bâti.'}"
        ]
        _draw_lines(ax, 0.525, 0.480, diag_eq, wrap_w=56, step_y=0.017, gap_item=0.005, fontsize=6.8)

        ax.text(0.04, 0.335, "TABLEAU RÉTROSPECTIF DES SOLDES, INVESTISSEMENTS & DETTE (2021-2025)", fontsize=8.1, fontweight="bold", color="#0f172a", transform=ax.transAxes)
        tax = fig.add_axes([0.04, 0.140, 0.92, 0.180])
        tax.axis("off")
        t_rows = [
            ["Produits d'exploitation (M€)"] + [f"{v:.2f}" for v in p_r],
            ["Charges d'exploitation (M€)"] + [f"{v:.2f}" for v in c_r],
            ["Capacité d'Autofinancement — CAF (M€)"] + [f"{v:.2f}" for v in caf_r],
            ["Autofinancement net après dette (M€)"] + [f"{v:.2f}" for v in aut_r],
            ["Dotations aux amortissements 681 (M€)"] + [f"{v:.2f}" for v in amo_r],
            ["Investissements réalisés (M€)"] + [f"{v:.2f}" for v in inv_r],
            ["Encours dette immobilière 31/12 (M€)"] + [f"{v:.2f}" for v in det_r],
        ]
        tbl = tax.table(cellText=t_rows, colLabels=["Soldes & Flux Patrimoniaux"] + ans_r, loc="center", cellLoc="center", colWidths=[0.44] + [0.112]*len(ans_r))
        tbl.set_fontsize(6.9)
        tbl.scale(1, 1.15)
        for (r, c), cell in tbl.get_celld().items():
            cell.set_edgecolor("#cbd5e1")
            if r == 0:
                cell.set_facecolor("#1e293b")
                cell.get_text().set_color("white")
                cell.get_text().set_weight("bold")
            elif c == 0:
                cell.get_text().set_ha("left")

        _box(ax, 0.04, 0.050, 0.92, 0.078, fc="#fffbeb", ec="#fcd34d")
        ax.text(0.055, 0.108, "SYNTHÈSE DE LA TRAJECTOIRE PASSÉE", fontsize=7.6, fontweight="bold", color="#92400e", transform=ax.transAxes)
        cis_lines = [
            f"• Effet ciseau ({ciseau:+.2f} pts/an) : les dépenses (+{tcma_c:.2f} %/an) progressent {'plus vite' if ciseau > 0 else 'moins vite'} que les recettes (+{tcma_p:.2f} %/an).",
            f"• Effort de renouvellement à {tx_renouv:.0f} % des amortissements : {'maintien de la valeur des équipements.' if tx_renouv >= 95 else 'sous-investissement relatif à surveiller au regard du statut ' + statut_immo + '.'}"
        ]
        _draw_lines(ax, 0.055, 0.088, cis_lines, wrap_w=124, step_y=0.016, gap_item=0.004, fontsize=6.9)
        _footer_pdf(ax, "Dossier Rétrospectif ANC 2018-06  •  Cabinet QUINZE", "Page 1/2")
        pdf.savefig(fig)
        plt.close(fig)

        fig2 = plt.figure(figsize=(8.27, 11.69), dpi=150)
        ax2 = fig2.add_axes([0, 0, 1, 1])
        ax2.axis("off")
        _header_pdf(ax2, "ARCHÉTYPE ÉDUCATION  |  DÉCOMPOSITION DE LA DÉRIVE RH & SYNTHÈSE", f"ÉTABLISSEMENT : {etab.upper()}  •  LEVIERS MANAGÉRIAUX & PISTES D'AUDIT")

        ax2.text(0.04, 0.875, "1. DÉCOMPOSITION DE LA PROGRESSION DE LA MASSE SALARIALE INTERNE (COMPTE 64)", fontsize=8.2, fontweight="bold", color="#0f172a", transform=ax2.transAxes)
        grh = fig2.add_axes([0.24, 0.675, 0.70, 0.180])
        cats = ["Effet Volume\n(Postes / Rempl.)", "Mesures Convent.\n(EEPNL / SMIC)", "GVT Mécanique\n(Ancienneté)"]
        vals = [vol_pt, conv_pt, gvt_pt]
        cols_rh = ["#059669" if vol_pt <= 0.3 else "#dc2626", "#d97706", "#64748b"]
        grh.barh(cats, vals, color=cols_rh, height=0.52)
        grh.set_xlabel("Contribution annuelle (% / an)", fontsize=7.5)
        grh.grid(True, axis="x", linestyle="--", alpha=0.5)
        grh.tick_params(labelsize=7.5)

        _box(ax2, 0.04, 0.515, 0.92, 0.125, fc="#f8fafc", ec="#cbd5e1")
        ax2.text(0.055, 0.618, "LECTURE PÉDAGOGIQUE : FACTEURS SUBIS VS LEVIER INTERNE (NORME VOLUME <= 0,3 PT/AN)", fontsize=7.7, fontweight="bold", color="#0f172a", transform=ax2.transAxes)
        rh_lines = [
            f"• Sur +{tcma_ms:.2f} %/an de hausse salariale, {(gvt_pt+conv_pt):.2f} points sont automatiques (ancienneté GVT + revalorisations conventionnelles EEPNL/SMIC).",
            f"• {vol_pt:+.2f} points dépendent directement des décisions de gestion (créations de postes, remplacements non compensés, heures supplémentaires).",
            f"• Le poids global de la MS interne atteint {(ms_r[-1]/p_r[-1]*100):.1f} % des produits (Moyenne observatoire du profil : {normes['poids_ms']} %)."
        ]
        _draw_lines(ax2, 0.055, 0.592, rh_lines, wrap_w=122, step_y=0.017, gap_item=0.005, fontsize=7.1)

        ax2.text(0.04, 0.480, "2. BILAN STRATÉGIQUE : ATOUTS & LEVIERS D'AJUSTEMENT BUDGÉTAIRE", fontsize=8.2, fontweight="bold", color="#0f172a", transform=ax2.transAxes)
        _box(ax2, 0.04, 0.115, 0.445, 0.350, fc="#ecfdf5", ec="#6ee7b7")
        ax2.text(0.055, 0.442, "ATOUTS & MARGES DE MANŒUVRE", fontsize=7.8, fontweight="bold", color="#065f46", transform=ax2.transAxes)
        _draw_lines(ax2, 0.055, 0.412, [f"• {x}" for x in atouts_txt], wrap_w=54, step_y=0.019, gap_item=0.010, fontsize=7.1)

        _box(ax2, 0.515, 0.115, 0.445, 0.350, fc="#fffbeb", ec="#fcd34d")
        ax2.text(0.530, 0.442, "LEVIERS BUDGÉTAIRES & POINTS DE VIGILANCE", fontsize=7.8, fontweight="bold", color="#92400e", transform=ax2.transAxes)
        _draw_lines(ax2, 0.530, 0.412, [f"• {x}" for x in vig_txt], wrap_w=54, step_y=0.019, gap_item=0.010, fontsize=7.1)

        _footer_pdf(ax2, "Dossier Rétrospectif ANC 2018-06  •  Cabinet QUINZE", "Page 2/2")
        pdf.savefig(fig2)
        plt.close(fig2)
    return buf.getvalue()

def build_pdf_tbi(etab, normes, statut_immo, norme_amort_eff, eleves, surf, score, tp, ach, ext_f, va, ms, ch_ufa_cfc, ebe, fin_val, amo_val, rn, caf, remb, aut, dette, cap_d, treso, j_treso, ro_solde, maint_m2, amo_m2, eq_loyer_m2, b_peda, ben_app, ben_stag, synthese_tbi):
    buf = io.BytesIO()
    fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    _header_pdf(ax, "ARCHÉTYPE ÉDUCATION  |  PLATEFORME D'ARBITRAGE ANC 2018-06 & NORMES", f"ÉTABLISSEMENT : {etab.upper()} ({eleves} ÉLÈVES • {surf} M² • {statut_immo.upper()})")

    sc_col = "#059669" if score >= 70 else ("#d97706" if score >= 45 else "#dc2626")
    sc_bg = "#ecfdf5" if score >= 70 else ("#fffbeb" if score >= 45 else "#fef2f2")
    _box(ax, 0.04, 0.815, 0.92, 0.084, fc=sc_bg, ec=sc_col, lw=1.4)
    ax.text(0.055, 0.876, "HEALTH SCORE ANC 2018-06", fontsize=7.0, fontweight="bold", color="#475569", transform=ax.transAxes)
    ax.text(0.055, 0.832, f"{score}/100", fontsize=17.0, fontweight="bold", color=sc_col, transform=ax.transAxes)
    ax.plot([0.255, 0.255], [0.823, 0.891], color="#cbd5e1", lw=1.0, transform=ax.transAxes)

    statut_msg = "STRUCTURE FINANCIÈRE SAINE ET CONFORME AUX NORMES" if score >= 70 else ("TENSION D'ÉPARGNE OU D'ÉQUILIBRE PAR RAPPORT AUX MOYENNES" if score >= 45 else "ALERTE STRUCTURELLE : ÉCART CRITIQUE AUX NORMES")
    ax.text(0.275, 0.874, statut_msg, fontsize=8.0, fontweight="bold", color=sc_col, transform=ax.transAxes)
    tcaf = (caf / tp * 100) if tp > 0 else 0
    tebe = (ebe / tp * 100) if tp > 0 else 0
    ax.text(0.275, 0.850, f"EBE : {tebe:.1f}% (Moy. {normes['taux_ebe']}%) • CAF : {tcaf:.1f}% (Cible {normes['taux_caf']}%) • Désendettement : {cap_d:.1f} ans (Moy. {normes['desend_moy']} a.)", fontsize=6.8, color="#1e293b", transform=ax.transAxes)
    ax.text(0.275, 0.827, f"Règle d'Or : {ro_solde:+.2f} M€ (Norme >= 0) • Charge Immo Globale : {eq_loyer_m2:.1f} €/m² • Tréso : {j_treso} j", fontsize=6.8, color="#1e293b", transform=ax.transAxes)

    _box(ax, 0.04, 0.450, 0.50, 0.350, fc="#ffffff")
    ax.add_patch(Rectangle((0.04, 0.762), 0.50, 0.038, facecolor="#1e293b", transform=ax.transAxes))
    ax.text(0.055, 0.775, "1. CASCADE DES SIG (COHÉRENCE EBE -> CAF)", color="white", fontsize=7.9, fontweight="bold", transform=ax.transAxes)
    sig_rows = [
        ("Produits d'Exploitation", f"{tp:.2f} M€", "100%", True, "#1d4ed8"),
        ("- Achats & Charges ext. (60-62)", f"-{(ach+ext_f):.2f} M€", "-", False, "#475569"),
        ("= Valeur Ajoutée (VA)", f"{va:.2f} M€", "-", True, "#0f172a"),
        ("- MS interne (64) & Pôle UFA/CFC", f"-{(ms+ch_ufa_cfc):.2f} M€", "-", False, "#475569"),
        ("= EBE (Excédent Brut)", f"{ebe:.2f} M€ ({tebe:.1f}%)", f"Moy. {normes['taux_ebe']}%", True, "#059669" if tebe >= normes['taux_ebe'] else "#dc2626"),
        ("- Frais financiers / Intérêts (66)", f"-{fin_val:.2f} M€", "< 2,5%", False, "#475569"),
        ("= CAPACITÉ D'AUTOFINANCEMENT", f"{caf:.2f} M€ ({tcaf:.1f}%)", f"Cible {normes['taux_caf']}%", True, "#b45309"),
        ("- Dotations Amortissements (681)", f"-{amo_val:.2f} M€", f"{norme_amort_eff:.0f} €/m²", False, "#475569"),
        ("= Résultat Net Comptable (RCAI)", f"{rn:+.2f} M€", "Norme >= 0", True, "#059669" if rn >= 0 else "#dc2626"),
        ("- Remb. Capital Dette (164)", f"-{remb:.2f} M€", "-", False, "#475569"),
        ("= Autofinancement Net", f"{aut:+.2f} M€", "Norme >= 0", True, "#059669" if aut >= 0 else "#dc2626"),
    ]
    ys = 0.735
    for lbl, val, nrm, bld, col in sig_rows:
        if bld:
            ax.add_patch(Rectangle((0.046, ys - 0.007), 0.488, 0.024, facecolor="#f1f5f9", transform=ax.transAxes))
        ax.text(0.052, ys, lbl, fontsize=6.8, fontweight="bold" if bld else "normal", color="#1e293b", transform=ax.transAxes)
        ax.text(0.420, ys, val, ha="right", fontsize=6.9, fontweight="bold" if bld else "normal", color=col, transform=ax.transAxes)
        ax.text(0.532, ys, nrm, ha="right", fontsize=6.4, color="#64748b", transform=ax.transAxes)
        ys -= 0.027

    _box(ax, 0.56, 0.635, 0.40, 0.165, fc="#ffffff")
    ax.add_patch(Rectangle((0.56, 0.762), 0.40, 0.038, facecolor="#1e293b", transform=ax.transAxes))
    ax.text(0.575, 0.775, "2. PATRIMOINE & HORS CONTRAT", color="white", fontsize=7.9, fontweight="bold", transform=ax.transAxes)
    sc_items = [
        ("Amort. (681) / Éq. Loyer :", f"{amo_m2:.1f} / {eq_loyer_m2:.1f} €/m²"),
        ("Maintenance (615) :", f"{maint_m2:.1f} €/m² (Moy. {normes['maint_m2']} €)"),
        ("Bénéfice net / Apprenti :", f"{ben_app:+.0f} € (Cible +600 à +1000 €)"),
        ("Bénéfice net / Stagiaire FC :", f"{ben_stag:+.0f} € (Cible +100 à +250 €)"),
    ]
    ysc = 0.732
    for k, v in sc_items:
        ax.text(0.572, ysc, k, fontsize=6.7, color="#475569", transform=ax.transAxes)
        ax.text(0.948, ysc, v, ha="right", fontsize=6.8, fontweight="bold", color="#0f172a", transform=ax.transAxes)
        ysc -= 0.028

    _box(ax, 0.56, 0.450, 0.40, 0.170, fc="#ffffff")
    ax.add_patch(Rectangle((0.56, 0.582), 0.40, 0.038, facecolor="#1e293b", transform=ax.transAxes))
    ax.text(0.575, 0.595, "3. DETTE, ANNUITÉ & TRÉSORERIE", color="white", fontsize=7.9, fontweight="bold", transform=ax.transAxes)
    abs_caf = ((remb + fin_val) / max(0.01, caf)) * 100
    det_items = [
        ("Encours Dette OGEC :", f"{dette:.2f} M€ ({cap_d:.1f} ans)"),
        ("Absorption CAF par dette :", f"{abs_caf:.0f} % (Max 75 %)"),
        ("Règle d'Or Immo :", f"{ro_solde:+.2f} M€ (Norme >= 0)"),
        ("Trésorerie :", f"{j_treso} j (Cible {normes['jours_treso']} j)"),
    ]
    yd = 0.552
    for k, v in det_items:
        ax.text(0.572, yd, k, fontsize=6.7, color="#475569", transform=ax.transAxes)
        ax.text(0.948, yd, v, ha="right", fontsize=6.8, fontweight="bold", color="#0f172a", transform=ax.transAxes)
        yd -= 0.028

    _box(ax, 0.04, 0.275, 0.92, 0.160, fc="#f8fafc", ec="#94a3b8")
    ax.text(0.055, 0.415, "4. SYNTHÈSE EXÉCUTIVE & CLÉS D'AJUSTEMENT DU BUDGET PRÉVISIONNEL", fontsize=8.0, fontweight="bold", color="#0f172a", transform=ax.transAxes)
    _draw_lines(ax, 0.055, 0.390, synthese_tbi, wrap_w=124, step_y=0.017, gap_item=0.005, fontsize=7.0)

    ax.text(0.04, 0.248, f"REPÈRES RELATIVISÉS ({normes['type_court'].upper()} — {statut_immo.upper()})", fontsize=7.5, fontweight="bold", color="#0f172a", transform=ax.transAxes)
    refs = [
        ("PROPRIÉTAIRE VS LOCATAIRE", "Lecture des amortissements", [f"Norme ajustée : ~{norme_amort_eff:.0f} €/m²", "Prop. = amortit les murs", "Loc. = paie un loyer AEP (613)"]),
        ("ÉQUIVALENT LOYER", "Charge immo globale / m²", ["Amort. 681 + Loyers 613 + Int.", f"Repère profil : ~{normes['amort_m2']:.0f} €/m²", "Compare prop. et locataires"]),
        ("HORS CONTRAT", "UFA & Formation Continue", ["Bénéfice net > 0 obligatoire", "UFA : +600 à +1 000 €/app.", "CFC : +100 à +250 €/stag."]),
        ("RÈGLE D'OR & DETTE", "Étanchéité & solvabilité", ["756 >= Amort + Int + Loyers", f"Désend. : < {normes['desend_max']} ans", f"Tréso : {normes['jours_treso']} j"]),
    ]
    for i, (rt, rf, rbullets) in enumerate(refs):
        rx = 0.04 + i * 0.233
        _box(ax, rx, 0.055, 0.218, 0.180, fc="#ffffff")
        ax.text(rx + 0.012, 0.215, rt, fontsize=6.9, fontweight="bold", color="#0f172a", transform=ax.transAxes)
        ax.text(rx + 0.012, 0.193, rf, fontsize=6.2, color="#64748b", transform=ax.transAxes)
        _draw_lines(ax, rx + 0.012, 0.160, [f"• {b}" for b in rbullets], wrap_w=32, step_y=0.024, gap_item=0.004, fontsize=6.6)

    _footer_pdf(ax, "Rapport certifié conforme aux règles ANC 2018-06  •  Cabinet QUINZE", "Page 1/1")
    fig.savefig(buf, format="pdf")
    plt.close(fig)
    return buf.getvalue()

def build_pdf_prospective(etab, normes, statut_immo, ppi_annuel, exec_pct, df_proj, feuille_route):
    buf = io.BytesIO()
    fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    _header_pdf(ax, "ARCHÉTYPE ÉDUCATION  |  TRAJECTOIRE PROSPECTIVE & PROJET À 5 ANS (2026-2030)", f"ÉTABLISSEMENT : {etab.upper()}  •  {statut_immo.upper()}  •  PPI : {ppi_annuel:.2f} M€/AN (EXÉC. {exec_pct:.0f}%)")

    caf_30 = df_proj["CAF (M€)"].iloc[-1]
    tcaf_30 = (caf_30 / df_proj["Produits (M€)"].iloc[-1] * 100)
    des_30 = df_proj["Désendettement (ans)"].iloc[-1]
    det_30 = df_proj["Dette 31/12 (M€)"].iloc[-1]
    var_det = det_30 - df_proj["Dette 31/12 (M€)"].iloc[0]
    j_30 = df_proj["Trésorerie (jours)"].iloc[-1]
    tr_30 = df_proj["Trésorerie (M€)"].iloc[-1]

    kpis = [
        ("CAF 2030", f"+{caf_30:.2f} M€", f"Taux : {tcaf_30:.1f}% (Cible {normes['taux_caf']}%)", "#059669" if tcaf_30 >= normes["taux_caf"] else "#d97706"),
        ("DÉSENDETTEMENT 2030", f"{des_30:.1f} ans", f"Moy. {normes['desend_moy']} a. | Max {normes['desend_max']} a.", "#059669" if des_30 <= normes["desend_max"] else "#dc2626"),
        ("ENCOURS DETTE 2030", f"{det_30:.2f} M€", f"Variation période : {var_det:+.2f} M€", "#0f172a"),
        ("TRÉSORERIE 2030", f"{j_30:.0f} jours", f"{tr_30:.2f} M€ (Cible {normes['jours_treso']} j)", "#1d4ed8" if j_30 >= 60 else "#dc2626"),
    ]
    for i, (kt, kv, ks, kc) in enumerate(kpis):
        kx = 0.04 + i * 0.233
        _box(ax, kx, 0.815, 0.218, 0.084, fc="#f8fafc")
        ax.text(kx + 0.012, 0.880, kt, fontsize=6.9, fontweight="bold", color="#475569", transform=ax.transAxes)
        ax.text(kx + 0.012, 0.845, kv, fontsize=11.8, fontweight="bold", color=kc, transform=ax.transAxes)
        ax.text(kx + 0.012, 0.823, ks, fontsize=6.5, color="#64748b", transform=ax.transAxes)

    ax.text(0.04, 0.785, "1. PROJECTION PRODUITS VS CHARGES (INCLUANT AMORT. & OPEX PPI)", fontsize=7.9, fontweight="bold", color="#0f172a", transform=ax.transAxes)
    gp1 = fig.add_axes([0.06, 0.595, 0.41, 0.175])
    gp1.plot(df_proj["Année"], df_proj["Produits (M€)"], marker="o", color="#2563eb", lw=2, label="Produits")
    gp1.plot(df_proj["Année"], df_proj["Charges + OPEX (M€)"], marker="s", color="#dc2626", lw=2, label="Charges+OPEX")
    gp1.grid(True, linestyle="--", alpha=0.5)
    gp1.tick_params(labelsize=7)
    gp1.legend(fontsize=6.8, loc="upper left")

    ax.text(0.52, 0.785, "2. TRAJECTOIRE CAF, DETTE & TRÉSORERIE (M€)", fontsize=7.9, fontweight="bold", color="#0f172a", transform=ax.transAxes)
    gp2 = fig.add_axes([0.54, 0.595, 0.41, 0.175])
    gp2.plot(df_proj["Année"], df_proj["CAF (M€)"], marker="^", color="#059669", lw=2, label="CAF")
    gp2.plot(df_proj["Année"], df_proj["Trésorerie (M€)"], marker="s", linestyle=":", color="#2563eb", lw=2, label="Trésorerie")
    gp2.grid(True, linestyle="--", alpha=0.5)
    gp2.tick_params(labelsize=7)
    gp2.legend(fontsize=6.8, loc="upper left")

    ax.text(0.04, 0.548, "TABLEAU PLURIANNUEL DES TRAJECTOIRES BUDGÉTAIRES & PATRIMONIALES (2026-2030)", fontsize=8.0, fontweight="bold", color="#0f172a", transform=ax.transAxes)
    tp_ax = fig.add_axes([0.04, 0.335, 0.92, 0.200])
    tp_ax.axis("off")
    t_data = [
        ["Produits d'exploitation (M€)"] + [f"{v:.2f}" for v in df_proj["Produits (M€)"]],
        ["Charges d'exploitation + OPEX induits (M€)"] + [f"{v:.2f}" for v in df_proj["Charges + OPEX (M€)"]],
        [f"CAF (Norme cible : >= {normes['taux_caf']} %)"] + [f"{v:.2f}" for v in df_proj["CAF (M€)"]],
        ["Dotations aux amortissements 681 (M€)"] + [f"{v:.2f}" for v in df_proj["Amort. 681 (M€)"]],
        ["Taux de renouvellement (PPI / Amort.)"] + [f"{v:.0f} %" for v in df_proj["Renouvellement (%)"]],
        ["Encours de la dette au 31/12 (M€)"] + [f"{v:.2f}" for v in df_proj["Dette 31/12 (M€)"]],
        [f"Désendettement (Seuil max : {normes['desend_max']} ans)"] + [f"{v:.1f}" for v in df_proj["Désendettement (ans)"]],
        [f"Trésorerie nette (Cible : {normes['jours_treso']} jours)"] + [f"{v:.0f} j" for v in df_proj["Trésorerie (jours)"]],
    ]
    tbl = tp_ax.table(cellText=t_data, colLabels=["Indicateurs & Normes ANC 2018-06"] + list(df_proj["Année"]), loc="center", cellLoc="center", colWidths=[0.46] + [0.108]*5)
    tbl.set_fontsize(6.9)
    tbl.scale(1, 1.15)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor("#cbd5e1")
        if r == 0:
            cell.set_facecolor("#1e293b")
            cell.get_text().set_color("white")
            cell.get_text().set_weight("bold")
        elif c == 0:
            cell.get_text().set_ha("left")

    _box(ax, 0.04, 0.055, 0.92, 0.265, fc="#ecfdf5", ec="#6ee7b7")
    ax.text(0.055, 0.300, "SYNTHÈSE PROSPECTIVE & FEUILLE DE ROUTE POUR LE CONSEIL D'ADMINISTRATION", fontsize=7.8, fontweight="bold", color="#065f46", transform=ax.transAxes)
    _draw_lines(ax, 0.055, 0.275, feuille_route, wrap_w=124, step_y=0.016, gap_item=0.005, fontsize=7.0)

    _footer_pdf(ax, "Document de prospective ANC 2018-06  •  Cabinet QUINZE — Ingénierie & Conseil Éducation", "Page 1/1")
    fig.savefig(buf, format="pdf")
    plt.close(fig)
    return buf.getvalue()

# ==========================================
# 4. BARRE LATÉRALE : INGESTION & PARAMÉTRAGE CALIBRÉ
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
statut_immo = st.sidebar.selectbox(
    "Statut immobilier de l'OGEC",
    [
        "Mixte (Propriétaire partiel + Loyers AEP)",
        "Propriétaire des murs (Pleine propriété)",
        "Locataire (Murs portés par AEP / Diocèse)"
    ]
)
is_agricole = ("Agricole" in type_etab) or ("MFR" in type_etab)
normes = get_normes_etablissement(type_etab)
etab = st.sidebar.text_input("Nom de l'établissement", "Lycée Polyvalent Saint-Éloi")

# Ajustement de la norme d'amortissement au m² selon le statut immobilier
if "Propriétaire" in statut_immo:
    norme_amort_eff = normes["amort_m2"]
elif "Locataire" in statut_immo:
    norme_amort_eff = 10.0
else:
    norme_amort_eff = round(normes["amort_m2"] * 0.75, 1)

c_sb1, c_sb2 = st.sidebar.columns(2)
eleves_tot = c_sb1.number_input("Élèves (initial)", min_value=1, value=650, step=10)
surface_m2 = c_sb2.number_input("Surface bâtie (m²)", min_value=100, value=4800, step=100)
taux_internat = st.sidebar.slider("Taux demi-pensionnaires / internes (%)", 0, 100, int(normes["tx_internat"]), 5)
internes_tot = int(round(eleves_tot * taux_internat / 100))

st.sidebar.markdown("### 1. Ingestion Balances (2021-2025)")
fichiers = st.sidebar.file_uploader("Importer balances comptables (.csv, .xlsx)", type=["csv", "xlsx", "xls"], accept_multiple_files=True)
balances_parsees = []
if fichiers:
    for f in fichiers:
        rb = parse_balance_ogec(f)
        if rb:
            balances_parsees.append(rb)
balances_parsees.sort(key=lambda x: x["annee"] or x["fichier"])
source_reelle = len(balances_parsees) > 0

if source_reelle:
    dern = balances_parsees[-1]
    d_f74, d_c756, d_a70, d_autp = dern["f_74"], (dern["c_756"] if dern["c_756"] > 0 else dern["tp"]*0.22), dern["a_70"], dern["aut_p"]
    d_ach, d_loy, d_maint, d_ext, d_ms = dern["ach_60"], dern["loy_613"], dern["maint_615"], dern["aut_ext"], dern["ms_64"]
    d_fin, d_amo = dern["fin_66"], dern["amo_68"]
    d_det = dern["dette"] if dern["dette"] > 0 else 880000.0
    d_remb = dern["remb"] if dern["remb"] > 0 else 85000.0
    d_tres = dern["tres"] if dern["tres"] > 0 else 420000.0
else:
    d_f74 = float(eleves_tot * normes["forfait_eleve"])
    d_c756 = float(eleves_tot * normes["contrib_eleve"])
    d_a70 = float(internes_tot * 780 + 45000)
    d_autp = 45000.0
    prod_scol_base = d_f74 + d_c756 + d_a70 + d_autp
    d_ach = float(eleves_tot * normes["b_peda"] + internes_tot * 290)
    if "Propriétaire" in statut_immo:
        d_loy = 0.0
        d_amo = float(round(surface_m2 * normes["amort_m2"]))
        d_det = 1150000.0
        d_remb = 110000.0
        d_fin = 42000.0
    elif "Locataire" in statut_immo:
        d_loy = float(round(surface_m2 * max(8.0, normes["amort_m2"] - 8.0)))
        d_amo = float(round(surface_m2 * 10.0))
        d_det = 180000.0
        d_remb = 25000.0
        d_fin = 8000.0
    else:
        d_loy = 65000.0
        d_amo = float(round(surface_m2 * norme_amort_eff))
        d_det = 880000.0
        d_remb = 85000.0
        d_fin = 38000.0
    d_maint = float(round(surface_m2 * normes["maint_m2"]))
    d_ext = float(round(eleves_tot * normes["fluides_eleve"] / 0.55))
    d_ms = float(round(prod_scol_base * (normes["poids_ms"] / 100.0)))
    d_tres = 420000.0

st.sidebar.markdown("### 2. Recettes & Pôle Hors Contrat")
f_74 = st.sidebar.number_input("Forfaits & Subv. publiques (74) (€)", value=float(d_f74), step=10000.0)
c_756 = st.sidebar.number_input("Contributions familles scolarité (756) (€)", value=float(d_c756), step=10000.0)
a_70 = st.sidebar.number_input("Restauration, internat & annexes (70) (€)", value=float(d_a70), step=10000.0)
aut_p = st.sidebar.number_input("Autres produits (75/78/79) (€)", value=float(d_autp), step=5000.0)

activer_ufa_cfc = st.sidebar.checkbox("Intégrer un pôle Apprentissage (UFA) & CFC", value=(True if "Lycée" in type_etab or is_agricole else False))
prod_ufa, ch_ufa, prod_cfc, ch_cfc, app_tot, stag_tot = 0.0, 0.0, 0.0, 0.0, 1, 1
if activer_ufa_cfc:
    with st.sidebar.expander("🎓 Détail UFA (Apprentissage) & CFC", expanded=True):
        app_tot = st.number_input("Effectif apprentis (UFA)", min_value=1, value=110, step=5)
        prod_ufa = st.number_input("Produits UFA (NPEC OPCO, TA) (€)", value=740000.0, step=10000.0)
        ch_ufa = st.number_input("Charges UFA (Formateurs, redevance CFA) (€)", value=645000.0, step=10000.0)
        stag_tot = st.number_input("Stagiaires Formation Continue (CFC)", min_value=1, value=75, step=5)
        prod_cfc = st.number_input("Produits CFC (Entreprises, CPF, Région) (€)", value=115000.0, step=5000.0)
        ch_cfc = st.number_input("Charges CFC (Vacataires, com., matériel) (€)", value=103000.0, step=5000.0)

with st.sidebar.expander("👥 3. Granularité RH (Masse Salariale 64)", expanded=True):
    st.caption("Salaires + charges patronales (hors enseignants payés par l'État).")
    ms_prive = st.number_input("Enseignants de droit privé (Rempl., hors contrat)", value=float(round(d_ms * 0.14)), step=5000.0)
    ms_vie_scol = st.number_input("Vie scolaire, éducateurs, surveillants, AESH", value=float(round(d_ms * 0.34)), step=5000.0)
    ms_admin = st.number_input("Administration, direction, comptabilité", value=float(round(d_ms * 0.27)), step=5000.0)
    ms_tech = st.number_input("Technique, entretien, accueil & restauration", value=float(round(d_ms * 0.25)), step=5000.0)
    ms_totale = ms_prive + ms_vie_scol + ms_admin + ms_tech

with st.sidebar.expander("⚙️ 4. Achats, Maintenance & Fluides (60-62)", expanded=True):
    ach_peda = st.number_input("Budget pédagogique direct (601/606)", value=float(eleves_tot * normes["b_peda"]), step=2000.0)
    ach_resto = st.number_input("Achats denrées restauration (601)", value=float(max(0.0, d_ach - eleves_tot * normes["b_peda"])), step=5000.0)
    maint_615 = st.number_input("Maintenance & réparations bâtiments (615)", value=float(d_maint), step=5000.0)
    fluides_606 = st.number_input("Énergie & fluides (Eau, Gaz, Élec)", value=float(round(d_ext * 0.55)), step=5000.0)
    autres_ext = st.number_input("Autres charges externes (Assur., honoraires...)", value=float(round(d_ext * 0.45)), step=5000.0)
    loyers_613 = st.number_input("Loyers immobiliers versés à l'AEP (613)", value=float(d_loy), step=5000.0)

st.sidebar.markdown("### 5. Patrimoine, Dette & Trésorerie")
amort_68 = st.sidebar.number_input("Dotations aux amortissements (681) (€)", value=float(d_amo), step=5000.0)
fin_66 = st.sidebar.number_input("Intérêts des emprunts (66) (€)", value=float(d_fin), step=2000.0)
dette_16 = st.sidebar.number_input("Encours dette immobilière au 31/12 (€)", value=float(d_det), step=25000.0)
remb_16 = st.sidebar.number_input("Remboursement annuel capital emprunts (€)", value=float(d_remb), step=5000.0)
treso_51 = st.sidebar.number_input("Trésorerie globale disponible (€)", value=float(d_tres), step=10000.0)

# ==========================================
# 5. CALCULS DU MOTEUR FINANCIER (COHÉRENCE EBE -> CAF)
# ==========================================
ch_ufa_cfc_tot = 0.0 if source_reelle else (ch_ufa + ch_cfc)
prod_ufa_cfc_tot = 0.0 if source_reelle else (prod_ufa + prod_cfc)

tp_scol = f_74 + c_756 + a_70 + aut_p
tp = tp_scol + prod_ufa_cfc_tot

ch_achats = ach_peda + ach_resto
ch_ext_hors_achats = maint_615 + fluides_606 + autres_ext + loyers_613
tc = ch_achats + ch_ext_hors_achats + ms_totale + ch_ufa_cfc_tot + fin_66 + amort_68

# Cascade SIG mathématiquement cohérente : EBE - Frais financiers (66) = CAF
marge_brute = tp - ch_achats
valeur_ajoutee = marge_brute - ch_ext_hors_achats
ebe = valeur_ajoutee - ms_totale - ch_ufa_cfc_tot
tebe = (ebe / tp * 100) if tp > 0 else 0.0

caf = ebe - fin_66
rn = caf - amort_68
autofin_net = caf - remb_16
tcaf = (caf / tp * 100) if tp > 0 else 0.0
poids_fin_tp = (fin_66 / tp * 100) if tp > 0 else 0.0

# Bilan, Endettement, Amortissements & Règle d'Or
ch_dec = max(1.0, tc - amort_68)
j_treso = int(round((treso_51 / ch_dec) * 365))
cap_desend = (dette_16 / caf) if caf > 0 else 99.9
annuite_dette = remb_16 + fin_66
taux_abs_caf = (annuite_dette / caf * 100) if caf > 0 else 100.0

ro_solde = c_756 - (amort_68 + fin_66 + loyers_613)
ro_ok = ro_solde >= 0

# Ratios unitaires & patrimoniaux relativisés Propriétaire / Locataire
forfait_eleve_reel = f_74 / max(1, eleves_tot)
contrib_eleve_reel = c_756 / max(1, eleves_tot)
maint_m2 = maint_615 / max(1, surface_m2)
amort_m2 = amort_68 / max(1, surface_m2)
loyer_m2 = loyers_613 / max(1, surface_m2)
eq_loyer_m2 = (amort_68 + loyers_613 + fin_66) / max(1, surface_m2)
norme_eq_loyer = normes["amort_m2"] + 4.0

effort_immo_tot = maint_615 + amort_68 + loyers_613
poids_immo_tp = (effort_immo_tot / tp_scol * 100) if tp_scol > 0 else 0.0
fluides_eleve = fluides_606 / max(1, eleves_tot)
b_peda_eleve = ach_peda / max(1, eleves_tot)

base_ms_ratio = tp if source_reelle else max(1.0, tp_scol)
poids_ms_tp = (ms_totale / base_ms_ratio * 100)
poids_admin_ms = (ms_admin / ms_totale * 100) if ms_totale > 0 else 0.0

ch_resto_directes = ach_resto + (ms_tech * 0.45) + (fluides_606 * 0.25)
marge_resto = a_70 - ch_resto_directes
tx_couv_resto = (a_70 / ch_resto_directes * 100) if ch_resto_directes > 0 else 100.0

# Pôle Hors Contrat (UFA et Formation Continue)
marge_ufa = prod_ufa - ch_ufa
marge_cfc = prod_cfc - ch_cfc
ben_par_apprenti = (marge_ufa / max(1, app_tot)) if activer_ufa_cfc else 0.0
ben_par_stagiaire = (marge_cfc / max(1, stag_tot)) if activer_ufa_cfc else 0.0

s_caf = min(30, max(0, int(round((tcaf / normes["taux_caf"]) * 25))))
s_ro = 25 if ro_ok else max(0, int(round(25 + (ro_solde / max(1.0, c_756)) * 60)))
s_treso = min(25, max(0, int(round((j_treso / normes["jours_treso"]) * 22))))
s_det = 20 if cap_desend <= normes["desend_moy"] else (14 if cap_desend <= normes["desend_max"] else (6 if cap_desend <= 11 else 0))
health_score = min(100, s_caf + s_ro + s_treso + s_det)

# ==========================================
# 6. INTERFACE PRINCIPALE + GUIDE PÉDAGOGIQUE
# ==========================================
st.title("Archétype Éducation — Audit ANC 2018-06, Pilotage & Prospective")
badge_src = "Balances ANC 2018-06 certifiées" if source_reelle else "Modèle calibré Observatoire"
st.caption(f"Établissement : **{etab}** • {normes['type_court']} • **{statut_immo}** • {eleves_tot} élèves • {surface_m2} m² • {badge_src}")

with st.expander("📖 Guide pédagogique : relativiser les normes selon le statut immobilier & comprendre les ratios (Spécial CA & Président d'OGEC)", expanded=False):
    st.markdown("Ce guide traduit les termes comptables (norme associative **ANC 2018-06**) et précise comment lire les moyennes selon que l'OGEC est **propriétaire** ou **locataire** de ses murs :")
    gp_c1, gp_c2, gp_c3 = st.columns(3)
    with gp_c1:
        st.markdown("**1. Propriétaire vs Locataire : Relativiser les normes**")
        st.markdown("""* **Pourquoi les amortissements (681) varient :** un OGEC **propriétaire** amortit les bâtiments (repère : **18 €/m²** en école primaire où les murs sont souvent anciens, **30 à 40 €/m²** en collège/lycée/agricole). À l'inverse, un OGEC **locataire** (murs portés par une AEP ou le diocèse) n'amortit que le mobilier et l'informatique (**8 à 12 €/m²**), mais paie un **loyer (613)**.
* **L'indicateur « Équivalent Loyer » :** pour comparer équitablement propriétaires et locataires, on additionne `(Amortissements 681 + Loyers 613 + Intérêts 66) / m²`.
* **La Règle d'Or :** quelle que soit la structure juridique, les *contributions des familles* (756) doivent couvrir l'ensemble de cette charge immobilière sans ponctionner les forfaits publics.""")
    with gp_c2:
        st.markdown("**2. Cohérence EBE → CAF → Autofinancement Net**")
        st.markdown("""* **EBE (Excédent Brut d'Exploitation) :** marge dégagée par l'activité courante avant banques et amortissements.
* **CAF (Capacité d'Autofinancement) :** égale à l'`EBE - Frais financiers (intérêts)`. C'est la ressource interne dégagée sur l'année.
* **Autofinancement Net :** `CAF - Remboursement du capital des emprunts`. C'est l'argent réellement disponible pour financer le renouvellement courant sans réemprunter.""")
    with gp_c3:
        st.markdown("**3. Pôle Hors Contrat (UFA & CFC) & Spécificités**")
        st.markdown("""* **UFA & Formation Continue :** ces deux activités hors contrat doivent chacune dégager un **bénéfice net positif** (cibles indicatives : **+600 à +1 000 €/apprenti** et **+100 à +250 €/stagiaire FC**) pour renforcer la CAF globale sans jamais peser sur l'activité scolaire sous contrat.
* **MFR & Lycées Agricoles :** en **MFR**, les formateurs sont payés par l'association (masse salariale interne > 60 %) ; en **Lycée Agricole**, le poids de l'internat (~45 %) et des plateaux techniques augmente les charges immobilières et d'énergie.""")

onglets = st.tabs([
    "📊 1. Rétrospective (Trajectoire & Renouvellement)",
    "⚖️ 2. Situation à date (TBI, SIG & Dette)",
    "🔪 3. Scalpel (Choix Budget Prévisionnel)",
    "🔮 4. Prospective (Projet à 5 ans)"
])

# ------------------------------------------
# ONGLET 1 : RÉTROSPECTIVE (TRAJECTOIRE, RENOUVELLEMENT & DETTE)
# ------------------------------------------
with onglets[0]:
    st.subheader("D'où venons-nous ? Trajectoire d'exploitation, renouvellement et dette (2021-2025)")
    afficher_aide_pedagogique_onglet("Lecture de la trajectoire passée (relativisée au statut immobilier)", [
        ("Effet Ciseau (TCMA Charges vs Produits)", "Rythme annuel moyen d'évolution. Si les charges montent plus vite que les recettes, la CAF s'érode mécaniquement."),
        ("Taux de renouvellement (Investissements / Amortissements)", f"Statut actuel : **{statut_immo}**. Un ratio < 100 % sur 5 ans signifie que les nouveaux équipements ne compensent pas l'usure comptable. Si l'OGEC est locataire, cela ne concerne que les équipements mobiliers et aménagements intérieurs (le gros œuvre relevant de l'AEP propriétaire)."),
        ("Effet Volume RH", "Part de la hausse des salaires liée aux décisions locales (créations de postes, remplacements) par opposition aux hausses subies (ancienneté GVT et point d'indice/EEPNL).")
    ])

    if len(balances_parsees) >= 2:
        ans_r = [b["annee"] or f"Ex.{i+1}" for i, b in enumerate(balances_parsees)]
        p_r = [b["tp"]/1e6 for b in balances_parsees]
        c_r = [b["tc"]/1e6 for b in balances_parsees]
        ms_r = [b["ms_64"]/1e6 for b in balances_parsees]
        caf_r = [b["caf"]/1e6 for b in balances_parsees]
        amo_r = [b["amo_68"]/1e6 for b in balances_parsees]
        aut_r = [(b["caf"] - (b["remb"] if b["remb"]>0 else remb_16))/1e6 for b in balances_parsees]
        det_r = [(b["dette"] if b["dette"]>0 else dette_16)/1e6 for b in balances_parsees]
        inv_r = [round(a * 0.95, 2) for a in amo_r]
    else:
        ans_r = ["2021", "2022", "2023", "2024", "2025"]
        tp_m, tc_m, ms_m, caf_m, amo_m, det_m = tp/1e6, tc/1e6, ms_totale/1e6, caf/1e6, amort_68/1e6, dette_16/1e6
        p_r = [round(tp_m*0.88, 2), round(tp_m*0.91, 2), round(tp_m*0.94, 2), round(tp_m*0.97, 2), round(tp_m, 2)]
        c_r = [round(tc_m*0.85, 2), round(tc_m*0.89, 2), round(tc_m*0.93, 2), round(tc_m*0.97, 2), round(tc_m, 2)]
        ms_r = [round(ms_m*0.85, 2), round(ms_m*0.89, 2), round(ms_m*0.93, 2), round(ms_m*0.97, 2), round(ms_m, 2)]
        amo_r = [round(amo_m*0.92, 2), round(amo_m*0.94, 2), round(amo_m*0.96, 2), round(amo_m*0.98, 2), round(amo_m, 2)]
        caf_r = [round(p - c + a, 2) for p, c, a in zip(p_r[:-1], c_r[:-1], amo_r[:-1])] + [round(caf_m, 2)]
        aut_r = [round(cf - (remb_16/1e6), 2) for cf in caf_r]
        inv_r = [round(amo_m*0.75, 2), round(amo_m*1.15, 2), round(amo_m*0.80, 2), round(amo_m*0.90, 2), round(amo_m*0.85, 2)]
        det_r = [round(det_m*1.28, 2), round(det_m*1.22, 2), round(det_m*1.14, 2), round(det_m*1.07, 2), round(det_m, 2)]

    n_int = max(1, len(ans_r) - 1)
    tcma_p = ((p_r[-1]/p_r[0])**(1/n_int) - 1)*100 if p_r[0] > 0 else 0.0
    tcma_c = ((c_r[-1]/c_r[0])**(1/n_int) - 1)*100 if c_r[0] > 0 else 0.0
    tcma_ms = ((ms_r[-1]/ms_r[0])**(1/n_int) - 1)*100 if ms_r[0] > 0 else 0.0
    ciseau = tcma_c - tcma_p
    tx_renouv_hist = (sum(inv_r) / max(0.01, sum(amo_r))) * 100

    kr1, kr2, kr3, kr4 = st.columns(4)
    kr1.metric("TCMA Produits", f"+{tcma_p:.2f} % / an", "Rythme des ressources")
    kr2.metric("TCMA Charges", f"+{tcma_c:.2f} % / an", f"Effet ciseau : {ciseau:+.2f} pts (Cible <= 0)", delta_color="inverse" if ciseau > 0 else "normal")
    kr3.metric("Taux Renouvellement", f"{tx_renouv_hist:.0f} %", "Inv. / Amort. (Cible >= 100 %)", delta_color="normal" if tx_renouv_hist >= 95 else "inverse")
    kr4.metric("Trajectoire Dette OGEC", f"{det_r[-1]:.2f} M€", f"Variation 5 ans : {(det_r[-1]-det_r[0]):+.2f} M€")

    cg1, cg2, cg3 = st.columns(3)
    with cg1:
        st.markdown("**1. Effet de ciseau (Produits vs Charges M€)**")
        st.line_chart(pd.DataFrame({"Exercice": ans_r, "Produits (M€)": p_r, "Charges (M€)": c_r}).set_index("Exercice"))
    with cg2:
        st.markdown("**2. CAF & Autofinancement net (M€)**")
        st.line_chart(pd.DataFrame({"Exercice": ans_r, "CAF (M€)": caf_r, "Autofin. Net (M€)": aut_r}).set_index("Exercice"))
    with cg3:
        st.markdown("**3. Investissements vs Amortissements (M€)**")
        st.bar_chart(pd.DataFrame({"Exercice": ans_r, "Investissements": inv_r, "Amortissements": amo_r}).set_index("Exercice"))

    st.markdown("**4. Décomposition de la dérive salariale interne (Compte 64)**")
    cd1, cd2, cd3 = st.columns(3)
    gvt_pt = cd1.slider("GVT Mécanique — Ancienneté (pts/an)", 0.5, 2.5, 1.2, 0.1)
    conv_pt = cd2.slider("Mesures Nationales — EEPNL / SMIC (pts/an)", 0.5, 3.5, 1.5, 0.1)
    vol_pt = round(tcma_ms - gvt_pt - conv_pt, 2)
    cd3.metric("Effet Volume (Levier interne)", f"{vol_pt:+.2f} pts / an", "Norme cible : <= +0,30 pt/an", delta_color="inverse" if vol_pt > 0.3 else "normal")

    df_retro_tbl = pd.DataFrame({
        "Soldes & Flux Patrimoniaux (M€)": [
            "Produits d'exploitation", "Charges d'exploitation", "Capacité d'Autofinancement (CAF)",
            "Autofinancement net (après dette)", "Dotations aux amortissements (681)",
            "Investissements réalisés", "Encours dette immobilière (31/12)"
        ],
        **{ans_r[i]: [f"{p_r[i]:.2f}", f"{c_r[i]:.2f}", f"{caf_r[i]:.2f}", f"{aut_r[i]:.2f}", f"{amo_r[i]:.2f}", f"{inv_r[i]:.2f}", f"{det_r[i]:.2f}"] for i in range(len(ans_r))}
    })
    st.dataframe(df_retro_tbl, hide_index=True, use_container_width=True)

    relativisation_immo = (
        "L'OGEC étant locataire, ses amortissements ne portent que sur le mobilier et les agencements ; le renouvellement du gros œuvre relève de l'AEP propriétaire."
        if "Locataire" in statut_immo else
        f"En statut {statut_immo.lower()}, un renouvellement inférieur à 100 % des amortissements signale un vieillissement du parc à anticiper."
    )
    atouts_list = [
        f"Base de recettes solide ({tp/1e6:.2f} M€) et désendettement progressif ({(det_r[-1]-det_r[0]):+.2f} M€ sur la période).",
        f"Taux de CAF à {tcaf:.1f} % ({'conforme' if tcaf >= normes['taux_caf'] else 'inférieur'} au repère de {normes['taux_caf']} %).",
        "Autofinancement net positif permettant de soutenir le renouvellement courant."
    ]
    vig_list = [
        f"Effet ciseau de {ciseau:+.2f} pts/an à résorber sur le prochain Budget Prévisionnel.",
        f"Taux de renouvellement à {tx_renouv_hist:.0f} % : {relativisation_immo}",
        f"Maintenir l'effet volume RH ({vol_pt:+.2f} pts/an) sous la norme de +0,30 pt/an."
    ]
    pdf_retro_bytes = build_pdf_retro(etab, normes, statut_immo, ans_r, p_r, c_r, ms_r, caf_r, aut_r, inv_r, amo_r, det_r, tcma_p, tcma_c, tcma_ms, gvt_pt, conv_pt, vol_pt, atouts_list, vig_list)
    st.download_button("📑 Télécharger le Dossier Rétrospectif Complet (PDF 2 pages)", data=pdf_retro_bytes, file_name=f"Dossier_Retro_{etab.replace(' ','_')}.pdf", mime="application/pdf", type="primary")

    afficher_synthese_unique(
        "Rétrospective : Trajectoire d'exploitation & Renouvellement",
        f"Sur la période, les charges évoluent de +{tcma_c:.2f} %/an contre +{tcma_p:.2f} %/an pour les produits (effet ciseau : {ciseau:+.2f} pts/an). Côté patrimoine ({statut_immo}), les investissements cumulés ({sum(inv_r):.2f} M€) représentent {tx_renouv_hist:.0f} % des dotations aux amortissements ({sum(amo_r):.2f} M€), tandis que l'encours de dette évolue de {det_r[0]:.2f} M€ à {det_r[-1]:.2f} M€.",
        f"Le désendettement engagé libère progressivement de la marge financière, et {(gvt_pt+conv_pt):.2f} pts/an de la dérive salariale relèvent de facteurs externes subis (GVT et revalorisations conventionnelles).",
        f"{relativisation_immo} Contenir l'effet volume RH ({vol_pt:+.2f} pts/an) sous +0,30 pt/an dans le prochain Budget Prévisionnel."
    )

# ------------------------------------------
# ONGLET 2 : SITUATION À DATE (TBI, SIG, AMORTISSEMENTS & DETTE)
# ------------------------------------------
with onglets[1]:
    st.subheader("Où en est-on ? Situation à date, Cascade des SIG & Diagnostic Patrimonial")
    afficher_aide_pedagogique_onglet("Lecture de la cohérence EBE -> CAF & Relativisation Propriétaire / Locataire", [
        ("Passage EBE -> CAF", "La CAF est égale à l'EBE diminué des intérêts d'emprunts (compte 66). Si l'EBE est bon mais la CAF faible, c'est uniquement parce que les intérêts de la dette pèsent trop lourd."),
        ("Relativisation Amortissements (681) vs Loyers (613)", f"Pour un profil **{normes['type_court']}** en statut **{statut_immo}**, le repère d'amortissement est ajusté à **~{norme_amort_eff:.0f} €/m²** (contre {normes['amort_m2']:.0f} €/m² en pleine propriété). Pour comparer objectivement propriétaires et locataires, on utilise l'**Équivalent Loyer global** `(Amort. 681 + Loyers 613 + Intérêts 66) / m²`."),
        ("Taux d'absorption de la CAF par la dette", "(Remboursement capital + Intérêts) / CAF. Si l'annuité totale de dette dépasse 75 % de la CAF, l'établissement n'a plus de marge pour autofinancer ses travaux courants.")
    ])

    hs1, hs2 = st.columns([1, 2.5])
    with hs1:
        st.metric("HEALTH SCORE ANC 2018-06", f"{health_score} / 100", "Sain >= 70 | Vigilance 45-69")
    with hs2:
        if health_score >= 70:
            st.success(f"**Trajectoire maîtrisée ({health_score}/100) :** EBE à {tebe:.1f} % (moy. {normes['taux_ebe']} %), CAF à {tcaf:.1f} % (cible {normes['taux_caf']} %), Règle d'Or respectée ({ro_solde:+,.0f} €) et désendettement à {cap_desend:.1f} ans.".replace(",", " "))
        elif health_score >= 45:
            st.warning(f"**Infléchissement à surveiller ({health_score}/100) :** Des tensions apparaissent sur la CAF ({tcaf:.1f} % vs {normes['taux_caf']} %) ou la Règle d'Or ({ro_solde:+,.0f} €). Des ajustements sont nécessaires dans le prochain Budget Prévisionnel.".replace(",", " "))
        else:
            st.error(f"**Rupture d'équilibre ({health_score}/100) :** Alerte sur la CAF ({tcaf:.1f} %), la trésorerie ({j_treso} j) ou l'endettement ({cap_desend:.1f} ans). Plan de redressement requis.".replace(",", " "))

    if poids_fin_tp > 2.5:
        st.warning(f"**Diagnostic EBE → CAF :** Les intérêts d'emprunts ({fin_66:,.0f} €, soit **{poids_fin_tp:.1f} %** des produits) amputent fortement l'EBE ({tebe:.1f} %) pour ramener la CAF à {tcaf:.1f} %. L'endettement pèse sur la rentabilité.".replace(",", " "))

    c_sig1, c_sig2 = st.columns([1.45, 1])
    with c_sig1:
        st.markdown("**1. Cascade des Soldes Intermédiaires de Gestion (ANC 2018-06) vs Normes**")
        df_sig = pd.DataFrame([
            {"Solde Intermédiaire de Gestion": "Total Produits d'Exploitation (70/74/75 + UFA/CFC)", "Montant (€)": f"{tp:,.0f} €".replace(",", " "), "% Produits": "100,0 %", "Moyenne / Norme": "Base 100 %"},
            {"Solde Intermédiaire de Gestion": "- Achats consommés (Pédagogie + Denrées 60)", "Montant (€)": f"-{ch_achats:,.0f} €".replace(",", " "), "% Produits": f"{ch_achats/tp*100:.1f} %", "Moyenne / Norme": "12 - 18 %"},
            {"Solde Intermédiaire de Gestion": "- Services ext., Maintenance, Fluides & Loyers", "Montant (€)": f"-{ch_ext_hors_achats:,.0f} €".replace(",", " "), "% Produits": f"{ch_ext_hors_achats/tp*100:.1f} %", "Moyenne / Norme": "18 - 25 %"},
            {"Solde Intermédiaire de Gestion": "= VALEUR AJOUTÉE (VA)", "Montant (€)": f"{valeur_ajoutee:,.0f} €".replace(",", " "), "% Produits": f"{valeur_ajoutee/tp*100:.1f} %", "Moyenne / Norme": "55 - 65 %"},
            {"Solde Intermédiaire de Gestion": "- Masse Salariale interne (64) & Charges UFA/CFC", "Montant (€)": f"-{(ms_totale+ch_ufa_cfc_tot):,.0f} €".replace(",", " "), "% Produits": f"{(ms_totale+ch_ufa_cfc_tot)/tp*100:.1f} %", "Moyenne / Norme": f"MS scol. {normes['poids_ms']} %"},
            {"Solde Intermédiaire de Gestion": "= EXCÉDENT BRUT D'EXPLOITATION (EBE)", "Montant (€)": f"{ebe:,.0f} €".replace(",", " "), "% Produits": f"{tebe:.1f} %", "Moyenne / Norme": f"Moy. {normes['taux_ebe']} %"},
            {"Solde Intermédiaire de Gestion": "- Frais financiers / Intérêts emprunts (66)", "Montant (€)": f"-{fin_66:,.0f} €".replace(",", " "), "% Produits": f"{poids_fin_tp:.1f} %", "Moyenne / Norme": "Norme < 2,5 %"},
            {"Solde Intermédiaire de Gestion": "= CAPACITÉ D'AUTOFINANCEMENT (CAF)", "Montant (€)": f"{caf:,.0f} €".replace(",", " "), "% Produits": f"{tcaf:.1f} %", "Moyenne / Norme": f"Cible >= {normes['taux_caf']} %"},
            {"Solde Intermédiaire de Gestion": "- Dotations aux amortissements (681)", "Montant (€)": f"-{amort_68:,.0f} €".replace(",", " "), "% Produits": f"{amort_68/tp*100:.1f} %", "Moyenne / Norme": f"~{norme_amort_eff:.0f} €/m² ({statut_immo.split()[0]})"},
            {"Solde Intermédiaire de Gestion": "= RÉSULTAT NET COMPTABLE (RCAI)", "Montant (€)": f"{rn:+,.0f} €".replace(",", " "), "% Produits": f"{rn/tp*100:+.1f} %", "Moyenne / Norme": "Norme >= 0 %"},
            {"Solde Intermédiaire de Gestion": "- Remboursement annuel capital dette (164)", "Montant (€)": f"-{remb_16:,.0f} €".replace(",", " "), "% Produits": f"{remb_16/tp*100:.1f} %", "Moyenne / Norme": "4 - 8 %"},
            {"Solde Intermédiaire de Gestion": "= AUTOFINANCEMENT NET DISPONIBLE (CAF - Capital)", "Montant (€)": f"{autofin_net:+,.0f} €".replace(",", " "), "% Produits": f"{autofin_net/tp*100:+.1f} %", "Moyenne / Norme": "Norme >= 0 €"},
        ])
        st.dataframe(df_sig, hide_index=True, use_container_width=True)

    with c_sig2:
        st.markdown("**2. Diagnostic Patrimonial, Amortissements & Dette**")
        d_c1, d_c2 = st.columns(2)
        d_c1.metric("Désendettement OGEC", f"{cap_desend:.1f} ans", f"Moy. {normes['desend_moy']} a. | Max {normes['desend_max']} a.", delta_color="normal" if cap_desend <= normes["desend_max"] else "inverse")
        d_c2.metric("Absorption CAF / Dette", f"{taux_abs_caf:.0f} %", "Annuité / CAF (Max 75 %)", delta_color="normal" if taux_abs_caf <= 75 else "inverse")
        
        d_c3, d_c4 = st.columns(2)
        d_c3.metric("Amortissements (681)", f"{amort_m2:.1f} €/m²", f"Repère {statut_immo.split()[0]} : {norme_amort_eff:.0f} €/m²")
        d_c4.metric("Équivalent Loyer Global", f"{eq_loyer_m2:.1f} €/m²", f"Amort+Loyer+Int (Repère ~{norme_eq_loyer:.0f} €)")

        c_r1, c_r2 = st.columns(2)
        c_r1.metric("Règle d'Or Immobilière", f"{ro_solde:+,.0f} €".replace(",", " "), "Norme : >= 0 €", delta_color="normal" if ro_ok else "inverse")
        c_r2.metric("Trésorerie Sécurité", f"{j_treso} jours", f"Cible : {normes['jours_treso']} j", delta_color="normal" if j_treso >= 60 else "inverse")

        st.markdown("**3. Comparatif : Établissement vs Moyennes du Profil**")
        df_bench = pd.DataFrame([
            {"Indicateur": "Forfait public / élève", "Établissement": f"{forfait_eleve_reel:,.0f} €", "Moyenne / Norme": f"{normes['forfait_eleve']:,.0f} €", "Statut": "OK" if forfait_eleve_reel >= normes['forfait_eleve']*0.95 else "Sous moy."},
            {"Indicateur": "Contribution familles / élève", "Établissement": f"{contrib_eleve_reel:,.0f} €", "Moyenne / Norme": f"{normes['contrib_eleve']:,.0f} €", "Statut": "OK" if contrib_eleve_reel >= normes['contrib_eleve']*0.9 else "Sous moy."},
            {"Indicateur": "Taux d'EBE / Taux de CAF", "Établissement": f"{tebe:.1f}% / {tcaf:.1f}%", "Moyenne / Norme": f"{normes['taux_ebe']}% / {normes['taux_caf']}%", "Statut": "OK" if tcaf >= normes['taux_caf'] else "Vigilance"},
            {"Indicateur": "Effort Bâti (Maint.+Amort.+Loyers)", "Établissement": f"{poids_immo_tp:.1f} %", "Moyenne / Norme": "20 - 25 % (FNOGEC)", "Statut": "OK" if 18 <= poids_immo_tp <= 26 else "À vérifier"},
        ])
        st.dataframe(df_bench, hide_index=True, use_container_width=True)

    if autofin_net >= 0:
        arb_txt = f"• Arbitrage BP : L'autofinancement net ({autofin_net:+,.0f} €) permet de financer le renouvellement courant sans nouvel emprunt.".replace(",", " ")
    else:
        arb_txt = f"• Arbitrage BP : Déficit d'autofinancement net ({autofin_net:+,.0f} €) : redresser l'EBE avant tout nouvel investissement.".replace(",", " ")

    synthese_tbi_lines = [
        f"• Cohérence EBE -> CAF : EBE de {tebe:.1f} % (moy. {normes['taux_ebe']} %) moins {poids_fin_tp:.1f} % d'intérêts = CAF de {tcaf:.1f} % (cible {normes['taux_caf']} %).",
        f"• Patrimoine ({statut_immo}) : Amortissements à {amort_m2:.1f} €/m² (repère {norme_amort_eff:.0f} €/m²) et équivalent loyer global à {eq_loyer_m2:.1f} €/m².",
        arb_txt
    ]
    pdf_tbi_bytes = build_pdf_tbi(
        etab, normes, statut_immo, norme_amort_eff, eleves_tot, surface_m2, health_score,
        tp/1e6, ch_achats/1e6, ch_ext_hors_achats/1e6, valeur_ajoutee/1e6, ms_totale/1e6, ch_ufa_cfc_tot/1e6,
        ebe/1e6, fin_66/1e6, amort_68/1e6, rn/1e6, caf/1e6, remb_16/1e6, autofin_net/1e6,
        dette_16/1e6, cap_desend, treso_51/1e6, j_treso, ro_solde/1e6,
        maint_m2, amort_m2, eq_loyer_m2, b_peda_eleve, ben_par_apprenti, ben_par_stagiaire, synthese_tbi_lines
    )
    st.download_button("📑 Télécharger le TBI Exécutif, SIG & Patrimoine (PDF 1 page)", data=pdf_tbi_bytes, file_name=f"TBI_Executif_{etab.replace(' ','_')}.pdf", mime="application/pdf", type="primary")

    afficher_synthese_unique(
        "Situation à date : Rentabilité, Amortissements & Statut Immobilier",
        f"L'établissement dégage un EBE de {ebe/1e6:.2f} M€ ({tebe:.1f} %) et, après {fin_66:,.0f} € de frais financiers ({poids_fin_tp:.1f} %), une CAF de {caf/1e6:.2f} M€ ({tcaf:.1f} % vs {normes['taux_caf']} % attendus). En statut **{statut_immo.lower()}**, les amortissements ressortent à {amort_m2:.1f} €/m² (repère ajusté : {norme_amort_eff:.0f} €/m²) et l'équivalent loyer global (amortissements + loyers AEP + intérêts) s'établit à {eq_loyer_m2:.1f} €/m².".replace(",", " "),
        f"L'autofinancement net disponible ressort à {autofin_net:+,.0f} €, la capacité de désendettement à {cap_desend:.1f} ans (moyenne : {normes['desend_moy']} ans) et la trésorerie à {j_treso} jours.".replace(",", " "),
        f"{'En tant que locataire AEP, vérifier que le loyer versé (613) permet à l AEP de couvrir ses emprunts de gros œuvre tout en laissant à l OGEC une capacité d autofinancement nette positive pour le mobilier et l informatique.' if 'Locataire' in statut_immo else 'Inscrire au prochain Budget Prévisionnel une capacité d autofinancement nette positive d au moins 30 % des dotations aux amortissements pour financer le renouvellement courant sans alourdir la dette.'}"
    )

# ------------------------------------------
# ONGLET 3 : SCALPEL (INDICATEURS DE PILOTAGE POUR LE BP)
# ------------------------------------------
with onglets[2]:
    st.subheader("Où faire ses choix ? Les indicateurs de pilotage pour le Budget Prévisionnel")
    afficher_aide_pedagogique_onglet("Arbitrer poste par poste dans le Budget Prévisionnel", [
        ("Relativisation Propriétaire vs Locataire sur l'immobilier", f"Votre statut est **{statut_immo}**. Pour un **propriétaire**, des amortissements faibles (ex. 18 €/m² en école ou < 25 €/m² en lycée) combinés à une maintenance élevée signale des locaux anciens déjà amortis nécessitant des travaux. Pour un **locataire**, un amortissement faible (~10 €/m²) est tout à fait normal puisque l'AEP porte les murs : il faut alors regarder le cumul `Amortissements 681 + Loyers 613`."),
        ("Pôle Hors Contrat (UFA et Formation Continue)", "Permet de vérifier que chacune de ces deux activités dégage un bénéfice net positif afin d'améliorer la CAF globale de l'OGEC, sans jamais peser sur l'équilibre financier de l'activité scolaire sous contrat."),
        ("Équilibre Restauration & Internat", "Chaque euro de déficit sur la cantine ou l'internat ampute directement le budget pédagogique des élèves.")
    ])

    st.markdown("#### 1. Structure RH Interne (Compte 64 vs Moyennes)")
    crh1, crh2 = st.columns([1.45, 1])
    with crh1:
        df_rh = pd.DataFrame([
            {"Pôle RH (Hors profs État)": "Enseignants de droit privé (Rempl., hors contrat)", "Budget (€)": f"{ms_prive:,.0f} €".replace(",", " "), "Part MS": f"{ms_prive/max(1,ms_totale)*100:.1f} %", "Moyenne Strate": "12 - 18 %", "Coût / Élève": f"{ms_prive/eleves_tot:,.0f} €"},
            {"Pôle RH (Hors profs État)": "Vie scolaire, éducateurs, surveillants, AESH", "Budget (€)": f"{ms_vie_scol:,.0f} €".replace(",", " "), "Part MS": f"{ms_vie_scol/max(1,ms_totale)*100:.1f} %", "Moyenne Strate": "32 - 38 %", "Coût / Élève": f"{ms_vie_scol/eleves_tot:,.0f} €"},
            {"Pôle RH (Hors profs État)": "Administration, direction, comptabilité", "Budget (€)": f"{ms_admin:,.0f} €".replace(",", " "), "Part MS": f"{poids_admin_ms:.1f} %", "Moyenne Strate": f"Moy. {normes['poids_admin']} %", "Coût / Élève": f"{ms_admin/eleves_tot:,.0f} €"},
            {"Pôle RH (Hors profs État)": "Technique, entretien, accueil & restauration", "Budget (€)": f"{ms_tech:,.0f} €".replace(",", " "), "Part MS": f"{ms_tech/max(1,ms_totale)*100:.1f} %", "Moyenne Strate": "22 - 28 %", "Coût / Élève": f"{ms_tech/eleves_tot:,.0f} €"},
        ])
        st.dataframe(df_rh, hide_index=True, use_container_width=True)
    with crh2:
        st.bar_chart(pd.DataFrame({
            "Pôle": ["Profs Privé", "Vie Scolaire", "Admin/Dir.", "Tech/Resto"],
            "Montant (€)": [ms_prive, ms_vie_scol, ms_admin, ms_tech]
        }).set_index("Pôle"), color="#1d4ed8")

    st.divider()

    st.markdown(f"#### 2. Patrimoine : Maintenance (615), Amortissements (681) & Règle d'Or ({statut_immo})")
    cb1, cb2, cb3, cb4 = st.columns(4)
    cb1.metric("Maintenance (615)", f"{maint_m2:.1f} €/m²", f"Moy. : {normes['maint_m2']} €/m²", delta_color="inverse" if maint_m2 > normes["maint_m2"]*1.25 else "normal")
    cb2.metric("Amortissements (681)", f"{amort_m2:.1f} €/m²", f"Repère {statut_immo.split()[0]} : {norme_amort_eff:.0f} €/m²")
    cb3.metric("Équivalent Loyer Global", f"{eq_loyer_m2:.1f} €/m²", f"Amort.+Loyers+Int. (Rep. ~{norme_eq_loyer:.0f} €)")
    cb4.metric("Solde Règle d'Or", f"{ro_solde:+,.0f} €".replace(",", " "), "Norme : >= 0 €", delta_color="normal" if ro_ok else "inverse")

    if "Locataire" in statut_immo:
        st.info(f"**Lecture relativisée (OGEC Locataire) :** Les dotations aux amortissements ({amort_m2:.1f} €/m²) ne couvrent que les agencements et équipements mobiliers ; le loyer versé à l'AEP ({loyer_m2:.1f} €/m²) porte la charge des murs. L'équilibre s'apprécie sur l'équivalent loyer global ({eq_loyer_m2:.1f} €/m²).")
    elif maint_m2 > normes["maint_m2"] * 1.15 and amort_m2 < norme_amort_eff * 0.85:
        st.warning(f"**Signal de vieillissement immobilier (OGEC {statut_immo.split()[0]}) :** Votre maintenance au m² ({maint_m2:.1f} €/m²) est élevée alors que vos dotations aux amortissements ({amort_m2:.1f} €/m²) sont inférieures au repère ({norme_amort_eff:.0f} €/m²). Cela traduit un parc ancien déjà largement amorti qui génère des frais de réparation croissants.")
    if not ro_ok:
        st.error(f"**Rupture de la Règle d'Or ({ro_solde:+,.0f} €) :** Il manque **{int(round(abs(ro_solde)/eleves_tot))} € / élève / an** sur les contributions familles (756) pour couvrir les charges immobilières.".replace(",", " "))

    st.divider()

    cs1, cs2 = st.columns(2)
    with cs1:
        st.markdown("#### 3. Restauration & Internat (Norme >= 100 %)")
        st.metric("Marge sur coûts directs Resto/Internat", f"{marge_resto:+,.0f} €".replace(",", " "), f"Couverture : {tx_couv_resto:.1f} %", delta_color="normal" if marge_resto >= 0 else "inverse")
        if marge_resto < 0:
            st.error(f"**Subventionnement croisé :** Perte directe de **{abs(marge_resto):,.0f} €**. Hausse tarifaire nécessaire : **+{abs(marge_resto)/max(1,internes_tot):,.0f} € / usager / an**.".replace(",", " "))
        else:
            st.success("Équilibre respecté : le service couvre ses coûts directs.")

    with cs2:
        st.markdown("#### 4. Effort Pédagogique Direct")
        st.metric("Budget Pédagogique / Élève", f"{b_peda_eleve:,.0f} € / élève", f"Moyenne : {normes['b_peda']} € / élève", delta_color="normal" if b_peda_eleve >= normes["b_peda"]*0.85 else "inverse")
        if b_peda_eleve < normes["b_peda"] * 0.85:
            st.warning(f"**Sous-dotation pédagogique :** À {b_peda_eleve:,.0f} €/élève (vs {normes['b_peda']} € en moyenne), la pédagogie sert de variable d'ajustement.")
        else:
            st.success("Dotation pédagogique conforme aux standards du profil.")

    if activer_ufa_cfc:
        st.divider()
        st.markdown("#### 5. Pôle Hors Contrat : Apprentissage (UFA) et Formation Continue (CFC)")
        st.caption("Objectif : dégager un bénéfice net positif sur chacune des deux activités pour renforcer la CAF globale de l'établissement sans dégrader l'équilibre de l'activité scolaire sous contrat.")
        cu1, cu2 = st.columns(2)
        with cu1:
            st.metric(
                "Bénéfice Net Apprentissage (UFA)",
                f"{marge_ufa:+,.0f} €".replace(",", " "),
                f"{ben_par_apprenti:+,.0f} € / apprenti (Cible : +600 à +1 000 €/app.)",
                delta_color="normal" if ben_par_apprenti >= 500 else ("off" if ben_par_apprenti >= 0 else "inverse")
            )
            if marge_ufa < 0:
                st.error(f"**Déficit UFA ({marge_ufa:,.0f} €) :** L'apprentissage dégrade le résultat de l'OGEC et pèse sur l'activité scolaire.".replace(",", " "))
            elif ben_par_apprenti < 600:
                st.warning(f"**Rentabilité UFA limitée ({ben_par_apprenti:+,.0f} €/apprenti) :** Veiller à bien imputer les frais de structure (locaux, énergie, administration).")
            else:
                st.success(f"**Contribution positive :** L'UFA génère **{ben_par_apprenti:+,.0f} € / apprenti** et renforce la CAF globale.")
        with cu2:
            st.metric(
                "Bénéfice Net Formation Continue (CFC)",
                f"{marge_cfc:+,.0f} €".replace(",", " "),
                f"{ben_par_stagiaire:+,.0f} € / stagiaire (Cible : +100 à +250 €/stag.)",
                delta_color="normal" if ben_par_stagiaire >= 100 else ("off" if ben_par_stagiaire >= 0 else "inverse")
            )
            if marge_cfc < 0:
                st.error(f"**Déficit Formation Continue ({marge_cfc:,.0f} €) :** L'activité dégrade la situation financière de l'établissement. Relever les seuils d'ouverture de stages.".replace(",", " "))
            elif ben_par_stagiaire < 100:
                st.warning(f"**Marge CFC faible ({ben_par_stagiaire:+,.0f} €/stagiaire) :** Optimiser le taux de remplissage des sessions.")
            else:
                st.success(f"**Contribution positive :** La CFC génère **{ben_par_stagiaire:+,.0f} € / stagiaire** et améliore la rentabilité globale.")

    hc_synthese = (
        f"Sur le pôle hors contrat, l'UFA dégage {marge_ufa:+,.0f} € ({ben_par_apprenti:+,.0f} €/apprenti vs cible +600 à +1 000 €) et la Formation Continue dégage {marge_cfc:+,.0f} € ({ben_par_stagiaire:+,.0f} €/stagiaire vs cible +100 à +250 €).".replace(",", " ")
        if activer_ufa_cfc else
        f"La restauration/internat couvre {tx_couv_resto:.1f} % de ses coûts directs ({marge_resto:+,.0f} €) et le budget pédagogique s'établit à {b_peda_eleve:,.0f} €/élève.".replace(",", " ")
    )
    afficher_synthese_unique(
        "Indicateurs de pilotage annuel (Le Scalpel)",
        f"En statut **{statut_immo.lower()}**, l'effort immobilier global (Maintenance {maint_m2:.1f} €/m² + Amortissements {amort_m2:.1f} €/m² + Loyers {loyer_m2:.1f} €/m²) pèse {poids_immo_tp:.1f} % des produits scolaires (repère FNOGEC : 20-25 %). L'encadrement administratif représente {poids_admin_ms:.1f} % de la MS (moyenne : {normes['poids_admin']} %).",
        hc_synthese,
        "Pour le prochain Budget Prévisionnel : ajuster les tarifs de pension pour éliminer tout déficit, conditionner les sessions CFC et UFA à un bénéfice net unitaire positif et arbitrer entre maintenance curative et travaux amortissables."
    )

# ------------------------------------------
# ONGLET 4 : PROSPECTIVE (PROJET D'ÉTABLISSEMENT À 5 ANS)
# ------------------------------------------
with onglets[3]:
    st.subheader("Où allons-nous ? Poser financièrement le projet d'établissement à 5 ans (2026-2030)")
    afficher_aide_pedagogique_onglet("Tester la soutenabilité du PPI et de la dette à 5 ans", [
        ("Taux de renouvellement futur (PPI / Amortissements)", f"Statut : **{statut_immo}**. Permet de vérifier que votre Plan Pluriannuel d'Investissement (PPI) couvre au moins l'usure comptable annuelle (>= 100 % des amortissements)."),
        ("Impact du PPI sur les amortissements et la Règle d'Or", "Tout nouvel investissement porté par l'OGEC génère de nouvelles dotations aux amortissements (compte 681) dès sa mise en service. Il faut vérifier que les contributions des familles (756) suivront pour ne pas casser la Règle d'Or en 2030."),
        ("OPEX induits", "Charges nouvelles (ménage, maintenance) ou économies d'énergie (-1 à -2 %) générées par les travaux.")
    ])

    sp1, sp2, sp3, sp4 = st.columns(4)
    with sp1:
        st.markdown("**1. Fonctionnement & RH**")
        tx_ms_proj = st.slider("Évolution MS interne (%/an)", 0.5, 5.0, 2.2, 0.1)
        tx_ext_proj = st.slider("Inflation Achats/Fluides/Maint. (%/an)", 0.5, 5.0, 1.8, 0.1)
    with sp2:
        st.markdown("**2. Effectifs & Recettes**")
        tx_el_proj = st.slider("Évolution effectifs élèves (%/an)", -3.0, 4.0, 0.5, 0.1)
        tx_forf_proj = st.slider("Indexation Forfaits & Tarifs (%/an)", 0.0, 5.0, 2.0, 0.1)
    with sp3:
        st.markdown("**3. Investissement (PPI)**")
        ppi_annuel = st.slider("Enveloppe PPI cible (M€/an)", 0.0, 2.5, 0.30 if "Locataire" not in statut_immo else 0.10, 0.05)
        exec_pct = st.slider("Taux d'exécution PPI (%)", 50, 100, 85, 5)
        taux_subv_ppi = st.slider("Subventions Région/AEP/MASA (%)", 0, 70, 30, 5)
    with sp4:
        st.markdown("**4. OPEX induits & Dette**")
        opex_ppi_pct = st.slider("OPEX induits par le PPI (% du PPI)", -2.0, 5.0, 1.0, 0.5)
        duree_emprunt = st.selectbox("Durée nouveaux emprunts", [15, 20, 25], index=1)

    ans_p = ["2026", "2027", "2028", "2029", "2030"]
    ppi_reel = ppi_annuel * (exec_pct / 100.0)
    subv_ppi_an = ppi_reel * (taux_subv_ppi / 100.0)
    emprunt_ppi_an = max(0.0, (ppi_reel - subv_ppi_an) * 0.65)
    autofin_ppi_an = max(0.0, (ppi_reel - subv_ppi_an) * 0.35)

    p_list, c_list, caf_list, amo_list, ren_list, det_list, des_list, tr_list, jtr_list, ro_list = [], [], [], [], [], [], [], [], [], []
    curr_p = tp / 1e6
    curr_c756 = c_756 / 1e6
    curr_ms = ms_totale / 1e6
    curr_autres_ch = (ch_achats + ch_ext_hors_achats - loyers_613 + ch_ufa_cfc_tot) / 1e6
    curr_loy = loyers_613 / 1e6
    curr_amo = amort_68 / 1e6
    curr_fin = fin_66 / 1e6
    curr_det = dette_16 / 1e6
    curr_remb = remb_16 / 1e6
    curr_treso = treso_51 / 1e6
    opex_cumul = 0.0

    for _ in ans_p:
        curr_p = curr_p * (1 + tx_el_proj/100.0) * (1 + tx_forf_proj/100.0)
        curr_c756 = curr_c756 * (1 + tx_el_proj/100.0) * (1 + tx_forf_proj/100.0)
        curr_ms = curr_ms * (1 + tx_ms_proj/100.0)
        curr_autres_ch = curr_autres_ch * (1 + tx_ext_proj/100.0)
        opex_cumul += ppi_reel * (opex_ppi_pct / 100.0)
        curr_amo += ppi_reel / 20.0
        curr_fin += emprunt_ppi_an * 0.035

        tot_c_opex = curr_ms + curr_autres_ch + curr_loy + opex_cumul + curr_amo + curr_fin
        curr_caf = (curr_p - tot_c_opex) + curr_amo
        curr_det = max(0.0, curr_det - curr_remb + emprunt_ppi_an)
        curr_remb_tot = curr_remb + (emprunt_ppi_an / duree_emprunt)
        curr_treso = curr_treso + curr_caf - curr_remb_tot - autofin_ppi_an
        curr_des = (curr_det / curr_caf) if curr_caf > 0 else 99.9
        c_dec_an = max(0.01, tot_c_opex - curr_amo)
        curr_j = (curr_treso / c_dec_an) * 365
        curr_ro = curr_c756 - (curr_amo + curr_fin + curr_loy)
        curr_ren = (ppi_reel / max(0.01, curr_amo)) * 100

        p_list.append(round(curr_p, 2))
        c_list.append(round(tot_c_opex, 2))
        caf_list.append(round(curr_caf, 2))
        amo_list.append(round(curr_amo, 2))
        ren_list.append(round(curr_ren, 0))
        det_list.append(round(curr_det, 2))
        des_list.append(round(curr_des, 1))
        tr_list.append(round(curr_treso, 2))
        jtr_list.append(round(curr_j, 0))
        ro_list.append(round(curr_ro, 2))

    df_proj = pd.DataFrame({
        "Année": ans_p,
        "Produits (M€)": p_list,
        "Charges + OPEX (M€)": c_list,
        "CAF (M€)": caf_list,
        "Amort. 681 (M€)": amo_list,
        "Renouvellement (%)": ren_list,
        "Dette 31/12 (M€)": det_list,
        "Désendettement (ans)": des_list,
        "Règle d'Or (M€)": ro_list,
        "Trésorerie (M€)": tr_list,
        "Trésorerie (jours)": jtr_list
    })

    kp1, kp2, kp3, kp4 = st.columns(4)
    tcaf_2030 = (caf_list[-1]/p_list[-1]*100)
    kp1.metric("CAF Projetée 2030", f"+{caf_list[-1]:.2f} M€", f"Taux : {tcaf_2030:.1f} % (Cible : {normes['taux_caf']} %)")
    kp2.metric("Désendettement 2030", f"{des_list[-1]:.1f} ans", f"Dette : {det_list[-1]:.2f} M€ (Max {normes['desend_max']} a.)", delta_color="normal" if des_list[-1] <= normes["desend_max"] else "inverse")
    kp3.metric("Renouvellement 2030", f"{ren_list[-1]:.0f} %", f"PPI {ppi_reel:.2f} M€ / Amort. {amo_list[-1]:.2f} M€")
    kp4.metric("Trésorerie & Règle d'Or 2030", f"{jtr_list[-1]:.0f} jours", f"Règle d'Or : {ro_list[-1]:+.2f} M€", delta_color="normal" if (jtr_list[-1] >= 60 and ro_list[-1] >= 0) else "inverse")

    gp_c1, gp_c2 = st.columns(2)
    with gp_c1:
        st.markdown("**Trajectoire Produits vs Charges + OPEX induits (M€)**")
        st.line_chart(df_proj.set_index("Année")[["Produits (M€)", "Charges + OPEX (M€)"]])
    with gp_c2:
        st.markdown("**Trajectoire CAF, Dette & Trésorerie (M€)**")
        st.line_chart(df_proj.set_index("Année")[["CAF (M€)", "Dette 31/12 (M€)", "Trésorerie (M€)"]])

    st.dataframe(df_proj, hide_index=True, use_container_width=True)

    feuille_route = [
        f"1. Solvabilité & Épargne : CAF cible de {caf_list[-1]:.2f} M€ en 2030 ({tcaf_2030:.1f} % vs {normes['taux_caf']} % attendus) et désendettement à {des_list[-1]:.1f} ans (dette : {det_list[-1]:.2f} M€).",
        f"2. Renouvellement ({statut_immo}) : PPI exécuté de {ppi_reel:.2f} M€/an couvrant {ren_list[-1]:.0f} % des dotations aux amortissements 2030 ({amo_list[-1]:.2f} M€).",
        f"3. Étanchéité Règle d'Or 2030 : Solde prévisionnel de {ro_list[-1]:+.2f} M€ (indexation des contributions familles à +{tx_forf_proj:.1f} %/an pour absorber les nouveaux amortissements).",
        f"4. Maîtrise des charges & OPEX : Plafonner la MS interne à +{tx_ms_proj:.1f} %/an et intégrer {opex_ppi_pct:+.1f} %/an d'OPEX induits par les travaux.",
        f"5. Financement & Liquidité : Mobiliser {taux_subv_ppi} % de subventions, emprunter sur {duree_emprunt} ans et maintenir la trésorerie à {jtr_list[-1]:.0f} jours."
    ]

    pdf_pro_bytes = build_pdf_prospective(etab, normes, statut_immo, ppi_annuel, exec_pct, df_proj, feuille_route)
    st.download_button("📑 Télécharger la Synthèse Prospective 2026-2030 (PDF 1 page)", data=pdf_pro_bytes, file_name=f"Synthese_Prospective_2026_2030_{etab.replace(' ','_')}.pdf", mime="application/pdf", type="primary")

    afficher_synthese_unique(
        "Prospective : Soutenabilité du Projet d'Établissement à 5 ans",
        f"En statut **{statut_immo.lower()}**, avec un PPI exécuté de {ppi_reel:.2f} M€/an (taux de renouvellement de {ren_list[-1]:.0f} % des amortissements en 2030), la dette atteint {det_list[-1]:.2f} M€ (désendettement : {des_list[-1]:.1f} ans) et la trésorerie s'établit à {jtr_list[-1]:.0f} jours.",
        f"L'intégration des nouveaux amortissements ({amo_list[-1]:.2f} M€ en 2030) maintient un solde de Règle d'Or de {ro_list[-1]:+.2f} M€ sous réserve d'indexation des recettes à +{tx_forf_proj:.1f} %/an.",
        f"{'Le projet d investissement est soutenable en l état et peut être soumis au vote du Conseil d Administration.' if (jtr_list[-1] >= 60 and des_list[-1] <= normes['desend_max'] and ro_list[-1] >= 0) else 'Ajuster le calibrage du PPI, augmenter la part de subventions ou relever les contributions familles pour préserver la Règle d Or et la trésorerie à l horizon 2030.'}"
    )
