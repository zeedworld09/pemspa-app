import math
import streamlit as st
import plotly.graph_objects as go
from geopy.geocoders import Nominatim

# Function to get coordinates based on city name
def get_coordinates(city_name):
    geolocator = Nominatim(user_agent="my_geo_app")
    try:
        location = geolocator.geocode(city_name, timeout=10)
        if location:
            return (location.latitude, location.longitude)
        else:
            st.error(f"City '{city_name}' not found.")
            return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# Function to calculate the Haversine distance
def haversine(koordinat1, koordinat2):
    R = 6371.0  # Radius of the Earth in kilometers
    lat1, lon1 = math.radians(koordinat1[0]), math.radians(koordinat1[1])
    lat2, lon2 = math.radians(koordinat2[0]), math.radians(koordinat2[1])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

# Function to calculate the initial and final bearing (azimuth)
def calculate_bearing(koordinat1, koordinat2):
    lat1, lon1 = math.radians(koordinat1[0]), math.radians(koordinat1[1])
    lat2, lon2 = math.radians(koordinat2[0]), math.radians(koordinat2[1])

    dlon = lon2 - lon1

    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)

    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    initial_bearing = (initial_bearing + 360) % 360  # Normalize to 0-360 degrees

    final_bearing = (initial_bearing + 180) % 360  # Final bearing is 180 degrees opposite

    return initial_bearing, final_bearing

# Function to interpolate the great circle path
def interpolate_great_circle(koordinat1, koordinat2, n=100):
    lat1, lon1 = math.radians(koordinat1[0]), math.radians(koordinat1[1])
    lat2, lon2 = math.radians(koordinat2[0]), math.radians(koordinat2[1])

    d = 2 * math.asin(math.sqrt(math.sin((lat2 - lat1) / 2)**2 +
                                math.cos(lat1) * math.cos(lat2) *
                                math.sin((lon2 - lon1) / 2)**2))
    
    interpolated_points = []
    for i in range(n + 1):
        f = i / n
        A = math.sin((1 - f) * d) / math.sin(d)
        B = math.sin(f * d) / math.sin(d)
        
        x = A * math.cos(lat1) * math.cos(lon1) + B * math.cos(lat2) * math.cos(lon2)
        y = A * math.cos(lat1) * math.sin(lon1) + B * math.cos(lat2) * math.sin(lon2)
        z = A * math.sin(lat1) + B * math.sin(lat2)
        
        lat = math.atan2(z, math.sqrt(x**2 + y**2))
        lon = math.atan2(y, x)
        
        interpolated_points.append((math.degrees(lat), math.degrees(lon)))
    
    return interpolated_points

# Function to create the map visualization
def create_map(segmen, koordinat1, koordinat2, projection="orthographic"):
    fig = go.Figure()

    # Add the marker locations
    fig.add_trace(go.Scattergeo(
        lon=[koordinat1[1], koordinat2[1]],
        lat=[koordinat1[0], koordinat2[0]],
        mode='markers',
        marker=dict(size=10, color='red'),
        text=['Point 1', 'Point 2']
    ))

    # Add the great circle path
    fig.add_trace(go.Scattergeo(
        lon=[s[1] for s in segmen],
        lat=[s[0] for s in segmen],
        mode='lines',
        line=dict(width=2, color='blue')
    ))

    # Set projection type
    fig.update_geos(
        projection_type=projection,
        showcountries=True,
        showcoastlines=True,
        showland=True,
        showocean=True,
        oceancolor="LightBlue",
        landcolor="LightGreen"
    )

    fig.update_layout(
        height=700,  # Fullscreen map
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )
    
    return fig

# Streamlit App
st.title("Great Circle Distance Calculator")

# Sidebar Menu as Dropdown
menu = st.sidebar.selectbox("Select Menu", ["Calculate Distance", "App Information"])

if menu == "Calculate Distance":
    # Input mode selection
    input_mode = st.sidebar.selectbox("Choose Input Mode", ["City Name", "Manual Coordinates"])
    
    if input_mode == "City Name":
        # Input City Names
        st.sidebar.header("Enter City Names")
        city1 = st.sidebar.text_input("Starting City", value="Jakarta")
        city2 = st.sidebar.text_input("Destination City", value="Tokyo")

        # Get coordinates from city names
        koordinat1 = get_coordinates(city1)
        koordinat2 = get_coordinates(city2)
    else:
        # Input Manual Coordinates
        st.sidebar.header("Enter Coordinates")
        lat1 = st.sidebar.number_input("Latitude of Point 1", value=-6.2, format="%.6f")
        lon1 = st.sidebar.number_input("Longitude of Point 1", value=106.8166, format="%.6f")
        lat2 = st.sidebar.number_input("Latitude of Point 2", value=35.6895, format="%.6f")
        lon2 = st.sidebar.number_input("Longitude of Point 2", value=139.6917, format="%.6f")
        koordinat1 = (lat1, lon1)
        koordinat2 = (lat2, lon2)

    if koordinat1 and koordinat2:
        # Calculate Distance and Bearings
        jarak_haversine = haversine(koordinat1, koordinat2)
        initial_bearing, final_bearing = calculate_bearing(koordinat1, koordinat2)
        segmen = interpolate_great_circle(koordinat1, koordinat2)

        # Display Results
        st.metric("Haversine Distance", f"{jarak_haversine:.2f} km")
        st.metric("Initial Bearing", f"{initial_bearing:.2f}°")
        st.metric("Final Bearing", f"{final_bearing:.2f}°")

        # Display Map
        projection = st.sidebar.selectbox("Select Map Type", ["Globe", "Map"])
        
        # Set projection type based on selection
        if projection == "Globe":
            projection_type = "orthographic"
        else:
            projection_type = "mercator"
        
        fig = create_map(segmen, koordinat1, koordinat2, projection_type)
        st.plotly_chart(fig, use_container_width=True)

elif menu == "App Information":
    st.subheader("About the App")
    st.write("""
    This app uses the Great Circle method to calculate the shortest distance
    between two points on the surface of the Earth. The bearing (azimuth)
    indicates the direction from the start point to the destination point and vice versa.
    """)