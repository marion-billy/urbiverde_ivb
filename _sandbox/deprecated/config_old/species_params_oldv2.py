"""
species_params.py
=========================
Configuration des guildes de déplacement pour l'analyse de connectivité
écologique urbaine. 

═══════════════════════════════════════════════════════════════════════════════
PRINCIPES DE CONSTRUCTION
═══════════════════════════════════════════════════════════════════════════════

1. GUILDES
   Chaque guilde couvre un syndrome fonctionnel distinct dans le paysage urbain
   (lisière, mosaïque, boisement, milieu ouvert, zones humides, herbacé fleuri,
   espace aérien nocturne). 8 guildes pour une couverture complète des niveaux
   structuraux du paysage.

2. FOURCHETTE DE FRICTION : 1 → 100 (+ np.nan pour les barrières absolues)
   · 1        : habitat optimal — tous les habitat_codes ont friction = 1
                (hypothèse "movement inside patches is free", cohérente avec
                l'approche edge-to-edge utilisée dans le graphe Gabriel)
   · 1–100    : matrix franchissable, coût croissant
   · np.nan   : barrière imperméable → np.inf dans create_resistance_surface()
                MCP_Geometric ne traversera jamais ces pixels
   Au moins une valeur non-barrière atteint 100 par guilde.

3. d0 : DISTANCE CARACTÉRISTIQUE DE MOUVEMENT (mètres)
   Ce n'est pas la distance de dispersion natale (émancipation des jeunes).
   C'est le paramètre de déclin exponentiel de la probabilité de connexion :
       prob(d) = exp(−d / d0)
   À d = d0  → prob ≈ 0.37  (connexion improbable mais possible)
   À d = 2*d0 → prob ≈ 0.13  (connexion rare)
   Convention adoptée ici : d0 = distance_max_littérature / 2
   (la distance max correspond au seuil candidat Gabriel = 2*d0)

4. INTERFACE AVEC create_resistance_surface()
   La fonction attend un seul dict friction_dict{code: cost}.
   Les barrières sont encodées comme np.nan dans ce dict :
       friction[xx] = np.nan  →  cost_matrix[raster==xx] = np.inf
       
═══════════════════════════════════════════════════════════════════════════════
CODES RASTER (WorldCover v200 + OSM)
═══════════════════════════════════════════════════════════════════════════════
10  Forêt           (Trees, WorldCover)
20  Arbustes        (Shrubland, WorldCover)
30  Prairie         (Grassland, WorldCover)
40  Agriculture     (Cropland, WorldCover)
50  Urbain diffus   (Built-up, WorldCover)
51  Bâtiments       (polygones OSM)
52  Autoroutes + voies ferrées (OSM)
53  Petites routes  (secondary/tertiary/residential OSM)
54  Chemins piétons (pedestrian/path/footway OSM)
60  Sol nu          (Bare soil / impervious, WorldCover)
80  Eau             (Permanent water, WorldCover)
90  Zones humides   (Wetlands, WorldCover)
95  Mangroves       (Mangroves, WorldCover)

═══════════════════════════════════════════════════════════════════════════════
RÉFÉRENCES
═══════════════════════════════════════════════════════════════════════════════
[1]  Balbi et al. (2021) J. Environ. Manage.
     Hérisson, Rennes, LCP empiriquement validé
[2]  Braaker et al. (2017) Landscape Ecol.
     Hérisson, Zurich, génétique des populations urbaines
[3]  Tarabon et al. (2019) Landscape Urban Plan.
     Hérisson (4 000 m), écureuil (5 000 m), blaireau (2 000 m), Lyon
[4]  Grafius et al. (2017) Landscape Ecol.
     Mésanges, villes UK, résistances Table 1
[5]  Merkens et al. / Bourgeois et al. (2023–2025) bioRxiv
     Merle noir, Munich, LCP empirique
[6]  Van Buskirk (2012) Ecol. & Evol.
     Amphibiens, Suisse, génétique
[7]  Biggs et al. (2014) Biol. Conserv.
     Triturus cristatus
[8]  Mimet et al. (2020) Landscape Urban Plan.
     Pipistrelle, Paris, jardins privés, rayon 1–3 km
[9]  Hale et al. (2012) PLOS ONE
     Chauves-souris, West Midlands UK 
[10] Voigt et al. (2019) Landscape Ecol.
     Noctule, Berlin, GPS + ALAN, corridors sombres
[11] Zurbuchen et al. (2010) J. Animal Ecol.
     Abeilles sauvages, rayon de butinage 300–600 m
[12] Hermann et al. (2023) Sci. Reports
     Pollinisateurs, prairies urbaines
[13] Foltête et al. (2024) Landsc. Urban Plan.
     Pollinisateurs, villes françaises
[14] Kaefer et al. (2010) ; Gasc et al. (2013)
     Reptiles urbains, lézard des murailles, domaine vital 100–500 m²
[15] Kirk et al. (2023) MethodsX
     7 guildes urbaines Melbourne, framework de planification
[16] Harris & Rayner (1986) J. Anim. Ecol.
     Renard urbain UK, déplacements nocturnes

"""

