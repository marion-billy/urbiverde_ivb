"""Extract the sweep response (connected % + n_subnetworks) on the two axes (d0, friction-contrast)
for the complete cities x 4 guilds, plus the d0 margin (scale at which the network loses/gains
connexity). Prints a compact digest to feed the section 3.4 rewrite and the figures. Read-only."""
import glob, os
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
CITIES = ["Kourou", "Perpignan", "Nancy", "LaRochelle"]
GUILDS = [("ground_mammal", "herisson"), ("ground_reptile", "lezard"),
          ("arboreal_mammal", "ecureuil"), ("forest_edge_bird", "fauvette")]
D0 = [50, 60, 70, 80, 90, 110, 120]
FC = [0, 25, 50, 75, 125, 150, 200]


def val(city, guild, metric, tag=None):
    p = (f"{ROOT}/data/outputs/{city}/{guild}/stats_*.csv" if tag is None
         else f"{ROOT}/data/sensitivity/{tag}/data/outputs/{city}/{guild}/stats_*.csv")
    f = glob.glob(p)
    if not f:
        return None
    s = pd.read_csv(f[0]).iloc[0]
    return round(float(s.get("connected_habitat_pct", float("nan"))), 1), int(s.get("n_subnetworks", -1))


def d0_margin(city, guild, ref_nsub):
    """Lowest d0 scale (%) at which the network is still connexe (nsub==1), scanning up from 50."""
    connexe = []
    for m in D0 + [100]:
        v = val(city, guild, "connected_habitat_pct" if False else "n_subnetworks",
                None if m == 100 else f"swd0_{m:03d}")
        if v is None:
            continue
        nsub = v[1] if isinstance(v, tuple) else None
    # simpler: return the set of d0 where nsub==1
    pts = {}
    for m in D0:
        r = val(city, guild, "x", f"swd0_{m:03d}")
        if r:
            pts[m] = r[1]
    r = val(city, guild, "x")
    if r:
        pts[100] = r[1]
    connexe_scales = sorted([m for m, n in pts.items() if n == 1])
    return pts, connexe_scales


for city in CITIES:
    print(f"\n############ {city} ############")
    for g, nom in GUILDS:
        ref = val(city, g, "x")
        if ref is None:
            print(f"  {nom:10s} : (absent)")
            continue
        d0curve = []
        for m in D0:
            v = val(city, g, "x", f"swd0_{m:03d}")
            d0curve.append(f"{m}:{v[0]:.0f}%/{v[1]}" if v else f"{m}:--")
        fccurve = []
        for m in FC:
            v = val(city, g, "x", f"swfc_{m:03d}")
            fccurve.append(f"{m}:{v[0]:.0f}%/{v[1]}" if v else f"{m}:--")
        pts, connexe = d0_margin(city, g, ref[1])
        marge = f"connexe aux d0={connexe}%" if connexe else "jamais connexe sur la plage"
        print(f"  {nom:10s} REF {ref[0]:.0f}%/{ref[1]}ss-res")
        print(f"      d0  : {' '.join(d0curve)}")
        print(f"      cont: {' '.join(fccurve)}")
        print(f"      marge: {marge}")
