import global_vars

import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.io.shapereader import natural_earth, Reader
from cartopy.feature import ShapelyFeature
from shapely.geometry import Point, Polygon
import geopandas as gpd
import math
import matplotlib.pyplot as plt
from io import BytesIO

polygon_colors_SAME = {
    "TOR": '#d900ff',
    "SVR": '#ffb300',
    "FFW": '#00bf03',
    "SPS": '#0086bf',
    "FAY": '#00ff8c',
    "FLW": '#00ff40',
    "FLS": '#00ff40',
} # SMW/MAW for Special Marine Warning

ucf = Point(-81.2001, 28.6024) # UCF coords for shapely polygon checking
ucf_point = gpd.GeoSeries([Point(ucf)], crs="EPSG:4326") # Converting UCF to GeoSeries now so we aren't doing this over and over again for just one point.
ucf_point = ucf_point.to_crs(epsg=6439) # Convert to local CRS, this one being Florida East in meters.

roads_shp = r"C:\Users\sheri\OneDrive\Desktop\WeatherAlerts\ne_10m_roads_north_america.shp" # Natural Earth road shapefile path.

def ucf_in_or_near_polygon(geodat): # Specific to figuring out if UCF is included or near the alert polygon, only for WEAS handling.
    if not geodat:
        return False, ""
    
    poly = Polygon(geodat)

    if ucf.within(poly):
        return True, "within"
    else: # Handle logic to find out if this alert polygon is near UCF.
        gdf_alert = gpd.GeoSeries([poly], crs="EPSG:4326")

        gdf_alert = gdf_alert.to_crs(epsg=6439)  # NAD83 / Florida East (meters)

        # Buffer UCF point by 3 miles (1 mile ≈ 1609.34 m)
        pBuffer = ucf_point.buffer(global_vars.buffer_WEASTrigger * 1609.34)

        # Check if alert polygon intersects the buffered area
        intersects = gdf_alert.intersects(pBuffer.iloc[0])[0]

        if intersects:
            return True, "around"
    return False, ""

def get_bounds_from_polygon(polygon_coords, buffer_miles=0):
    lons, lats = zip(*polygon_coords)  # unzip into separate lists
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)

    if buffer_miles > 0:
        # 1 mile ~ 0.0145 degrees latitude
        lat_buffer = buffer_miles * 0.0145
        avg_lat = sum(lats) / len(lats)
        # adjust longitude for latitude
        lon_buffer = buffer_miles * 0.0145 / max(0.0001, abs(math.cos(math.radians(avg_lat))))
        
        min_lon -= lon_buffer
        max_lon += lon_buffer
        min_lat -= lat_buffer
        max_lat += lat_buffer

    return min_lon, max_lon, min_lat, max_lat


def filter_points_in_bounds(points, bounds):
    """
    points: list of tuples (name, lon, lat)
    bounds: min_lon, max_lon, min_lat, max_lat
    returns: filtered list of points inside bounds
    """
    min_lon, max_lon, min_lat, max_lat = bounds
    filtered = []
    for name, lon, lat in points:
        if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
            filtered.append((name, lon, lat))
    return filtered

