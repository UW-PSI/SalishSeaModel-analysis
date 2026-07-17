# Created by Ben Roberts for the Puget Sound Institute with funding from King County

import os
from dataclasses import dataclass

import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd
from joblib import Parallel, delayed

from .vol_area_stats import VolAreaStats

@dataclass
class ExposureReturn:
    ssm_config: dict
    gdf: gpd.GeoDataFrame
    sizes: dict # sizes of the dimensions of DataArray that will be passed to apply()
    scope: str=None # Depth reduction, optional

    def __post_init__(self):
        self.stats = VolAreaStats(ssm_config=self.ssm_config, gdf=self.gdf, sizes=self.sizes, scope=self.scope)

        self.exposure = None
        self.net_exposure = None
        self.return_time = None
        self.partial_return = None
        self._exposure_by_day = None

    def apply(self, data_min: xr.DataArray, data_max: xr.DataArray = None):
        """Update data source and perform calculations"""
        if data_min.ndim == 2:
            # Create a single layer axis
            data_min = np.expand_dims(data_min, axis=1)
            if data_max is not None:
                data_max = np.expand_dims(data_max, axis=1)
        if data_min.shape != (self.stats.ndays,self.stats.nlevels,self.stats.nnodes):
            raise ValueError(f'Data has unexpected shape {data.shape} (should be ({self.stats.ndays},{self.stats.nlevels},{self.stats.nnodes})')
        min_vol_days = self.stats.apply(data_min)

        data_partial = data_min & ~data_max if data_max is not None else None
        self.exposure = self._calc_exposure_lengths(data_min)
        self.return_time = self._calc_exposure_lengths(data_min, is_return=True)
        self.partial_return = self._calc_exposure_lengths(~data_partial, is_return=True) if data_partial is not None else None
        # hmm, this is mathematically equivalent to just using data_max
        self.net_exposure = self._calc_exposure_lengths(data_min & ~data_partial) if data_partial is not None else None
        self._exposure_by_day = None

    def load(self, data_min, exposure, return_time, partial_return, net_exposure):
        """Load previously-computed exposure data"""
        self.stats.apply(data_min)
        self.exposure = exposure
        self.return_time = return_time
        self.partial_return = partial_return
        self.net_exposure = net_exposure
        self._exposure_by_day = None

    def _calc_exposure_lengths(self, d: xr.DataArray, is_return=False):
        """Per-node durations of boolean events as a masked DataArray"""
        # We're about to use nonzero to detect all the start and end days of
        # the condition for each node. But first there are some edge cases to
        # deal with. If the condition exists on the first day, there won't be
        # a corresponding start to the first end.
        # And if the condition exists on the last day, there won't be a
        # corresponding end to the first start.
        # The easy way to address this is to use np.pad() to add False values
        # on either end. This offsets the start and end dates, but that's okay
        # because we don't care (at this point) about detecting the exact dates
        # of each event.
        data_pad = np.pad(d, ((1,1),(0,0),(0,0)))
        # Detect changes by subtracting adjacent time points. A +1 means an
        # event began, a -1 means an event ended
        data_diff = data_pad[1:,:,:].astype(int) - data_pad[:-1,:,:].astype(int)
        if is_return:
            data_diff = -data_diff[:-1,:,:]
        starts = (data_diff == 1).nonzero()
        ends = (data_diff == -1).nonzero()
        # starts and ends are both lists of 3 arrays of indices.
        # First array is the day an event started/ended, second array
        # is the depth, third array is the node

        # An array of exposure lengths that are only non-NaN on the day the exposure begins
        exposure_lengths_start = np.ma.masked_all(d.shape, dtype=np.float16)
        def worker(n):
            for k in range(exposure_lengths_start.shape[1]):
                start_idxs = ((starts[1] == k) & (starts[2] == n)).nonzero()[0]
                if not len(start_idxs):
                    continue
                start_days = starts[0][start_idxs]
                end_idxs = ((ends[1] == k) & (ends[2] == n)).nonzero()[0]
                if is_return:
                    # Ignore the first "end" as it's not real
                    end_idxs = end_idxs[1:]
                end_days = ends[0][end_idxs]
                if is_return and len(end_days) < len(start_days):
                    # The year ends in a return condition, and because of earlier hacks we missed it
                    end_days = np.append(end_days, exposure_lengths_start.shape[0])
                # Assigning to a masked array by default unmasks those cells
                exposure_lengths_start[start_days,k,n] = end_days - start_days
        ns = [n for n in range(exposure_lengths_start.shape[-1]) if n in starts[2]]
        Parallel(n_jobs=len(os.sched_getaffinity(0)), prefer='threads')(delayed(worker)(n) for n in ns)
        # Single-threaded version
        #for n in ns: worker(n)
        return xr.DataArray(exposure_lengths_start.data, coords=d.coords).where(~exposure_lengths_start.mask)

    def _fill_by_day(self, v):
        by_day = xr.DataArray(np.full(v.shape, np.nan), dims=v.dims, coords=v.coords)
        def worker(n):
            for t,k in zip(*np.nonzero(~np.isnan(v[:,:,n].values))):
                e = v[t,k,n].astype(np.int16).item()
                by_day[t:t+e,k,n] = e
        ns = [n for n in range(v.sizes['node'])]
        Parallel(n_jobs=len(os.sched_getaffinity(0)), prefer='threads')(delayed(worker)(n) for n in ns)
        # Single-threaded version
        #for n in ns: worker(n)

        return by_day

    def get_exposure_by_day(self):
        """Fill in the NaNs for exposure days with the total duration of that exposure and return result"""
        if self._exposure_by_day is None:
            self._exposure_by_day = self._fill_by_day(self.exposure)
        return self._exposure_by_day

    def get_exposure_by_node(self):
        """Build and return GDF of various per-node exposure statistics"""
        # Get all-regions volume stats to determine worst day
        days, volume_days, pct_vol_day, daily_volumes = self.stats.get_vol_stats_by_region('all')
        worst_day = daily_volumes.argmax(axis=0)

        # FIXME this needs to be improved using a new masking system implemented in DepthReducer
        if self.sizes['siglay'] > 1:
            depth_weights = xr.DataArray(self.stats.depth_fraction, dims=('siglay',))
            exp_mean = self.exposure.weighted(weights=depth_weights)
            netexp_mean = self.net_exposure.weighted(weights=depth_weights)
        else:
            exp_mean = self.exposure
            netexp_mean = self.net_exposure

        duration_gdf = gpd.GeoDataFrame({
            'depth': self.gdf['depth'],
            'exp_max': self.exposure.max(axis=(0,1)).astype(np.float32),
            'exp_mean': exp_mean.mean(dim=('siglay','day')).astype(np.float32),
            'exp_sum': self.exposure.sum(dim='day').max(dim='siglay').astype(np.float32),
            'netexp_max': self.net_exposure.max(axis=(0,1)).astype(np.float32),
            'netexp_mean': netexp_mean.mean(dim=('siglay','day')).astype(np.float32),
            'netexp_sum': self.net_exposure.sum(dim='day').max(dim='siglay').astype(np.float32),
            'exposure_worst': self.exposure.isel(day=worst_day).max(dim='siglay').astype(np.float32)
        }, geometry=self.gdf.geometry, index=self.gdf.index, crs=self.gdf.crs)
        return duration_gdf

    def get_duration_stats_by_region(self, region: str):
        """Compute region aggregated statistics"""
        if self.exposure is None:
            raise ValueError("run apply first")

        if region == 'all':
            idx = (self.gdf['included_i'] == 1)
        else:
            idx = ((self.gdf['Regions'] == region) &
                (self.gdf['included_i'] == 1))
        # Converting the indexer to a mask is much faster in some situations
        mask = xr.DataArray(np.broadcast_to(idx, self.exposure.shape), dims=self.exposure.dims)
        vol_masked = self.stats.volume.where(xr.DataArray(np.broadcast_to(idx, self.stats.volume.shape), dims=self.stats.volume.dims), 0)
        area_masked = self.stats.area.where(xr.DataArray(idx, dims='node'), 0)
        # Convenience measure of region nodes
        nrnodes = idx.sum()

        RegionVolumes = self.stats.volume[:,idx].sum(axis=0)
        assert RegionVolumes.shape == (nrnodes,), RegionVolumes.shape

        max_exposures = self.exposure.where(mask).max(dim=('day','siglay'))
        median_exposures = self.exposure.where(mask).median(dim='day').weighted(vol_masked).mean(dim='siglay')
        mean_exposures = self.exposure.where(mask).mean(dim='day').weighted(vol_masked).mean(dim='siglay')
        max_returns = self.return_time.where(mask).max(dim=('day','siglay'))
        median_returns = self.return_time.where(mask).median(dim='day').weighted(vol_masked).mean(dim='siglay')
        mean_returns = self.return_time.where(mask).mean(dim='day').weighted(vol_masked).mean(dim='siglay')
        max_netexps = self.net_exposure.where(mask).max(dim=('day','siglay'))
        median_netexps = self.net_exposure.where(mask).median(dim='day').weighted(vol_masked).mean(dim='siglay')
        mean_netexps = self.net_exposure.where(mask).mean(dim='day').weighted(vol_masked).mean(dim='siglay')

        ret = {
            'Exposure_Count_Per_Vol': (self.exposure.where(mask).count() / RegionVolumes.sum()).item(),
            'Med_Exposure_MinCell': median_exposures.min().item(),
            'Med_Exposure': median_exposures.weighted(area_masked).mean().item(),
            'Med_Exposure_MaxCell': median_exposures.max().item(),
            'Mean_Exposure_MinCell': mean_exposures.min().item(),
            'Mean_Exposure': mean_exposures.weighted(area_masked).mean().item(),
            'Mean_Exposure_MaxCell': mean_exposures.max().item(),
            'Max_Exposure_MinCell': max_exposures.min().item(),
            'Max_Exposure': max_exposures.weighted(area_masked).mean().item(),
            'Max_Exposure_MaxCell': max_exposures.max().item(),

            'Med_ReturnTime_MinCell': median_returns.min().item(),
            'Med_ReturnTime': median_returns.weighted(area_masked).mean().item(),
            'Med_ReturnTime_MaxCell': median_returns.max().item(),
            'Mean_ReturnTime_MinCell': mean_returns.min().item(),
            'Mean_ReturnTime': mean_returns.weighted(area_masked).mean().item(),
            'Mean_ReturnTime_MaxCell': mean_returns.max().item(),
            'Max_ReturnTime_MinCell': max_returns.min().item(),
            'Max_ReturnTime': max_returns.weighted(area_masked).mean().item(),
            'Max_ReturnTime_MaxCell': max_returns.max().item(),

            'Med_Net_Exposure_MinCell': median_netexps.min().item(),
            'Med_Net_Exposure': median_netexps.weighted(area_masked).mean().item(),
            'Med_Net_Exposure_MaxCell': median_netexps.max().item(),
            'Mean_Net_Exposure_MinCell': mean_netexps.min().item(),
            'Mean_Net_Exposure': mean_netexps.weighted(area_masked).mean().item(),
            'Mean_Net_Exposure_MaxCell': mean_netexps.max().item(),
            'Max_Net_Exposure_MinCell': max_netexps.min().item(),
            'Max_Net_Exposure': max_netexps.weighted(area_masked).mean().item(),
            'Max_Net_Exposure_MaxCell': max_netexps.max().item()
        }

        return ret