import numpy as np

NaN = float('nan')  # Alias lisible pour les barrières dans les dicts friction


SPECIES_CONFIG = {

    # =========================================================================
    # GUILDE 1 — Petit mammifère de lisière
    # =========================================================================
    # Syndrome : terrestre strict, spécialiste des haies et boisements.
    # Non nageur. Première cause de mortalité = routes.
    # Représente la trame verte de proximité (bocage péri-urbain, jardins).
    #
    # Espèce commune      : Hérisson d'Europe (Erinaceus europaeus)
    # Espèce charismatique: Écureuil roux (Sciurus vulgaris)
    #   Spécialiste de canopée, se déplace de boisement en boisement.
    #   Très sensible à la fragmentation. Partage habitat et barrières
    #   avec le hérisson.
    # Espèce menacée      : Musaraigne pygmée (Sorex minutus) — LC mais
    #   indicatrice de qualité de lisière
    #
    # Barrières (np.nan → np.inf) :
    #   51 bâtiments, 52 autoroutes/ferrées, 80 eau 
    # =========================================================================
    'mammal_edge': {
        'label': 'Petit mammifère de lisière',
        'description': (
            'Terrestre strict, dépendant des haies et lisières boisées. '
            'Non nageur. Mortalité routière = première menace. '
            'Représente la trame verte de proximité.'
        ),
        'habitat_codes': [10, 20, 30],
        'graph': {'d0': 1500},
        'friction': {
            10: 1,    # Forêt : habitat optimal [1][2][3]
            20: 1,    # Arbustes / haies : habitat optimal
            30: 1,    # Prairie : habitat optimal
            90: 25,   # Zones humides : sol instable, non habitat
            95: 25,   # Zones humides : sol instable, non habitat
            40: 35,   # Agriculture : découvert, risque prédation
            60: 50,   # Sol nu / imperméable
            54: 60,   # Chemins piétons : perturbation humaine
            50: 75,   # Tissu urbain diffus
            53: 100,  # Petites routes : mortalité [1] — MAX franchissable
            51: NaN,  # Bâtiments → np.inf
            52: NaN,  # Autoroutes + ferrées → np.inf
            80: NaN,  # Eau → np.inf (hérisson non nageur)
        },
        'species': {
            'common':      ('Erinaceus europaeus', 'Hérisson d\'Europe'),
            'charismatic': ('Sciurus vulgaris',    'Écureuil roux'),
            'threatened':  ('Sorex minutus',       'Musaraigne pygmée', 'LC — indicatrice lisières'),
            'refs': 'Balbi et al. (2021), Braaker et al. (2017), Tarabon et al. (2019)',
        },
    },

    # =========================================================================
    # GUILDE 2 — Mammifère généraliste de mosaïque
    # =========================================================================
    # Syndrome : généraliste de matrice, utilise toutes les classes du paysage.
    # Habitat = mosaïque complète. [16]
    # L'agriculture est une ressource (chasse aux campagnols).
    # Actif la nuit. Nage si nécessaire.
    # Représente la connexion fonctionnelle entre tous les espaces verts.
    #
    # Espèce commune      : Renard roux (Vulpes vulpes)
    # Espèce charismatique: Fouine (Martes foina)
    # Espèce menacée      : Putois d'Europe (Mustela putorius) — NT UICN
    #
    # Barrières : 51 bâtiments, 52 autoroutes.
    # =========================================================================
    'mammal_matrix': {
        'label': 'Mammifère généraliste de mosaïque',
        'description': (
            'Généraliste : utilise tous les types de couverture du sol, '
            'de la forêt aux jardins urbains. Actif la nuit. '
            'Agriculture = ressource (chasse). '
            'Représente la connexion entre tous les espaces verts.'
        ),
        'habitat_codes': [10, 20, 30, 40],
        'graph': {'d0': 2000},
        'friction': {
            10: 1,    # Forêt : habitat, gîte diurne [16]
            20: 1,    # Shrublands : habitat
            30: 1,    # Prairie : habitat, chasse (campagnols)
            40: 1,    # Agriculture : habitat, chasse active [16]
            90: 10,   # Zones humides : traversable (renard nage)
            95: 10,   # Zones humides : traversable (renard nage)
            80: 18,   # Eau : traversable à la nage
            60: 25,   # Sol nu
            54: 15,   # Chemins piétons : empruntés la nuit [16]
            50: 35,   # Tissu urbain diffus : jardins colonisés [16]
            53: 65,   # Petites routes : risque, renard traverse rapidement
            51: NaN,  # Bâtiments → np.inf
            52: NaN,  # Autoroutes + ferrées → np.inf
        },
        'species': {
            'common':      ('Vulpes vulpes',    'Renard roux'),
            'charismatic': ('Martes foina',     'Fouine'),
            'threatened':  ('Mustela putorius', 'Putois d\'Europe', 'NT UICN'),
            'refs': 'Harris & Rayner (1986)',
        },
    },

    # =========================================================================
    # GUILDE 3 — Oiseau sylvicole cavicole
    # =========================================================================
    # Syndrome : dépendant des vieux arbres à cavités pour la reproduction.
    # Se déplace en vol — routes et bâtiments = coûts d'habitat, pas barrières.
    # Indicateur de la qualité des boisements matures urbains.
    #
    # Espèce commune      : Pic épeiche (Dendrocopos major)
    # Espèce charismatique: Chouette hulotte (Strix aluco)
    #   Nocturne mais contraintes identiques : cavités de vieux arbres,
    #   chasse en lisière. Justifié par habitat et paramètres identiques [4].
    # Espèce menacée      : Verdier d'Europe (Chloris chloris) — VU UICN Europe
    #
    # barrier_codes = aucun (oiseaux volants).
    # =========================================================================
    'bird_woodland': {
        'label': 'Oiseau sylvicole cavicole',
        'description': (
            'Dépendant des vieux arbres à cavités. '
            'Routes et bâtiments = coûts d\'habitat, pas barrières physiques.'
        ),
        'habitat_codes': [10, 20],
        'graph': {'d0': 1000},
        'friction': {
            10: 1,    # Forêt mature : habitat optimal [4]
            20: 1,    # Arbustes : habitat (alimentation, couvert)
            30: 20,   # Prairie : alimentation occasionnelle
            90: 25,   # Zones humides
            95: 25,   # Zones humides
            80: 22,   # Eau : traversable en vol
            40: 35,   # Agriculture
            60: 42,   # Sol nu
            54: 22,   # Chemins piétons
            50: 60,   # Tissu urbain diffus
            53: 72,   # Petites routes : bruit [4]
            52: 88,   # Autoroutes : bruit fort, franchissable en vol
            51: 100,  # Bâtiments : sans cavité, sans ressource — MAX franchissable
        },
        'species': {
            'common':      ('Dendrocopos major', 'Pic épeiche'),
            'charismatic': ('Strix aluco',       'Chouette hulotte'),
            'threatened':  ('Chloris chloris',   'Verdier d\'Europe', 'VU UICN Europe'),
            'refs': 'Grafius et al. (2017), Kirk et al. (2023)',
        },
    },

    # =========================================================================
    # GUILDE 4 — Oiseau généraliste de la mosaïque urbaine
    # =========================================================================
    # Syndrome : très adapté à l'hétérogénéité urbaine, exploite tous les
    # types d'espaces verts. Le martinet gîte dans les bâtiments.
    # Aucune barrière physique absolue.
    #
    # Espèce commune      : Merle noir (Turdus merula)
    # Espèce charismatique: Faucon crécerelle (Falco tinnunculus)
    # Espèce menacée      : Martinet noir (Apus apus) — VU France
    #
    # barrier_codes = aucun.
    # =========================================================================
    'bird_generalist': {
        'label': 'Oiseau généraliste de la mosaïque urbaine',
        'description': (
            'Très adapté à l\'hétérogénéité urbaine.'
            'Bâtiments = gîte potentiel (martinet, crécerelle)'
            'Aucune barrière physique absolue.'
        ),
        'habitat_codes': [10, 20, 30],
        'graph': {'d0': 3000},
        'friction': {
            10: 1,    # Forêt : habitat [5]
            20: 1,    # Arbustes : habitat
            30: 1,    # Prairie : habitat, chasse au sol [5]
            90: 6,    # Zones humides
            95: 6,    # Zones humides
            80: 8,    # Eau : ripisylve, ressource
            40: 12,   # Agriculture
            60: 18,   # Sol nu
            54: 10,   # Chemins piétons
            51: 30,   # Bâtiments : gîte martinet/crécerelle → friction modérée
            50: 22,   # Tissu urbain diffus : merle très adapté [5]
            53: 38,   # Petites routes
            52: 100,  # Autoroutes : bruit + thermique — MAX franchissable
        },
        'species': {
            'common':      ('Turdus merula',     'Merle noir'),
            'charismatic': ('Falco tinnunculus', 'Faucon crécerelle'),
            'threatened':  ('Apus apus',         'Martinet noir', 'VU France'),
            'refs': 'Merkens et al. (2023), Bourgeois et al. (2025)',
        },
    },

    # =========================================================================
    # GUILDE 5 — Amphibien aquatique-terrestre
    # =========================================================================
    # Syndrome : double dépendance eau (reproduction) + terrestre (hivernage).
    # Très faible portée. Routes = barrière mortelle (migrations printanières).
    # Sol imperméable = dessiccation rapide de la peau.
    # Arbustes (20) = matrice franchissable, pas habitat
    #   (ni reproduction ni hivernage préférentiel).
    #
    # Espèce commune      : Crapaud commun (Bufo bufo)
    # Espèce charismatique: Grenouille rousse (Rana temporaria)
    # Espèce menacée      : Triton crêté (Triturus cristatus) — NT, Dir. Hab. II/IV
    #
    # Barrières : 51, 52, 53 (routes toutes catégories = mortalité en masse).
    # =========================================================================
    'amphibian': {
        'label': 'Amphibien aquatique-terrestre',
        'description': (
            'Double dépendance : eau pour la reproduction, terrestre pour l\'hivernage. '
            'Routes = barrière mortelle (migrations printanières). '
            'Indicateur de la continuité des mares et de la trame bleue.'
        ),
        'habitat_codes': [10, 30, 80, 90],
        'graph': {'d0': 400},
        'friction': {
            90: 1,    # Zones humides : habitat reproduction [6]
            95: 1,    # Zones humides : habitat reproduction [6]
            80: 1,    # Eau : habitat reproduction
            10: 1,    # Forêt : habitat hivernage [6]
            30: 1,    # Prairie humide : habitat
            20: 12,   # Arbustes : matrix, ni reproduction ni hivernage préférentiel
            40: 40,   # Agriculture : dessiccation, pesticides
            60: 75,   # Sol nu / imperméable : dessiccation critique
            54: 65,   # Chemins piétons : risque mortalité
            50: 100,  # Tissu urbain : imperméable, sec — MAX franchissable
            51: NaN,  # Bâtiments → np.inf
            52: NaN,  # Autoroutes → np.inf
            53: NaN,  # Petites routes → np.inf (mortalité en masse)
        },
        'species': {
            'common':      ('Bufo bufo',          'Crapaud commun'),
            'charismatic': ('Rana temporaria',    'Grenouille rousse'),
            'threatened':  ('Triturus cristatus', 'Triton crêté', 'NT Dir. Hab. II/IV'),
            'refs': 'Van Buskirk (2012), Biggs et al. (2014)',
        },
    },

    # =========================================================================
    # GUILDE 6 — Reptile thermophile de milieux ouverts
    # =========================================================================
    # Syndrome : ectotherme, dépendant des surfaces ensoleillées.
    # Sol nu et dalles = habitat optimal (thermorégulation).
    # Forêt fermée = matrice froide et ombragée
    # Eau = barrière (non aquatique).
    #
    # Espèce commune      : Lézard des murailles (Podarcis muralis)
    # Espèce charismatique: Orvet fragile (Anguis fragilis)
    # Espèce menacée      : Couleuvre d'Esculape (Zamenis longissimus) — Ann. IV
    #
    # Barrières : 51, 52, 53 (routes), 80 (eau).
    # =========================================================================
    'reptile': {
        'label': 'Reptile thermophile de milieux ouverts',
        'description': (
            'Ectotherme dépendant des surfaces ensoleillées. '
            'Sol nu et talus exposés = habitat optimal. '
            'Forêt fermée = matrice froide défavorable. '
            'Groupe le plus sensible à la fragmentation urbaine [15].'
        ),
        'habitat_codes': [20, 30, 60],
        'graph': {'d0': 300},
        'friction': {
            60: 1,    # Sol nu : thermorégulation optimale [14]
            30: 1,    # Prairie rase ensoleillée : habitat
            20: 1,    # Arbustes : habitat (refuge thermique, chasse insectes)
            40: 20,   # Agriculture
            54: 25,   # Chemins piétons : dalles = habitat potentiel
            90: 50,   # Zones humides : humidité défavorable
            95: 50,   # Zones humides : humidité défavorable
            50: 62,   # Tissu urbain : jardins exposés = potentiel
            10: 100,  # Forêt fermée : ombre, humidité — MAX franchissable [14]
            51: NaN,  # Bâtiments → np.inf
            52: NaN,  # Autoroutes → np.inf
            53: NaN,  # Petites routes → np.inf (mortalité directe)
            80: NaN,  # Eau → np.inf (reptile terrestre non aquatique)
        },
        'species': {
            'common':      ('Podarcis muralis',    'Lézard des murailles'),
            'charismatic': ('Anguis fragilis',     'Orvet fragile'),
            'threatened':  ('Zamenis longissimus', 'Couleuvre d\'Esculape', 'Ann. IV Dir. Hab.'),
            'refs': 'Kaefer et al. (2010), Kirk et al. (2023)',
        },
    },

    # =========================================================================
    # GUILDE 7 — Insecte pollinisateur herbacé
    # =========================================================================
    # Syndrome : volant, dépendant des ressources florales.
    # Sol nu = habitat de nidification terricole pour abeilles solitaires.
    # Forêt dense = matrice (peu de fleurs).
    # Arbustes en fleurs = habitat (nidification cavicole, ressource florale).
    #
    # Espèce commune      : Abeille domestique (Apis mellifera)
    # Espèce charismatique: Bourdon des prés (Bombus pratorum)
    # Espèce menacée      : Andrena fulva / Osmia cornuta — VU liste rouge France
    #
    # barrier_codes = aucun (insecte volant).
    # =========================================================================
    'pollinator': {
        'label': 'Insecte pollinisateur herbacé',
        'description': (
            'Dépendant des ressources florales. '
            'Sol nu = habitat de nidification terricole. '
            '51 et 52 = friction élevée mais pas barrière (survol possible). '
            'Connectivité 3D non modélisée — limite à déclarer.'
        ),
        'habitat_codes': [20, 30, 60, 90],
        'graph': {'d0': 500},
        'friction': {
            30: 1,    # Prairie fleurie : habitat optimal [11][12]
            20: 1,    # Arbustes en fleurs : habitat (nidification, ressource)
            60: 1,    # Sol nu : habitat de nidification terricole [12]
            90: 1,    # Zones humides : habitat (flore hygrophile)
            95: 1,    # Zones humides : habitat (flore hygrophile)
            80: 22,   # Eau : traversable en vol
            54: 15,   # Chemins piétons
            40: 28,   # Agriculture intensive : pesticides [12]
            50: 42,   # Tissu urbain diffus : jardins potentiels
            10: 55,   # Forêt fermée : peu de fleurs
            53: 68,   # Petites routes
            52: 100,  # Autoroutes : vent, pollution — MAX franchissable
            51: NaN,   # Bâtiments : ressources réduites, connectivité 3D réduite [12]
        },
        'species': {
            'common':      ('Apis mellifera',              'Abeille domestique'),
            'charismatic': ('Bombus pratorum',             'Bourdon des prés'),
            'threatened':  ('Andrena fulva / Osmia cornuta', 'Abeilles solitaires', 'VU liste rouge Fr.'),
            'refs': 'Foltête et al. (2024), Hermann et al. (2023), Zurbuchen et al. (2010)',
        },
    },

    # =========================================================================
    # GUILDE 8 — Chiroptère insectivore nocturne
    # =========================================================================
    # Syndrome : actif la nuit, utilise l'écholocation.
    # Eau = habitat de chasse optimal (insectes en surface).
    #
    # 51 et 52 ne sont pas barrières ?
    #   La chauve-souris vole au-dessus des routes et bâtiments.
    #   La vraie barrière est l'ALAN (pollution lumineuse), non modélisable ici.
    #   Friction haute (80–100) sans np.inf.
    #   LIMITE : ALAN non modélisé → surestimation de la connectivité
    #
    # Espèce commune      : Pipistrelle commune (Pipistrellus pipistrellus)
    # Espèce charismatique: Noctule commune (Nyctalus noctula)
    # Espèce menacée      : Petit rhinolophe (Rhinolophus hipposideros) — NT Dir. Hab. II/IV
    #
    # barrier_codes = aucun (chiroptère volant).
    # =========================================================================
    'bat': {
        'label': 'Chiroptère insectivore nocturne',
        'description': (
            'Actif la nuit. Eau = habitat de chasse optimal. '
            'Arbustes = zone de chasse en lisière [9]. '
            '51 et 52 = friction haute (ALAN comportemental), pas barrière physique. '
            '⚠ Limite : ALAN non modélisé → résultats à interpréter avec précaution.'
        ),
        'habitat_codes': [10, 80, 90, 30],
        'graph': {'d0': 2500},
        'friction': {
            10: 1,    # Forêt : gîtes arboricoles, corridors de vol [8]
            80: 1,    # Eau : chasse optimale [9][10]
            90: 1,    # Zones humides : habitat, chasse active
            95: 1,    # Zones humides : habitat, chasse active
            30: 1,    # Prairie : habitat, insectes nocturnes
            20: 8,    # Arbustes : zone de chasse en lisière [9]
            40: 22,   # Agriculture : ressources réduites, pesticides
            60: 32,   # Sol nu
            54: 25,   # Chemins piétons sombres : corridors nocturnes [10]
            50: 48,   # Tissu urbain diffus : pipistrelle tolère [9]
            53: 68,   # Petites routes : ALAN + bruit
            51: 80,   # Bâtiments : ALAN, sans ressource nocturne
            52: 100,  # Autoroutes éclairées : ALAN fort + bruit — MAX franchissable [10]
        },
        'species': {
            'common':      ('Pipistrellus pipistrellus', 'Pipistrelle commune'),
            'charismatic': ('Nyctalus noctula',          'Noctule commune'),
            'threatened':  ('Rhinolophus hipposideros',  'Petit rhinolophe', 'NT Dir. Hab. II/IV'),
            'refs': 'Mimet et al. (2020), Hale et al. (2012), Voigt et al. (2019)',
        },
    },
}

