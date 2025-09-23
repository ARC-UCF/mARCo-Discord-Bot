To retreive the files regarding the roads, refer to natural earth and the North America Roads 10m. The file is needed to successfully run the code for image generation.

## Shapehandler
Responsible for geometries given from polygon coordinates as provided by the NOAA api. Includes distance information and image generation based on given points. Will error if no points are provided. Requires a geoJSON format (like provided by the NOAA api).

`ucf_in_or_near_polygon(coordinates)` - Determines whether or not UCF is in or near a defined polygon. Based upon `buffer_WEASTrigger`, provides two outputs; `alertSpace` and `type`. `alertSpace` is a boolean and returns `True` when the alert polygon is within the defined area from campus. Returns `False` otherwise. `type` returns whether or not UCF is "around" or "within" the alert polygon.
