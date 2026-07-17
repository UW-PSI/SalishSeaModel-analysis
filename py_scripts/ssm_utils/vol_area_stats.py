# Created by Ben Roberts for the Puget Sound Institude with funding from King County

from dataclasses import dataclass
import logging

import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd

from .depth import DepthReducer

logger = logging.getLogger('ssm_utils.vol_area_stats')

@dataclass
class VolAreaStats:
    """Class for computing volume days, daily volumes, areas, etc

    Operates on any part of the grid that meets a certain condition, so it's
    agnostic to measurements of DO, MI, ... and also doesn't care what those
    quantities are being compared to.
    """
    ssm_config: dict
    gdf: gpd.GeoDataFrame
    sizes: dict
    scope: str = None

    def __post_init__(self):
        # Purely for readability
        if len(self.sizes) == 2:
            self.ndays, self.nnodes = self.sizes.values()
            self.nlevels = 1
        else:
            self.ndays, self.nlevels, self.nnodes = self.sizes.values()
        assert len(self.gdf) == self.nnodes, f"Node count {self.nnodes} does not match GDF length {len(self.gdf)}"

        self.depth_fraction = np.array(self.ssm_config['siglev_diff']) / 100
        self.volume = xr.DataArray(
                np.expand_dims(self.depth_fraction, axis=1) @ np.expand_dims(self.gdf.volume, axis=0),
                dims={d: v for d,v in self.sizes.items() if d != 'time' and d != 'day'})
        if self.nlevels > 1:
            # Notice how I'm using assert statements to document what shape
            # variables have. This prevents having to guess whether a comment is
            # accurate or not, because if the code runs, it must be right.
            assert self.depth_fraction.shape == (self.nlevels,), f"Level count {self.nlevels} does not match case sigma layer count {len(self.depth_fraction)}"
        elif self.scope is not None:
            dr = DepthReducer(self.ssm_config, self.gdf)
            # Run the same depth reduction on the volume matrix, then add a
            # size-1 depth dimension so our math still works out
            # FIXME this only makes sense for simple modes like tp and bt!
            self.volume = dr.select_depth(self.volume, self.scope).expand_dims(dim='siglay',axis=0)
        else:
            raise ValueError("scope argument is required when level count == 1")
        assert self.volume.shape == (self.nlevels,self.nnodes), self.volume.shape

        self.area = xr.DataArray(self.gdf.Area_m2.to_numpy() * 1e-6, dims={'node': self.nnodes})
        assert self.area.shape == (self.nnodes,), self.area.shape

        self.data = None
        self.VolumeDays = None

    def apply(self, data: xr.DataArray):
        """Update data source for calculations and get volume days"""
        if data.ndim == 2:
            # Create a single layer axis
            self.data = np.expand_dims(data, axis=1)
        else:
            self.data = data
        if self.data.sizes != self.sizes:
            raise ValueError(f'Data has unexpected shape {data.shape} (should be {tuple(self.sizes.values())})')

        # Done for backwards compatibility
        return self.get_volume_days()

    def get_volume_days(self):
        days = self.data.sum(axis=0,initial=0)
        assert days.shape == (self.nlevels,self.nnodes), days.shape

        self.VolumeDays = (self.volume * days).sum(axis=0)
        assert self.VolumeDays.shape == (self.nnodes,), self.VolumeDays.shape
        return self.VolumeDays

    def get_area_days(self):
        days = self.data.any(dim='siglay').sum(dim='day', initial=0)
        assert days.shape == (self.nnodes,), days.shape

        self.AreaDays = self.area * days
        return self.AreaDays

    def get_vol_stats_by_region(self, region: str):
        """Compute volume statistics by region, pass "all" for all regions"""
        if self.VolumeDays is None:
            raise ValueError('Run apply first')
        if region == 'all':
            idx = (self.gdf['included_i'] == 1).values
        else:
            idx = ((self.gdf['Regions'] == region) &
                (self.gdf['included_i'] == 1)).values
        # Convenience measure of region nodes
        nrnodes = np.sum(idx)

        # Find number of (unique) days in region by node
        Days = self.data[:,:,idx].any(axis=(1,2)).sum().item()

        VolumeDays = self.VolumeDays[idx].sum().item()

        RegionVolumes = self.volume[:,idx].sum(axis=0)
        assert RegionVolumes.shape == (nrnodes,), RegionVolumes.shape

        PercentVolumeDays = 100 * (VolumeDays / (RegionVolumes.sum() * self.ndays)).item()

        DailyVolumes = (self.volume[:,idx] * self.data[:,:,idx]).sum(dim=('siglay','node'))
        assert DailyVolumes.shape == (self.ndays,), DailyVolumes.shape

        return Days, VolumeDays, PercentVolumeDays, DailyVolumes

    def get_area_stats_by_region(self, region: str):
        """Compute area statistics by region, pass "all" for all regions"""
        if self.data is None:
            raise ValueError('Run apply first')
        if region == 'all':
            idx = (self.gdf['included_i'] == 1).values
        else:
            idx = ((self.gdf['Regions'] == region) &
                (self.gdf['included_i'] == 1)).values
        # Convenience measure of region nodes
        nrnodes = np.sum(idx)

        RegionArea = (self.area[idx] * self.data[:,:,idx].any(axis=(0,1))).sum().item()

        DailyAreas = (self.area[idx] * self.data[:,:,idx].any(dim='siglay')).sum(dim='node')
        assert DailyAreas.shape == (self.ndays,), DailyAreas.shape

        return RegionArea, DailyAreas

    def get_day_stats_by_region(self, region: str):
        """Compute duration-based statistics by region"""
        if self.VolumeDays is None:
            raise ValueError('Run apply first')
        if region == 'all':
            idx = (self.gdf['included_i'] == 1).values
        else:
            idx = ((self.gdf['Regions'] == region) &
                (self.gdf['included_i'] == 1)).values
        # Find number of (unique) days in region by node
        Days = self.data[:,:,idx].any(axis=(1,2)).sum().item()

        # Total days of below-threshold condition aggregated spatially
        TotalDays = self.data[:,:,idx].any(axis=1).sum().item()

        return Days, TotalDays

