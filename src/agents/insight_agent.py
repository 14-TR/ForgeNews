#!/usr/bin/env python3
"""
InsightAgent for ForgeNews.
Extracts structured insights from ACLED conflict data.
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from collections import defaultdict
import numpy as np
import glob
from src.scoring.scorer import score_insight, DOMAIN_KEYWORDS
from src.sources.loader import load_registry, get_source

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InsightAgent:
    """Agent for extracting insights from ACLED conflict data."""
    
    def __init__(self,
                 raw_data_dir: str = os.path.join("data", "raw"),
                 processed_data_dir: str = os.path.join("data", "processed")):
        """
        Initialize the InsightAgent.
        
        Args:
            raw_data_dir: Path to the directory containing raw ACLED JSON files.
            processed_data_dir: Path to the directory where processed data will be saved.
        """
        self.raw_data_dir = Path(raw_data_dir)
        self.processed_data_dir = Path(processed_data_dir)
        self.processed_data_path = self.processed_data_dir / "acled_processed.csv"
        self.data = None
        self.insights = {
            "metadata": {
                "generated_at": "",
                "period_start": "",
                "period_end": "",
                "total_events": 0,
                "total_fatalities": 0,
                "countries_covered": []
            },
            "country_profiles": {},
            "event_type_summary": {},
            "actor_profiles": {},
            "hotspots": [],
            "strategic_alerts": [],
            "events": []
        }
        
    def _preprocess_raw_data(self) -> None:
        """Find the latest raw data, preprocess, and save as CSV."""
        try:
            # Find the latest raw conflict JSON file
            list_of_files = glob.glob(str(self.raw_data_dir / 'conflict_*.json'))
            if not list_of_files:
                logger.error(f"No raw conflict JSON files found in {self.raw_data_dir}")
                raise FileNotFoundError(f"No raw conflict JSON files found in {self.raw_data_dir}")

            latest_file = max(list_of_files, key=os.path.getctime)
            logger.info(f"Found latest raw data file: {latest_file}")

            # Load the raw JSON data
            with open(latest_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

            # Extract the 'event' data from each item
            # Handle cases where the structure might be different
            if isinstance(raw_data, list) and raw_data and isinstance(raw_data[0], dict) and 'event' in raw_data[0]:
                 events_data = [item['event'] for item in raw_data if 'event' in item]
            elif isinstance(raw_data, list) and raw_data and isinstance(raw_data[0], dict) and 'event_id_cnty' in raw_data[0]:
                 # Assume it's already a list of events if 'event' key is missing but other keys exist
                 events_data = raw_data
            else:
                 logger.warning(f"Unexpected raw data structure in {latest_file}. Trying direct load.")
                 events_data = raw_data # Fallback

            if not events_data:
                logger.warning(f"No events found in {latest_file}. Processed CSV will be empty.")
                df = pd.DataFrame() # Create empty DataFrame
            else:
                df = pd.DataFrame(events_data)
                # Basic cleaning (ensure essential columns exist, handle potential type issues if needed)
                if 'event_date' in df.columns:
                    df['event_date'] = pd.to_datetime(df['event_date'], errors='coerce')
                if 'fatalities' in df.columns:
                    df['fatalities'] = pd.to_numeric(df['fatalities'], errors='coerce').fillna(0).astype(int)
                else:
                    df['fatalities'] = 0 # Add fatalities column if missing
                # Ensure 'data_id' exists if missing (though ACLED usually has event_id_cnty)
                if 'data_id' not in df.columns and 'event_id_cnty' in df.columns:
                     df['data_id'] = df['event_id_cnty']
                elif 'data_id' not in df.columns:
                     df['data_id'] = df.index # Fallback to index

            # Ensure the processed directory exists
            self.processed_data_dir.mkdir(parents=True, exist_ok=True)

            # Save as CSV
            df.to_csv(self.processed_data_path, index=False)
            logger.info(f"Preprocessed data saved to {self.processed_data_path}")

        except FileNotFoundError:
            # Re-raise FileNotFoundError specifically
             raise
        except Exception as e:
            logger.error(f"Failed during preprocessing: {e}")
            raise RuntimeError(f"Failed during preprocessing: {e}")

    def load_data(self) -> None:
        """Preprocess raw data if needed and load the processed ACLED data."""
        try:
            # Preprocess raw data first
            self._preprocess_raw_data()

            # Now load the processed CSV
            self.data = pd.read_csv(self.processed_data_path)
            # Convert event_date to datetime objects after loading
            if 'event_date' in self.data.columns:
                 self.data['event_date'] = pd.to_datetime(self.data['event_date'], errors='coerce')
            else:
                 logger.warning("Column 'event_date' not found in processed CSV.")

            logger.info(f"Loaded {len(self.data)} events from {self.processed_data_path}")

        except FileNotFoundError:
             logger.error(f"Preprocessing failed: Raw data file not found.")
             # Decide how to handle this: raise error, or proceed with empty data?
             # For now, let's raise to indicate the pipeline dependency failed.
             raise RuntimeError("Preprocessing failed because the required raw data file was not found.")
        except Exception as e:
            logger.error(f"Failed to load or preprocess data: {e}")
            raise
            
    def extract_metadata(self) -> None:
        """Extract metadata from the dataset."""
        if self.data is None:
            logger.error("No data loaded. Call load_data() first.")
            return
            
        # Get date range
        self.data['event_date'] = pd.to_datetime(self.data['event_date'])
        min_date = self.data['event_date'].min()
        max_date = self.data['event_date'].max()
        
        # Calculate basic stats
        total_events = len(self.data)
        total_fatalities = self.data['fatalities'].sum()
        countries = sorted(self.data['country'].unique().tolist())
        
        # Update metadata
        self.insights["metadata"] = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "period_start": min_date.strftime("%Y-%m-%d"),
            "period_end": max_date.strftime("%Y-%m-%d"),
            "total_events": total_events,
            "total_fatalities": int(total_fatalities),
            "countries_covered": countries
        }
        
        logger.info(f"Extracted metadata covering {len(countries)} countries from {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
    
    def extract_country_profiles(self) -> None:
        """Extract country-level insights."""
        if self.data is None:
            logger.error("No data loaded. Call load_data() first.")
            return
            
        country_profiles = {}
        
        # Group by country
        country_groups = self.data.groupby('country')
        
        for country, group in country_groups:
            # Calculate event counts by type
            event_type_counts = group['event_type'].value_counts().to_dict()
            
            # Calculate fatalities
            total_fatalities = int(group['fatalities'].sum())
            fatality_rate = float(total_fatalities / len(group)) if len(group) > 0 else 0
            
            # Identify top actors in this country
            actor1_counts = group['actor1'].value_counts().head(5).to_dict()
            actor2_counts = group['actor2'].value_counts().head(5).to_dict()
            
            # Find top locations
            location_counts = group.groupby('location').agg({
                'data_id': 'count',
                'fatalities': 'sum'
            }).sort_values('data_id', ascending=False).head(5)
            
            top_locations = []
            for location, data in location_counts.iterrows():
                top_locations.append({
                    "location": location,
                    "count": int(data['data_id']),
                    "fatalities": int(data['fatalities'])
                })
            
            # Calculate trend (events in the most recent 1/4 of the date range vs the first 1/4)
            date_range = group['event_date'].max() - group['event_date'].min()
            quarter_range = date_range / 4
            
            if not pd.isna(date_range):
                recent_cutoff = group['event_date'].max() - quarter_range
                early_cutoff = group['event_date'].min() + quarter_range
                
                recent_events = len(group[group['event_date'] >= recent_cutoff])
                early_events = len(group[group['event_date'] <= early_cutoff])
                
                if early_events > 0:
                    trend_factor = (recent_events - early_events) / early_events
                else:
                    trend_factor = 1 if recent_events > 0 else 0
            else:
                trend_factor = 0
                
            # Trend description
            if trend_factor > 0.1:
                trend = "increasing"
            elif trend_factor < -0.1:
                trend = "decreasing"
            else:
                trend = "stable"
            
            # Store country profile
            country_profiles[country] = {
                "events": len(group),
                "fatalities": total_fatalities,
                "fatality_rate": round(fatality_rate, 2),
                "event_types": event_type_counts,
                "top_actors": {
                    "actor1": actor1_counts,
                    "actor2": actor2_counts
                },
                "top_locations": top_locations,
                "trend": trend,
                "trend_factor": round(trend_factor, 2)
            }
        
        self.insights["country_profiles"] = country_profiles
        logger.info(f"Extracted profiles for {len(country_profiles)} countries")
    
    def extract_event_type_summary(self) -> None:
        """Extract insights by event type."""
        if self.data is None:
            logger.error("No data loaded. Call load_data() first.")
            return
        
        event_type_summary = {}
        
        # Group by event type
        event_type_groups = self.data.groupby('event_type')
        
        for event_type, group in event_type_groups:
            # Calculate basic stats
            events_count = len(group)
            fatalities = int(group['fatalities'].sum())
            fatality_rate = float(fatalities / events_count) if events_count > 0 else 0
            
            # Calculate trend
            date_range = group['event_date'].max() - group['event_date'].min()
            quarter_range = date_range / 4
            
            if not pd.isna(date_range):
                recent_cutoff = group['event_date'].max() - quarter_range
                early_cutoff = group['event_date'].min() + quarter_range
                
                recent_events = len(group[group['event_date'] >= recent_cutoff])
                early_events = len(group[group['event_date'] <= early_cutoff])
                
                if early_events > 0:
                    trend_factor = (recent_events - early_events) / early_events
                else:
                    trend_factor = 1 if recent_events > 0 else 0
            else:
                trend_factor = 0
                
            # Trend description
            if trend_factor > 0.1:
                trend = "increasing"
            elif trend_factor < -0.1:
                trend = "decreasing"
            else:
                trend = "stable"
            
            # Top countries for this event type
            country_counts = group['country'].value_counts().head(5).to_dict()
            
            # Store event type profile
            event_type_summary[event_type] = {
                "count": events_count,
                "fatalities": fatalities,
                "fatality_rate": round(fatality_rate, 2),
                "trend": trend,
                "trend_factor": round(trend_factor, 2),
                "top_countries": country_counts
            }
        
        self.insights["event_type_summary"] = event_type_summary
        logger.info(f"Extracted summaries for {len(event_type_summary)} event types")
    
    def extract_actor_profiles(self) -> None:
        """Extract insights about key actors."""
        if self.data is None:
            logger.error("No data loaded. Call load_data() first.")
            return
        
        actor_profiles = {}
        
        # Process both actor1 and actor2
        for actor_col in ['actor1', 'actor2']:
            # Get top actors by event count
            top_actors = self.data[actor_col].value_counts().head(20).index.tolist()
            
            for actor in top_actors:
                # Skip if empty or already processed
                if pd.isna(actor) or actor == '' or actor in actor_profiles:
                    continue
                
                # Get events where this actor appears in either actor column
                actor_events = self.data[(self.data['actor1'] == actor) | (self.data['actor2'] == actor)]
                
                if len(actor_events) < 5:  # Only process significant actors
                    continue
                
                # Calculate basic stats
                events_count = len(actor_events)
                fatalities = int(actor_events['fatalities'].sum())
                fatality_rate = float(fatalities / events_count) if events_count > 0 else 0
                
                # Get countries where active
                countries = actor_events['country'].value_counts().head(5).to_dict()
                
                # Get event types
                event_types = actor_events['event_type'].value_counts().head(5).to_dict()
                
                # Calculate trend
                date_range = actor_events['event_date'].max() - actor_events['event_date'].min()
                quarter_range = date_range / 4
                
                if not pd.isna(date_range):
                    recent_cutoff = actor_events['event_date'].max() - quarter_range
                    early_cutoff = actor_events['event_date'].min() + quarter_range
                    
                    recent_events = len(actor_events[actor_events['event_date'] >= recent_cutoff])
                    early_events = len(actor_events[actor_events['event_date'] <= early_cutoff])
                    
                    if early_events > 0:
                        trend_factor = (recent_events - early_events) / early_events
                    else:
                        trend_factor = 1 if recent_events > 0 else 0
                else:
                    trend_factor = 0
                    
                # Trend description
                if trend_factor > 0.1:
                    trend = "increasing"
                elif trend_factor < -0.1:
                    trend = "decreasing"
                else:
                    trend = "stable"
                
                # Get interactions with other actors
                if actor_col == 'actor1':
                    interactions = actor_events['actor2'].value_counts().head(5).to_dict()
                else:
                    interactions = actor_events['actor1'].value_counts().head(5).to_dict()
                
                # Store actor profile
                actor_profiles[actor] = {
                    "events": events_count,
                    "fatalities": fatalities,
                    "fatality_rate": round(fatality_rate, 2),
                    "countries": countries,
                    "event_types": event_types,
                    "trend": trend,
                    "trend_factor": round(trend_factor, 2),
                    "interactions": interactions
                }
        
        self.insights["actor_profiles"] = actor_profiles
        logger.info(f"Extracted profiles for {len(actor_profiles)} actors")
    
    def identify_hotspots(self) -> None:
        """Identify conflict hotspots based on event concentration and fatalities."""
        if self.data is None:
            logger.error("No data loaded. Call load_data() first.")
            return
        
        # Group by location and country
        location_data = self.data.groupby(['country', 'location']).agg({
            'data_id': 'count',
            'fatalities': 'sum',
            'latitude': 'first',
            'longitude': 'first',
            'event_date': ['min', 'max']
        })
        
        location_data.columns = ['count', 'fatalities', 'latitude', 'longitude', 'first_event', 'last_event']
        
        # Reset index for easier processing
        location_data = location_data.reset_index()
        
        # Filter to locations with at least 5 events or significant fatalities
        significant_locations = location_data[(location_data['count'] >= 5) | (location_data['fatalities'] >= 10)]
        
        # Sort by a combined score of event count and fatalities
        significant_locations['hotspot_score'] = (
            significant_locations['count'] / significant_locations['count'].max() +
            significant_locations['fatalities'] / significant_locations['fatalities'].max()
        )
        
        hotspots = []
        for _, row in significant_locations.sort_values('hotspot_score', ascending=False).head(20).iterrows():
            # Get event types for this location
            location_events = self.data[
                (self.data['country'] == row['country']) & 
                (self.data['location'] == row['location'])
            ]
            
            event_types = location_events['event_type'].value_counts().head(3).to_dict()
            
            # Get recent activity trend
            date_range = row['last_event'] - row['first_event']
            quarter_range = date_range / 4
            
            if not pd.isna(date_range):
                recent_cutoff = row['last_event'] - quarter_range
                
                recent_events = len(location_events[location_events['event_date'] >= recent_cutoff])
                recent_ratio = recent_events / row['count'] if row['count'] > 0 else 0
                
                if recent_ratio > 0.4:
                    trend = "escalating"
                elif recent_ratio < 0.15:
                    trend = "deescalating"
                else:
                    trend = "ongoing"
            else:
                trend = "unknown"
            
            hotspots.append({
                "country": row['country'],
                "location": row['location'],
                "count": int(row['count']),
                "fatalities": int(row['fatalities']),
                "latitude": float(row['latitude']) if not pd.isna(row['latitude']) else None,
                "longitude": float(row['longitude']) if not pd.isna(row['longitude']) else None,
                "event_types": event_types,
                "trend": trend,
                "first_event": row['first_event'].strftime("%Y-%m-%d"),
                "last_event": row['last_event'].strftime("%Y-%m-%d")
            })
        
        self.insights["hotspots"] = hotspots
        logger.info(f"Identified {len(hotspots)} conflict hotspots")
    
    def identify_strategic_alerts(self) -> None:
        """
        Identify strategic alerts and emerging patterns in the conflict data.
        Alerts are based on emerging hotspots, significant trends, and unusual patterns.
        """
        if self.data is None:
            logger.error("No data loaded. Call load_data() first.")
            return
        
        alerts = []
        
        # 1. Look for emerging hotspots - locations with rapid increase in events
        recent_cutoff = self.data['event_date'].max() - pd.Timedelta(days=30)
        
        # Get locations with at least 3 events in the last 30 days
        recent_locations = self.data[self.data['event_date'] >= recent_cutoff].groupby(
            ['country', 'location']
        ).size().reset_index(name='recent_count')
        
        recent_locations = recent_locations[recent_locations['recent_count'] >= 3]
        
        for _, row in recent_locations.iterrows():
            # Check if this is a new or escalating hotspot
            all_events_at_location = self.data[
                (self.data['country'] == row['country']) & 
                (self.data['location'] == row['location'])
            ]
            
            total_events = len(all_events_at_location)
            recent_ratio = row['recent_count'] / total_events
            
            # If most events are recent, it's an emerging hotspot
            if recent_ratio > 0.7 and total_events >= 5:
                # Get event types for context
                event_types = all_events_at_location['event_type'].value_counts().head(2).to_dict()
                event_type_str = ", ".join(event_types.keys())
                
                # Get fatalities
                fatalities = int(all_events_at_location['fatalities'].sum())
                
                alerts.append({
                    "type": "Emerging Hotspot",
                    "severity": "High" if fatalities > 10 else "Medium",
                    "location": {
                        "country": row['country'],
                        "location": row['location']
                    },
                    "description": f"Rapid escalation of conflict in {row['location']}, {row['country']} with {row['recent_count']} recent events ({event_type_str})."
                })
        
        # 2. Look for unusual spikes in fatalities
        country_recent_fatalities = self.data[self.data['event_date'] >= recent_cutoff].groupby(
            'country'
        )['fatalities'].sum().reset_index()
        
        for _, row in country_recent_fatalities.iterrows():
            # Compare to historical averages
            country_data = self.data[self.data['country'] == row['country']]
            
            # Skip if not enough data
            if len(country_data) < 10:
                continue
                
            # Calculate average fatalities per month historically
            date_range_days = (country_data['event_date'].max() - country_data['event_date'].min()).days
            if date_range_days <= 0:
                continue
                
            months = date_range_days / 30
            historical_monthly_avg = country_data['fatalities'].sum() / months
            
            # Recent is for last ~1 month
            recent_monthly = row['fatalities']
            
            # If recent fatalities are significantly higher than historical average
            if recent_monthly > 0 and (recent_monthly / historical_monthly_avg) > 2:
                alerts.append({
                    "type": "Fatality Spike",
                    "severity": "High" if recent_monthly > 50 else "Medium",
                    "location": {
                        "country": row['country']
                    },
                    "description": f"Significant increase in fatalities in {row['country']} with {int(recent_monthly)} fatalities in the last 30 days, compared to historical average of {int(historical_monthly_avg)} per month."
                })
        
        # 3. Look for new conflict actors
        recent_actors = set()
        for col in ['actor1', 'actor2']:
            recent_actors.update(self.data[self.data['event_date'] >= recent_cutoff][col].unique())
        
        older_cutoff = recent_cutoff - pd.Timedelta(days=60)
        older_actors = set()
        for col in ['actor1', 'actor2']:
            older_actors.update(self.data[
                (self.data['event_date'] < recent_cutoff) & 
                (self.data['event_date'] >= older_cutoff)
            ][col].unique())
        
        historical_actors = set()
        for col in ['actor1', 'actor2']:
            historical_actors.update(self.data[self.data['event_date'] < older_cutoff][col].unique())
        
        # New actors are those in recent_actors but not in historical_actors
        new_actors = recent_actors - historical_actors
        new_actors = {actor for actor in new_actors if actor and not pd.isna(actor) and len(str(actor)) > 3}
        
        for actor in new_actors:
            # Get context about this new actor
            actor_events = self.data[(self.data['actor1'] == actor) | (self.data['actor2'] == actor)]
            
            if len(actor_events) < 3:
                continue
                
            countries = actor_events['country'].value_counts().head(2).index.tolist()
            countries_str = ", ".join(countries)
            
            event_types = actor_events['event_type'].value_counts().head(2).index.tolist()
            event_types_str = ", ".join(event_types)
            
            fatalities = int(actor_events['fatalities'].sum())
            
            alerts.append({
                "type": "New Actor",
                "severity": "High" if fatalities > 20 else "Medium",
                "location": {
                    "countries": countries
                },
                "description": f"Emergence of new conflict actor: {actor} in {countries_str}. Associated with {event_types_str} events and {fatalities} fatalities."
            })
        
        # 4. Look for changes in conflict dynamics (e.g., shift from protests to violence)
        for country in self.data['country'].unique():
            country_data = self.data[self.data['country'] == country]
            
            if len(country_data) < 10:
                continue
                
            # Analyze event type distribution over time
            recent_events = country_data[country_data['event_date'] >= recent_cutoff]
            historical_events = country_data[country_data['event_date'] < recent_cutoff]
            
            if len(recent_events) < 5 or len(historical_events) < 5:
                continue
                
            # Compare event type distributions
            recent_types = recent_events['event_type'].value_counts(normalize=True)
            historical_types = historical_events['event_type'].value_counts(normalize=True)
            
            for event_type in recent_types.index:
                if event_type in historical_types:
                    change = recent_types[event_type] - historical_types[event_type]
                    
                    # If there's a significant increase in this event type
                    if change > 0.2:  # 20% shift in distribution
                        alerts.append({
                            "type": "Conflict Dynamic Shift",
                            "severity": "Medium",
                            "location": {
                                "country": country
                            },
                            "description": f"Significant shift toward {event_type} events in {country}. This event type now represents {int(recent_types[event_type]*100)}% of recent events, up from {int(historical_types[event_type]*100)}% historically."
                        })
                elif recent_types[event_type] > 0.25:  # If a new event type represents >25% of recent events
                    alerts.append({
                        "type": "New Conflict Dynamic",
                        "severity": "High",
                        "location": {
                            "country": country
                        },
                        "description": f"Emergence of {event_type} as a significant new conflict dynamic in {country}, representing {int(recent_types[event_type]*100)}% of recent events."
                    })
        
        # Sort alerts by severity
        severity_order = {"High": 0, "Medium": 1, "Low": 2}
        alerts = sorted(alerts, key=lambda x: severity_order.get(x["severity"], 3))
        
        self.insights["strategic_alerts"] = alerts
        logger.info(f"Identified {len(alerts)} strategic alerts")
    
    def extract_event_samples(self) -> None:
        """Extract sample events to include with the insights."""
        if self.data is None:
            logger.error("No data loaded. Call load_data() first.")
            return
        
        # Extract the last 30 days of significant events (with fatalities)
        recent_cutoff = self.data['event_date'].max() - pd.Timedelta(days=30)
        significant_events = self.data[
            (self.data['event_date'] >= recent_cutoff) & 
            (self.data['fatalities'] > 0)
        ].sort_values('fatalities', ascending=False).head(100)
        
        # Also grab some events from each identified hotspot
        hotspot_events = []
        for hotspot in self.insights.get("hotspots", []):
            events = self.data[
                (self.data['country'] == hotspot['country']) & 
                (self.data['location'] == hotspot['location'])
            ].sort_values('event_date', ascending=False).head(5)
            
            hotspot_events.append(events)
        
        if hotspot_events:
            hotspot_events = pd.concat(hotspot_events)
        else:
            hotspot_events = pd.DataFrame()
        
        # Combine and deduplicate events
        selected_events = pd.concat([significant_events, hotspot_events]).drop_duplicates(subset=['data_id'])
        
        # Convert to list of dictionaries
        events_list = []
        for _, row in selected_events.iterrows():
            event_dict = row.to_dict()
            
            # Convert date to string
            if 'event_date' in event_dict and isinstance(event_dict['event_date'], pd.Timestamp):
                event_dict['event_date'] = event_dict['event_date'].strftime("%Y-%m-%d")
            
            # Clean up NaN values
            for key, value in event_dict.items():
                if pd.isna(value):
                    event_dict[key] = None
                elif isinstance(value, (np.int64, np.float64)):
                    event_dict[key] = float(value) if key in ['latitude', 'longitude'] else int(value)
            
            events_list.append(event_dict)
        
        self.insights["events"] = events_list
        logger.info(f"Extracted {len(events_list)} sample events")
    
    def run(self) -> Dict[str, Any]:
        """
        Run the complete insight extraction pipeline and return structured insights.
        
        Returns:
            Dict containing all structured insights
        """
        try:
            # Load data
            self.load_data()
            
            # Extract insights
            self.extract_metadata()
            self.extract_country_profiles()
            self.extract_event_type_summary()
            self.extract_actor_profiles()
            self.identify_hotspots()
            self.identify_strategic_alerts()
            self.extract_event_samples()
            
            # Save insights to file
            self.save_insights()
            
            return self.insights
        except Exception as e:
            logger.error(f"Error running insight extraction: {e}")
            raise
    
    def save_insights(self, output_dir: str = os.path.join("data", "processed", "insights")) -> str:
        """
        Save insights to a JSON file.
        
        Args:
            output_dir: Directory to save insights to
            
        Returns:
            Path to saved insights file
        """
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename based on current time
        filename = f"conflict_insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.insights, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved insights to {filepath}")
        return filepath

def run() -> Dict[str, Any]:
    """
    Run the insight agent to collect insights from all sources.
    
    Returns:
        Dict containing all structured insights
    """
    all_insights = []
    source_registry = load_registry()
    
    # gather raw events from loader
    for dom in ["conflict","ai","markets"]:
        for src_meta in source_registry[dom]:
            mod = get_source(dom, src_meta["id"])
            try:
                raw = mod.normalize(mod.fetch())
                all_insights.extend(raw)
                logger.info(f"Collected {len(raw)} insights from {dom}/{src_meta['id']}")
            except Exception as e:
                logger.error(f"Error processing {dom}/{src_meta['id']}: {e}")
    
    # persist scored insights json -> data/processed/insights_<date>.json
    output_dir = os.path.join("data", "processed", "insights")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename based on current time
    filename = f"insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Save to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(all_insights, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(all_insights)} insights to {filepath}")
    return {"insights": all_insights, "filepath": filepath}

if __name__ == "__main__":
    agent = InsightAgent()
    insights = agent.run() 