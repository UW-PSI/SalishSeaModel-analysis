This document provides an overview of the work of getting sediment flux variables included in output

# Output file overview (Sept 21, 2022)

File locations that I was given were:
```
reference: /mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/WQM_REF
exist: /mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/WQM
```
I found model output in:
```
/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/WQM_REF/WQM_REF/hotstart/outputs
```
However, these files don't have NPP and sediment flux information.  
```
(base) [rdmseas@klone-login01 outputs]$ allocate1
salloc: Granted job allocation 6230148
salloc: Waiting for resource configuration
salloc: Nodes n3263 are ready for job
(base) [rdmseas@n3263 outputs]$ module load stf/netcdf/c-ompi/4.8.1
(base) [rdmseas@n3263 outputs]$ ncdump -h ssm_output.nc
netcdf ssm_output {
dimensions:
	time = 8784 ;
	siglay = 10 ;
	node = 16012 ;
variables:
	float time(time) ;
	float depth(time, siglay, node) ;
	float DOXG(time, siglay, node) ;
	float LDOC(time, siglay, node) ;
	float B1(time, siglay, node) ;
	float B2(time, siglay, node) ;
	float NH4(time, siglay, node) ;
	float NO3(time, siglay, node) ;
	float PO4(time, siglay, node) ;
	float temp(time, siglay, node) ;
	float salinity(time, siglay, node) ;
	float RDOC(time, siglay, node) ;
	float LPOC(time, siglay, node) ;
	float RPOC(time, siglay, node) ;
	float TDIC(time, siglay, node) ;
	float TALK(time, siglay, node) ;
	float pH(time, siglay, node) ;
	float pCO2(time, siglay, node) ;
}

```
I sent an email to Su Kyong on 9/22 asking for paths with complete model output. 

Ben suggested looking at the station output files.  The location for these files for the `Baseline` scenario is:

`/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/WQM/WQM/hotstart/outputs`

They include:
```
algae.3_yr_11         exist_do.pkl                      restart.180  slurm-5845639.out      ssm_history_00002.out  ssm_history_00009.out
algae_exist.pkl       kinetics.3_yr_11                  restart.220  slurm-5900090.out      ssm_history_00003.out  ssm_history_00010.out
avg_plot.3_yr_11      make_netcdf_output_klone_par.sh*  restart.300  slurm-5900096.out      ssm_history_00004.out  ssm_output.nc
benthic_flux.3_yr_11  nitrogen_exist.pkl                restart.360  slurm-5900101.out      ssm_history_00005.out  ssm_station.out
create_do_pkl.py      plot.3_yr_11                      restart.364  slurm-5900108.out      ssm_history_00006.out  transport_flux.3_yr_11
create_do_pkl.sh      restart.100                       restart.40   snapshot.3_yr_11       ssm_history_00007.out
diagnostics.3_yr_11   restart.140                       restart.60   ssm_history_00001.out  ssm_history_00008.out
```

Although most of the `.3_yr_11` files are empty.  Looking in `benthic_flux.3_yr_11` shows that it contains `S E D I M E N T   I N I T I A L   C O N D I T I O N S`, which suggests that the other `.3_yr_11` files are initial condition files.  Looking at `$ head ssm_station.out` shows:
```
(base) [rdmseas@klone-login01 outputs]$ head ssm_station.out
 Nstation,Nlayer
          26          10
Variables="StationID","Node","Layer","depth(m)","DO","NO3","NH4","Alg1","Alg2","LDOC","RDOC","LPOC","RPOC","PO4","DIC","TALK","pH","pCO2","T","S","P1","P2","BM1","BM2","NL1","NL2","PL1","PL2","FI1","FI2","B1SZ","B2SZ","B1LZ","B2LZ","PR1","PR2","IAVG","DICUPT","DICBMP","DICPRD","DICMNL","DICDEN","DICGAS","DICSED","DICADV","DICVDIF","ALKNH4","ALKNO3","ALKNIT","ALKDEN","ALKREM","ALKNH4SED","ALKNO3SED","ALKADV","ALKVDIF","Jcin1","Jcin2","Jcin3","Jnin1","Jnin2","Jnin3","Jpin1","Jpin2","Jpin3","Jsin","O20","Depth","Tw","NH30","NO30","PO40","SI0","CH40","SALw","SOD","Jnh4","Jno3","JDenitT","Jch4","Jch4g","Jhs","Jpo4","Jsi","NH31","NH32","NO31","NO32","PO41","PO42","Si1","Si2","CH41","CH42","HS1","HS2","POC21","POC22","POC23","PON21","PON22","PON23,"POP21","POP22","POP23","POS2","H1","BEN_STR"
          26          10  4.629629629629630E-004
```

