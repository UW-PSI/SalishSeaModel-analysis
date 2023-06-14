#!/usr/bin/env python
# coding: utf-8
# This code was provided by Su Kyong Yun at PNNL
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import os
import pathlib
import time

scenario_name = '3j'
# directory of model output (within directories named the same as `scenario_name`, above)
scenario_output_directory = '/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel'
# RDM modified to SK's 2014 Conditions station file 
baseline_output_directory = '/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/WQM/WQM/hotstart/outputs/ssm_station.out'

def read_file(filename):
    data_pd = pd.read_csv(filename, delim_whitespace=True, skiprows=4, names=col_Names, dtype='unicode')

    data_pd['col_1']=pd.to_numeric(data_pd['col_1'], errors='coerce')
    data_pd['col_2']=pd.to_numeric(data_pd['col_2'], errors='coerce')
    data_pd['col_3']=pd.to_numeric(data_pd['col_3'], errors='coerce')
    data_pd['col_4']=pd.to_numeric(data_pd['col_4'], errors='coerce')
    data_pd['col_5']=pd.to_numeric(data_pd['col_5'], errors='coerce')
    data_pd['col_6']=pd.to_numeric(data_pd['col_6'], errors='coerce')
    data_pd['col_7']=pd.to_numeric(data_pd['col_7'], errors='coerce')
    data_pd['col_8']=pd.to_numeric(data_pd['col_8'], errors='coerce')
    data_pd['col_9']=pd.to_numeric(data_pd['col_9'], errors='coerce')

    ##used for first checking the structure of data
    #start_index=data_pd.index[data_pd.isna().sum(axis=1)==6]
    #adding=((np.ones((26*10,24*366))*np.arange(24*366)).T.flatten()).astype(int)
    #temp_index=np.arange(0,26*10*24*366)+adding
    #data_index=((np.ones((6,26*10*24*366))*start_index.values[temp_index]).T+np.ones((26*10*24*366,6))*np.arange(1,7)).flatten()
    #data_np=data_pd.iloc[np.sort(data_index.astype(int)),:].values.flatten()

    data_index=np.arange(1,13703041).flatten()+(np.ones((6,2283840))*np.arange(0,2283840)).T.flatten()+(np.ones((60,228384))*np.arange(0,228384*6,6)).T.flatten()+(np.ones((1560,8784))*np.arange(0,8784)).T.flatten()
    data_np=data_pd.iloc[data_index.astype(int),:].values.flatten()
    data_np=np.reshape(data_np,(366*24,26,10,54)) #time, station,layer,varialbe
    data_np=data_np[:,:,:,:52]

    return data_np

def statistic_analysis(base_values, compare_values, variable_id):
    bv=np.reshape(np.transpose(base_values[:,:,:,variable_id], (0,2,1)), (366*24*10,26)) #(366*24,10,26)
    cv=np.reshape(np.transpose(compare_values[:,:,:,variable_id], (0,2,1)), (366*24*10,26)) #(366*24,10,26)
    
    diff=bv-cv
    me=np.round(np.nanmean(diff, axis=0),3)
    ame=np.round(np.nanmean(np.abs(diff), axis=0),3)
    rmse=np.round(np.sqrt(np.nanmean(diff**2, axis=0)),3)
    
    base_max=np.round(np.nanmax(bv, axis=0),3)
    base_min=np.round(np.nanmin(bv, axis=0),3)
    base_avg=np.round(np.nanmean(bv, axis=0),3)
    
    comprison_max=np.round(np.nanmax(cv, axis=0),3)
    comparison_min=np.round(np.nanmin(cv, axis=0),3)
    comparison_avg=np.round(np.nanmean(cv, axis=0),3)
    
    return me, ame, rmse, base_max, base_min, base_avg, comprison_max, comparison_min, comparison_avg

def statistic_analysis_pd(base_values, compare_values, variable_id):
    statistic_analysis_pd=pd.DataFrame(statistic_analysis(base_values, compare_values, variable_id)).T
    statistic_analysis_pd.columns=['ME', 'AME', 'RMSE', 
                                   'Baseline_Max', 'Baseline_Min', 'Baseline_Avg', 
                                   'Scenario_Max', 'Scenario_Min', 'Scenario_Avg']
    
    statistic_analysis_pd.index=station_long_name
    return statistic_analysis_pd

