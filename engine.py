"""UrbanScope baseline computer-vision processing and measurement tools."""
import io
import json
from dataclasses import dataclass
from typing import Optional
import cv2
import numpy as np
from PIL import Image

@dataclass
class RasterInput:
    rgb: np.ndarray
    transform: object = None
    crs: object = None
    source: str = "image"
    spectral: object = None
    valid: object = None


def load_image(data: bytes, filename: str, landsat: bool = False) -> RasterInput:
    if filename.lower().endswith((".tif", ".tiff")):
        import rasterio
        from rasterio.io import MemoryFile
        with MemoryFile(data) as mem:
            with mem.open() as ds:
                if ds.count < 3:
                    raise ValueError("GeoTIFF requires at least 3 bands (RGB).")
                if landsat and ds.count < 6:
                    raise ValueError("Landsat 8/9 mode requires at least six ordered bands: B1–B6.")
                # Landsat 8/9 order B1..B6: B4=red, B3=green, B2=blue,
                # B5=NIR and B6=SWIR1. Generic TIFF mode uses B1..B3 as RGB.
                display_indexes = [4, 3, 2] if landsat else [1, 2, 3]
                raw = ds.read(display_indexes).astype(np.float32)
                valid = ds.dataset_mask() > 0
                out = []
                for band in raw:
                    good = band[valid & np.isfinite(band)]
                    if good.size == 0:
                        out.append(np.zeros_like(band, dtype=np.uint8))
                        continue
                    lo, hi = np.percentile(good, [2, 98])
                    if hi <= lo:
                        lo, hi = float(good.min()), float(good.max())
                    scaled = np.clip((band-lo)*255/max(hi-lo, 1e-6), 0, 255)
                    out.append(np.nan_to_num(scaled).astype(np.uint8))
                rgb = np.moveaxis(np.stack(out), 0, 2)
                spectral = None
                if landsat:
                    b4, b5, b6 = ds.read([4,5,6]).astype(np.float32)
                    spectral = {"red": b4, "nir": b5, "swir1": b6}
                    valid &= np.isfinite(b4) & np.isfinite(b5) & np.isfinite(b6)
                return RasterInput(rgb, ds.transform, ds.crs, filename, spectral, valid)
    rgb = np.asarray(Image.open(io.BytesIO(data)).convert("RGB"))
    return RasterInput(rgb, source=filename)


def classify_baseline(rgb: np.ndarray, mode: str, sensitivity: int = 50) -> np.ndarray:
    """Exploratory RGB-only heuristic; NOT a trained or validated land-cover model."""
    if mode not in ("Forest", "Urban"):
        raise ValueError("Mode must be Forest or Urban")
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    r, g, b = [rgb[:, :, i].astype(np.int16) for i in range(3)]
    exg = 2*g-r-b
    # Greenness index reduces false positives from many blue surfaces.
    green = (exg > 12 + (50-sensitivity)*0.38) & (hsv[:,:,0] >= 27) & (hsv[:,:,0] <= 95) & (hsv[:,:,1] > 34)
    # Heuristic excludes strongly colored pixels, very dark shadows and highlights.
    neutral = (hsv[:,:,1] < 92 + (sensitivity-50)*0.5) & (hsv[:,:,2] > 58) & (hsv[:,:,2] < 250)
    not_green = exg < 19
    urban = neutral & not_green & (lab[:,:,0] > 72)
    # Remove tiny isolated detections; it is deliberately a baseline only.
    raw = green if mode == "Forest" else urban
    kernel = np.ones((3, 3), np.uint8)
    clean = cv2.morphologyEx(raw.astype(np.uint8), cv2.MORPH_OPEN, kernel)
    return clean.astype(bool)


def spectral_indices(spectral: dict) -> tuple[np.ndarray, np.ndarray]:
    """NDVI=(NIR-red)/(NIR+red); NDBI=(SWIR1-NIR)/(SWIR1+NIR)."""
    red, nir, swir = [np.asarray(spectral[k], dtype=np.float32) for k in ("red", "nir", "swir1")]
    ndvi = np.divide(nir-red, nir+red, out=np.zeros_like(red), where=np.abs(nir+red)>1e-6)
    ndbi = np.divide(swir-nir, swir+nir, out=np.zeros_like(red), where=np.abs(swir+nir)>1e-6)
    return ndvi, ndbi


