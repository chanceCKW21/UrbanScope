# UrbanScope: Capstone Project Specification
**Version:** 0.1 | **Date:** 2026-11-18 | **Status:** prototype implementation

## Problem statement
Satellite imagery offers valuable insights into urban development and vegetation cover, but interpreting and quantifying land-cover patterns manually can be time-consuming. UrbanScope offers an accessible web workflow for identifying candidate built-up and tree-covered areas, comparing results against source imagery, and exporting reproducible metrics.

## Main objective
Build a polished, reliable web application that accepts uploaded RGB imagery or a map-selected image, labels either built-up or visually forested areas, visualizes classification masks, measures coverage when scale is available, and saves/export results.

## Functional requirements
- FR-01: Upload JPG, PNG, RGB GeoTIFF.
- FR-02: Select a location on a geographic map and acquire source imagery, subject to provider availability and permissions.
- FR-03: Choose Forest or Urban independently.
- FR-04: Offer an experimental classical RGB baseline and a benchmarked pretrained AI classifier.
- FR-05: Render a color overlay and image comparison control.
- FR-06: Summarize pixels, coverage percentage and area **only with valid scale/georeference**.
- FR-07: Export metrics and masks.
- FR-08: Save/reopen analyses locally.
- FR-09: Display source, method, limitations and attribution.

## Nonfunctional requirements / acceptance targets
- NFR-01: User can run a local demonstration in a standard browser.
- NFR-02: Handle unsupported files and provider failures without crashing the app.
- NFR-03: Never invent a physical-area measurement from an unreferenced PNG.
- NFR-04: A prepared ~1024×1024 image should finish classical classification promptly on a standard laptop; benchmark on actual demonstration hardware.
- NFR-05: Maintain unit and integration tests, reproducible environments, and a bug log.
- NFR-06: Validate classification separately for forest and built-up classes using ground-truth masks; report IoU, precision, recall and F1, plus representative failures. No accuracy claims without evaluation.

## Out of scope for initial release
Longitudinal land-change detection, manual segmentation editing, multi-user authentication, large-scale batch inference, official zoning/forest delineation, nationwide measurement on an unreferenced screenshot.

## One-month stages
1. Week 1: basic upload, classification, visualization, export + test harness.
2. Week 2: test AI model and map imagery acquisition, verify measured area, benchmark model accuracy.
3. Week 3: persistence, error handling, integration tests, UI polish, data attribution.
4. Week 4: user manual, PowerPoint, PRs, screenshot evidence, reproducible final demo.

## Example demonstration
1. Open UrbanScope in a browser and upload a well-lit aerial RGB image.
2. Select Forest and run classical or AI segmentation; inspect green overlay and % cover.
3. Drag the slider and examine errors (e.g., parks vs tree canopy).
4. Switch to Urban and show buildings/roads; explain domain adaptation and visual ambiguity.
5. Load a georeferenced GeoTIFF; display valid area estimate and export CSV/PNG.
6. Save analysis and reopen it from history.
7. If stable and permitted, select a map region and analyze the acquired image.

## Evaluation dataset plan
Prepare at least 10 varied urban and 10 varied forest scenes from legally usable, documented sources. Label reference pixels, compare against classical and AI masks. Stratify scenes by lighting, season, shadows, water, urban density and image source. WorldCover built-up/tree cover (10-meter resolution) can support a carefully aligned reference comparison but is not equivalent to high-resolution building/tree pixels; manually labeled imagery is useful for fine-grained validation.

## Architectural decisions
Web UI: Streamlit; processing: NumPy/OpenCV + optional PyTorch/Transformers; metadata and physical area: Rasterio/PyProj; map: Folium / map provider; storage: SQLite + PNG; metrics: JSON/CSV. The optional pretrained model must be locally verified and its terms checked before public redistribution.

## Deliverables
- presentation.pptx: 10–12 slides, plus live demo
- source code, requirements, tests and startup instructions
- PR reports: repeatable issue reproduction and resolution history
- user manual: installation, workflow, interface, troubleshooting, limitations

## Adaptation of previous ArcGIS / Landsat research (2026-11-18)
The original research script computed NDVI=(B5-B4)/(B5+B4) and NDBI=(B6-B5)/(B6+B5) for Landsat 8, applied NDBI>0.05 with NDVI<0.2 to urban estimates, used morphological cleanup and contoured regions, and exported georeferenced polygons. UrbanScope now implements this approach in the web UI for explicitly identified Landsat 8/9 ordered multispectral stacks. It adds a vegetation-proxy mode based on NDVI >0.35, before-after comparison, coverage metrics, downloadable GeoJSON, and PNG/CSV/JSON exports. Forest and urban thresholds require site-specific validation and should not be presented as validated AI.
