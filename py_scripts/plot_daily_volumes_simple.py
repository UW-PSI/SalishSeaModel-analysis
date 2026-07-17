#!/usr/bin/env python3
# Created by Ben Roberts at the Puget Sound Institute with funding from King
# County.

import logging
import argparse
from pathlib import Path
from dataclasses import dataclass

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from cycler import cycler

from ssm_utils import read_case

@dataclass
class PlotDailies():
    case: str
    ssm_config: dict
    kind: str = 'volume'
    ymax_small: float = np.nan
    ymax_big: float = np.nan

    def __post_init__(self):
        logger = logging.getLogger('PlotDailies')
        shp = self.ssm_config['paths']['shapefile']
        self.gdf = gpd.read_file(shp).set_index('tce')
        if len(self.gdf) == 16013:
            logger.warning('Correcting shapefile length')
            self.gdf = self.gdf.iloc[:-1].copy()
        self.regions = self.gdf.groupby('region_inf').count().index.to_list()
        self.regions.remove('Other') # These will be removed in future iterations
        self.regions.insert(0, 'All_regions')

    def _sheet_name(self, run_tag: str):
        if self.kind == 'volume':
            return f'Daily_Volumes_{run_tag}'
        else:
            return f'Daily_Areas_{run_tag}'

    def _get_region_totals(self, file_path, run_tag):
        summary = pd.read_excel(file_path, sheet_name=f'{self.kind.title()}_{run_tag}', index_col=0)
        hab_col = f'Total_Habitat_{self._kind_abbr.title()}_{self._kind_unit}'
        norm_col = f'Total_{self._kind_abbr.title()}_{self._kind_unit}'
        is_habitat = hab_col in summary.columns
        regionals = summary[hab_col if is_habitat else norm_col]
        return regionals, is_habitat

    @property
    def _kind_unit(self):
        return 'km³' if self.kind == 'volume' else 'km²'

    @property
    def _kind_abbr(self):
        return 'vol' if self.kind == 'volume' else self.kind

    def run(self, file_path: Path, run_tag: str=None, reference: bool=True):
        """
        Create clean time series plots showing all scenarios for all specified regions

        Parameters:
        file_path: path or file handle to the spreadsheet containing daily volume data
        run_tag: optional, if included only plots a single run
        reference: optional, defaults to on. Show a reference run even when plotting a single run with run_tag

        FIXME
        regions_to_plot: list of regions to include
        """

        logger = logging.getLogger('PlotDailies')

        labels = self.ssm_config['run_information']['run_tag'][self.case]
        if run_tag is not None:
            assert run_tag in labels, f'{run_tag} not found in this case'
            newlbl = { run_tag: labels[run_tag] }
            ref_tag = self.ssm_config['run_information']['reference']
            if reference and ref_tag in labels:
                newlbl[ref_tag] = labels[ref_tag]
            labels = newlbl

        regionals, is_habitat = self._get_region_totals(file_path, next(iter(labels)))

        readme = pd.read_excel(file_path, sheet_name='README', index_col=0)
        threshold_key = readme.loc['Threshold value:'].item()
        unit = readme.loc['Threshold unit:'].item()
        threshold_var = readme.loc['Variable examined:'].item()
        if pd.isna(unit) and threshold_var.startswith('MI'):
            unit = 'Metabolic Index'

        fig, axes = plt.subplots(len(self.regions), 1, figsize=(12, 2.5*len(self.regions)))  

        all_regions_max = 0.04  #maximum volume for All_regions across scenarios
        hood_max = 0.04  #maximum volume for Hood across scenarios
        other_max = 0.04  #maximum volume for other regions across scenarios

        daily_results = {}
        for run_tag,label in labels.items():
            daily_results[run_tag] = pd.read_excel(file_path, sheet_name=self._sheet_name(run_tag), index_col=0)
            for region in self.regions + ['All_regions']:
                if region == 'All_regions':
                    all_regions_max = max(all_regions_max, daily_results[run_tag][region].max())
                elif region == 'Hood':
                    hood_max = max(hood_max, daily_results[run_tag][region].max())
                else:
                    other_max = max(other_max, daily_results[run_tag][region].max())

        large_scale_ylim = max(all_regions_max, hood_max) * 1.1  #All_regions and Hood scale
        if self.ymax_big is not None:
            if large_scale_ylim > self.ymax_big:
                logger.warning(f'Forced to rescale large_scale_ylim to {large_scale_ylim}')
            else:
                large_scale_ylim = self.ymax_big
        other_scale_ylim = other_max * 1.1  #other regions scale
        if self.ymax_small is not None:
            if other_scale_ylim > self.ymax_small:
                logger.warning(f'Forced to rescale other_scale_ylim to {other_scale_ylim}')
            else:
                other_scale_ylim = self.ymax_small

        for region,ax in zip(self.regions,axes):
            if len(labels) == 2:
                ax.set_prop_cycle(cycler(color=['black','gray']))

            for scenario,label in labels.items():
                #get daily volume data for this region/scenario combination
                dailies = daily_results[scenario][region]

                #plot clean time series - no grid, no markers, no annotations
                ax.plot(dailies.index, dailies,
                       linewidth=1, label=label)

            #format axis - clean and simple
            ax.set_ylabel(f'{region}\n{self.kind.title()} ({self._kind_unit})', fontsize=11)

            ax.set_ylim(0, large_scale_ylim if region in ('All_regions','Hood') else other_scale_ylim)  #All_regions and Hood share large scale

            # Format x-axis as days in 2014
            ax.set_xlim(dailies.index[0], dailies.index[-1])
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))  #every 2 months
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))    #month abbreviations

            #add total regional volume text to top left corner with padding from top
            total = regionals.loc[region].item()
            ax.text(0.02, 0.93,
                    f'Total {"habitat " if is_habitat else ""}{self.kind} of {region}: {total:.0f} {self._kind_unit}',
                    transform=ax.transAxes, fontsize=9, verticalalignment='top',
                    horizontalalignment='left')  #no background box, padded down from top
        #add legend for first subplot only
        axes[0].legend(loc='upper right', fontsize=10)

        #format x-axis for bottom subplot only
        axes[-1].set_xlabel(f'Days in {dailies.index.year[0]}', fontsize=12)

        #add overall title with padding from top of plot box
        fig.suptitle(f'{threshold_var} Daily {self.kind.title()} Below {threshold_key} {unit}',
                    fontsize=13, y=0.995)  #moved down from 0.98 to 0.995 for padding from plot box

        fig.tight_layout()
        return fig, threshold_var, threshold_key

