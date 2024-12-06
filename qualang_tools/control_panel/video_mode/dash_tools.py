from abc import ABC, abstractmethod
from enum import Flag, auto
from typing import Any, Dict, List, Literal, Optional

from dash import html
import plotly.graph_objects as go
import xarray as xr
import dash_bootstrap_components as dbc


__all__ = ["xarray_to_plotly", "BaseDashComponent", "ModifiedFlags"]


class ModifiedFlags(Flag):
    """Flags indicating what needs to be modified after parameter changes."""

    NONE = 0
    PARAMETERS_MODIFIED = auto()
    PROGRAM_MODIFIED = auto()
    CONFIG_MODIFIED = auto()


class BaseDashComponent(ABC):
    def __init__(self, *args, component_id: str, **kwargs):
        assert not args, "BaseDashComponent does not accept any positional arguments"
        assert not kwargs, "BaseDashComponent does not accept any keyword arguments"

        self.component_id = component_id

    def update_parameters(self, parameters: Dict[str, Dict[str, Any]]) -> ModifiedFlags:
        """Update the component's attributes based on the input values."""
        return ModifiedFlags.NONE

    def get_dash_components(self, include_subcomponents: bool = True) -> List[html.Div]:
        """Return a list of Dash components.

        Args:
            include_subcomponents (bool, optional): Whether to include subcomponents. Defaults to True.

        Returns:
            List[html.Div]: A list of Dash components.
        """
        return []

    def get_component_ids(self) -> List[str]:
        """Return a list of component IDs for this component including subcomponents."""
        return [self.component_id]


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

    y_label, y_coord = next(coords_iter)
    y_label = y_coord.attrs.get("long_name", y_label)
    y_unit = y_coord.attrs.get("units", "")

    x_label, x_coord = next(coords_iter)
    x_label = x_coord.attrs.get("long_name", x_label)
    x_unit = x_coord.attrs.get("units", "")

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


def create_input_field(
    id,
    label,
    value,
    debounce=True,
    input_style=None,
    div_style=None,
    units=None,
    **kwargs,
):
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
    if units is not None:
        elements.append(dbc.Col(dbc.Label(units, className="ml-2"), width="auto"))

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
    component_id: Optional[str] = None,
):
    if component_id is None:
        ids = {"span": f"{axis.lower()}-span", "points": f"{axis.lower()}-points"}
    else:
        ids = {
            "span": {"type": component_id, "index": f"{axis.lower()}-span"},
            "points": {"type": component_id, "index": f"{axis.lower()}-points"},
        }
    return dbc.Col(
        dbc.Card(
            [
                dbc.CardHeader(axis.upper()),
                dbc.CardBody(
                    [
                        create_input_field(
                            id=ids["span"],
                            label="Span",
                            value=span,
                            min=min_span,
                            max=max_span,
                            input_style={"width": "100px"},
                            units=units,
                        ),
                        create_input_field(
                            id=ids["points"],
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
