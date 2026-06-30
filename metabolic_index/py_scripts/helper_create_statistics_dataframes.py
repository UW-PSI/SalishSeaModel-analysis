# Created by Ben Roberts with funding from King County

# Original version of this function is in the new calc_DO_below_threshold.py
# on the private repo. Eventually this will all be merged together and
# this file should then be deleted.

import geopandas as gpd
import pandas as pd
import numpy as np

def create_statistics_dataframes(case: str, ssm_config: dict, dtype: str, daily_data: dict, regions_to_plot, time_coords, habitat_sizes=None):
    """Create DataFrames for daily volume statistics - ready for Excel export

    Parameters:
    case: case name
    ssm_config: dict of case configuration
    dtype: str either 'node', 'area' or 'volume', basically only affects row headers and
        percentage calculations
    daily_data: dict of scenarios, each containing a dict of regions,
        mapping to dataframes containing per-region daily volumes/areas/nodes

    Returns:
    dict of DataFrames keyed by run scenario containing the formatted table
    """
    # Get regional "volume" totals
    # Note that this function may be working with either node count, area or volume, but
    # the process is essentially the same. Don't take the variable names too
    # literally!
    shp = ssm_config['paths']['shapefile']
    gdf = gpd.read_file(shp)
    if dtype == 'volume':
        regional_total_volumes = gdf.loc[gdf['included_i'] == 1].groupby('region_inf')['volume'].sum().to_dict()
    elif dtype == 'area':
        regional_total_volumes = (gdf.loc[gdf['included_i'] == 1].groupby('region_inf')['Area_m2'].sum() * 1e-6).to_dict()
    else: # Node count
        regional_total_volumes = gdf.loc[gdf['included_i'] == 1].groupby('region_inf')['volume'].count().to_dict()

    dataframes = {}

    # Create DataFrame with correct column order
    if dtype == 'volume':
        label = 'Vol'
        unit = 'km3'
    elif dtype == 'area':
        label = 'Area'
        unit = 'km2'
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
    if habitat_sizes is not None:
        columns.insert(2, f'Total_Habitat_{label}_{unit}')

    date_of_index = lambda idx: time_coords[idx].strftime('%m/%d')

    # Create separate DataFrame for each scenario
    for scn,d in daily_data.items():
        table_data = []

        # This part differs a bit from the upstream version because it assumes
        # there's a DataFrame here, when in this code it's actually a dict
        for region in regions_to_plot:
            data = d[region]

            #find min/max indices and dates
            min_idx = np.argmin(data)
            max_idx = np.argmax(data)
            min_date = date_of_index(min_idx)
            max_date = date_of_index(max_idx)

            #calculate statistics
            min_vol = data.min()
            avg_vol = data.mean()
            max_vol = data.max()
            # Compute average compressed volume
            nonzero = data.nonzero()[0]
            if len(nonzero):
                avg_compr_vol = data[nonzero[0]:nonzero[-1]].mean()
                compr_first_datestr = date_of_index(nonzero[0])
                compr_last_datestr = date_of_index(nonzero[-1])
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
            if habitat_sizes is not None:
                row.insert(2, habitat_sizes[region])
            table_data.append(row)

        df = pd.DataFrame(table_data, columns=columns)
        dataframes[scn] = df

    return dataframes
