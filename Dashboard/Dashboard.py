import pandas as pd
# The server and widgets library
import panel as pn
# enabling panel backend
pn.extension()

# the plotting libs
import holoviews as hv
from holoviews.operation.datashader import inspect, rasterize
from  holoviews.element.tiles import ESRI
# provides the color maps
import colorcet as cc

# using bokeh as a backend for holoviews, it works better than plotly wiith panel
hv.extension('bokeh')
#--------------------------------------------------

# The options for the operators and thier colour maps
COLORS = {"Operator A": cc.kr, "Operator B": cc.kg, "Operator C": cc.kb}
PLOT_WIDTH = 900
PLOT_HEIGHT= 900

RSRP_data = pd.read_parquet("RSRP_data_viz.parq")

# Using the map tiles provided by Esri. OpenStreetMaps can be used as well
esri = ESRI().redim(x="Longtitude", y="Latitude").opts(alpha=0.2, width=PLOT_WIDTH, height=PLOT_HEIGHT, bgcolor='black')
# osm = OSM().redim(x="Longtitude", y="Latitude").opts(alpha=0.2, width=900, height=700, bgcolor='black')


def hour_map(hours_range, days_range):
    start_hour, end_hour = hours_range
    start_day, end_day = days_range
    df_time_range = RSRP_data[  ((start_day <= RSRP_data["Timestamp"].dt.day) & (RSRP_data["Timestamp"].dt.day<= end_day)) 
                                    &
                                ((start_hour <= RSRP_data["Timestamp"].dt.hour) & (RSRP_data["Timestamp"].dt.hour<= end_hour))].copy()

    if (len(df_time_range) == 0):
        return esri
    time_range_points = hv.Points(df_time_range, kdims=["LocationLongitude", "LocationLatitude"])
    rastered = rasterize(time_range_points).opts(cmap=cc.fire, cnorm="eq_hist", width=PLOT_WIDTH, height=PLOT_HEIGHT)
    hour_highlight = inspect(rastered).opts(marker="o", size=10, fill_alpha=0, color='white', tools=["hover"])
    return esri * rastered * hour_highlight

def operator_map(operator_name):
    df_operator = RSRP_data[RSRP_data["RadioOperatorName"] == operator_name].copy()
    if (len(df_operator) == 0 ):
        return esri
    operator_points =  hv.Points(df_operator, kdims=["LocationLongitude", "LocationLatitude"])
    rastered = rasterize(operator_points).opts(cmap=COLORS[operator_name], cnorm="eq_hist",  width=PLOT_WIDTH, height=PLOT_HEIGHT)
    operator_highlight = inspect(rastered).opts(marker="o", size=10, fill_alpha=0, color='white', tools=["hover"])
    return esri * rastered * operator_highlight

hour_select = pn.widgets.IntRangeSlider(name="Hour", start=0, end=23, value=(2, 8))
day_select = pn.widgets.IntRangeSlider(name="Day", start=1, end=4, value=(2,3))
Hours_maps = pn.bind(hour_map, hours_range=hour_select, days_range=day_select)

operator_select = pn.widgets.RadioButtonGroup(options=list(COLORS.keys()))
Operators_maps = pn.bind(operator_map, operator_name=operator_select)


template = pn.template.FastListTemplate(title="Telecom Analysis",
                                        main=[pn.Row(pn.Column(day_select, Hours_maps,hour_select), 
                                                    pn.Column(operator_select, Operators_maps))
                                            ]
)
template.servable()