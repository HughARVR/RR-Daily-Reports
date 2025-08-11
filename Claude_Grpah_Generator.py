# -*- coding: utf-8 -*-
"""
Created on Fri Aug  1 13:35:18 2025

@author: OEM
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template, FileSystemLoader, Environment
from datetime import datetime
import os
import mysql.connector as mysql

HOST = "192.168.1.82" # or "domain.com"
# database name, if you want just to connect to MySQL server, leave it empty
DATABASE = "RR_Data"
# this is the user you create
USER = "operations"
# user password
PASSWORD = "rUm3n@ut!"
# connect to MySQL server
print("Hello")
db_connection = mysql.connect(host=HOST, database=DATABASE, user=USER, password=PASSWORD)
print("Connected to:", db_connection.server_info)
# enter your code here!


query = """
select SystemID, timestamp, reactor_temperature
from temperature_data
where timestamp >= NOW() - INTERVAL 24 HOUR
order by timestamp desc;
"""
df = pd.read_sql(query, db_connection)

df['Herd_Number'] = df.apply(lambda row : (row.SystemID - 1) // 10 + 1, axis = 1)


def herd_status(n):
    if n == 1:
       return 'A'
    elif n == 2:
        return 'B'
    elif n == 3:
        return 'C'
    elif n == 4:
        return 'D'
    else:
        return 'Undefined'

df['Herd'] = df['Herd_Number'].map(herd_status)

df['RR_Name'] = df['Herd'] + ((df['SystemID'] - 1) % 10 + 1).astype(str)

def create_graphs_and_report(df, output_dir='output'):
    """
    Generate graphs for each SystemID and create HTML report
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(f'{output_dir}/graphs', exist_ok=True)
    
    # Get unique system IDs
    system_ids = df['SystemID'].unique()
    
    # Sort numerically if possible
    try:
        system_ids = sorted(system_ids, key=lambda x: int(x))
    except ValueError:
        # If conversion to int fails, sort as strings
        system_ids = sorted(system_ids)
    # Prepare data for template
    systems_data = []
    
    for system_id in system_ids:
        # Filter data for this system
        system_df = df[df['SystemID'] == system_id].copy()
        system_name = system_df['RR_Name'].iloc[0]
        
        # Create graph
        plt.figure(figsize=(10, 6))
        plt.plot(system_df['timestamp'], system_df['reactor_temperature'], linewidth=2)
        plt.xlabel('Time')
        plt.ylabel('Temperature (°C)')
        plt.title(f'Temperature vs Time - {system_name}')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save graph
        graph_filename = f'system_{system_id}_temperature.png'
        graph_path = f'{output_dir}/graphs/{graph_filename}'
        plt.savefig(graph_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Calculate statistics
        stats = {
            'mean': system_df['reactor_temperature'].mean(),
            'max': system_df['reactor_temperature'].max(),
            'min': system_df['reactor_temperature'].min(),
            'count': len(system_df)
        }
        
        # Add to systems data
        systems_data.append({
            'id': system_id,
            'name': system_name,
            'graph_path': f'graphs/{graph_filename}',  # Relative path for HTML
            'stats': stats
        })
    
    # Load and render template
    with open('Claude_report_template.html', 'r') as f:
        template_content = f.read()
    
    template = Template(template_content)
    
    # Render the template
    html_content = template.render(
        report_title='RR Temperature Analysis Report',
        generation_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        systems=systems_data
    )
    
    # Save HTML report
    with open(f'{output_dir}/temperature_report.html', 'w') as f:
        f.write(html_content)
    
    print(f"Report generated: {output_dir}/temperature_report.html")
    print(f"Graphs saved in: {output_dir}/graphs/")

# Usage example:
# Assuming you have your DataFrame 'df' with columns: timestamp, systemID, temperature
create_graphs_and_report(df)