import pandas as pd
import numpy as np
from pandasql import sqldf
# The server and widgets library
import panel as pn
# enabling panel backend
pn.extension()

# the plotting libs
import holoviews as hv
from holoviews.operation.datashader import inspect, rasterize
from holoviews.element.tiles import ESRI
# provides the color maps
import colorcet as cc

# using bokeh as a backend for holoviews, it works better than plotly wiith panel
hv.extension('bokeh')
#--------------------------------------------------

# The options for the operators and thier colour maps
COLORS = {"Operator A": cc.kr, "Operator B": cc.kg, "Operator C": cc.kb}
AGGS = {"Average": np.mean, "Minimum": np.min, "Maximum":np.max, "90th Percentile":np.percentile}
PLOT_WIDTH = 900
PLOT_HEIGHT= 700

RSRP_data = pd.read_parquet("RSRP_data_viz.parq")
Downlink_traffic = pd.read_parquet("Downlink_traffic.parq")

# Using the map tiles provided by Esri. OpenStreetMaps can be used as well
esri = ESRI().opts(alpha=0.2, width=PLOT_WIDTH, height=PLOT_HEIGHT, bgcolor='black', xaxis=None, yaxis=None)
# osm = OSM().redim(x="Longtitude", y="Latitude").opts(alpha=0.2, width=900, height=700, bgcolor='black')

def time_range_plot(hours_range, days_range):
    """Plots the users of all operators during the day and show the areas with high intensity"""
    start_hour, end_hour = hours_range
    start_day, end_day = days_range
    df_time_range = RSRP_data[  (RSRP_data["Timestamp"].dt.day >= start_day)
                                    & 
                                (RSRP_data["Timestamp"].dt.day <= end_day)
                                    &
                                (RSRP_data["Timestamp"].dt.hour >= start_hour)
                                    & 
                                (RSRP_data["Timestamp"].dt.hour <= end_hour)
                            ]

    if (len(df_time_range) == 0):
        return esri
    time_range_points = hv.Points(df_time_range, kdims=["LocationLongitude", "LocationLatitude"])
    rastered = rasterize(time_range_points).opts(cmap=cc.fire, cnorm="eq_hist", width=PLOT_WIDTH, height=PLOT_HEIGHT)
    hour_highlight = inspect(rastered).opts(marker="o", size=10, fill_alpha=0, color='white', tools=["hover"])
    return esri * rastered * hour_highlight

def operator_plot(operator_name):
    """Plots the users of each operator with the map tiles on the background"""
    df_operator = RSRP_data[RSRP_data["RadioOperatorName"] == operator_name]
    if (len(df_operator) == 0 ):
        return esri
    operator_points =  hv.Points(df_operator, kdims=["LocationLongitude", "LocationLatitude"])
    rastered = rasterize(operator_points).opts(cmap=COLORS[operator_name], cnorm="eq_hist",  width=PLOT_WIDTH, height=PLOT_HEIGHT)
    operator_highlight = inspect(rastered).opts(marker="o", size=10, fill_alpha=0, color='white', tools=["hover"])
    return esri * rastered * operator_highlight

def traffic_plot(operator_name):
    """Plots a hexbin for each operator where the size of each hex depends on the counts of values that falls inside this hex"""
    df_operator = Downlink_traffic[Downlink_traffic["RadioOperatorName"] == operator_name]
    if (len(df_operator) == 0 ):
        return esri
    operator_tiles =  hv.element.HexTiles(df_operator, kdims=["LocationLongitude", "LocationLatitude"], vdims=["TrafficVolume"])
    operator_tiles.opts(cmap=COLORS[operator_name], alpha=0.8, cnorm="linear", tools=["hover"], width=PLOT_WIDTH, height=PLOT_HEIGHT, scale=(hv.dim('Count').norm()*0.5)+0.5)
    return esri * operator_tiles

def RSRP_bar_plot(operator_name, aggregator_method):
    """"Plots a bar chart of RSRP per device type per operator with an option to choose the aggregation method of RSRP (avg, min, max and 90th Percentile)."""
    df_operator = RSRP_data[RSRP_data["RadioOperatorName"] == operator_name]
    if(aggregator_method=="90th Percentile"):
        bars = hv.Bars(df_operator, "DeviceManufacturer", "RSRP").aggregate(function=AGGS[aggregator_method], q=90)
    else:
        bars = hv.Bars(df_operator, "DeviceManufacturer", "RSRP").aggregate(function=AGGS[aggregator_method])
    
    bars.opts(width=PLOT_WIDTH, height=PLOT_HEIGHT, xrotation=45, labelled=["y"], invert_yaxis=True)
    return bars


hour_select = pn.widgets.IntRangeSlider(name="Hours: ", start=0, end=23, value=(2, 8))
day_select = pn.widgets.IntRangeSlider(name="Days: ", start=1, end=4, value=(2,3))
Time_range_map = pn.bind(time_range_plot, hours_range=hour_select, days_range=day_select)

operator_select = pn.widgets.RadioButtonGroup(options=list(COLORS.keys()))

Operators_maps = pn.bind(operator_plot, operator_name=operator_select)

Traffic_maps = pn.bind(traffic_plot, operator_name=operator_select)

aggregator_select = pn.widgets.RadioButtonGroup(options=list(AGGS.keys()))

RSRP_values_maps = pn.bind(RSRP_bar_plot, operator_name=operator_select, aggregator_method=aggregator_select)

template = pn.template.FastListTemplate(title="Telecom Analysis",
                                        main=[pn.Row(pn.Column("<h2>Usage During the Day</h2>", day_select, Time_range_map, hour_select), 
                                                     pn.Column("<h2>Users Per Operator</h2>", operator_select, Operators_maps)
                                                    ),
                                              pn.Row(pn.Column("<h2>Downlink Traffic Per Operator</h2>", operator_select, Traffic_maps),
                                                     pn.Column("<h2>RSRP per Operator per Device</h2>", operator_select, aggregator_select, RSRP_values_maps)
                                                    )
                                             ]
                                       )
template.servable()