def save_statistic_analysis_pd(base_values, compare_values, scenario_name):
    #print(f'writing to: {scenario_name}_stat.xlsx')
    writer = pd.ExcelWriter(scenario_name+'_stat.xlsx')
    for variable_id in range(1,4):
        #print('save_statistic_analysis_pd, variable_id: ', variable_id)
        df=statistic_analysis_pd(base_values, compare_values, variable_id)
        df.to_excel(writer, sheet_name = variable_name[variable_id])
    writer.save()

    
def save_lyr_ME_analysis_pd(base_values, compare_values, scenario_name):
    writer = pd.ExcelWriter(scenario_name+'_ME_lyr.xlsx')
    for variable_id in range(1,4):
        diff=base_values[:,:,:,variable_id]-compare_values[:,:,:,variable_id]
        df=pd.DataFrame(np.round(np.nanmean(diff,axis=0),3), columns=layers)
        df.index=station_long_name
        df.to_excel(writer, sheet_name = variable_name[variable_id])
    writer.save()  
    
def surface_bottom_comparison(scenario_name, np_baseline, np_comparison, station_index):
    legend_loc_surface_bottom=[1.01,1,1.16,1]
    plt.figure(figsize=(10, 15), dpi=80)
    
    plt.subplot(6,1,1)
    plt.title(scenario_name+'\n'+station_long_name[station_index], fontsize=title_fontsize)
    plt.plot(x_time,np_baseline[:,station_index,0,1], color='blue', label='surface_baseline')
    plt.plot(x_time,np_comparison[:,station_index,0,1], '--', color='red', alpha=0.8, label='surface_scenario')
    
    plt.plot(x_time,np_baseline[:,station_index,-1,1], color='orange', label='bottom_baseline')
    plt.plot(x_time,np_comparison[:,station_index,-1,1], '--', color='green', alpha=0.8, label='bottom_scenario')
    plt.ylim([0,15])
    plt.ylabel('DO [mg/L]', fontsize=label_fontsize)
    plt.legend(bbox_to_anchor=(legend_loc_surface_bottom[0],legend_loc_surface_bottom[1]), borderaxespad=0)
    
    plt.subplot(6,1,2)
    #plt.figure(figsize=(10, 3), dpi=80)
    plt.plot(x_time,np_baseline[:,station_index,0,1]-np_comparison[:,station_index,0,1], color=colors[0], label='surface')
    plt.plot(x_time,np_baseline[:,station_index,-1,1]-np_comparison[:,station_index,-1,1], color=colors[9], label='bottom')
    plt.ylim([-0.15,0.15])
    plt.ylabel('\u0394DO [mg/L]\n (baseline-scenario)', fontsize=label_fontsize)
    plt.legend(bbox_to_anchor=(legend_loc_surface_bottom[2],legend_loc_surface_bottom[3]), borderaxespad=0)
    
    #plt.figure(figsize=(10, 6), dpi=80)
    plt.subplot(6,1,3)
    plt.plot(x_time,np_baseline[:,station_index,0,2], color='blue', label='surface_baseline')
    plt.plot(x_time,np_comparison[:,station_index,0,2], '--', color='red', alpha=0.8, label='surface_scenario')
    
    plt.plot(x_time,np_baseline[:,station_index,-1,2], color='orange', label='bottom_baseline')
    plt.plot(x_time,np_comparison[:,station_index,-1,2], '--', color='green', alpha=0.8, label='bottom_scenario')
    plt.ylim([0,0.8])
    plt.ylabel('NO3 [mg/L]', fontsize=label_fontsize)
    plt.legend(bbox_to_anchor=(legend_loc_surface_bottom[0],legend_loc_surface_bottom[1]), borderaxespad=0)
    
    plt.subplot(6,1,4)
    #plt.figure(figsize=(10, 3), dpi=80)
    plt.plot(x_time,np_baseline[:,station_index,0,2]-np_comparison[:,station_index,0,2], color=colors[0], label='surface')
    plt.plot(x_time,np_baseline[:,station_index,-1,2]-np_comparison[:,station_index,-1,2], color=colors[9], label='bottom')
    plt.ylim([0,0.01])
    plt.ylabel('\u0394NO3 [mg/L]\n (baseline-scenario)', fontsize=label_fontsize)
    plt.legend(bbox_to_anchor=(legend_loc_surface_bottom[2],legend_loc_surface_bottom[3]), borderaxespad=0)
    
    #plt.figure(figsize=(10, 6), dpi=80)
    plt.subplot(6,1,5)
    plt.plot(x_time,np_baseline[:,0,0,3], color='blue', label='surface_baseline')
    plt.plot(x_time,np_comparison[:,0,0,3], '--', color='red', alpha=0.8, label='surface_scenario')
    
    plt.plot(x_time,np_baseline[:,0,-1,3], color='orange', label='bottom_baseline')
    plt.plot(x_time,np_comparison[:,0,-1,3], '--', color='green', alpha=0.8, label='bottom_scenario')
    plt.ylim([0,0.18])
    plt.ylabel('NH4 [mg/L]', fontsize=label_fontsize)
    plt.legend(bbox_to_anchor=(legend_loc_surface_bottom[0],legend_loc_surface_bottom[1]), borderaxespad=0)
    
    plt.subplot(6,1,6)
    #plt.figure(figsize=(10, 3), dpi=80)
    plt.plot(x_time,np_baseline[:,station_index,0,3]-np_comparison[:,station_index,0,3], color=colors[0], label='surface')
    plt.plot(x_time,np_baseline[:,station_index,-1,3]-np_comparison[:,station_index,-1,3], color=colors[9], label='bottom')
    plt.ylim([0,0.022])
    plt.ylabel('\u0394NH4 [mg/L]\n (baseline-scenario)', fontsize=label_fontsize)
    plt.legend(bbox_to_anchor=(legend_loc_surface_bottom[2],legend_loc_surface_bottom[3]), borderaxespad=0)
  
    plt.tight_layout()
    plt.savefig(scenario_name+'_'+station_short_name[station_index]+'_surface_bottom.png')
    plt.close('all')
    