# =============================================================================
LC_MAP = {
    10: 'Forêt', 20: 'Arbustes', 30: 'Prairie', 40: 'Agriculture',
    50: 'Urbain diffus', 51: 'Bâtiments', 52: 'Autoroutes/Ferrées',
    53: 'Petites routes', 54: 'Chemins piétons', 60: 'Sol nu',
    80: 'Eau', 90: 'Zones humides', 95: 'Mangroves'
}

def get_summary_df():
    """Retourne un DataFrame pandas de synthèse des guildes."""
    import pandas as pd
    rows = []
    for key, g in SPECIES_CONFIG.items():
        frictions = {k: v for k, v in g['friction'].items() if not (isinstance(v, float) and np.isnan(v))}
        barriers  = [k for k, v in g['friction'].items() if isinstance(v, float) and np.isnan(v)]
        rows.append({
            'clé':           key,
            'guilde':        g['label'],
            'd0 (m)':        g['graph']['d0'],
            'habitat':       g['habitat_codes'],
            'barrières':     barriers,
            'espèce commune':    g['species']['common'][1],
            'charismatique':     g['species']['charismatic'][1],
            'menacée':           g['species']['threatened'][1],
            'réfs':              g['species']['refs'],
        })
    return pd.DataFrame(rows)

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

