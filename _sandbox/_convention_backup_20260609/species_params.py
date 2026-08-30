"""
species_params.py
=========================
Configuration des espèces chimères pour l'analyse de connectivité
écologique urbaine basée sur observation satellite.

═══════════════════════════════════════════════════════════════════════════════
CADRE MÉTHODOLOGIQUE
═══════════════════════════════════════════════════════════════════════════════

Approche : guildes fonctionnelles définies par syndromes d'usage de l'habitat,
ancrées sur des espèces représentatives à valeur illustrative (non modélisées
individuellement).

Distinctions explicites :

  - Pas d'approche espèce focale : les frictions ne représentent pas le
    comportement d'une espèce unique, mais le syndrome écologique commun à
    un ensemble d'espèces partageant ces préférences d'habitat.
    L'espèce nommée (Hérisson, Écureuil, etc.) sert d'ancrage cognitif pour
    rendre la guilde nommable et communicable, pas d'objet de modélisation.

  - Pas d'approche cortège-par-sous-trame (CEREMA) : on ne moyenne pas les
    frictions de plusieurs espèces au sein d'une sous-trame d'habitat. Le
    découpage en sous-trames (Arborée / Mixte / Herbacée / etc.) suppose une
    granularité de classification du paysage (OCS GE, BD Topo, RPG) qui n'est
    pas disponible sur observation satellite globale (WorldCover 10m + OSM).
    La distinction Arborée vs Mixte n'a pas de support spatial dans nos
    données.

═══════════════════════════════════════════════════════════════════════════════
CALIBRATION
═══════════════════════════════════════════════════════════════════════════════

Frictions empruntées au Tableau CEREMA La Rochelle (2025, pp. 96-98) pour
l'espèce de référence de chaque guilde. Ces valeurs sont réinterprétées comme
caractérisant le syndrome écologique de la guilde, pas l'individu de
l'espèce nommée.

Distances de dispersion : Tableau 8 p44 CEREMA, colonne "Distance max entrée"
du cortège dont fait partie l'espèce de référence.

Habitat (codes dans habitat_codes) : FORCÉ à friction 1.
  Hypothèse structurelle de calculate_pc_index_lcp : un trajet en habitat pur
  doit retomber sur prob = exp(-d/d0). Quand CEREMA assigne 2-6 à un code que
  nous considérons habitat de la guilde, nous ramenons à 1. Cette agrégation
  est cohérente avec la résolution plus grossière de nos données : nous ne
  pouvons pas distinguer prairie permanente (CEREMA = 2) de prairie temporaire
  (CEREMA = 3) dans le code WorldCover 30.

Barrières : encodées en np.nan (→ np.inf dans create_resistance_surface).
  Pour les codes que CEREMA met à 100 et que nous voulons traiter comme
  infranchissables. NaN ≠ 100 dans notre convention.

═══════════════════════════════════════════════════════════════════════════════
LIMITES CONNUES
═══════════════════════════════════════════════════════════════════════════════

  - Voies ferrées agrégées avec autoroutes dans le code 52. CEREMA distingue
    (ferrées = 10, autoroutes = 100). Non corrigeable sans split du code 52
    dans landcover.py.

  - Surfaces d'eau (code 80) traitées comme barrière (NaN) pour les guildes
    terrestres (ground_mammal, ground_reptile) bien que les fiches CEREMA
    indiquent que ces espèces peuvent nager (Hérisson p93, Lézard p89).
    Justification : WorldCover 10m ne capture que les surfaces d'eau
    permanentes de grande taille. Petits étangs, fossés et ruisselets ne
    sont pas représentés. Les pixels code 80 correspondent donc à des
    obstacles équivalents aux "canaux principaux" CEREMA (= 100), pas aux
    "surfaces d'eau" CEREMA (= 8-9). NaN cohérent avec cette agrégation.

  - Pas de granularité dans la zone favorable. Toutes les prairies = code 30,
    tous les boisements = code 10. Perte de signal CEREMA sur les sous-classes.

  - Validation terrain non implémentée. Une guilde se valide en principe sur
    des données d'occurrence multi-espèces (GBIF, INPN) couvrant l'ensemble
    des espèces représentatives, pas une seule.

  - Guildes chimères (generalist_mammal, wetland_amphibian, aerial_bat) :
    pas d'équivalent CEREMA. Frictions calibrées sur littérature propre.
    Marquées _chimera_no_cerema_ref. Ne pas utiliser pour comparaison
    méthodologique avec CEREMA.

═══════════════════════════════════════════════════════════════════════════════
"""

