"""Build the self-hosted GEBCO relief tiles for the map.

Source: GEBCO Web Map Service, layer GEBCO_LATEST (shaded relief of the GEBCO Grid).
Credit: GEBCO Compilation Group, GEBCO Grid (https://www.gebco.net/). Free to use with attribution.

Usage: uv run --with pillow python scripts/gebco_tiles.py ../web/public/layers/gebco

Writes Web Mercator tiles as {z}/{x}/{y}.webp: zooms 0-5 for the whole world,
6-7 for Iran and adjacent areas only. The map upsamples beyond those zooms.
Run it once; the tiles are committed, so the site never calls GEBCO.
"""

import io
import math
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
from PIL import Image

WMS = "https://wms.gebco.net/mapserv"
LAYER = "GEBCO_LATEST"
WORLD_ZOOMS = range(0, 6)
REGION_ZOOMS = range(6, 8)
REGION = (38.0, 68.0, 20.0, 44.0)  # lon min/max, lat min/max; keep in sync with Map.vue
HALF = 20037508.342789244  # half the Web Mercator world width, metres
QUALITY = 72


def tile_x(lon, z):
    return int((lon + 180) / 360 * 2**z)


def tile_y(lat, z):
    r = math.radians(lat)
    return int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 2**z)


def tiles():
    for z in WORLD_ZOOMS:
        for x in range(2**z):
            for y in range(2**z):
                yield z, x, y
    for z in REGION_ZOOMS:
        for x in range(tile_x(REGION[0], z), tile_x(REGION[1], z) + 1):
            for y in range(tile_y(REGION[3], z), tile_y(REGION[2], z) + 1):
                yield z, x, y


def bbox(z, x, y):
    size = 2 * HALF / 2**z
    return (-HALF + x * size, HALF - (y + 1) * size, -HALF + (x + 1) * size, HALF - y * size)


def fetch(client, out, z, x, y):
    path = out / str(z) / str(x) / f"{y}.webp"
    if path.exists():
        return
    params = {
        "service": "WMS", "version": "1.3.0", "request": "GetMap", "layers": LAYER, "styles": "",
        "crs": "EPSG:3857", "bbox": ",".join(f"{v:.2f}" for v in bbox(z, x, y)),
        "width": 256, "height": 256, "format": "image/png",
    }
    for attempt in range(4):
        try:
            r = client.get(WMS, params=params)
            r.raise_for_status()
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            break
        except (httpx.HTTPError, OSError):
            if attempt == 3:
                raise
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "WEBP", quality=QUALITY, method=6)


def main(dst):
    out = Path(dst)
    todo = list(tiles())
    with httpx.Client(timeout=60) as client, ThreadPoolExecutor(6) as pool:
        for i, _ in enumerate(pool.map(lambda t: fetch(client, out, *t), todo), 1):
            if i % 100 == 0:
                print(i, "/", len(todo), flush=True)
    size = sum(p.stat().st_size for p in out.rglob("*.webp"))
    print(len(todo), "tiles,", round(size / 1e6, 1), "MB")


if __name__ == "__main__":
    main(sys.argv[1])