def prepare_data(config):
    """Transforme le dictionnaire SPECIES_CONFIG en DataFrame long format."""
    rows = []
    for guild_key, guild_info in config.items():
        for code, friction in guild_info['friction'].items():
            rows.append({
                'Guilde': guild_info['label'],
                'Code': code,
                'Label': LC_MAP.get(code, str(code)),
                'Friction': friction,
                'Habitat_Codes': guild_info['habitat_codes']
            })
    return pd.DataFrame(rows)

def get_color(row):
    """Logique de couleur : Rouge (Barrière), Vert (Habitat), Gris (Matrice)."""
    if np.isnan(row['Friction']):
        return '#FF6B6B' # Rouge
    if row['Code'] in row['Habitat_Codes']:
        return '#51CF66' # Vert
    return '#ADB5BD' # Gris (Matrice)
    
def plot_friction_by_guild(df):
    """Affiche un graphe par guilde avec étiquettes des valeurs."""
    g = sns.FacetGrid(df, col="Guilde", col_wrap=2, height=3, aspect=2, sharex=False)
    
    def plot_bars(data, **kwargs):
        ax = plt.gca()
        colors = [get_color(r) for _, r in data.iterrows()]
        plot_data = data.copy()
        plot_data['Friction'] = plot_data['Friction'].fillna(110)
        
        # Création des barres
        containers = sns.barplot(data=plot_data, x='Label', y='Friction', palette=colors, ax=ax)
        
        # Ajout des labels
        # Si la valeur est >= 100 (barrière), on écrit "Inf", sinon la valeur entière
        for c in ax.containers:
            ax.bar_label(c, fmt=lambda x: 'Inf' if x >= 100 else f'{x:.0f}', padding=3)
            
        plt.xticks(rotation=45, ha='right')

    g.map_dataframe(plot_bars)
    g.fig.suptitle('Friction par Guilde (Vert=Habitat, Rouge=Barrière)', y=1.02)
    plt.tight_layout()
    plt.show()

def plot_friction_by_landcover(df):
    """Affiche un graphe comparatif par landcover avec étiquettes."""
    plt.figure(figsize=(15, 6))
    
    # Préparation données
    df_plot = df.copy()
    df_plot['Friction'] = df_plot['Friction'].fillna(110)
    
    ax = sns.barplot(data=df_plot, x='Label', y='Friction', hue='Guilde')
    
    # Ajout des labels
    for c in ax.containers:
        # On n'affiche pas les valeurs pour éviter la surcharge visuelle sur ce graphe dense
        # ou alors on utilise une taille de police plus petite
        ax.bar_label(c, fmt=lambda x: 'Inf' if x >= 100 else f'{x:.0f}', padding=3, fontsize=8, rotation=90)
        
    plt.xticks(rotation=45, ha='right')
    plt.title('Comparaison des frictions par type de couverture du sol')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

# Utilisation :
# df = prepare_data(SPECIES_CONFIG)
# plot_friction_by_guild(df)
# plot_friction_by_landcover(df)