import math
import sqlite3
from datetime import datetime, timedelta
import re, textwrap, pathlib, json, os, sys
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
import numpy as np
from collections import defaultdict

# Database setup with enhanced materials
def initialize_database():
    conn = sqlite3.connect('construction_materials.db')
    cursor = conn.cursor()
    
    # Create enhanced materials tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS bricks (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        size TEXT NOT NULL,
                        per_sqm INTEGER NOT NULL,
                        price_per_unit REAL NOT NULL,
                        wastage_percent REAL NOT NULL,
                        compressive_strength_mpa REAL,
                        thermal_conductivity REAL,
                        water_absorption REAL,
                        lifecycle_years INTEGER,
                        embodied_carbon REAL
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS cement_types (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        grade TEXT NOT NULL,
                        bag_weight_kg REAL NOT NULL,
                        price_per_bag REAL NOT NULL,
                        wastage_percent REAL NOT NULL,
                        setting_time_min INTEGER,
                        compressive_strength_mpa REAL,
                        lifecycle_years INTEGER,
                        embodied_carbon REAL
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS steel_rods (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        diameter_mm INTEGER NOT NULL,
                        weight_per_meter_kg REAL NOT NULL,
                        price_per_kg REAL NOT NULL,
                        wastage_percent REAL NOT NULL,
                        yield_strength_mpa REAL,
                        ultimate_strength_mpa REAL,
                        elongation_percent REAL,
                        lifecycle_years INTEGER,
                        embodied_carbon REAL
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS roofing_materials (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        coverage_per_unit_sqm REAL NOT NULL,
                        price_per_unit REAL NOT NULL,
                        wastage_percent REAL NOT NULL,
                        wind_rating_kmh INTEGER,
                        fire_rating TEXT,
                        lifespan_years INTEGER,
                        u_value REAL,
                        r_value REAL,
                        embodied_carbon REAL
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS doors (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        material TEXT NOT NULL,
                        standard_size TEXT NOT NULL,
                        price REAL NOT NULL,
                        thermal_insulation REAL,
                        sound_reduction_db REAL,
                        u_value REAL,
                        lifecycle_years INTEGER
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS windows (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        material TEXT NOT NULL,
                        standard_size TEXT NOT NULL,
                        price REAL NOT NULL,
                        u_value REAL,
                        solar_heat_gain_coeff REAL,
                        lifecycle_years INTEGER
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS insulation_materials (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        thickness_mm REAL NOT NULL,
                        price_per_sqm REAL NOT NULL,
                        thermal_conductivity REAL,
                        r_value REAL,
                        lifecycle_years INTEGER
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS labor_rates (
                        id INTEGER PRIMARY KEY,
                        activity TEXT NOT NULL,
                        rate_per_sqm REAL NOT NULL,
                        unit TEXT NOT NULL,
                        climate_factor REAL DEFAULT 1.0,
                        skill_level TEXT DEFAULT 'Standard',
                        duration_per_unit REAL
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS climate_zones (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        temperature_factor REAL,
                        rainfall_factor REAL,
                        wind_factor REAL,
                        energy_code TEXT
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS seismic_zones (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        zone_factor REAL,
                        importance_factor REAL,
                        response_reduction_factor REAL
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS energy_codes (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        max_u_value_walls REAL,
                        max_u_value_roof REAL,
                        max_u_value_windows REAL,
                        min_r_value_walls REAL,
                        min_r_value_roof REAL
                    )''')
    
    # Insert default data if tables are empty
    if cursor.execute("SELECT COUNT(*) FROM bricks").fetchone()[0] == 0:
        enhanced_bricks = [
            ('Standard Red Brick', '230x110x75 mm', 60, 10, 5, 10.5, 0.8, 15, 50, 0.8),
            ('Hollow Brick', '200x200x150 mm', 12, 25, 3, 7.5, 0.5, 12, 50, 0.6),
            ('Concrete Block', '400x200x200 mm', 12.5, 30, 2, 15.0, 1.2, 8, 60, 1.0),
            ('Engineering Brick', '230x110x75 mm', 60, 15, 4, 50.0, 0.7, 6, 75, 0.9),
            ('Fly Ash Brick', '230x110x75 mm', 60, 12, 4, 12.0, 0.6, 10, 55, 0.5)
        ]
        cursor.executemany("INSERT INTO bricks (name, size, per_sqm, price_per_unit, wastage_percent, compressive_strength_mpa, thermal_conductivity, water_absorption, lifecycle_years, embodied_carbon) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", enhanced_bricks)
    
    if cursor.execute("SELECT COUNT(*) FROM cement_types").fetchone()[0] == 0:
        enhanced_cement = [
            ('OPC 43 Grade', 'Ordinary Portland', '43', 50, 400, 2, 90, 43, 50, 0.9),
            ('OPC 53 Grade', 'Ordinary Portland', '53', 50, 420, 2, 90, 53, 50, 0.9),
            ('PPC', 'Pozzolana', '33', 50, 380, 2, 120, 33, 60, 0.7),
            ('SRC', 'Sulfate Resistant', '33', 50, 450, 2, 90, 33, 60, 1.0),
            ('White Cement', 'Decorative', '43', 50, 600, 3, 90, 43, 50, 1.2)
        ]
        cursor.executemany("INSERT INTO cement_types (name, type, grade, bag_weight_kg, price_per_bag, wastage_percent, setting_time_min, compressive_strength_mpa, lifecycle_years, embodied_carbon) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", enhanced_cement)
    
    if cursor.execute("SELECT COUNT(*) FROM steel_rods").fetchone()[0] == 0:
        enhanced_rods = [
            ('Fe 415', 8, 0.395, 65, 5, 415, 485, 14, 50, 2.5),
            ('Fe 500', 8, 0.395, 70, 5, 500, 545, 12, 50, 2.5),
            ('Fe 550', 8, 0.395, 80, 5, 550, 585, 10, 50, 2.5),
            ('Fe 415', 10, 0.617, 65, 5, 415, 485, 14, 50, 2.5),
            ('Fe 500', 10, 0.617, 70, 5, 500, 545, 12, 50, 2.5),
            ('Fe 550', 10, 0.617, 80, 5, 550, 585, 10, 50, 2.5)
        ]
        cursor.executemany("INSERT INTO steel_rods (name, diameter_mm, weight_per_meter_kg, price_per_kg, wastage_percent, yield_strength_mpa, ultimate_strength_mpa, elongation_percent, lifecycle_years, embodied_carbon) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", enhanced_rods)
    
    if cursor.execute("SELECT COUNT(*) FROM roofing_materials").fetchone()[0] == 0:
        enhanced_roofing = [
            ('Clay Tiles', 'Tile', 0.25, 15, 10, 120, 'Class A', 50, 2.5, 0.4, 0.7),
            ('Concrete Tiles', 'Tile', 0.25, 12, 8, 150, 'Class A', 40, 2.0, 0.5, 1.0),
            ('Metal Sheets', 'Sheet', 1.0, 300, 5, 200, 'Class B', 30, 5.0, 0.2, 1.5),
            ('Asphalt Shingles', 'Shingle', 1.0, 200, 7, 150, 'Class C', 20, 3.0, 0.3, 1.2),
            ('Solar Tiles', 'Special', 0.25, 500, 5, 120, 'Class A', 25, 1.5, 0.25, 0.5)
        ]
        cursor.executemany("INSERT INTO roofing_materials (name, type, coverage_per_unit_sqm, price_per_unit, wastage_percent, wind_rating_kmh, fire_rating, lifespan_years, u_value, r_value, embodied_carbon) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", enhanced_roofing)
    
    if cursor.execute("SELECT COUNT(*) FROM doors").fetchone()[0] == 0:
        enhanced_doors = [
            ('Solid Wood Door', 'Wood', '0.9x2.1m', 5000, 0.8, 30, 3.0, 30),
            ('Hollow Core Door', 'Engineered Wood', '0.9x2.1m', 3000, 0.5, 25, 4.0, 20),
            ('Metal Door', 'Steel', '0.9x2.1m', 6000, 1.2, 35, 5.0, 40),
            ('Fiberglass Door', 'Fiberglass', '0.9x2.1m', 7000, 0.7, 40, 2.5, 30),
            ('Fire-Rated Door', 'Special', '0.9x2.1m', 9000, 1.0, 45, 3.5, 35)
        ]
        cursor.executemany("INSERT INTO doors (name, material, standard_size, price, thermal_insulation, sound_reduction_db, u_value, lifecycle_years) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", enhanced_doors)
    
    if cursor.execute("SELECT COUNT(*) FROM windows").fetchone()[0] == 0:
        enhanced_windows = [
            ('Single Glazed', 'Aluminum', '1.2x1.2m', 4000, 5.8, 0.8, 15),
            ('Double Glazed', 'PVC', '1.2x1.2m', 7000, 2.8, 0.6, 25),
            ('Triple Glazed', 'Wood', '1.2x1.2m', 10000, 1.5, 0.5, 30),
            ('Low-E Glass', 'Special', '1.2x1.2m', 12000, 1.2, 0.4, 25),
            ('Impact Resistant', 'Special', '1.2x1.2m', 15000, 2.0, 0.5, 30)
        ]
        cursor.executemany("INSERT INTO windows (name, material, standard_size, price, u_value, solar_heat_gain_coeff, lifecycle_years) VALUES (?, ?, ?, ?, ?, ?, ?)", enhanced_windows)
    
    if cursor.execute("SELECT COUNT(*) FROM insulation_materials").fetchone()[0] == 0:
        insulation_materials = [
            ('Fiberglass Batt', 'Batt', 100, 50, 0.04, 2.5, 30),
            ('Mineral Wool', 'Batt', 100, 60, 0.035, 2.85, 40),
            ('Cellulose', 'Loose-fill', 100, 45, 0.038, 2.63, 25),
            ('Spray Foam', 'Spray', 50, 80, 0.023, 4.35, 20),
            ('XPS', 'Board', 50, 70, 0.033, 3.03, 50)
        ]
        cursor.executemany("INSERT INTO insulation_materials (name, type, thickness_mm, price_per_sqm, thermal_conductivity, r_value, lifecycle_years) VALUES (?, ?, ?, ?, ?, ?, ?)", insulation_materials)
    
    if cursor.execute("SELECT COUNT(*) FROM labor_rates").fetchone()[0] == 0:
        enhanced_labor = [
            ('Excavation', 50, 'cum', 1.2, 'Standard', 0.5),
            ('Foundation', 300, 'cum', 1.1, 'Skilled', 0.3),
            ('Brickwork', 200, 'sqm', 1.3, 'Skilled', 0.1),
            ('Concreting', 250, 'cum', 1.0, 'Skilled', 0.5),
            ('Plastering', 80, 'sqm', 1.1, 'Standard', 0.15),
            ('Painting', 40, 'sqm', 1.0, 'Standard', 0.1),
            ('Roofing', 150, 'sqm', 1.4, 'Skilled', 0.2),
            ('Plumbing', 5000, 'unit', 1.0, 'Specialized', 0.5),
            ('Electrical', 6000, 'unit', 1.0, 'Specialized', 0.5),
            ('Insulation', 40, 'sqm', 1.0, 'Standard', 0.1)
        ]
        cursor.executemany("INSERT INTO labor_rates (activity, rate_per_sqm, unit, climate_factor, skill_level, duration_per_unit) VALUES (?, ?, ?, ?, ?, ?)", enhanced_labor)
    
    if cursor.execute("SELECT COUNT(*) FROM climate_zones").fetchone()[0] == 0:
        climate_zones = [
            ('Tropical', 'Hot and humid', 1.2, 1.3, 1.1, 'ASHRAE 90.1-2019'),
            ('Arid', 'Hot and dry', 1.3, 0.7, 1.2, 'ASHRAE 90.1-2019'),
            ('Temperate', 'Moderate', 1.0, 1.0, 1.0, 'ASHRAE 90.1-2019'),
            ('Cold', 'Low temperatures', 0.8, 0.9, 1.3, 'ASHRAE 90.1-2019'),
            ('Polar', 'Extreme cold', 0.6, 0.5, 1.5, 'ASHRAE 90.1-2019')
        ]
        cursor.executemany("INSERT INTO climate_zones (name, description, temperature_factor, rainfall_factor, wind_factor, energy_code) VALUES (?, ?, ?, ?, ?, ?)", climate_zones)
    
    if cursor.execute("SELECT COUNT(*) FROM seismic_zones").fetchone()[0] == 0:
        seismic_zones = [
            ('Zone I', 0.10, 1.0, 3.0),
            ('Zone II', 0.16, 1.2, 3.0),
            ('Zone III', 0.24, 1.5, 3.0),
            ('Zone IV', 0.36, 1.5, 3.0),
            ('Zone V', 0.48, 1.5, 3.0)
        ]
        cursor.executemany("INSERT INTO seismic_zones (name, zone_factor, importance_factor, response_reduction_factor) VALUES (?, ?, ?, ?)", seismic_zones)
    
    if cursor.execute("SELECT COUNT(*) FROM energy_codes").fetchone()[0] == 0:
        energy_codes = [
            ('ASHRAE 90.1-2019', 0.57, 0.27, 3.3, 1.75, 3.75),
            ('IECC 2021', 0.51, 0.24, 2.8, 1.96, 4.17),
            ('Passivhaus', 0.15, 0.15, 0.8, 6.67, 6.67),
            ('ECBC 2017', 0.63, 0.33, 3.3, 1.59, 3.03)
        ]
        cursor.executemany("INSERT INTO energy_codes (name, max_u_value_walls, max_u_value_roof, max_u_value_windows, min_r_value_walls, min_r_value_roof) VALUES (?, ?, ?, ?, ?, ?)", energy_codes)
    
    conn.commit()
    conn.close()

# Initialize database
initialize_database()

class ConstructionEstimator:
    def __init__(self):
        self.conn = sqlite3.connect('construction_materials.db')
        self.cursor = self.conn.cursor()
        self.project_details = {}
        self.calculations = {}
        self.summary = {}
        self.timeline_data = {}
        self.cash_flow = {}
        self.cpm_data = {}
        self.alternatives = {}
        self.energy_analysis = {}
        self.structural_design = {}
    
    def get_user_input(self):
        print("\n=== Advanced Construction Material Estimator ===")
        
        # Basic project information
        self.project_details['project_name'] = input("Project Name: ")
        self.project_details['client_name'] = input("Client Name: ")
        self.project_details['location'] = input("Project Location: ")
        self.project_details['date'] = datetime.now().strftime("%Y-%m-%d")
        self.project_details['project_duration_months'] = float(input("Project Duration (months): "))
        self.project_details['interest_rate'] = float(input("Annual Interest Rate (%): ")) / 100
        self.project_details['inflation_rate'] = float(input("Annual Inflation Rate (%): ")) / 100
        
        # Climate zone selection
        print("\nSelect Climate Zone:")
        climate_zones = self.cursor.execute("SELECT id, name, description FROM climate_zones").fetchall()
        for zone in climate_zones:
            print(f"{zone[0]}. {zone[1]} - {zone[2]}")
        climate_choice = int(input("Enter choice (1-{}): ".format(len(climate_zones))))
        self.project_details['climate_zone'] = climate_zones[climate_choice-1][1]
        climate_data = self.cursor.execute(
            "SELECT temperature_factor, rainfall_factor, wind_factor, energy_code FROM climate_zones WHERE id=?", 
            (climate_choice,)).fetchone()
        self.project_details['climate_factors'] = {
            'temperature': climate_data[0],
            'rainfall': climate_data[1],
            'wind': climate_data[2],
            'energy_code': climate_data[3]
        }
        
        # Seismic zone selection
        print("\nSelect Seismic Zone:")
        seismic_zones = self.cursor.execute("SELECT id, name FROM seismic_zones").fetchall()
        for zone in seismic_zones:
            print(f"{zone[0]}. {zone[1]}")
        seismic_choice = int(input("Enter choice (1-{}): ".format(len(seismic_zones))))
        self.project_details['seismic_zone'] = seismic_zones[seismic_choice-1][1]
        seismic_factors = self.cursor.execute(
            "SELECT zone_factor, importance_factor, response_reduction_factor FROM seismic_zones WHERE id=?", 
            (seismic_choice,)).fetchone()
        self.project_details['seismic_factors'] = {
            'zone_factor': seismic_factors[0],
            'importance_factor': seismic_factors[1],
            'response_reduction': seismic_factors[2]
        }
        
        # Construction method selection
        print("\nSelect Construction Method:")
        print("1. RCC Framed Structure")
        print("2. Load Bearing Structure")
        print("3. Steel Framed Structure")
        construction_method = int(input("Enter choice (1-3): "))
        self.project_details['construction_method'] = {
            1: "RCC Framed Structure",
            2: "Load Bearing Structure",
            3: "Steel Framed Structure"
        }[construction_method]
        
        # Room dimensions
        print("\nEnter Room/Floor Dimensions:")
        self.project_details['length'] = float(input("Length (m): "))
        self.project_details['width'] = float(input("Width (m): "))
        self.project_details['height'] = float(input("Height (m): "))
        self.project_details['floors'] = int(input("Number of Floors: "))
        
        # Wall thickness
        self.project_details['wall_thickness'] = float(input("Wall Thickness (m): "))
        
        # Roof type
        print("\nSelect Roof Type:")
        print("1. Flat RCC Roof")
        print("2. Sloped Roof")
        print("3. Dome Roof")
        roof_type = int(input("Enter choice (1-3): "))
        self.project_details['roof_type'] = {
            1: "Flat RCC Roof",
            2: "Sloped Roof",
            3: "Dome Roof"
        }[roof_type]
        
        # Openings
        self.project_details['doors'] = int(input("Number of Doors: "))
        self.project_details['windows'] = int(input("Number of Windows: "))
        
        # Material selections
        print("\nSelect Primary Materials:")
        
        # Brick selection
        print("\nAvailable Brick Types:")
        bricks = self.cursor.execute("SELECT id, name, size, compressive_strength_mpa FROM bricks").fetchall()
        for brick in bricks:
            print(f"{brick[0]}. {brick[1]} ({brick[2]}, {brick[3]} MPa)")
        brick_choice = int(input("Select brick type (1-{}): ".format(len(bricks))))
        self.project_details['brick_type'] = bricks[brick_choice-1][1]
        
        # Cement selection
        print("\nAvailable Cement Types:")
        cements = self.cursor.execute("SELECT id, name, type, grade FROM cement_types").fetchall()
        for cement in cements:
            print(f"{cement[0]}. {cement[1]} ({cement[2]}, Grade {cement[3]})")
        cement_choice = int(input("Select cement type (1-{}): ".format(len(cements))))
        self.project_details['cement_type'] = cements[cement_choice-1][1]
        
        # Steel rod selection
        print("\nAvailable Steel Rod Types:")
        rods = self.cursor.execute("SELECT id, name, diameter_mm, yield_strength_mpa FROM steel_rods").fetchall()
        for rod in rods:
            print(f"{rod[0]}. {rod[1]} ({rod[2]}mm, {rod[3]} MPa)")
        rod_choice = int(input("Select steel rod type (1-{}): ".format(len(rods))))
        self.project_details['steel_rod_type'] = rods[rod_choice-1][1]
        
        # Roofing material selection
        print("\nAvailable Roofing Materials:")
        roofing = self.cursor.execute("SELECT id, name, type, wind_rating_kmh FROM roofing_materials").fetchall()
        for roof in roofing:
            print(f"{roof[0]}. {roof[1]} ({roof[2]}, Wind: {roof[3]} km/h)")
        roofing_choice = int(input("Select roofing material (1-{}): ".format(len(roofing))))
        self.project_details['roofing_material'] = roofing[roofing_choice-1][1]
        
        # Door selection
        print("\nAvailable Door Types:")
        doors = self.cursor.execute("SELECT id, name, material FROM doors").fetchall()
        for door in doors:
            print(f"{door[0]}. {door[1]} ({door[2]})")
        door_choice = int(input("Select door type (1-{}): ".format(len(doors))))
        self.project_details['door_type'] = doors[door_choice-1][1]
        
        # Window selection
        print("\nAvailable Window Types:")
        windows = self.cursor.execute("SELECT id, name, material FROM windows").fetchall()
        for window in windows:
            print(f"{window[0]}. {window[1]} ({window[2]})")
        window_choice = int(input("Select window type (1-{}): ".format(len(windows))))
        self.project_details['window_type'] = windows[window_choice-1][1]
        
        # Insulation selection
        print("\nAvailable Insulation Materials:")
        insulations = self.cursor.execute("SELECT id, name, type, r_value FROM insulation_materials").fetchall()
        for insul in insulations:
            print(f"{insul[0]}. {insul[1]} ({insul[2]}, R-value: {insul[3]})")
        insul_choice = int(input("Select insulation type (1-{}): ".format(len(insulations))))
        self.project_details['insulation_type'] = insulations[insul_choice-1][1]
        
        # Transportation distance
        self.project_details['transport_distance_km'] = float(input("\nTransportation Distance (km): "))
        
        # Structural parameters
        print("\nStructural Design Parameters:")
        self.project_details['footing_depth'] = float(input("Footing Depth (m): "))
        self.project_details['footing_width'] = float(input("Footing Width (m): "))
        self.project_details['column_size'] = input("Column Size (e.g., 0.3x0.3): ")
        self.project_details['beam_size'] = input("Beam Size (e.g., 0.3x0.45): ")
        self.project_details['slab_thickness'] = float(input("Slab Thickness (m): "))
        self.project_details['live_load'] = float(input("Design Live Load (kN/m²): "))
        self.project_details['wind_speed'] = float(input("Design Wind Speed (km/h): "))
        self.project_details['soil_bearing_capacity'] = float(input("Soil Bearing Capacity (kN/m²): "))
        
        # Get material details from database
        self.project_details['brick_details'] = self.cursor.execute(
            "SELECT * FROM bricks WHERE name=?", (self.project_details['brick_type'],)).fetchone()
        self.project_details['cement_details'] = self.cursor.execute(
            "SELECT * FROM cement_types WHERE name=?", (self.project_details['cement_type'],)).fetchone()
        self.project_details['steel_details'] = self.cursor.execute(
            "SELECT * FROM steel_rods WHERE name=?", (self.project_details['steel_rod_type'],)).fetchone()
        self.project_details['roofing_details'] = self.cursor.execute(
            "SELECT * FROM roofing_materials WHERE name=?", (self.project_details['roofing_material'],)).fetchone()
        self.project_details['door_details'] = self.cursor.execute(
            "SELECT * FROM doors WHERE name=?", (self.project_details['door_type'],)).fetchone()
        self.project_details['window_details'] = self.cursor.execute(
            "SELECT * FROM windows WHERE name=?", (self.project_details['window_type'],)).fetchone()
        self.project_details['insulation_details'] = self.cursor.execute(
            "SELECT * FROM insulation_materials WHERE name=?", (self.project_details['insulation_type'],)).fetchone()
        self.project_details['labor_rates'] = self.cursor.execute(
            "SELECT * FROM labor_rates").fetchall()
        
        # Get energy code details
        energy_code_name = self.project_details['climate_factors']['energy_code']
        energy_code_data = self.cursor.execute(
            "SELECT max_u_value_walls, max_u_value_roof, max_u_value_windows, min_r_value_walls, min_r_value_roof FROM energy_codes WHERE name=?", 
            (energy_code_name,)).fetchone()
        
        if energy_code_data:
            self.project_details['energy_code'] = {
                'name': energy_code_name,
                'max_u_value_walls': energy_code_data[0],
                'max_u_value_roof': energy_code_data[1],
                'max_u_value_windows': energy_code_data[2],
                'min_r_value_walls': energy_code_data[3],
                'min_r_value_roof': energy_code_data[4]
            }
        else:
            # Default values if energy code not found
            self.project_details['energy_code'] = {
                'name': "Not specified",
                'max_u_value_walls': 1.0,
                'max_u_value_roof': 1.0,
                'max_u_value_windows': 5.0,
                'min_r_value_walls': 1.0,
                'min_r_value_roof': 1.0
            }
    
    def calculate_wind_load(self, wind_speed, roof_angle=0):
        """Calculate wind load on roof according to ASCE 7 standards"""
        # Basic wind speed conversion to m/s
        V = wind_speed / 3.6  # Convert km/h to m/s
        
        # Exposure factor (assuming Exposure C - open terrain)
        Kz = 0.85
        
        # Topographic factor (assuming flat terrain)
        Kzt = 1.0
        
        # Directionality factor
        Kd = 0.85
        
        # Velocity pressure coefficient
        qz = 0.613 * Kz * Kzt * Kd * V**2
        
        # External pressure coefficient (depends on roof angle)
        if roof_angle == 0:  # Flat roof
            Cp = -0.9  # Uplift pressure
        elif roof_angle < 30:
            Cp = -0.7
        else:
            Cp = -0.5
        
        # Wind load in Pa (N/m²)
        wind_load = qz * Cp
        
        # Convert to kN/m²
        return wind_load / 1000
    
    def calculate_seismic_load(self, zone_factor, importance_factor, response_reduction, building_weight):
        """Calculate seismic base shear using equivalent static force method"""
        # Zone factor (Z)
        Z = zone_factor
        
        # Importance factor (I)
        I = importance_factor
        
        # Response reduction factor (R)
        R = response_reduction
        
        # Average response acceleration coefficient (Sa/g)
        # Assuming medium soil (Type II) and 0.2s period
        Sa_g = 2.5
        
        # Seismic weight (W)
        W = building_weight * 9.81  # Convert to kN
        
        # Design horizontal seismic coefficient (Ah)
        Ah = (Z * I * Sa_g) / (2 * R)
        
        # Base shear (V)
        V = Ah * W
        
        return V
    
    def design_beam(self, span, live_load, dead_load=2.5):
        """Simple beam design for rectangular RCC beams"""
        # Total load (kN/m)
        w = (dead_load + live_load) * span / 2  # Triangular distribution
        
        # Moment (kN-m)
        M = w * span**2 / 10  # Conservative estimate
        
        # Assume M20 concrete and Fe415 steel
        fck = 20  # MPa
        fy = 415   # MPa
        
        # Effective depth (mm)
        d = math.sqrt(M * 10**6 / (0.138 * fck * 300))  # Assuming width=300mm
        
        # Total depth (mm)
        D = d + 50  # Adding cover
        
        # Steel area (mm²)
        Ast = (0.5 * fck * 300 * d / fy) * (1 - math.sqrt(1 - (4.6 * M * 10**6) / (fck * 300 * d**2)))
        
        # Number of bars (assuming 16mm bars)
        num_bars = math.ceil(Ast / 201)  # 201mm² for 16mm bar
        
        return {
            'width': 300,
            'depth': D,
            'steel_bars': f"{num_bars}-16mm bars",
            'stirrups': "8mm @ 150mm c/c",
            'design_moment': M
        }
    
    def design_column(self, axial_load, height):
        """Simple column design for square RCC columns"""
        # Assume M20 concrete and Fe415 steel
        fck = 20  # MPa
        fy = 415   # MPa
        
        # Factored load (1.5 x service load)
        Pu = 1.5 * axial_load * 1000  # kN to N
        
        # Gross area required (mm²)
        Ag = Pu / (0.4 * fck)
        
        # Column size (mm)
        size = math.ceil(math.sqrt(Ag) / 50) * 50  # Round up to nearest 50mm
        
        # Steel area (1% of gross area)
        Ast = 0.01 * size**2
        
        # Number of bars (assuming 16mm bars)
        num_bars = math.ceil(Ast / 201)  # 201mm² for 16mm bar
        
        # Lateral ties
        tie_spacing = min(16 * 16, 300, size)  # 16 x bar diameter or 300mm or column size
        
        return {
            'size': f"{size}x{size} mm",
            'steel_bars': f"{num_bars}-16mm bars",
            'ties': f"8mm @ {tie_spacing}mm c/c",
            'axial_capacity': axial_load
        }
    
    def design_footing(self, column_load, soil_capacity):
        """Simple isolated footing design"""
        # Area required (m²)
        area = column_load / soil_capacity
        
        # Square footing size (m)
        size = math.ceil(math.sqrt(area) * 10) / 10  # Round up to nearest 0.1m
        
        # Depth (conservative estimate)
        depth = max(0.3, size / 5)  # At least 300mm
        
        # Steel area (0.12% of cross-section)
        Ast = 0.0012 * size * depth * 10**6  # mm²
        
        # Bars in each direction (assuming 12mm bars)
        num_bars = math.ceil(Ast / (2 * 113))  # 113mm² for 12mm bar
        
        return {
            'size': f"{size}x{size} m",
            'depth': f"{depth} m",
            'steel_bars': f"{num_bars}-12mm bars each way",
            'soil_pressure': column_load / (size * size)
        }
    
    def calculate_thermal_performance(self):
        """Calculate U-values and R-values for building envelope"""
        if not self.project_details.get('energy_code'):
            return {
                'wall_u_value': 0,
                'wall_r_value': 0,
                'roof_u_value': 0,
                'roof_r_value': 0,
                'window_u_value': 0,
                'door_u_value': 0,
                'wall_compliant': False,
                'roof_compliant': False,
                'window_compliant': False,
                'code_name': "Not specified",
                'code_wall_max': 0,
                'code_roof_max': 0,
                'code_window_max': 0
            }
        
        # Wall construction (brick + plaster)
        brick_conductivity = self.project_details['brick_details'][6]  # W/mK
        brick_thickness = self.project_details['wall_thickness']  # m
        plaster_conductivity = 0.72  # W/mK
        plaster_thickness = 0.02  # m
        
        # Insulation
        insulation_r_value = self.project_details['insulation_details'][6]  # m²K/W
        
        # Wall R-value
        wall_r_value = (brick_thickness / brick_conductivity) + (plaster_thickness / plaster_conductivity) + insulation_r_value
        wall_u_value = 1 / wall_r_value
        
        # Roof U-value (from selected material)
        roof_u_value = self.project_details['roofing_details'][9]
        roof_r_value = self.project_details['roofing_details'][10]
        
        # Window U-value
        window_u_value = self.project_details['window_details'][5]
        
        # Door U-value
        door_u_value = self.project_details['door_details'][7]
        
        # Check against energy code
        code = self.project_details['energy_code']
        wall_compliant = wall_u_value <= code['max_u_value_walls']
        roof_compliant = roof_u_value <= code['max_u_value_roof']
        window_compliant = window_u_value <= code['max_u_value_windows']
        
        return {
            'wall_u_value': wall_u_value,
            'wall_r_value': wall_r_value,
            'roof_u_value': roof_u_value,
            'roof_r_value': roof_r_value,
            'window_u_value': window_u_value,
            'door_u_value': door_u_value,
            'wall_compliant': wall_compliant,
            'roof_compliant': roof_compliant,
            'window_compliant': window_compliant,
            'code_name': code['name'],
            'code_wall_max': code['max_u_value_walls'],
            'code_roof_max': code['max_u_value_roof'],
            'code_window_max': code['max_u_value_windows']
        }
    
    def calculate_lifecycle_cost(self, years=30):
        """Calculate lifecycle costs for major components"""
        # Get lifecycle years for each material
        brick_life = self.project_details['brick_details'][9]
        cement_life = self.project_details['cement_details'][9]
        steel_life = self.project_details['steel_details'][9]
        roof_life = self.project_details['roofing_details'][8]
        door_life = self.project_details['door_details'][7]
        window_life = self.project_details['window_details'][6]
        insul_life = self.project_details['insulation_details'][6]
        
        # Calculate replacement cycles
        brick_replacements = math.floor(years / brick_life)
        cement_replacements = math.floor(years / cement_life)
        steel_replacements = math.floor(years / steel_life)
        roof_replacements = math.floor(years / roof_life)
        door_replacements = math.floor(years / door_life)
        window_replacements = math.floor(years / window_life)
        insul_replacements = math.floor(years / insul_life)
        
        # Initial costs
        initial_cost = self.summary['Total Estimated Cost']
        
        # Replacement costs (present value)
        discount_rate = self.project_details['interest_rate'] - self.project_details['inflation_rate']
        if discount_rate <= 0:
            discount_rate = 0.01  # Minimum 1% real discount rate
        
        def replacement_cost(base_cost, life, years):
            replacements = math.floor(years / life)
            cost = 0
            for i in range(1, replacements + 1):
                cost += base_cost / ((1 + discount_rate) ** (i * life))
            return cost
        
        brick_cost = replacement_cost(
            self.summary['Bricks'] * self.project_details['brick_details'][4],
            brick_life, years)
        
        cement_cost = replacement_cost(
            self.summary['Cement (bags)'] * self.project_details['cement_details'][5],
            cement_life, years)
        
        steel_cost = replacement_cost(
            self.summary['Steel (tons)'] * 1000 * self.project_details['steel_details'][4],
            steel_life, years)
        
        roof_cost = replacement_cost(
            self.summary['Roofing Units'] * self.project_details['roofing_details'][4],
            roof_life, years)
        
        door_cost = replacement_cost(
            self.project_details['door_details'][4] * self.summary['Doors'],
            door_life, years)
        
        window_cost = replacement_cost(
            self.project_details['window_details'][4] * self.summary['Windows'],
            window_life, years)
        
        insul_cost = replacement_cost(
            self.calculations['wall_area'] * self.project_details['insulation_details'][4],
            insul_life, years)
        
        total_lifecycle_cost = initial_cost + brick_cost + cement_cost + steel_cost + roof_cost + door_cost + window_cost + insul_cost
        
        return {
            'initial_cost': initial_cost,
            'brick_replacements': brick_replacements,
            'cement_replacements': cement_replacements,
            'steel_replacements': steel_replacements,
            'roof_replacements': roof_replacements,
            'door_replacements': door_replacements,
            'window_replacements': window_replacements,
            'insul_replacements': insul_replacements,
            'brick_cost': brick_cost,
            'cement_cost': cement_cost,
            'steel_cost': steel_cost,
            'roof_cost': roof_cost,
            'door_cost': door_cost,
            'window_cost': window_cost,
            'insul_cost': insul_cost,
            'total_lifecycle_cost': total_lifecycle_cost,
            'years': years
        }
    
    def generate_alternatives(self):
        """Generate alternative material options with comparisons"""
        alternatives = {}
        
        # Brick alternatives
        brick_alts = self.cursor.execute(
            "SELECT name, price_per_unit, compressive_strength_mpa, thermal_conductivity, lifecycle_years, embodied_carbon FROM bricks WHERE name != ?", 
            (self.project_details['brick_type'],)).fetchall()
        
        # Cement alternatives
        cement_alts = self.cursor.execute(
            "SELECT name, price_per_bag, compressive_strength_mpa, lifecycle_years, embodied_carbon FROM cement_types WHERE name != ?", 
            (self.project_details['cement_type'],)).fetchall()
        
        # Steel alternatives
        steel_alts = self.cursor.execute(
            "SELECT name, price_per_kg, yield_strength_mpa, lifecycle_years, embodied_carbon FROM steel_rods WHERE name != ?", 
            (self.project_details['steel_rod_type'],)).fetchall()
        
        # Roofing alternatives
        roofing_alts = self.cursor.execute(
            "SELECT name, price_per_unit, lifespan_years, u_value, r_value, embodied_carbon FROM roofing_materials WHERE name != ?", 
            (self.project_details['roofing_material'],)).fetchall()
        
        alternatives['bricks'] = brick_alts
        alternatives['cement'] = cement_alts
        alternatives['steel'] = steel_alts
        alternatives['roofing'] = roofing_alts
        
        return alternatives
    
    def value_engineering_suggestions(self):
        """Generate value engineering suggestions based on alternatives"""
        suggestions = []
        
        # Current material costs
        current_brick_cost = self.summary['Bricks'] * self.project_details['brick_details'][4]
        current_cement_cost = self.summary['Cement (bags)'] * self.project_details['cement_details'][5]
        current_steel_cost = self.summary['Steel (tons)'] * 1000 * self.project_details['steel_details'][4]
        current_roof_cost = self.summary['Roofing Units'] * self.project_details['roofing_details'][4]
        
        # Check for cheaper bricks with similar properties
        brick_alts = self.cursor.execute(
            "SELECT name, price_per_unit, compressive_strength_mpa FROM bricks WHERE price_per_unit < ? AND compressive_strength_mpa >= ?", 
            (self.project_details['brick_details'][4], self.project_details['brick_details'][6] * 0.9)).fetchall()
        
        if brick_alts:
            best_brick = min(brick_alts, key=lambda x: x[1])
            savings = (self.project_details['brick_details'][4] - best_brick[1]) * self.summary['Bricks']
            suggestions.append(
                f"Consider using {best_brick[0]} bricks instead (AED{savings:.2f} savings, {best_brick[2]} MPa strength)")
        
        # Check for cement alternatives
        cement_alts = self.cursor.execute(
            "SELECT name, price_per_bag, compressive_strength_mpa FROM cement_types WHERE price_per_bag < ? AND compressive_strength_mpa >= ?", 
            (self.project_details['cement_details'][5], self.project_details['cement_details'][8] * 0.9)).fetchall()
        
        if cement_alts:
            best_cement = min(cement_alts, key=lambda x: x[1])
            savings = (self.project_details['cement_details'][5] - best_cement[1]) * self.summary['Cement (bags)']
            suggestions.append(
                f"Consider using {best_cement[0]} cement instead (AED{savings:.2f} savings, {best_cement[2]} MPa strength)")
        
        # Check for steel alternatives
        steel_alts = self.cursor.execute(
            "SELECT name, price_per_kg, yield_strength_mpa FROM steel_rods WHERE price_per_kg < ? AND yield_strength_mpa >= ?", 
            (self.project_details['steel_details'][4], self.project_details['steel_details'][6] * 0.9)).fetchall()
        
        if steel_alts:
            best_steel = min(steel_alts, key=lambda x: x[1])
            savings = (self.project_details['steel_details'][4] - best_steel[1]) * self.summary['Steel (tons)'] * 1000
            suggestions.append(
                f"Consider using {best_steel[0]} steel instead (AED{savings:.2f} savings, {best_steel[2]} MPa yield strength)")
        
        # Check for roofing alternatives
        roofing_alts = self.cursor.execute(
            "SELECT name, price_per_unit, lifespan_years FROM roofing_materials WHERE price_per_unit < ? AND lifespan_years >= ?", 
            (self.project_details['roofing_details'][4], self.project_details['roofing_details'][8] * 0.8)).fetchall()
        
        if roofing_alts:
            best_roof = min(roofing_alts, key=lambda x: x[1])
            savings = (self.project_details['roofing_details'][4] - best_roof[1]) * self.summary['Roofing Units']
            suggestions.append(
                f"Consider using {best_roof[0]} roofing instead (AED{savings:.2f} savings, {best_roof[2]} year lifespan)")
        
        return suggestions
    
    def calculate_cash_flow(self):
        """Calculate monthly cash flow projections"""
        months = int(self.project_details['project_duration_months'])
        cash_flow = []
        
        # Distribute costs across project duration
        total_cost = self.summary['Total Estimated Cost']
        
        # S-curve distribution (common for construction projects)
        def s_curve(month, total_months):
            x = month / total_months
            return 3 * x**2 - 2 * x**3  # Simple S-curve formula
        
        cumulative_percent = 0
        for month in range(1, months + 1):
            month_percent = s_curve(month, months) - cumulative_percent
            month_amount = total_cost * month_percent
            cumulative_percent += month_percent
            
            cash_flow.append({
                'month': month,
                'amount': month_amount,
                'cumulative': cumulative_percent * total_cost
            })
        
        return cash_flow
    
    def calculate_cpm_schedule(self):
        """Calculate Critical Path Method schedule"""
        activities = [
            {'name': 'Excavation', 'duration': self.timeline_data['Excavation'], 'predecessors': []},
            {'name': 'Foundation', 'duration': self.timeline_data['Foundation'], 'predecessors': ['Excavation']},
            {'name': 'Structure', 'duration': self.timeline_data['Structure'], 'predecessors': ['Foundation']},
            {'name': 'Brickwork', 'duration': self.timeline_data['Brickwork'], 'predecessors': ['Structure']},
            {'name': 'Roofing', 'duration': self.timeline_data['Roofing'], 'predecessors': ['Structure']},
            {'name': 'Finishing', 'duration': self.timeline_data['Finishing'], 'predecessors': ['Brickwork', 'Roofing']}
        ]
        
        # Calculate early start and early finish
        for activity in activities:
            if not activity['predecessors']:
                activity['early_start'] = 0
            else:
                max_predecessor_finish = 0
                for pred in activity['predecessors']:
                    pred_activity = next(a for a in activities if a['name'] == pred)
                    if pred_activity.get('early_finish', 0) > max_predecessor_finish:
                        max_predecessor_finish = pred_activity['early_finish']
                activity['early_start'] = max_predecessor_finish
            activity['early_finish'] = activity['early_start'] + activity['duration']
        
        # Project duration
        project_duration = max(activity['early_finish'] for activity in activities)
        
        # Calculate late start and late finish
        for activity in reversed(activities):
            if activity['name'] == 'Finishing':  # Last activity
                activity['late_finish'] = project_duration
            else:
                successors = [a for a in activities if activity['name'] in a['predecessors']]
                if not successors:
                    activity['late_finish'] = project_duration
                else:
                    min_successor_start = min(s['early_start'] for s in successors)
                    activity['late_finish'] = min_successor_start
            activity['late_start'] = activity['late_finish'] - activity['duration']
        
        # Calculate float
        for activity in activities:
            activity['total_float'] = activity['late_start'] - activity['early_start']
        
        # Identify critical path
        critical_path = [a['name'] for a in activities if a['total_float'] == 0]
        
        return {
            'activities': activities,
            'project_duration': project_duration,
            'critical_path': critical_path
        }
    
    def calculate_materials(self):
        length = self.project_details['length']
        width = self.project_details['width']
        height = self.project_details['height']
        floors = self.project_details['floors']
        wall_thickness = self.project_details['wall_thickness']
        
        # Calculate areas and volumes
        floor_area = length * width
        total_floor_area = floor_area * floors
        
        # Wall calculations
        perimeter = 2 * (length + width)
        wall_area = perimeter * height * floors
        wall_volume = wall_area * wall_thickness
        
        # Footing calculations with soil bearing capacity check
        footing_depth = self.project_details['footing_depth']
        footing_width = self.project_details['footing_width']
        footing_volume = perimeter * footing_depth * footing_width
        
        # Check soil bearing capacity
        building_weight_per_floor = (wall_volume * 20 + floor_area * 12)  # kN (20 kN/m³ for walls, 12 kN/m² for floors)
        total_building_weight = building_weight_per_floor * floors
        footing_area = perimeter * footing_width
        soil_pressure = total_building_weight / footing_area
        
        if soil_pressure > self.project_details['soil_bearing_capacity']:
            print(f"Warning: Soil pressure ({soil_pressure:.2f} kN/m²) exceeds bearing capacity ({self.project_details['soil_bearing_capacity']} kN/m²)")
            # Increase footing width to reduce pressure
            required_footing_width = total_building_weight / (self.project_details['soil_bearing_capacity'] * perimeter)
            print(f"Suggested footing width: {required_footing_width:.2f} m")
            footing_width = required_footing_width
            footing_volume = perimeter * footing_depth * footing_width
        
        # Column calculations
        column_x, column_y = map(float, self.project_details['column_size'].split('x'))
        column_volume = column_x * column_y * height * 4 * floors  # Assuming 4 columns
        
        # Beam calculations
        beam_x, beam_y = map(float, self.project_details['beam_size'].split('x'))
        beam_volume = perimeter * beam_x * beam_y * floors
        
        # Slab calculations
        slab_volume = floor_area * self.project_details['slab_thickness'] * floors
        
        # Total concrete volume
        total_concrete = footing_volume + column_volume + beam_volume + slab_volume
        
        # Brick calculations
        brick_details = self.project_details['brick_details']
        bricks_per_sqm = brick_details[3]
        total_bricks = wall_area * bricks_per_sqm * (1 + brick_details[5]/100)
        
        # Cement calculations (1:2:4 ratio)
        cement_per_cum = 6.5  # bags per cubic meter of concrete
        total_cement_bags = total_concrete * cement_per_cum * (1 + self.project_details['cement_details'][6]/100)
        
        # Sand and aggregate calculations
        sand_per_cum = 0.44  # cubic meters per cubic meter of concrete
        aggregate_per_cum = 0.88  # cubic meters per cubic meter of concrete
        total_sand = total_concrete * sand_per_cum
        total_aggregate = total_concrete * aggregate_per_cum
        
        # Steel calculations with seismic considerations
        if self.project_details['construction_method'] == "RCC Framed Structure":
            # Base steel percentage
            steel_percentage = 1.5  # 1.5% of concrete volume for RCC
            
            # Increase for seismic zones
            seismic_factor = 1 + (self.project_details['seismic_factors']['zone_factor'] / 0.1)
            steel_percentage *= seismic_factor
            
        elif self.project_details['construction_method'] == "Load Bearing Structure":
            steel_percentage = 0.8
        elif self.project_details['construction_method'] == "Steel Framed Structure":
            steel_percentage = 3.0
            
        steel_volume = total_concrete * steel_percentage / 100
        steel_density = 7850  # kg/m3
        total_steel_kg = steel_volume * steel_density * (1 + self.project_details['steel_details'][5]/100)
        
        # Calculate seismic load
        seismic_shear = self.calculate_seismic_load(
            self.project_details['seismic_factors']['zone_factor'],
            self.project_details['seismic_factors']['importance_factor'],
            self.project_details['seismic_factors']['response_reduction'],
            building_weight_per_floor * floors / 9.81  # Convert to tons
        )
        
        # Roofing calculations with wind load check
        roofing_details = self.project_details['roofing_details']
        roofing_units = math.ceil(floor_area / roofing_details[3] * (1 + roofing_details[5]/100))
        
        # Check wind rating
        wind_load = self.calculate_wind_load(self.project_details['wind_speed'])
        if self.project_details['wind_speed'] > roofing_details[6]:
            print(f"Warning: Design wind speed ({self.project_details['wind_speed']} km/h) exceeds roofing material rating ({roofing_details[6]} km/h)")
        
        # Doors and windows
        door_cost = self.project_details['doors'] * self.project_details['door_details'][4]
        window_cost = self.project_details['windows'] * self.project_details['window_details'][4]
        
        # Insulation
        insulation_cost = wall_area * self.project_details['insulation_details'][4]
        
        # Labor calculations with climate factors
        labor_cost = 0
        labor_breakdown = []
        for rate in self.project_details['labor_rates']:
            activity_cost = 0
            if rate[1] == "Excavation":
                activity_cost = footing_volume * rate[2] * rate[4]  # Apply climate factor
            elif rate[1] == "Foundation":
                activity_cost = footing_volume * rate[2] * rate[4]
            elif rate[1] == "Brickwork":
                activity_cost = wall_area * rate[2] * rate[4]
            elif rate[1] == "Concreting":
                activity_cost = total_concrete * rate[2] * rate[4]
            elif rate[1] == "Plastering":
                activity_cost = wall_area * 2 * rate[2] * rate[4]  # Both sides
            elif rate[1] == "Painting":
                activity_cost = wall_area * 2 * rate[2] * rate[4]  # Both sides
            elif rate[1] == "Roofing":
                activity_cost = floor_area * rate[2] * rate[4]
            elif rate[1] == "Plumbing":
                activity_cost = self.project_details['floors'] * rate[2] * rate[4]
            elif rate[1] == "Electrical":
                activity_cost = self.project_details['floors'] * rate[2] * rate[4]
            elif rate[1] == "Insulation":
                activity_cost = wall_area * rate[2] * rate[4]
            
            labor_cost += activity_cost
            labor_breakdown.append((rate[1], activity_cost))
        
        # Transportation cost with climate factors
        transport_cost_per_km = 5  # AED per km per ton
        estimated_weight = (total_cement_bags * self.project_details['cement_details'][4]/1000 + 
                          total_steel_kg/1000 + 
                          total_bricks * 3/1000 +  # approx 3kg per brick
                          total_sand * 1.6 +       # 1.6 ton per cum
                          total_aggregate * 1.5)    # 1.5 ton per cum
        
        # Increase transport cost for adverse climate
        transport_cost = estimated_weight * transport_cost_per_km * self.project_details['transport_distance_km']
        transport_cost *= self.project_details['climate_factors']['temperature']  # Higher cost in extreme climates
        
        # Timeline estimation (in days) with climate factors
        base_timeline = (footing_volume * 0.5 + 
                        wall_area * 0.1 + 
                        total_concrete * 0.5 + 
                        floor_area * 0.2) * floors
        
        # Adjust for climate (slower work in extreme temperatures)
        timeline = base_timeline * self.project_details['climate_factors']['temperature']
        
        # Create timeline breakdown
        self.timeline_data = {
            'Excavation': footing_volume * 0.5 * floors * self.project_details['climate_factors']['temperature'],
            'Foundation': footing_volume * 0.3 * floors * self.project_details['climate_factors']['temperature'],
            'Structure': (column_volume + beam_volume) * 0.4 * floors * self.project_details['climate_factors']['temperature'],
            'Brickwork': wall_area * 0.1 * floors * self.project_details['climate_factors']['temperature'],
            'Roofing': floor_area * 0.2 * floors * self.project_details['climate_factors']['temperature'],
            'Finishing': (wall_area * 0.15 + floor_area * 0.1) * floors * self.project_details['climate_factors']['temperature']
        }
        
        # Structural design calculations
        beam_design = self.design_beam(length, self.project_details['live_load'])
        column_load = building_weight_per_floor * floors / 4  # Assuming 4 columns
        column_design = self.design_column(column_load, height)
        footing_design = self.design_footing(column_load, self.project_details['soil_bearing_capacity'])
        
        # Thermal performance calculations
        thermal_performance = self.calculate_thermal_performance()
        
        # Lifecycle cost analysis
        #lifecycle_cost = self.calculate_lifecycle_cost()
        
        # Alternative materials
        alternatives = self.generate_alternatives()
        
        # Value engineering suggestions
        #ve_suggestions = self.value_engineering_suggestions()
        
        # Cash flow projections
        #cash_flow = self.calculate_cash_flow()
        
        # CPM scheduling
        cpm_schedule = self.calculate_cpm_schedule()
        
        # Store calculations
        self.calculations = {
            'floor_area': floor_area,
            'total_floor_area': total_floor_area,
            'wall_area': wall_area,
            'wall_volume': wall_volume,
            'footing_volume': footing_volume,
            'column_volume': column_volume,
            'beam_volume': beam_volume,
            'slab_volume': slab_volume,
            'total_concrete': total_concrete,
            'total_bricks': total_bricks,
            'total_cement_bags': total_cement_bags,
            'total_sand': total_sand,
            'total_aggregate': total_aggregate,
            'total_steel_kg': total_steel_kg,
            'roofing_units': roofing_units,
            'door_cost': door_cost,
            'window_cost': window_cost,
            'insulation_cost': insulation_cost,
            'labor_cost': labor_cost,
            'labor_breakdown': labor_breakdown,
            'transport_cost': transport_cost,
            'timeline_days': timeline,
            'wind_load': wind_load,
            'seismic_shear': seismic_shear,
            'soil_pressure': soil_pressure,
            'steel_percentage': steel_percentage
        }
        # Embodied Carbon Calculations (in kg CO2e)
        carbon_bricks = self.calculations['total_bricks'] * self.project_details['brick_details'][10]
        # Carbon for cement is: (total bags) * (weight per bag) * (carbon per kg)
        carbon_cement = self.calculations['total_cement_bags'] * self.project_details['cement_details'][4] * self.project_details['cement_details'][10]
        carbon_steel = self.calculations['total_steel_kg'] * self.project_details['steel_details'][10]
        # Carbon for roofing is: (total roof area in sqm) * (carbon per sqm)
        carbon_roofing = self.calculations['floor_area'] * self.project_details['roofing_details'][11]

        total_embodied_carbon = carbon_bricks + carbon_cement + carbon_steel + carbon_roofing
        # Store for internal use in other methods
        self.calculations['total_embodied_carbon_kg'] = total_embodied_carbon
        
        # Store advanced calculations
        self.structural_design = {
            'beam': beam_design,
            'column': column_design,
            'footing': footing_design
        }
        
        self.energy_analysis = thermal_performance
        #self.lifecycle_cost = lifecycle_cost
        self.alternatives = alternatives
        #self.ve_suggestions = ve_suggestions
        #self.cash_flow = cash_flow
        self.cpm_data = cpm_schedule

        # Calculate total estimated cost
        total_estimated_cost = (
            total_cement_bags * self.project_details['cement_details'][5] +
            total_steel_kg * self.project_details['steel_details'][4] / 1000 +
            total_bricks * self.project_details['brick_details'][4] +
            roofing_units * self.project_details['roofing_details'][4] +
            door_cost +
            window_cost +
            insulation_cost +
            labor_cost +
            transport_cost
        )
        
        # Create summary
        self.summary = {
            #'Cement (bags)': round(total_cement_bags, 2),
            #'Steel (tons)': round(total_steel_kg / 1000, 2),
            #'Bricks': round(total_bricks),
            #'Sand (cubic meters)': round(total_sand, 2),
            #'Aggregate (cubic meters)': round(total_aggregate, 2),
            #'Roofing Units': roofing_units,
            #'Doors': self.project_details['doors'],
            #'Windows': self.project_details['windows'],
            #'Construction Time (days)': round(timeline),
            #'Wind Load (kN/m²)': round(wind_load, 3),
            #'Seismic Base Shear (kN)': round(seismic_shear, 2),
            #'Soil Pressure (kN/m²)': round(soil_pressure, 2),
            #'Total Estimated Cost': round(total_estimated_cost, 2)

            'Cement (bags)': round(total_cement_bags, 2),
            'Steel (tons)': round(total_steel_kg / 1000, 2),
            'Bricks': round(total_bricks),
            'Sand (cubic meters)': round(total_sand, 2),
            'Aggregate (cubic meters)': round(total_aggregate, 2),
            'Roofing Units': roofing_units,
            'Doors': self.project_details['doors'],
            'Windows': self.project_details['windows'],
            'Construction Time (days)': round(timeline),
            'Wind Load (kN/m²)': round(wind_load, 3),
            'Seismic Base Shear (kN)': round(seismic_shear, 2),
            'Soil Pressure (kN/m²)': round(soil_pressure, 2),
            'Total Embodied Carbon (kg CO2e)': round(total_embodied_carbon, 2),
            'Total Estimated Cost': round(total_estimated_cost, 2)
        }
        # ✅ Now it is safe to call this
        lifecycle_cost = self.calculate_lifecycle_cost()
        ve_suggestions  = self.value_engineering_suggestions()
        cash_flow       = self.calculate_cash_flow()
        # Store additional results
        self.lifecycle_cost = lifecycle_cost
        self.ve_suggestions = ve_suggestions
        self.cash_flow      = cash_flow
    
    def generate_timeline_chart(self):
        activities = list(self.timeline_data.keys())
        durations = list(self.timeline_data.values())
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(activities, durations, color='skyblue')
        
        ax.set_xlabel('Duration (days)')
        ax.set_title('Construction Timeline Estimation')
        ax.invert_yaxis()  # Show top activity first
        
        # Add duration labels
        for bar in bars:
            width = bar.get_width()
            ax.text(width + max(durations)*0.02, bar.get_y() + bar.get_height()/2,
                   f'{width:.1f} days',
                   va='center')
        
        plt.tight_layout()
        
        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150)
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    def generate_cash_flow_chart(self):
        months = [cf['month'] for cf in self.cash_flow]
        amounts = [cf['amount'] for cf in self.cash_flow]
        cumulative = [cf['cumulative'] for cf in self.cash_flow]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(months, amounts, color='lightblue', label='Monthly Cost')
        ax.plot(months, cumulative, 'r-', marker='o', label='Cumulative Cost')
        
        ax.set_xlabel('Month')
        ax.set_ylabel('Amount (AED)')
        ax.set_title('Project Cash Flow Projection')
        ax.legend()
        ax.grid(True)
        
        plt.tight_layout()
        
        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150)
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    def generate_cpm_chart(self):
        activities = self.cpm_data['activities']
        
        # Create Gantt chart
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for i, activity in enumerate(activities):
            # Actual duration bar
            ax.barh(activity['name'], activity['duration'], 
                    left=activity['early_start'], 
                    color='skyblue', edgecolor='black')
            
            # Float time (if any)
            if activity['total_float'] > 0:
                ax.barh(activity['name'], activity['total_float'], 
                        left=activity['early_finish'], 
                        color='lightgray', edgecolor='black', alpha=0.5)
        
        ax.set_xlabel('Days')
        ax.set_title('Critical Path Method Schedule')
        ax.grid(True)
        
        plt.tight_layout()
        
        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150)
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    def generate_pdf_report(self):
        filename = f"Construction_Estimate_{self.project_details['project_name'].replace(' ', '_')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=1,
            spaceAfter=20
        )
        
        heading_style = ParagraphStyle(
            'Heading2',
            parent=styles['Heading2'],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6
        )
        
        subheading_style = ParagraphStyle(
            'Heading3',
            parent=styles['Heading3'],
            fontSize=10,
            spaceBefore=6,
            spaceAfter=3
        )
        
        normal_style = styles['Normal']
        bold_style = ParagraphStyle(
            'Bold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold'
        )
        
        # Content
        content = []
        
        # Title
        content.append(Paragraph("ADVANCED CONSTRUCTION ESTIMATE REPORT", title_style))
        
        # Project details
        content.append(Paragraph("Project Details", heading_style))
        
        project_data = [
            ["Project Name:", self.project_details['project_name']],
            ["Client Name:", self.project_details['client_name']],
            ["Location:", self.project_details['location']],
            ["Date:", self.project_details['date']],
            ["Construction Method:", self.project_details['construction_method']],
            ["Climate Zone:", f"{self.project_details['climate_zone']} (Temp Factor: {self.project_details['climate_factors']['temperature']:.1f})"],
            ["Seismic Zone:", f"{self.project_details['seismic_zone']} (Zone Factor: {self.project_details['seismic_factors']['zone_factor']})"],
            ["Roof Type:", self.project_details['roof_type']],
            ["Design Wind Speed:", f"{self.project_details['wind_speed']} km/h"],
            ["Soil Bearing Capacity:", f"{self.project_details['soil_bearing_capacity']} kN/m²"],
            ["Project Duration:", f"{self.project_details['project_duration_months']} months"]
        ]
        
        project_table = Table(project_data, colWidths=[2*inch, 4*inch])
        project_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        content.append(project_table)
        content.append(Spacer(1, 12))
        
        # Dimensions
        content.append(Paragraph("Building Dimensions and Loads", heading_style))
        
        dim_data = [
            ["Length:", f"{self.project_details['length']} m"],
            ["Width:", f"{self.project_details['width']} m"],
            ["Height:", f"{self.project_details['height']} m"],
            ["Floors:", str(self.project_details['floors'])],
            ["Wall Thickness:", f"{self.project_details['wall_thickness']} m"],
            ["Footing Depth:", f"{self.project_details['footing_depth']} m"],
            ["Footing Width:", f"{self.project_details['footing_width']} m"],
            ["Column Size:", self.project_details['column_size'] + " m"],
            ["Beam Size:", self.project_details['beam_size'] + " m"],
            ["Slab Thickness:", f"{self.project_details['slab_thickness']} m"],
            ["Live Load:", f"{self.project_details['live_load']} kN/m²"],
            ["Calculated Wind Load:", f"{self.calculations['wind_load']:.3f} kN/m²"],
            ["Calculated Seismic Shear:", f"{self.calculations['seismic_shear']:.2f} kN"],
            ["Soil Pressure:", f"{self.calculations['soil_pressure']:.2f} kN/m²"]
        ]
        
        dim_table = Table(dim_data, colWidths=[2*inch, 1*inch])
        dim_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        
        content.append(dim_table)
        content.append(Spacer(1, 12))
        
        # Selected materials with enhanced properties
        content.append(Paragraph("Selected Materials with Specifications", heading_style))
        
        mat_data = [
            ["Brick Type:", f"{self.project_details['brick_type']}",
             f"Comp. Strength: {self.project_details['brick_details'][6]} MPa, Water Abs: {self.project_details['brick_details'][8]}%"],
            ["Cement Type:", f"{self.project_details['cement_type']}",
             f"Grade: {self.project_details['cement_details'][3]}, Setting Time: {self.project_details['cement_details'][7]} min"],
            ["Steel Rod Type:", f"{self.project_details['steel_rod_type']}",
             f"Yield Strength: {self.project_details['steel_details'][6]} MPa, Elongation: {self.project_details['steel_details'][8]}%"],
            ["Roofing Material:", f"{self.project_details['roofing_material']}",
             f"Wind Rating: {self.project_details['roofing_details'][6]} km/h, Fire Rating: {self.project_details['roofing_details'][7]}"],
            ["Door Type:", f"{self.project_details['door_type']}",
             f"Sound Reduction: {self.project_details['door_details'][6]} dB"],
            ["Window Type:", f"{self.project_details['window_type']}",
             f"U-Value: {self.project_details['window_details'][5]}, SHGC: {self.project_details['window_details'][6]}"],
            ["Insulation Type:", f"{self.project_details['insulation_type']}",
             f"R-Value: {self.project_details['insulation_details'][6]} m²K/W"]
        ]
        
        mat_table = Table(mat_data, colWidths=[1.5*inch, 1.5*inch, 3*inch])
        mat_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        
        content.append(mat_table)
        content.append(Spacer(1, 12))
        
        # Add timeline chart
        content.append(Paragraph("Construction Timeline Estimation", heading_style))
        timeline_img = self.generate_timeline_chart()
        content.append(Image(timeline_img, width=6*inch, height=3.5*inch))
        content.append(Spacer(1, 12))
        
        # Add CPM chart
        content.append(Paragraph("Critical Path Method Schedule", heading_style))
        cpm_img = self.generate_cpm_chart()
        content.append(Image(cpm_img, width=6*inch, height=3.5*inch))
        content.append(Spacer(1, 12))
        
        # Add cash flow chart
        content.append(Paragraph("Cash Flow Projection", heading_style))
        cashflow_img = self.generate_cash_flow_chart()
        content.append(Image(cashflow_img, width=6*inch, height=3.5*inch))
        content.append(Spacer(1, 12))
        
        # Structural design
        content.append(Paragraph("Structural Design Summary", heading_style))
        
        # Beam design
        content.append(Paragraph("Beam Design", subheading_style))
        beam_data = [
            ["Design Parameter", "Value"],
            ["Width", f"{self.structural_design['beam']['width']} mm"],
            ["Depth", f"{self.structural_design['beam']['depth']} mm"],
            ["Steel Reinforcement", self.structural_design['beam']['steel_bars']],
            ["Stirrups", self.structural_design['beam']['stirrups']],
            ["Design Moment", f"{self.structural_design['beam']['design_moment']:.2f} kN-m"]
        ]
        beam_table = Table(beam_data, colWidths=[2*inch, 2*inch])
        beam_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        content.append(beam_table)
        content.append(Spacer(1, 6))
        
        # Column design
        content.append(Paragraph("Column Design", subheading_style))
        column_data = [
            ["Design Parameter", "Value"],
            ["Size", self.structural_design['column']['size']],
            ["Steel Reinforcement", self.structural_design['column']['steel_bars']],
            ["Lateral Ties", self.structural_design['column']['ties']],
            ["Axial Capacity", f"{self.structural_design['column']['axial_capacity']:.2f} kN"]
        ]
        column_table = Table(column_data, colWidths=[2*inch, 2*inch])
        column_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        content.append(column_table)
        content.append(Spacer(1, 6))
        
        # Footing design
        content.append(Paragraph("Footing Design", subheading_style))
        footing_data = [
            ["Design Parameter", "Value"],
            ["Size", self.structural_design['footing']['size']],
            ["Depth", self.structural_design['footing']['depth']],
            ["Steel Reinforcement", self.structural_design['footing']['steel_bars']],
            ["Soil Pressure", f"{self.structural_design['footing']['soil_pressure']:.2f} kN/m²"]
        ]
        footing_table = Table(footing_data, colWidths=[2*inch, 2*inch])
        footing_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        content.append(footing_table)
        content.append(Spacer(1, 12))
        
        # Thermal performance
        content.append(Paragraph("Thermal Performance Analysis", heading_style))
        
        thermal_data = [
            ["Component", "U-Value (W/m²K)", "R-Value (m²K/W)", "Code Compliance"],
            ["Wall", f"{self.energy_analysis['wall_u_value']:.3f}", 
             f"{self.energy_analysis['wall_r_value']:.2f}", 
             "Compliant" if self.energy_analysis['wall_compliant'] else "Not Compliant"],
            ["Roof", f"{self.energy_analysis['roof_u_value']:.3f}", 
             f"{self.energy_analysis['roof_r_value']:.2f}", 
             "Compliant" if self.energy_analysis['roof_compliant'] else "Not Compliant"],
            ["Window", f"{self.energy_analysis['window_u_value']:.3f}", 
             "-", 
             "Compliant" if self.energy_analysis['window_compliant'] else "Not Compliant"],
            ["Door", f"{self.energy_analysis['door_u_value']:.3f}", 
             "-", "-"],
            ["", "", "", ""],
            ["Energy Code:", self.energy_analysis['code_name'], "", ""],
            ["Max Wall U-Value:", f"{self.energy_analysis['code_wall_max']} W/m²K", "", ""],
            ["Max Roof U-Value:", f"{self.energy_analysis['code_roof_max']} W/m²K", "", ""],
            ["Max Window U-Value:", f"{self.energy_analysis['code_window_max']} W/m²K", "", ""]
        ]
        
        thermal_table = Table(thermal_data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 1.5*inch])
        thermal_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BACKGROUND', (0, 5), (-1, 5), colors.lightgrey),
        ]))
        content.append(thermal_table)
        content.append(Spacer(1, 12))
        
        # Lifecycle cost analysis
        content.append(Paragraph(f"Lifecycle Cost Analysis ({self.lifecycle_cost['years']} years)", heading_style))
        
        lifecycle_data = [
            ["Component", "Initial Cost", "Replacements", "Replacement Cost", "Lifecycle Cost"],
            ["Bricks", 
             f"{self.summary['Bricks'] * self.project_details['brick_details'][4]:.2f}", 
             self.lifecycle_cost['brick_replacements'], 
             f"{self.lifecycle_cost['brick_cost']:.2f}", 
             f"{self.summary['Bricks'] * self.project_details['brick_details'][4] + self.lifecycle_cost['brick_cost']:.2f}"],
            ["Cement", 
             f"{self.summary['Cement (bags)'] * self.project_details['cement_details'][5]:.2f}", 
             self.lifecycle_cost['cement_replacements'], 
             f"{self.lifecycle_cost['cement_cost']:.2f}", 
             f"{self.summary['Cement (bags)'] * self.project_details['cement_details'][5] + self.lifecycle_cost['cement_cost']:.2f}"],
            ["Steel", 
             f"{self.summary['Steel (tons)'] * 1000 * self.project_details['steel_details'][4]:.2f}", 
             self.lifecycle_cost['steel_replacements'], 
             f"{self.lifecycle_cost['steel_cost']:.2f}", 
             f"{self.summary['Steel (tons)'] * 1000 * self.project_details['steel_details'][4] + self.lifecycle_cost['steel_cost']:.2f}"],
            ["Roofing", 
             f"{self.summary['Roofing Units'] * self.project_details['roofing_details'][4]:.2f}", 
             self.lifecycle_cost['roof_replacements'], 
             f"{self.lifecycle_cost['roof_cost']:.2f}", 
             f"{self.summary['Roofing Units'] * self.project_details['roofing_details'][4] + self.lifecycle_cost['roof_cost']:.2f}"],
            ["Doors", 
             f"{self.project_details['door_details'][4] * self.summary['Doors']:.2f}", 
             self.lifecycle_cost['door_replacements'], 
             f"{self.lifecycle_cost['door_cost']:.2f}", 
             f"{self.project_details['door_details'][4] * self.summary['Doors'] + self.lifecycle_cost['door_cost']:.2f}"],
            ["Windows", 
             f"{self.project_details['window_details'][4] * self.summary['Windows']:.2f}", 
             self.lifecycle_cost['window_replacements'], 
             f"{self.lifecycle_cost['window_cost']:.2f}", 
             f"{self.project_details['window_details'][4] * self.summary['Windows'] + self.lifecycle_cost['window_cost']:.2f}"],
            ["Insulation", 
             f"{self.calculations['wall_area'] * self.project_details['insulation_details'][4]:.2f}", 
             self.lifecycle_cost['insul_replacements'], 
             f"{self.lifecycle_cost['insul_cost']:.2f}", 
             f"{self.calculations['wall_area'] * self.project_details['insulation_details'][4] + self.lifecycle_cost['insul_cost']:.2f}"],
            ["", "", "", "", ""],
            ["Total", 
             f"{self.lifecycle_cost['initial_cost']:.2f}", 
             "-", 
             f"{sum([self.lifecycle_cost['brick_cost'], self.lifecycle_cost['cement_cost'], self.lifecycle_cost['steel_cost'], self.lifecycle_cost['roof_cost'], self.lifecycle_cost['door_cost'], self.lifecycle_cost['window_cost'], self.lifecycle_cost['insul_cost']]):.2f}", 
             f"{self.lifecycle_cost['total_lifecycle_cost']:.2f}"]
        ]
        
        lifecycle_table = Table(lifecycle_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        lifecycle_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BACKGROUND', (0, 7), (-1, 7), colors.lightgrey),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ]))
        content.append(lifecycle_table)
        content.append(Spacer(1, 12))
        
        # Value engineering suggestions
        if self.ve_suggestions:
            content.append(Paragraph("Value Engineering Suggestions", heading_style))
            for suggestion in self.ve_suggestions:
                content.append(Paragraph(f"• {suggestion}", normal_style))
                content.append(Spacer(1, 4))
            content.append(Spacer(1, 12))
        
        # Material calculations
        content.append(Paragraph("Material Calculations with Engineering Formulas", heading_style))
        
        calc_data = [
            ["Item", "Quantity", "Unit", "Formula Used"],
            ["Total Floor Area", f"{self.calculations['total_floor_area']:.2f}", "sqm", "Length × Width × Floors"],
            ["Wall Area", f"{self.calculations['wall_area']:.2f}", "sqm", "Perimeter × Height × Floors"],
            ["Total Concrete", f"{self.calculations['total_concrete']:.2f}", "cum", "Footing + Columns + Beams + Slab"],
            ["Total Bricks", f"{self.calculations['total_bricks']:.0f}", "units", f"Wall Area × {self.project_details['brick_details'][3]} bricks/sqm + {self.project_details['brick_details'][5]}% wastage"],
            ["Total Cement", f"{self.calculations['total_cement_bags']:.2f}", "bags", f"6.5 bags/cum × Total Concrete + {self.project_details['cement_details'][6]}% wastage"],
            ["Total Steel", f"{self.calculations['total_steel_kg']/1000:.2f}", "tons", 
             f"{self.calculations['total_concrete']:.2f} cum × {self.calculations['steel_percentage']}% × 7850 kg/m³ + {self.project_details['steel_details'][5]}% wastage"],
            ["Wind Load", f"{self.calculations['wind_load']:.3f}", "kN/m²", 
             "ASCE 7: qz = 0.613×Kz×Kzt×Kd×V²; Cp based on roof angle"],
            ["Seismic Shear", f"{self.calculations['seismic_shear']:.2f}", "kN", 
             f"IS 1893: V = (Z×I×Sa)/(2×R) × W; Z={self.project_details['seismic_factors']['zone_factor']}, R={self.project_details['seismic_factors']['response_reduction']}"],
            ["Beam Design Moment", f"{self.structural_design['beam']['design_moment']:.2f}", "kN-m", 
             f"w = (DL+LL)×span/2; M = w×span²/10; DL={2.5} kN/m², LL={self.project_details['live_load']} kN/m²"]
        ]
        
        calc_table = Table(calc_data, colWidths=[1.5*inch, 1*inch, 0.8*inch, 4*inch])
        calc_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (3, 0), (3, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        
        content.append(calc_table)
        content.append(Spacer(1, 12))
        
        # Summary
        content.append(Paragraph("Summary Estimate", heading_style))
        
        summary_data = [
            ["Item", "Quantity", "Unit", "Total Cost"],
            ["Cement", f"{self.summary['Cement (bags)']:.0f}", "bags", 
             f"{self.summary['Cement (bags)'] * self.project_details['cement_details'][5]:.2f}"],
            ["Steel", f"{self.summary['Steel (tons)']:.2f}", "tons", 
             f"{self.summary['Steel (tons)'] * 1000 * self.project_details['steel_details'][4]:.2f}"],
            ["Bricks", f"{self.summary['Bricks']:.0f}", "units", 
             f"{self.summary['Bricks'] * self.project_details['brick_details'][4]:.2f}"],
            ["Roofing", f"{self.summary['Roofing Units']}", "units", 
             f"{self.summary['Roofing Units'] * self.project_details['roofing_details'][4]:.2f}"],
            ["Doors", f"{self.summary['Doors']}", "units", f"{self.project_details['door_details'][4] * self.summary['Doors']:.2f}"],
            ["Windows", f"{self.summary['Windows']}", "units", f"{self.project_details['window_details'][4] * self.summary['Windows']:.2f}"],
            ["Insulation", "-", "-", f"{self.calculations['insulation_cost']:.2f}"],
            ["Labor", "-", "-", f"{self.calculations['labor_cost']:.2f}"],
            ["Transport", "-", "-", f"{self.calculations['transport_cost']:.2f}"],
            ["Embodied Carbon", f"{self.calculations['total_embodied_carbon_kg']:.0f}", "kg CO2e", ""],
            ["", "", "TOTAL:", f"{self.summary['Total Estimated Cost']:.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[1.5*inch, 1*inch, 0.8*inch, 1.2*inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BACKGROUND', (0, -1), (-2, -1), colors.lightgrey),
            ('BACKGROUND', (-1, -1), (-1, -1), colors.lightblue),
            ('FONTNAME', (-1, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        content.append(summary_table)
        content.append(Spacer(1, 12))
        
        # Labor breakdown
        content.append(Paragraph("Labor Cost Breakdown", heading_style))
        
        labor_data = [["Activity", "Cost"]] + self.calculations['labor_breakdown']
        labor_table = Table(labor_data, colWidths=[4*inch, 1.5*inch])
        labor_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        
        content.append(labor_table)
        content.append(Spacer(1, 12))
        
        # Cash flow details
        content.append(Paragraph("Cash Flow Projection Details", heading_style))
        
        cashflow_data = [["Month", "Amount", "Cumulative"]]
        for cf in self.cash_flow:
            cashflow_data.append([
                str(cf['month']),
                f"{cf['amount']:.2f}",
                f"{cf['cumulative']:.2f}"
            ])
        
        cashflow_table = Table(cashflow_data, colWidths=[1*inch, 2*inch, 2*inch])
        cashflow_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        
        content.append(cashflow_table)
        content.append(Spacer(1, 12))
        
        # CPM details
        content.append(Paragraph("Critical Path Method Details", heading_style))
        
        cpm_data = [["Activity", "Duration", "Early Start", "Early Finish", "Late Start", "Late Finish", "Total Float"]]
        for activity in self.cpm_data['activities']:
            cpm_data.append([
                activity['name'],
                f"{activity['duration']:.1f}",
                f"{activity['early_start']:.1f}",
                f"{activity['early_finish']:.1f}",
                f"{activity['late_start']:.1f}",
                f"{activity['late_finish']:.1f}",
                f"{activity['total_float']:.1f}"
            ])
        
        cpm_table = Table(cpm_data, colWidths=[1.3*inch] + [0.9*inch]*6)
        cpm_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        
        content.append(cpm_table)
        content.append(Paragraph(f"Critical Path: {' → '.join(self.cpm_data['critical_path'])}", normal_style))
        content.append(Paragraph(f"Total Project Duration: {self.cpm_data['project_duration']:.1f} days", normal_style))
        content.append(Spacer(1, 12))
        
        # Alternative materials
        content.append(Paragraph("Alternative Material Options", heading_style))
        
        # Brick alternatives
        content.append(Paragraph("Brick Alternatives", subheading_style))
        brick_alt_data = [["Type", "Price/Unit", "Strength (MPa)", "Thermal Conductivity", "Lifecycle (years)", "Embodied Carbon"]]
        for alt in self.alternatives['bricks']:
            brick_alt_data.append([
                alt[0],                       # name
                f"{alt[1]:.2f}",              # price_per_unit
                f"{alt[2]:.1f}",              # compressive_strength_mpa
                f"{alt[3]:.3f}",              # thermal_conductivity
                str(alt[4]),                  # lifecycle_years
                f"{alt[5]:.2f}"               # embodied_carbon
                ])
        
        brick_alt_table = Table(brick_alt_data, colWidths=[1.5*inch] + [1.2*inch]*5)
        brick_alt_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        content.append(brick_alt_table)
        content.append(Spacer(1, 6))
        
        # Cement alternatives
        content.append(Paragraph("Cement Alternatives", subheading_style))
        cement_alt_data = [["Type", "Price/Bag", "Strength (MPa)", "Lifecycle (years)", "Embodied Carbon"]]
        for alt in self.alternatives['cement']:
            cement_alt_data.append([
                alt[0],                       # name
                f"{alt[1]:.2f}",              # price_per_bag
                f"{alt[2]:.1f}",              # strength
                str(alt[3]),                  # lifecycle_years
                f"{alt[4]:.2f}"               # embodied_carbon
                ])
        
        cement_alt_table = Table(cement_alt_data, colWidths=[1.5*inch] + [1.2*inch]*4)
        cement_alt_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        content.append(cement_alt_table)
        content.append(Spacer(1, 6))
        
        # Steel alternatives
        content.append(Paragraph("Steel Alternatives", subheading_style))
        steel_alt_data = [["Type", "Price/kg", "Yield Strength (MPa)", "Lifecycle (years)", "Embodied Carbon"]]
        for alt in self.alternatives['steel']:
            steel_alt_data.append([
                alt[0],                       # name
                f"{alt[1]:.2f}",              # price_per_kg
                f"{alt[2]:.1f}",              # yield_strength
                str(alt[3]),                  # lifecycle_years
                f"{alt[4]:.2f}"               # embodied_carbon
                ])
        
        steel_alt_table = Table(steel_alt_data, colWidths=[1.5*inch] + [1.2*inch]*4)
        steel_alt_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        content.append(steel_alt_table)
        content.append(Spacer(1, 6))
        
        # Roofing alternatives
        content.append(Paragraph("Roofing Alternatives", subheading_style))
        roof_alt_data = [["Type", "Price/Unit", "Lifespan (years)", "U-Value", "R-Value", "Embodied Carbon"]]
        for alt in self.alternatives['roofing']:
            roof_alt_data.append([
                alt[0],                       # name
                f"{alt[1]:.2f}",              # price_per_unit
                str(alt[2]),                  # lifespan_years
                f"{alt[3]:.3f}",              # u_value
                f"{alt[4]:.2f}",              # r_value
                f"{alt[5]:.2f}"               # embodied_carbon
                ])
        
        roof_alt_table = Table(roof_alt_data, colWidths=[1.5*inch] + [1.2*inch]*5)
        roof_alt_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        content.append(roof_alt_table)
        content.append(Spacer(1, 12))
        
        # Notes
        content.append(Paragraph("Engineering Notes:", heading_style))
        notes = [
            "1. All quantities include standard wastage percentages for each material type.",
            "2. Wind load calculated according to ASCE 7 standards using velocity pressure method.",
            "3. Seismic load calculated using equivalent static force method per IS 1893.",
            "4. Steel percentage adjusted for seismic zone factor and construction method.",
            "5. Timeline estimates include climate factor adjustments for productivity.",
            "6. All structural calculations should be verified by a licensed engineer.",
            "7. Material specifications are based on manufacturer data and standard codes.",
            "8. Lifecycle costs are calculated using net present value method with discount rate.",
            "9. Energy code compliance is based on selected climate zone requirements."
        ]
        
        for note in notes:
            content.append(Paragraph(note, normal_style))
            content.append(Spacer(1, 4))
        
        # Build the PDF
        doc.build(content)
        print(f"\nAdvanced report generated successfully: {filename}")
    
    def display_summary(self):
        print("\n=== ADVANCED CONSTRUCTION ESTIMATE SUMMARY ===")
        print(f"Project: {self.project_details['project_name']}")
        print(f"Construction Method: {self.project_details['construction_method']}")
        print(f"Climate Zone: {self.project_details['climate_zone']}")
        print(f"Seismic Zone: {self.project_details['seismic_zone']}")
        print(f"Total Floor Area: {self.calculations['total_floor_area']:.2f} sqm")
        
        print("\nKey Engineering Parameters:")
        print(f"- Wind Load: {self.calculations['wind_load']:.3f} kN/m²")
        print(f"- Seismic Base Shear: {self.calculations['seismic_shear']:.2f} kN")
        print(f"- Soil Pressure: {self.calculations['soil_pressure']:.2f} kN/m²")
        print(f"- Total Embodied Carbon: {self.calculations['total_embodied_carbon_kg']:.2f} kg CO2e")
        
        print("\nMaterials Required:")
        print(f"- Cement: {self.summary['Cement (bags)']:.0f} bags ({self.project_details['cement_type']})")
        print(f"- Steel: {self.summary['Steel (tons)']:.2f} tons ({self.project_details['steel_rod_type']})")
        print(f"- Bricks: {self.summary['Bricks']:.0f} ({self.project_details['brick_type']})")
        print(f"- Roofing: {self.summary['Roofing Units']} units ({self.project_details['roofing_material']})")
        
        print("\nStructural Design:")
        print(f"- Beam: {self.structural_design['beam']['width']}x{self.structural_design['beam']['depth']}mm with {self.structural_design['beam']['steel_bars']}")
        print(f"- Column: {self.structural_design['column']['size']} with {self.structural_design['column']['steel_bars']}")
        print(f"- Footing: {self.structural_design['footing']['size']} with {self.structural_design['footing']['steel_bars']}")
        
        print("\nThermal Performance:")
        print(f"- Wall U-value: {self.energy_analysis['wall_u_value']:.3f} W/m²K (Code max: {self.energy_analysis['code_wall_max']})")
        print(f"- Roof U-value: {self.energy_analysis['roof_u_value']:.3f} W/m²K (Code max: {self.energy_analysis['code_roof_max']})")
        print(f"- Window U-value: {self.energy_analysis['window_u_value']:.3f} W/m²K (Code max: {self.energy_analysis['code_window_max']})")
        
        print("\nEstimated Construction Time:")
        for activity, days in self.timeline_data.items():
            print(f"- {activity}: {days:.1f} days")
        
        print(f"\nCritical Path: {' → '.join(self.cpm_data['critical_path'])}")
        print(f"Total Project Duration: {self.cpm_data['project_duration']:.1f} days")
        
        print(f"\nTotal Estimated Cost: {self.summary['Total Estimated Cost']:.2f}")
        print(f"30-Year Lifecycle Cost: {self.lifecycle_cost['total_lifecycle_cost']:.2f}")
        
        if self.ve_suggestions:
            print("\nValue Engineering Suggestions:")
            for suggestion in self.ve_suggestions:
                print(f"- {suggestion}")

# Main program
if __name__ == "__main__":
    estimator = ConstructionEstimator()
    estimator.get_user_input()
    estimator.calculate_materials()
    estimator.display_summary()
    estimator.generate_pdf_report()
