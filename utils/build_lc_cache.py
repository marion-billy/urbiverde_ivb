"""Constitue le cache d'occupation du sol (WorldCover + OSM) d'un ou plusieurs territoires,
sans exécuter la chaîne de connectivité.

Pourquoi. `data/lc_cache/<Ville>_<tampon>/` archive l'instantané d'entrée réellement utilisé
(WorldCover + vecteurs OpenStreetMap fusionnés sur l'emprise tamponnée). C'est cette archive qui
rend la chaîne rejouable à l'identique : OpenStreetMap est une base vivante, sans version citable,
et sans cet instantané deux exécutions séparées par quelques jours ne partent pas des mêmes données.

Point important. Le téléchargement passe par `landcover.download_lc_data`, qui interroge
OpenStreetMap via OSMnx avec son cache HTTP activé et pointé sur `data/cache/`. Une requête déjà
posée y est resservie sans re-solliciter Overpass : constituer le cache aujourd'hui reprend donc les
réponses déjà obtenues pour ce territoire, et non l'état courant du réseau. WorldCover v200 est de
son côté un produit publié et figé. L'archive obtenue devrait ainsi correspondre aux données ayant
produit les jeux de référence, ce que le protocole de vérification de `suivi/reproductibilite.md`
permet de contrôler.

Le tampon est celui de la chaîne, deux fois la plus grande distance de dispersion des profils, soit
6 000 m ; le nom du dossier de cache le reprend, comme dans `run_pipeline.py`.

Usage, depuis la racine du projet :

    export PYTHONPATH=/opt/conda/lib/python3.11/site-packages
    python3 utils/build_lc_cache.py Nancy
    python3 utils/build_lc_cache.py Nancy LaRochelle Toulouse LRSY
    python3 utils/build_lc_cache.py --list          # état des caches existants
    python3 utils/build_lc_cache.py Nancy --force   # reconstruit même si présent

Un territoire déjà en cache est ignoré, sauf `--force`. Chaque territoire est traité
indépendamment : un échec sur l'un n'interrompt pas les suivants.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

PROJECT_ROOT = "/home/jovyan/work/team/marion/corridor_project"
ABC = "/home/jovyan/work/team/Hugo/a_b_c_functions"
for _p in (os.path.join(PROJECT_ROOT, "utils"), os.path.join(PROJECT_ROOT, "libs"),
           ABC, os.path.join(ABC, "spatial_analysis"), os.path.join(ABC, "gee_with_python")):
    sys.path.insert(1, _p)

import ee  # noqa: E402
import geopandas as gpd  # noqa: E402
import rioxarray  # noqa: E402, F401  (enregistre l'accesseur .rio)

import landcover as lc  # noqa: E402
import species_params as spp  # noqa: E402
from run_pipeline import CITY_CONFIG, CREDENTIALS_PATH, load_aoi  # noqa: E402


def buffer_m() -> int:
    """Tampon de la chaîne : deux fois la plus grande distance de dispersion (6 000 m)."""
    return int(round(2 * max(s["graph"]["d0"] for s in spp.SPECIES_CONFIG.values())))


def cache_paths(city: str) -> tuple[str, str, str]:
    """Renvoie (dossier, chemin du raster, chemin des vecteurs) du cache d'un territoire."""
    d = os.path.join(PROJECT_ROOT, "data", "lc_cache", f"{city}_{buffer_m()}")
    return d, os.path.join(d, "lc_wc.tif"), os.path.join(d, "lc_osm.parquet")


def is_cached(city: str) -> bool:
    """Le cache du territoire est-il complet ?"""
    _, wc, osm = cache_paths(city)
    return os.path.exists(wc) and os.path.exists(osm)


# Seules ces colonnes de `lc_osm` sont lues en aval de la chaîne : la géométrie et le code
# d'occupation du sol pour la rastérisation et les obstacles, l'ordre pour la priorité du burn.
# Vérifié par relecture de landcover.py, connectivity.py et run_pipeline.py.
COLONNES_UTILES = {"geometry", "wc_code", "wc_order"}

# Ordre de priorité du brûlage des infrastructures OpenStreetMap, du moins au plus prioritaire.
# Doit rester identique à `custom_order` de `landcover.download_lc_data`.
ORDRE_BURN = [50, 80, 51, 52, 53, 55, 54]


