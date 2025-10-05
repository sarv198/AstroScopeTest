# sim.py
from flask import Blueprint, render_template, jsonify, request
from helpers import get_palermo_leaderboard, get_vi_data
import math, re, sys, json, requests

# Import your existing helpers
# from your_project.sentry import get_palermo_leaderboard  # , get_vi_data

sim = Blueprint("sim", __name__, url_prefix="/sim")

# ----------------------- Utils -----------------------

def _parse_mt_str(s):
    """Accepts '123.4 Mt' or a number; returns float(Mt) or None."""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    m = re.search(r"([-+]?\d*\.?\d+)", str(s))
    return float(m.group(1)) if m else None

# ---- Population providers ----
WORLDPOP_IMG = "https://worldpop.arcgis.com/arcgis/rest/services/WorldPop_Population_Density_1km/ImageServer/identify"
SEDAC_WMS    = "https://sedac.ciesin.columbia.edu/geoserver/wms"
SEDAC_LAYER  = "gpw-v4:gpw-v4-population-density_2020"

def population_density_worldpop(lat: float, lng: float, year: int = 2020, timeout: int = 8):
    """WorldPop ArcGIS ImageServer identify (persons/km²) at a point."""
    params = {
        "f": "json",
        "geometry": json.dumps({"x": float(lng), "y": float(lat), "spatialReference": {"wkid": 4326}}),
        "geometryType": "esriGeometryPoint",
        "returnGeometry": "false",
        "processAsMultidimensional": "true",
        "time": f"{year}-01-01T00:00:00Z",
    }
    r = requests.get(WORLDPOP_IMG, params=params, timeout=timeout)
    r.raise_for_status()
    js = r.json()
    val = js.get("value")
    if val is None and isinstance(js.get("results"), list) and js["results"]:
        val = js["results"][0].get("value")
    return (float(val) if val is not None else None, "worldpop")

def population_density_sedac(lat: float, lng: float, timeout: int = 8):
    """SEDAC GPWv4 WMS GetFeatureInfo (persons/km²) with version/format fallbacks."""
    import re as _re
    def _parse_any(payload):
        if isinstance(payload, dict):
            feats = payload.get("features") or []
            if feats and "properties" in feats[0]:
                props = feats[0]["properties"]
                for k in ("GRAY_INDEX", "value", "Band1"):
                    if k in props:
                        try: return float(props[k])
                        except: pass
        if isinstance(payload, str):
            try:
                j = json.loads(payload)
                v = _parse_any(j)
                if v is not None: return v
            except: pass
            m = _re.search(r"(-?\d+(?:\.\d+)?)", payload)
            if m:
                try: return float(m.group(1))
                except: pass
        return None

    attempts = []
    # 1) WMS 1.3.0 (CRS=EPSG:4326, bbox: minLat,minLon,maxLat,maxLon; i/j)
    bbox_130 = f"{lat-0.05},{lng-0.05},{lat+0.05},{lng+0.05}"
    base_130 = {
        "service":"WMS","version":"1.3.0","request":"GetFeatureInfo",
        "layers":SEDAC_LAYER,"query_layers":SEDAC_LAYER,"crs":"EPSG:4326",
        "bbox":bbox_130,"width":101,"height":101,"i":50,"j":50
    }
    for fmt in ("application/json","application/vnd.ogc.gml","text/plain"):
        attempts.append(({**base_130,"info_format":fmt},"1.3.0 "+fmt))
    # 2) WMS 1.1.1 (SRS=EPSG:4326, bbox: minLon,minLat,maxLon,maxLat; x/y)
    bbox_111 = f"{lng-0.05},{lat-0.05},{lng+0.05},{lat+0.05}"
    base_111 = {
        "service":"WMS","version":"1.1.1","request":"GetFeatureInfo",
        "layers":SEDAC_LAYER,"query_layers":SEDAC_LAYER,"srs":"EPSG:4326",
        "bbox":bbox_111,"width":101,"height":101,"x":50,"y":50
    }
    for fmt in ("application/json","application/vnd.ogc.gml","text/plain"):
        attempts.append(({**base_111,"info_format":fmt},"1.1.1 "+fmt))

    headers = {"User-Agent":"AsteroidLauncher/1.0", "Accept":"*/*"}
    for params, _ in attempts:
        try:
            resp = requests.get(SEDAC_WMS, params=params, headers=headers, timeout=timeout)
            payload = resp.json() if "application/json" in resp.headers.get("Content-Type","") else resp.text
            val = _parse_any(payload)
            if val is not None:
                if val < 0: val = 0.0
                return (float(val), "sedac")
        except Exception:
            continue
    return (None, "sedac")