def layer_comparison(scenario_name, np_baseline, np_comparison,station_index):
    legend_loc_lyr=[1.01,0.5]
    plt.figure(figsize=(10, 8), dpi=80)
    plt.subplot(3,1,1)
    plt.title(scenario_name+'\n'+station_long_name[station_index], fontsize=title_fontsize)
    for k in range(0,10):
        plt.plot(x_time,np_baseline[:,station_index,k,1]-np_comparison[:,station_index,k,1], color=colors[k], label=str(k+1)+'_lyr')
    plt.legend(bbox_to_anchor=(legend_loc_lyr[0],legend_loc_lyr[1]), loc="center left", borderaxespad=0)
    plt.ylim([-0.15,0.15])
    plt.ylabel('\u0394DO [mg/L]\n (baseline-scenario)', fontsize=label_fontsize)
    
    plt.subplot(3,1,2)
    for k in range(0,10):
        plt.plot(x_time,np_baseline[:,station_index,k,2]-np_comparison[:,station_index,k,2], color=colors[k], label=str(k+1)+'_lyr')
    plt.ylim([0,0.01])
    plt.legend(bbox_to_anchor=(legend_loc_lyr[0],legend_loc_lyr[1]), loc="center left", borderaxespad=0)
    plt.ylabel('\u0394NO3 [mg/L]\n (baseline-scenario)', fontsize=12)
    
    plt.subplot(3,1,3)
    for k in range(0,10):
        plt.plot(x_time,np_baseline[:,station_index,k,3]-np_comparison[:,station_index,k,3], color=colors[k], label=str(k+1)+'_lyr')
    plt.ylim([0,0.025])
    plt.legend(bbox_to_anchor=(legend_loc_lyr[0],legend_loc_lyr[1]), loc="center left", borderaxespad=0)
    plt.ylabel('\u0394NH4 [mg/L]\n (baseline-scenario)', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(scenario_name+'_'+station_short_name[station_index]+'_all_layer.png')
    plt.close('all')    
    
    

#26 stations
station_list=np.array([6151, 7786, 11793, 4040, 5112, 5308, 6231, 9516, 9323, 9887,
                     9683, 10746, 12166, 13789, 13264, 14271, 14885, 15199, 15490, 11959,
                     7796, 15903, 15967, 1424, 7294, 40])

station_short_name=np.array(['BLL009','ADM002','SAR003','SIN001','PSB003','CMB003','GOR001','BUD005',
                             'GRG002','PTH005','ADM001','PSS019','ADM003','HCB010','ELB015','EAP001',
                             'HCB004','NSQ002','DNA001','HCB003','SKG003','TOT002','OAK004','DFO_NB','DFO_GB','SSMOBC'])

station_long_name=np.array(['Bellingham Bay','Admiralty Inlet North (Qumper Pt)','Saratoga Passage East',
                            'Sinclair Inlet, Naval Shipyard','Puget Sound Main Basin West Pt','Commencement Bay',
                            'Gordon Pt','Budd Inlet','Georgia Strait','Port Townsend Harbor (Walan Pt)',
                            'Admiralty Inlet Mid(Bush Pt)','Posession Sound Gedney Island','Admiralty Inlet South',
                            'Hood Canal, Send Creek, Bangor','Elliot Bay, E of Duwamish Head','East Passage',
                            'Hood Canal Gt Bend Sister Pt.','Nisqually Reach Devil Head',
                            'Dana Passage','Hood Canal, Elden, Hamma, Hamma','Skagit Basin',
                            'Toten Inlet Inner','Oakland Bay','DFO Neah Bay Staion','DFO Geargia Basin',
                            'SSM Model OBC Node across from SJF'])

col_Names=["col_1", "col_2", "col_3", "col_4","col_5","col_6","col_7","col_8","col_9"]

x_time=np.array([datetime.datetime(2014,1,1,0,0)+datetime.timedelta(hours=k) for k in range(0,24*366)])

variable_name=np.array(["depth(m)","DO","NO3","NH4","Alg1","Alg2",
                        "LDOC","RDOC","LPOC","RPOC","PO4","DIC",
                        "TALK","pH","pCO2","T","S","P1",
                        "P2","BM1","BM2","NL1","NL2","PL1",
                        "PL2","FI1","FI2","B1SZ","B2SZ","B1LZ",
                        "B2LZ","PR1","PR2","IAVG","DICUPT","DICBMP",
                        "DICPRD","DICMNL","DICDEN","DICGAS","DICSED","DICADV",
                        "DICVDIF","ALKNH4","ALKNO3","ALKNIT","ALKDEN","ALKREM",
                        "ALKNH4SED","ALKNO3SED","ALKADV","ALKVDIF"])

layers=np.array(['lyr1','lyr2','lyr3','lyr4','lyr5','lyr6','lyr7','lyr8','lyr9','lyr10'])

title_fontsize=15
label_fontsize=14

colormap = plt.cm.plasma
colors = [colormap(i) for i in np.linspace(0, 1, 14)]

## READ IN FILES
start = time.time()
start_initial = start
# read in 2014 station file
base_values=read_file(baseline_output_directory)
# read in scenario station file 
compare_values=read_file(f'{scenario_output_directory}/{scenario_name}/hotstart/outputs/ssm_station.out')
end = time.time()
elapsed = (end - start)/60
print(elapsed, " minutes to open files")

## SAVE INFORMATION
start = time.time()
#create stat.xlsx
print('*** Calling save_statistic_analysis_pd ***')
save_statistic_analysis_pd(base_values, compare_values, scenario_name)
end = time.time()
elapsed = (end - start)/60
print(elapsed, " minutes to save statistics excel")

print('*** Calling save_lyr_ME_analysis_pd ***')
start = time.time()
save_lyr_ME_analysis_pd(base_values, compare_values, scenario_name)
end = time.time()
elapsed = (end - start)/60
print(elapsed, " minutes to save layer information to excel")

#create figures
print('*** looping through stations ***')
for station_id in range(0,3):#26):
    print(station_id)
    surface_bottom_comparison(scenario_name, base_values, compare_values, station_id)
    layer_comparison(scenario_name, base_values, compare_values, station_id)

end_final = time.time()
elapsed = (end_final - start_initial)/60
print(elapsed, " minutes to save layer information to excel")    
