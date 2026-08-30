"""Tests de non-régression complémentaires (compléments listés dans le README racine).

Couvre les manques signalés : indice PC sur un graphe jouet, seuils de la segmentation
morphologique, surface de friction, et invariants de la table de calibration. Chaque valeur
attendue est calculable à la main, de sorte qu'un écart signale un changement de comportement
et non une imprécision numérique.

ATTENTION : ce fichier a été écrit sans pouvoir être exécuté (environnement géospatial absent de
la machine de rédaction, cf. suivi/reproductibilite.md §5). Le lancer une fois et corriger ce qui
casse AVANT de le citer dans le rapport.

Exécution, depuis la racine du projet (le répertoire de travail compte : connectivity.py résout
a_b_c_functions par un chemin relatif) :

    export PYTHONPATH=/opt/conda/lib/python3.11/site-packages
    python3 -m pytest tests/ -q
    # ou, sans pytest :
    python3 tests/test_pipeline_extra.py
"""
import math
import os
import sys
from unittest import SkipTest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))

import numpy as np  # noqa: E402

import species_params as spp  # noqa: E402

# Les modules de traitement tirent des dépendances externes (a_b_c_functions, smoothify) :
# on les importe de façon défensive pour que les tests de calibration restent exécutables seuls.
try:
    import networkx as nx
    import xarray as xr
    import rioxarray  # noqa: F401  (enregistre l'accesseur .rio)
    from shapely.geometry import Point

    import connectivity as conn
    import routing as rout

    HEAVY_OK, HEAVY_ERR = True, None
except Exception as exc:  # pragma: no cover
    HEAVY_OK, HEAVY_ERR = False, f"{type(exc).__name__}: {exc}"


def _need_heavy():
    if not HEAVY_OK:
        raise SkipTest(f"dépendances de traitement indisponibles ({HEAVY_ERR})")


# ---------------------------------------------------------------------------
# 1. Surface de friction
# ---------------------------------------------------------------------------

def test_resistance_surface_barriers_and_default():
    """NaN -> inf (barrière), hors AOI (0/NaN) -> inf, code absent -> coût par défaut."""
    _need_heavy()
    da = xr.DataArray(
        np.array([[10.0, 20.0], [51.0, 0.0]]),
        dims=("y", "x"), coords={"y": [1, 0], "x": [0, 1]},
    ).rio.write_crs("EPSG:32631")

    res = rout.create_resistance_surface(da, {10: 1, 20: 2, 51: float("nan")}).values
    assert res[0, 0] == 1.0                      # habitat
    assert res[0, 1] == 2.0                      # matrice franchissable
    assert np.isinf(res[1, 0])                   # barrière (NaN -> inf)
    assert np.isinf(res[1, 1])                   # hors AOI (0 -> inf)

    # Un code absent du dictionnaire reçoit le coût par défaut, pas une barrière.
    da2 = xr.DataArray(
        np.array([[40.0]]), dims=("y", "x"), coords={"y": [0], "x": [0]},
    ).rio.write_crs("EPSG:32631")
    assert rout.create_resistance_surface(da2, {10: 1}).values[0, 0] == 100.0


# ---------------------------------------------------------------------------
# 2. Segmentation morphologique (MSPA)
# ---------------------------------------------------------------------------

def test_fast_mspa_compact_patch_has_core():
    """Bloc 5x5 : érosion d'un pixel -> coeur 3x3, lisière 16 pixels, aucun îlot."""
    _need_heavy()
    arr = np.zeros((7, 7), dtype="uint8")
    arr[1:6, 1:6] = 1
    da = xr.DataArray(arr, dims=("y", "x"))

    core, islet, edge = conn.fast_mspa(da, edge_width_pixels=1)
    assert int(core.values.sum()) == 9      # 3x3
    assert int(islet.values.sum()) == 0
    assert int(edge.values.sum()) == 16     # 25 - 9


def test_fast_mspa_linear_patch_has_no_core():
    """Tache filiforme (1 pixel de large) : aucun coeur, tout est classé îlot.

    Comportement documenté en §2.4.2 du rapport : une tache entièrement constituée de lisière
    n'a pas d'intérieur écologique. sp_pipeline ne conserve ensuite que les espaces relais
    dotés d'un coeur, donc une telle tache est écartée quelle que soit sa surface.
    """
    _need_heavy()
    arr = np.zeros((7, 7), dtype="uint8")
    arr[3, 1:6] = 1                          # ligne de 5 pixels
    da = xr.DataArray(arr, dims=("y", "x"))

    core, islet, edge = conn.fast_mspa(da, edge_width_pixels=1)
    assert int(core.values.sum()) == 0
    assert int(islet.values.sum()) == 5
    assert int(edge.values.sum()) == 0


# ---------------------------------------------------------------------------
# 3. Indice de connectivité (PC) sur graphe jouet
# ---------------------------------------------------------------------------