def ecrire_parquet(gdf, chemin: str) -> str:
    """Écrit les vecteurs OSM en parquet, en réparant si besoin les colonnes de tags.

    OpenStreetMap expose un tag `width`, si bien que la colonne du même nom mélange les valeurs
    textuelles des tags et les largeurs entières calculées par `landcover.download_lc_data` pour
    les voies. Arrow ne sait pas typer une telle colonne et refuse l'écriture. La réparation
    convertit en chaîne les colonnes de tags concernées, en laissant intactes celles dont la
    chaîne se sert (`COLONNES_UTILES`). L'écriture native est tentée d'abord, de sorte que les
    caches qui passaient déjà restent produits à l'identique.
    """
    import geopandas as _gpd

    gdf = gdf.copy()

    # `wc_order` est une catégorie ORDONNÉE dans la chaîne : son tri donne la priorité du brûlage
    # (50 < 80 < 51 < 52 < 53 < 55 < 54). Le parquet la dégrade en entiers, et un tri numérique
    # donnerait alors 50, 51, ... 80, plaçant l'eau en tête et déclassant les chemins : le brûlage,
    # donc l'occupation du sol, en serait changé. La catégorie est remplacée par un rang entier
    # explicite, qui survit à l'aller-retour et se trie à l'identique. Les codes hors nomenclature
    # reçoivent un rang supérieur, comme le tri d'une catégorie place ses valeurs manquantes en fin.
    rangs = {code: i for i, code in enumerate(ORDRE_BURN)}
    if "wc_order" in gdf.columns:
        gdf["wc_order"] = gdf["wc_code"].map(rangs).fillna(len(ORDRE_BURN)).astype("int16")

    def _relire_et_verifier() -> None:
        relu = _gpd.read_parquet(chemin)
        obtenu = list(dict.fromkeys(relu.sort_values("wc_order")["wc_code"].tolist()))
        attendu = [c for c in ORDRE_BURN if c in set(relu["wc_code"])]
        if obtenu[:len(attendu)] != attendu:
            raise ValueError(f"l'ordre de brûlage n'est pas préservé : attendu {attendu}, "
                             f"obtenu {obtenu[:len(attendu)]}")

    try:
        gdf.to_parquet(chemin)
        _relire_et_verifier()
        return "écriture native, ordre de brûlage vérifié"
    except Exception as e:
        repare = gdf.copy()
        touchees = [c for c in repare.columns
                    if c not in COLONNES_UTILES and repare[c].dtype == object]
        for c in touchees:
            repare[c] = repare[c].astype("string")
        repare.to_parquet(chemin)
        _relire_et_verifier()
        apercu = ", ".join(touchees[:5]) + ("..." if len(touchees) > 5 else "")
        return (f"réparé ({type(e).__name__} sur l'écriture native ; "
                f"{len(touchees)} colonne(s) de tags converties en chaîne : {apercu}), "
                f"ordre de brûlage vérifié")


def ecrire_raster(da, chemin: str) -> str:
    """Écrit le raster d'occupation du sol, puis vérifie par relecture que les codes sont intacts.

    Earth Engine attache un facteur d'échelle à la bande. `rio.to_raster` le respecte et divise les
    valeurs à l'écriture, tandis que `open_rasterio` ne le ré-applique pas à la relecture : un cache
    écrit naïvement contient 1, 2, 3 au lieu de 10, 20, 30, et la chaîne n'y trouve plus aucun code
    d'habitat. L'échelle est donc retirée, et les valeurs sont écrites en `uint8`, type dans lequel
    les codes WorldCover (0 à 95) tiennent exactement et qui exclut toute mise à l'échelle. Le
    hors-emprise est codé 0, valeur que la chaîne traite déjà comme extérieure au même titre que NaN.

    La relecture immédiate garantit qu'un cache erroné échoue franchement plutôt que de produire
    des sorties vides à la première utilisation.
    """
    import numpy as np

    wc = da.copy()
    for cle in ("scale_factor", "add_offset", "_FillValue", "scales", "offsets"):
        wc.attrs.pop(cle, None)
        wc.encoding.pop(cle, None)

    attendus = set(np.unique(wc.values[np.isfinite(wc.values)]).astype(int).tolist())
    wc = wc.fillna(0).astype("uint8")
    wc.rio.write_nodata(0, inplace=True)
    wc.rio.to_raster(chemin, dtype="uint8")

    relu = rioxarray.open_rasterio(chemin).squeeze("band", drop=True)
    obtenus = set(np.unique(relu.values).tolist()) - {0}
    if obtenus != attendus - {0}:
        raise ValueError(
            f"le raster relu ne porte pas les mêmes codes que la source : "
            f"attendus {sorted(attendus - {0})[:12]}, obtenus {sorted(obtenus)[:12]}")
    return f"{len(obtenus)} codes d'occupation du sol vérifiés après relecture"


