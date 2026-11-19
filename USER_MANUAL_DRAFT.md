# UrbanScope — User Manual (Working Draft)

## Purpose
UrbanScope helps visually classify likely built-up or forested land in uploaded satellite/aerial imagery. Predictions are provisional. It is not an official land-cover survey.

## Installation
Install Python 3.11/3.12, create a Python virtual environment, then run `pip install -r requirements.txt` and `streamlit run app.py` in this folder. Optional AI: `pip install -r requirements-ai.txt` and allow initial model download.

## Opening UrbanScope
Open the local URL shown by Streamlit, usually `http://localhost:8501`.

## Upload workflow
1. Open **Analyze imagery** and select **Upload image**.
2. Choose JPG/PNG or RGB GeoTIFF. A GeoTIFF should contain first three visible-light bands in RGB order for this starter.
3. In the left sidebar, choose target **Forest** or **Urban** and method.
4. Examine the comparison slider, overlay, mask and summary.
5. Export overlay/mask PNG and metrics CSV/JSON.
6. Click **Save analysis locally** and revisit results in **Saved analyses**.

## Map workflow
Select **Choose location on map**. Pan/zoom to your region of interest. Click **Use current map area**. Map source is dependent on internet and provider restrictions. This functionality requires live environment testing before classroom demonstration.

## Interpreting metrics
Coverage is the fraction of image pixels classified as the selected target. Real area appears only if geospatial metadata is available; ordinary JPEG screenshots do not supply geographic scale. Other/unclassified pixels are *not automatically* an opposite class.

## Frequent issues
- **Module not found:** activate environment and reinstall requirements.
- **Model cannot load:** check internet, model repository, installed optional AI dependencies and local model cache.
- **No geographic area for PNG:** upload a properly georeferenced GeoTIFF.
- **Map error:** retry with a smaller region or use offline upload mode.
- **Misclassification:** choose representative imagery, try the alternative method and report errors in the PR log.

## Safety, limitations and privacy
Analysis history is stored locally in `saved_analyses/`. Do not publicly distribute sensitive or restricted imagery. Verify licensing of third-party basemaps and model weights. All model and classical predictions require validation before use in planning or research conclusions.

### Landsat 8 / Landsat 9 spectral analysis
If your GeoTIFF is a **single stacked six-or-more-band raster in B1–B6 order**, upload it and enable the Landsat 8/9 checkbox. Select the Traditional method. Urban mode uses NDBI and an NDVI exclusion threshold; Forest mode uses an NDVI vegetation threshold (not strict forest recognition). Export geographically referenced regions with the GeoJSON download button. If your file contains only an ordinary RGB scene, keep the Landsat checkbox off.
