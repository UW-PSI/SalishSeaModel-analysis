# Created by Ben Roberts for the Puget Sound Institute with funding from King County

import warnings
from dataclasses import dataclass

import numpy as np
import geopandas as gpd

@dataclass
class DOCompliance:
    """Class for computing dissolved oxygen non-compliance with various water quality standards

    Constructor parameters:
    - gdf: a GeoDataFrame giving the relevant physical and water quality properties of each cell
    - shape: the dimensions of model data that will be considered
    - Human Allowance.  Pre-industrial DO must be less than DO standard plus human allowance 
      to be considered for Part B of the Dept. of Ecology's non-compliance calculation
      This is unaffected by rounding.
    - Non-compliant Threshold: This was 0.2 mg/L during the 2019 work but because of rounding
      that's done, the 2021 and later Ecology reports use an equivalent of -0.25 mg/L
    - include_parta: Whether or not to consider only locations which fall below the Part A human
      use criteria. Defaults to it being used.
    """
    gdf: gpd.GeoDataFrame
    shape: tuple
    human_allowance: float = -0.2 # this should be -0.2 for proper function
    non_compliant_threshold: float = -0.25
    include_parta: bool = True

    def __post_init__(self):
        if len(self.shape) == 2:
            self._DO_std = np.tile(self.gdf.DO_std, (self.shape[0], 1))
            self._unmasked = np.tile(self.gdf.included_i, (self.shape[0], 1)).astype(bool)
        else:
            self._DO_std = np.tile(self.gdf.DO_std, (self.shape[0], self.shape[1], 1))
            self._unmasked = np.tile(self.gdf.included_i, (self.shape[0], self.shape[1], 1)).astype(bool)

    def find_noncompliant(self, run, reference, include_magnitudes=False):
        """Returns a boolean array of all locations which are noncompliant at all times.

        See Ahmed 2021 Appendix F. The operation here is intended to be mathematically
        equivalent.

        See also WAC 173-201A-210 1(d). https://app.leg.wa.gov/wac/default.aspx?cite=173-201A-210

        Returns an array of booleans flagging noncompliance. Dimensions match those
        of run and reference. If include_magnitudes is True, also return arrays of the
        magnitude of noncompliance for whichever Parts of the standard were evaluated.
        """
        if run.shape != self.shape:
            raise ValueError(f"Data does not match expected shape {self.shape}")
        if run.shape != reference.shape:
            raise ValueError("Shape of reference does not match run")

        # This is Step 2 from Appendix F: determine whether Part A or Part B test applies
        do_parta = (self._DO_std > 0) & (reference + self.human_allowance > self._DO_std)

        # Part B noncompliance check: is DO_diff less than the noncompliance threshold?
        # (-0.2 or -0.25 for "rounding method" as this is mathematically equivalent to
        # the later rounding Ecology has started doing)
        DO_part_b = reference + self.non_compliant_threshold
        noncompliant = ~do_parta & (run < DO_part_b) & self._unmasked
        if include_magnitudes:
            # Magnitude of noncompliance is a negative result related to the above
            # inequality. It's just a measurement of how much less run is than DO_part_b
            partb_magnitude = np.where(noncompliant, run - DO_part_b, 0)

        # Part A noncompliance check: is the minimum DO less than the standard?
        # Similarly to above, the later rounding that Ecology does makes this
        # equivalent to checking if the DOmin is less than DO standard minus 0.05
        if self.include_parta:
            # FIXME ability to not account for rounding
            parta_failed = self._unmasked & do_parta & (run < self._DO_std - 0.05)
            if include_magnitudes:
                # Same math applies here as for the Part B magnitude calculation
                parta_magnitude = np.where(parta_failed, run - self._DO_std + 0.05, 0)
            noncompliant |= parta_failed
        if not noncompliant.any():
            warnings.warn("No noncompliance found, that's really strange")

        if include_magnitudes:
            ret = [noncompliant]
            if self.include_parta:
                ret.append(parta_magnitude)
            ret.append(partb_magnitude)
            return ret
        else:
            return noncompliant
