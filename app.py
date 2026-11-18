<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Archétype Satellites | Démonstration Interactive</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @media print {
            .no-print { display: none !important; }
            body { background: white; -webkit-print-color-adjust: exact; print-color-adjust: exact; margin: 0; padding: 0; }
            .print-container { padding: 0; margin: 0; box-shadow: none; border: none; width: 100%; max-width: 100%; }
        }
    </style>
</head>
<body class="bg-slate-100 font-sans text-slate-800 p-3 md:p-6">

<div class="max-w-6xl mx-auto">
    
    <!-- En-tête Principal & Badge Démonstration -->
    <div class="bg-slate-900 text-white p-5 rounded-t-xl shadow-lg flex flex-col md:flex-row justify-between items-center no-print">
        <div>
            <div class="text-[10px] uppercase font-bold tracking-widest text-blue-400">Direction Générale & Finances</div>
            <h1 class="text-xl md:text-2xl font-black tracking-tight">ARCHÉTYPE SATELLITES</h1>
            <p class="text-xs text-slate-400 mt-0.5">Plateforme Sécurisée d'Arbitrage des SEM, SPL, DSP & Tiers</p>
        </div>
        <div class="mt-3 md:mt-0 flex items-center gap-3">
            <span class="bg-amber-500/20 border border-amber-400/50 text-amber-300 text-[11px] font-black uppercase tracking-wider px-3 py-1.5 rounded-lg">
                Mode Démonstration
            </span>
        </div>
    </div>

    <!-- BANDEAU D'INFORMATION DÉMONSTRATION -->
    <div class="bg-amber-50 px-5 py-3 border-x border-b border-amber-300 no-print flex flex-col sm:flex-row justify-between items-center gap-2 text-xs text-amber-950">
        <div>
            <span class="font-black uppercase">Environnement de test interactif :</span>
            <span>manipulez librement les ratios financiers, juridiques et de gouvernance sur les trois cas fictifs préchargés.</span>
        </div>
        <button onclick="loadCaseTemplate()" class="shrink-0 bg-amber-800 hover:bg-amber-900 text-white font-bold py-1 px-3 rounded text-[11px] transition">
            Réinitialiser le cas
        </button>
    </div>

    <!-- ESPACE DE TRAVAIL DE L'AUDIT (OUVERT EN MODE DÉMO) -->
    <div id="workspace-section" class="bg-white p-6 md:p-8 rounded-b-xl shadow-lg no-print space-y-8">
        
        <!-- BARRE DE STATUT DÉMO -->
        <div class="bg-slate-900 text-white p-4 rounded-xl flex flex-col md:flex-row justify-between items-center gap-4">
            <div class="flex items-center gap-3 w-full md:w-auto">
                <span class="text-xl">📁</span>
                <div>
                    <div class="text-xs font-bold text-blue-300 uppercase">Dossier de démonstration actif :</div>
                    <div id="current-dossier-label" class="text-sm font-black text-white">SEM Adour Mobilité Rurale (Cas fictif)</div>
                </div>
            </div>
            
            <div class="flex flex-wrap items-center gap-2 w-full md:w-auto justify-end">
                <button onclick="demoRestrictedNotice()" class="bg-slate-800 hover:bg-slate-700 text-slate-400 font-bold py-2 px-4 rounded text-xs flex items-center gap-1.5 border border-slate-700 cursor-not-allowed">
                    <span>🔒</span> Sauvegarde Cloud (Version complète)
                </button>
                <button onclick="loadCaseTemplate()" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-3 rounded text-xs shadow">
                    ↻ Valeurs d'origine
                </button>
            </div>
        </div>

        <div id="input-section">
        <!-- ÉTAPE 0 : PARAMÉTRAGE DU DOSSIER & SECTEUR D'ACTIVITÉ -->
        <div class="bg-blue-50/70 p-5 rounded-xl border border-blue-200 space-y-4 mb-8">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h2 class="text-sm font-bold text-blue-950 uppercase tracking-wide">Étape 0 : Choix du Cas Fictif & Typologie Sectorielle</h2>
                    <p class="text-xs text-blue-700">Sélectionnez l'un des trois scénarios préchargés. Le secteur calibre automatiquement les seuils d'alerte.</p>
                </div>
                <div class="w-full md:w-80">
                    <select id="case-selector" onchange="loadCaseTemplate()" class="w-full border-2 border-blue-300 bg-white p-2 text-xs rounded-lg font-bold text-blue-900 outline-none">
                        <option value="adour">Cas Démo 1 : SEM Adour Mobilité Rurale (Transport)</option>
                        <option value="amenagement">Cas Démo 2 : SPL Grand Sud Aménagement (Foncier)</option>
                        <option value="esms">Cas Démo 3 : ESMS Le Bois Fleuri (Médico-social M22)</option>
                    </select>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
                <div>
                    <label class="block font-semibold mb-1 text-slate-700">Structure auditée (verrouillé)</label>
                    <input type="text" id="cfg-entity" readonly title="Intitulé verrouillé en mode démonstration" class="w-full border border-slate-300 p-2 rounded bg-slate-100 text-slate-600 font-medium cursor-not-allowed" value="SEM Adour Mobilité Rurale">
                </div>
                <div>
                    <label class="block font-semibold mb-1 text-slate-700">Collectivité / Tutrice (verrouillé)</label>
                    <input type="text" id="cfg-authority" readonly title="Intitulé verrouillé en mode démonstration" class="w-full border border-slate-300 p-2 rounded bg-slate-100 text-slate-600 font-medium cursor-not-allowed" value="Conseil Départemental des Landes">
                </div>
                <div>
                    <label class="block font-semibold mb-1 text-slate-700">Instance délibérante (verrouillé)</label>
                    <input type="text" id="cfg-instance" readonly title="Intitulé verrouillé en mode démonstration" class="w-full border border-slate-300 p-2 rounded bg-slate-100 text-slate-600 font-medium cursor-not-allowed" value="Commission Permanente (Séance DM2)">
                </div>
                <div>
                    <label class="block font-semibold mb-1 text-blue-900 font-bold">Référentiel Sectoriel</label>
                    <select id="cfg-sector" onchange="computeFinances()" class="w-full border-2 border-blue-200 p-2 rounded bg-white font-bold text-blue-950">
                        <option value="transport" selected>Transport Public & DSP (SEM/SPL)</option>
                        <option value="amenagement">Aménagement & Logement (SEM/SPL)</option>
                        <option value="medicosocial">Médico-social & Santé (M22 / CPOM)</option>
                        <option value="general">Association / Entreprise Générale</option>
                    </select>
                </div>
            </div>

            <!-- Interrupteurs de modules -->
            <div class="border-t border-blue-200 pt-3">
                <span class="block text-[11px] font-black uppercase text-blue-900 tracking-wider mb-2">Périmètre commandé :</span>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    <label class="flex items-center gap-2 p-2 bg-white rounded border border-blue-200 cursor-pointer font-bold text-slate-700">
                        <input type="checkbox" id="mod-toggle-fin" onchange="toggleModule('fin')" checked class="rounded text-blue-600">
                        <span>Volet 1. Finances & Bilan</span>
                    </label>
                    <label class="flex items-center gap-2 p-2 bg-white rounded border border-blue-200 cursor-pointer font-bold text-slate-700">
                        <input type="checkbox" id="mod-toggle-jur" onchange="toggleModule('jur')" checked class="rounded text-blue-600">
                        <span>Volet 2. Légalité & Risques</span>
                    </label>
                    <label class="flex items-center gap-2 p-2 bg-white rounded border border-blue-200 cursor-pointer font-bold text-slate-700">
                        <input type="checkbox" id="mod-toggle-quinze" onchange="toggleModule('quinze')" checked class="rounded text-blue-600">
                        <span>Volet 3. Matrice de Gouvernance</span>
                    </label>
                    <label class="flex items-center gap-2 p-2 bg-white rounded border border-blue-200 cursor-pointer font-bold text-slate-700">
                        <input type="checkbox" id="mod-toggle-other" onchange="toggleModule('other')" checked class="rounded text-blue-600">
                        <span>Volet 4. Fait Majeur</span>
                    </label>
                </div>
            </div>
        </div>

        <!-- COMMUTATEUR : ALERTE ROUGE DÉCLASSANTE -->
        <div class="bg-red-50 p-4 rounded-xl border-2 border-red-300 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
            <div class="flex items-start gap-3">
                <span class="text-2xl">🚨</span>
                <div>
                    <div class="flex items-center gap-2">
                        <h2 class="text-sm font-black text-red-900 uppercase tracking-wide">Alerte Rouge Déclassante (Critère Bloquant)</h2>
                        <span class="text-[10px] bg-red-200 text-red-800 font-bold px-2 py-0.5 rounded uppercase">Déclassement immédiat</span>
                    </div>
                    <p class="text-xs text-red-700 mt-0.5">Activez si un risque pénal, un vice de forme grave ou une cessation de paiements impose un moratoire immédiat.</p>
                </div>
            </div>
            <div class="flex items-center gap-3 w-full md:w-auto justify-end">
                <label class="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" id="red-flag-toggle" onchange="toggleRedFlag()" class="sr-only peer">
                    <div class="w-11 h-6 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                </label>
                <span id="red-flag-status-label" class="text-xs font-black text-slate-500 uppercase">Inactif</span>
            </div>
        </div>

        <div id="red-flag-reason-container" class="hidden text-xs bg-red-100/60 p-3 rounded-lg border border-red-200 mb-8">
            <label class="block font-bold text-red-900 mb-1 uppercase text-[11px]">Motif impératif de l'Alerte Rouge :</label>
            <input type="text" id="red-flag-reason" class="w-full border border-red-300 p-2 rounded bg-white text-red-900 font-semibold" value="Risque de prise illégale d'intérêts et vice de forme sur avenant DSP">
        </div>

        <!-- ZONE DE CALCULS ET FORMULAIRES -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            
            <!-- MODULE 1 : MOTEUR FINANCIER & BILANCIEL -->
            <div id="section-mod-fin" class="bg-slate-50 p-5 rounded-xl border border-slate-200 space-y-4">
                <div class="border-b pb-2 flex justify-between items-end">
                    <div>
                        <h2 class="font-bold text-blue-900 uppercase tracking-wide text-sm border-l-4 border-blue-900 pl-2">