def generate_alert_image(coords, code): # function to generate an image for the alert area.
    if not coords: # Gating. Return false if we don't have coords (in cases where alerts are for county and have no geodata)
        return False 
    
    city_points = [ # Expand to include locations as needed. Maybe want a secondary list for more minor locations?
        ("Orlando", -81.379, 28.538),
        ("Oviedo", -81.204, 28.669),
        ("Bithlo", 	-81.11016, 28.5632373),
        ("MCO", -81.308, 28.431),
        ("Winter Park", -81.348, 28.599),
        ("Lake Mary", -81.347, 28.777),
        ("Sanford", -81.291, 28.802),
        ("UCF", -81.2023, 28.6024),
        ("Apopka", -81.5322149, 28.6934076),
        ("Lake Nona", -81.2639123, 28.3976142),
        ("Doctor Phillips", -81.4914804, 28.4608599),
        ("Casselberry", -81.3382005, 28.6714702),
        ("Rosen", -81.4421618, 28.4290395),
        ("Ocoee", -81.5441944, 28.5694468),
        ("Wedgefield", -81.0776654, 28.4853741),
        ("Christmas", -80.9977987, 28.520462),
        ("Hunter's Creek", -81.421598, 28.3568574),
        ("Titusville", -80.8075537, 28.6122187),
        ("Melbourne", -80.6081089, 28.0836269),
        ("Palm Bay", -80.5886646, 28.0344621),
        ("Cape Canaveral", -80.6077132, 28.3922182),
        ("Rockledge", -80.736647, 28.3201553),
        ("Viera", -80.7301522, 28.243006),
        ("Clermont", -81.7728543, 28.5494447),
        ("Eustis", -81.6853534, 28.8527675),
        ("Mount Dora", -81.6458572379921, 28.81874675),
        ("Kissimmee", -81.407571, 28.2919557),
        ("St. Cloud", -81.2839038, 28.2498534),
        ("Harmony", -81.1450659, 28.1894586),
        ("Holopaw", -81.0761754, 28.1358492),
        ("Astor Park", -81.5720175, 29.1535911),
        ("Seville", -81.4925714, 29.3169208),
        ("Ormond Beach", -81.0557921, 29.2854132),
        ("Daytona Beach", -81.0228331, 29.2108147),
        ("Port Orange", -81.0105961760805, 29.10162805),
        ("DeLand", -81.3031098, 29.0283213),
        ("Deltona", -81.2636738, 28.9005446),
        ("New Smyrna Beach", -80.9269984, 29.0258191),
        ("Scottsmoor", -80.87811, 28.7669363),
        ("Satellite Beach", -80.5900519, 28.1761233),
        ("Yeehaw Junction", -80.9043171, 27.6997754),
        ("Lakeland", -81.9498042, 28.0394654),
        ("Highland Park", -81.5617427, 27.8650254),
        ("Polk City", -81.8239676, 28.1825147),
        ("Poinciana", -81.4932235, 28.1743275),
        ("Winter Haven", -81.7328567, 28.0222435),
        ("Homeland", -81.8245267, 27.8178061),
        ("Bradley Junction", -81.9803629, 27.7953069),
        ("Frostproof", -81.5306313, 27.7458626),
        ("Indian Lake Estates", -81.3786902, 27.8141828),
        ("Bartow", -81.8431567, 27.8963791),
        ("Fruit Cove", -81.6069919, 30.0928745),
        ("Saint Augustine", -81.3124341, 29.9012437),
        ("Saint Augustine Beach", -81.2716634, 29.8508613),
        ("Hartford", -81.5065599, 30.0156817),
        ("Palmo", -81.5673077, 29.9663545),
        ("Old Town Villages", -81.3996685, 29.9103519),
        ("Crescent Beach", -81.2423048, 29.738289),
        ("Hastings", -81.5081338, 29.7180248),
        ("Shell Bluff", -81.4925332, 29.5071816),
        ("Myrtle Island", -81.441184, 29.5855272),
        ("Palm Coast", -81.2078699, 29.5844524),
        ("Dupont", -81.2225622, 29.4269207),
        ("Codys Corner", -81.3110131, 29.3433587),
        ("Flagler Beach", -81.1269982, 29.4749927),
        ("Bunnell", -81.2576832, 29.4657731),
        ("Fellsmere", -80.6013691, 27.7677894),
        ("Sebastian", -80.4706078, 27.816415),
        ("Indian River Shores", -80.3781423, 27.7124084),
        ("Vero Beach", -80.3972736, 27.6386434),
        ("Oslo", -80.3807842, 27.587099),
        ("Lakewood Park", -80.3858334, 27.539169),
        ("Bayside Lakes", -80.6665445, 27.9488718),
        ("Grant-Valkaria", -80.5773329, 27.9378067),
        ("Deer Run", -80.6500523, 27.8713665),
        ("Micco", -80.5052124, 27.8639584),
        ("Port Saint John", -80.7859151, 28.476174),
        ("Mims", -80.8457402, 28.683293),
    ]

    poly = Polygon(coords)

    minx, miny, maxx, maxy = poly.bounds
    
    if not poly:
        return False

    fig, ax = plt.subplots(
        figsize=(14, 10),
        subplot_kw={'projection': ccrs.PlateCarree()}
    )

    # Applying overlays
    ax.add_feature(cfeature.LAND.with_scale('10m'), facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN.with_scale('10m'), facecolor='lightblue')
    ax.add_feature(cfeature.LAKES.with_scale('10m'), facecolor='lightblue')
    ax.add_feature(cfeature.RIVERS.with_scale('10m'), edgecolor='blue')
    ax.add_feature(cfeature.BORDERS.with_scale('10m'), edgecolor='black')
    ax.add_feature(cfeature.STATES.with_scale('10m'), edgecolor='black')

   # Counties (Natural Earth Admin 2)
    counties_shp = natural_earth(resolution='10m', category='cultural', name='admin_2_counties')
    counties_feature = ShapelyFeature(
        geometries=Reader(counties_shp).geometries(),
        crs=ccrs.PlateCarree(),
        facecolor='none',
        edgecolor='red',
        linewidth=1
    )
    if counties_feature is not None:
        ax.add_feature(counties_feature)

    roads_feature = ShapelyFeature(
        Reader(roads_shp).geometries(),
        crs=ccrs.PlateCarree(),
        edgecolor='grey',  # whatever color you like
        facecolor='none'
    )
    if roads_feature is not None:
        ax.add_feature(roads_feature)
    
    polyColor = '#6e6e6e'
    
    if code in polygon_colors_SAME:
        polyColor = polygon_colors_SAME[code]

    # Plot polygon
    x, y = poly.exterior.xy
    ax.plot(x, y, color=polyColor, linewidth=2, transform=ccrs.PlateCarree())
    ax.fill(x, y, color=polyColor, alpha=0.2, transform=ccrs.PlateCarree())

    # Zoom to polygon with padding
    lon_pad = 0.5  # wider east-west
    lat_pad = 0.25  # shorter north-south
    ax.set_extent([minx - lon_pad, maxx + lon_pad, miny - lat_pad, maxy + lat_pad], crs=ccrs.PlateCarree())
    # we love rectangles btw

    bounds = get_bounds_from_polygon(coords, 15)

    filtered_points = filter_points_in_bounds(city_points, bounds)

    for name, lon, lat in filtered_points:
        ax.scatter(lon, lat, color='blue', s=45, transform=ccrs.PlateCarree())
        ax.text(lon, lat + 0.01, name, fontsize=9, transform=ccrs.PlateCarree())

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf  # Return image