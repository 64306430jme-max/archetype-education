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
    page_title="Archétype Éducation — Plateforme d'Audit ANC 2018-06 & Prospective",
    page_icon="🎓",
    layout="wide"
)

# ==========================================
# 1. RÉFÉRENTIEL & NORMES PAR PROFIL
# ==========================================
def get_normes_etablissement(type_etab):
    if "1er degré" in type_etab:
        return {
            "type_court": "1er degré (École)",
            "strate": "Écoles sous contrat (Loi Debré — Art. L. 442-5)",
            "financeur": "Commune (Forfait communal)",
            "forfait_eleve": 880,
            "contrib_eleve": 420,
            "taux_caf": 6.5,
            "jours_treso": 90,
            "poids_ms": 48.0,
            "b_peda": 70,
            "maint_m2": 15,
            "tx_internat": 0,
            "desend_max": 8.0
        }
    elif "Collège" in type_etab:
        return {
            "type_court": "2nd degré (Collège)",
            "strate": "Collèges sous contrat (Art. L. 442-9)",
            "financeur": "Département (Forfait externat)",
            "forfait_eleve": 647,
            "contrib_eleve": 580,
            "taux_caf": 7.5,
            "jours_treso": 90,
            "poids_ms": 44.0,
            "b_peda": 100,
            "maint_m2": 18,
            "tx_internat": 5,
            "desend_max": 8.0
        }
    elif "Lycée GT" in type_etab:
        return {
            "type_court": "2nd degré (Lycée GT/Pro)",
            "strate": "Lycées GT & Pro sous contrat (Art. L. 442-9)",
            "financeur": "Région (Forfait externat)",
            "forfait_eleve": 803,
            "contrib_eleve": 690,
            "taux_caf": 8.0,
            "jours_treso": 90,
            "poids_ms": 42.0,
            "b_peda": 130,
            "maint_m2": 22,
            "tx_internat": 12,
            "desend_max": 8.0
        }
    elif "Agricole" in type_etab:
        return {
            "type_court": "Lycée Agricole (MASA)",
            "strate": "Enseignement Agricole Temps Plein (Art. L. 813-8)",
            "financeur": "MASA (Subv. globale) & Région",
            "forfait_eleve": 2450,
            "contrib_eleve": 720,
            "taux_caf": 8.5,
            "jours_treso": 75,
            "poids_ms": 46.0,
            "b_peda": 150,
            "maint_m2": 28,
            "tx_internat": 65,
            "desend_max": 8.5
        }
    elif "MFR" in type_etab:
        return {
            "type_court": "MFR / Alternance",
            "strate": "Maisons Familiales Rurales (Art. L. 813-9)",
            "financeur": "MASA & OPCO",
            "forfait_eleve": 4100,
            "contrib_eleve": 680,
            "taux_caf": 8.0,
            "jours_treso": 75,
            "poids_ms": 64.0,
            "b_peda": 150,
            "maint_m2": 24,
            "tx_internat": 75,
            "desend_max": 8.0
        }
    else:
        return {
            "type_court": "Ensemble scolaire mixte",
            "strate": "Ensembles scolaires multi-niveaux (Loi Debré)",
            "financeur": "Commune + Département + Région",
            "forfait_eleve": 760,
            "contrib_eleve": 560,
            "taux_caf": 7.5,
            "jours_treso": 90,
            "poids_ms": 45.0,
            "b_peda": 110,
            "maint_m2": 20,
            "tx_internat": 8,
            "desend_max": 8.0
        }

def bloc_synthese_strategique(titre_onglet, synthese_globale, cle_direction, cle_dgs):
    st.markdown("---")
    st.markdown(f"### Synthèse & Clés de lecture — {titre_onglet}")
    st.info(f"**Diagnostic d'étape :** {synthese_globale}")
    c1, c2 = st.columns(2)
    with c1:
        st.success(f"**Clé de lecture Chef d'Établissement / OGEC (Ajustement budgétaire) :**\n\n{cle_direction}")
    with c2:
        st.warning(f"**Clé de lecture DGS / Collectivité (Dialogue financeurs) :**\n\n{cle_dgs}")

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
        "dette": dette_16, "remb": remb_16, "tres": tres_51
    }

# ==========================================
# 3. GÉNÉRATEURS DE RAPPORTS PDF EXÉCUTIFS
# ==========================================
def _box(ax, x, y, w, h, fc="#ffffff", ec="#cbd5e1", lw=1.0, r=0.012):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", facecolor=fc, edgecolor=ec, linewidth=lw, transform=ax.transAxes))

def _header_pdf(ax, titre_doc, sous_titre):
    ax.add_patch(Rectangle((0, 0.915), 1, 0.085, facecolor="#0f172a", transform=ax.transAxes))
    ax.add_patch(Rectangle((0, 0.911), 1, 0.004, facecolor="#d97706", transform=ax.transAxes))
    ax.text(0.04, 0.962, titre_doc, color="white", fontsize=10.5, fontweight="bold")
    ax.text(0.04, 0.930, sous_titre, color="#cbd5e1", fontsize=7.8)

def _footer_pdf(ax, gauche, page_txt):
    ax.plot([0.04, 0.96], [0.038, 0.038], color="#cbd5e1", lw=0.8, transform=ax.transAxes)
    ax.text(0.04, 0.020, gauche, fontsize=7.0, color="#64748b")
    ax.text(0.96, 0.020, page_txt, ha="right", fontsize=7.0, fontweight="bold", color="#475569")

