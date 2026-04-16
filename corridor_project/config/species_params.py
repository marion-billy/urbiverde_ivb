# Configuration des guildes de déplacement
# d0 : Distance de dispersion (en mètres)
# k : Nombre de voisins pour le graphe KNN
# friction : Coût de passage par classe d'occupation du sol (Common Legend)

# low d0=500 et k=4
# high d0=5000 et k=12

SPECIES_CONFIG = {
    'low_walker': {
        'habitat_codes': [10, 20, 30],  
        'graph': {
            'd0': 500,
            'k_neighbors': 4,
        },
        'friction': {
            10: 1,    # Trees : Habitat favorable
            20: 5,    # Shrubland
            30: 10,    # Grassland : Passage facile
            40: 15,    # Agriculture : Traversée possible mais découverte
            60: 20,   # Bare soil / Impervious : Stressant (bitume/parking)
            54: 25,   # Pedestrian roads
            90: 30,   # Wetlands
            50: 50,  # Built-up
            53: 100,   # Petites routes
            52: 10000,   # Highways : Très risqué (mortalité routière élevée)
            80: 10000,   # Water : Obstacle (sauf si nageur)
            51: 99999,  # Batiments OSM
        }
    },
    'low_flyer': {
        'habitat_codes': [10, 20, 30],
        'graph': {
            'd0': 500,
            'k_neighbors': 4,
        },
        'friction': {
            10: 1,    # Trees
            20: 2,    # Shrubland
            30: 2,    # Grassland
            40: 5,    # Agriculture
            90: 5,    # Wetlands
            60: 15,    # Bare soil
            80: 20,    # Water
            54: 20,   # Pedestrian roads
            50: 30,  # Built-up
            53: 50,   # Petites routes
            52: 1000,    # Highways
            51: 99999,   # Batiments OSM
       }
    },

    
    'mid_walker': {
        'habitat_codes': [10, 20, 30],
        'graph': {
            'd0': 2000,
            'k_neighbors': 8,
        },
        'friction': {
            10: 1,    # Trees : Habitat favorable
            20: 2,    # Shrubland
            30: 5,    # Grassland : Passage facile
            40: 10,    # Agriculture : Traversée possible mais découverte
            60: 15,   # Bare soil / Impervious : Stressant (bitume/parking)
            54: 25,   # Pedestrian roads
            90: 25,   # Wetlands
            50: 50,  # Built-up
            53: 100,   # Petites routes
            52: 10000,   # Highways : Très risqué (mortalité routière élevée)
            80: 10000,   # Water : Obstacle (sauf si nageur)
            51: 99999,  # Batiments OSM
        }
    },
    
    'mid_flyer': {
        'habitat_codes': [10, 20, 30],
        'graph': {
            'd0': 2000,
            'k_neighbors': 8,
        },
        'friction': {
            10: 1,    # Trees
            20: 2,    # Shrubland
            30: 2,    # Grassland
            40: 5,    # Agriculture
            90: 5,    # Wetlands
            60: 10,    # Bare soil
            80: 10,    # Water
            54: 20,   # Pedestrian roads
            50: 50,  # Built-up
            53: 50,   # Petites routes
            52: 150,    # Highways : Pas un obstacle pour le vol
            51: 99999,  # Batiments OSM
        }
    }
}