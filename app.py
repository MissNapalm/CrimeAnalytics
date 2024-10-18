import sqlite3
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template
import os

# Connect to the crimes.db database
conn = sqlite3.connect('crimes.db')

# Query the database for all records containing 'HOMICIDE' in the 'Primary Type'
query = """
SELECT *
FROM crime_data
WHERE "Primary Type" LIKE '%HOMICIDE%'
"""
homicide_df = pd.read_sql(query, conn)

# Close the database connection
conn.close()

# Convert 'Date' column to datetime format
homicide_df['Date'] = pd.to_datetime(homicide_df['Date'], errors='coerce')

# Extract the day of the week and time of day from the 'Date' column
homicide_df['Day of Week'] = homicide_df['Date'].dt.day_name()
homicide_df['Hour'] = homicide_df['Date'].dt.hour

# Convert hour to 12-hour format with AM/PM
homicide_df['Time of Day'] = homicide_df['Date'].dt.strftime('%I:%M %p')

# Create output directory for images if it doesn't exist
output_dir = 'output_images'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Visualization 1: Homicides by Day of the Week
plt.figure(figsize=(10, 6))
homicides_by_day = homicide_df['Day of Week'].value_counts()
sns.barplot(x=homicides_by_day.index, y=homicides_by_day.values, palette='Blues_d')
plt.title('Homicides by Day of the Week', fontsize=18)
plt.xlabel('Day of Week', fontsize=14)
plt.ylabel('Number of Homicides', fontsize=14)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(f'{output_dir}/homicides_by_day_of_week.png')
plt.close()

# Visualization 2: Homicides by Time of Day (Hourly Breakdown)
plt.figure(figsize=(10, 6))
homicides_by_hour = homicide_df['Hour'].value_counts().sort_index()
sns.barplot(x=homicides_by_hour.index, y=homicides_by_hour.values, palette='Greens_d')
plt.title('Homicides by Time of Day (Hourly)', fontsize=18)
plt.xlabel('Hour of the Day', fontsize=14)
plt.ylabel('Number of Homicides', fontsize=14)
plt.xticks(range(0, 24), labels=[f'{i % 12 if i % 12 != 0 else 12} {"AM" if i < 12 else "PM"}' for i in range(24)], rotation=45)
plt.tight_layout()
plt.savefig(f'{output_dir}/homicides_by_time_of_day.png')
plt.close()

# Visualization 3: Homicides by Location on Map (Toggleable Points and Heatmap)

# Filter out rows where lat/lon are missing
homicide_map_df = homicide_df.dropna(subset=['Latitude', 'Longitude'])

# Create a base map centered around the average coordinates
map_center = [homicide_map_df['Latitude'].mean(), homicide_map_df['Longitude'].mean()]
homicide_map = folium.Map(location=map_center, zoom_start=12)

# Add a heatmap layer
heat_data = [[row['Latitude'], row['Longitude']] for index, row in homicide_map_df.iterrows()]
heatmap_layer = folium.FeatureGroup(name='Heatmap')
HeatMap(heat_data).add_to(heatmap_layer)

# Add a layer of points (MarkerCluster)
marker_cluster_layer = folium.FeatureGroup(name='Points')
marker_cluster = MarkerCluster().add_to(marker_cluster_layer)
for idx, row in homicide_map_df.iterrows():
    folium.Marker([row['Latitude'], row['Longitude']], popup=f"Homicide on {row['Date']}, {row['Block']}").add_to(marker_cluster)

# Add both layers to the map with LayerControl for toggling
heatmap_layer.add_to(homicide_map)
marker_cluster_layer.add_to(homicide_map)
folium.LayerControl().add_to(homicide_map)

# Save the map to an HTML file
homicide_map.save('output_images/homicides_map_toggle.html')

# Additional Insights
total_homicides = len(homicide_df)
most_common_day = homicide_df['Day of Week'].value_counts().idxmax()

# HTML template to display results
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Homicide Data Analysis</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; }
        .container { width: 80%; margin: 0 auto; }
        h1, h2 { text-align: center; color: #B22222; }
        .image-container { text-align: center; margin-bottom: 30px; }
        img { width: 80%; max-width: 600px; border: 2px solid #ccc; }
        iframe { width: 100%; height: 500px; border: none; }
        .stats { margin-bottom: 20px; }
        .stat { font-size: 1.2em; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Homicide Data Analysis Report</h1>
        <div class="stats">
            <h2>Key Insights</h2>
            <p class="stat"><strong>Total Homicides:</strong> {{ total_homicides }}</p>
            <p class="stat"><strong>Most Common Day for Homicides:</strong> {{ most_common_day }}</p>
        </div>
        <div class="image-container">
            <h2>Homicides by Day of the Week</h2>
            <img src="output_images/homicides_by_day_of_week.png" alt="Homicides by Day of the Week">
        </div>
        <div class="image-container">
            <h2>Homicides by Time of Day (Hourly)</h2>
            <img src="output_images/homicides_by_time_of_day.png" alt="Homicides by Time of Day">
        </div>
        <div class="image-container">
            <h2>Homicides Locations (Toggleable Points and Heatmap)</h2>
            <iframe src="output_images/homicides_map_toggle.html"></iframe>
        </div>
    </div>
</body>
</html>
"""

# Render the HTML with Jinja2
template = Template(html_template)
html_content = template.render(
    total_homicides=total_homicides,
    most_common_day=most_common_day
)

# Save the HTML report
with open('homicide_report.html', 'w') as file:
    file.write(html_content)

print("Homicide analysis report has been generated and saved as 'homicide_report.html'.")
