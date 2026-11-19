UrbanScope
Satellite imagery classification and land-cover visualization | Senior Computer Science Capstone
UrbanScope is a browser-based geospatial analysis application that highlights likely vegetation-rich or built-up surfaces in aerial and satellite imagery. Users can upload their own images or choose a map area, inspect a classification overlay, and export results.
> **Research prototype:** Classifications are exploratory and have not been validated for real-world planning or environmental decisions. UrbanScope detects visual/spectral proxies, not official forest boundaries or municipal urban boundaries.
Features
Classify Forest (vegetation proxy) or Urban (built-up proxy).
Upload JPG, PNG, TIFF, and GeoTIFF imagery.
Choose a geographic area on an interactive map using Esri World Imagery.
Analyze compatible Landsat 8/9 multispectral GeoTIFFs with six ordered bands (B1–B6).
Explore original and classified imagery using a reveal slider, overlay and binary mask.
View percentage coverage, detected pixel counts and geographic area when valid georeferencing permits.
Download overlay and mask PNG files, summary CSV/JSON, and GeoJSON polygons for georeferenced inputs.
Save and view analyses in a local SQLite history (temporary on many cloud deployments).
How to use the online application
Open the deployed UrbanScope website (add the public application URL here once verified).
Select Forest or Urban from the sidebar.
Choose Upload image or Choose location on map.
Upload an image, or navigate the map and choose Use current map area.
Review the classification statistics and move Comparison reveal (%) to compare the original and overlay.
Download any needed output files.
Landsat-specific analysis
For a GeoTIFF containing Landsat 8/9 reflectance bands B1–B6 in that exact order, enable the Landsat checkbox. UrbanScope computes:
NDVI = (NIR − Red) / (NIR + Red) to find vegetation-rich areas (default threshold > 0.35).
NDBI = (SWIR1 − NIR) / (SWIR1 + NIR) to estimate built-up surfaces (default NDBI > 0.05 and NDVI < 0.2).
The software uses B4 (red), B5 (near infrared), and B6 (shortwave infrared). Do not enable Landsat mode for an ordinary three-band RGB GeoTIFF or an incorrectly ordered image. Spectral thresholds assume suitable reflectance scaling; sensor products and metadata should be checked first.
Technical implementation
Component	Technology
Web interface	Streamlit
Processing and morphology	NumPy and OpenCV
Raster and geospatial processing	Rasterio and PyProj
Interactive mapping	Folium and Streamlit-Folium
Display and exports	Pillow, Pandas, Streamlit
Local analysis history	SQLite
Code overview: `app.py` handles the UI and map interaction; `engine.py` implements classification and statistics; `storage.py` manages local saved analyses; `requirements.txt` lists dependencies.
Run locally (optional)
The public website requires no coding tools or local installation. Developers may run the source with Python 3.11 or 3.12:
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Known limitations
RGB-only analysis is a heuristic; green-painted surfaces can be confused with vegetation, and brown/leaf-off woodland is frequently missed.
NDVI responds to vegetation, including grass and crops, not only forests. NDBI can respond to bare soil and other nonurban materials.
Measurements require valid geographic scale; arbitrary JPG/PNG screenshots do not provide authoritative area measurements.
Map-selected imagery depends on an external provider and its licensing, image dates, resolution and availability.
Cloud-based saved analyses may be lost on restart or redeployment; download exports for durable copies.
No pretrained AI model is included in the current public release.
Results are not independently accuracy-benchmarked or suitable as authoritative land-cover maps.
Capstone submission
The application source is in this repository. Final academic submission documents may be placed in `docs/`:
Presentation (PowerPoint)
User manual (PDF)
Software Problem Report (PDF)
Future enhancements
Validated semantic segmentation, manually corrected labels, time-series change detection, durable cloud history and reference-data accuracy evaluation.
Source imagery and attribution
Map imagery is supplied through Esri World Imagery and underlying imagery providers; applicable attribution and terms must be observed. Uploaded imagery remains subject to its own source terms.