import numpy as np

NaN = float('nan')

# =============================================================================
# CONSTANTES MÉTHODOLOGIQUES
# =============================================================================
# Friction favorable moyenne — convention CEREMA Tab. 8 p44.
# Représente la friction moyenne attendue le long d'un corridor plausible
# (mix habitat + matrice favorable). Utilisée pour convertir une distance
# de dispersion en seuil de coût accumulé :
#     threshold_UC = d0 × FRICTION_AVG_FAVORABLE
FRICTION_AVG_FAVORABLE = 3

# =============================================================================
# CODES D'OCCUPATION DU SOL
# =============================================================================

LC_MAP = {
    10: 'Forêt', 20: 'Arbustes', 30: 'Prairie', 40: 'Agriculture',
    50: 'Urbain diffus', 51: 'Bâtiments', 52: 'Autoroutes',
    53: 'Petites routes', 54: 'Chemins piétons', 55: 'Voies ferrées',
    60: 'Sol nu', 80: 'Eau', 90: 'Zones humides', 95: 'Mangroves'
}
# =============================================================================
# CONFIGURATION DES GUILDES
# =============================================================================

SPECIES_CONFIG = {

    # =========================================================================
    # GROUND_MAMMAL — Syndrome mammifère terrestre de lisière
    # Réf. calibrage : Hérisson d'Europe (CEREMA Mixte, Tab. 8)
    # =========================================================================
    'ground_mammal': {
        'label': 'Mammifère terrestre de lisière',
        'description': (
            'Syndrome fonctionnel : petits mammifères terrestres dépendants '
            'des haies, lisières basses et prairies. Mortalité routière '
            'comme première menace.'
        ),
        'habitat_codes': [10, 20, 30],
        'graph': {'d0': 3000},
        'friction': {
            # Habitat (CEREMA Hérisson 1-3, forcé à 1)
            10: 1, 20: 1, 30: 1,
            # Matrice (CEREMA Hérisson)
            40: 7,     # Cultures
            54: 5,     # Chemins (proxy chemins agricoles CEREMA = 5)
            60: 10,    # Sol nu
            90: 9, 95: 9,   # Zones humides (proxy surfaces eau)
            50: 10,    # Urbain (CEREMA "bâti fréquente bords routes")
            53: 50,    # Petites routes
            55: 10,    # Voies ferrées
            # Barrières (CEREMA 100 → NaN)
            80: NaN,   # Eau
            51: NaN,   # Bâti
            52: NaN,   # Autoroutes + ferrées
        },
        'reference_species_cerema': ('Erinaceus europaeus', 'Hérisson d\'Europe'),
        'representative_species': [
            ('Erinaceus europaeus', 'Hérisson d\'Europe'), # Tarabon et al. 2019, d0 : 4km
            ('Sorex minutus',       'Musaraigne pygmée'),
            ('Apodemus sylvaticus', 'Mulot sylvestre'),
            ('Mustela nivalis',     'Belette d\'Europe'),
        ],
        'refs': (
            'Frictions : CEREMA La Rochelle (2025) pp. 96-98 col. Hérisson. '
            'Distance d0 : Tab. 8 p44 (cortège Mixte). '
            'Cadre guilde fonctionnelle : approche propre (cette étude).'
        ),
    },

    # =========================================================================
    # ARBOREAL_MAMMAL — Syndrome mammifère arboricole
    # Réf. calibrage : Écureuil roux (CEREMA Arborée, Tab. 8 d0=1500)
    # NOTE : habitat = forêt seule. Les arbustes deviennent matrice.
    # =========================================================================
    'arboreal_mammal': {
        'label': 'Mammifère arboricole de canopée',
        'description': (
            'Syndrome fonctionnel : mammifères strictement arboricoles, '
            'dépendants de la canopée forestière continue. Se déplacent '
            'd\'arbre en arbre, très sensibles à la fragmentation. '
            'Habitat restreint à la forêt stricte ; arbustes sont matrice.'
        ),
        'habitat_codes': [10],
        'graph': {'d0': 2000},
        'friction': {
            # Habitat
            10: 1,     # Forêt (CEREMA Écureuil boisements 1-3, forcé à 1)
            # Matrice (CEREMA Écureuil)
            20: 6,     # Arbustes (CEREMA = 6, formation arbustive)
            30: 4,     # Prairies (CEREMA prairies écureuil = 4-5)
            40: 8,     # Cultures (CEREMA = 8)
            54: 8,
            60: 10,    # Sol nu (CEREMA = 10)
            90: 9, 95: 9,
            80: 9,     # Eau (CEREMA = 9, ripisylve traversée)
            50: 50,    # Urbain (CEREMA bâti = 100 ; ici on tolère couloirs verts urbains)
            53: 50,    # Routes (CEREMA = 50)
            55: 9,    # Voies ferrées
            # Pas barrières absolues (arboricole, mais saut au sol possible)
            52: NaN,   # Autoroutes + ferrées (CEREMA autoroutes = 100)
            51: NaN,   # Bâti (CEREMA = 100)
        },
        'reference_species_cerema': ('Sciurus vulgaris', 'Écureuil roux'),
        'representative_species': [
            ('Sciurus vulgaris',         'Écureuil roux'),
            ('Glis glis',                'Loir gris'),
            ('Muscardinus avellanarius', 'Muscardin'),
            ('Eliomys quercinus',        'Lérot'),
        ],
        'refs': (
            'Frictions : CEREMA La Rochelle (2025) pp. 96-98 col. Écureuil. '
            'Distance d0 : Tab. 8 p44 (cortège Arborée/Arbustive). '
            'Cadre guilde fonctionnelle : approche propre (cette étude).'
        ),
    },

    # =========================================================================
    # FOREST_EDGE_BIRD — Syndrome oiseau de mosaïque boisée
    # Réf. calibrage : Fauvette à tête noire (CEREMA Arborée, Tab. 8 d0=1500)
    # =========================================================================
    'forest_edge_bird': {
        'label': 'Oiseau de mosaïque boisée',
        'description': (
            'Syndrome fonctionnel : oiseaux insectivores mobiles inféodés '
            'aux lisières boisées et fourrés arbustifs. Volants : aucune '
            'barrière mortelle absolue. Friction modérée sur urbain.'
        ),
        'habitat_codes': [10, 20],
        'graph': {'d0': 1500},
        'friction': {
            # Habitat (CEREMA Fauvette 1-3, forcé à 1)
            10: 1, 20: 1,
            # Matrice (CEREMA Fauvette)
            30: 7,     # Prairie (CEREMA Fauvette = 7 ; hors habitat pour cette guilde)
            40: 8,     # Cultures (CEREMA = 8)
            54: 6,
            60: 10,    # Sol nu (CEREMA = 10)
            90: 7, 95: 7,
            80: 7,     # Eau (CEREMA = 7)
            50: 10,    # Urbain (CEREMA "bâti fréquente bords" = 10)
            53: 50,    # Routes (CEREMA = 50)
            55: 7,    # Voies ferrées
            # Volant : friction max, pas de barrière mortelle
            52: 100,   # Autoroutes + ferrées
            51: 100,   # Bâti
        },
        'reference_species_cerema': ('Sylvia atricapilla', 'Fauvette à tête noire'),
        'representative_species': [
            ('Sylvia atricapilla', 'Fauvette à tête noire'),
            ('Erithacus rubecula', 'Rougegorge familier'),
            ('Sylvia communis',    'Fauvette grisette'),
            ('Turdus philomelos',  'Grive musicienne'),
        ],
        'refs': (
            'Frictions : CEREMA La Rochelle (2025) pp. 96-98 col. Fauvette. '
            'Distance d0 : Tab. 8 p44 (cortège Arborée/Arbustive). '
            'Cadre guilde fonctionnelle : approche propre (cette étude).'
        ),
    },

    # =========================================================================
    # GROUND_REPTILE — Syndrome reptile thermophile
    # Réf. calibrage : Lézard des murailles (CEREMA Herbacée, Tab. 8 d0=500)
    # =========================================================================
    'ground_reptile': {
        'label': 'Reptile thermophile de milieux ouverts',
        'description': (
            'Syndrome fonctionnel : reptiles ectothermes dépendants des '
            'surfaces ensoleillées. Sol nu, talus exposés et prairies rases '
            'comme habitat. Forêt fermée défavorable. Mortalité routière '
            'directe sur toutes catégories de routes.'
        ),
        'habitat_codes': [20, 30, 60],
        'graph': {'d0': 750},
        'friction': {
            # Habitat (CEREMA Lézard sol nu 3, prairie 1-2, arbustes 4, forcé à 1)
            60: 1, 30: 1, 20: 1,
            # Matrice (CEREMA Lézard)
            40: 6,     # Cultures (CEREMA = 6)
            54: 3,
            10: 8,     # Forêt fermée (CEREMA = 4-8, défavorable)
            90: 10, 95: 10,   # Zones humides : humidité défavorable
            50: 10,    # Urbain
            55: 3,    # Voies ferrées
            # Barrières (CEREMA 100 + choix Marion non aquatique)
            80: NaN,   # Eau (reptile terrestre strict)
            51: NaN,   # Bâti
            52: NaN,   # Autoroutes + ferrées
            53: NaN,   # Petites routes (mortalité directe)
        },
        'reference_species_cerema': ('Podarcis muralis', 'Lézard des murailles'),
        'representative_species': [
            ('Podarcis muralis',    'Lézard des murailles'),
            ('Anguis fragilis',     'Orvet fragile'),
            ('Zamenis longissimus', 'Couleuvre d\'Esculape'),
            ('Lacerta bilineata',   'Lézard à deux raies'),
        ],
        'refs': (
            'Frictions : CEREMA La Rochelle (2025) pp. 96-98 col. Lézard. '
            'Distance d0 : Tab. 8 p44 (cortège Herbacée). '
            'Cadre guilde fonctionnelle : approche propre (cette étude).'
        ),
    },

    # =========================================================================
    # HERBACEOUS_INSECT — Syndrome insecte des milieux herbacés
    # Réf. calibrage : Orthoptères (CEREMA Herbacée, Tab. 8 d0=500)
    # =========================================================================
    'herbaceous_insect': {
        'label': 'Insecte des milieux herbacés ouverts',
        'description': (
            'Syndrome fonctionnel : insectes sauteurs/volants dépendants '
            'des prairies ouvertes, sols nus pour nidification, arbustes '
            'pour refuge. Mobilité limitée mais d0 du cortège CEREMA = 500 m.'
        ),
        'habitat_codes': [20, 30, 60, 90, 95],
        'graph': {'d0': 300},
        'friction': {
            # Habitat (CEREMA Orthoptères 1-5, forcé à 1)
            30: 1, 20: 1, 60: 1, 90: 1, 95: 1,
            # Matrice (CEREMA Orthoptères)
            40: 5,     # Cultures (CEREMA = 5)
            54: 2,
            10: 8,     # Forêt fermée (CEREMA = 8)
            50: 10,    # Urbain
            80: 10,    # Eau (CEREMA = 100, mais Orthoptères volants tolèrent)
            53: 50,    # Routes (CEREMA = 50)
            55: 3,    # Voies ferrées
            # Barrières
            52: 100,   # Autoroutes + ferrées
            51: NaN,   # Bâti (CEREMA = 100, NaN car ressources nulles)
        },
        'reference_species_cerema': ('Chorthippus brunneus', 'Criquet duettiste'),
        'representative_species': [
            ('Chorthippus brunneus',     'Criquet duettiste'),
            ('Tessellana tessellata',    'Decticelle carroyée'),
            ('Pseudochorthippus parallelus', 'Criquet des pâtures'),
            ('Apis mellifera',           'Abeille domestique'),
            ('Bombus pratorum',          'Bourdon des prés'),
        ],
        'refs': (
            'Frictions : CEREMA La Rochelle (2025) pp. 96-98 col. Orthoptères. '
            'Distance d0 : Tab. 8 p44 (cortège Herbacée). '
            'Cadre guilde fonctionnelle : approche propre (cette étude).'
        ),
    },
}