def test_pc_index_two_connected_patches():
    """Deux taches de 100 ha reliées à coût ln(2) dans une zone de 2 km2 -> PC = 0,75.

    Calcul : surfaces 1 km2 chacune ; p_12 = exp(-ln 2) = 0,5 ; la somme porte sur toutes les
    paires, diagonale comprise (p_ii = 1) : 1 + 1 + 0,5 + 0,5 = 3 ; PC = 3 / 2**2.
    """
    _need_heavy()
    G = nx.Graph()
    G.add_node(0, area=100.0)
    G.add_node(1, area=100.0)
    G.add_edge(0, 1, cost_log=math.log(2))

    assert abs(conn.calculate_pc_index(G, total_area_km2=2.0) - 0.75) < 1e-12


def test_pc_index_two_isolated_patches():
    """Sans lien, chaque tache ne compte que son terme propre : PC = (1 + 1) / 2**2 = 0,5."""
    _need_heavy()
    G = nx.Graph()
    G.add_node(0, area=100.0)
    G.add_node(1, area=100.0)

    assert abs(conn.calculate_pc_index(G, total_area_km2=2.0) - 0.5) < 1e-12


def test_touching_patches_give_valid_geometry():
    """Taches jointives (points d'ancrage confondus) : segment de 1 mm valide, pas de géométrie
    dégénérée qui casserait l'export GeoJSON."""
    _need_heavy()
    G = nx.Graph()
    G.add_node(0, area=1.0)
    G.add_node(1, area=1.0)
    G.add_edge(0, 1, dist_m=0.0, prob=1.0, cost_log=0.0,
               anchor_pts=(Point(0, 0), Point(0, 0)))

    gdf = conn.graph_to_gdf_edges(G, crs="EPSG:32631")
    geom = gdf.geometry.iloc[0]
    assert geom.geom_type == "LineString"
    assert not geom.is_empty
    assert abs(geom.length - 1e-3) < 1e-9


# ---------------------------------------------------------------------------
# 4. Invariants de la table de calibration
# ---------------------------------------------------------------------------

def test_ecoprofils_expected_set():
    """Quatre profils actifs, aucune chimère (le profil insecte a été retiré)."""
    assert set(spp.SPECIES_CONFIG) == {
        "ground_mammal", "arboreal_mammal", "forest_edge_bird", "ground_reptile",
    }
    assert spp.list_cerema_aligned_ecoprofils() == list(spp.SPECIES_CONFIG)


def test_habitat_codes_have_friction_at_most_three():
    """Règle de calibration (annexe A) : tout code d'habitat a une friction définie <= 3.

    La règle ne vaut que dans ce sens. La réciproque est fausse par construction : les codes
    d'infrastructure OpenStreetMap (51 à 55) ne sont jamais habitat, même à friction <= 3
    (chemins et voies ferrées valent 3 pour le profil lézard).
    """
    for key, cfg in spp.SPECIES_CONFIG.items():
        for code in cfg["habitat_codes"]:
            assert code in cfg["friction"], f"{key}: code habitat {code} sans friction"
            f = cfg["friction"][code]
            assert not (isinstance(f, float) and np.isnan(f)), f"{key}: habitat {code} en barrière"
            assert f <= 3, f"{key}: habitat {code} a une friction de {f} (> 3)"
            assert not 51 <= code <= 55, \
                f"{key}: le code d'infrastructure OSM {code} ne peut pas être habitat"


def test_barriers_match_documented_set():
    """Barrières infranchissables (NaN) conformes au tableau 2 : bâti pour tous les profils
    terrestres, eau pour les deux profils strictement terrestres, aucune pour le profil volant."""
    expected = {
        "ground_mammal": {51, 80},
        "arboreal_mammal": {51},
        "forest_edge_bird": set(),
        "ground_reptile": {51, 80},
    }
    for key, cfg in spp.SPECIES_CONFIG.items():
        nan_codes = {c for c, v in cfg["friction"].items()
                     if isinstance(v, float) and np.isnan(v)}
        assert nan_codes == expected[key], f"{key}: barrières {nan_codes} != {expected[key]}"


def test_dispersal_distances_and_cost_budget():
    """d0 des quatre profils et budget de déplacement = 3 x d0 (équation du chapitre 2)."""
    assert spp.FRICTION_AVG_FAVORABLE == 3
    expected_d0 = {
        "ground_mammal": 3000, "arboreal_mammal": 2000,
        "forest_edge_bird": 1500, "ground_reptile": 750,
    }
    for key, d0 in expected_d0.items():
        assert spp.SPECIES_CONFIG[key]["graph"]["d0"] == d0, f"{key}: d0 modifié"
        assert d0 * spp.FRICTION_AVG_FAVORABLE == 3 * d0


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    ok = skipped = failed = 0
    for t in tests:
        try:
            t()
            ok += 1
            print(f"  OK      {t.__name__}")
        except SkipTest as e:
            skipped += 1
            print(f"  IGNORÉ  {t.__name__} : {e}")
        except AssertionError as e:
            failed += 1
            print(f"  ÉCHEC   {t.__name__} : {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  ERREUR  {t.__name__} : {type(e).__name__}: {e}")
    print(f"\n{ok} réussis, {skipped} ignorés, {failed} en échec (sur {len(tests)})")
    sys.exit(1 if failed else 0)