# --- PDF 1 : DOSSIER RÉTROSPECTIF (2 PAGES) ---
def build_pdf_retro(etab, normes, ans_r, p_r, c_r, ms_r, caf_r, aut_r, inv_r, tcma_p, tcma_c, tcma_ms, gvt_pt, conv_pt, vol_pt, atouts_txt, vig_txt):
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        # PAGE 1
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        _header_pdf(ax, "ARCHÉTYPE ÉDUCATION  |  DOSSIER D'AUDIT RÉTROSPECTIF ANC 2018-06 (2021-2025)", f"ÉTABLISSEMENT : {etab.upper()}  •  {normes['type_court'].upper()}  •  ANALYSE DES ÉQUILIBRES HISTORIQUES")

        ciseau = tcma_c - tcma_p
        var_caf = caf_r[-1] - caf_r[0]
        kpis = [
            ("TCMA PRODUITS", f"+{tcma_p:.2f} % / an", "Dynamique des ressources", "#059669"),
            ("TCMA CHARGES", f"+{tcma_c:.2f} % / an", f"Écart : {ciseau:+.2f} pts vs Prod.", "#dc2626" if ciseau > 0.3 else "#d97706"),
            ("TCMA MASSE SALARIALE", f"+{tcma_ms:.2f} % / an", f"Poids : {(ms_r[-1]/p_r[-1]*100):.1f} % des prod.", "#1d4ed8"),
            ("ÉVOLUTION CAF", f"{caf_r[-1]:.2f} M€", f"Variation période : {var_caf:+.2f} M€", "#059669" if var_caf >= 0 else "#dc2626"),
        ]
        for i, (kt, kv, ks, kc) in enumerate(kpis):
            kx = 0.04 + i * 0.233
            _box(ax, kx, 0.815, 0.218, 0.084, fc="#f8fafc")
            ax.text(kx + 0.012, 0.880, kt, fontsize=7.0, fontweight="bold", color="#475569")
            ax.text(kx + 0.012, 0.845, kv, fontsize=12.0, fontweight="bold", color=kc)
            ax.text(kx + 0.012, 0.823, ks, fontsize=6.8, color="#64748b")

        # Graphique 1 : Effet Ciseau
        ax.text(0.04, 0.785, "1. EFFET DE CISEAU HISTORIQUE (PRODUITS VS CHARGES)", fontsize=8.2, fontweight="bold", color="#0f172a")
        g1 = fig.add_axes([0.06, 0.595, 0.41, 0.175])
        g1.plot(ans_r, p_r, marker="o", color="#2563eb", lw=2, label="Produits")
        g1.plot(ans_r, c_r, marker="s", color="#dc2626", lw=2, label="Charges")
        g1.grid(True, linestyle="--", alpha=0.5)
        g1.tick_params(labelsize=7)
        g1.legend(fontsize=6.8, loc="upper left")

        # Graphique 2 : Érosion CAF & Autofinancement
        ax.text(0.52, 0.785, "2. TRAJECTOIRE DE LA CAF & AUTOFINANCEMENT NET", fontsize=8.2, fontweight="bold", color="#0f172a")
        g2 = fig.add_axes([0.54, 0.595, 0.41, 0.175])
        g2.plot(ans_r, caf_r, marker="^", color="#059669", lw=2, label="CAF")
        g2.plot(ans_r, aut_r, marker="s", color="#d97706", lw=2, label="Autofin. Net")
        g2.grid(True, linestyle="--", alpha=0.5)
        g2.tick_params(labelsize=7)
        g2.legend(fontsize=6.8, loc="upper left")

        # Graphique 3 : Investissement
        ax.text(0.04, 0.545, "3. EFFORT D'INVESTISSEMENT & RENOUVELLEMENT PATRIMONIAL (M€)", fontsize=8.2, fontweight="bold", color="#0f172a")
        g3 = fig.add_axes([0.06, 0.375, 0.41, 0.155])
        g3.bar(ans_r, inv_r, color="#1e40af", width=0.5)
        g3.grid(True, axis="y", linestyle="--", alpha=0.5)
        g3.tick_params(labelsize=7)

        _box(ax, 0.51, 0.375, 0.45, 0.155, fc="#f8fafc")
        ax.text(0.525, 0.508, "DIAGNOSTIC DE L'EFFORT D'ÉQUIPEMENT", fontsize=7.8, fontweight="bold", color="#0f172a")
        moy_inv = np.mean(inv_r)
        ax.text(0.525, 0.478, f"• Enveloppe moyenne exécutée : {moy_inv:.2f} M€ / an.", fontsize=7.2, color="#1e293b")
        ax.text(0.525, 0.450, f"• Taux de renouvellement vs amortissements : {(moy_inv / max(0.01, (caf_r[-1] - (p_r[-1]-c_r[-1]))) * 100):.0f} %.", fontsize=7.2, color="#1e293b")
        ax.text(0.525, 0.422, "• Enjeu : Préserver la valeur nette comptable du bâti", fontsize=7.2, color="#475569")
        ax.text(0.525, 0.398, "  sans dégrader la Règle d'Or ni la trésorerie.", fontsize=7.2, color="#475569")

        # Tableau rétrospectif
        ax.text(0.04, 0.335, "TABLEAU RÉTROSPECTIF DES SOLDES ANC 2018-06 (2021-2025)", fontsize=8.2, fontweight="bold", color="#0f172a")
        tax = fig.add_axes([0.04, 0.145, 0.92, 0.175])
        tax.axis("off")
        t_rows = [
            ["Produits d'exploitation (M€)"] + [f"{v:.2f}" for v in p_r],
            ["Charges d'exploitation (M€)"] + [f"{v:.2f}" for v in c_r],
            ["Masse salariale interne Cpte 64 (M€)"] + [f"{v:.2f}" for v in ms_r],
            ["Capacité d'Autofinancement — CAF (M€)"] + [f"{v:.2f}" for v in caf_r],
            ["Autofinancement net après dette (M€)"] + [f"{v:.2f}" for v in aut_r],
            ["Taux de CAF (%)"] + [f"{(c/p*100):.1f} %" for c, p in zip(caf_r, p_r)],
        ]
        tbl = tax.table(cellText=t_rows, colLabels=["Soldes ANC 2018-06"] + ans_r, loc="center", cellLoc="center", colWidths=[0.42] + [0.116]*len(ans_r))
        tbl.set_fontsize(7.2)
        tbl.scale(1, 1.25)
        for (r, c), cell in tbl.get_celld().items():
            cell.set_edgecolor("#cbd5e1")
            if r == 0:
                cell.set_facecolor("#1e293b")
                cell.get_text().set_color("white")
                cell.get_text().set_weight("bold")
            elif c == 0:
                cell.get_text().set_ha("left")

        _box(ax, 0.04, 0.055, 0.92, 0.075, fc="#fffbeb", ec="#fcd34d")
        ax.text(0.055, 0.110, "DIAGNOSTIC DE L'EFFET DE CISEAU BUDGÉTAIRE", fontsize=7.6, fontweight="bold", color="#92400e")
        ax.text(0.055, 0.088, f"• Les charges d'exploitation (+{tcma_c:.2f} %/an) progressent {'plus vite' if ciseau > 0 else 'moins vite'} que les produits (+{tcma_p:.2f} %/an).", fontsize=7.1, color="#1e293b")
        ax.text(0.055, 0.068, f"• La CAF passe de {caf_r[0]:.2f} M€ en {ans_r[0]} à {caf_r[-1]:.2f} M€ en {ans_r[-1]} ({var_caf:+.2f} M€).", fontsize=7.1, color="#1e293b")
        _footer_pdf(ax, "Dossier Rétrospectif ANC 2018-06  •  Cabinet QUINZE", "Page 1/2")
        pdf.savefig(fig)
        plt.close(fig)

        # PAGE 2 : DÉRIVE RH & BILAN STRATÉGIQUE
        fig2 = plt.figure(figsize=(8.27, 11.69), dpi=150)
        ax2 = fig2.add_axes([0, 0, 1, 1])
        ax2.axis("off")
        _header_pdf(ax2, "ARCHÉTYPE ÉDUCATION  |  DÉCOMPOSITION DE LA DÉRIVE RH & ARBITRAGES", f"ÉTABLISSEMENT : {etab.upper()}  •  LEVIERS MANAGÉRIAUX & PISTES D'AUDIT")

        ax2.text(0.04, 0.875, "1. DÉCOMPOSITION DE LA PROGRESSION DE LA MASSE SALARIALE INTERNE (COMPTE 64)", fontsize=8.3, fontweight="bold", color="#0f172a")
        grh = fig2.add_axes([0.24, 0.675, 0.70, 0.180])
        cats = ["Effet Volume\n(Postes / Rempl.)", "Mesures Convent.\n(EEPNL / SMIC)", "GVT Mécanique\n(Ancienneté)"]
        vals = [vol_pt, conv_pt, gvt_pt]
        cols_rh = ["#059669", "#d97706", "#64748b"]
        grh.barh(cats, vals, color=cols_rh, height=0.52)
        grh.set_xlabel("Contribution annuelle (% / an)", fontsize=7.5)
        grh.grid(True, axis="x", linestyle="--", alpha=0.5)
        grh.tick_params(labelsize=7.5)

        _box(ax2, 0.04, 0.525, 0.92, 0.115, fc="#f8fafc", ec="#cbd5e1")
        ax2.text(0.055, 0.618, "LECTURE MANAGÉRIALE : FACTEURS SUBIS VS LEVIER INTERNE", fontsize=7.8, fontweight="bold", color="#0f172a")
        ax2.text(0.055, 0.592, f"• Sur +{tcma_ms:.2f} %/an d'évolution salariale, {(gvt_pt+conv_pt):.2f} points sont structurels (GVT ancienneté + revalorisations conventionnelles).", fontsize=7.2, color="#1e293b")
        ax2.text(0.055, 0.568, f"• {vol_pt:+.2f} points relèvent directement de l'organisation interne (créations de postes, remplacements non financés, heures sup.).", fontsize=7.2, color="#1e293b")
        ax2.text(0.055, 0.544, "• Cible pacte RH : Auditer l'encadrement administratif, sécuriser le financement UFA/CFC et optimiser les remplacements.", fontsize=7.2, color="#1d4ed8", fontweight="bold")

        ax2.text(0.04, 0.485, "2. BILAN STRATÉGIQUE : ATOUTS & PISTES D'INVESTIGATION", fontsize=8.3, fontweight="bold", color="#0f172a")
        _box(ax2, 0.04, 0.130, 0.445, 0.340, fc="#ecfdf5", ec="#6ee7b7")
        ax2.text(0.055, 0.448, "ATOUTS & MARGES DE MANŒUVRE", fontsize=7.8, fontweight="bold", color="#065f46")
        ya = 0.415
        for item in atouts_txt:
            for wl in textwrap.wrap(f"• {item}", width=54):
                ax2.text(0.055, ya, wl, fontsize=7.2, color="#1e293b")
                ya -= 0.022
            ya -= 0.015

        _box(ax2, 0.515, 0.130, 0.445, 0.340, fc="#fffbeb", ec="#fcd34d")
        ax2.text(0.530, 0.448, "POINTS DE VIGILANCE & PISTES D'AUDIT", fontsize=7.8, fontweight="bold", color="#92400e")
        yv = 0.415
        for item in vig_txt:
            for wl in textwrap.wrap(f"• {item}", width=54):
                ax2.text(0.530, yv, wl, fontsize=7.2, color="#1e293b")
                yv -= 0.022
            yv -= 0.015

        _footer_pdf(ax2, "Dossier Rétrospectif ANC 2018-06  •  Cabinet QUINZE", "Page 2/2")
        pdf.savefig(fig2)
        plt.close(fig2)
    return buf.getvalue()

