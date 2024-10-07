from dash import html
from dash_extensions.enrich import dcc
import plotly.graph_objects as go
import xarray as xr


__all__ = ["xarray_to_plotly"]


def xarray_to_plotly(da: xr.DataArray):
    """Convert an xarray DataArray to a Plotly figure.

    Args:
        da (xr.DataArray): The data array to convert.

    Returns:
        plotly.graph_objects.Figure: A Plotly figure with the data.
    """
    x_label = da.coords["x"].attrs.get("long_name", "x")
    x_unit = da.coords["x"].attrs.get("units", "")
    y_label = da.coords["y"].attrs.get("long_name", "y")
    y_unit = da.coords["y"].attrs.get("units", "")
    z_label = da.attrs.get("long_name", da.name or "Value")
    z_unit = da.attrs.get("units", "")

    xaxis_label = f"{x_label} ({x_unit})" if x_unit else x_label
    yaxis_label = f"{y_label} ({y_unit})" if y_unit else y_label
    zaxis_label = f"{z_label} ({z_unit})" if z_unit else z_label

    fig = go.Figure(
        go.Heatmap(
            z=da.values,
            x=da.coords["x"].values,
            y=da.coords["y"].values,
            colorscale="plasma",
            colorbar=dict(title=zaxis_label),
        )
    )
    fig.update_layout(xaxis_title=xaxis_label, yaxis_title=yaxis_label)
    return fig


def create_input_field(id, label, value, debounce=True, input_style=None, div_style=None, unit=None, **kwargs):
    if input_style is None:
        input_style = {"width": "40px"}

    elements = [
        html.Label(
            f"{label}:",
            style={
                "text-align": "left",
                "white-space": "nowrap",
                "margin-left": "15px",
                "margin-right": "5px",
            },
        ),
        dcc.Input(
            id=id,
            type="number",
            value=value,
            debounce=debounce,
            style=input_style,
            **kwargs,
        ),
    ]
    if unit is not None:
        elements.append(html.Label(unit, style={"text-align": "left", "margin-left": "15px"}))

    if div_style is not None:
        div_style = {"display": "flex", "margin-bottom": "10px"}

    return html.Div(elements, style=div_style)


def create_axis_layout(axis, span, points, min_span, max_span):
    return html.Div(
        [
            html.Label(axis.upper(), style={"text-align": "left"}),
            create_input_field(
                id=f"{axis.lower()}-span",
                label="Span",
                value=span,
                min=min_span,
                max=max_span,
                input_style={"width": "55px"},
                div_style={"display": "flex", "margin-bottom": "10px"},
                unit="V",
            ),
            create_input_field(
                id=f"{axis.lower()}-points",
                label="Points",
                value=points,
                min=1,
                max=501,
                step=1,
                div_style={"display": "flex", "margin-bottom": "10px"},
            ),
        ],
        style={"display": "flex", "flex-direction": "row", "flex-wrap": "wrap"},
    )