def create_statistics_dataframes(case: str, ssm_config: dict, dtype: str,
                                 daily_data: dict, habitat_mask: xr.DataArray=None,
                                 scope=None):
    """Create DataFrames for daily volume statistics - ready for Excel export

    Parameters:
    case: case name
    ssm_config: dict of case configuration
    dtype: str either 'node', 'area' or 'volume', basically only affects row headers and
        percentage calculations
    daily_data: dict of scenarios, each containing a dict of regions,
        mapping to dataframes containing per-region daily volumes/areas/nodes
    habitat_mask: optional boolean DataArray with dims siglay x node that allows
        including habitat area statistics. 'True' means the cell is habitat.
    scope: if a depth reduction was applied, the reduction parameter may be required

    Returns:
    dict of DataFrames keyed by run scenario containing the formatted table
    """
    # Get regional "volume" totals
    # Note that this function may be working with either node count, area or volume, but
    # the process is essentially the same. Don't take the variable names too
    # literally!
    shp = ssm_config['paths']['shapefile']
    gdf = gpd.read_file(shp)
    if len(gdf) == 16013:
        logger.warning('Correcting shapefile length')
        gdf = gdf.iloc[:-1].copy()
    if habitat_mask is not None:
        stats = VolAreaStats(ssm_config=ssm_config, gdf=gdf, scope=scope,
                             sizes={'day': 1} | dict(habitat_mask.sizes))
        habitat_node_volumes = stats.volume.where(np.broadcast_to(gdf['included_i'] == 1, stats.volume.shape) & habitat_mask).sum(dim='siglay')
        gdf['vol_habitat'] = habitat_node_volumes
        hab_mask_node = habitat_mask.any(dim='siglay').data
        hab_node_idx = (gdf['included_i'] == 1) & hab_mask_node
        habitat_node_areas = stats.area.where(xr.DataArray(hab_node_idx, dims=('node',)))
        gdf['area_habitat'] = habitat_node_areas
        gdf['is_habitat'] = hab_node_idx
    if dtype == 'volume':
        regional_total_volumes = gdf.loc[gdf['included_i'] == 1].groupby('region_inf')['volume'].sum().to_dict()
        regional_total_volumes['All_regions'] = gdf.loc[gdf['included_i'] == 1, 'volume'].sum()
        if habitat_mask is not None:
            regional_habitat_volumes = gdf.groupby('region_inf')['vol_habitat'].sum().to_dict()
            regional_habitat_volumes['All_regions'] = gdf['vol_habitat'].sum()
    elif dtype == 'area':
        regional_total_volumes = (gdf.loc[gdf['included_i'] == 1].groupby('region_inf')['Area_m2'].sum() * 1e-6).to_dict()
        regional_total_volumes['All_regions'] = gdf.loc[gdf['included_i'] == 1, 'Area_m2'].sum() * 1e-6
        if habitat_mask is not None:
            regional_habitat_volumes = gdf.groupby('region_inf')['area_habitat'].sum().to_dict()
            regional_habitat_volumes['All_regions'] = gdf['area_habitat'].sum()
    else: # Node count
        regional_total_volumes = gdf.loc[gdf['included_i'] == 1].groupby('region_inf')['volume'].count().to_dict()
        regional_total_volumes['All_regions'] = len(np.nonzero(gdf['included_i'] == 1)[0])
        if habitat_mask is not None:
            regional_habitat_volumes = gdf.groupby('region_inf')['is_habitat'].sum().to_dict()
            regional_habitat_volumes['All_regions'] = gdf['is_habitat'].sum()

    labels = ssm_config['run_information']['run_tag'][case]

    dataframes = {}

    # Create DataFrame with correct column order
    if dtype == 'volume':
        label = 'Vol'
        unit = 'km³'
    elif dtype == 'area':
        label = 'Area'
        unit = 'km²'
    else:
        label = 'Nodes'
        unit = 'count'
    columns = [
        'Region', f'Total_{label}_{unit}', f'Avg_{label}_{unit}',
        f'Avg{label}_%ofTotal', f'Avg{label}_Compr_{unit}',
        f'Avg{label}_Compr_%ofTotal', 'Compr_Start_M/D', 'Compr_End_M/D',
        f'Min_{label}_{unit}', 'Min_Date_M/D', f'Min{label}_%ofTotal',
        f'Max_{label}_{unit}', 'Max_Date_M/D', f'Max{label}_%ofTotal'
    ]
    if habitat_mask is not None:
        columns.insert(2, f'Total_Habitat_{label}_{unit}')

    date_of_index = lambda x, idx: x.index[idx].strftime('%m/%d')

    # Create separate DataFrame for each scenario
    for scn,df in daily_data.items():
        table_data = []

        for region in df.columns:
            data = df[region]

            #find min/max indices and dates
            min_idx = np.argmin(data)
            max_idx = np.argmax(data)
            min_date = date_of_index(df, min_idx)
            max_date = date_of_index(df, max_idx)

            #calculate statistics
            min_vol = data.min()
            avg_vol = data.mean()
            max_vol = data.max()
            # Compute average compressed volume
            nonzero = data.loc[data > 0]
            if len(nonzero):
                avg_compr_vol = data.loc[nonzero.index[0]:nonzero.index[-1]].mean()
                compr_first_datestr = date_of_index(nonzero, 0)
                compr_last_datestr = date_of_index(nonzero, -1)
            else:
                avg_compr_vol = None
                compr_first_datestr = 'N/A'
                compr_last_datestr = 'N/A'

            #add total regional volume and calculate percentages
            total_region_vol = regional_total_volumes.get(region, None) if regional_total_volumes else None
            avg_vol_pct = (avg_vol / total_region_vol) * 100 if total_region_vol else None
            avg_compr_vol_pct = (avg_compr_vol / total_region_vol) * 100 if avg_compr_vol and total_region_vol else None
            min_vol_pct = (min_vol / total_region_vol) * 100 if total_region_vol else None
            max_vol_pct = (max_vol / total_region_vol) * 100 if total_region_vol else None

            # Row data: finish all avg, then all min, then all max
            row = [
                region,
                round(total_region_vol, 3) if total_region_vol else np.nan,
                round(avg_vol, 6),
                round(avg_vol_pct, 3) if avg_vol_pct else np.nan,
                round(avg_compr_vol, 6) if avg_compr_vol else np.nan,
                round(avg_compr_vol_pct, 3) if avg_vol_pct else np.nan,
                compr_first_datestr,
                compr_last_datestr,
                round(min_vol, 6),
                min_date,
                round(min_vol_pct, 3) if min_vol_pct else np.nan,
                round(max_vol, 6),
                max_date,
                round(max_vol_pct, 3) if max_vol_pct else np.nan
            ]
            if habitat_mask is not None:
                row.insert(2, round(regional_habitat_volumes.get(region), 3))
            table_data.append(row)

        df = pd.DataFrame(table_data, columns=columns)
        dataframes[scn] = df

    return dataframes
