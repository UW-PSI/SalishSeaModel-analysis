# Created by Ben Roberts at the Puget Sound Institude with funding from King County

from dataclasses import dataclass

import numpy as np
import xarray as xr
import geopandas as gpd

SCOPES = {
    'tp': 'Top layer',
    'bt': 'Bottom layer',
    'md': 'Mid-layer minimum',
    'mA': 'Mid-layer mean (naive)',
    'wA': 'Water column mean (naive)',
    'wc': 'Water column minimum',
    'depth': 'Single layer containing given depth'
}

@dataclass
class DepthReducer():
    """Class primarily for performing depth dimensional reductions

    Once initialized, it also includes a calculated DataArray property
    layer_depths which contains the depths at the intravertical
    boundaries of each cell.
    """
    ssm_config: dict
    gdf: gpd.GeoDataFrame

    def __post_init__(self):
        # Back-calculate the intra-vertical levels
        assert np.abs(np.sum(self.ssm_config['siglev_diff']) - 100) < 0.01, 'Siglev_diff does not sum to 100'
        self.z = np.cumsum([0] + self.ssm_config['siglev_diff']) / 100
        self.zz = .5 * (self.z[:-1] + self.z[1:])
        self.layer_depths = xr.DataArray(
                np.expand_dims(self.z, axis=1) @ np.expand_dims(self.gdf.depth * 1000, axis=0),
                dims=('siglev','node')
            )

    def select_depth(self, data: xr.DataArray, mode: str, **kwargs):
        """Given the DataArray data containing a siglay depth dimension, reduce it.

        Options:
        tp: take top layer
        bt: take bottom layer
        md: take the minimum value of the mid layers
        mA: take the mean value of the mid layers
        wA: take the mean value of all water column layers
        wc: take the water column minimum

        depth: take the layer containing a given water depth. Pass 'depth' as
            additional parameter.
        """
        if mode == 'tp':
            ret = data.isel(siglay=0)
        elif mode == 'bt':
            ret = data.isel(siglay=-1)
        elif mode == 'md':
            ret = data.isel(siglay=slice(1,-1)).min(dim='siglay')
        elif mode == 'mA':
            # FIXME not a weighted mean
            ret = data.isel(siglay=slice(1,-1)).mean(dim='siglay')
        elif mode == 'wA':
            # FIXME not a weighted mean
            ret = data.mean(dim='siglay')
        elif mode == 'wc':
            ret = data.min(dim='siglay')
        elif mode == 'depth':
            # Find all depth boundaries above the target depth
            above = self.layer_depths.where(self.layer_depths < kwargs['depth'])
            # Pick the largest (deepest) one to find the layer cutoff above.
            # Add one to get the insert position of this depth into the
            # intravertical layers.
            insert_position = above.argmax(dim='siglev') + 1
            # Some nodes have the value sizes['siglev'], indicating that the
            # last index was still smaller than depth. We're going to replace
            # those cell values with NaN before the selection, but it will still
            # lead to an indexing error so replace those with a valid index.
            insert_position.loc[insert_position == len(self.z)] = 0

            # Now select the data, by first dropping any values for nodes
            # above the target depth so we get NaNs there.
            max_depth_xd = np.broadcast_to(self.layer_depths[-1], data.shape)
            ret = data.where(max_depth_xd > kwargs['depth']).isel(siglay=insert_position)
        # TODO: depth_below and depth_above
        return ret
