#!/usr/bin/env python
"""
QA Verification for Regional Volume Calculations
================================================
Created: 2026-02-12
Purpose: Quality assurance checks for regional volume masking and calculations

This module was extracted from 2b_manipulate_calculate_regional_volumes.py
to separate QA/debug functionality from core calculations.

Dependencies (from earlier modules):
- volume2D: Original volume array from initialization
- volume2D_masked: Masked volume array from 2a_manipulate_habitat_depth_masks.py
- regional_volumes_WC: Water column volumes from 2b_manipulate_calculate_regional_volumes.py
- regional_volumes: Habitat volumes from 2b_manipulate_calculate_regional_volumes.py
- regions: List of regions from initialization
- habitat_depth_mask: The mask applied from 2a_manipulate_habitat_depth_masks.py
"""

import numpy as np

# ==============================================================================
# QA VERIFICATION FOR REGIONAL VOLUME MASKING
# ==============================================================================

# ------------------------------------------------------------------------------
# QA SECTION A: GENERIC MASKING VERIFICATION (applies to ANY habitat mask)
# ------------------------------------------------------------------------------

total_volume_before = np.sum(volume2D)  #sum all cells in full water column volume2D (includes all layers, all nodes)
total_volume_after = np.nansum(volume2D_masked)  #sum only non-NaN cells in masked volume2D (excludes habitat mask NaN cells)
pct_retained = (total_volume_after / total_volume_before * 100) if total_volume_before > 0 else 0  #calculate percentage of volume retained after masking

print(f"\n{'='*80}")
print(f"QA SECTION A: GENERIC MASKING VERIFICATION (any mask applied)")
print(f"{'='*80}")

print(f"\n[QA A.1] Total Volume Comparison (domain-wide before vs after masking):")
print(f"  Full WC volume2D total:    {total_volume_before:8.3f} km³ (sum of all nodes×layers before masking)")
print(f"  Masked volume2D total:     {total_volume_after:8.3f} km³ (sum of non-NaN nodes×layers after masking)")
print(f"  Retained:                  {pct_retained:6.2f}% of original WC volume")

print(f"\n[QA A.2] Regional Volumes - WC vs Habitat (all regions):")
print(f"  {'Region':<15} {'WC (km³)':>10} {'Habitat (km³)':>14} {'% of WC':>10}")  #table header
print(f"  {'-'*15} {'-'*10} {'-'*14} {'-'*10}")  #separator line

total_wc_sum = 0  #accumulator for total WC volume across all regions
total_habitat_sum = 0  #accumulator for total habitat volume across all regions

for region in regions:  #iterate through regions to display comparison
    wc_vol = regional_volumes_WC[region]  #full water column volume for this region
    habitat_vol = regional_volumes[region]  #habitat-masked volume for this region
    pct_of_wc = (habitat_vol / wc_vol * 100) if wc_vol > 0 else 0  #calculate habitat as percentage of WC

    total_wc_sum += wc_vol  #add to running WC total
    total_habitat_sum += habitat_vol  #add to running habitat total

    print(f"  {region:<15} {wc_vol:10.3f} {habitat_vol:14.3f} {pct_of_wc:9.1f}%")  #region row

print(f"  {'-'*15} {'-'*10} {'-'*14} {'-'*10}")  #separator before total
print(f"  {'TOTAL':<15} {total_wc_sum:10.3f} {total_habitat_sum:14.3f} {(total_habitat_sum/total_wc_sum*100):9.1f}%")  #totals row

kept_layers = [i for i in range(10) if not np.isnan(habitat_depth_mask[0, i, 0])]  #identify which depth layers were kept (non-NaN) in mask
print(f"\n[QA A.3] Habitat mask summary:")
print(f"  Depth layers: {kept_layers} (these layers are shown to have non-NaN values in mask)")
print(f"  Nodes/Cells: {np.sum(np.any(~np.isnan(habitat_depth_mask[0, :, :]), axis=0))} (raw mask before volume calc - see QA A.2 for actual habitat)")

# ------------------------------------------------------------------------------
# QA SECTION B: BOTTOM-LAYER-ONLY VERIFICATION (if mask targets bottom layer)
# ------------------------------------------------------------------------------

expected_bottom_pct = 14.6  #expected percentage for bottom-only masking from siglev_diff[-1]

print(f"\n{'='*80}")
print(f"QA SECTION B: BOTTOM-LAYER-ONLY VERIFICATION (compare vs expected ~{expected_bottom_pct}%)")
print(f"{'='*80}")
print(f"NOTE: This section only relevant if habitat_depth_mask targets bottom layer (layer 9)")
print(f"      If masking other layers, ignore this comparison.\n")

print(f"[QA B.1] Regional Bottom-Layer Verification:")
print(f"  {'Region':<15} {'Habitat (km³)':>14} {'Expected (km³)':>15} {'Diff (%)':>10} {'Status':>8}")  #table header
print(f"  {'-'*15} {'-'*14} {'-'*15} {'-'*10} {'-'*8}")  #separator

for region in regions:  #verify each region against expected bottom percentage
    calc_vol = regional_volumes[region]  #calculated habitat volume from mask
    wc_vol = regional_volumes_WC[region]  #full WC volume reference
    expected_vol = wc_vol * (expected_bottom_pct / 100)  #expected volume if exactly 14.6% of WC
    diff_pct = ((calc_vol - expected_vol) / expected_vol * 100) if expected_vol > 0 else 0  #percentage difference from expected
    status = "[OK]" if abs(diff_pct) < 1 else "[WARN]"  #OK if within 1%, WARN otherwise
    print(f"  {region:<15} {calc_vol:14.3f} {expected_vol:15.3f} {diff_pct:+9.2f}% {status:>8}")  #region comparison row

print(f"\n{'='*80}")
print("QA VERIFICATION COMPLETE - Regional volume masking checks finished")
print(f"{'='*80}\n")