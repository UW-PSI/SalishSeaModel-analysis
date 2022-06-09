# SSMGrid2_060922 development notes

### Developer 
This shapefile was created by Kevin Bogue on June 9th, 2022, to help facilitate work for King County. 
### Modification overview
The shapefile includes information for the Salish Sea Model, version `FVCOM_v2.7ecy` (see the [Salish Sea Modeling Center version history page](https://ssmc-uw.org/salish-sea-modeling-center/salish-sea-model/history/) for more information). Updates to this shapefile from previous versions include:

- Add `DO_std` attribute
- Add `include_indicator` attribute
- Create/add a `uncatagorized_boundary` attribute
- Add `depth` attribute
- Change attribute `tce` to `node_id`
- Change regions from those used in State of Knowledge report (relating to the 2021 Department of Ecology Optimization Report), to the updated regions described in the [Dept. of Ecology GIS](https://waecy.maps.arcgis.com/apps/webappviewer/index.html?id=c7318e19bf3141aca62e980a7e5b53f2) as the `Optimization scenarios regions`
### Attribute Descriptions
These attributes are explained as follows:
- **DO_std**: The dissolved oxygen standard for the given node as established by the EPA.  Values ranges from 1-7.
- **include_indicator**: [0] for nodes where the Department of Ecology has specified to mask out node (due to water depth being too shallow or other reasons), [1] for nodes that are to be included in analyses.  
- **uncatagorized_boundary**: [1] for nodes with areas that are on but mostly outside of regional boundaries. These are mostly points along the outer boundaries of the JDF and Admiralty region as well as the SOG and N. Bays region.
- **depth**: Salish Sea model depth for given node

The attributes `DO_std`, `include_indicator`, and `depth` are from the file `ecy_node_info_v2.csv` that was provided by Su Kyong Yun on June 8th, 2022, via our [shared drive](https://uwnetid.sharepoint.com/sites/og_uwt_psi/Shared%20Documents/Forms/AllItems.aspx?csf=1&web=1&e=OHg44e&cid=5a74cba8%2Da907%2D42fe%2D9640%2D2248c1df3029&RootFolder=%2Fsites%2Fog%5Fuwt%5Fpsi%2FShared%20Documents%2FDO%20%2D%20KC%20%26%20CWA%2F9%2E%20Modeling%2F1%2E%20Scripts%20and%20training%2Fetc%2Earchive%5Ftraining%5Ffrom%5Fsk&FolderCTID=0x012000E1FB0BCD1B07D744B7496CC9C490067D)

