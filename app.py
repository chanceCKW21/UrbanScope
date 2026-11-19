"""UrbanScope — Streamlit prototype. Run: streamlit run app.py"""
import io, json, base64
import numpy as np
import cv2
import pandas as pd
import streamlit as st
from PIL import Image
from engine import RasterInput, load_image, classify_baseline, render_overlay, result_stats, png_bytes, mask_png, classify_multispectral, mask_geojson
import storage

st.set_page_config(page_title='UrbanScope', page_icon='🛰️', layout='wide')
st.markdown("""<style>
:root {color-scheme: dark}
.stApp {background: radial-gradient(ellipse at 85% 0%,rgba(31,93,85,.20),transparent 43%), linear-gradient(145deg,#0b151b,#101821 60%,#0d161d);color:#e8f2f0}
.block-container {padding-top:1.25rem;padding-bottom:4rem;max-width:1220px}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#14232c,#0d1921);border-right:1px solid #2b444a}
[data-testid="stSidebar"] h2 {letter-spacing:.02em}
.hero {padding:28px 30px;border-radius:18px;background:linear-gradient(110deg,#173b36,#18313f 67%,#173144);border:1px solid #41675f;margin-bottom:23px;box-shadow:0 12px 42px rgba(0,0,0,.15)}
.hero h1 {margin:0;color:#f6fdf9;font-size:2.5rem;line-height:1.15;letter-spacing:-.035em}
.hero p {color:#bfe0d5;margin:8px 0 0;font-size:1.02rem}
.hero small {color:#8be0bf;font-weight:700;letter-spacing:.14em}
[data-testid="stMetric"] {border:1px solid #315451;border-radius:14px;padding:15px 18px;background:#142a2d}
[data-testid="stMetricValue"] {color:#a2f3c5}
[data-testid="stTabs"] button {font-weight:600}
[data-testid="stFileUploader"] {border-radius:12px}
div.stButton>button[kind="primary"],div.stDownloadButton>button[kind="primary"] {background:#177b63;border:1px solid #58ae96;color:white}
[data-testid="stAlert"] {border-radius:12px}
h1,h2,h3 {letter-spacing:-.02em}
</style>""", unsafe_allow_html=True)
st.markdown('<div class="hero"><small>GEOSPATIAL INTELLIGENCE · SENIOR CAPSTONE</small><h1>URBANSCOPE <span style="color:#9ef0c5">◈</span></h1><p>Discover patterns in the landscape. Classify urban development and vegetation across satellite imagery.</p></div>',unsafe_allow_html=True)
with st.sidebar:
    st.header('Analysis settings')
    st.caption('01 / Configure classification')
    mode=st.radio('Target land cover',['Forest','Urban'])
    method=st.selectbox('Classification method',['Traditional (experimental RGB baseline)','Pretrained AI (experimental, requires model download)'])
    sensitivity=st.slider('Baseline sensitivity',0,100,50,disabled=not method.startswith('Traditional'))
    opacity=st.slider('Overlay opacity',0.15,0.90,0.55)
    st.caption('RGB results are exploratory. For stronger multispectral analysis, upload an ordered Landsat B1–B6 GeoTIFF.')