1. Moteur Financier & Bilanciel
                        </h2>
                        <p class="text-xs text-slate-500 mt-0.5">
                            Cliquez sur <button type="button" onclick="showHelp('moteurGlobal')" class="text-blue-600 font-bold hover:underline">ℹ️ Méthode & Normes</button> pour la vue d'ensemble.
                        </p>
                    </div>
                    <span class="text-[11px] text-slate-400 font-mono">Calcul temps réel</span>
                </div>

                <div class="grid grid-cols-2 gap-3 text-xs">
                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <label class="font-semibold">Chiffre d'Affaires HT</label>
                            <button type="button" onclick="showHelp('ca')" class="text-blue-600 hover:text-blue-800 font-bold">ℹ️</button>
                        </div>
                        <input type="number" id="fn-ca" oninput="computeFinances()" class="w-full border p-2 rounded bg-white" value="4200">
                    </div>
                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <label class="font-semibold">CAF annuelle</label>
                            <button type="button" onclick="showHelp('caf')" class="text-blue-600 hover:text-blue-800 font-bold">ℹ️</button>
                        </div>
                        <input type="number" id="fn-caf" oninput="computeFinances()" class="w-full border p-2 rounded bg-white" value="110">
                    </div>
                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <label class="font-semibold">Ressources Durables</label>
                            <button type="button" onclick="showHelp('ressources')" class="text-blue-600 hover:text-blue-800 font-bold">ℹ️</button>
                        </div>
                        <input type="number" id="fn-ressources" oninput="computeFinances()" class="w-full border p-2 rounded bg-white" value="3100">
                    </div>
                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <label class="font-semibold">Emplois Stables</label>
                            <button type="button" onclick="showHelp('emplois')" class="text-blue-600 hover:text-blue-800 font-bold">ℹ️</button>
                        </div>
                        <input type="number" id="fn-emplois" oninput="computeFinances()" class="w-full border p-2 rounded bg-white" value="3220">
                    </div>
                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <label class="font-semibold">Actif Circulant (Créances/Stocks)</label>
                            <button type="button" onclick="showHelp('actifCirc')" class="text-blue-600 hover:text-blue-800 font-bold">ℹ️</button>
                        </div>
                        <input type="number" id="fn-actif-circ" oninput="computeFinances()" class="w-full border p-2 rounded bg-white" value="840">
                    </div>
                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <label class="font-semibold">Passif Circulant (Dettes CT)</label>
                            <button type="button" onclick="showHelp('passifCirc')" class="text-blue-600 hover:text-blue-800 font-bold">ℹ️</button>
                        </div>
                        <input type="number" id="fn-passif-circ" oninput="computeFinances()" class="w-full border p-2 rounded bg-white" value="690">
                    </div>
                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <label class="font-semibold">Dette Financière Brute</label>
                            <button type="button" onclick="showHelp('dette')" class="text-blue-600 hover:text-blue-800 font-bold">ℹ️</button>
                        </div>
                        <input type="number" id="fn-dette" oninput="computeFinances()" class="w-full border p-2 rounded bg-white" value="2800">
                    </div>
                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <label class="font-semibold">Garantie d'Emprunt Publique</label>
                            <button type="button" onclick="showHelp('garantie')" class="text-blue-600 hover:text-blue-800 font-bold">ℹ️</button>
                        </div>
                        <select id="fn-garantie-pct" onchange="computeFinances()" class="w-full border p-2 rounded bg-white font-medium">
                            <option value="0">0 % (Aucune)</option>
                            <option value="50">50 %</option>
                            <option value="80" selected>80 %</option>
                            <option value="100">100 %</option>
                        </select>
                    </div>
                </div>

                <!-- Ratios calculés -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-2 pt-2 text-center text-xs">
                    <div class="bg-white p-2 rounded border">
                        <div class="text-[10px] text-slate-400 font-bold uppercase flex justify-center items-center gap-1">
                            FRNG <button type="button" onclick="showHelp('frng')" class="text-blue-500 font-bold">ℹ️</button>
                        </div>
                        <div id="calc-frng" class="text-sm font-black text-slate-800">--</div>
                    </div>
                    <div class="bg-white p-2 rounded border">
                        <div class="text-[10px] text-slate-400 font-bold uppercase flex justify-center items-center gap-1">
                            BFR <button type="button" onclick="showHelp('bfr')" class="text-blue-500 font-bold">ℹ️</button>
                        </div>
                        <div id="calc-bfr" class="text-sm font-black text-slate-800">--</div>
                    </div>
                    <div class="bg-white p-2 rounded border">
                        <div class="text-[10px] text-slate-400 font-bold uppercase flex justify-center items-center gap-1">
                            Trésorerie <button type="button" onclick="showHelp('treso')" class="text-blue-500 font-bold">ℹ️</button>
                        </div>
                        <div id="calc-treso" class="text-sm font-black text-slate-800">--</div>
                    </div>
                    <div class="bg-white p-2 rounded border">
                        <div class="text-[10px] text-slate-400 font-bold uppercase flex justify-center items-center gap-1">
                            Dette/CAF <button type="button" onclick="showHelp('ratioDette')" class="text-blue-500 font-bold">ℹ️</button>
                        </div>
                        <div id="calc-ratio-dette" class="text-sm font-black text-slate-800">--</div>
                    </div>
                </div>

                <!-- ENCADRÉ DIAGNOSTIC NORMATIF AUTOMATISÉ -->
                <div class="bg-blue-50/80 p-3.5 rounded-lg border border-blue-200 text-xs space-y-2">
                    <div class="flex justify-between items-center border-b border-blue-200 pb-1.5">
                        <span class="font-black text-blue-950 uppercase text-[10px] tracking-wider">Avis Clinique Automatisé vs Normes :</span>
                        <span id="label-sector-norm" class="text-[10px] font-bold text-blue-700 bg-white px-2 py-0.5 rounded border border-blue-200">--</span>
                    </div>
                    <ul id="diagnostic-bullet-points" class="space-y-1.5 text-[11px] leading-snug"></ul>
                </div>
            </div>

            <!-- MODULE 2 : CONTRÔLE DE LÉGALITÉ -->
            <div id="section-mod-jur" class="bg-slate-50 p-5 rounded-xl border border-slate-200 space-y-4">
                <div class="border-b pb-2 flex justify-between items-end">
                    <div>
                        <h2 class="font-bold text-slate-800 uppercase tracking-wide text-sm border-l-4 border-slate-800 pl-2">
2. Contrôle de Légalité & Conformité
                        </h2>
                        <p class="text-xs text-slate-500 mt-0.5">Décochez les piliers non visés par la lettre de mission.</p>
                    </div>
                    <span id="badge-legal-global" class="text-[11px] font-black px-2 py-0.5 rounded uppercase bg-amber-200 text-amber-900">Vigilance</span>
                </div>

                <div class="space-y-3 text-xs">
                    <!-- J1 Commande publique -->
                    <div class="bg-white p-2.5 rounded border space-y-1">
                        <div class="flex justify-between items-center">
                            <label class="flex items-center gap-1.5 font-bold text-slate-800 cursor-pointer">
                                <input type="checkbox" id="jur-toggle-1" onchange="computeLegal()" checked class="rounded text-blue-600">
                                <span>J1. Commande Publique & Avenants</span>
                            </label>
                            <div class="flex items-center gap-2">
                                <button type="button" onclick="showHelp('j1')" class="text-blue-600 hover:text-blue-800 font-bold">ℹ️</button>
                                <select id="jur-j1" onchange="computeLegal()" class="border rounded p-1 text-[11px] font-bold">
                                    <option value="1">Conforme</option>
                                    <option value="0.5">Sous Réserves</option>
                                    <option value="0" selected>Irrégularité</option>
                                </select>
                            </div>
                        </div>
                        <input type="text" id="jur-j1-note" class="w-full border p-1 rounded text-[11px]" value="Avenant n°3 modifiant les tarifs sans base légale solide">
                    </div>

                    <!-- J2 Conventions réglementées -->
                    <div class="bg-white p-2.5 rounded border space-y-1">
                        <div class="flex justify-between items-center">
                            <label class="flex items-center gap-1.5 font-bold text-slate-800 cursor-pointer">
                                <input type="checkbox" id="jur-toggle-2" onchange="computeLegal()" checked class="rounded text-blue-600">
                                <span>J2. Conventions Réglementées (L. 225-38)</span>
                            </label>
                            <div class="flex items-center gap-2">
                                <button type="button" onclick="showHelp('j2')" class="text-blue-600 hover:text-blue-800 font-bold">ℹ️</button>
                                <select id="jur-j2" onchange="computeLegal()" class="border rounded p-1 text-[11px] font-bold">
                                    <option value="1">Conforme</option>
                                    <option value="0.5">Sous Réserves</option>
                                    <option value="0" selected>Irrégularité</option>
                                </select>
                            </div>
                        </div>
                        <input type="text" id="jur-j2-note" class="w-full border p-1 rounded text-[11px]" value="Convention d'appui facturée sans accord préalable du CA">
                    </div>

                    <!-- J3 Probité / Sapin 2 -->
                    <div class="bg-white p-2.5 rounded border space-y-1">
                        <div class="flex justify-between items-center">
                            <label class="flex items-center gap-1.5 font-bold text-slate-800 cursor-pointer">
                                <input type="checkbox" id="jur-toggle-3" onchange="computeLegal()" checked class="rounded text-blue-600">
                                <span>J3. Probité & Loi Sapin 2</span>
                            </label>
                            <div class="flex items-center gap-2">
                                <button type="button" onclick="showHelp('j3')" class="text-blue-600 hover:text-blue-800 font-bold">ℹ️</button>
                                <select id="jur-j3" onchange="computeLegal()" class="border rounded p-1 text-[11px] font-bold">
                                    <option value="1">Conforme</option>
                                    <option value="0.5">Sous Réserves</option>
                                    <option value="0" selected>Irrégularité</option>
                                </select>
                            </div>
                        </div>
                        <input type="text" id="jur-j3-note" class="w-full border p-1 rounded text-[11px]" value="Absence d'enregistrement formel des déports d'élus en CA">
                    </div>

                    <!-- J4 Champ exclusif SPL -->
                    <div class="bg-white p-2.5 rounded border space-y-1">
                        <div class="flex justify-between items-center">
                            <label class="flex items-center gap-1.5 font-bold text-slate-800 cursor-pointer">
                                <input type="checkbox" id="jur-toggle-4" onchange="computeLegal()" checked class="rounded text-blue-600">
                                <span>J4. Périmètre de Compétence (L. 1531-1)</span>
                            </label>
                            <div class="flex items-center gap-2">
                                <button type="button" onclick="showHelp('j4')" class="text-blue-600 hover:text-blue-800 font-bold">ℹ️</button>
                                <select id="jur-j4" onchange="computeLegal()" class="border rounded p-1 text-[11px] font-bold">
                                    <option value="1" selected>Conforme</option>
                                    <option value="0.5">Sous Réserves</option>
                                    <option value="0">Irrégularité</option>
                                </select>
                            </div>
                        </div>
                        <input type="text" id="jur-j4-note" class="w-full border p-1 rounded text-[11px]" value="Actionnariat 100 % public et champ territorial conformes">
                    </div>
                </div>
            </div>
        </div>

        <!-- MODULE 3 : MATRICE DE GOUVERNANCE OBJECTIVÉE -->
        <div id="section-mod-quinze" class="space-y-4 mb-8">
            <div class="border-b pb-2 flex flex-col md:flex-row justify-between items-start md:items-end gap-2">
                <div>
                    <h2 class="font-bold text-slate-900 uppercase tracking-wide text-sm border-l-4 border-slate-900 pl-2">
