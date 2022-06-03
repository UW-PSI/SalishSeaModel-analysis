# 2014 bounding scenarios model output on Klone 
See [bounding_scenarios_mdl_info.xlxs](https://uwnetid.sharepoint.com/:x:/r/sites/og_uwt_psi/_layouts/15/Doc.aspx?sourcedoc=%7B1E21B111-D763-443D-B04C-44E241B144FF%7D&file=bounding_scenarios_mdl_info.xlsx&action=default&mobileredirect=true&cid=68de1b56-cddc-4d4a-a771-e2aa480a7e93) for a complete list of the scenarios and their directory paths
To start with, I will summarize the files in the `Reference` run with files located in 
```
/mmfs1/gscratch/ssmc/USRS/PSI/Adi/BS_WQM/2014_SSM4_WQ_ref_orig/hotstart/outputs
```
Strangely, all files appear to be executables (`*` at the end).  I'm not familiar with having files show up as executables like this.  The complete list of files in this directory are:
```
algae.3_yr_11*         restart.180*         s_hy_base000_pnnl007_nodes.mat*
avg_plot.3_yr_11*      restart.220*         s_hy_base000_pnnl007_nodes.nc*
benthic_flux.3_yr_11*  restart.300*         s_hy_base000_pnnl007_sedim.mat*
diagnostics.3_yr_11*   restart.360*         s_hy_base000_pnnl007_sedim.nc*
kinetics.3_yr_11*      restart.364*         slurm-201071.out*
plot.3_yr_11*          restart.40*          snapshot.3_yr_11*
restart.100*           restart.60*          transport_flux.3_yr_11*
restart.140*           run_bs_wqm_HYAK.sh*
```
The model output file used in the python script from Su Kyong is `s_hy_base000_pnnl007_nodes.nc*`.  It's big: 272 GB; which is great!
Running `ncdump` on this files yields the following information about this file's content.
```
[rdmseas@klone1 outputs]$ module load stf/netcdf/c-ompi/4.8.1
[rdmseas@klone1 outputs]$ ncdump -h s_hy_base000_pnnl007_nodes.nc
netcdf s_hy_base000_pnnl007_nodes {
dimensions:
	IJK = 160120 ;
	Time = 8760 ;
variables:
	float Var_1(Time, IJK) ;
		Var_1:FVCOM_Name = "Time IDX" ;
	float Var_2(Time, IJK) ;
		Var_2:FVCOM_Name = "I" ;
	float Var_3(Time, IJK) ;
		Var_3:FVCOM_Name = "J" ;
	float Var_4(Time, IJK) ;
		Var_4:FVCOM_Name = "K" ;
	float Var_5(Time, IJK) ;
		Var_5:FVCOM_Name = "Surface Elevation" ;
	float Var_6(Time, IJK) ;
		Var_6:FVCOM_Name = "Still Water Depth ICM" ;
	float Var_7(Time, IJK) ;
		Var_7:FVCOM_Name = "Surface Elevation ICM" ;
	float Var_8(Time, IJK) ;
		Var_8:FVCOM_Name = "Total Water Depth ICM" ;
	float Var_9(Time, IJK) ;
		Var_9:FVCOM_Name = "Layer Center Depth ICM" ;
	float Var_10(Time, IJK) ;
		Var_10:FVCOM_Name = "Conc. of DO mg/l" ;
	float Var_11(Time, IJK) ;
		Var_11:FVCOM_Name = "Conc. of OC_D mg/l" ;
	float Var_12(Time, IJK) ;
		Var_12:FVCOM_Name = "Conc of I_GAM1_C mg/l" ;
	float Var_13(Time, IJK) ;
		Var_13:FVCOM_Name = "Conc of I_GAM2_C mg/l" ;
	float Var_14(Time, IJK) ;
		Var_14:FVCOM_Name = "Conc. of NH3 mg/l" ;
	float Var_15(Time, IJK) ;
		Var_15:FVCOM_Name = "Conc. of NO3 mg/l" ;
	float Var_16(Time, IJK) ;
		Var_16:FVCOM_Name = "Conc. of PO4 mg/l" ;
	float Var_17(Time, IJK) ;
		Var_17:FVCOM_Name = "total netPP mgC/m2/d" ;
	float Var_18(Time, IJK) ;
		Var_18:FVCOM_Name = "Temperature C" ;
	float Var_19(Time, IJK) ;
		Var_19:FVCOM_Name = "Conc. of Salinity ppt" ;
	float Var_20(Time, IJK) ;
		Var_20:FVCOM_Name = "PAR E/m2/day" ;
	float Var_21(Time, IJK) ;
		Var_21:FVCOM_Name = "RDOC gC/m3" ;
	float Var_22(Time, IJK) ;
		Var_22:FVCOM_Name = "LPOC gC/m3" ;
	float Var_23(Time, IJK) ;
		Var_23:FVCOM_Name = "RPOC gC/m3" ;
	float Var_24(Time, IJK) ;
		Var_24:FVCOM_Name = "GPP mgC/m2/d" ;
	float Var_25(Time, IJK) ;
		Var_25:FVCOM_Name = "NPP mgC/m2/d" ;
	float Var_26(Time, IJK) ;
		Var_26:FVCOM_Name = "LDON gN/m3" ;
	float Var_27(Time, IJK) ;
		Var_27:FVCOM_Name = "RDON gN/m3" ;
	float Var_28(Time, IJK) ;
		Var_28:FVCOM_Name = "LPON gN/m3" ;
	float Var_29(Time, IJK) ;
		Var_29:FVCOM_Name = "RPON gN/m3" ;
	float Var_30(Time, IJK) ;
		Var_30:FVCOM_Name = "DIC mmol/m3" ;
	float Var_31(Time, IJK) ;
		Var_31:FVCOM_Name = "TAlk mmol/m3" ;
	float Var_32(Time, IJK) ;
		Var_32:FVCOM_Name = "pH" ;
	float Var_33(Time, IJK) ;
		Var_33:FVCOM_Name = "pCO2 uatm" ;
	float Var_34(Time, IJK) ;
		Var_34:FVCOM_Name = "DIC uptake mmolC/m3/day" ;
	float Var_35(Time, IJK) ;
		Var_35:FVCOM_Name = "DIC resp mmolC/m3/day" ;
	float Var_36(Time, IJK) ;
		Var_36:FVCOM_Name = "DIC pred mmolC/m3/day" ;
	float Var_37(Time, IJK) ;
		Var_37:FVCOM_Name = "DIC remin DOC mmolC/m3/day" ;
	float Var_38(Time, IJK) ;
		Var_38:FVCOM_Name = "DIC denit mmolC/m3/day" ;
	float Var_39(Time, IJK) ;
		Var_39:FVCOM_Name = "DIC air-sea mmolC/m3/day" ;
	float Var_40(Time, IJK) ;
		Var_40:FVCOM_Name = "DIC sedims mmolC/m3/day" ;
	float Var_41(Time, IJK) ;
		Var_41:FVCOM_Name = "DIC adv+hdiff mmolC/m3/day" ;
	float Var_42(Time, IJK) ;
		Var_42:FVCOM_Name = "DIC vdiff mmolC/m3/day" ;
	float Var_43(Time, IJK) ;
		Var_43:FVCOM_Name = "TA uptake NH4 mmol/m3/day" ;
	float Var_44(Time, IJK) ;
		Var_44:FVCOM_Name = "TA uptake NO3 mmol/m3/day" ;
	float Var_45(Time, IJK) ;
		Var_45:FVCOM_Name = "TA nitrif mmol/m3/day" ;
	float Var_46(Time, IJK) ;
		Var_46:FVCOM_Name = "TA denit mmol/m3/day" ;
	float Var_47(Time, IJK) ;
		Var_47:FVCOM_Name = "TA remin DON mmol/m3/day" ;
	float Var_48(Time, IJK) ;
		Var_48:FVCOM_Name = "TA sedims NH4 mmol/m3/day" ;
	float Var_49(Time, IJK) ;
		Var_49:FVCOM_Name = "TA sedims NO3 mmol/m3/day" ;
	float Var_50(Time, IJK) ;
		Var_50:FVCOM_Name = "TA adv+hdiff mmolC/m3/day" ;
	float Var_51(Time, IJK) ;
		Var_51:FVCOM_Name = "TA vdiff mmolC/m3/day" ;
	float Var_52(Time, IJK) ;
		Var_52:FVCOM_Name = "Water Body" ;
}
```
This file appears to be the full model output complete with all the information we need. 
I am not yet familiar with how to go from the model coordinates, namely:
```
float Var_2(Time, IJK) ;
		Var_2:FVCOM_Name = "I" ;
float Var_3(Time, IJK) ;
		Var_3:FVCOM_Name = "J" ;
```
to lat/lon.  My guess is that `I` and `J` are grid coordinates rather than lat/lon coordinates.  In addition, the 2D grid is flattened to 160120 values, and I need to learn how to map from the location of this flattened index to a lat/lon location.  

The good news is that all the `*.nc` files appear to be complete output files.  I looked in three other directories and they all had a `*_nodes.nc` file of 272 Gb. 