def population_density_any(lat: float, lng: float, year: int = 2020):
    """Try WorldPop first, then SEDAC fallback."""
    try:
        v, src = population_density_worldpop(lat, lng, year)
        if v is not None:
            return v, src
    except Exception:
        pass
    try:
        v, src = population_density_sedac(lat, lng)
        if v is not None:
            return v, src
    except Exception:
        pass
    return None, "none"

# ----------------------- Routes -----------------------

@sim.route("/asteroid-launcher")
def asteroid_launcher_page():
    return render_template("asteroid_launcher.html")

@sim.route("/neos")
def api_neos():
    """
    Return NEOs sorted by energy_mt (desc). For speed, we **only**
    use energy present on the leaderboard; we skip VI lookups here.
    """
    try:
        # Use a direct approach to avoid cache issues
        import requests
        SENTRY_URL = "https://ssd-api.jpl.nasa.gov/sentry.api"
        
        r = requests.get(SENTRY_URL, timeout=10)
        r.raise_for_status()
        sentry_list = r.json().get("data", [])
        
        if not sentry_list:
            return jsonify({"neos": []})
        
        # Sort by Palermo Scale descending
        sentry_list.sort(key=lambda o: float(o.get("ps_max", -99) or -99), reverse=True)
        
        cleaned, seen = [], set()
        for obj in sentry_list[:50]:  # Limit to first 50 for performance
            des = obj.get("des")
            full_name = obj.get("fullname") or obj.get("des", "Unknown")
            
            if full_name in seen:
                continue
                
            # Get VI data for kinetic energy
            try:
                vi_r = requests.get(SENTRY_URL, params={"des": des}, timeout=5)
                vi_r.raise_for_status()
                vi_data = vi_r.json()
                
                vi_list = vi_data.get("data", [])
                top_vi = max(vi_list, key=lambda v: v.get("ps", -99) or -99) if vi_list else {}
                e_mt = float(top_vi.get('energy', 0)) if top_vi else 0
                
                if e_mt > 0:  # Only include objects with energy data
                    seen.add(full_name)
                    cleaned.append({
                        "name": full_name,
                        "energy_mt": float(f"{e_mt:.3f}"),
                        "status": "Active",
                    })
            except Exception:
                continue  # Skip this object if VI lookup fails
        
        neos_sorted = sorted(cleaned, key=lambda x: x["energy_mt"], reverse=True)
        return jsonify({"neos": neos_sorted})
        
    except Exception as e:
        print(f"NEO fetch failed: {e}", file=sys.stderr)
        return jsonify({"neos": []})

@sim.route("/impact", methods=["POST"])
def api_impact():
    """Blast-only model (server-side physics)."""
    js = request.get_json(force=True) or {}
    lat = float(js.get("lat"));  lng = float(js.get("lng"))
    energy_mt = float(js.get("energy_mt"))
    angle_deg = float(js.get("angle_deg", 45))
    pop_density = float(js.get("pop_density_km2", 3000))

    W_kt = energy_mt * 1000.0
    w13 = W_kt ** (1.0 / 3.0)
    coupling = max(0.4, min(1.0, math.sin(math.radians(angle_deg))))

    c10, c5, c1 = 0.40, 0.75, 2.10
    r10 = c10 * w13 * coupling
    r5  = c5  * w13 * coupling
    r1  = c1  * w13 * coupling

    a10 = math.pi * r10 * r10
    a5  = math.pi * r5 * r5  - a10
    a1  = math.pi * r1 * r1  - math.pi * r5 * r5

    cas_sev   = int(pop_density * a10 * 0.90)
    cas_mod   = int(pop_density * a5  * 0.40)
    cas_light = int(pop_density * a1  * 0.10)
    total = cas_sev + cas_mod + cas_light

    return jsonify({
        "center": {"lat": lat, "lng": lng},
        "radii_km": {"r10psi": r10, "r5psi": r5, "r1psi": r1},
        "areas_km2": {"a10psi_km2": a10, "a5psi_km2": a5, "a1psi_km2": a1},
        "casualties_est": {
            "severe": cas_sev, "moderate": cas_mod, "light": cas_light, "total": total
        }
    })

@sim.route("/population")
def api_population():
    """
    GET /sim/population?lat=..&lng=..[&year=2020]
    Returns: {"ok": bool, "density_km2": float|None, "src": "worldpop"|"sedac"|"none", "year": int?}
    """
    try:
        lat = float(request.args.get("lat"))
        lng = float(request.args.get("lng"))
        year = int(request.args.get("year", "2020"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "bad lat/lng/year"}), 400

    val, src = population_density_any(lat, lng, year=year)
    if val is None:
        return jsonify({"ok": False, "density_km2": None, "src": src}), 200
    return jsonify({"ok": True, "density_km2": float(val), "src": src, "year": year})
