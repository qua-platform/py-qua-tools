from importlib import metadata

from qcodes.parameters import ManualParameter
from qcodes.dataset import Measurement
import numpy as np
import xarray as xr
import json



def _register_meas_params(meas, names, units, setpoints):
    for name, unit, setpoint in zip(names, units, setpoints):
        meas.register_custom_parameter(name, name, unit, setpoints=setpoint)


def _reshape_args(args):
    reshaped_args = np.array(list(args), dtype=object).reshape(-1, 3)

    names = reshaped_args[:, 0]
    units = reshaped_args[:, 1]
    values = reshaped_args[:, 2]

    return names, units, values


def _save_metadata(datasaver, metadata):
    for tag, value in (metadata or {}).items():
        if value is None:
            continue

        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        datasaver.dataset.add_metadata(tag, value)


def save_1d(setpoint_name, setpoint_unit, setpoint_vals, *args, metadata=None):
    if len(args) % 3 != 0:
        raise Exception(
            "all measured things must be specified with: name, unit, values"
        )

    setpoint_param = ManualParameter(setpoint_name, unit=setpoint_unit)

    names, units, values = _reshape_args(args)

    setpoints = [(setpoint_param,)] * names.shape[0]

    meas = Measurement()
    meas.register_parameter(setpoint_param)

    _register_meas_params(meas, names, units, setpoints)

    with meas.run() as datasaver:
        datasaver.add_result((setpoint_param, setpoint_vals),*list(zip(names, values)))

        _save_metadata(datasaver, metadata)

    return datasaver.run_id


def save_2d(
    setpoint_rows_name,
    setpoint_rows_unit,
    setpoint_rows_vals,
    setpoint_columns_name,
    setpoint_columns_unit,
    setpoint_columns_vals,
    *args,
    metadata=None,
):
    if len(args) % 3 != 0:
        raise Exception(
            "all measured things must be specified with: name, unit, values"
        )

    setpoint_columns_param = ManualParameter(
        setpoint_columns_name, unit=setpoint_columns_unit
    )
    setpoint_rows_param = ManualParameter(setpoint_rows_name, unit=setpoint_rows_unit)

    names, units, values = _reshape_args(args)
    for i, value in enumerate(values):
        values[i] = value.flatten()

    setpoints = [
        (
            setpoint_columns_param,
            setpoint_rows_param,
        )
    ] * names.shape[0]

    meas = Measurement()
    meas.register_parameter(setpoint_columns_param)
    meas.register_parameter(setpoint_rows_param)

    _register_meas_params(meas, names, units, setpoints)

    with meas.run() as datasaver:
        datasaver.add_result(
            (
                setpoint_rows_param,
                np.repeat(setpoint_rows_vals, len(setpoint_columns_vals)),
            ),
            (
                setpoint_columns_name,
                np.tile(setpoint_columns_vals, len(setpoint_rows_vals)),
            ),
            *list(zip(names, values)),
        )

        _save_metadata(datasaver, metadata)

    return datasaver.run_id


def save_xarray(
    data: xr.DataArray,
    *,
    name: str = "data",
    annotations=None,
    metadata=None,
):
    if not isinstance(data, xr.DataArray):
        raise TypeError("data must be an xarray.DataArray")

    data_name = data.name or name
    data_unit = data.attrs.get(
        "unit",
        data.attrs.get("units", ""),
    )

    save_metadata = dict(metadata or {})

    if annotations is not None:
        save_metadata["annotations"] = annotations

    # Single measured parameter
    if data.ndim == 1:
        x_dim = data.dims[0]
        x_coord = data.coords[x_dim]

        x_unit = x_coord.attrs.get(
            "unit",
            x_coord.attrs.get("units", ""),
        )

        return save_1d(
            x_dim,
            x_unit,
            x_coord.values,
            data_name,
            data_unit,
            data.values,
            metadata=save_metadata,
        )

    # Single measured parameter over a 2D sweep
    if data.ndim == 2:
        y_dim, x_dim = data.dims

        x_coord = data.coords[x_dim]
        y_coord = data.coords[y_dim]

        x_unit = x_coord.attrs.get(
            "unit",
            x_coord.attrs.get("units", ""),
        )
        y_unit = y_coord.attrs.get(
            "unit",
            y_coord.attrs.get("units", ""),
        )

        return save_2d(
            y_dim,
            y_unit,
            y_coord.values,
            x_dim,
            x_unit,
            x_coord.values,
            data_name,
            data_unit,
            data.values,
            metadata=save_metadata,
        )

    # Multiple measured parameters sharing the same 2D sweep
    if "readout" in data.dims:
        sweep_dims = [
            dim for dim in data.dims
            if dim != "readout"
        ]

        if len(sweep_dims) != 2:
            raise ValueError(
                "Multi-readout data must contain exactly two sweep dimensions."
            )

        y_dim, x_dim = sweep_dims

        x_coord = data.coords[x_dim]
        y_coord = data.coords[y_dim]

        x_unit = x_coord.attrs.get(
            "unit",
            x_coord.attrs.get("units", ""),
        )
        y_unit = y_coord.attrs.get(
            "unit",
            y_coord.attrs.get("units", ""),
        )

        measured_args = []

        for readout_name in data.coords["readout"].values:
            signal = data.sel(readout=readout_name)

            measured_args.extend(
                [
                    str(readout_name),
                    data_unit,
                    signal.values,
                ]
            )

        return save_2d(
            y_dim,
            y_unit,
            y_coord.values,
            x_dim,
            x_unit,
            x_coord.values,
            *measured_args,
            metadata=save_metadata,
        )

    raise ValueError(
        f"Unsupported DataArray dimensions: {data.dims}"
    )