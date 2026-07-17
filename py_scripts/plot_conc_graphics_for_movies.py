#!/usr/bin/env python3
# Created by Rachael D. Mueller at the Puget Sound Institute with funding from King County
import os
import sys
import argparse
from pathlib import Path
import time
import logging
import subprocess
from datetime import date

import xarray as xr
import contextily as cx 
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib as mpl
import cmocean.cm as cm

sys.path.append(str(Path(__file__).parent.parent))
from apis import API_KEYS
from ssm_utils import read_case, DepthReducer, FileFinder
from ssm_utils.depth import SCOPES

def plot_conc_graphics(case, ssm, stat_type, vtype, depth, run_type, region=None,
                       mitype=None, mispecies=None, toner=False, delta_ref=False):
    """
    case [string]: "SOG_NB" or "whidbey"
    model_var [string]: "DOXG", "NO3", "salinity"
    stat_type[string]: "mean","min","max"
    loc[string]: "surface" or "bottom"
    """

    logger = logging.getLogger(f'plot_conc_graphics_{run_type + ("-ref" if delta_ref else "")}_{vtype}')

    plt.rc('font', family='sans-serif', weight='normal', style='normal', size=10)
    plt.rc('legend', fontsize=10, title_fontsize=12)
    plt.rc('axes', titlesize=14, labelsize=12)
    plt.rc('figure', titlesize=14)

    # Define dimension sizes and load shapefile
    shp = ssm['paths']['shapefile']
    gdf = gpd.read_file(shp).set_index('tce')
    if len(gdf) == 16013:
            logger.warning('Correcting shapefile length')
            gdf = gdf.iloc[:-1].copy()
    gdf = gdf.rename(columns={'region_inf':'Regions'}).to_crs('EPSG:4326')
    # Filter the GeoDataFrame to include only rows where 'included_i' == 1 (exclude shallow/outside areas)
    gdf = gdf.loc[gdf['included_i'] == 1].copy()

    ff = FileFinder(case=case, ssm_config=ssm, vtype=vtype,
                    mitype=mitype, mispecies=mispecies, run_type=run_type)
    dr = DepthReducer(ssm_config=ssm, gdf=gdf)

    run_file = ff.get_file(ff.run_types[0], stat_type)
    with xr.open_dataset(run_file) as ds:
        param=ds[ff.get_var_name(run_file)]
        param = dr.select_depth(param, depth)
        if ds.attrs.get('version', 1) >= 2:
            time_coords = param.coords['day']
            long_name = param.attrs['long_name']
            units = param.attrs['units']
        else:
            # TODO assign reasonable defaults
            pass
    if delta_ref:
        ref_file = ff.get_file(ssm['run_information']['reference'], stat_type)
        logger.info(f'Subtracting reference condition from {ref_file}')
        with xr.open_dataset(ref_file) as ds:
            param -= dr.select_depth(ds[ff.get_var_name(ref_file)], depth)

    graphics_output_dir = Path(ssm['paths']['movies']) / ff.output_var_base
    frame = 'FullDomain' if region is None else region
    output_directory = graphics_output_dir / frame / depth / (
            run_type + ('-ref' if delta_ref else ''))
    logger.info(f'Writing graphics to {output_directory}')
    # create output directory, if it doesn't already exist 
    if not output_directory.is_dir():
        logger.info(f'creating: {output_directory}.  Assumed that {graphics_output_dir} exists.')
        output_directory.mkdir(mode=0o777, parents=True, exist_ok=True)

    # NOTE: Labels are hard-coded (not ideal) and need to match colormap list
    if not delta_ref:
        upper_bounds={
            'DOXG': [2, 3, 4, 5, 6, 7],
            'salinity': [5, 10, 15, 20, 25, 30],
            'NO3': [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6],
            'mi': [1, 2]
        }
        color_list = {
            'DOXG': ['red','orange','navajowhite','beige','skyblue','royalblue','midnightblue'],
            'salinity': ['navy','mediumblue','cadetblue','seagreen','lightseagreen','khaki','lemonchiffon'],
            'SST': ['midnightblue','darkslateblue','darkmagenta','darkorchid',
                    'palevioletred','thistle','palegoldenrod','khaki','gold','goldenrod'],
            'NO3': ['darkgoldenrod','goldenrod','darkkhaki','khaki','thistle','palevioletred','darkorchid',
                    'darkmagenta','darkslateblue','midnightblue'],
            'mi': ['red', 'orange', 'skyblue']
        }
    else:
        upper_bounds = {
            'DOXG': [-1,-.9,-.8,-.7,-.6,-.5,-.4,-.3],
            'mi': [-1,-.9,-.8,-.7,-.6,-.5,-.4,-.3,-.2,-.1]
        }
        color_list = {
            'DOXG': ['#010101','#4d8684','#fcfc00','#f3be00','#e4760d',
                     '#8b0000','#ae0100','#ff6347','#ef797b'],
            'mi': ['#010101','#4d8684','#fcfc00','#f3be00','#e4760d','#8b0000',
                   '#ae0100','#ff6347','#ef797b','#f1cece','#fce4ec']
        }

    # create legend labels
    bounds = []
    max_val = np.ceil(param.max().item())
    for index, upper_bound in enumerate(upper_bounds[vtype] + [max_val]):

        if index == 0:
            if upper_bound < 0:
                bound = f'< {upper_bound}'
                bounds.append(bound)
                continue
            else:
                lower_bound = 0
        else:
            lower_bound = upper_bounds[vtype][index-1]
        # Prevent inconsistent legend labels between ints and floats
        if type(lower_bound) == int and upper_bound == np.round(upper_bound):
            upper_bound = int(upper_bound)

        # format the numerical legend here
        bound = f'{lower_bound} - {upper_bound}'
        bounds.append(bound)

    title = f"{ssm['run_information']['run_description_short'][case][run_type]}"
    if delta_ref:
        title += " Minus Reference"
    title += f"\n{SCOPES[depth]}, {stat_type.capitalize()} Daily {long_name}"
    area = gdf if region is None else gdf.loc[gdf['Regions'] == region]
    hatch_gdf = []
    if mispecies is not None and depth == 'bt':
        depth_threshold = ssm['mi']['species'][mispecies].get('habitat_max_depth')
        if depth_threshold is not None:
            logger.info(f'Applying max depth {depth_threshold} for species {mispecies}')
            depth_mask_hatch = area['depth'] * 1000 > depth_threshold
            hatch_gdf = area.loc[depth_mask_hatch]
            area = area.loc[~depth_mask_hatch]

    # Define background tileset
    if toner or ('stadia' not in API_KEYS):
        tileset = cx.providers.CartoDB.PositronNoLabels
        #if toner:
        #    tileset = cx.providers.Stadia.StamenTonerLite
        #    tileset['url'] = 'https://tiles.stadiamaps.com/tiles/stamen_toner_background/{z}/{x}/{y}{r}.png?api_key=' + API_KEYS['stadia']
    else:
        tileset = cx.providers.Stadia.StamenTerrainBackground
        tileset['url'] = 'https://tiles.stadiamaps.com/tiles/stamen_terrain_background/{z}/{x}/{y}{r}.png?api_key=' + API_KEYS['stadia']

    output_file_base = f'{case}_{run_type + ("-ref" if delta_ref else "")}_{ff.output_var_base}_{stat_type}_{depth}'

    # Plot for each day
    def plot_day(i,model_dt):
        # define output file name with model day-of-year
        output_file = output_directory / f'{output_file_base}_{i+1:03d}.png'
        model_date = model_dt.data

        if i % 10 == 0:
            logger.info(f'Date {model_date}')
        data = param.sel(day=model_date, node=area.index).to_numpy()

        fig, ax = plt.subplots(1, figsize = (8,9))
        area.plot(data, ax=ax,
               scheme="User_Defined",
               classification_kwds=dict(bins=upper_bounds[vtype] + [max_val]),
               cmap=mpl.colors.ListedColormap(color_list[vtype])
        )
        handles = [mpl.patches.Patch(color=color_list[vtype][j], label=bounds[j]) for j in range(len(color_list[vtype]))]
        if len(hatch_gdf) > 0:
            hatch_gdf.plot(ax=ax, color='lightgrey', edgecolor='#9A9A9A', linewidth=0.4, hatch='///', alpha=1)
            handles.append(mpl.patches.Patch(facecolor='lightgrey', edgecolor='black', hatch='///', label=f'>{depth_threshold}m'))
        if region is None:
            ax.set_xlim(-123.3, -122.18)  # Limiting longitude for PSound
            ax.set_ylim(47, 48.77)        # Limiting latitude for PSound
        # set legend to lower left corner 
        # (instead of default upper-right, which overlaps SOGNB)
        # the legend for salinity and nitrogen doesn't have the 
        # same attributes
        ax.legend(handles=handles, loc='lower left', title=f'{vtype}{" [" + units + "]" if units is not None and units != "none" else ""}')
        ax.set(xlabel='Latitude',ylabel='Longitude')
        # add background landscape
        cx.add_basemap(ax, crs=gdf.crs, source=tileset, alpha=1)
        ax.set_title(f"{title}\n{mispecies.title() + ' ' + mitype.title() + '; ' if mispecies is not None else ''}{model_dt.dt.strftime('%B %d, %Y').item()}")
        fig.savefig(output_file, bbox_inches='tight')
        plt.close(fig) #clear figure and memory
        return output_file

    # Pretty sure this can't be parallelized because GeoDataFrames aren't pickleable.
    outputs = [plot_day(i, dt) for i, dt in enumerate(time_coords)]

    return outputs

