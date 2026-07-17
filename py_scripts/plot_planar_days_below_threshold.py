#!/usr/bin/env python3

# Created by Ben Roberts at the Puget Sound Institute with funding from King County
#

import sys
import os
import argparse
from pathlib import Path

import numpy as np
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import contextily as cx

sys.path.append(str(Path(__file__).parent.parent))
from apis import API_KEYS
from ssm_utils import read_case

def plot_threshold(ssm_config, gdf_plot, col_name, depth_threshold=None, delta=None, toner=False):
    """Threshold plotting with optional depth hatching"""

    plt.rc('font', family='sans-serif', weight='normal', style='normal', size=10)
    plt.rc('legend', fontsize=10, title_fontsize=12)
    plt.rc('axes', labelsize=12, titlesize=14)
    plt.rc('figure', titlesize=14)

    gdf = gpd.read_file(ssm_config['paths']['shapefile']).set_index('tce')

    # TODO we might want to specify a different color scheme for delta plots
    #boundaries = [0, 1, 8, 31, 91, 121, 181, 366]  # BoundaryNorm uses [left, right) bins - left included, right excluded
    #legend_labels = ['0 days', '1-7 days', '8-30 days', '31-90 days', '91-120 days', '121-180 days', '181+ days']
    boundaries = [0, 1, 2, 3, 4, 5, 6, 7, 14, 30, 366]
    legend_labels = ['0 days', '1 day', '2 days', '3 days', '4 days', '5 days', '6 days', '7 days', '8-14 days', '15-30 days', '31+ days']
    #colors = ['#E8E8E8', 'deepskyblue', 'blue', '#1E3A8A', 'plum', 'blueviolet', '#8B3535']  # 0d: lt gray | 1-7d: lt blue | 8-30d: med blue | 31-90d: dk navy | 91-120d: lt plum | 121-180d: dk violet | 181+d: dk maroon
    #colors = ['#FAFAFA', 'lightblue', 'deepskyblue', 'blue', 'plum', 'blueviolet', '#2d1b2e']  # 0d: ultra lt gray | 1-7d: lt blue | 8-30d: sky blue | 31-90d: med blue | 91-120d: lt plum | 121-180d: dk violet | 181+d: dk purple
    #colors = ['#FAFAFA', '#B3D9FF', '#6BB6FF', '#2E86C1', '#D4B5D4', '#9370DB', '#4B0082']  # 0d: ultra lt gray | 1-7d: lt sky blue | 8-30d: med sky blue | 31-90d: dk steel blue | 91-120d: lt lavender | 121-180d: med purple | 181+d: dk indigo
    colors = ['#fafafa', '#fee8c8', '#fdd49e', '#fdbb84', '#fc8d59', '#e34a33',
              '#b30000', '#7f0000', '#542788', '#2d004b', '#111111']

    cmap = mpl.colors.ListedColormap(colors)
    norm = mpl.colors.BoundaryNorm(boundaries, len(colors), clip=True)

    gdf_plot = gdf_plot.to_crs('EPSG:4326')
    gdf_data = gpd.GeoDataFrame({'data': gdf_plot[col_name] if delta is None else gdf_plot[col_name] - gdf_plot[delta]}, geometry=gdf_plot['geometry'], crs=gdf_plot.crs, index=gdf_plot.index)
    # There's no guarantee the shapefile we're reading contains all the TCEs
    # of the master, so we need to use this slow method of matching TCEs by
    # index
    gdf_data = gdf_data.join(gdf['included_i'], how='left')
    gdf_data = gdf_data.loc[gdf_data['included_i'] == 1].fillna(0)
    #gdf_data = gdf_data.fillna(0).loc[np.isin(gdf_data, (gdf['included_i'] == 1).index.to_numpy().nonzero()[0])]
    if depth_threshold is not None:
        depth_mask_hatch = gdf_plot['depth'] * 1000 > depth_threshold
        gdf_data = gdf_data[~depth_mask_hatch]
        gdf_hatch = gdf_plot[depth_mask_hatch]
    else:
        gdf_hatch = []

    fig, ax = plt.subplots(1, 1, figsize=(19.2, 10.8), constrained_layout=True)

    if len(gdf_data) > 0:
        gdf_data.plot('data', ax=ax, cmap=cmap, norm=norm, edgecolor='#9A9A9A', linewidth=0.4, legend=False) #or lightgrey is lighter
    handles = [mpl.patches.Patch(color=colors[i], label=legend_labels[i]) for i in range(len(colors))]
    if len(gdf_hatch) > 0:
        gdf_hatch.plot(ax=ax, color='lightgrey', edgecolor='#9A9A9A', linewidth=0.4, hatch='///', alpha=0.7, legend=False)
        handles.append(mpl.patches.Patch(facecolor='lightgrey', edgecolor='black', hatch='///', label=f'>{depth_threshold}m'))
    ax.set_title(col_name, ha='center')
    ax.set(xlabel='Longitude', ylabel='Latitude')
    ax.set_xlim(-123.3, -122.18)  # Limiting longitude for PSound
    ax.set_ylim(47, 48.77)        # Limiting latitude for PSound
    if toner or ('stadia' not in API_KEYS):
        tileset = cx.providers.CartoDB.PositronNoLabels
    else:
        tileset = cx.providers.Stadia.StamenTerrainBackground
        tileset['url'] = 'https://tiles.stadiamaps.com/tiles/stamen_terrain_background/{z}/{x}/{y}{r}.png?api_key=' + API_KEYS['stadia']
    # add background landscape
    cx.add_basemap(ax, crs=gdf_plot.crs, source=tileset, alpha=1)

    ax.legend(handles=handles, title="Days Below Threshold", loc='center left',
              bbox_to_anchor=(1.02, 0.5), bbox_transform=ax.transAxes)

    return fig, ax

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('case', help='Case name or file')
    parser.add_argument('shapefile', type=argparse.FileType('rb'),
                        help='Path to shapefile containing data to plot')
    parser.add_argument('-c', '--column', help='Specify one column of data to plot')
    parser.add_argument('-T', '--title', help='Specify a plot title')
    parser.add_argument('-t', '--toner', action='store_true',
                        help='Use Stamen Toner background instead of terrain')
    parser.add_argument('-H', '--hatch-below', type=float, help='Hatch cells below given depth')
    parser.add_argument('-d', '--delta-ref', action='store_true', help='Subtract reference condition')

    args = parser.parse_args()

    # load yaml file containing path definitions
    ssm, case = read_case(args.case)

    shapefile_path = Path(args.shapefile.name)
    shapefile_base = shapefile_path.stem
    args.shapefile.close()
    DBTG = gpd.read_file(shapefile_path).set_index('tce')

    graphics_output_path = Path(ssm['paths']['graphics'])
    if not graphics_output_path.is_dir():
        print(f'creating: {graphics_output_path}')
        os.umask(0) #clears permissions
        graphics_output_path.mkdir(parents=True, exist_ok=True) # Race conditions are possible when running in parallel
    print('*************************************************************')
    print('Writing plots to:', graphics_output_path)
    print('*************************************************************')

    columns = DBTG.columns if args.column is None else [args.column]
    ref_tag = ssm['run_information']['reference']
    for col_name in columns:
        if col_name in ('tce','depth','geometry'):
            continue
        if args.delta_ref and col_name == ref_tag:
            continue
        fig, ax = plot_threshold(ssm, DBTG, col_name,
                                 depth_threshold=args.hatch_below,
                                 delta=ref_tag if args.delta_ref else None,
                                 toner=args.toner)
        if args.title is not None:
            ax.set_title(args.title)
        else:
            ax.set_title('Days Below Threshold - ' + ssm['run_information']['run_description_short'][case][col_name] + (' Minus Reference' if args.delta_ref else ''))
        name = f'{shapefile_base}_{col_name}' + ('_minus_ref' if args.delta_ref else '')
        if args.hatch_below is not None:
            name += f'_hatched_{args.hatch_below}'
        fig.savefig(graphics_output_path / f'{name}.png', bbox_inches='tight', dpi=200)
        plt.close(fig)

if __name__ == '__main__': main()