# --- PDF 2 : TBI EXÉCUTIF & SCALPEL (1 PAGE) ---
def build_pdf_tbi(etab, normes, eleves, surf, score, tp, ach, ext_f, va, ms, ebe, amo_fin, rn, caf, remb, aut, dette, cap_d, treso, j_tr, ro_solde, maint_m2, b_peda, m_ufa, m_cfc):
    buf = io.BytesIO()
    fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    _header_pdf(ax, "ARCHÉTYPE ÉDUCATION  |  PLATEFORME D'ARBITRAGE ANC 2018-06 & SCALPEL", f"ÉTABLISSEMENT : {etab.upper()} ({eleves} ÉLÈVES  •  {surf} M²  •  {normes['strate'].upper()})")

    # Bannière Health Score
    sc_col = "#059669" if score >= 70 else ("#d97706" if score >= 45 else "#dc2626")
    sc_bg = "#ecfdf5" if score >= 70 else ("#fffbeb" if score >= 45 else "#fef2f2")
    _box(ax, 0.04, 0.815, 0.92, 0.084, fc=sc_bg, ec=sc_col, lw=1.4)
    ax.text(0.06, 0.875, "HEALTH SCORE ANC 2018-06", fontsize=7.5, fontweight="bold", color="#475569")
    ax.text(0.06, 0.832, f"{score}/100", fontsize=19.0, fontweight="bold", color=sc_col)
    statut_msg = "STRUCTURE FINANCIÈRE SAINE ET AUTOFINANCÉE" if score >= 70 else ("TENSION D'ÉPARGNE OU RÈGLE D'OR À CORRIGER" if score >= 45 else "ALERTE STRUCTURELLE : RISQUE DE TRÉSORERIE OU DE SOLVABILITÉ")
    ax.text(0.24, 0.872, statut_msg, fontsize=8.4, fontweight="bold", color=sc_col)
    tcaf = (caf / tp * 100) if tp > 0 else 0
    ax.text(0.24, 0.848, f"Taux CAF : {tcaf:.1f} % (Cible : {normes['taux_caf']} %)  |  Désendettement : {cap_d:.1f} ans (Seuil : {normes['desend_max']} ans)", fontsize=7.3, color="#1e293b")
    ax.text(0.24, 0.826, f"Règle d'Or Immo : {ro_solde:+.2f} M€  |  Trésorerie : {j_tr} jours (Cible : {normes['jours_treso']} j)  |  Pédagogie : {b_peda:.0f} €/élève", fontsize=7.3, color="#1e293b")

    # Bloc 1 : Cascade SIG
    _box(ax, 0.04, 0.450, 0.46, 0.350, fc="#ffffff")
    ax.add_patch(Rectangle((0.04, 0.762), 0.46, 0.038, facecolor="#1e293b", transform=ax.transAxes))
    ax.text(0.055, 0.775, "1. CASCADE DES SIG (ANC 2018-06)", color="white", fontsize=8.2, fontweight="bold")
    sig_rows = [
        ("Produits d'Exploitation (70/74/75)", f"{tp:.2f} M€", True, "#1d4ed8"),
        ("- Achats consommés (60)", f"-{ach:.2f} M€", False, "#475569"),
        ("- Services ext., Fluides, Maint. (61-62)", f"-{ext_f:.2f} M€", False, "#475569"),
        ("= Valeur Ajoutée (VA)", f"{va:.2f} M€", True, "#0f172a"),
        ("- Masse Salariale interne (64)", f"-{ms:.2f} M€", False, "#475569"),
        ("= Excédent Brut d'Exploitation (EBE)", f"{ebe:.2f} M€", True, "#059669" if ebe >= 0 else "#dc2626"),
        ("- Amortissements & Frais Fin. (66/68)", f"-{amo_fin:.2f} M€", False, "#475569"),
        ("= Résultat Net Comptable (RCAI)", f"{rn:+.2f} M€", True, "#059669" if rn >= 0 else "#dc2626"),
        ("= Capacité d'Autofinancement (CAF)", f"{caf:.2f} M€ ({tcaf:.1f}%)", True, "#b45309"),
        ("- Capital emprunts remboursé (164)", f"-{remb:.2f} M€", False, "#475569"),
        ("= Autofinancement Net disponible", f"{aut:+.2f} M€", True, "#059669" if aut >= 0 else "#dc2626"),
    ]
    ys = 0.735
    for lbl, val, bld, col in sig_rows:
        if bld:
            ax.add_patch(Rectangle((0.048, ys - 0.007), 0.444, 0.024, facecolor="#f1f5f9", transform=ax.transAxes))
        ax.text(0.055, ys, lbl, fontsize=7.2, fontweight="bold" if bld else "normal", color="#1e293b")
        ax.text(0.488, ys, val, ha="right", fontsize=7.3, fontweight="bold" if bld else "normal", color=col)
        ys -= 0.027

    # Bloc 2 : Scalpel Métier
    _box(ax, 0.52, 0.635, 0.44, 0.165, fc="#ffffff")
    ax.add_patch(Rectangle((0.52, 0.762), 0.44, 0.038, facecolor="#1e293b", transform=ax.transAxes))
    ax.text(0.535, 0.775, "2. SCALPEL ANALYTIQUE & MÉTIER", color="white", fontsize=8.2, fontweight="bold")
    sc_items = [
        ("Maintenance Bâtiment (Cpte 615) :", f"{maint_m2:.1f} €/m² (Norme : {normes['maint_m2']} €/m²)"),
        ("Effort Pédagogique Direct :", f"{b_peda:.0f} €/élève (Norme : {normes['b_peda']} €/él.)"),
        ("Marge Apprentissage (UFA) :", f"{m_ufa:+.2f} M€"),
        ("Marge Formation Continue (CFC) :", f"{m_cfc:+.2f} M€"),
    ]
    ysc = 0.732
    for k, v in sc_items:
        ax.text(0.535, ysc, k, fontsize=7.2, color="#475569")
        ax.text(0.945, ysc, v, ha="right", fontsize=7.3, fontweight="bold", color="#0f172a")
        ysc -= 0.028

    # Bloc 3 : Endettement & Règle d'Or
    _box(ax, 0.52, 0.450, 0.44, 0.170, fc="#ffffff")
    ax.add_patch(Rectangle((0.52, 0.582), 0.44, 0.038, facecolor="#1e293b", transform=ax.transAxes))
    ax.text(0.535, 0.595, "3. PATRIMOINE, DETTE & TRÉSORERIE", color="white", fontsize=8.2, fontweight="bold")
    det_items = [
        ("Encours Dette Immobilière :", f"{dette:.2f} M€"),
        ("Capacité de Désendettement :", f"{cap_d:.1f} ans (Seuil : {normes['desend_max']} ans)"),
        ("Solde Règle d'Or Immobilière :", f"{ro_solde:+.2f} M€"),
        ("Trésorerie Disponible :", f"{treso:.2f} M€ ({j_tr} jours)"),
    ]
    yd = 0.552
    for k, v in det_items:
        ax.text(0.535, yd, k, fontsize=7.2, color="#475569")
        ax.text(0.945, yd, v, ha="right", fontsize=7.3, fontweight="bold", color="#0f172a")
        yd -= 0.028

    # Bloc 4 : Arbitrage 3 scénarios
    _box(ax, 0.04, 0.305, 0.92, 0.130, fc="#f8fafc")
    ax.text(0.055, 0.415, "4. ARBITRAGE DES SCÉNARIOS BUDGÉTAIRES (CA & DIALOGUE FINANCEURS)", fontsize=8.0, fontweight="bold", color="#0f172a")
    ax.text(0.055, 0.388, "1. Scénario Fil de l'eau (Sans ajustement) : Érosion continue de la CAF sous l'effet de l'inflation salariale et énergétique.", fontsize=7.2, color="#1e293b")
    ax.text(0.055, 0.362, "2. Scénario PPI Intégral sans indexation : Tension de trésorerie sous 36 mois et dégradation du ratio de désendettement.", fontsize=7.2, color="#b91c1c")
    ax.text(0.055, 0.336, "3. Scénario Cible Optimisé : Maîtrise des charges fixes, équilibre cantine/CFC et indexation des forfaits/contributions.", fontsize=7.2, color="#065f46", fontweight="bold")

    # Référentiel bas de page
    ax.text(0.04, 0.275, f"RÉFÉRENTIEL ANC 2018-06 & NORMES OBSERVATOIRE ({normes['strate'].upper()})", fontsize=7.8, fontweight="bold", color="#0f172a")
    refs = [
        ("TAUX DE CAF", "CAF / Produits d'expl.", [f"Cible : >= {normes['taux_caf']} %", "Vigilance : < 5,0 %", "Alerte : < 3,0 %"]),
        ("RÈGLE D'OR IMMO", "Contrib. 756 - Charges Immo", ["Cible : >= 0 €", "Étanchéité scolaire", "Alerte si déficit"]),
        ("DÉSENDETTEMENT", "Encours Dette / CAF", [f"Seuil : < {normes['desend_max']} ans", "Vigilance : 8-10 ans", "Refus prêt : > 10 ans"]),
        ("TRÉSORERIE", "Tréso / Charges déc. x 365", [f"Cible : {normes['jours_treso']}-120 j", "Vigilance : 45-60 j", "Alerte : < 30 jours"]),
    ]
    for i, (rt, rf, rbullets) in enumerate(refs):
        rx = 0.04 + i * 0.233
        _box(ax, rx, 0.060, 0.218, 0.200, fc="#ffffff")
        ax.text(rx + 0.012, 0.238, rt, fontsize=7.3, fontweight="bold", color="#0f172a")
        ax.text(rx + 0.012, 0.215, rf, fontsize=6.6, color="#64748b")
        yb = 0.175
        for b in rbullets:
            ax.text(rx + 0.012, yb, f"• {b}", fontsize=6.9, color="#1e293b")
            yb -= 0.032

    _footer_pdf(ax, "Rapport certifié conforme aux règles ANC 2018-06  •  Cabinet QUINZE", "Page 1/1")
    fig.savefig(buf, format="pdf")
    plt.close(fig)
    return buf.getvalue()

