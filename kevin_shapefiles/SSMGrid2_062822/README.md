# SSMGrid2_062822 development notes

### Developer 
This shapefile was created by Kevin Bogue on June 9th, 2022, to help facilitate work for King County. The shapefile and basin boundaries come from [The Department of Ecology](https://waecy.maps.arcgis.com/apps/webappviewer/index.html?id=c7318e19bf3141aca62e980a7e5b53f2).s 
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
- **DO_std**: The dissolved oxygen standard for the given node as established by the Department of Ecology.  Values ranges from 1-7.
- **include_indicator**: [0] for nodes where the Department of Ecology has specified to mask out node (due to water depth being too shallow or other reasons), [1] for nodes that are to be included in analyses.  
- **uncatagorized_boundary**: [1] for nodes with areas that are on but mostly outside of regional boundaries. These are mostly points along the outer boundaries of the JDF and Admiralty region as well as the SOG and N. Bays region.
- **depth**: Salish Sea model depth for given node

The attributes `DO_std`, `include_indicator`, and `depth` are from the file `ecy_node_info_v2.csv` that was provided by Su Kyong Yun on June 8th, 2022, via our [shared drive](https://uwnetid.sharepoint.com/sites/og_uwt_psi/Shared%20Documents/Forms/AllItems.aspx?csf=1&web=1&e=OHg44e&cid=5a74cba8%2Da907%2D42fe%2D9640%2D2248c1df3029&RootFolder=%2Fsites%2Fog%5Fuwt%5Fpsi%2FShared%20Documents%2FDO%20%2D%20KC%20%26%20CWA%2F9%2E%20Modeling%2F1%2E%20Scripts%20and%20training%2Fetc%2Earchive%5Ftraining%5Ffrom%5Fsk&FolderCTID=0x012000E1FB0BCD1B07D744B7496CC9C490067D)

### Coordinate system overview
The coordinate system of the shapefile can be identified using `.crs.to_espg()`, e.g.:
```
shapefile_EPSG = gdf.crs.to_epsg()
```
For this shapefile, the returning value of `shapefile_ESPG` is `3857`, i.e. the projection is `EPSG:3857`.  In contrast, the `x-`, `y-coordinate` information from Su Kyong is projected to `EPSG:32610`.  It's important to understand this difference becuase the `x`, `y` columns in this shapefile are projected in `EPSG:32610`, which is different than the shapefile projection.  If we want to find the distance from a lat/lon location to a node location in a way that can be robust and replicable over time then we want to be able to check the projection programatically and to calculate distances to the shapefile centroids.  One method to calculate the `x-`, `y-coordinate` values corresponding to the shapefile is by using `enter_geopandas_dataframe_name.geometry.centroid[i].coords[0][0]` where `i` relates to the centroid number, `[0][0]` is the `x-coordinate` value of the tuple and `[0][1]` is the `y-coordinate` value of the tuple.  An example of code looks like this: 

```
## load shapefile
gdf = gpd.read_file(shapefile_path) 

## get centroid x/y location for each node
[n_nodes,n_attrs]=gdf.shape
x_shp = [gdf.geometry.centroid[i].coords[0][0] for i in range(0,n_nodes)]
y_shp = [gdf.geometry.centroid[i].coords[0][1] for i in range(0,n_nodes)]
gdf['x_shp'] = x_shp
gdf['y_shp'] = y_shp

# save to ammended shapefile
gdf.to_file(root_dir/'kevin_shapefiles/SSMGrid2_060922/SSMGrid2_060922_withcoord.shp') 
```
The problem with this code is that it takes FOREVER to run.  I'm exploring other options includeing asking Kevin to add these `x-`, `y-coordinate` values directly from `ArcGIS`, which I assume may be trivial? 
