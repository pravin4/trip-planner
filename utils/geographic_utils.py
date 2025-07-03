"""
Geographic Utilities for Travel Planning
Handles location clustering, distance calculations, and geographic logic for realistic itineraries.
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class LocationCluster:
    """Represents a cluster of nearby locations"""
    center_lat: float
    center_lng: float
    activities: List[Dict[str, Any]]
    restaurants: List[Dict[str, Any]]
    name: str
    radius_km: float = 5.0  # Default cluster radius

class GeographicUtils:
    """Utilities for geographic calculations and clustering"""
    
    @staticmethod
    def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        Returns distance in kilometers
        """
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    @staticmethod
    def estimate_travel_time(distance_km: float, transport_mode: str = "car") -> int:
        """
        Estimate travel time between locations
        Returns time in minutes
        """
        # Average speeds in km/h
        speeds = {
            "walking": 5,
            "bicycle": 15,
            "car": 30,  # Urban driving
            "public_transit": 20,
            "taxi": 35
        }
        
        speed = speeds.get(transport_mode, 30)
        time_hours = distance_km / speed
        return int(time_hours * 60)  # Convert to minutes
    
    @staticmethod
    def cluster_activities_by_location(activities: List[Dict[str, Any]], 
                                     max_cluster_radius_km: float = 5.0) -> List[LocationCluster]:
        """
        Cluster activities by geographic proximity
        Returns list of LocationCluster objects
        """
        if not activities:
            return []
        
        clusters = []
        used_activities = set()
        
        for activity in activities:
            if activity.get("name") in used_activities:
                continue
                
            # Get activity location
            location = activity.get("location", {})
            if not location or not location.get("latitude") or not location.get("longitude"):
                continue
            
            lat = location["latitude"]
            lng = location["longitude"]
            
            # Check if this activity fits in an existing cluster
            added_to_cluster = False
            for cluster in clusters:
                distance = GeographicUtils.calculate_distance(
                    lat, lng, cluster.center_lat, cluster.center_lng
                )
                
                if distance <= max_cluster_radius_km:
                    cluster.activities.append(activity)
                    used_activities.add(activity.get("name"))
                    added_to_cluster = True
                    break
            
            # If not added to existing cluster, create new one
            if not added_to_cluster:
                new_cluster = LocationCluster(
                    center_lat=lat,
                    center_lng=lng,
                    activities=[activity],
                    restaurants=[],
                    name=f"Area around {activity.get('name', 'Unknown')}",
                    radius_km=max_cluster_radius_km
                )
                clusters.append(new_cluster)
                used_activities.add(activity.get("name"))
        
        # Update cluster centers and names
        for cluster in clusters:
            GeographicUtils._update_cluster_center(cluster)
            GeographicUtils._update_cluster_name(cluster)
        
        return clusters
    
    @staticmethod
    def cluster_restaurants_by_location(restaurants: List[Dict[str, Any]], 
                                      clusters: List[LocationCluster]) -> List[LocationCluster]:
        """
        Assign restaurants to existing activity clusters
        """
        if not restaurants:
            return clusters
        
        for restaurant in restaurants:
            location = restaurant.get("location", {})
            if not location or not location.get("latitude") or not location.get("longitude"):
                continue
            
            lat = location["latitude"]
            lng = location["longitude"]
            
            # Find closest cluster
            closest_cluster = None
            min_distance = float('inf')
            
            for cluster in clusters:
                distance = GeographicUtils.calculate_distance(
                    lat, lng, cluster.center_lat, cluster.center_lng
                )
                
                if distance < min_distance and distance <= cluster.radius_km:
                    min_distance = distance
                    closest_cluster = cluster
            
            if closest_cluster:
                closest_cluster.restaurants.append(restaurant)
        
        return clusters
    
    @staticmethod
    def _update_cluster_center(cluster: LocationCluster):
        """Update cluster center based on all activities"""
        if not cluster.activities:
            return
        
        total_lat = 0
        total_lng = 0
        count = 0
        
        for activity in cluster.activities:
            location = activity.get("location", {})
            if location.get("latitude") and location.get("longitude"):
                total_lat += location["latitude"]
                total_lng += location["longitude"]
                count += 1
        
        if count > 0:
            cluster.center_lat = total_lat / count
            cluster.center_lng = total_lng / count
    
    @staticmethod
    def _update_cluster_name(cluster: LocationCluster):
        """Generate a meaningful name for the cluster"""
        if not cluster.activities:
            return
        
        # Find the most prominent activity
        activities = cluster.activities
        if len(activities) == 1:
            cluster.name = f"Area around {activities[0].get('name', 'Unknown')}"
        else:
            # Use the first activity name and indicate multiple locations
            first_name = activities[0].get('name', 'Unknown')
            cluster.name = f"{first_name} and nearby attractions"
    
    @staticmethod
    def create_geographic_day_plans(clusters: List[LocationCluster], 
                                  num_days: int,
                                  max_activities_per_day: int = 4) -> List[Dict[str, Any]]:
        """
        Create day plans based on geographic clusters
        Ensures each day focuses on one geographic area
        """
        if not clusters:
            return []
        
        day_plans = []
        
        # Sort clusters by number of activities (most interesting first)
        sorted_clusters = sorted(clusters, key=lambda c: len(c.activities), reverse=True)
        
        for day_num in range(num_days):
            if day_num >= len(sorted_clusters):
                # If we have more days than clusters, cycle through clusters
                cluster_idx = day_num % len(sorted_clusters)
                cluster = sorted_clusters[cluster_idx]
            else:
                cluster = sorted_clusters[day_num]
            
            # Select activities for this day (limit to max_activities_per_day)
            day_activities = cluster.activities[:max_activities_per_day]
            
            # Select restaurants for this day (limit to 2-3)
            day_restaurants = cluster.restaurants[:3]
            
            # Calculate total duration
            total_duration = sum(act.get("duration_hours", 2) for act in day_activities)
            
            # Add travel time between activities
            travel_time = GeographicUtils._calculate_cluster_travel_time(day_activities)
            
            day_plan = {
                "day_number": day_num + 1,
                "cluster_name": cluster.name,
                "activities": day_activities,
                "restaurants": day_restaurants,
                "total_duration_hours": total_duration + (travel_time / 60),  # Convert to hours
                "travel_time_minutes": travel_time,
                "geographic_area": {
                    "center_lat": cluster.center_lat,
                    "center_lng": cluster.center_lng,
                    "radius_km": cluster.radius_km
                }
            }
            
            day_plans.append(day_plan)
        
        return day_plans
    
    @staticmethod
    def _calculate_cluster_travel_time(activities: List[Dict[str, Any]]) -> int:
        """Calculate total travel time between activities in a cluster"""
        if len(activities) <= 1:
            return 0
        
        total_travel_time = 0
        
        for i in range(len(activities) - 1):
            loc1 = activities[i].get("location", {})
            loc2 = activities[i + 1].get("location", {})
            
            if (loc1.get("latitude") and loc1.get("longitude") and 
                loc2.get("latitude") and loc2.get("longitude")):
                
                distance = GeographicUtils.calculate_distance(
                    loc1["latitude"], loc1["longitude"],
                    loc2["latitude"], loc2["longitude"]
                )
                
                travel_time = GeographicUtils.estimate_travel_time(distance, "car")
                total_travel_time += travel_time
        
        return total_travel_time
    
    @staticmethod
    def validate_itinerary_geography(day_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate that an itinerary makes geographic sense
        Returns validation results with issues and suggestions
        """
        issues = []
        suggestions = []
        
        for day_plan in day_plans:
            activities = day_plan.get("activities", [])
            
            if len(activities) < 2:
                continue
            
            # Check distances between consecutive activities
            for i in range(len(activities) - 1):
                loc1 = activities[i].get("location", {})
                loc2 = activities[i + 1].get("location", {})
                
                if (loc1.get("latitude") and loc1.get("longitude") and 
                    loc2.get("latitude") and loc2.get("longitude")):
                    
                    distance = GeographicUtils.calculate_distance(
                        loc1["latitude"], loc1["longitude"],
                        loc2["latitude"], loc2["longitude"]
                    )
                    
                    if distance > 20:  # More than 20km between activities
                        issues.append({
                            "type": "large_distance",
                            "day": day_plan.get("day_number"),
                            "activity1": activities[i].get("name"),
                            "activity2": activities[i + 1].get("name"),
                            "distance_km": round(distance, 1)
                        })
                        
                        suggestions.append(
                            f"Consider grouping activities in {day_plan.get('day_number')} "
                            f"by location to reduce travel time"
                        )
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions
        }

    @staticmethod
    def validate_day_plan_geography(day_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that activities in a day plan are geographically realistic.
        
        Args:
            day_plan: Day plan dictionary with activities
            
        Returns:
            Validation results with issues and suggestions
        """
        issues = []
        suggestions = []
        
        activities = day_plan.get("activities", [])
        if len(activities) < 2:
            return {"is_valid": True, "issues": [], "suggestions": []}
        
        # Check distances between all activities
        max_reasonable_distance = 50  # km - maximum reasonable distance for a day
        total_distance = 0
        
        for i in range(len(activities) - 1):
            loc1 = activities[i].get("location", {})
            loc2 = activities[i + 1].get("location", {})
            
            if (loc1.get("latitude") and loc1.get("longitude") and 
                loc2.get("latitude") and loc2.get("longitude")):
                
                distance = GeographicUtils.calculate_distance(
                    loc1["latitude"], loc1["longitude"],
                    loc2["latitude"], loc2["longitude"]
                )
                
                total_distance += distance
                
                if distance > max_reasonable_distance:
                    issues.append({
                        "type": "unrealistic_distance",
                        "activity1": activities[i].get("name", "Unknown"),
                        "activity2": activities[i + 1].get("name", "Unknown"),
                        "distance_km": round(distance, 1)
                    })
                    
                    suggestions.append(
                        f"Activities '{activities[i].get('name', 'Unknown')}' and "
                        f"'{activities[i + 1].get('name', 'Unknown')}' are {round(distance, 1)}km apart. "
                        f"This may not be realistic for a single day."
                    )
        
        # Check if total travel distance is reasonable
        if total_distance > 200:  # More than 200km total travel in a day
            issues.append({
                "type": "excessive_travel",
                "total_distance_km": round(total_distance, 1)
            })
            
            suggestions.append(
                f"Total travel distance of {round(total_distance, 1)}km in one day may be excessive. "
                f"Consider spreading activities across multiple days or focusing on a smaller geographic area."
            )
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "total_distance_km": round(total_distance, 1)
        } 