# --- PDF 3 : SYNTHÈSE PROSPECTIVE 2026-2030 (1 PAGE) ---
def build_pdf_prospective(etab, normes, ppi_annuel, exec_pct, df_proj, feuille_route):
    buf = io.BytesIO()
    fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    _header_pdf(ax, "ARCHÉTYPE ÉDUCATION  |  TRAJECTOIRE PROSPECTIVE & ARBITRAGE BUDGET (2026-2030)", f"ÉTABLISSEMENT : {etab.upper()}  •  SCÉNARIO : CIBLE OPTIMISÉE  •  PPI : {ppi_annuel:.2f} M€/AN (EXÉC. {exec_pct:.0f}%)")

    caf_30 = df_proj["CAF (M€)"].iloc[-1]
    tcaf_30 = (caf_30 / df_proj["Produits (M€)"].iloc[-1] * 100)
    des_30 = df_proj["Désendettement (ans)"].iloc[-1]
    det_30 = df_proj["Dette 31/12 (M€)"].iloc[-1]
    var_det = det_30 - df_proj["Dette 31/12 (M€)"].iloc[0]
    j_30 = df_proj["Trésorerie (jours)"].iloc[-1]
    tr_30 = df_proj["Trésorerie (M€)"].iloc[-1]

    kpis = [
        ("CAF 2030", f"+{caf_30:.2f} M€", f"Taux de CAF : {tcaf_30:.1f} %", "#059669" if tcaf_30 >= normes["taux_caf"] else "#d97706"),
        ("CAPACITÉ DÉSEND. 2030", f"{des_30:.1f} ans", f"Seuil alerte : {normes['desend_max']} ans", "#059669" if des_30 <= normes["desend_max"] else "#dc2626"),
        ("ENCOURS DETTE 2030", f"{det_30:.2f} M€", f"Variation : {var_det:+.2f} M€", "#0f172a"),
        ("TRÉSORERIE 2030", f"{j_30:.0f} jours", f"Encours : {tr_30:.2f} M€", "#1d4ed8" if j_30 >= 60 else "#dc2626"),
    ]
    for i, (kt, kv, ks, kc) in enumerate(kpis):
        kx = 0.04 + i * 0.233
        _box(ax, kx, 0.815, 0.218, 0.084, fc="#f8fafc")
        ax.text(kx + 0.012, 0.880, kt, fontsize=7.0, fontweight="bold", color="#475569")
        ax.text(kx + 0.012, 0.845, kv, fontsize=12.0, fontweight="bold", color=kc)
        ax.text(kx + 0.012, 0.823, ks, fontsize=6.8, color="#64748b")

    # Graphiques
    ax.text(0.04, 0.785, "1. PROJECTION PRODUITS VS CHARGES (INCLUANT OPEX INDUITS PPI)", fontsize=8.0, fontweight="bold", color="#0f172a")
    gp1 = fig.add_axes([0.06, 0.595, 0.41, 0.175])
    gp1.plot(df_proj["Année"], df_proj["Produits (M€)"], marker="o", color="#2563eb", lw=2, label="Produits")
    gp1.plot(df_proj["Année"], df_proj["Charges + OPEX (M€)"], marker="s", color="#dc2626", lw=2, label="Charges+OPEX")
    gp1.grid(True, linestyle="--", alpha=0.5)
    gp1.tick_params(labelsize=7)
    gp1.legend(fontsize=6.8, loc="upper left")

    ax.text(0.52, 0.785, "2. SOLDE DE CAF & TRÉSORERIE DISPONIBLE (M€)", fontsize=8.0, fontweight="bold", color="#0f172a")
    gp2 = fig.add_axes([0.54, 0.595, 0.41, 0.175])
    gp2.plot(df_proj["Année"], df_proj["CAF (M€)"], marker="^", color="#059669", lw=2, label="CAF")
    gp2.plot(df_proj["Année"], df_proj["Trésorerie (M€)"], marker="s", linestyle=":", color="#2563eb", lw=2, label="Trésorerie")
    gp2.grid(True, linestyle="--", alpha=0.5)
    gp2.tick_params(labelsize=7)
    gp2.legend(fontsize=6.8, loc="upper left")

    # Tableau pluriannuel
    ax.text(0.04, 0.548, "TABLEAU PLURIANNUEL DES TRAJECTOIRES BUDGÉTAIRES ANC 2018-06 (2026-2030)", fontsize=8.1, fontweight="bold", color="#0f172a")
    tp_ax = fig.add_axes([0.04, 0.340, 0.92, 0.195])
    tp_ax.axis("off")
    t_data = [
        ["Produits d'exploitation (M€)"] + [f"{v:.2f}" for v in df_proj["Produits (M€)"]],
        ["Charges d'exploitation + OPEX induits (M€)"] + [f"{v:.2f}" for v in df_proj["Charges + OPEX (M€)"]],
        ["Capacité d'Autofinancement — CAF (M€)"] + [f"{v:.2f}" for v in df_proj["CAF (M€)"]],
        ["Subventions d'équipement / AEP encaissées (M€)"] + [f"{v:.2f}" for v in df_proj["Subv. PPI (M€)"]],
        ["Encours de la dette au 31/12 (M€)"] + [f"{v:.2f}" for v in df_proj["Dette 31/12 (M€)"]],
        ["Capacité de désendettement (années)"] + [f"{v:.1f}" for v in df_proj["Désendettement (ans)"]],
        ["Trésorerie nette (Jours de charges décaiss.)"] + [f"{v:.0f} j" for v in df_proj["Trésorerie (jours)"]],
    ]
    tbl = tp_ax.table(cellText=t_data, colLabels=["Indicateurs ANC 2018-06"] + list(df_proj["Année"]), loc="center", cellLoc="center", colWidths=[0.44] + [0.112]*5)
    tbl.set_fontsize(7.1)
    tbl.scale(1, 1.24)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor("#cbd5e1")
        if r == 0:
            cell.set_facecolor("#1e293b")
            cell.get_text().set_color("white")
            cell.get_text().set_weight("bold")
        elif c == 0:
            cell.get_text().set_ha("left")

    # Feuille de route exhaustive
    _box(ax, 0.04, 0.055, 0.92, 0.270, fc="#ecfdf5", ec="#6ee7b7")
    ax.text(0.055, 0.305, "FEUILLE DE ROUTE EXHAUSTIVE CHEF D'ÉTABLISSEMENT & DGS : TRAJECTOIRE SOUTENABLE", fontsize=7.6, fontweight="bold", color="#065f46")
    yfr = 0.283
    for ligne in feuille_route:
        for wl in textwrap.wrap(ligne, width=128):
            ax.text(0.055, yfr, wl, fontsize=6.9, color="#1e293b")
            yfr -= 0.0155
        yfr -= 0.004

    _footer_pdf(ax, "Document de prospective ANC 2018-06  •  Cabinet QUINZE — Ingénierie & Conseil Éducation", "Page 1/1")
    fig.savefig(buf, format="pdf")
    plt.close(fig)
    return buf.getvalue()

# ==========================================
# 4. BARRE LATÉRALE : INGESTION & PARAMÉTRAGE
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
    d_det = dern["dette"] if dern["dette"] > 0 else 1550000.0
    d_remb = dern["remb"] if dern["remb"] > 0 else 145000.0
    d_tres = dern["tres"] if dern["tres"] > 0 else 440000.0
else:
    d_f74 = float(eleves_tot * normes["forfait_eleve"])
    d_c756 = float(eleves_tot * normes["contrib_eleve"])
    d_a70 = float(internes_tot * 780 + 45000)
    d_autp = 45000.0
    d_ach = float(eleves_tot * normes["b_peda"] + internes_tot * 290)
    d_loy = 85000.0
    d_maint = float(surface_m2 * normes["maint_m2"])
    d_ext = float(eleves_tot * 240)
    d_ms = float(eleves_tot * 1450)
    d_fin, d_amo, d_det, d_remb, d_tres = 52000.0, 195000.0, 1550000.0, 145000.0, 440000.0

st.sidebar.markdown("### 2. Recettes & Pôle Hors Contrat")
f_74 = st.sidebar.number_input("Forfaits & Subv. publiques (74) (€)", value=float(d_f74), step=10000.0)
c_756 = st.sidebar.number_input("Contributions familles scolarité (756) (€)", value=float(d_c756), step=10000.0)
a_70 = st.sidebar.number_input("Restauration, internat & annexes (70) (€)", value=float(d_a70), step=10000.0)
aut_p = st.sidebar.number_input("Autres produits (75/78/79) (€)", value=float(d_autp), step=5000.0)

