# Configuration des guildes de déplacement
# d0 : Distance de dispersion (en mètres)
# k : Nombre de voisins pour le graphe KNN
# friction : Coût de passage par classe d'occupation du sol (Common Legend)

SPECIES_CONFIG = {
    'mid_walker': {
        'name': 'Mammifère terrestre moyen',
        'graph': {
            'd0': 2000,
            'k_neighbors': 8,
        },
        'friction': {
            10: 1.0,    # Trees : Habitat favorable
            30: 1.5,    # Grassland : Passage facile
            40: 5.0,    # Agriculture : Traversée possible mais découverte
            60: 30.0,   # Bare soil / Impervious : Stressant (bitume/parking)
            51: 90.0,   # Highways : Très risqué (mortalité routière élevée)
            80: 100.0,   # Water : Obstacle (sauf si nageur)
            50: 999.0,  # Built-up : Barrière quasi-infranchissable (Bâtiments)
        }
    },
    'mid_flyer': {
        'name': 'Oiseau',
        'graph': {
            'd0': 2000,
            'k_neighbors': 8,
        },
        'friction': {
            10: 1.0,    # Trees
            30: 2.0,    # Grassland
            40: 5.0,    # Agriculture
            60: 10.0,    # Bare soil
            80: 10.0,    # Water
            50: 20.0,   # Built-up : Dérangement/Obstacle vertical
            51: 30.0     # Highways : Pas un obstacle pour le vol
        }
    }
}