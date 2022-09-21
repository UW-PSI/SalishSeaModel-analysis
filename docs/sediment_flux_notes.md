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