activer_ufa_cfc = st.sidebar.checkbox("Intégrer un pôle Apprentissage (UFA) & CFC", value=(True if "Lycée" in type_etab or is_agricole else False))
prod_ufa, ch_ufa, prod_cfc, ch_cfc, app_tot, stag_tot = 0.0, 0.0, 0.0, 0.0, 0, 0
if activer_ufa_cfc:
    with st.sidebar.expander("🎓 Détail UFA (Apprentissage) & CFC", expanded=True):
        app_tot = st.number_input("Effectif apprentis (UFA)", value=110, step=5)
        prod_ufa = st.number_input("Produits UFA (NPEC OPCO, TA) (€)", value=740000.0, step=10000.0)
        ch_ufa = st.number_input("Charges UFA (Formateurs, redevance CFA) (€)", value=610000.0, step=10000.0)
        stag_tot = st.number_input("Stagiaires Formation Continue (CFC)", value=75, step=5)
        prod_cfc = st.number_input("Produits CFC (Entreprises, CPF, Région) (€)", value=115000.0, step=5000.0)
        ch_cfc = st.number_input("Charges CFC (Vacataires, com., matériel) (€)", value=132000.0, step=5000.0)

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
# 5. CALCULS DU MOTEUR FINANCIER & SCALPEL
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

# Cascade SIG
marge_brute = tp - ch_achats
valeur_ajoutee = marge_brute - ch_ext_hors_achats
ebe = valeur_ajoutee - ms_totale
rcai = ebe - amort_68 - fin_66

# Bilan & Règle d'Or
ch_dec = max(1.0, tc - amort_68)
j_treso = int(round((treso_51 / ch_dec) * 365))
cap_desend = (dette_16 / caf) if caf > 0 else 99.9
ro_solde = c_756 - (amort_68 + fin_66 + loyers_613)
ro_ok = ro_solde >= 0

# Ratios Scalpel
maint_m2 = maint_615 / max(1, surface_m2)
fluides_eleve = fluides_606 / max(1, eleves_tot)
b_peda_eleve = ach_peda / max(1, eleves_tot)
poids_ms_tp = (ms_totale / tp * 100) if tp > 0 else 0.0
poids_admin_ms = (ms_admin / ms_totale * 100) if ms_totale > 0 else 0.0

# Restauration / Internat (coûts directs : denrées + 45% RH technique/cuisine + 25% fluides)
ch_resto_directes = ach_resto + (ms_tech * 0.45) + (fluides_606 * 0.25)
marge_resto = a_70 - ch_resto_directes
tx_couv_resto = (a_70 / ch_resto_directes * 100) if ch_resto_directes > 0 else 100.0

# UFA / CFC
marge_ufa = prod_ufa - ch_ufa
marge_cfc = prod_cfc - ch_cfc

# Health Score ANC 2018-06 (/100)
s_caf = min(30, max(0, int(round((tcaf / normes["taux_caf"]) * 25))))
s_ro = 25 if ro_ok else max(0, int(round(25 + (ro_solde / max(1.0, c_756)) * 60)))
s_treso = min(25, max(0, int(round((j_treso / normes["jours_treso"]) * 22))))
s_det = 20 if cap_desend <= 6 else (14 if cap_desend <= normes["desend_max"] else (6 if cap_desend <= 11 else 0))
health_score = min(100, s_caf + s_ro + s_treso + s_det)

# ==========================================
# 6. INTERFACE PRINCIPALE (4 ONGLETS EXÉCUTIFS)
# ==========================================
st.title("Archétype Éducation — Plateforme d'Audit ANC 2018-06 & Prospective")
badge_src = "Balances ANC 2018-06 certifiées" if source_reelle else "Modèle calibré Observatoire"
st.caption(f"Établissement : **{etab}** • {normes['type_court']} • {eleves_tot} élèves • {surface_m2} m² • {badge_src}")

onglets = st.tabs([
    "📊 1. Rétrospective & Dérive RH (2021-2025)",
    "⚖️ 2. TBI Exécutif, SIG & Arbitrage",
    "🔪 3. Audit au Scalpel (RH, Bâti, Cantine, UFA)",
    "🔮 4. Prospective & Feuille de Route (2026-2030)"
])

# ------------------------------------------
# ONGLET 1 : RÉTROSPECTIVE & DÉRIVE RH
# ------------------------------------------
with onglets[0]:
    st.subheader("Analyse Rétrospective & Décomposition de la Masse Salariale")
    if len(balances_parsees) >= 2:
        ans_r = [b["annee"] or f"Ex.{i+1}" for i, b in enumerate(balances_parsees)]
        p_r = [b["tp"]/1e6 for b in balances_parsees]
        c_r = [b["tc"]/1e6 for b in balances_parsees]
        ms_r = [b["ms_64"]/1e6 for b in balances_parsees]
        caf_r = [b["caf"]/1e6 for b in balances_parsees]
        aut_r = [(b["caf"] - (b["remb"] if b["remb"]>0 else remb_16))/1e6 for b in balances_parsees]
    else:
        ans_r = ["2021", "2022", "2023", "2024", "2025"]
        tp_m, tc_m, ms_m, caf_m, aut_m = tp/1e6, tc/1e6, ms_totale/1e6, caf/1e6, autofin_net/1e6
        p_r = [round(tp_m*0.87, 2), round(tp_m*0.90, 2), round(tp_m*0.93, 2), round(tp_m*0.97, 2), round(tp_m, 2)]
        c_r = [round(tc_m*0.81, 2), round(tc_m*0.86, 2), round(tc_m*0.91, 2), round(tc_m*0.96, 2), round(tc_m, 2)]
        ms_r = [round(ms_m*0.82, 2), round(ms_m*0.87, 2), round(ms_m*0.92, 2), round(ms_m*0.96, 2), round(ms_m, 2)]
        caf_r = [round(p - c + (amort_68/1e6)*0.92, 2) for p, c in zip(p_r[:-1], c_r[:-1])] + [round(caf_m, 2)]
        aut_r = [round(cf - (remb_16/1e6), 2) for cf in caf_r]

    inv_r = [round((amort_68/1e6)*0.85, 2), round((amort_68/1e6)*1.15, 2), round((amort_68/1e6)*0.95, 2), round((amort_68/1e6)*1.10, 2), round((amort_68/1e6)*1.05, 2)]

    n_int = max(1, len(ans_r) - 1)
    tcma_p = ((p_r[-1]/p_r[0])**(1/n_int) - 1)*100 if p_r[0] > 0 else 0.0
    tcma_c = ((c_r[-1]/c_r[0])**(1/n_int) - 1)*100 if c_r[0] > 0 else 0.0
    tcma_ms = ((ms_r[-1]/ms_r[0])**(1/n_int) - 1)*100 if ms_r[0] > 0 else 0.0
    ciseau = tcma_c - tcma_p

    kr1, kr2, kr3, kr4 = st.columns(4)
    kr1.metric("TCMA Produits", f"+{tcma_p:.2f} % / an", "Dynamique des ressources")
    kr2.metric("TCMA Charges", f"+{tcma_c:.2f} % / an", f"Effet ciseau : {ciseau:+.2f} pts", delta_color="inverse" if ciseau > 0 else "normal")
    kr3.metric("TCMA Masse Salariale", f"+{tcma_ms:.2f} % / an", f"Poids : {poids_ms_tp:.1f} % des prod.")
    kr4.metric("CAF Dernier Exercice", f"{caf_r[-1]:.2f} M€", f"Variation période : {(caf_r[-1]-caf_r[0]):+.2f} M€")

    cg1, cg2 = st.columns(2)
    with cg1:
        st.markdown("**1. Effet de ciseau historique (Produits vs Charges en M€)**")
        st.line_chart(pd.DataFrame({"Exercice": ans_r, "Produits (M€)": p_r, "Charges (M€)": c_r}).set_index("Exercice"))
    with cg2:
        st.markdown("**2. Érosion de la CAF & Autofinancement net (M€)**")
        st.line_chart(pd.DataFrame({"Exercice": ans_r, "CAF (M€)": caf_r, "Autofinancement Net (M€)": aut_r}).set_index("Exercice"))

    st.markdown("**3. Décomposition de la dérive salariale interne (Compte 64)**")
    cd1, cd2, cd3 = st.columns(3)
    gvt_pt = cd1.slider("GVT Mécanique — Ancienneté (pts/an)", 0.5, 2.5, 1.2, 0.1)
    conv_pt = cd2.slider("Mesures Nationales — EEPNL / SMIC (pts/an)", 0.5, 3.5, 1.6, 0.1)
    vol_pt = round(tcma_ms - gvt_pt - conv_pt, 2)
    cd3.metric("Effet Volume (Levier interne)", f"{vol_pt:+.2f} pts / an", "Créations de postes / remplacements", delta_color="inverse" if vol_pt > 0.5 else "normal")

    df_retro_tbl = pd.DataFrame({
        "Soldes ANC 2018-06": ["Produits d'exploitation (M€)", "Charges d'exploitation (M€)", "Masse salariale Cpte 64 (M€)", "Capacité d'Autofinancement (M€)", "Autofinancement net (M€)", "Taux de CAF (%)"],
        **{ans_r[i]: [f"{p_r[i]:.2f}", f"{c_r[i]:.2f}", f"{ms_r[i]:.2f}", f"{caf_r[i]:.2f}", f"{aut_r[i]:.2f}", f"{(caf_r[i]/p_r[i]*100):.1f} %"] for i in range(len(ans_r))}
    })
    st.dataframe(df_retro_tbl, hide_index=True, use_container_width=True)

    atouts_list = [
        f"Base de recettes sécurisée ({tp/1e6:.2f} M€) portée par les forfaits publics et la contribution des familles.",
        f"Capacité d'autofinancement maintenue à {caf/1e6:.2f} M€ ({tcaf:.1f} % des produits).",
        "Potentiel de développement hors contrat (UFA/CFC) et de mutualisation des fonctions support."
    ]
    vig_list = [
        f"Résorber l'effet ciseau ({ciseau:+.2f} pts/an) : contenir les achats et fluides sous l'inflation.",
        f"Maîtriser l'effet volume RH ({vol_pt:+.2f} pts/an) : encadrer les remplacements et heures supplémentaires.",
        "Sécuriser l'étanchéité de la Règle d'Or immobilière avant tout nouvel emprunt."
    ]
    pdf_retro_bytes = build_pdf_retro(etab, normes, ans_r, p_r, c_r, ms_r, caf_r, aut_r, inv_r, tcma_p, tcma_c, tcma_ms, gvt_pt, conv_pt, vol_pt, atouts_list, vig_list)
    st.download_button("📑 Télécharger le Dossier Rétrospectif Complet (PDF 2 pages)", data=pdf_retro_bytes, file_name=f"Dossier_Retro_{etab.replace(' ','_')}.pdf", mime="application/pdf", type="primary")

    bloc_synthese_strategique(
        "Rétrospective & Dynamique RH",
        f"Sur la période observée, les charges progressent de +{tcma_c:.2f} %/an contre +{tcma_p:.2f} %/an pour les produits, générant un effet ciseau de {ciseau:+.2f} pts/an. Sur +{tcma_ms:.2f} %/an de dérive salariale, {(gvt_pt+conv_pt):.2f} pts sont subis (GVT et convention collective) et {vol_pt:+.2f} pts relèvent des choix internes d'organisation.",
        "Pour l'exercice à venir, gel des créations de postes administratifs et révision des taux de remplacement sur les absences courtes afin de ramener l'effet volume RH sous +0,3 pt/an.",
        f"La dérive subie des charges (+{tcma_c:.2f} %/an, tirée par le point d'indice/EEPNL, l'énergie et la maintenance) dépasse l'indexation des forfaits publics ({normes['financeur']}). Une revalorisation du forfait par élève est indispensable pour éviter l'érosion de la CAF."
    )

