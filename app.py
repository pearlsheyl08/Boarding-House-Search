import pickle
import streamlit as st
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice as ors
from functools import reduce
import operator


# Load data and similarity model
with open('artifacts/bh_list.pkl', 'rb') as f:
    bh = pickle.load(f)

with open('artifacts/similarity.pkl', 'rb') as f:
    similarity = pickle.load(f)

# Set up Streamlit app
st.header("Boarding House Search")

# Filter options
location_list = bh['Location'].str.title().unique()  
bed_list = bh['Bed'].unique()                        
bath_list = bh['Bath'].unique()                      

# Filter inputs from user
selected_location = st.selectbox('Select a Location:', location_list)
selected_bed = st.selectbox('Select Number of Beds:', bed_list)
selected_bath = st.selectbox('Select Bath Type:', bath_list)
selected_price = st.slider('Select Maximum Price:', int(bh['Price'].min()), int(bh['Price'].max()))

# Preprocess the data to ensure consistent capitalization
bh['Location'] = bh['Location'].str.title()

# Recommendation function
def recommend(location, bed, bath, price):
    # Filter data based on user selection
    filtered_data = bh[
        (bh['Location'] == location) &  # No need for str.title() since already applied
        (bh['Bed'] == bed) &
        (bh['Bath'] == bath) &
        (bh['Price'] <= price)
    ]

    # Sort results by price and show top 5 matches
    recommendations = filtered_data.sort_values(by='Price', ascending=True).head(5)
    return recommendations[['Name', 'Price', 'Street', 'Location']]

# Display recommendations
recommendations = recommend(selected_location, selected_bed, selected_bath, selected_price)

if not recommendations.empty:
    st.subheader("Recommended Boarding Houses")
    st.write(recommendations)
else:
    st.write("No recommendations found for the selected criteria.")


# Initialize OpenRouteService client
client = ors.Client(key='5b3ce3597851110001cf62488b5b21f9e9294ba4bd6ecd103bf2bb74')

# Coordinates with names
coords_with_names = [
    {"coord": [122.56246, 10.70078], "name": "Luna Street, Iloilo City Proper"},
    {"coord": [122.56529, 10.69776], "name": "Delgado Street, Iloilo City Proper"},
    {"coord": [122.56475, 10.69699], "name": "Mabini Street, Iloilo City Proper"},
    {"coord": [122.57462, 10.70182], "name": "Rizal Street, Iloilo City Proper"},
    {"coord": [122.56246, 10.70078], "name": "General Luna Street, Iloilo City Proper"},
    {"coord": [122.55564, 10.72769], "name": "431 A Lopez Jaena St., old railroad, Jaro"},
    {"coord": [122.55564, 10.72769], "name": "152 Lopez Jaena St., Jaro"},
    {"coord": [122.56732, 10.74389], "name": "E. Lopez St., Jaro"},
    {"coord": [122.56240, 10.69746], "name": "Villa Matilde, Jaro"},
    {"coord": [122.55708, 10.73620], "name": "36 A D.B. Ledesma St., Jaro"},
    {"coord": [122.58053, 10.71679], "name": "Ticud, La Paz, Iloilo City, Lapaz"},
    {"coord": [122.32826, 10.75904], "name": "Zone 3 Brgy. Baldoza, La Paz, Iloilo City, Lapaz"},
    {"coord": [122.57987, 10.72090], "name": "San Juan, Ledesco City Homes, La Paz, Iloilo City, Lapaz"},
    {"coord": [122.57536, 10.71426], "name": "La Paz Norte, Iloilo City, Lapaz"},
    {"coord": [122.56774, 10.70511], "name": "243 Mirasol Subdivision, Nabitasan, Lapaz"},
    {"coord": [122.50738, 10.68188], "name": "Sto. Niño Street, Arevalo"},
    {"coord": [122.59208, 10.75619], "name": "Coastal Road, Arevalo"},
    {"coord": [122.52013, 10.68375], "name": "Yulo Drive, Arevalo"},
    {"coord": [122.55170, 10.70394], "name": "Villa San Pedro St., Arevalo"},
    {"coord": [122.50857, 10.67989], "name": "Villa Beach Road, Arevalo"},
    {"coord": [122.58212, 10.69827], "name": "Lapuz Norte Road, Lapuz"},
    {"coord": [122.57663, 10.70179], "name": "Jalandoni Street, Lapuz"},
    {"coord": [122.57215, 10.70656], "name": "Rizal Road, Lapuz"},
    {"coord": [122.57309, 10.70179], "name": "Burgos Street, Lapuz"},
    {"coord": [122.53995, 10.71699], "name": "Mirasol Street, Mandurriao"},
    {"coord": [122.53578, 10.71525], "name": "Onate De Leon Street, Mandurriao"},
    {"coord": [122.54201, 10.71806], "name": "Q. Abeto Street, Mandurriao"},
    {"coord": [122.53456, 10.71636], "name": "1 De Leon Street, Mandurriao"},
    {"coord": [122.53939, 10.72163], "name": "Mandurriao, Mandurriao"}
]

# Streamlit UI
st.title("Route Visualization")

# Centered Dropdowns for Start and End Points
st.write("### Select Start and End Points")
col1, col2 = st.columns(2, gap="large")

with col1:
    start_name = st.selectbox("Start Point", [None] + [point["name"] for point in coords_with_names], index=0)

with col2:
    end_name = st.selectbox("End Point", [None] + [point["name"] for point in coords_with_names], index=0)

# Initialize map
map_center = [10.71679, 122.55564]  # Center of the map (average location)
m = folium.Map(location=map_center, tiles="CartoDB positron", zoom_start=13)

# Logic to display only start and end points and route when selected
if start_name and end_name:
    if start_name == end_name:
        st.error("Start and end points must be different.")
    else:
        # Get selected coordinates
        start_point = next(point["coord"] for point in coords_with_names if point["name"] == start_name)
        end_point = next(point["coord"] for point in coords_with_names if point["name"] == end_name)

        # Fetch route from OpenRouteService API
        route = client.directions(
            coordinates=[start_point, end_point],
            profile='foot-walking',
            format='geojson'
        )

        # Extract route geometry
        geometry = route['features'][0]['geometry']['coordinates']

        # Add route to the map
        folium.PolyLine(
            locations=[[lat, lon] for lon, lat in geometry],
            color="blue",
            weight=5,
            opacity=0.8
        ).add_to(m)

        # Highlight start and end points
        st.write("#### Green is the starting location and red is the end location")
        folium.Marker(
            location=list(reversed(start_point)),
            popup="Start Point: " + start_name,
            icon=folium.Icon(color="green", icon="play")
        ).add_to(m)

        folium.Marker(
            location=list(reversed(end_point)),
            popup="End Point: " + end_name,
            icon=folium.Icon(color="red", icon="stop")
        ).add_to(m)
else:
    # Add all points as initial markers if no route is selected
    for point in coords_with_names:
        folium.Marker(
            location=list(reversed(point["coord"])),
            popup=point["name"],
            icon=folium.Icon(color="pink")
        ).add_to(m)

# Display the map
st_folium(m, width=700, height=500)