3. Matrice de Gouvernance & Risques Opérationnels
                    </h2>
                    <p class="text-xs text-slate-500 mt-0.5">Cochez les critères vérifiés sur pièces. Le Health Score est recalculé proportionnellement sur base 100.</p>
                </div>
                <div class="bg-slate-900 text-white px-3 py-1.5 rounded text-xs font-bold flex items-center gap-2">
                    <span>Health Score Renormalisé :</span>
                    <span id="hs-display" class="text-blue-400 text-sm font-black">40</span>
                    <span class="text-slate-400 text-[10px]">/100</span>
                    <span id="hs-diag-label" class="ml-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-red-600 text-white">Vulnérabilité Forte</span>
                </div>
            </div>

            <!-- Grille des 5 dimensions -->
            <div class="grid grid-cols-1 md:grid-cols-5 gap-4 text-xs">
                
                <div id="card-axe-1" class="bg-slate-50 p-3 rounded-lg border border-slate-200 flex flex-col justify-between">
                    <div>
                        <div class="flex justify-between items-center mb-2 pb-1 border-b">
                            <label class="flex items-center gap-1 font-bold text-slate-800 uppercase text-[11px] cursor-pointer">
                                <input type="checkbox" id="axe-toggle-1" onchange="computeHealthScore()" checked class="rounded text-blue-600">
                                <span>1. Gouvernance</span>
                            </label>
                            <span id="score-axe-1" class="font-black text-blue-900">1,25/5</span>
                        </div>
                        <div class="space-y-2">
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-1-1" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Régularité CA/AG (Quorum, PV signés)</span></label>
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-1-2" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Conventions autorisées formellement</span></label>
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-1-3" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Déport effectif des élus au CA</span></label>
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-1-4" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Périmètre statutaire respecté</span></label>
                        </div>
                    </div>
                </div>

                <div id="card-axe-2" class="bg-slate-50 p-3 rounded-lg border border-slate-200 flex flex-col justify-between">
                    <div>
                        <div class="flex justify-between items-center mb-2 pb-1 border-b">
                            <label class="flex items-center gap-1 font-bold text-slate-800 uppercase text-[11px] cursor-pointer">
                                <input type="checkbox" id="axe-toggle-2" onchange="computeHealthScore()" checked class="rounded text-blue-600">
                                <span>2. Modèle Éco</span>
                            </label>
                            <span id="score-axe-2" class="font-black text-blue-900">0,00/5</span>
                        </div>
                        <div class="space-y-2">
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-2-1" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Exploitation équilibrée hors secours</span></label>
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-2-2" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Service dette couvert (DSCR > 1,2)</span></label>
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-2-3" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Dépendance subventions maîtrisée</span></label>
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-2-4" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>BFR d'exploitation sous contrôle</span></label>
                        </div>
                    </div>
                </div>

                <div id="card-axe-3" class="bg-slate-50 p-3 rounded-lg border border-slate-200 flex flex-col justify-between">
                    <div>
                        <div class="flex justify-between items-center mb-2 pb-1 border-b">
                            <label class="flex items-center gap-1 font-bold text-slate-800 uppercase text-[11px] cursor-pointer">
                                <input type="checkbox" id="axe-toggle-3" onchange="computeHealthScore()" checked class="rounded text-blue-600">
                                <span>3. Org. & RH</span>
                            </label>
                            <span id="score-axe-3" class="font-black text-blue-900">1,25/5</span>
                        </div>
                        <div class="space-y-2">
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-3-1" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Vacance structurelle < 5 %</span></label>
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-3-2" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Intérim maîtrisé (< 5 % masse sal.)</span></label>
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-3-3" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Taux d'absentéisme maîtrisé</span></label>
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-3-4" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Organigramme & suppléance actés</span></label>
                        </div>
                    </div>
                </div>

                <div id="card-axe-4" class="bg-slate-50 p-3 rounded-lg border border-slate-200 flex flex-col justify-between">
                    <div>
                        <div class="flex justify-between items-center mb-2 pb-1 border-b">
                            <label class="flex items-center gap-1 font-bold text-slate-800 uppercase text-[11px] cursor-pointer">
                                <input type="checkbox" id="axe-toggle-4" onchange="computeHealthScore()" checked class="rounded text-blue-600">
                                <span>4. Usagers</span>
                            </label>
                            <span id="score-axe-4" class="font-black text-blue-900">3,75/5</span>
                        </div>
                        <div class="space-y-2">
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-4-1" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Volumes réalisés (> 95 %)</span></label>
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-4-2" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Coût unitaire conforme au barème</span></label>
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-4-3" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Satisfaction usagers > 85 %</span></label>
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-4-4" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Faible taux de réclamations</span></label>
                        </div>
                    </div>
                </div>

                <div id="card-axe-5" class="bg-slate-50 p-3 rounded-lg border border-slate-200 flex flex-col justify-between">
                    <div>
                        <div class="flex justify-between items-center mb-2 pb-1 border-b">
                            <label class="flex items-center gap-1 font-bold text-slate-800 uppercase text-[11px] cursor-pointer">
                                <input type="checkbox" id="axe-toggle-5" onchange="computeHealthScore()" checked class="rounded text-blue-600">
                                <span>5. Exécution</span>
                            </label>
                            <span id="score-axe-5" class="font-black text-blue-900">1,25/5</span>
                        </div>
                        <div class="space-y-2">
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-5-1" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Plan d'investissement tenu (CAPEX)</span></label>
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-5-2" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Reporting et délais respectés</span></label>
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-5-3" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Suivi actif des audits antérieurs</span></label>
                            <label class="flex items-start gap-2 cursor-pointer"><input type="checkbox" id="c-5-4" onchange="computeHealthScore()" class="mt-0.5 rounded text-blue-600"><span>Alignement territorial & RSE</span></label>
                        </div>
                    </div>
                </div>

            </div>
        </div>

        <!-- MODULE 4 : CRITÈRE « AUTRE » -->
        <div id="section-mod-other" class="bg-amber-50/70 p-5 rounded-xl border border-amber-200 space-y-3 mb-8">
            <div class="flex justify-between items-center border-b border-amber-200 pb-2">
                <div>
                    <h2 class="font-bold text-amber-950 uppercase tracking-wide text-xs">