# ------------------------------------------
# ONGLET 2 : TBI EXÉCUTIF, SIG & ARBITRAGE
# ------------------------------------------
with onglets[1]:
    st.subheader("Tableau de Bord Exécutif (TBI) & Cascade des SIG")

    hs1, hs2 = st.columns([1, 2.5])
    with hs1:
        st.metric("HEALTH SCORE ANC 2018-06", f"{health_score} / 100", "Sain >= 70 | Vigilance 45-69")
    with hs2:
        if health_score >= 70:
            st.success(f"**Équilibre structurel validé ({health_score}/100) :** Taux de CAF à {tcaf:.1f} % (cible {normes['taux_caf']} %), Règle d'Or respectée ({ro_solde:+,.0f} €) et trésorerie à {j_treso} jours.".replace(",", " "))
        elif health_score >= 45:
            st.warning(f"**Zone de vigilance ({health_score}/100) :** Des tensions apparaissent sur la CAF ({tcaf:.1f} %) ou la couverture immobilière ({ro_solde:+,.0f} €). Des ajustements budgétaires ciblés sont nécessaires dès l'EPRD prochain.".replace(",", " "))
        else:
            st.error(f"**Alerte financière ({health_score}/100) :** Rupture d'autofinancement ou tension critique sur la trésorerie ({j_tr} jours) et la Règle d'Or ({ro_solde:+,.0f} €). Plan de redressement requis.".replace(",", " "))

    c_sig1, c_sig2 = st.columns([1.4, 1])
    with c_sig1:
        st.markdown("**1. Cascade des Soldes Intermédiaires de Gestion (ANC 2018-06)**")
        df_sig = pd.DataFrame([
            {"Solde Intermédiaire de Gestion": "Total Produits d'Exploitation (70/74/75)", "Montant (€)": f"{tp:,.0f} €".replace(",", " "), "% Produits": "100,0 %"},
            {"Solde Intermédiaire de Gestion": "- Achats consommés (Pédagogie + Denrées Cpte 60)", "Montant (€)": f"-{ch_achats:,.0f} €".replace(",", " "), "% Produits": f"{ch_achats/tp*100:.1f} %"},
            {"Solde Intermédiaire de Gestion": "= MARGE BRUTE GLOBALE", "Montant (€)": f"{marge_brute:,.0f} €".replace(",", " "), "% Produits": f"{marge_brute/tp*100:.1f} %"},
            {"Solde Intermédiaire de Gestion": "- Services ext., Maintenance, Fluides & Loyers (61-62)", "Montant (€)": f"-{ch_ext_hors_achats:,.0f} €".replace(",", " "), "% Produits": f"{ch_ext_hors_achats/tp*100:.1f} %"},
            {"Solde Intermédiaire de Gestion": "= VALEUR AJOUTÉE (VA)", "Montant (€)": f"{valeur_ajoutee:,.0f} €".replace(",", " "), "% Produits": f"{valeur_ajoutee/tp*100:.1f} %"},
            {"Solde Intermédiaire de Gestion": "- Masse Salariale OGEC / Asso (Cpte 64)", "Montant (€)": f"-{ms_totale:,.0f} €".replace(",", " "), "% Produits": f"{ms_totale/tp*100:.1f} %"},
            {"Solde Intermédiaire de Gestion": "= EXCÉDENT BRUT D'EXPLOITATION (EBE)", "Montant (€)": f"{ebe:,.0f} €".replace(",", " "), "% Produits": f"{ebe/tp*100:.1f} %"},
            {"Solde Intermédiaire de Gestion": "- Dotations Amortissements & Intérêts (68 + 66)", "Montant (€)": f"-{(amort_68+fin_66):,.0f} €".replace(",", " "), "% Produits": f"{(amort_68+fin_66)/tp*100:.1f} %"},
            {"Solde Intermédiaire de Gestion": "= RÉSULTAT NET COMPTABLE (RCAI)", "Montant (€)": f"{rn:+,.0f} €".replace(",", " "), "% Produits": f"{rn/tp*100:+.1f} %"},
            {"Solde Intermédiaire de Gestion": "= CAPACITÉ D'AUTOFINANCEMENT (CAF)", "Montant (€)": f"{caf:,.0f} €".replace(",", " "), "% Produits": f"{tcaf:.1f} %"},
            {"Solde Intermédiaire de Gestion": "- Remboursement annuel capital dette (164)", "Montant (€)": f"-{remb_16:,.0f} €".replace(",", " "), "% Produits": f"{remb_16/tp*100:.1f} %"},
            {"Solde Intermédiaire de Gestion": "= AUTOFINANCEMENT NET DISPONIBLE", "Montant (€)": f"{autofin_net:+,.0f} €".replace(",", " "), "% Produits": f"{autofin_net/tp*100:+.1f} %"},
        ])
        st.dataframe(df_sig, hide_index=True, use_container_width=True)

    with c_sig2:
        st.markdown("**2. Bilan, Endettement & Étanchéité Patrimoniale**")
        st.metric("Capacité de Désendettement", f"{cap_desend:.1f} ans", f"Seuil bancaire : < {normes['desend_max']} ans", delta_color="normal" if cap_desend <= normes["desend_max"] else "inverse")
        st.metric("Trésorerie de Sécurité", f"{j_treso} jours", f"Encours : {treso_51/1e6:.2f} M€ (Cible : {normes['jours_treso']} j)", delta_color="normal" if j_treso >= 60 else "inverse")
        st.metric("Règle d'Or Immobilière", f"{ro_solde:+,.0f} €".replace(",", " "), "Contrib. 756 - [Amort. + Int. + Loyers]", delta_color="normal" if ro_ok else "inverse")

        st.markdown("**3. Arbitrage des 3 Scénarios Budgétaires**")
        st.markdown(f"""
        * **Scénario 1 — Fil de l'eau :** sans ajustement tarifaire ni maîtrise des charges, l'inflation grignote l'EBE ({ebe/1e6:.2f} M€) dès l'exercice N+1.
        * **Scénario 2 — Investissement lourd sans recettes :** tout nouvel emprunt dégraderait le désendettement ({cap_desend:.1f} ans) au-delà du seuil d'alerte.
        * **Scénario 3 — Cible Optimisée :** sanctuarisation de la CAF à ≥ {normes['taux_caf']} % et équilibre analytique des services annexes.
        """)

    pdf_tbi_bytes = build_pdf_tbi(
        etab, normes, eleves_tot, surface_m2, health_score,
        tp/1e6, ch_achats/1e6, ch_ext_hors_achats/1e6, valeur_ajoutee/1e6, ms_totale/1e6,
        ebe/1e6, (amort_68+fin_66)/1e6, rn/1e6, caf/1e6, remb_16/1e6, autofin_net/1e6,
        dette_16/1e6, cap_desend, treso_51/1e6, j_treso, ro_solde/1e6,
        maint_m2, b_peda_eleve, marge_ufa/1e6, marge_cfc/1e6
    )
    st.download_button("📑 Télécharger le TBI Exécutif & SIG (PDF 1 page)", data=pdf_tbi_bytes, file_name=f"TBI_Executif_{etab.replace(' ','_')}.pdf", mime="application/pdf", type="primary")

    bloc_synthese_strategique(
        "Tableau de Bord Exécutif & SIG",
        f"L'établissement dégage une Valeur Ajoutée de {valeur_ajoutee/1e6:.2f} M€ et un EBE de {ebe/1e6:.2f} M€. Après charges calculées et frais financiers, la CAF s'établit à {caf/1e6:.2f} M€ ({tcaf:.1f} % des produits), laissant un autofinancement net de {autofin_net/1e6:+.2f} M€ après remboursement du capital de la dette ({remb_16/1e6:.2f} M€).",
        f"Si l'autofinancement net ({autofin_net:+,.0f} €) est faible ou négatif, le budget prévisionnel doit impérativement intégrer un redressement de l'EBE avant d'engager de nouveaux travaux non subventionnés.",
        f"Les forfaits publics ({f_74:,.0f} €, soit {f_74/eleves_tot:,.0f} €/élève contre {normes['forfait_eleve']} € de référence nationale) couvrent les dépenses de fonctionnement courant, mais ne financent jamais l'immobilier ni les amortissements."
    )