tab_analysis,tab_history,tab_about=st.tabs(['Analyze imagery','Saved analyses','Project / limitations'])
with tab_analysis:
    source=st.radio('Select an image source',['Upload image','Choose location on map'],horizontal=True)
    raster=None
    if source=='Upload image':
        file=st.file_uploader('Upload JPG, PNG, TIFF or GeoTIFF',type=['jpg','jpeg','png','tif','tiff'])
        landsat = st.checkbox('This GeoTIFF contains ordered Landsat 8/9 bands B1–B6', value=bool(file and file.name.lower().startswith(('lc08','lc09'))), disabled=not(file and file.name.lower().endswith(('.tif','.tiff'))), help='For Landsat stacks only: B4 red, B5 NIR, B6 SWIR1. Do not enable on standard RGB GeoTIFFs.')
        if file:
            try: raster=load_image(file.getvalue(),file.name,landsat=landsat)
            except Exception as exc: st.error(f'Could not open image: {exc}')
    else:
        st.caption('Map-source imagery is requested from Esri World Imagery. Internet access and source terms apply. Attribution: Esri and imagery providers.')
        try:
            import folium
            from streamlit_folium import st_folium
            import requests
            from rasterio.transform import from_bounds
            from rasterio.crs import CRS
            center=st.session_state.get('map_center',[38.9,-77.04])
            fmap=folium.Map(location=center,zoom_start=12,tiles=None)
            folium.TileLayer(tiles='OpenStreetMap',name='Street map').add_to(fmap)
            folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',attr='Esri, imagery providers',name='Satellite imagery',overlay=False).add_to(fmap)
            folium.LayerControl().add_to(fmap)
            info=st_folium(fmap,height=400,width=None,key='map')
            st.caption('Pan and zoom the map, then click "Use current map area" to fetch a 768 × 768 pixel image of the visible bounds.')
            if st.button('Use current map area',type='primary'):
                bounds=info.get('bounds') if info else None
                if not bounds: st.warning('Please interact with the map, then try again.')
                else:
                    sw,ne=bounds['_southWest'],bounds['_northEast']
                    west,south,east,north=sw['lng'],sw['lat'],ne['lng'],ne['lat']
                    if east<=west or north<=south or abs(east-west)>1.5 or abs(north-south)>1.5:
                        st.error('Select a smaller area that does not cross the international date line (maximum 1.5 degrees).')
                    else:
                        endpoint='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export'
                        params={'bbox':f'{west},{south},{east},{north}','bboxSR':4326,'imageSR':4326,'size':'768,768','format':'png','f':'image'}
                        response=requests.get(endpoint,params=params,timeout=25)
                        response.raise_for_status()
                        if not response.headers.get('Content-Type','').startswith('image/'):
                            raise ValueError('The imagery provider did not return an image.')
                        rgb=np.asarray(Image.open(io.BytesIO(response.content)).convert('RGB'))
                        transform=from_bounds(west,south,east,north,rgb.shape[1],rgb.shape[0])
                        st.session_state['map_raster']=(rgb,transform,CRS.from_epsg(4326),f'Map [{west:.4f},{south:.4f},{east:.4f},{north:.4f}]')
            if 'map_raster' in st.session_state:
                rgb,transform,crs,src=st.session_state['map_raster']
                raster=RasterInput(rgb,transform,crs,src)
        except ImportError: st.error('Map mode requires folium, streamlit-folium, requests, and rasterio.')
        except Exception as exc: st.error(f'Map imagery request failed: {exc}')
    if raster is not None:
        st.divider()
        st.markdown('### Analysis results')
        rgb=raster.rgb
        if rgb.shape[0]*rgb.shape[1]>7_000_000:
            st.warning('Large image: processing a reduced preview; downsampled pixel-level classification and boundaries are approximate.')
            ratio=(7_000_000/(rgb.shape[0]*rgb.shape[1]))**.5
            new_width=max(1,int(rgb.shape[1]*ratio)); new_height=max(1,int(rgb.shape[0]*ratio))
            rgb=np.asarray(Image.fromarray(rgb).resize((new_width,new_height)))
            if raster.spectral is not None:
                raster.spectral = {k:cv2.resize(v,(new_width,new_height),interpolation=cv2.INTER_AREA) for k,v in raster.spectral.items()}
            if raster.valid is not None:
                raster.valid = cv2.resize(raster.valid.astype(np.uint8),(new_width,new_height),interpolation=cv2.INTER_NEAREST).astype(bool)
            raster.transform=raster.transform * raster.transform.scale(raster.rgb.shape[1]/new_width,raster.rgb.shape[0]/new_height) if raster.transform is not None else None
        try:
            if raster.spectral is not None and method.startswith('Traditional'):
                mask=classify_multispectral(raster.spectral,mode,raster.valid)
                st.success('Multispectral mode: Landsat NDVI/NDBI threshold segmentation. No AI training needed.')
            elif method.startswith('Traditional'):
                mask=classify_baseline(rgb,mode,sensitivity)
                st.info('RGB-only approximation: results are less reliable than multispectral NDVI/NDBI.')
            else:
                from ai_model import classify_ai
                with st.spinner('Loading pretrained model and classifying...'): mask=classify_ai(rgb,mode)
            overlay=render_overlay(rgb,mask,mode,opacity)
            stats=result_stats(mask,raster.transform,raster.crs)
            if raster.valid is not None:
                valid_count=int(raster.valid.sum())
                stats['coverage_percent'] = round(100 * int((mask & raster.valid).sum())/valid_count,2) if valid_count else 0.0
                stats['valid_pixels'] = valid_count
            c1,c2,c3=st.columns(3)
            c1.metric('Target coverage',f"{stats['coverage_percent']:.2f}%")
            c2.metric('Detected pixels',f"{stats['selected_pixels']:,}")
            c3.metric('Detected area',f"{stats['area_square_kilometers']:.4f} km²" if stats['area_square_kilometers'] is not None else 'Unknown (no geographic scale)')
            st.subheader('Explore the classified landscape')
            st.caption('Drag the reveal slider to compare the analysis (left) against original imagery (right).')
            reveal = st.slider('Comparison reveal (%)', 0, 100, 50, key='comparison_reveal', help='0 = original image only; 100 = classified overlay only.')
            # Native Streamlit slider is intentionally used here; it continues to work
            # when browsers or hosted platforms restrict JavaScript in HTML iframes.
            split = int(round(rgb.shape[1] * reveal / 100.0))
            comparison_img = rgb.copy()
            comparison_img[:, :split] = overlay[:, :split]
            if 0 < split < rgb.shape[1]:
                comparison_img[:, max(0,split-2):min(rgb.shape[1],split+2)] = [245, 249, 243]
            st.image(comparison_img, caption=f'Classification overlay {reveal}% · Original image {100-reveal}%', use_container_width=True)
            a,b=st.columns(2)
            a.image(overlay,caption='Classification overlay',use_container_width=True)
            b.image((mask*255).astype('uint8'),caption='Binary classification mask',use_container_width=True)
            st.bar_chart(pd.DataFrame({'Percent':[stats['coverage_percent'],100-stats['coverage_percent']]},index=[mode,'Other / unclassified']))
            st.caption('Other / unclassified does not mean the opposite land-cover class. Urban and forest classification are independent selections. NDVI vegetation may include grass/crops, not just forest.')
            st.download_button('Download overlay PNG',png_bytes(overlay),'urbanscope_overlay.png','image/png')
            st.download_button('Download mask PNG',mask_png(mask),'urbanscope_mask.png','image/png')
            if raster.transform is not None and raster.crs is not None:
                try:
                    geojson = mask_geojson(mask,raster.transform,raster.crs)
                    st.download_button('Download classified polygons (GeoJSON)',geojson,'urbanscope_polygons.geojson','application/geo+json')
                except Exception as exc: st.warning(f'Polygon export unavailable: {exc}')
            st.download_button('Download metrics JSON',json.dumps({'source':raster.source,'target':mode,'method':method,'results':stats},indent=2),'urbanscope_metrics.json','application/json')
            csv='metric,value\n'+''.join(f'{k},{v}\n' for k,v in stats.items())
            st.download_button('Download metrics CSV',csv,'urbanscope_metrics.csv','text/csv')
            if st.button('Save analysis locally',type='primary'):
                ident=storage.save(raster.source,mode,method,stats,png_bytes(rgb),png_bytes(overlay),mask_png(mask))
                st.success(f'Saved analysis {ident}')
            st.warning('Results are provisional. Validate predictions against manually labeled reference areas before making real planning or conservation claims.')
        except Exception as exc: st.error(f'Classification error: {exc}')
with tab_history:
    rows=storage.history()
    if not rows: st.info('No analyses saved yet.')
    else:
        st.dataframe(pd.DataFrame([{'ID':x[0],'Created UTC':x[1],'Source':x[2],'Target':x[3],'Method':x[4],'Coverage %':json.loads(x[5]).get('coverage_percent')} for x in rows]),use_container_width=True)
        selected=st.selectbox('View saved result', [r[0] for r in rows])
        if selected:
            path=storage.DATA/f'{selected}_overlay.png'
            if path.exists(): st.image(str(path),caption=f'Saved overlay: {selected}',use_container_width=True)
with tab_about:
    st.markdown('''**UrbanScope prototype**\n\n- Classical image processing is an exploratory RGB heuristic, not independently validated forest or urban classification.\n- The optional pretrained AI is a third-party model and may fail on imagery unlike its training data.\n- Measurements are emitted only when geographic metadata is available, and map imagery is subject to source resolution and licensing.\n- Aerial/satellite imagery often lacks original acquisition dates in image screenshots. No time-change claims are made.\n- Future research: evaluate precision, recall, F1 and IoU against manually annotated reference masks or a compatible land-cover dataset.\n''')