#     # =========================================================================
#     # ───────────── GUILDES CHIMÈRES (sans équivalent CEREMA) ─────────────
#     # Calibration héritée littérature propre. Pas de comparaison directe avec
#     # CEREMA possible.
#     # =========================================================================

#     'generalist_mammal': {
#         '_chimera_no_cerema_ref': True,
#         'label': '[CHIMERA] Mammifère généraliste de mosaïque',
#         'description': (
#             'CHIMÈRE — pas d\'équivalent CEREMA. Mammifères généralistes '
#             'tolérant tous les types de couverture, y compris urbain diffus. '
#             'Actifs la nuit. Agriculture = ressource (chasse).'
#         ),
#         'habitat_codes': [10, 20, 30, 40],
#         'graph': {'d0': 2000},
#         'friction': {
#             10: 1, 20: 1, 30: 1, 40: 1,
#             90: 10, 95: 10, 80: 18, 60: 25,
#             54: 15, 50: 35, 53: 65,
#             51: NaN, 52: NaN,
#         },
#         'reference_species_cerema': None,
#         'representative_species': [
#             ('Vulpes vulpes',    'Renard roux'),
#             ('Martes foina',     'Fouine'),
#             ('Meles meles',      'Blaireau européen'),
#             ('Mustela putorius', 'Putois d\'Europe'),
#         ],
#         'refs': 'Harris & Rayner (1986). Pas d\'équivalent CEREMA.',
#     },