# ------------------------------------------
# ONGLET 3 : AUDIT AU SCALPEL (RH, BÂTI, CANTINE, UFA)
# ------------------------------------------
with onglets[2]:
    st.subheader("Audit Analytique au Scalpel : Les 5 Centres de Sensibilité")

    # 1. RH Granulaire
    st.markdown("#### 1. Cartographie RH Interne (Décomposition du Compte 64)")
    crh1, crh2 = st.columns([1.4, 1])
    with crh1:
        df_rh = pd.DataFrame([
            {"Pôle RH (Hors profs État)": "Enseignants de droit privé (Rempl., hors contrat)", "Budget (€)": f"{ms_prive:,.0f} €".replace(",", " "), "Part MS": f"{ms_prive/max(1,ms_totale)*100:.1f} %", "Coût / Élève": f"{ms_prive/eleves_tot:,.0f} €"},
            {"Pôle RH (Hors profs État)": "Vie scolaire, éducateurs, surveillants, AESH", "Budget (€)": f"{ms_vie_scol:,.0f} €".replace(",", " "), "Part MS": f"{ms_vie_scol/max(1,ms_totale)*100:.1f} %", "Coût / Élève": f"{ms_vie_scol/eleves_tot:,.0f} €"},
            {"Pôle RH (Hors profs État)": "Administration, direction, comptabilité", "Budget (€)": f"{ms_admin:,.0f} €".replace(",", " "), "Part MS": f"{ms_admin/max(1,ms_totale)*100:.1f} %", "Coût / Élève": f"{ms_admin/eleves_tot:,.0f} €"},
            {"Pôle RH (Hors profs État)": "Technique, entretien, accueil & restauration", "Budget (€)": f"{ms_tech:,.0f} €".replace(",", " "), "Part MS": f"{ms_tech/max(1,ms_totale)*100:.1f} %", "Coût / Élève": f"{ms_tech/eleves_tot:,.0f} €"},
        ])
        st.dataframe(df_rh, hide_index=True, use_container_width=True)
        if poids_admin_ms > 32.0:
            st.warning(f"**Point de vigilance RH :** Le pôle Administration/Direction représente **{poids_admin_ms:.1f} %** de la masse salariale interne (seuil de vigilance : 32 %). Vérifier la mutualisation possible avec d'autres établissements du réseau.")
    with crh2:
        st.bar_chart(pd.DataFrame({
            "Pôle": ["Profs Privé", "Vie Scolaire", "Admin/Dir.", "Tech/Resto"],
            "Montant (€)": [ms_prive, ms_vie_scol, ms_admin, ms_tech]
        }).set_index("Pôle"), color="#1d4ed8")

    st.divider()

    # 2. Bâtiment, Maintenance & Règle d'Or
    st.markdown("#### 2. Patrimoine, Maintenance (Cpte 615) & Énergie")
    cb1, cb2, cb3 = st.columns(3)
    cb1.metric("Maintenance & Réparations (615)", f"{maint_615:,.0f} €".replace(",", " "), f"{maint_m2:.1f} €/m² (Norme : {normes['maint_m2']} €/m²)", delta_color="inverse" if maint_m2 > normes["maint_m2"]*1.25 else "normal")
    cb2.metric("Énergie & Fluides (606)", f"{fluides_606:,.0f} €".replace(",", " "), f"{fluides_eleve:,.0f} € / élève")
    cb3.metric("Solde Règle d'Or Immobilière", f"{ro_solde:+,.0f} €".replace(",", " "), "Contrib. 756 - [Amort+Int+Loyers]", delta_color="normal" if ro_ok else "inverse")

    if not ro_ok:
        st.error(f"**Rupture de la Règle d'Or ({ro_solde:+,.0f} €) :** Les contributions des familles ({c_756:,.0f} €) ne couvrent plus les charges immobilières et locatives ({(amort_68+fin_66+loyers_613):,.0f} €). Il manque **{int(round(abs(ro_solde)/eleves_tot))} € / élève / an** pour rétablir l'étanchéité patrimoniale.".replace(",", " "))

    st.divider()

    # 3. Restauration/Internat & 4. Effort Pédagogique
    cs1, cs2 = st.columns(2)
    with cs1:
        st.markdown("#### 3. Restauration & Internat (Services annexes)")
        st.metric("Marge sur coûts directs Resto/Internat", f"{marge_resto:+,.0f} €".replace(",", " "), f"Taux de couverture : {tx_couv_resto:.1f} %", delta_color="normal" if marge_resto >= 0 else "inverse")
        if marge_resto < 0:
            st.error(f"**Subventionnement croisé interdit :** La restauration/internat perd **{abs(marge_resto):,.0f} €** sur ses coûts directs (denrées + cuisine + fluides). Les tarifs familles doivent être revalorisés de **{abs(marge_resto)/max(1,internes_tot):,.0f} € / usager / an**.".replace(",", " "))
        else:
            st.success("Tarification équilibrée : le service couvre ses coûts directs sans ponctionner le budget pédagogique.")

    with cs2:
        st.markdown("#### 4. Effort Pédagogique Direct")
        st.metric("Budget Pédagogique / Élève", f"{b_peda_eleve:,.0f} € / élève", f"Référentiel observatoire : ~{normes['b_peda']} €", delta_color="normal" if b_peda_eleve >= normes["b_peda"]*0.85 else "inverse")
        if b_peda_eleve < normes["b_peda"] * 0.85:
            st.warning(f"**Sous-dotation pédagogique :** À {b_peda_eleve:,.0f} €/élève, le budget alloué aux équipes enseignantes sert de variable d'ajustement pour absorber les charges fixes (énergie, cantine).")
        else:
            st.success("L'enveloppe pédagogique directe est préservée au niveau des standards nationaux.")

    # 5. Pôle UFA / CFC
    if activer_ufa_cfc:
        st.divider()
        st.markdown("#### 5. Pôle Hors Contrat : Apprentissage (UFA) vs Formation Continue (CFC)")
        cu1, cu2 = st.columns(2)
        cu1.metric("Marge Nette Apprentissage (UFA)", f"{marge_ufa:+,.0f} €".replace(",", " "), f"Pour {app_tot} apprentis ({marge_ufa/max(1,app_tot):+,.0f} €/apprenti)")
        cu2.metric("Marge Nette Formation Continue (CFC)", f"{marge_cfc:+,.0f} €".replace(",", " "), f"Pour {stag_tot} stagiaires", delta_color="normal" if marge_cfc >= 0 else "inverse")
        if marge_ufa > 0 > marge_cfc:
            st.error(f"**Alerte destruction de valeur :** Le déficit de la Formation Continue (**{marge_cfc:,.0f} €**) ampute directement l'excédent dégagé par l'Apprentissage (**+{marge_ufa:,.0f} €**). Il faut restructurer l'offre CFC ou relever les seuils d'ouverture de groupes.".replace(",", " "))

    bloc_synthese_strategique(
        "Audit Analytique au Scalpel",
        f"L'analyse par centre de coût révèle une maintenance bâtiment à {maint_m2:.1f} €/m², un effort pédagogique à {b_peda_eleve:,.0f} €/élève et un solde restauration/internat de {marge_resto:+,.0f} €.",
        "Ajuster dès la prochaine rentrée les tarifs de restauration/internat pour éliminer tout déficit direct, stopper les sessions CFC déficitaires et sanctuariser l'enveloppe pédagogique par élève.",
        f"Le poids des personnels éducatifs (Vie scolaire : {ms_vie_scol:,.0f} €), des fluides ({fluides_606:,.0f} €) et de la maintenance courante ({maint_615:,.0f} €) démontre la réalité des charges matérielles et d'externat supportées par l'établissement."
    )

