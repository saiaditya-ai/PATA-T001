import os
import pandas as pd
from typing import Optional, Tuple

class PincodeLocator:
    def __init__(self, csv_path: str):
        """
        Initializes the PincodeLocator and loads the CSV data.
        """
        self.csv_path = csv_path
        self._df = None

    def _load_data(self):
        if self._df is None:
            # We only need specific columns to save memory
            usecols = ['pincode', 'latitude', 'longitude']
            self._df = pd.read_csv(self.csv_path, usecols=usecols)
            # Drop rows with missing latitude or longitude
            self._df.dropna(subset=['latitude', 'longitude'], inplace=True)
            # Convert latitude and longitude to numeric, coercing errors like 'NA' string
            self._df['latitude'] = pd.to_numeric(self._df['latitude'], errors='coerce')
            self._df['longitude'] = pd.to_numeric(self._df['longitude'], errors='coerce')
            self._df.dropna(subset=['latitude', 'longitude'], inplace=True)

    def get_coordinates(self, pincode: str) -> Optional[Tuple[float, float]]:
        """
        Returns the mean latitude and longitude for a given pincode.
        Returns None if the pincode is not found or has no valid coordinates.
        """
        self._load_data()
        
        try:
            pincode_int = int(pincode)
        except ValueError:
            return None

        # Filter for the pincode
        filtered_df = self._df[self._df['pincode'] == pincode_int]
        
        if filtered_df.empty:
            return None
        
        # Calculate the mean latitude and longitude for the pincode
        mean_lat = filtered_df['latitude'].mean()
        mean_lon = filtered_df['longitude'].mean()

        if pd.isna(mean_lat) or pd.isna(mean_lon):
            return None

        return (float(mean_lat), float(mean_lon))

# Instance to be imported
CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'all_india_pincode_directory_2025.csv')
pincode_locator = PincodeLocator(CSV_PATH)
