from typing import Literal, Optional
from dash import html
from dash_extensions.enrich import dcc
import plotly.graph_objects as go
import xarray as xr
import dash_bootstrap_components as dbc


__all__ = ["xarray_to_plotly"]


def xarray_to_plotly(da: xr.DataArray):
    """Convert an xarray DataArray to a Plotly figure.

    Args:
        da (xr.DataArray): The data array to convert.

    Returns:
        plotly.graph_objects.Figure: A Plotly figure with the data.
    """
    if len(da.coords) != 2:
        raise ValueError("DataArray must have exactly 2 coordinates.")

    coords_iter = iter(da.coords.items())
    x_label, x_coord = next(coords_iter)
    x_label = x_coord.attrs.get("long_name", x_label)
    x_unit = x_coord.attrs.get("units", "")

    y_label, y_coord = next(coords_iter)
    y_label = y_coord.attrs.get("long_name", y_label)
    y_unit = y_coord.attrs.get("units", "")

    z_label = da.attrs.get("long_name", da.name or "Value")
    z_unit = da.attrs.get("units", "")

    xaxis_label = f"{x_label} ({x_unit})" if x_unit else x_label
    yaxis_label = f"{y_label} ({y_unit})" if y_unit else y_label
    zaxis_label = f"{z_label} ({z_unit})" if z_unit else z_label

    fig = go.Figure(
        go.Heatmap(
            z=da.values,
            x=x_coord.values,
            y=y_coord.values,
            colorscale="plasma",
            colorbar=dict(title=zaxis_label),
        )
    )
    fig.update_layout(xaxis_title=xaxis_label, yaxis_title=yaxis_label)
    return fig


def create_input_field(id, label, value, debounce=True, input_style=None, div_style=None, unit=None, **kwargs):
    if input_style is None:
        input_style = {"width": "80px"}

    elements = [
        dbc.Col(
            dbc.Label(
                f"{label}:",
                html_for=id,
                className="mr-2",
                style={"white-space": "nowrap"},
            ),
            width="auto",
        ),
        dbc.Col(
            dbc.Input(
                id=id,
                type="number",
                value=value,
                debounce=debounce,
                style=input_style,
                **kwargs,
            ),
            width="auto",
        ),
    ]
    if unit is not None:
        elements.append(dbc.Col(dbc.Label(unit, className="ml-2"), width="auto"))

    return dbc.Row(
        elements,
        className="align-items-center mb-2",
        style=div_style,
    )


def create_axis_layout(
    axis: Literal["x", "y"],
    span: float,
    points: int,
    min_span: float,
    max_span: Optional[float] = None,
    units: Optional[str] = None,
):
    return dbc.Col(
        dbc.Card(
            [
                dbc.CardHeader(axis.upper()),
                dbc.CardBody(
                    [
                        create_input_field(
                            id=f"{axis.lower()}-span",
                            label="Span",
                            value=span,
                            min=min_span,
                            max=max_span,
                            input_style={"width": "100px"},
                            unit=units,
                        ),
                        create_input_field(
                            id=f"{axis.lower()}-points",
                            label="Points",
                            value=points,
                            min=1,
                            max=501,
                            step=1,
                        ),
                    ]
                ),
            ],
            className="h-100",
        ),
        md=6,
        className="mb-3",
    )