def main():
    parser = argparse.ArgumentParser(description="Plot concentration animation frames")
    parser.add_argument('case', help='Case name (SOG_NB, whidbey, ...) or file')
    parser.add_argument('stat_type', choices=('min','mean','max'), help='Daily aggregation')
    parser.add_argument('depth', choices=SCOPES.keys(), help='Depth reduction')
    parser.add_argument('run_type', help='Run tag for scenario to plot')
    parser.add_argument('-d', '--delta-ref', action='store_true',
                        help='Make a delta plot against reference condition')
    parser.add_argument('-r', '--region', help='More restrictive regional scope')
    parser.add_argument('-t', '--toner', action='store_true',
                        help='Use Stamen Toner background instead of terrain')
    parser.add_argument('-m', '--ffmpeg', action='store_true', help='Produce movie at end')
    subparsers = parser.add_subparsers(title='Data type selection')
    parser_var = subparsers.add_parser('var', help='Work with a model output variable')
    parser_var.add_argument('variable', help='Output variable, like DOXG')
    parser_var.set_defaults(mode='var')

    parser_mi = subparsers.add_parser('mi', help='Work with metabolic index data')
    parser_mi.add_argument('species', help='Species tag')
    parser_mi.add_argument('type', choices=('routine','smr'), help='routine or smr')
    parser_mi.set_defaults(mode='mi')
    args = parser.parse_args()

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

    # Start time counter
    start = time.perf_counter()

    # Load yaml file containing path definitions
    ssm, case = read_case(args.case)

    if args.mode == 'mi':
        outputs = plot_conc_graphics(case, ssm, args.stat_type, 'mi',
                                 args.depth, args.run_type, region=args.region,
                                 mitype=args.type, mispecies=args.species,
                                 toner=args.toner, delta_ref=args.delta_ref)
    else:
        outputs = plot_conc_graphics(case, ssm, args.stat_type, args.variable,
                                     args.depth, args.run_type, region=args.region,
                                     toner=args.toner, delta_ref=args.delta_ref)

    if args.ffmpeg:
        video_output = str(outputs[0].parent / '_'.join(outputs[0].stem.split('_')[:-1])) + '_video.mp4'
        logger.info(f'Creating video file {video_output}')
        ffmpeg_command = ["ffmpeg","-y","-framerate",'6']
        ffmpeg_command += ['-i',str(outputs[0].parent / outputs[0].stem[:-3]) + '%03d' + outputs[0].suffix]
        ffmpeg_command += ["-vf","scale=trunc(iw/2)*2:trunc(ih/2)*2","-c:v","libx264","-r",'30',"-pix_fmt","yuv420p"]
        ffmpeg_command.append(video_output)
        subprocess.check_output(ffmpeg_command)

    # End time counter
    end = time.perf_counter()
    logger.info(f'Execution time: {(end - start)/60:.3f} minutes')

if __name__=='__main__': main()
