# Prototype for px.combine
# Combine 2 figures containing subplots
# Run as
# python px_combine.py

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import test_data
import json
from itertools import product


def multi_index(*kwargs):
    return product(*[range(k) for k in kwargs])


def extract_axes(layout):
    ret = dict()
    for k in dir(layout):
        if k[1 : 1 + len("axis")] == "axis":
            ret[k] = layout[k]
    return ret


def fig_grid_ref_shape(fig):
    grid_ref = fig._validate_get_grid_ref()
    return (len(grid_ref), len(grid_ref[0]))


def fig_subplot_axes(fig, r, c):
    grid_ref = fig._validate_get_grid_ref()
    return [fig.layout[k] for k in grid_ref[r - 1][c - 1][0].layout_keys]


def extract_axis_titles(fig):
    """
    Given figure created using make_subplots, with r rows and c columns, return
    r titles from the x axes and y titles from the y axes.
    """
    grid_ref_shape = fig_grid_ref_shape(fig)
    r_titles = [
        fig_subplot_axes(fig, r + 1, 1)[1]["title"] for r in range(grid_ref_shape[0])
    ]
    c_titles = [
        fig_subplot_axes(fig, 1, c + 1)[0]["title"] for c in range(grid_ref_shape[1])
    ]
    return (r_titles, c_titles)


def px_simple_combine(fig0, fig1):
    """
    Combines two figures by just using the layout of the first figure and
    appending the data of the second figure.
    """
    grid_ref_shape = fig_grid_ref_shape(fig0)
    if grid_ref_shape != fig_grid_ref_shape(fig1):
        raise ValueError(
            "Only two figures with the same subplot geometry can be combined."
        )
    if fig0.layout.annotations != fig1.layout.annotations:
        raise ValueError(
            "Only two figures created with Plotly Express with "
            "identical faceting can be combined."
        )
    fig = go.Figure(data=fig0.data + fig1.data, layout=fig0.layout)
    return fig


def px_combine_secondary_y(fig0, fig1):
    """
    Combines two figures that have the same faceting but whose y axes refer
    to different data by referencing the second figure's y-data to secondary
    y-axes.
    """
    grid_ref_shape = fig_grid_ref_shape(fig0)
    if grid_ref_shape != fig_grid_ref_shape(fig1):
        raise ValueError(
            "Only two figures with the same subplot geometry can be combined."
        )
    if fig0.layout.annotations != fig1.layout.annotations:
        raise ValueError(
            "Only two figures created with Plotly Express with "
            "identical faceting can be combined."
        )
    specs = [
        [dict(secondary_y=True) for __ in range(grid_ref_shape[1])]
        for _ in range(grid_ref_shape[0])
    ]
    fig = make_subplots(*grid_ref_shape, specs=specs, start_cell="bottom-left")
    fig0_ax_titles = extract_axis_titles(fig0)
    fig1_ax_titles = extract_axis_titles(fig1)
    # set primary y
    for r, c in multi_index(*grid_ref_shape):
        for tr in fig0.select_traces(row=r + 1, col=c + 1):
            fig.add_trace(tr, row=r + 1, col=c + 1)
        if r == 0:
            t = fig0_ax_titles[1][c]
            fig.update_xaxes(title=t, row=r + 1, col=c + 1)
        if c == 0:
            t = fig0_ax_titles[0][r]
            fig.update_yaxes(
                selector=lambda ax: ax["side"] != "right", title=t, row=r + 1, col=c + 1
            )
    # set secondary y
    for r, c in multi_index(*grid_ref_shape):
        for tr in fig1.select_traces(row=r + 1, col=c + 1):
            # TODO: How to set meaningful color regardless of trace type?
            tr["marker_color"] = "red"
            fig.add_trace(tr, row=r + 1, col=c + 1, secondary_y=True)
        t = fig1_ax_titles[0][r]
        # TODO: How to best set the secondary y's title standoff?
        t["standoff"] = 0
        fig.update_yaxes(
            selector=lambda ax: ax["side"] == "right", title=t, row=r + 1, col=c + 1
        )
    fig.update_layout(annotations=fig0.layout.annotations)
    return fig


df = test_data.aug_tips()


def simple_combine_example():
    fig0 = px.scatter(df, x="total_bill", y="tip", facet_row="sex", facet_col="smoker")
    fig1 = px.histogram(
        df, x="total_bill", y="tip", facet_row="sex", facet_col="smoker"
    )
    fig1.update_traces(marker_color="red")
    fig = px_simple_combine(fig0, fig1)
    fig.update_layout(title="Simple figure combination")
    return fig


def secondary_y_combine_example():
    fig0 = px.scatter(df, x="total_bill", y="tip", facet_row="sex", facet_col="smoker")
    fig1 = px.scatter(
        df,
        x="total_bill",
        y="calories_consumed",
        facet_row="sex",
        facet_col="smoker",
        trendline="ols",
    )
    fig1.update_traces(marker_size=3)
    fig = px_combine_secondary_y(fig0, fig1)
    fig.update_layout(title="Figure combination with secondary y-axis")
    return fig


fig_simple = simple_combine_example()
fig_secondary_y = secondary_y_combine_example()
fig_simple.show()
fig_secondary_y.show()