#     'wetland_amphibian': {
#         '_chimera_no_cerema_ref': True,
#         'label': '[CHIMERA] Amphibien aquatique-terrestre',
#         'description': (
#             'CHIMÈRE — CEREMA n\'a pas modélisé d\'amphibiens. Double '
#             'dépendance eau (reproduction) + terrestre (hivernage). '
#             'Routes = barrière mortelle (migrations printanières).'
#         ),
#         'habitat_codes': [10, 30, 80, 90],
#         'graph': {'d0': 400},
#         'friction': {
#             90: 1, 95: 1, 80: 1, 10: 1, 30: 1,
#             20: 12, 40: 40, 60: 75, 54: 65, 50: 100,
#             51: NaN, 52: NaN, 53: NaN,
#         },
#         'reference_species_cerema': None,
#         'representative_species': [
#             ('Bufo bufo',          'Crapaud commun'),
#             ('Rana temporaria',    'Grenouille rousse'),
#             ('Triturus cristatus', 'Triton crêté'),
#             ('Salamandra salamandra', 'Salamandre tachetée'),
#         ],
#         'refs': 'Van Buskirk (2012), Biggs et al. (2014). Pas dans CEREMA.',
#     },

#     'aerial_bat': {
#         '_chimera_no_cerema_ref': True,
#         'label': '[CHIMERA] Chiroptère insectivore nocturne',
#         'description': (
#             'CHIMÈRE — CEREMA n\'a pas modélisé de chiroptères. Actifs la '
#             'nuit, eau = habitat de chasse optimal. Limite ALAN (pollution '
#             'lumineuse) non modélisée → friction haute comportementale sur '
#             '51, 52 sans np.inf.'
#         ),
#         'habitat_codes': [10, 80, 90, 30],
#         'graph': {'d0': 2500},
#         'friction': {
#             10: 1, 80: 1, 90: 1, 95: 1, 30: 1,
#             20: 8, 40: 22, 60: 32, 54: 25,
#             50: 48, 53: 68, 51: 80, 52: 100,
#         },
#         'reference_species_cerema': None,
#         'representative_species': [
#             ('Pipistrellus pipistrellus', 'Pipistrelle commune'),
#             ('Nyctalus noctula',          'Noctule commune'),
#             ('Rhinolophus hipposideros',  'Petit rhinolophe'),
#             ('Myotis daubentonii',        'Murin de Daubenton'),
#         ],
#         'refs': 'Mimet et al. (2020), Voigt et al. (2019). Pas dans CEREMA.',
#     },
# }


# =============================================================================
# UTILITAIRES
# =============================================================================

def get_summary_df():
    """DataFrame de synthèse des guildes."""
    import pandas as pd
    rows = []
    for key, g in SPECIES_CONFIG.items():
        barriers = [k for k, v in g['friction'].items()
                    if isinstance(v, float) and np.isnan(v)]
        ref_sp = g.get('reference_species_cerema')
        rows.append({
            'clé':            key,
            'guilde':         g['label'],
            'chimère':        g.get('_chimera_no_cerema_ref', False),
            'd0 (m)':         g['graph']['d0'],
            'threshold (UC)': g['graph']['d0'] * FRICTION_AVG_FAVORABLE,
            'habitat':        g['habitat_codes'],
            'barrières':      barriers,
            'réf. CEREMA':    ref_sp[1] if ref_sp else '—',
            'n. espèces rep.': len(g.get('representative_species', [])),
            'réfs':           g['refs'],
        })
    return pd.DataFrame(rows)


def list_cerema_aligned_guilds():
    """Retourne les clés des guildes calibrées sur CEREMA (hors chimères)."""
    return [k for k, g in SPECIES_CONFIG.items()
            if not g.get('_chimera_no_cerema_ref', False)]
    