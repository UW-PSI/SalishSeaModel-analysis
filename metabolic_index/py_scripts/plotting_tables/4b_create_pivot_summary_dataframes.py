#!/usr/bin/env python
"""
Create Pivot Summary DataFrames
Cells 46-48 from original notebook
Includes pivot tables and summary Excel export
"""


# ============================================================================
# ## Excel pivot table of aggregated excel thresholds
# outputs volumes_wc_parm_summary_all_thresholds.xls
# ============================================================================

# ==============================================================================
# CREATE PIVOT-STYLE SUMMARY TABLE FOR EXCEL PLOTTING
# ==============================================================================

def create_threshold_summary_table(metric_name, scenario='wqm_baseline', regional_total_volumes=None):
    """
    Create pivot-style table with thresholds as rows and regions as columns
    Shows one metric across all thresholds for easy Excel plotting
    Only includes threshold_X format (ignores threshold_DO_standard)
    
    Parameters:
    metric_name: column name from statistics DataFrames (e.g., 'MaxVol_%ofTotal')
    scenario: 'wqm_baseline' or 'wqm_reference'
    regional_total_volumes: dict with total volume for each region in km³ (optional, adds Total_km3 header row)
    
    Returns:
    DataFrame with DO_threshold as rows, regions as columns, optionally with Total_km3 header row
    """
    
    threshold_nums = []  #extract threshold numbers for sorting - only threshold_X format
    for threshold_key in daily_volume_results.keys():
        if threshold_key.startswith('threshold_') and threshold_key != 'threshold_DO_standard':
            num = threshold_key.replace('threshold_', '')
            threshold_nums.append((float(num), threshold_key))
    
    threshold_nums.sort(key=lambda x: x[0])  #sort by threshold number ascending
    
    pivot_data = []  #build pivot table data with each threshold as a row
    
    if regional_total_volumes:  #add first row with total volumes for each region to enable recalculation from percentages
        total_row = {'DO_threshold': 'Total_km3'}  #first row label
        dfs = create_statistics_dataframes(case, ssm_config, 'volume', daily_volume_results[threshold_nums[0][1]], regions, time_coords)
        df_existing = dfs['wqm_baseline']#get any DataFrame just to extract region names in correct order
        df_reference = dfs['wqm_reference']
        df_scenario = df_existing if scenario == 'wqm_baseline' else df_reference
        for _, row in df_scenario.iterrows():  #loop through regions in DataFrame order
            region = row['Region']
            total_vol = regional_total_volumes.get(region, None)  #lookup total volume for this region
            total_row[region] = f"{total_vol:.3f}" if total_vol else "N/A"  #add total volume with same formatting as individual Excel tabs
        pivot_data.append(total_row)  #insert total volumes as first row
    
    for thresh_num, threshold_key in threshold_nums:  #loop through each threshold to create data rows
        dfs = create_statistics_dataframes(case, ssm_config, 'volume', daily_volume_results[threshold_key], regions, time_coords) #get statistics DataFrame for this threshold using helper function

        df_existing = dfs['wqm_baseline']
        df_reference = dfs['wqm_reference']
        df_scenario = df_existing if scenario == 'wqm_baseline' else df_reference  #select scenario-specific DataFrame
        
        row_data = {'DO_threshold': thresh_num}  #initialize row with threshold number
        
        for _, row in df_scenario.iterrows():  #extract the metric values for each region
            region = row['Region']
            value = row[metric_name]
            if isinstance(value, str) and value != 'N/A':  #convert percentage strings back to float for Excel plotting
                if '%' in value:
                    row_data[region] = float(value.replace('%', ''))
                else:
                    row_data[region] = float(value)
            else:
                row_data[region] = value
        
        pivot_data.append(row_data)
    
    pivot_df = pd.DataFrame(pivot_data)  #create DataFrame from collected pivot data
    
    return pivot_df

# ==============================================================================
# CREATE PIVOT TABLES FOR EXCEL PLOTTING - ALL METRICS, BOTH SCENARIOS
# ==============================================================================

print("=== PIVOT TABLES FOR EXCEL PLOTTING ===")
print("Maximum daily volume below DO threshold as % of total regional volume")
pivot_max_existing = create_threshold_summary_table('MaxVol_%ofTotal', 'wqm_baseline', regional_volumes)
print(pivot_max_existing.to_string(index=False))  #removed float_format to fix error
print()

print("Average daily volume below DO threshold as % of total regional volume")
pivot_avg_existing = create_threshold_summary_table('AvgVol_%ofTotal', 'wqm_baseline', regional_volumes)
print(pivot_avg_existing.to_string(index=False))  #removed float_format to fix error
print()

print("Minimum daily volume below DO threshold as % of total regional volume")
pivot_min_existing = create_threshold_summary_table('MinVol_%ofTotal', 'wqm_baseline', regional_volumes)
print(pivot_min_existing.to_string(index=False))  #removed float_format to fix error
print()

# ==============================================================================
# EXCEL EXPORT FOR SUMMARY TABLES from pivot-style tables
# ==============================================================================
import pathlib

def export_volume_summary_excel():
    """
    Export all pivot tables with Total_Vol_km3 columns for recalculation from percentages
    Filename uses dynamic case/scope/variable naming for DO/MI compatibility
    """
    
    excel_dir = pathlib.Path(excel_output_path)  #convert to Path object from global excel_output_path string defined in initialization section
    filename = f'{case}_{scope}_{excel_file_param_name}_volume_percent_all_thresh_summary.xlsx'  #uses dynamic variables (case/scope/excel_file_param_name) for DO/MI compatibility matching individual threshold Excel files
    filepath = excel_dir / filename
        
    # Using scenarios, scenario_excel_tabs initialized at beginning of script workflow
    metrics = ['MaxVol_%ofTotal', 'AvgVol_%ofTotal', 'MinVol_%ofTotal']  #volume metrics to export as pivot tables
    scenario_tuples = [(s, scenario_excel_tabs[s]) for s in scenarios]  # Creates list of tuples: [('wqm_baseline', '2014_Conditions'), ('wqm_reference', 'Reference')] by pairing each scenario name with its Excel tab label

    with pd.ExcelWriter(filepath, mode='w') as writer:  #create Excel file with multiple tabs
        for metric in metrics:
            for scenario_key, scenario_label in scenario_tuples:  # Loops: ('wqm_baseline', '2014_Conditions'), then ('wqm_reference', 'Reference')
                pivot_df = create_threshold_summary_table(metric, scenario_key, regional_volumes)  #pass regional_volumes to add Total_Vol_km3 row for each region enabling recalculation from percentages
                
                metric_short = metric.replace('Vol_%ofTotal', '').replace('Vol_', '')  #extract short metric name: Max, Avg, or Min
                sheet_name = f'{metric_short}_{scenario_label}'  #create tab name combining metric and scenario
                
                pivot_df.to_excel(writer, sheet_name=sheet_name, index=False)  #write DataFrame to Excel tab without row index
    
    print(f"[DEBUG] Excel summary exported to: {filepath}")
    return filepath

export_filepath = export_volume_summary_excel()  #execute export function and store filepath