def classify_multispectral(spectral: dict, mode: str, valid=None,
                           ndvi_forest: float = 0.35, ndbi_urban: float = 0.05) -> np.ndarray:
    """Landsat 8/9 threshold baseline; vegetation is NOT necessarily forest."""
    if mode not in ("Forest", "Urban"):
        raise ValueError("Mode must be Forest or Urban")
    ndvi, ndbi = spectral_indices(spectral)
    if mode == "Forest":
        raw = ndvi > ndvi_forest
    else:
        raw = (ndbi > ndbi_urban) & (ndvi < 0.2)
    if valid is not None:
        raw &= valid
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    clean = cv2.morphologyEx(raw.astype(np.uint8), cv2.MORPH_OPEN, kernel).astype(bool)
    if valid is not None:
        clean &= valid
    return clean


def mask_geojson(mask: np.ndarray, transform, crs, min_pixels: int = 9) -> bytes:
    """Export threshold regions as georeferenced polygons in EPSG:4326."""
    if transform is None or crs is None:
        raise ValueError("GeoJSON export requires a raster transform and coordinate reference system.")
    from rasterio.features import shapes
    from rasterio.warp import transform_geom
    import rasterio
    src_crs = rasterio.crs.CRS.from_user_input(crs)
    # Use connected components to exclude smaller regions before polygonization.
    labels_count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    keep = np.zeros(mask.shape, dtype=np.uint8)
    for i in range(1, labels_count):
        if int(stats[i, cv2.CC_STAT_AREA]) >= min_pixels:
            keep[labels == i] = 1
    features=[]
    for geom, value in shapes(keep, mask=keep.astype(bool), transform=transform):
        if value != 1: continue
        geo = transform_geom(src_crs, 'EPSG:4326', geom, antimeridian_cutting=False)
        features.append({"type":"Feature", "properties":{"classification":"selected"}, "geometry":geo})
    return json.dumps({"type":"FeatureCollection", "features":features}, separators=(',',':')).encode('utf-8')


def render_overlay(rgb: np.ndarray, mask: np.ndarray, mode: str, opacity: float=.55) -> np.ndarray:
    color = np.array([32, 208, 111] if mode == "Forest" else [255, 99, 91], dtype=np.float32)
    out = rgb.astype(np.float32).copy()
    out[mask] = out[mask] * (1-opacity) + color * opacity
    return np.clip(out, 0, 255).astype(np.uint8)


def mask_png(mask: np.ndarray) -> bytes:
    return png_bytes((mask.astype(np.uint8)*255))


def png_bytes(image: np.ndarray) -> bytes:
    f=io.BytesIO(); Image.fromarray(image).save(f, format="PNG"); return f.getvalue()


def area_square_meters(mask: np.ndarray, transform, crs) -> Optional[float]:
    """Area only when raster has a valid known CRS and transform."""
    if crs is None or transform is None: return None
    import rasterio
    from pyproj import Geod
    crs = rasterio.crs.CRS.from_user_input(crs)
    if crs.is_projected:
        from pyproj import CRS
        units = CRS.from_user_input(crs).axis_info
        if len(units) < 2 or not all(ax.unit_conversion_factor for ax in units[:2]): return None
        area = abs(transform.a*transform.e-transform.b*transform.d)
        return float(mask.sum()*area*units[0].unit_conversion_factor*units[1].unit_conversion_factor)
    if crs.is_geographic:
        geod = Geod(ellps="WGS84")
        total = 0.0
        # Each row's cell area calculated geodesically; north-up affine assumed.
        if abs(transform.b)>1e-9 or abs(transform.d)>1e-9: return None
        for row in range(mask.shape[0]):
            count = int(mask[row].sum())
            if not count: continue
            x0, y0 = transform*(0,row); x1,y1=transform*(1,row+1)
            area,_ = geod.polygon_area_perimeter([x0,x1,x1,x0], [y0,y0,y1,y1])
            total += abs(area)*count
        return total
    return None


def result_stats(mask, transform=None, crs=None):
    pct = float(np.mean(mask)*100)
    area = area_square_meters(mask, transform, crs)
    return {"coverage_percent": round(pct,2), "selected_pixels": int(mask.sum()), "total_pixels": int(mask.size), "area_square_meters": None if area is None else round(area,2), "area_square_kilometers": None if area is None else round(area/1e6,5)}