def main():
    parser = argparse.ArgumentParser(description='Create clean time series plots showing daily volumes for all scenarios/regions')
    parser.add_argument('case', help='Case name or file')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Quiet mode; suppress most output')
    parser.add_argument('-a', '--area', action='store_true',
                        help='Plot daily areas rather than volumes')
    parser.add_argument('-y', '--ymax', type=float,
                        help='Override ymax for small regions')
    parser.add_argument('-b', '--ymax-big', type=float,
                        help='Override ymax for big regions')
    parser.add_argument('threshold_sheet_path', nargs='+', type=argparse.FileType(), help='Path to a DO threshold spreadsheet from calc_below_threshold.py')
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING if args.quiet else logging.INFO)
    logger = logging.getLogger(__name__)

    ssm_config, case = read_case(args.case)

    plotter = PlotDailies(case=case, ssm_config=ssm_config,
                          kind='area' if args.area else 'volume',
                          ymax_small=args.ymax, ymax_big=args.ymax_big)

    for f in args.threshold_sheet_path:
        file_path = f.name
        f.close()
        logger.info(f'Working on {file_path}')

        labels = ssm_config['run_information']['run_tag'][case]
        for tag in labels.keys():
            if tag == ssm_config['run_information']['reference']:
                continue
            fig, var, thresh = plotter.run(file_path, run_tag=tag)

            ### save figure to PNG file #########################################
            stem = Path(file_path).stem
            filename = f'{stem}_daily_{plotter.kind}.png'
            output_path = Path(ssm_config['paths']['graphics']) / 'SSM_plot_timeseries'
            output_path.mkdir(parents=True, exist_ok=True)
            fig.savefig(output_path / filename, dpi=300, bbox_inches='tight')  #save as high-resolution PNG with tight bounding box
            logger.info(f"Saved plot to: {output_path / filename}")  #show save location
            plt.close(fig)

if __name__=='__main__': main()