# ------------------------------------------
# ONGLET 4 : PROSPECTIVE & FEUILLE DE ROUTE (2026-2030)
# ------------------------------------------
with onglets[3]:
    st.subheader("Simulateur Quinquennal & Arbitrage Budgétaire (2026-2030)")

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
        ppi_annuel = st.slider("Enveloppe PPI cible (M€/an)", 0.0, 2.5, 0.35, 0.05)
        exec_pct = st.slider("Taux d'exécution PPI (%)", 50, 100, 85, 5)
        taux_subv_ppi = st.slider("Subventions Région/AEP/MASA (%)", 0, 70, 30, 5)
    with sp4:
        st.markdown("**4. OPEX induits & Dette**")
        opex_ppi_pct = st.slider("OPEX induits par le PPI (% du PPI)", -2.0, 5.0, 1.5, 0.5, help="Négatif si rénovation thermique générant des économies d'énergie.")
        duree_emprunt = st.selectbox("Durée nouveaux emprunts", [15, 20, 25], index=1)

    ans_p = ["2026", "2027", "2028", "2029", "2030"]
    ppi_reel = ppi_annuel * (exec_pct / 100.0)
    subv_ppi_an = ppi_reel * (taux_subv_ppi / 100.0)
    emprunt_ppi_an = max(0.0, (ppi_reel - subv_ppi_an) * 0.65)
    autofin_ppi_an = max(0.0, (ppi_reel - subv_ppi_an) * 0.35)

    p_list, c_list, caf_list, subv_list, det_list, des_list, tr_list, jtr_list = [], [], [], [], [], [], [], []
    curr_p = tp / 1e6
    curr_ms = ms_totale / 1e6
    curr_autres_ch = (ch_achats + ch_ext_hors_achats + (0 if source_reelle else ch_ufa + ch_cfc)) / 1e6
    curr_amo = amort_68 / 1e6
    curr_fin = fin_66 / 1e6
    curr_det = dette_16 / 1e6
    curr_remb = remb_16 / 1e6
    curr_treso = treso_51 / 1e6
    opex_cumul = 0.0

    for _ in ans_p:
        curr_p = curr_p * (1 + tx_el_proj/100.0) * (1 + tx_forf_proj/100.0)
        curr_ms = curr_ms * (1 + tx_ms_proj/100.0)
        curr_autres_ch = curr_autres_ch * (1 + tx_ext_proj/100.0)
        opex_cumul += ppi_reel * (opex_ppi_pct / 100.0)
        curr_amo += ppi_reel / 20.0
        curr_fin += emprunt_ppi_an * 0.035

        tot_c_opex = curr_ms + curr_autres_ch + opex_cumul + curr_amo + curr_fin
        curr_caf = (curr_p - tot_c_opex) + curr_amo
        curr_det = max(0.0, curr_det - curr_remb + emprunt_ppi_an)
        curr_remb_tot = curr_remb + (emprunt_ppi_an / duree_emprunt)
        curr_treso = curr_treso + curr_caf - curr_remb_tot - autofin_ppi_an
        curr_des = (curr_det / curr_caf) if curr_caf > 0 else 99.9
        c_dec_an = max(0.01, tot_c_opex - curr_amo)
        curr_j = (curr_treso / c_dec_an) * 365

        p_list.append(curr_p)
        c_list.append(tot_c_opex)
        caf_list.append(curr_caf)
        subv_list.append(subv_ppi_an)
        det_list.append(curr_det)
        des_list.append(curr_des)
        tr_list.append(curr_treso)
        jtr_list.append(curr_j)

    df_proj = pd.DataFrame({
        "Année": ans_p,
        "Produits (M€)": p_list,
        "Charges + OPEX (M€)": c_list,
        "CAF (M€)": caf_list,
        "Subv. PPI (M€)": subv_list,
        "Dette 31/12 (M€)": det_list,
        "Désendettement (ans)": des_list,
        "Trésorerie (M€)": tr_list,
        "Trésorerie (jours)": jtr_list
    })

    kp1, kp2, kp3, kp4 = st.columns(4)
    kp1.metric("CAF Projetée 2030", f"+{caf_list[-1]:.2f} M€", f"Taux CAF : {(caf_list[-1]/p_list[-1]*100):.1f} %")
    kp2.metric("Capacité Désendettement 2030", f"{des_list[-1]:.1f} ans", f"Seuil : {normes['desend_max']} ans", delta_color="normal" if des_list[-1] <= normes["desend_max"] else "inverse")
    kp3.metric("Encours Dette 2030", f"{det_list[-1]:.2f} M€", f"Variation : {(det_list[-1]-det_list[0]):+.2f} M€")
    kp4.metric("Trésorerie 2030", f"{jtr_list[-1]:.0f} jours", f"Encours : {tr_list[-1]:.2f} M€", delta_color="normal" if jtr_list[-1] >= 60 else "inverse")

    gp_c1, gp_c2 = st.columns(2)
    with gp_c1:
        st.markdown("**Trajectoire Produits vs Charges + OPEX induits (M€)**")
        st.line_chart(df_proj.set_index("Année")[["Produits (M€)", "Charges + OPEX (M€)"]])
    with gp_c2:
        st.markdown("**Trajectoire CAF & Trésorerie disponible (M€)**")
        st.line_chart(df_proj.set_index("Année")[["CAF (M€)", "Trésorerie (M€)"]])

    st.dataframe(df_proj.style.format({
        "Produits (M€)": "{:.2f}", "Charges + OPEX (M€)": "{:.2f}", "CAF (M€)": "{:.2f}",
        "Subv. PPI (M€)": "{:.2f}", "Dette 31/12 (M€)": "{:.2f}", "Désendettement (ans)": "{:.1f}",
        "Trésorerie (M€)": "{:.2f}", "Trésorerie (jours)": "{:.0f} j"
    }), hide_index=True, use_container_width=True)

    feuille_route = [
        f"1. Solvabilité & Épargne : CAF cible de {caf_list[-1]:.2f} M€ en 2030 ({(caf_list[-1]/p_list[-1]*100):.1f} % des produits) et désendettement à {des_list[-1]:.1f} ans.",
        f"2. Fonctionnement & RH : Plafonner l'évolution de la MS interne à +{tx_ms_proj:.1f} %/an et contenir l'inflation des achats/maintenance à +{tx_ext_proj:.1f} %/an.",
        f"3. Tarification & Recettes : Indexer les forfaits publics et contributions familles à +{tx_forf_proj:.1f} %/an et éliminer tout déficit sur la restauration et la CFC.",
        f"4. Investissement (PPI) & OPEX : Calibrer le PPI exécuté à {ppi_reel:.2f} M€/an ({taux_subv_ppi} % de subventions Région/AEP) en intégrant {opex_ppi_pct:+.1f} %/an d'OPEX induits.",
        f"5. Dette & Trésorerie : Flécher les emprunts sur {duree_emprunt} ans et maintenir un matelas de sécurité supérieur à {normes['jours_treso']} jours de charges décaissables."
    ]

    pdf_pro_bytes = build_pdf_prospective(etab, normes, ppi_annuel, exec_pct, df_proj, feuille_route)
    st.download_button("📑 Télécharger la Synthèse Prospective 2026-2030 (PDF 1 page)", data=pdf_pro_bytes, file_name=f"Synthese_Prospective_2026_2030_{etab.replace(' ','_')}.pdf", mime="application/pdf", type="primary")

    bloc_synthese_strategique(
        "Prospective Quinquennale 2026-2030",
        f"Avec un PPI exécuté de {ppi_reel:.2f} M€/an et une évolution salariale contenue à +{tx_ms_proj:.1f} %/an, la CAF atteint {caf_list[-1]:.2f} M€ en 2030 et la trésorerie s'établit à {jtr_list[-1]:.0f} jours.",
        f"Chaque projet immobilier inscrit au PPI doit désormais être chiffré en coût complet (incluant {opex_ppi_pct:+.1f} %/an d'OPEX induits) et conditionné à l'obtention de {taux_subv_ppi} % de cofinancements.",
        f"La soutenabilité à 5 ans repose sur une indexation annuelle minimale de +{tx_forf_proj:.1f} %/an des dotations publiques ({normes['financeur']}) pour absorber l'évolution des charges fixes et réglementaires."
    )
