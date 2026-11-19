# UrbanScope — senior capstone starter application

UrbanScope estimates built-up surfaces or vegetation from (a) Landsat 8/9 multispectral stacks with bands B1–B6 in order using NDVI/NDBI, (b) ordinary RGB aerial/satellite images using experimental color heuristics, or (c) map-selected RGB imagery. It includes geospatial uploads, class overlays, before/after comparison, metrics, exports, and SQLite-backed local history.

## Running on Windows / macOS / Linux

1. Install Python 3.11 or 3.12.
2. Open a terminal in this folder.
3. Create an environment: `python -m venv .venv`
4. Activate: Windows PowerShell: `.venv\Scripts\Activate.ps1`; macOS/Linux: `source .venv/bin/activate`
5. Install: `pip install -r requirements.txt`
6. Run: `streamlit run app.py`
7. Open the URL shown in the terminal (normally `http://localhost:8501`).

Optional AI: `pip install -r requirements-ai.txt`. The AI downloads a third-party model on first use and has not yet been benchmarked for American cities. Its exact labels and inference behavior require local validation.

## What works in this prototype

- Upload JPG/PNG, RGB GeoTIFF, or Landsat 8/9 GeoTIFF stacks with B1–B6 ordered
- Landsat workflow: B4 red, B5 near infrared, B6 short-wave infrared; NDVI vegetation or NDBI built-up estimation; morphology
- Export detected polygon regions as georeferenced GeoJSON where CRS/transform are present
- Experimental RGB-only Forest / Urban classification
- Optional experimental pretrained segmentation model adapter
- Before/after drag slider, overlay, mask, summary and bar chart
- Correctly distinguishes pixel percentage from measured area
- Area measurements for referenced rasters (projected or north-up WGS84 geographic)
- Map selection with a web imagery endpoint (requires internet and compliance with provider terms)
- Download overlay PNG, binary mask PNG, CSV and JSON results
- Locally persist results in SQLite and image files

## Important limitations

This is an early prototype, **not a validated land-cover model**. Aerial RGB photographs do not automatically indicate *official* forest boundaries or urban jurisdiction. Pixel counts are meaningful as proportions, but measurements in square kilometers require real geospatial metadata; uploading an arbitrary screenshot does not provide scale. Third-party map imagery may have access, rate, licensing, or acquisition-date constraints. Unless the Landsat checkbox is selected, GeoTIFF bands 1,2,3 are treated as RGB. Landsat mode **requires an ordered B1–B6 stack**; a single-band file, rearranged stack, or different sensor cannot be treated as the same sensor. NDVI detects vegetation, not forests specifically; NDBI can confuse bare soil with built-up areas. Thresholds are exploratory and need ground-truth validation. The numeric indices are meaningful for bands with compatible reflectance units/scaling; inspect raster metadata. Map-selected coverage is an estimate from the provider's visual basemap and should not be used as authoritative GIS data. Model weights, licensing and model generalization should be verified before distribution.

## Test

`python -m unittest discover -s tests -v`

## Next build targets

1. Validate and refine map-selected export and AI inference in a live Streamlit environment.
2. Assemble 15–30 diverse test scenes with ground-truth pixel masks.
3. Evaluate precision, recall, IoU and false positives for each class.
4. Add model confidence visualization and provider attribution.
5. Improve export with georeferenced GeoTIFF masks and better image band controls.
6. Write Problem Reports, screenshots, demo script, user manual and final presentation.

## Using the prior Landsat project code

1. Choose **Upload image** in UrbanScope.
2. Select a single GeoTIFF containing Landsat 8 or 9 reflectance bands B1, B2, B3, B4, B5, B6 in **that order**.
3. Enable the **ordered Landsat 8/9 bands** checkbox (auto-enabled when filename begins LC08/LC09).
4. Keep **Traditional** selected, and choose **Urban** (NDBI > 0.05 and NDVI < 0.2) or **Forest** (NDVI > 0.35; vegetation proxy).
5. Compare original/overlay, review measured coverage, and download **GeoJSON**, PNG or metrics.

Not every `.tif` is a Landsat stack. If the file is a normal RGB image, **disable** Landsat mode.
