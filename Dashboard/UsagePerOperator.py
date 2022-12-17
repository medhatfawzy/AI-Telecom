import pandas as pd

# The server and widgets library
import panel as pn
pn.extension(template="material")

# the plotting libs
import holoviews as hv
from holoviews.operation.datashader import inspect, datashade, rasterize
# gives the ability to call hvplot on a pandas dataframe
import hvplot.pandas   #noqa

# provides the color maps
import colorcet as cc
# This lib is used to rasetrize the data
import datashader as ds
# from datashader.utils import lnglat_to_meters
hv.extension('bokeh')

RSRP_data = pd.read_parquet("RSRP_data_lnglat_to_meters.parq")

# Using the map tiles provided by Esri. OpenStreetMaps can be used as well
esri = hv.element.tiles.ESRI().redim(x="Longtitude", y="Latitude").opts(alpha=0.2, width=1000, height=700, bgcolor='black')
COLORS = {"Operator A":"red", "Operator B": "green", "Operator C": "blue"}

def operator_map(operator_name):
    # Best Method of plotting to get inspect while using datashader
    df = RSRP_data[RSRP_data["RadioOperatorName"] == operator_name].copy()

    points =  hv.Points(df, kdims=["LocationLongitude", "LocationLatitude"])
    # raster = rasterize(points).opts(cmap=cc.kg, cnorm="eq_hist",clim=(0, 10000))
    shaded = datashade(points, color_key=COLORS, aggregator=ds.count_cat("RadioOperatorName")).opts(width=1000, height=700)
    highlight = inspect(shaded).opts(marker="o", size=10, fill_alpha=0, color='white', tools=["hover"])

    return esri * shaded * highlight
    
operator_select = pn.widgets.RadioButtonGroup(options=list(COLORS.keys()))
interactive = pn.bind(operator_map, operator_name=operator_select)
first_app = pn.Column(operator_select, interactive).servable(target="main")