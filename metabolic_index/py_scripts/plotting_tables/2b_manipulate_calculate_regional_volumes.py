#!/usr/bin/env python
"""
Calculate Total Habitat Volumes by Region
Cells 15-16 from original notebook
"""


# ============================================================================
# ## CALCULATE TOTAL HABITAT VOLUMES BY REGION -considering all non masked area for total vol/%vol calcs following
# ============================================================================

# ==============================================================================
# CALCULATE TOTAL HABITAT VOLUMES BY REGION
# ==============================================================================
# PURPOSE: Calculate effective regional volumes based on habitat_depth_mask applied in prior cell
# LOGIC: habitat_depth_mask defines valid habitat (NaN=excluded, 1=valid) → calculate volume2D from shapefile → apply mask → sum by region → store in regional_volumes
# RESULT: regional_volumes represents ACTUAL AVAILABLE HABITAT (not full WC) → statistics percentages correct → plot annotations correct

# ==============================================================================
# Section 1: Load Shapefile and Calculate volume2D (Full Water Column)
#Note executed earlier before habitat mask creation 

# ==============================================================================
# Section 2: Calculate WC Regional Volumes (for QA comparison)
# ==============================================================================

regional_volumes_WC = {}  #initialize dictionary to store full water column volumes by region for comparison with habitat volumes

for region in regions:  #iterate through all regions including virtual All_regions
    if region == 'All_regions':  #All_regions is not in shapefile, calculated as union of all included nodes
        idx = (gdf['included_i'] == 1)  #boolean mask selecting all nodes with included_i=1 (excludes boundary/land nodes)
    else:  #individual named regions from shapefile (Hood, Main, etc.)
        idx = ((gdf['Regions'] == region) & (gdf['included_i'] == 1))  #boolean mask filtering nodes by region name AND included status
    
    regional_volumes_WC[region] = volume[idx].sum()  #sum base node volumes (km³) for all nodes in region to get total WC volume

# ==============================================================================
# Section 3: Apply Habitat Mask and Calculate Effective Regional Volumes
# ==============================================================================

volume2D_masked = volume2D * habitat_depth_mask[0, :, :].T  #element-wise multiply (16012×10) volume by transposed (10×16012) mask → NaN habitat becomes NaN volume, valid habitat keeps volume value

effective_regional_volumes = {}  #initialize dictionary to store habitat-based volumes by region

for region in regions:  #iterate through all regions to calculate habitat volumes
    if region == 'All_regions':  #virtual region uses all included nodes
        idx = (gdf['included_i'] == 1)  #boolean mask for included nodes across entire domain
    else:  #individual named regions
        idx = ((gdf['Regions'] == region) & (gdf['included_i'] == 1))  #boolean mask for region nodes that are included
    
    region_masked_volumes = volume2D_masked[idx, :]  #extract (N_region_nodes×10) subset of masked volumes for this region
    total_effective_volume = np.nansum(region_masked_volumes)  #sum all non-NaN values (NaN from mask excluded) to get total valid habitat volume in km³
    
    effective_regional_volumes[region] = total_effective_volume  #store calculated habitat volume for this region

#APPROACH NOT USED regional_volumes = effective_regional_volumes  #assign habitat volumes to regional_volumes variable used throughout downstream code (statistics, plots, Excel)
    regional_volumes = regional_volumes_WC

# QA verification moved to 6b_qa_verification_regional_volumes.py for cleaner code organization
print(f"Regional volumes calculated. Run QA module (6b) for verification details.")