def build(city: str, force: bool = False) -> bool:
    """Constitue le cache d'un territoire. Renvoie True si le cache est en place à la sortie."""
    cache_dir, wc_cache, osm_cache = cache_paths(city)
    if is_cached(city) and not force:
        print(f"  {city} : déjà en cache ({cache_dir}), ignoré", flush=True)
        return True

    t0 = time.perf_counter()
    print(f"  {city} : emprise et téléchargement en cours...", flush=True)
    aoi_raw = load_aoi(city)
    aoi_utm, _aoi_ee, utm_epsg = lc.setup_aoi(aoi_raw)
    print(f"    aire d'étude : {aoi_utm.area.sum() / 1e6:.1f} km2", flush=True)

    # Emprise élargie du tampon, exactement comme dans run_pipeline.py
    buffered_geom = gpd.GeoSeries(aoi_utm.buffer(buffer_m()), crs=utm_epsg).to_crs(aoi_raw.crs)
    aoi_buffered = aoi_raw.copy()
    aoi_buffered.geometry = buffered_geom
    aoi_buffered = aoi_buffered.dissolve()
    aoib_utm, aoib_ee, utmb_epsg = lc.setup_aoi(aoi_buffered)

    lc_wc, lc_osm = lc.download_lc_data(aoib_ee, aoib_utm, aoi_buffered, utmb_epsg)

    os.makedirs(cache_dir, exist_ok=True)
    # Le parquet est écrit en premier : c'est l'étape qui peut échouer. Le raster ne l'est
    # qu'ensuite, pour ne jamais laisser un cache à moitié constitué, que `is_cached` compterait
    # comme absent mais qu'un lecteur humain croirait présent.
    mode = ecrire_parquet(lc_osm, osm_cache)
    controle = ecrire_raster(lc_wc, wc_cache)
    os.system(f"chmod -R a+rwX {cache_dir} 2>/dev/null")

    size = sum(os.path.getsize(os.path.join(cache_dir, f)) for f in os.listdir(cache_dir))
    print(f"  {city} : cache écrit en {(time.perf_counter() - t0) / 60:.1f} min "
          f"({size / 1e6:.0f} Mo, {len(lc_osm)} entités OSM)\n"
          f"    vecteurs : {mode}\n    raster   : {controle}\n    {cache_dir}", flush=True)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Constitue le cache d'occupation du sol par territoire.")
    # Pas de `choices` sur ce positionnel : avec nargs="*", argparse valide la liste vide
    # elle-même contre les choix quand aucun territoire n'est passé, et refuse `--list` seul.
    # La validation est donc faite juste après, avec un message explicite.
    ap.add_argument("cities", nargs="*", metavar="VILLE",
                    help=f"territoires à traiter, parmi : {', '.join(sorted(CITY_CONFIG))}")
    ap.add_argument("--force", action="store_true", help="reconstruire même si le cache existe")
    ap.add_argument("--list", action="store_true", help="afficher l'état des caches et sortir")
    args = ap.parse_args()

    inconnues = [c for c in args.cities if c not in CITY_CONFIG]
    if inconnues:
        ap.error(f"territoire(s) inconnu(s) : {', '.join(inconnues)}. "
                 f"Choisir parmi : {', '.join(sorted(CITY_CONFIG))}")

    if args.list or not args.cities:
        print(f"Cache d'occupation du sol, tampon {buffer_m()} m :")
        for c in sorted(CITY_CONFIG):
            d, _, _ = cache_paths(c)
            if is_cached(c):
                size = sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d)) / 1e6
                print(f"  {c:18s} présent   ({size:.0f} Mo)")
            else:
                print(f"  {c:18s} ABSENT")
        return 0

    # Earth Engine est nécessaire même sur cache-hit OSM : WorldCover vient de là.
    with open(CREDENTIALS_PATH) as kf:
        service_account = json.load(kf)["client_email"]
    ee.Initialize(ee.ServiceAccountCredentials(service_account, CREDENTIALS_PATH))
    print(f"Earth Engine initialisé. Tampon : {buffer_m()} m.\n", flush=True)

    ok, failed = [], []
    for city in args.cities:
        try:
            build(city, force=args.force)
            ok.append(city)
        except Exception as e:  # un échec ne doit pas interrompre les suivants
            print(f"  {city} : ÉCHEC -- {type(e).__name__}: {e}", flush=True)
            failed.append(city)

    print(f"\nTerminé : {len(ok)} cache(s) en place{', échecs : ' + ', '.join(failed) if failed else ''}.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
