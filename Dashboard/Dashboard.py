import pandas as pd
# The server and widgets library
import panel as pn
pn.extension()

# the plotting libs
import holoviews as hv
from holoviews.operation.datashader import inspect, rasterize
from  holoviews.element.tiles import ESRI
# provides the color maps
import colorcet as cc
# a module for plotting large ds
import datashader as ds
# from datashader.utils import lnglat_to_meters
hv.extension('bokeh')

RSRP_data = pd.read_parquet("RSRP_data_lnglat_to_meters.parq")
RSRP_data_houred = pd.read_parquet("RSRP_data_houred.parq")

# Using the map tiles provided by Esri. OpenStreetMaps can be used as well
esri = ESRI().redim(x="Longtitude", y="Latitude").opts(alpha=0.2, width=900, height=700, bgcolor='black')
# osm = OSM().redim(x="Longtitude", y="Latitude").opts(alpha=0.2, width=900, height=700, bgcolor='black')

# The options for the operators and thier colour maps
COLORS = {"Operator A": cc.kr, "Operator B": cc.kg, "Operator C": cc.kb}

def hour_map(hours_range, days_rage):
    start_hour, end_hour = hours_range
    start_day, end_day = days_rage
    df_hour = RSRP_data_houred[RSRP_data_houred["Timestamp"] == f"Day {start_day:02}, {start_hour:02}:00"].copy()
    if (len(df_hour) == 0):
        return esri
    hour_points = hv.Points(df_hour, kdims=["LocationLongitude", "LocationLatitude"])
    rastered = rasterize(hour_points).opts(cmap=cc.fire, cnorm="eq_hist", width=1000, height=700)
    hour_highlight = inspect(rastered).opts(marker="o", size=10, fill_alpha=0, color='white', tools=["hover"])
    return esri * rastered * hour_highlight

def operator_map(operator_name):
    df_operator = RSRP_data[RSRP_data["RadioOperatorName"] == operator_name].copy()
    if (len(df_operator) == 0 ):
        return esri
    operator_points =  hv.Points(df_operator, kdims=["LocationLongitude", "LocationLatitude"], aggregator=ds.count_cat('RadioOperatorName'))
    rastered = rasterize(operator_points).opts(cmap=COLORS[operator_name], cnorm="eq_hist",  width=1000, height=700)
    operator_highlight = inspect(rastered).opts(marker="o", size=10, fill_alpha=0, color='white', tools=["hover"])
    return esri * rastered * operator_highlight

hour_select = pn.widgets.IntRangeSlider(name="Hour", start=0, end=23, value=(2, 8))
day_select = pn.widgets.IntRangeSlider(name="Day", start=1, end=4, value=(2,3))
Hours_maps = pn.bind(hour_map, hour_select, day_select)

operator_select = pn.widgets.RadioButtonGroup(options=list(COLORS.keys()))
Operators_maps = pn.bind(operator_map, operator_select)


template = pn.template.FastListTemplate(title="Telecom Analysis",
                                        main=[pn.Row(pn.Column(day_select, Hours_maps,hour_select), 
                                                    pn.Column(operator_select, Operators_maps))
                                            ],

)
template.servable()