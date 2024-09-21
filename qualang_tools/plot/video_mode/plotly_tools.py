import plotly.graph_objects as go
import xarray as xr
import logging


__all__ = ["xarray_to_plotly"]

# Configure logging
logging.basicConfig(level=logging.DEBUG)


def xarray_to_plotly(da: xr.DataArray):
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
    logging.debug("Created Plotly figure from xarray DataArray")
    return fig