4. Fait Majeur ou Signal Faible Spécifique (« Autre »)
                    </h2>
                    <p class="text-[11px] text-amber-800">Sujet non capté par la grille standard (Cyber, crise RH, contrôle fiscal, sinistre).</p>
                </div>
                <div class="flex items-center gap-2">
                    <label class="text-xs font-bold text-amber-900">Niveau :</label>
                    <select id="other-impact" onchange="handleOtherImpact()" class="border border-amber-300 rounded p-1 text-xs font-bold bg-white text-amber-900">
                        <option value="none">Aucun fait majeur</option>
                        <option value="minor">Mineur (À surveiller)</option>
                        <option value="major">Majeur (Dégradation opérationnelle)</option>
                        <option value="blocking" selected>Bloquant (Active l'Alerte Rouge)</option>
                    </select>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                <div>
                    <label class="block font-semibold mb-1 text-slate-700">Intitulé de l'événement</label>
                    <input type="text" id="other-title" class="w-full border p-2 rounded bg-white" value="Crise managériale aiguë et vacance de la direction générale">
                </div>
                <div class="md:col-span-2">
                    <label class="block font-semibold mb-1 text-slate-700">Conséquences prévisibles pour la collectivité</label>
                    <input type="text" id="other-desc" class="w-full border p-2 rounded bg-white" value="Absence de pilotage exécutif depuis 4 mois et retards critiques dans la facturation des usagers">
                </div>
            </div>
        </div>

        <!-- ÉTAPE 5 : DÉCISION D'ARBITRAGE -->
        <div class="bg-slate-50 p-5 rounded-xl border border-slate-200 space-y-4 mb-8">
            <div class="border-b pb-2">
                <h2 class="font-bold text-slate-900 uppercase tracking-wide text-sm border-l-4 border-blue-600 pl-2">
5. Décision d'Arbitrage & Préconisations Soumises au Vote
                </h2>
                <p class="text-xs text-slate-500 mt-0.5">Formulez la décision motivée et opposable que l'Assemblée délibérante doit acter.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
                <div>
                    <label class="block font-semibold mb-1">Option d'arbitrage</label>
                    <select id="arb-choice" class="w-full border p-2 rounded bg-white font-bold text-blue-900">
                        <option value="Scénario A : Maintien sous condition stricte">Scénario A : Maintien sous condition stricte</option>
                        <option value="Scénario B : Restructuration opérationnelle immédiate" selected>Scénario B : Restructuration opérationnelle immédiate</option>
                        <option value="Scénario C : Injonction de retour à l'équilibre (Zéro concours)">Scénario C : Injonction de retour à l'équilibre (Zéro concours)</option>
                        <option value="Scénario Moratoire : Suspension conservatoire des versements">Scénario Moratoire : Suspension conservatoire des versements</option>
                    </select>
                </div>
                <div>
                    <label class="block font-semibold mb-1 text-green-700">Impact Financier attendu (€)</label>
                    <input type="text" id="arb-impact-fin" class="w-full border p-2 rounded bg-white font-medium" value="+ 240 k€ / an (économies)">
                </div>
                <div>
                    <label class="block font-semibold mb-1 text-blue-700">Levier Social & Ressources Humaines</label>
                    <input type="text" id="arb-impact-rh" class="w-full border p-2 rounded bg-white font-medium" value="Titularisation chauffeurs & baisse intérim de 60 %">
                </div>
                <div>
                    <label class="block font-semibold mb-1 text-amber-700">Cotation du Risque Politique</label>
                    <select id="arb-risk-pol" class="w-full border p-2 rounded bg-white font-bold text-amber-900">
                        <option value="Faible - Mesure consensuelle">Faible - Mesure consensuelle</option>
                        <option value="Modéré - Explicable en séance" selected>Modéré - Explicable en séance</option>
                        <option value="Élevé - Tension locale à anticiper">Élevé - Tension locale à anticiper</option>
                    </select>
                </div>
            </div>

            <div class="text-xs">
                <label class="block font-semibold mb-1">Exposé des motifs pour la délibération (Texte officiel)</label>
                <textarea id="arb-text" rows="3" class="w-full border p-2.5 rounded bg-white text-slate-800" placeholder="Exposé des motifs..."></textarea>
            </div>
        </div>

        <button onclick="renderTBI()" class="w-full bg-slate-900 hover:bg-blue-700 text-white font-bold py-3.5 px-6 rounded-lg transition duration-200 text-sm tracking-wide uppercase shadow-lg">
            Générer l'Aperçu du Tableau de Bord d'Impact (Spécimen Démo)
        </button>
        
        </div>
    </div>

    <!-- MODALE PÉDAGOGIQUE & FICHES RÉFLEXES -->
    <div id="help-modal" class="hidden fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 no-print">
        <div class="bg-white rounded-xl shadow-2xl max-w-lg w-full p-6 space-y-4 border border-slate-200">
            <div class="flex justify-between items-start border-b pb-3">
                <div>
                    <span id="help-badge" class="text-[10px] font-black uppercase px-2 py-0.5 rounded bg-blue-100 text-blue-800">Fiche Réflexe</span>
                    <h3 id="help-title" class="text-lg font-bold text-slate-900 mt-1">--</h3>
                </div>
                <button type="button" onclick="closeHelp()" class="text-slate-400 hover:text-slate-600 text-xl font-black">✕</button>
            </div>
            
            <div class="space-y-3 text-xs leading-relaxed text-slate-700">
                <div>
                    <h4 class="font-bold text-slate-900 uppercase text-[11px] mb-0.5">Définition :</h4>
                    <p id="help-def" class="bg-slate-50 p-2.5 rounded border">--</p>
                </div>
                <div>
                    <h4 class="font-bold text-slate-900 uppercase text-[11px] mb-0.5">Mode de calcul :</h4>
                    <p id="help-calc" class="font-mono text-blue-900 bg-blue-50 p-2 rounded border border-blue-200">--</p>
                </div>
                <div>
                    <h4 class="font-bold text-slate-900 uppercase text-[11px] mb-0.5">Normes Sectorielles :</h4>
                    <p id="help-norm" class="text-slate-800 bg-amber-50/70 p-2.5 rounded border border-amber-200">--</p>
                </div>
                <div>
                    <h4 class="font-bold text-slate-900 uppercase text-[11px] mb-0.5">Conséquence pour la collectivité :</h4>
                    <p id="help-impact" class="text-slate-700 italic">--</p>
                </div>
            </div>

            <div class="pt-2 text-right">
                <button type="button" onclick="closeHelp()" class="bg-slate-900 hover:bg-slate-800 text-white font-bold py-2 px-5 rounded text-xs">
                    Fermer
                </button>
            </div>
        </div>
    </div>

    <!-- RENDU FINAL : TBI-RU RECTO UNIQUE (FILIGRANÉ DÉMONSTRATION) -->
    <div id="output-section" class="hidden bg-white p-8 rounded-xl shadow-2xl mt-4 print-container border border-slate-300">
        
        <!-- FILIGRANE DÉMONSTRATION NON OPPOSABLE -->
        <div class="mb-5 p-3 bg-amber-100 border-2 border-amber-500 text-amber-950 rounded-lg text-center">
            <div class="text-xs font-black uppercase tracking-widest">
                ⚠️ Spécimen de démonstration — Document non opposable (Données fictives)
            </div>
        </div>

        <!-- BANDEAU D'ALERTE ROUGE -->
        <div id="tbi-red-banner" class="hidden mb-6 p-4 bg-red-600 text-white rounded-lg shadow-lg border-2 border-red-700">
            <div class="flex items-center gap-3">
                <span class="text-3xl">⛔</span>
                <div>
                    <div class="text-sm font-black uppercase tracking-wider">Alerte Rouge Déclassante - Moratoire Immédiat Recommandé</div>
                    <div class="text-xs font-medium text-red-100 mt-0.5" id="tbi-red-banner-desc">--</div>
                </div>
            </div>
        </div>

        <!-- En-tête officiel TBI -->
        <div class="border-b-4 border-slate-900 pb-4 mb-6 flex justify-between items-start">
            <div>
                <div class="flex items-center gap-3">
                    <span class="bg-slate-900 text-white px-2.5 py-1 text-sm font-black rounded tracking-widest">TBI-RU</span>
                    <h1 class="text-xl font-black text-slate-900 uppercase">Tableau de Bord d'Impact - Recto Unique</h1>
                </div>
                <div class="text-xs text-slate-600 font-semibold mt-1">
                    Structure : <span id="tbi-out-entity" class="font-black text-slate-900">--</span> | Tutelle : <span id="tbi-out-authority">--</span>
                </div>
                <div class="text-[11px] text-slate-500 font-medium mt-0.5">
                    Instance : <span id="tbi-out-instance">--</span> | <span id="tbi-out-scope-desc" class="font-bold text-blue-900">Périmètre complet</span>
                </div>
            </div>
            <div class="text-right">
                <div class="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Doctrine d'Arbitrage Satellites</div>
                <div class="text-[10px] text-slate-400 mt-1" id="tbi-out-date">--</div>
            </div>
        </div>

        <!-- Grille Principale Dynamique -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6" id="tbi-main-grid">
            
            <!-- COLONNE GAUCHE -->
            <div id="tbi-col-left" class="col-span-1 bg-slate-50 p-5 rounded-lg border-l-4 border-slate-900 flex flex-col justify-between">
                <div>
                    <div id="tbi-box-hs">
                        <div class="text-[11px] uppercase text-slate-500 font-black tracking-wider mb-2">Health Score Renormalisé</div>
                        <div class="text-5xl font-black text-slate-900 text-center my-2" id="tbi-out-hs">--</div>
                        <div class="text-center py-1.5 px-2 rounded text-xs font-black uppercase mb-4" id="tbi-out-hs-badge">--</div>
                        
                        <div class="text-[10px] uppercase text-slate-400 font-bold border-t pt-3 mb-2">Scores des Axes Audités (/5) :</div>
                        <div class="space-y-1.5 text-[11px] text-slate-600 font-medium" id="tbi-radar-list"></div>
                    </div>
                    <div id="tbi-box-hs-off" class="hidden text-xs text-slate-500 italic p-3 bg-white rounded border text-center">
                        Matrice de gouvernance hors champ du mandat.
                    </div>
                </div>

                <div id="tbi-box-legal" class="border-t border-slate-200 pt-3 mt-4 space-y-2">
                    <div>
                        <div class="text-[10px] uppercase text-slate-500 font-black tracking-wider mb-1">Conformité Légale :</div>
                        <div id="tbi-out-legal-badge" class="text-xs font-black uppercase py-1 px-2 rounded text-center">--</div>
                    </div>
                    <p class="text-[11px] text-slate-700 leading-tight italic" id="tbi-out-legal-summary">--</p>
                </div>
            </div>

            <!-- COLONNE DROITE -->
            <div id="tbi-col-right" class="col-span-2 space-y-5 flex flex-col justify-between">
                
                <div id="tbi-box-fin" class="space-y-2">
                    <div class="flex justify-between items-center">
                        <span class="text-xs uppercase text-slate-500 font-black tracking-wider">Équilibres Financiers & Comparatif Sectoriel</span>
                        <span id="tbi-out-sector-tag" class="text-[10px] font-bold text-slate-500 uppercase">--</span>
                    </div>

                    <table class="w-full text-left border-collapse text-xs">
                        <thead>
                            <tr class="bg-slate-100 text-[10px] uppercase text-slate-600 border-b">
                                <th class="p-2 font-bold">Indicateur Financier</th>
                                <th class="p-2 font-bold text-right">Réalisé N-1</th>
                                <th class="p-2 font-bold">Norme / Moyenne Sectorielle</th>
                                <th class="p-2 font-bold text-center">Alerte</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-200 text-[11px]">
                            <tr>
                                <td class="p-2 font-semibold">Chiffre d'Affaires réalisé</td>
                                <td class="p-2 font-black text-right" id="tbi-row-ca">--</td>
                                <td class="p-2 text-slate-600" id="tbi-row-ca-norm">Activité contractuelle attendue</td>
                                <td class="p-2 text-center" id="tbi-row-ca-alert">🟢</td>
                            </tr>
                            <tr>
                                <td class="p-2 font-semibold">Fonds de Roulement (FRNG)</td>
                                <td class="p-2 font-black text-right" id="tbi-row-frng">--</td>
                                <td class="p-2 text-slate-600" id="tbi-row-frng-norm">> 250 k€ (ou 6-8 % du CA)</td>
                                <td class="p-2 text-center" id="tbi-row-frng-alert">--</td>
                            </tr>
                            <tr>
                                <td class="p-2 font-semibold">Besoin en Fonds de Roulement (BFR)</td>
                                <td class="p-2 font-black text-right" id="tbi-row-bfr">--</td>
                                <td class="p-2 text-slate-600" id="tbi-row-bfr-norm">Moyenne : ~15 à 20 jours de CA</td>
                                <td class="p-2 text-center" id="tbi-row-bfr-alert">--</td>
                            </tr>
                            <tr>
                                <td class="p-2 font-semibold">Trésorerie Nette à la clôture</td>
                                <td class="p-2 font-black text-right" id="tbi-row-treso">--</td>
                                <td class="p-2 text-slate-600">Seuil de sécurité : > 0 €</td>
                                <td class="p-2 text-center" id="tbi-row-treso-alert">--</td>
                            </tr>
                            <tr>
                                <td class="p-2 font-semibold">Capacité de désendettement (Dette/CAF)</td>
                                <td class="p-2 font-black text-right" id="tbi-row-ratio">--</td>
                                <td class="p-2 text-slate-600" id="tbi-row-ratio-norm">Seuil d'alerte critique : 5 années</td>
                                <td class="p-2 text-center" id="tbi-row-ratio-alert">--</td>
                            </tr>
                        </tbody>
                    </table>

                    <div class="p-2 bg-red-50 border border-red-200 rounded text-xs text-red-900 flex justify-between items-center">
                        <span class="font-bold">Risque hors-bilan (Garantie d'emprunt accordée) :</span>
                        <span class="font-black text-sm" id="tbi-out-garantie">--</span>
                    </div>
                </div>

                <div id="tbi-box-other" class="bg-amber-50 p-3 rounded border border-amber-200 text-xs">
                    <div class="flex justify-between items-center mb-1">
                        <span class="font-black text-amber-900 uppercase text-[10px] tracking-wide">Fait Majeur / Signal Faible :</span>
                        <span id="tbi-out-other-impact" class="font-bold text-[10px] px-1.5 py-0.2 rounded bg-amber-200 text-amber-900">--</span>
                    </div>
                    <div class="font-bold text-slate-900" id="tbi-out-other-title">--</div>
                    <p class="text-slate-600 text-[11px] mt-0.5" id="tbi-out-other-desc">--</p>
                </div>

                <div>
                    <div class="text-xs uppercase text-slate-500 font-black tracking-wider mb-2">Orientation & Décision d'Arbitrage Soumise au Vote</div>
                    <div class="bg-slate-900 text-white p-3.5 rounded-lg">
                        <div class="text-xs font-bold text-blue-300 uppercase tracking-wide mb-1" id="tbi-out-arb-choice">--</div>
                        <p class="text-xs leading-relaxed text-slate-200 italic" id="tbi-out-arb-text">--</p>
                    </div>

                    <div class="grid grid-cols-3 gap-2.5 mt-2.5 text-center">
                        <div class="p-2 bg-green-50 rounded border border-green-200">
                            <div class="text-[9px] font-bold text-green-700 uppercase">Impact Financier</div>
                            <div class="text-xs font-black text-green-800" id="tbi-out-imp-fin">--</div>
                        </div>
                        <div class="p-2 bg-blue-50 rounded border border-blue-200">
                            <div class="text-[9px] font-bold text-blue-700 uppercase">Volet RH / Social</div>
                            <div class="text-xs font-black text-blue-800" id="tbi-out-imp-rh">--</div>
                        </div>
                        <div class="p-2 bg-amber-50 rounded border border-amber-200">
                            <div class="text-[9px] font-bold text-amber-700 uppercase">Risque Politique</div>
                            <div class="text-xs font-black text-amber-800" id="tbi-out-risk-pol">--</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="mt-5 pt-2 border-t border-amber-300 text-center text-[10px] font-bold uppercase text-amber-800">
            Archétype Satellites — Version de démonstration interactive (Usage commercial ou délibératif interdit)
        </div>

        <div class="mt-4 pt-4 border-t text-center no-print flex justify-center gap-4">
            <button onclick="window.print()" class="bg-blue-900 hover:bg-blue-800 text-white text-xs font-bold py-2.5 px-6 rounded shadow">
                🖨️ Aperçu Impression (Spécimen filigrané)
            </button>
            <button onclick="backToEdit()" class="bg-slate-200 hover:bg-slate-300 text-slate-800 text-xs font-bold py-2.5 px-6 rounded shadow">
                ✏️ Revenir aux paramètres de test
            </button>
        </div>
    </div>
</div>

<script>
    function demoRestrictedNotice() {
        alert("Mode démonstration : la sauvegarde dans le Cloud et la création de nouveaux dossiers sont réservées à la version sous licence.");
    }

    // --- BASE DE CONNAISSANCES & FICHES RÉFLEXES ENRICHIE ---
    const helpDatabase = {
        moteurGlobal: {
            title: "Mécanique du Moteur Financier & Bilanciel",
            badge: "Doctrine d'Audit",
            def: "L'analyse repose sur le triptyque de l'analyse bilancielle : FRNG - BFR = Trésorerie Nette, complété par la capacité de désendettement (Dette / CAF) et le risque hors-bilan.",
            calc: "1. FRNG = Ressources Durables - Emplois Stables\n2. BFR = Actif Circulant - Passif Circulant\n3. Trésorerie = FRNG - BFR",
            norm: "Le FRNG doit être strictement positif et couvrir intégralement le BFR pour garantir une trésorerie saine (> 0 €) sans dépendance aux découverts bancaires.",
            impact: "Alerte immédiatement les élus et le DGS si la structure vit à crédit ou risque d'appeler la garantie d'emprunt de la collectivité."
        },
        ca: {
            title: "Chiffre d'Affaires HT (CA)",
            badge: "Activité Économique",
            def: "Montant total hors taxes des prestations facturées, ventes d'usagers et recettes d'exploitation sur l'exercice.",
            calc: "Total des comptes 70 du plan comptable général (PCG)",
            norm: "Doit couvrir a minima 35 à 45 % des charges d'exploitation dans le transport public sous DSP, 80 % en aménagement.",
            impact: "Un recul du CA combiné à des charges fixes rigides provoque immédiatement un effet de ciseau budgétaire."
        },
        caf: {
            title: "Capacité d'Autofinancement (CAF)",
            badge: "Rentabilité Réelle",
            def: "Surplus monétaire réel généré par l'activité opérationnelle permettant de renouveler les investissements et de rembourser la dette bancaire.",
            calc: "EBE + Autres produits encaissables - Autres charges décaissables",
            norm: "Moyenne sectorielle : 6 à 10 % du chiffre d'affaires annuel.",
            impact: "Une CAF négative ou proche de zéro rend le satellite incapable d'honorer ses annuités sans secours financier de la collectivité."
        },
        ressources: {
            title: "Ressources Durables (Haut de Bilan - Passif)",
            badge: "Financement Stable",
            def: "Capitaux permanents restant à disposition de l'organisme sur plus d'un an : capital social, réserves, provisions pour risques, subventions d'investissement et emprunts bancaires à moyen/long terme.",
            calc: "Capitaux Propres + Provisions Long Terme + Dettes Financières MLT (Comptes 10 à 16)",
            norm: "Doivent toujours être supérieures aux emplois stables pour dégager un FRNG protecteur.",
            impact: "Une insuffisance de ressources durables fragilise l'ensemble de la structure bilancielle et oblige à financer des immobilisations par du court terme."
        },
        emplois: {
            title: "Emplois Stables (Haut de Bilan - Actif)",
            badge: "Actifs Immobilisés",
            def: "Ensemble des investissements durables nécessaires au fonctionnement du service : matériel roulant, bus, terrains, réseaux, équipements et immobilisations financières.",
            calc: "Total de l'Actif Immobilisé Brut (Classe 2 du plan comptable)",
            norm: "Doivent être financés exclusivement par des ressources de long terme (emprunts bancaires + fonds propres).",
            impact: "Financer des actifs stables avec des découverts bancaires ou du crédit fournisseur conduit à court terme à la cessation de paiements."
        },
        actifCirc: {
            title: "Actif Circulant (Exploitation)",
            badge: "Cycle d'Exploitation",
            def: "Créances clients/usagers en attente d'encaissement, créances de subventions notifiées, avances accordées et stocks de fournitures.",
            calc: "Stocks + Créances usagers et collectivités tutrices (Comptes 3 et 4 de l'actif)",
            norm: "Doit être encaissé dans les délais contractuels légaux (30 à 60 jours maximum).",
            impact: "Un gonflement de l'actif circulant dénote des impayés d'usagers, des litiges de facturation ou des retards administratifs de versement des subventions."
        },
        passifCirc: {
            title: "Passif Circulant (Dettes d'Exploitation)",
            badge: "Cycle d'Exploitation",
            def: "Dettes court terme non financières contractées auprès des fournisseurs, sous-traitants, organismes sociaux (URSSAF) et administration fiscale.",
            calc: "Dettes Fournisseurs + Dettes Fiscales et Sociales (Comptes 4 du passif)",
            norm: "Délais de règlement fournisseurs alignés sur les obligations légales LME (45 à 60 jours maximum).",
            impact: "Une accumulation anormale signale des retards de paiement imposés aux sous-traitants par manque de liquidités et un risque d'assignation."
        },
        dette: {
            title: "Dette Financière Brute (Passif Stable)",
            badge: "Endettement Bancaire",
            def: "Total du capital restant dû sur les emprunts contractés auprès des banques et des avances remboursables octroyées par la collectivité.",
            calc: "Emprunts bancaires MLT + Avances en compte courant d'associé (Comptes 16)",
            norm: "Ratio Dette / CAF ne devant pas excéder 4 à 5 années de CAF.",
            impact: "Sert de base directe au calcul de l'exposition hors-bilan de la collectivité si une garantie d'emprunt a été accordée."
        },
        frng: {
            title: "Fonds de Roulement Net Global (FRNG)",
            badge: "Solvabilité Long Terme",
            def: "Excédent des capitaux stables sur les immobilisations. Il constitue le matelas financier de sécurité permanent.",
            calc: "Ressources Durables - Emplois Stables",
            norm: "Doit toujours être strictement positif (> 0 €) et représenter entre 6 et 15 % du CA selon le secteur d'activité.",
            impact: "Un FRNG négatif indique que la structure finance des actifs durables au moyen de dettes à court terme."
        },
        bfr: {
            title: "Besoin en Fonds de Roulement (BFR)",
            badge: "Décalage d'Exploitation",
            def: "Montant gelé dans le décalage quotidien entre ce que la structure doit décaisser pour fonctionner et ce qu'elle encaisse des usagers.",
            calc: "Actif Circulant (Créances + Stocks) - Passif Circulant (Dettes CT)",
            norm: "Transport : 15 à 20 jours de CA. Aménagement foncier : 45 à 90 jours de CA.",
            impact: "Si le BFR s'envole, il absorbe l'intégralité de la trésorerie même si l'exploitation dégage un résultat comptable positif."
        },
        treso: {
            title: "Trésorerie Nette à la Clôture",
            badge: "Liquidité Immédiate",
            def: "Fonds immédiatement disponibles sur les comptes bancaires après compensation des découverts et facilités de caisse.",
            calc: "FRNG - BFR (ou Disponibilités bancaires - Concours bancaires courants)",
            norm: "Seuil impératif : > 0 €. Idéalement un matelas équivalent à 30 à 45 jours de charges de fonctionnement.",
            impact: "Une trésorerie négative et durable conduit directement à la cessation de paiements et à la nomination d'un administrateur judiciaire."
        },
        ratioDette: {
            title: "Capacité de Désendettement (Dette / CAF)",
            badge: "Surveillance Prudentielle",
            def: "Nombre théorique d'années nécessaires pour rembourser l'intégralité de la dette en y consacrant 100 % de la CAF annuelle.",
            calc: "Dette Financière Brute / Capacité d'Autofinancement (CAF)",
            norm: "Sain : < 4 ans | Vigilance : 4 à 5 ans | Seuil critique d'alerte : > 5 années (7 ans en aménagement).",
            impact: "Au-delà du seuil critique, la structure ne peut plus se refinancer sans injection de fonds publics."
        },
        garantie: {
            title: "Garantie d'Emprunt Accordée par la Collectivité",
            badge: "Risque Hors-Bilan",
            def: "Engagement juridique pris par la collectivité de se substituer au satellite défaillant pour rembourser les échéances bancaires.",
            calc: "Dette Financière Brute x Pourcentage garanti par délibération",
            norm: "Encadrement strict par le Code général des collectivités territoriales (règles de division des risques).",
            impact: "L'activation de la garantie entraîne l'inscription immédiate d'une dépense obligatoire au budget primitif de la collectivité."
        },
        j1: {
            title: "Commande Publique & Avenants",
            badge: "Sécurité Juridique",
            def: "Contrôle du respect des règles de passation, des seuils de publicité et des limites apportées aux avenants contractuels.",
            calc: "Avenants limités à 50 % du montant initial du contrat sans modification substantielle de l'objet.",
            norm: "Traçabilité intégrale des motifs techniques et financiers justifiant chaque avenant.",
            impact: "Un avenant jugé illégal expose au risque d'annulation contentieuse et de remboursement des sommes versées."
        },
        j2: {
            title: "Conventions Réglementées (Art. L. 225-38)",
            badge: "Gouvernance & Probité",
            def: "Procédure d'autorisation préalable pour toute convention passée entre le satellite et une structure où un administrateur détient des intérêts.",
            calc: "Autorisation préalable du conseil d'administration + avis spécial du commissaire aux comptes.",
            norm: "Zéro convention conclue sans délibération formelle préalable.",
            impact: "L'omission de cette formalité peut engager la responsabilité civile et pénale des administrateurs pour prise illégale d'intérêts."
        },
        j3: {
            title: "Déport des Élus & Prévention Pénale (Sapin 2)",
            badge: "Prévention Pénale",
            def: "Obligation stricte pour les élus désignés administrateurs de ne participer ni aux débats ni aux votes lors de l'octroi d'aides ou de contrats à la structure.",
            calc: "Mention expresse et nominative du déport inscrite au procès-verbal de séance.",
            norm: "Application de l'article 432-12 du Code pénal (jurisprudence constante de la Cour de cassation).",
            impact: "Le défaut de déport matérialise le délit pénal de prise illégale d'intérêts pour les élus concernés."
        },
        j4: {
            title: "Périmètre de Compétence des SPL (Art. L. 1531-1 CGCT)",
            badge: "Régime Quasi-Régie",
            def: "Une Société Publique Locale ne peut travailler que pour le compte exclusif de ses collectivités actionnaires et sur leur seul territoire géographique.",
            calc: "Actionnariat : 100 % public | Chiffre d'affaires hors actionnaires : 0 %.",
            norm: "Contrôle analogue exercé conjointement par l'ensemble des membres actionnaires.",
            impact: "Toute prestation réalisée au profit d'un tiers privé est frappée de nullité absolue."
        }
    };

    const sectorBenchmarks = {
        transport: { label: "Transport Public Local (DSP / SEM)", frngNormTxt: "> 250 k€ (ou 6-8 % du CA)", bfrDays: 18, ratioMax: 5.0 },
        amenagement: { label: "Aménagement & Logement (SPL / SEM)", frngNormTxt: "> 10-15 % du CA pour le foncier", bfrDays: 60, ratioMax: 6.5 },
        medicosocial: { label: "Médico-social & Santé (M22 / CPOM)", frngNormTxt: "15 jours de charges réelles", bfrDays: 25, ratioMax: 4.0 },
        general: { label: "Association / Entreprise Générale", frngNormTxt: "> 0 € (positif)", bfrDays: 30, ratioMax: 5.0 }
    };

    function showHelp(topic) {
        const item = helpDatabase[topic];
        if (!item) return;
        document.getElementById('help-title').innerText = item.title;
        document.getElementById('help-badge').innerText = item.badge;
        document.getElementById('help-def').innerText = item.def;
        document.getElementById('help-calc').innerText = item.calc;
        document.getElementById('help-norm').innerText = item.norm;
        document.getElementById('help-impact').innerText = item.impact;
        document.getElementById('help-modal').classList.remove('hidden');
    }

    function closeHelp() {
        document.getElementById('help-modal').classList.add('hidden');
    }

    const templates = {
        adour: {
            entity: "SEM Adour Mobilité Rurale",
            authority: "Conseil Départemental des Landes",
            instance: "Commission Permanente (Séance DM2)",
            sector: "transport",
            modules: { fin: true, jur: true, quinze: true, other: true },
            redFlag: true,
            redFlagReason: "Risque avéré de prise illégale d'intérêts et vice de forme sur l'Avenant n°3 DSP",
            ca: 4200, caf: 110, ressources: 3100, emplois: 3220, actifCirc: 840, passifCirc: 690, dette: 2800, garantiePct: 80,
            legalToggles: [true, true, true, true],
            legalVals: ["0", "0", "0", "1"],
            legalNotes: ["Avenant n°3 modifiant les tarifs sans base légale solide", "Convention d'appui facturée sans accord préalable du CA", "Absence d'enregistrement formel des déports d'élus en CA", "Actionnariat 100 % public et champ territorial conformes"],
            axeToggles: [true, true, true, true, true],
            checks: [true, false, false, false, false, false, false, false, false, false, false, true, true, false, true, true, false, true, false, false],
            other: { impact: "blocking", title: "Crise managériale aiguë et vacance de la direction générale", desc: "Absence de pilotage exécutif depuis 4 mois et retards critiques de facturation." },
            arbChoice: "Scénario Moratoire : Suspension conservatoire des versements",
            impactFin: "Moratoire sur l'avance d'associé de 200 k€",
            impactRh: "Injonction de nomination d'une direction par intérim",
            riskPol: "Modéré - Explicable en séance",
            arbText: "Conditionner formellement le vote de toute aide financière ou avance en compte courant à la purge intégrale du vice de forme de l'Avenant n°3 et à la régularisation des déports d'élus sous 60 jours."
        },
        amenagement: {
            entity: "SPL Grand Sud Aménagement",
            authority: "Région Occitanie",
            instance: "Comité d'Audit Régional",
            sector: "amenagement",
            modules: { fin: true, jur: true, quinze: true, other: false },
            redFlag: false,
            redFlagReason: "",
            ca: 12500, caf: 820, ressources: 9400, emplois: 8900, actifCirc: 3400, passifCirc: 2800, dette: 6200, garantiePct: 50,
            legalToggles: [true, true, true, true],
            legalVals: ["1", "1", "1", "1"],
            legalNotes: ["Marchés VRD conformes", "Conventions approuvées", "Déports actés", "Champ exclusif 100 % respecté"],
            axeToggles: [true, true, true, true, true],
            checks: Array(20).fill(true),
            other: { impact: "none", title: "", desc: "" },
            arbChoice: "Scénario A : Maintien sous condition stricte",
            impactFin: "Soutenance de la dette sur 7,5 ans",
            impactRh: "Effectifs techniques stables",
            riskPol: "Faible - Mesure consensuelle",
            arbText: "La structure dégage une CAF positive permettant d'absorber le portage foncier. Maintien des concours financiers recommandé."
        },
        esms: {
            entity: "Association ESMS Le Bois Fleuri",
            authority: "Conseil Départemental / ARS",
            instance: "Commission Tarification M22",
            sector: "medicosocial",
            modules: { fin: true, jur: true, quinze: true, other: true },
            redFlag: true,
            redFlagReason: "Défaut d'étanchéité des sections tarifaires M22 et absence de CPOM opposable",
            ca: 3800, caf: -45, ressources: 1200, emplois: 1450, actifCirc: 310, passifCirc: 480, dette: 1600, garantiePct: 50,
            legalToggles: [true, true, true, true],
            legalVals: ["0.5", "0", "0.5", "0.5"],
            legalNotes: ["Intérim non mis en concurrence", "Transferts indus de charges M22", "Déports non documentés", "Caducité du CPOM"],
            axeToggles: [true, true, true, true, true],
            checks: [true, false, false, false, false, false, false, false, false, false, false, false, true, true, true, false, false, false, false, false],
            other: { impact: "major", title: "Absentéisme RH critique (> 22 %)", desc: "Péril sur la continuité des soins et surconsommation d'intérim non budgétée." },
            arbChoice: "Scénario C : Injonction de retour à l'équilibre (Zéro concours)",
            impactFin: "Plan d'économies de 180 k€ sous 12 mois",
            impactRh: "Audit clinique de l'absentéisme et gel du recours intérimaire",
            riskPol: "Élevé - Tension locale à anticiper",
            arbText: "Refus de toute dotation non compensée sans signature préalable d'un protocole de redressement de gestion et renouvellement des organes de direction."
        }
    };

    function toggleModule(mod) {
        const isChecked = document.getElementById('mod-toggle-' + mod).checked;
        const sec = document.getElementById('section-mod-' + mod);
        if (sec) {
            sec.style.display = isChecked ? 'block' : 'none';
        }
        computeHealthScore();
        computeLegal();
        computeFinances();
    }

    function loadCaseTemplate() {
        const key = document.getElementById('case-selector').value;
        const d = templates[key] || templates.adour;

        document.getElementById('current-dossier-label').innerText = d.entity + " (Cas fictif)";
        document.getElementById('cfg-entity').value = d.entity;
        document.getElementById('cfg-authority').value = d.authority;
        document.getElementById('cfg-instance').value = d.instance;
        document.getElementById('cfg-sector').value = d.sector;

        document.getElementById('mod-toggle-fin').checked = d.modules.fin;
        document.getElementById('mod-toggle-jur').checked = d.modules.jur;
        document.getElementById('mod-toggle-quinze').checked = d.modules.quinze;
        document.getElementById('mod-toggle-other').checked = d.modules.other;
        toggleModule('fin'); toggleModule('jur'); toggleModule('quinze'); toggleModule('other');

        const rfToggle = document.getElementById('red-flag-toggle');
        rfToggle.checked = d.redFlag;
        document.getElementById('red-flag-reason').value = d.redFlagReason;
        toggleRedFlag();

        document.getElementById('fn-ca').value = d.ca;
        document.getElementById('fn-caf').value = d.caf;
        document.getElementById('fn-ressources').value = d.ressources;
        document.getElementById('fn-emplois').value = d.emplois;
        document.getElementById('fn-actif-circ').value = d.actifCirc;
        document.getElementById('fn-passif-circ').value = d.passifCirc;
        document.getElementById('fn-dette').value = d.dette;
        document.getElementById('fn-garantie-pct').value = d.garantiePct;

        for (let i = 1; i <= 4; i++) {
            document.getElementById('jur-toggle-' + i).checked = d.legalToggles[i - 1];
            document.getElementById('jur-j' + i).value = d.legalVals[i - 1];
            document.getElementById('jur-j' + i + '-note').value = d.legalNotes[i - 1];
        }

        for (let i = 1; i <= 5; i++) {
            document.getElementById('axe-toggle-' + i).checked = d.axeToggles[i - 1];
        }
        d.checks.forEach((val, idx) => {
            const axe = Math.floor(idx / 4) + 1;
            const c = (idx % 4) + 1;
            document.getElementById(`c-${axe}-${c}`).checked = val;
        });

        document.getElementById('other-impact').value = d.other.impact;
        document.getElementById('other-title').value = d.other.title;
        document.getElementById('other-desc').value = d.other.desc;

        document.getElementById('arb-choice').value = d.arbChoice;
        document.getElementById('arb-impact-fin').value = d.impactFin;
        document.getElementById('arb-impact-rh').value = d.impactRh;
        document.getElementById('arb-risk-pol').value = d.riskPol;
        document.getElementById('arb-text').value = d.arbText;

        computeFinances();
        computeLegal();
        computeHealthScore();
    }

    function toggleRedFlag() {
        const isChecked = document.getElementById('red-flag-toggle').checked;
        const container = document.getElementById('red-flag-reason-container');
        const lbl = document.getElementById('red-flag-status-label');
        if (isChecked) {
            container.classList.remove('hidden');
            lbl.innerText = "ACTIF (DÉCLASSANT)";
            lbl.className = "text-xs font-black text-red-600 uppercase";
        } else {
            container.classList.add('hidden');
            lbl.innerText = "Inactif";
            lbl.className = "text-xs font-black text-slate-500 uppercase";
        }
    }

    function handleOtherImpact() {
        const val = document.getElementById('other-impact').value;
        if (val === 'blocking') {
            document.getElementById('red-flag-toggle').checked = true;
            toggleRedFlag();
        }
    }

    let calculatedFinances = {};

    function computeFinances() {
        if (!document.getElementById('mod-toggle-fin').checked) {
            calculatedFinances = { ca: 0, caf: 0, frng: 0, bfr: 0, treso: 0, dette: 0, ratioDette: "N/A", montantGarantie: 0, garantiePct: 0 };
            return;
        }
        const ca = parseFloat(document.getElementById('fn-ca').value) || 0;
        const caf = parseFloat(document.getElementById('fn-caf').value) || 0;
        const ressources = parseFloat(document.getElementById('fn-ressources').value) || 0;
        const emplois = parseFloat(document.getElementById('fn-emplois').value) || 0;
        const actifCirc = parseFloat(document.getElementById('fn-actif-circ').value) || 0;
        const passifCirc = parseFloat(document.getElementById('fn-passif-circ').value) || 0;
        const dette = parseFloat(document.getElementById('fn-dette').value) || 0;
        const garantiePct = parseFloat(document.getElementById('fn-garantie-pct').value) || 0;

        const frng = ressources - emplois;
        const bfr = actifCirc - passifCirc;
        const treso = frng - bfr;
        const ratioDette = caf > 0 ? (dette / caf).toFixed(1) : (dette > 0 ? "Critique (>15)" : "0,0");
        const montantGarantie = (dette * (garantiePct / 100)).toFixed(0);

        calculatedFinances = { ca, caf, frng, bfr, treso, dette, ratioDette, montantGarantie, garantiePct };

        const elFrng = document.getElementById('calc-frng');
        elFrng.innerText = frng + " k€";
        elFrng.className = frng >= 0 ? "text-sm font-black text-green-700" : "text-sm font-black text-red-600";

        const elBfr = document.getElementById('calc-bfr');
        elBfr.innerText = bfr + " k€";

        const elTreso = document.getElementById('calc-treso');
        elTreso.innerText = treso + " k€";
        elTreso.className = treso >= 0 ? "text-sm font-black text-green-700" : "text-sm font-black text-red-600";

        const elRatio = document.getElementById('calc-ratio-dette');
        elRatio.innerText = ratioDette + " ans";
        if (parseFloat(ratioDette) > 8 || caf <= 0) {
            elRatio.className = "text-sm font-black text-red-600";
        } else if (parseFloat(ratioDette) > 5) {
            elRatio.className = "text-sm font-black text-amber-600";
        } else {
            elRatio.className = "text-sm font-black text-green-700";
        }

        const sKey = document.getElementById('cfg-sector').value;
        const bm = sectorBenchmarks[sKey] || sectorBenchmarks.transport;
        document.getElementById('label-sector-norm').innerText = bm.label;

        const bulletContainer = document.getElementById('diagnostic-bullet-points');
        bulletContainer.innerHTML = '';

        if (frng < 0) {
            bulletContainer.innerHTML += `<li class="text-red-700 flex items-start gap-1.5"><span>🔴</span> <b>FRNG négatif (${frng} k€) :</b> Anomalie critique. Les immobilisations sont financées par des dettes court terme.</li>`;
        } else {
            bulletContainer.innerHTML += `<li class="text-green-800 flex items-start gap-1.5"><span>🟢</span> <b>FRNG positif (${frng} k€) :</b> Situation saine. Matelas de sécurité stable.</li>`;
        }

        const bfrNormEstimate = ca > 0 ? Math.round((ca / 365) * bm.bfrDays) : 180;
        if (bfr > bfrNormEstimate * 1.4) {
            bulletContainer.innerHTML += `<li class="text-amber-800 flex items-start gap-1.5"><span>🟡</span> <b>BFR anormal (${bfr} k€ vs moyenne sectorielle ~${bfrNormEstimate} k€) :</b> Écart de +${bfr - bfrNormEstimate} k€. Allongement des impayés ou délais d'encaissement.</li>`;
        } else {
            bulletContainer.innerHTML += `<li class="text-green-800 flex items-start gap-1.5"><span>🟢</span> <b>BFR maîtrisé (${bfr} k€ vs moyenne ~${bfrNormEstimate} k€) :</b> Délais de paiement conformes aux standards.</li>`;
        }

        if (treso < 0) {
            bulletContainer.innerHTML += `<li class="text-red-700 flex items-start gap-1.5"><span>🔴</span> <b>Trésorerie Nette déficitaire (${treso} k€) :</b> Rupture de liquidité. Le FRNG ne couvre plus le BFR.</li>`;
        } else {
            bulletContainer.innerHTML += `<li class="text-green-800 flex items-start gap-1.5"><span>🟢</span> <b>Trésorerie Nette positive (${treso} k€) :</b> Liquidités disponibles.</li>`;
        }

        const rVal = parseFloat(ratioDette);
        if (isNaN(rVal) || rVal > bm.ratioMax || caf <= 0) {
            bulletContainer.innerHTML += `<li class="text-red-700 flex items-start gap-1.5"><span>🚨</span> <b>Désendettement critique (${ratioDette} ans vs seuil limite de ${bm.ratioMax} ans) :</b> Risque majeur d'appel de la garantie publique (${montantGarantie} k€).</li>`;
        } else {
            bulletContainer.innerHTML += `<li class="text-green-800 flex items-start gap-1.5"><span>🟢</span> <b>Endettement soutenable (${ratioDette} ans) :</b> Capacité de remboursement alignée.</li>`;
        }
    }

    let legalStatus = "Conforme";

    function computeLegal() {
        if (!document.getElementById('mod-toggle-jur').checked) {
            legalStatus = "Hors champ";
            document.getElementById('badge-legal-global').innerText = "Hors champ";
            document.getElementById('badge-legal-global').className = "text-[11px] font-black px-2 py-0.5 rounded uppercase bg-slate-200 text-slate-700";
            return;
        }

        let totalPoints = 0;
        let activeCount = 0;

        for (let i = 1; i <= 4; i++) {
            if (document.getElementById('jur-toggle-' + i).checked) {
                totalPoints += parseFloat(document.getElementById('jur-j' + i).value);
                activeCount++;
            }
        }

        const badge = document.getElementById('badge-legal-global');
        if (activeCount === 0) {
            legalStatus = "Non audité";
            badge.innerText = "Non audité";
            badge.className = "text-[11px] font-black px-2 py-0.5 rounded uppercase bg-slate-200 text-slate-700";
            return;
        }

        const ratio = totalPoints / activeCount;
        if (ratio >= 0.95) {
            legalStatus = "Conforme";
            badge.innerText = "Conforme";
            badge.className = "text-[11px] font-black px-2 py-0.5 rounded uppercase bg-green-200 text-green-900";
        } else if (ratio >= 0.5) {
            legalStatus = "Sous Réserves";
            badge.innerText = "Sous Réserves";
            badge.className = "text-[11px] font-black px-2 py-0.5 rounded uppercase bg-amber-200 text-amber-900";
        } else {
            legalStatus = "Irrégularité Critique";
            badge.innerText = "Irrégularité Critique";
            badge.className = "text-[11px] font-black px-2 py-0.5 rounded uppercase bg-red-200 text-red-900";
        }
    }

    let calculatedHS = 40;
    let scoresAxes = [0, 0, 0, 0, 0];
    let axesActifs = [true, true, true, true, true];

    function computeHealthScore() {
        const isQuinzeActive = document.getElementById('mod-toggle-quinze').checked;
        if (!isQuinzeActive) {
            calculatedHS = 0;
            document.getElementById('hs-display').innerText = "N/A";
            document.getElementById('hs-diag-label').innerText = "Hors mandat";
            document.getElementById('hs-diag-label').className = "ml-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-500 text-white";
            return;
        }

        let totalPtsGagnes = 0;
        let totalPtsPossibles = 0;

        for (let axe = 1; axe <= 5; axe++) {
            const isAxeActive = document.getElementById('axe-toggle-' + axe).checked;
            axesActifs[axe - 1] = isAxeActive;
            const card = document.getElementById('card-axe-' + axe);

            if (!isAxeActive) {
                card.classList.add('opacity-40');
                scoresAxes[axe - 1] = "Hors champ";
                document.getElementById('score-axe-' + axe).innerText = "Exclu";
                continue;
            } else {
                card.classList.remove('opacity-40');
            }

            let ptsAxe = 0;
            for (let c = 1; c <= 4; c++) {
                if (document.getElementById(`c-${axe}-${c}`).checked) {
                    ptsAxe++;
                }
            }

            totalPtsGagnes += ptsAxe;
            totalPtsPossibles += 4;

            scoresAxes[axe - 1] = (ptsAxe * 1.25).toFixed(2).replace('.', ',') + "/5";
            document.getElementById('score-axe-' + axe).innerText = scoresAxes[axe - 1];
        }

        if (totalPtsPossibles === 0) {
            calculatedHS = 100;
        } else {
            calculatedHS = Math.round((totalPtsGagnes / totalPtsPossibles) * 100);
        }

        document.getElementById('hs-display').innerText = calculatedHS;

        const lbl = document.getElementById('hs-diag-label');
        if (calculatedHS >= 75) {
            lbl.innerText = "Situation Saine";
            lbl.className = "ml-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-green-600 text-white";
        } else if (calculatedHS >= 50) {
            lbl.innerText = "Vigilance Requise";
            lbl.className = "ml-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-600 text-white";
        } else {
            lbl.innerText = "Vulnérabilité Forte";
            lbl.className = "ml-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-red-600 text-white";
        }
    }

    function renderTBI() {
        document.getElementById('input-section').classList.add('hidden');
        document.getElementById('workspace-section').classList.add('hidden');
        document.getElementById('output-section').classList.remove('hidden');

        document.getElementById('tbi-out-entity').innerText = document.getElementById('cfg-entity').value;
        document.getElementById('tbi-out-authority').innerText = document.getElementById('cfg-authority').value;
        document.getElementById('tbi-out-instance').innerText = document.getElementById('cfg-instance').value;
        document.getElementById('tbi-out-date').innerText = "Simulation du " + new Date().toLocaleDateString('fr-FR');

        const finActive = document.getElementById('mod-toggle-fin').checked;
        const jurActive = document.getElementById('mod-toggle-jur').checked;
        const qzActive = document.getElementById('mod-toggle-quinze').checked;
        const othActive = document.getElementById('mod-toggle-other').checked;

        let scopes = [];
        if (finActive) scopes.push("Finances & Bilan");
        if (jurActive) scopes.push("Légalité & Risques");
        if (qzActive) scopes.push("Matrice de Gouvernance");
        if (othActive) scopes.push("Fait Majeur");
        document.getElementById('tbi-out-scope-desc').innerText = "Mandat : " + (scopes.length ? scopes.join(" + ") : "Synthèse libre");

        const isRedFlag = document.getElementById('red-flag-toggle').checked;
        const redBanner = document.getElementById('tbi-red-banner');
        const b = document.getElementById('tbi-out-hs-badge');

        if (isRedFlag) {
            redBanner.classList.remove('hidden');
            document.getElementById('tbi-red-banner-desc').innerText = document.getElementById('red-flag-reason').value;
            b.innerText = "ALERTE ROUGE (DÉCISION BLOQUÉE)";
            b.className = "text-center py-1.5 px-2 rounded text-xs font-black uppercase mb-4 bg-red-600 text-white animate-pulse";
        } else {
            redBanner.classList.add('hidden');
            if (!qzActive) {
                b.innerText = "Hors Périmètre de Gouvernance";
                b.className = "text-center py-1.5 px-2 rounded text-xs font-black uppercase mb-4 bg-slate-200 text-slate-700";
            } else if (calculatedHS >= 75) {
                b.innerText = "Situation Saine & Maîtrisée";
                b.className = "text-center py-1.5 px-2 rounded text-xs font-black uppercase mb-4 bg-green-100 text-green-800";
            } else if (calculatedHS >= 50) {
                b.innerText = "Vigilance Modérée Requise";
                b.className = "text-center py-1.5 px-2 rounded text-xs font-black uppercase mb-4 bg-amber-100 text-amber-800";
            } else {
                b.innerText = "Vulnérabilité Critique";
                b.className = "text-center py-1.5 px-2 rounded text-xs font-black uppercase mb-4 bg-red-100 text-red-800";
            }
        }

        const boxHs = document.getElementById('tbi-box-hs');
        const boxHsOff = document.getElementById('tbi-box-hs-off');
        if (qzActive) {
            boxHs.classList.remove('hidden');
            boxHsOff.classList.add('hidden');
            document.getElementById('tbi-out-hs').innerText = calculatedHS;

            const radarList = document.getElementById('tbi-radar-list');
            radarList.innerHTML = '';
            const labels = ["1. Gouvernance", "2. Modèle Économique", "3. Organisation & RH", "4. Activité & Usagers", "5. Exécution"];
            for (let i = 0; i < 5; i++) {
                if (axesActifs[i]) {
                    radarList.innerHTML += `
                        <div class="flex justify-between items-center">
                            <span>${labels[i]} :</span>
                            <span class="font-black px-1.5 py-0.5 rounded text-white bg-slate-800 text-[10px]">${scoresAxes[i]}</span>
                        </div>
                    `;
                }
            }
        } else {
            boxHs.classList.add('hidden');
            boxHsOff.classList.remove('hidden');
        }

        const boxLegal = document.getElementById('tbi-box-legal');
        if (jurActive) {
            boxLegal.classList.remove('hidden');
            const outLegalBadge = document.getElementById('tbi-out-legal-badge');
            outLegalBadge.innerText = legalStatus;
            if (legalStatus === "Conforme") {
                outLegalBadge.className = "text-xs font-black uppercase py-1 px-2 rounded text-center bg-green-100 text-green-800";
            } else if (legalStatus === "Sous Réserves") {
                outLegalBadge.className = "text-xs font-black uppercase py-1 px-2 rounded text-center bg-amber-100 text-amber-800";
            } else {
                outLegalBadge.className = "text-xs font-black uppercase py-1 px-2 rounded text-center bg-red-100 text-red-800";
            }
            let notes = [];
            for (let i = 1; i <= 4; i++) {
                if (document.getElementById('jur-toggle-' + i).checked) {
                    const txt = document.getElementById('jur-j' + i + '-note').value.trim();
                    if (txt) notes.push(txt);
                }
            }
            document.getElementById('tbi-out-legal-summary').innerText = notes.length ? notes.join(" ; ") : "Points d'audit réguliers sans anomalie majeure.";
        } else {
            boxLegal.classList.add('hidden');
        }

        const boxFin = document.getElementById('tbi-box-fin');
        if (finActive) {
            boxFin.classList.remove('hidden');
            const sKey = document.getElementById('cfg-sector').value;
            const bm = sectorBenchmarks[sKey] || sectorBenchmarks.transport;
            document.getElementById('tbi-out-sector-tag').innerText = "Référentiel : " + bm.label;

            document.getElementById('tbi-row-ca').innerText = calculatedFinances.ca + " k€";
            document.getElementById('tbi-row-frng').innerText = calculatedFinances.frng + " k€";
            document.getElementById('tbi-row-frng-norm').innerText = bm.frngNormTxt;
            document.getElementById('tbi-row-frng-alert').innerText = calculatedFinances.frng >= 0 ? "🟢" : "🔴";

            const bfrNormEstimate = calculatedFinances.ca > 0 ? Math.round((calculatedFinances.ca / 365) * bm.bfrDays) : 180;
            document.getElementById('tbi-row-bfr').innerText = calculatedFinances.bfr + " k€";
            document.getElementById('tbi-row-bfr-norm').innerText = `Moyenne sectorielle : ~${bfrNormEstimate} k€`;
            document.getElementById('tbi-row-bfr-alert').innerText = calculatedFinances.bfr <= bfrNormEstimate * 1.3 ? "🟢" : "🟡";

            document.getElementById('tbi-row-treso').innerText = calculatedFinances.treso + " k€";
            document.getElementById('tbi-row-treso-alert').innerText = calculatedFinances.treso >= 0 ? "🟢" : "🔴";

            document.getElementById('tbi-row-ratio').innerText = calculatedFinances.ratioDette + " ans";
            document.getElementById('tbi-row-ratio-norm').innerText = `Seuil critique : ${bm.ratioMax} années`;
            const rVal = parseFloat(calculatedFinances.ratioDette);
            document.getElementById('tbi-row-ratio-alert').innerText = (isNaN(rVal) || rVal > bm.ratioMax || calculatedFinances.caf <= 0) ? "🔴" : "🟢";

            document.getElementById('tbi-out-garantie').innerText = calculatedFinances.montantGarantie + " k€ (" + calculatedFinances.garantiePct + " % du total)";
        } else {
            boxFin.classList.add('hidden');
        }

        const boxOther = document.getElementById('tbi-box-other');
        const otherImpact = document.getElementById('other-impact').value;
        if (othActive && otherImpact !== 'none') {
            boxOther.classList.remove('hidden');
            document.getElementById('tbi-out-other-title').innerText = document.getElementById('other-title').value;
            document.getElementById('tbi-out-other-desc').innerText = document.getElementById('other-desc').value;
            const impBadge = document.getElementById('tbi-out-other-impact');
            if (otherImpact === 'blocking') {
                impBadge.innerText = "Bloquant";
                impBadge.className = "font-bold text-[10px] px-1.5 py-0.5 rounded bg-red-600 text-white";
            } else if (otherImpact === 'major') {
                impBadge.innerText = "Majeur";
                impBadge.className = "font-bold text-[10px] px-1.5 py-0.5 rounded bg-amber-600 text-white";
            } else {
                impBadge.innerText = "Mineur";
                impBadge.className = "font-bold text-[10px] px-1.5 py-0.5 rounded bg-slate-300 text-slate-800";
            }
        } else {
            boxOther.classList.add('hidden');
        }

        document.getElementById('tbi-out-arb-choice').innerText = document.getElementById('arb-choice').value;
        document.getElementById('tbi-out-arb-text').innerText = document.getElementById('arb-text').value || "Aucun motif consigné.";
        document.getElementById('tbi-out-imp-fin').innerText = document.getElementById('arb-impact-fin').value;
        document.getElementById('tbi-out-imp-rh').innerText = document.getElementById('arb-impact-rh').value;
        document.getElementById('tbi-out-risk-pol').innerText = document.getElementById('arb-risk-pol').value;
    }

    function backToEdit() {
        document.getElementById('output-section').classList.add('hidden');
        document.getElementById('input-section').classList.remove('hidden');
        document.getElementById('workspace-section').classList.remove('hidden');
    }

    // Initialisation directe sur le cas de démonstration 1
    loadCaseTemplate();
</script>
</body>
</html>
