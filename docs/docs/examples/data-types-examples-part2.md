# SurrealDB Python SDK Data Types Examples - Part 2

This is the continuation of comprehensive real-world examples for SurrealDB Python SDK data types.

## DateTime Examples (Continued)

### Example 2: Audit Log System (Continued)

```python
from surrealdb.data.types.datetime import IsoDateTimeWrapper
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, List

class AuditAction(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS = "access"

class AuditLogger:
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
        self.session_logs: Dict[str, List[Dict[str, Any]]] = {}
    
    def log_action(self, user_id: str, action: AuditAction, resource: str, 
                  details: Dict[str, Any] = None, session_id: str = None):
        """Log an audit action with timestamp"""
        timestamp = IsoDateTimeWrapper(datetime.now(timezone.utc).isoformat())
        
        log_entry = {
            "timestamp": timestamp,
            "user_id": user_id,
            "action": action.value,
            "resource": resource,
            "details": details or {},
            "session_id": session_id
        }
        
        self.logs.append(log_entry)
        
        # Also track by session if provided
        if session_id:
            if session_id not in self.session_logs:
                self.session_logs[session_id] = []
            self.session_logs[session_id].append(log_entry)
        
        return log_entry
    
    def get_user_activity(self, user_id: str, start_date: datetime = None, 
                         end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get user activity within date range"""
        user_logs = [log for log in self.logs if log["user_id"] == user_id]
        
        if start_date or end_date:
            filtered_logs = []
            start_iso = start_date.isoformat() if start_date else None
            end_iso = end_date.isoformat() if end_date else None
            
            for log in user_logs:
                log_time = log["timestamp"].dt
                
                if start_iso and log_time < start_iso:
                    continue
                if end_iso and log_time > end_iso:
                    continue
                
                filtered_logs.append(log)
            
            return filtered_logs
        
        return user_logs
    
    def get_session_activity(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all activity for a session"""
        return self.session_logs.get(session_id, [])
    
    def generate_activity_report(self, user_id: str, days_back: int = 7) -> Dict[str, Any]:
        """Generate activity report for user"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        activities = self.get_user_activity(user_id, start_date, end_date)
        
        # Count actions by type
        action_counts = {}
        for activity in activities:
            action = activity["action"]
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            "user_id": user_id,
            "period_start": IsoDateTimeWrapper(start_date.isoformat()),
            "period_end": IsoDateTimeWrapper(end_date.isoformat()),
            "total_activities": len(activities),
            "action_breakdown": action_counts,
            "activities": activities
        }

# Usage
audit_logger = AuditLogger()

# Simulate user activities
session_id = "session_abc123"
user_id = "user_001"

# Log various activities
audit_logger.log_action(user_id, AuditAction.LOGIN, "system", 
                       {"ip_address": "192.168.1.100"}, session_id)

audit_logger.log_action(user_id, AuditAction.ACCESS, "dashboard", 
                       {"page": "main_dashboard"}, session_id)

audit_logger.log_action(user_id, AuditAction.CREATE, "users", 
                       {"new_user_id": "user_002", "role": "editor"}, session_id)

audit_logger.log_action(user_id, AuditAction.UPDATE, "users", 
                       {"updated_user_id": "user_002", "field": "email"}, session_id)

audit_logger.log_action(user_id, AuditAction.ACCESS, "reports", 
                       {"report_type": "monthly_summary"}, session_id)

audit_logger.log_action(user_id, AuditAction.LOGOUT, "system", 
                       {"session_duration": "45m"}, session_id)

# Generate activity report
report = audit_logger.generate_activity_report(user_id, days_back=1)
print("📊 User Activity Report:")
print(f"User: {report['user_id']}")
print(f"Period: {report['period_start'].dt} to {report['period_end'].dt}")
print(f"Total Activities: {report['total_activities']}")
print("Action Breakdown:")
for action, count in report['action_breakdown'].items():
    print(f"  {action}: {count}")

# Get session-specific activity
session_activity = audit_logger.get_session_activity(session_id)
print(f"\n🔍 Session {session_id} Activity:")
for activity in session_activity:
    print(f"  {activity['timestamp'].dt}: {activity['action']} on {activity['resource']}")
```

### Example 3: Time Series Data Management

```python
from surrealdb.data.types.datetime import IsoDateTimeWrapper
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import statistics

class TimeSeriesManager:
    def __init__(self):
        self.data_points: Dict[str, List[Dict[str, Any]]] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
    
    def create_series(self, series_id: str, description: str, unit: str = None):
        """Create a new time series"""
        self.data_points[series_id] = []
        self.metadata[series_id] = {
            "description": description,
            "unit": unit,
            "created_at": IsoDateTimeWrapper(datetime.now(timezone.utc).isoformat()),
            "last_updated": None,
            "data_point_count": 0
        }
    
    def add_data_point(self, series_id: str, value: float, timestamp: datetime = None):
        """Add a data point to a time series"""
        if series_id not in self.data_points:
            raise ValueError(f"Series {series_id} does not exist")
        
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        elif timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        data_point = {
            "timestamp": IsoDateTimeWrapper(timestamp.isoformat()),
            "value": value
        }
        
        self.data_points[series_id].append(data_point)
        
        # Update metadata
        self.metadata[series_id]["last_updated"] = IsoDateTimeWrapper(
            datetime.now(timezone.utc).isoformat()
        )
        self.metadata[series_id]["data_point_count"] += 1
    
    def get_data_range(self, series_id: str, start_time: datetime, 
                      end_time: datetime) -> List[Dict[str, Any]]:
        """Get data points within a time range"""
        if series_id not in self.data_points:
            return []
        
        start_iso = start_time.isoformat()
        end_iso = end_time.isoformat()
        
        filtered_points = []
        for point in self.data_points[series_id]:
            point_time = point["timestamp"].dt
            if start_iso <= point_time <= end_iso:
                filtered_points.append(point)
        
        return filtered_points
    
    def calculate_statistics(self, series_id: str, hours_back: int = 24) -> Dict[str, Any]:
        """Calculate statistics for recent data"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours_back)
        
        data_points = self.get_data_range(series_id, start_time, end_time)
        
        if not data_points:
            return {"error": "No data points in range"}
        
        values = [point["value"] for point in data_points]
        
        return {
            "series_id": series_id,
            "period_start": IsoDateTimeWrapper(start_time.isoformat()),
            "period_end": IsoDateTimeWrapper(end_time.isoformat()),
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0
        }
    
    def downsample_data(self, series_id: str, interval_minutes: int, 
                       hours_back: int = 24) -> List[Dict[str, Any]]:
        """Downsample data to reduce granularity"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours_back)
        
        data_points = self.get_data_range(series_id, start_time, end_time)
        
        if not data_points:
            return []
        
        # Group data points by interval
        interval_delta = timedelta(minutes=interval_minutes)
        downsampled = []
        
        current_interval_start = start_time
        while current_interval_start < end_time:
            interval_end = current_interval_start + interval_delta
            
            # Get points in this interval
            interval_points = []
            for point in data_points:
                point_time_str = point["timestamp"].dt
                point_time = datetime.fromisoformat(point_time_str.replace('Z', '+00:00'))
                
                if current_interval_start <= point_time < interval_end:
                    interval_points.append(point)
            
            if interval_points:
                values = [p["value"] for p in interval_points]
                downsampled.append({
                    "timestamp": IsoDateTimeWrapper(current_interval_start.isoformat()),
                    "value": statistics.mean(values),
                    "count": len(values),
                    "min": min(values),
                    "max": max(values)
                })
            
            current_interval_start = interval_end
        
        return downsampled

# Usage
ts_manager = TimeSeriesManager()

# Create time series for different metrics
ts_manager.create_series("cpu_usage", "CPU Usage Percentage", "%")
ts_manager.create_series("memory_usage", "Memory Usage", "MB")
ts_manager.create_series("response_time", "API Response Time", "ms")

# Simulate adding data points over time
import random

base_time = datetime.now(timezone.utc) - timedelta(hours=2)

# Add CPU usage data
for i in range(120):  # 2 hours of data, every minute
    timestamp = base_time + timedelta(minutes=i)
    cpu_value = 20 + random.uniform(-5, 15) + (i * 0.1)  # Trending upward
    ts_manager.add_data_point("cpu_usage", cpu_value, timestamp)

# Add memory usage data
for i in range(120):
    timestamp = base_time + timedelta(minutes=i)
    memory_value = 1024 + random.uniform(-100, 200)
    ts_manager.add_data_point("memory_usage", memory_value, timestamp)

# Add response time data
for i in range(120):
    timestamp = base_time + timedelta(minutes=i)
    response_time = 150 + random.uniform(-50, 100)
    ts_manager.add_data_point("response_time", response_time, timestamp)

# Calculate statistics
for series_id in ["cpu_usage", "memory_usage", "response_time"]:
    stats = ts_manager.calculate_statistics(series_id, hours_back=2)
    print(f"\n📈 Statistics for {series_id}:")
    for key, value in stats.items():
        if key.startswith("period_"):
            print(f"  {key}: {value.dt}")
        else:
            print(f"  {key}: {value}")

# Downsample CPU data to 15-minute intervals
downsampled = ts_manager.downsample_data("cpu_usage", interval_minutes=15, hours_back=2)
print(f"\n📊 Downsampled CPU data (15-minute intervals):")
for point in downsampled[:5]:  # Show first 5 intervals
    print(f"  {point['timestamp'].dt}: avg={point['value']:.2f}%, "
          f"min={point['min']:.2f}%, max={point['max']:.2f}%, count={point['count']}")
```

## Geometry Examples

The geometry classes represent various geometric shapes for spatial data operations.

### Example 1: Location-Based Service

```python
from surrealdb.data.types.geometry import (
    GeometryPoint, GeometryLine, GeometryPolygon, 
    GeometryMultiPoint, GeometryCollection
)
import math
from typing import List, Tuple

class LocationService:
    def __init__(self):
        self.locations = {}
        self.routes = {}
        self.zones = {}
    
    def add_location(self, location_id: str, name: str, longitude: float, latitude: float):
        """Add a point location"""
        point = GeometryPoint(longitude, latitude)
        self.locations[location_id] = {
            "name": name,
            "geometry": point,
            "type": "point"
        }
        return point
    
    def create_route(self, route_id: str, name: str, waypoints: List[Tuple[float, float]]):
        """Create a route from multiple waypoints"""
        points = [GeometryPoint(lon, lat) for lon, lat in waypoints]
        route_line = GeometryLine(*points)
        
        self.routes[route_id] = {
            "name": name,
            "geometry": route_line,
            "type": "route",
            "waypoint_count": len(waypoints)
        }
        return route_line
    
    def create_zone(self, zone_id: str, name: str, boundaries: List[List[Tuple[float, float]]]):
        """Create a polygonal zone"""
        lines = []
        for boundary in boundaries:
            points = [GeometryPoint(lon, lat) for lon, lat in boundary]
            line = GeometryLine(*points)
            lines.append(line)
        
        zone_polygon = GeometryPolygon(*lines)
        
        self.zones[zone_id] = {
            "name": name,
            "geometry": zone_polygon,
            "type": "zone",
            "boundary_count": len(boundaries)
        }
        return zone_polygon
    
    def calculate_distance(self, point1: GeometryPoint, point2: GeometryPoint) -> float:
        """Calculate distance between two points using Haversine formula"""
        lon1, lat1 = point1.get_coordinates()
        lon2, lat2 = point2.get_coordinates()
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        return c * r
    
    def find_nearby_locations(self, center_point: GeometryPoint, 
                            radius_km: float) -> List[Tuple[str, dict, float]]:
        """Find locations within radius of center point"""
        nearby = []
        
        for location_id, location_data in self.locations.items():
            location_point = location_data["geometry"]
            distance = self.calculate_distance(center_point, location_point)
            
            if distance <= radius_km:
                nearby.append((location_id, location_data, distance))
        
        # Sort by distance
        nearby.sort(key=lambda x: x[2])
        return nearby
    
    def get_route_length(self, route_id: str) -> float:
        """Calculate total route length"""
        if route_id not in self.routes:
            return 0
        
        route = self.routes[route_id]["geometry"]
        total_distance = 0
        
        points = route.geometry_points
        for i in range(len(points) - 1):
            distance = self.calculate_distance(points[i], points[i + 1])
            total_distance += distance
        
        return total_distance

# Usage
location_service = LocationService()

# Add various locations (using real coordinates)
location_service.add_location("starbucks_downtown", "Starbucks Downtown", -122.4194, 37.7749)
location_service.add_location("golden_gate_park", "Golden Gate Park", -122.4530, 37.7694)
location_service.add_location("pier_39", "Pier 39", -122.4098, 37.8085)
location_service.add_location("alcatraz", "Alcatraz Island", -122.4230, 37.8267)

# Create a tourist route
tourist_waypoints = [
    (-122.4194, 37.7749),  # Downtown
    (-122.4098, 37.8085),  # Pier 39
    (-122.4230, 37.8267),  # Alcatraz
    (-122.4530, 37.7694)   # Golden Gate Park
]

tourist_route = location_service.create_route("tourist_route", "SF Tourist Route", tourist_waypoints)
print(f"🗺️  Created tourist route with {len(tourist_route.geometry_points)} waypoints")

# Create a delivery zone
delivery_boundaries = [[
    (-122.4300, 37.7600),
    (-122.4100, 37.7600),
    (-122.4100, 37.7800),
    (-122.4300, 37.7800),
    (-122.4300, 37.7600)  # Close the polygon
]]

delivery_zone = location_service.create_zone("downtown_delivery", "Downtown Delivery Zone", delivery_boundaries)
print(f"📦 Created delivery zone with {len(delivery_zone.geometry_lines)} boundaries")

# Find nearby locations
center_point = GeometryPoint(-122.4194, 37.7749)  # Downtown
nearby_locations = location_service.find_nearby_locations(center_point, radius_km=5.0)

print(f"\n📍 Locations within 5km of downtown:")
for location_id, location_data, distance in nearby_locations:
    print(f"  {location_data['name']}: {distance:.2f} km")

# Calculate route length
route_length = location_service.get_route_length("tourist_route")
print(f"\n🛣️  Tourist route total length: {route_length:.2f} km")

# Display geometry coordinates
print(f"\n🎯 Geometry coordinates:")
print(f"Starbucks location: {location_service.locations['starbucks_downtown']['geometry'].get_coordinates()}")
print(f"Tourist route waypoints: {tourist_route.get_coordinates()}")
print(f"Delivery zone boundaries: {delivery_zone.get_coordinates()}")
```

### Example 2: Geographic Information System (GIS)

```python
from surrealdb.data.types.geometry import (
    GeometryPoint, GeometryLine, GeometryPolygon, 
    GeometryMultiPoint, GeometryMultiLine, GeometryMultiPolygon,
    GeometryCollection
)
from typing import List, Dict, Any

class GISManager:
    def __init__(self):
        self.layers: Dict[str, Dict[str, Any]] = {}
        self.features: Dict[str, List[Any]] = {}
    
    def create_layer(self, layer_id: str, layer_type: str, description: str):
        """Create a GIS layer"""
        self.layers[layer_id] = {
            "type": layer_type,
            "description": description,
            "feature_count": 0,
            "geometries": []
        }
        self.features[layer_id] = []
    
    def add_point_features(self, layer_id: str, points_data: List[Dict[str, Any]]):
        """Add point features to a layer"""
        if layer_id not in self.layers:
            self.create_layer(layer_id, "point", "Point layer")
        
        points = []
        for point_data in points_data:
            point = GeometryPoint(point_data["longitude"], point_data["latitude"])
            feature = {
                "geometry": point,
                "properties": point_data.get("properties", {}),
                "id": point_data.get("id", f"point_{len(points)}")
            }
            points.append(point)
            self.features[layer_id].append(feature)
        
        # Create multi-point geometry for the layer
        if len(points) > 1:
            multi_point = GeometryMultiPoint(*points)
            self.layers[layer_id]["geometries"].append(multi_point)
        
        self.layers[layer_id]["feature_count"] += len(points_data)
    
    def add_line_features(self, layer_id: str, lines_data: List[Dict[str, Any]]):
        """Add line features to a layer"""
        if layer_id not in self.layers:
            self.create_layer(layer_id, "line", "Line layer")
        
        lines = []
        for line_data in lines_data:
            coordinates = line_data["coordinates"]
            points = [GeometryPoint(coord[0], coord[1]) for coord in coordinates]
            line = GeometryLine(*points)
            
            feature = {
                "geometry": line,
                "properties": line_data.get("properties", {}),
                "id": line_data.get("id", f"line_{len(lines)}")
            }
            lines.append(line)
            self.features[layer_id].append(feature)
        
        # Create multi-line geometry for the layer
        if len(lines) > 1:
            multi_line = GeometryMultiLine(*lines)
            self.layers[layer_id]["geometries"].append(multi_line)
        
        self.layers[layer_id]["feature_count"] += len(lines_data)
    
    def add_polygon_features(self, layer_id: str, polygons_data: List[Dict[str, Any]]):
        """Add polygon features to a layer"""
        if layer_id not in self.layers:
            self.create_layer(layer_id, "polygon", "Polygon layer")
        
        polygons = []
        for polygon_data in polygons_data:
            rings = polygon_data["rings"]  # List of coordinate rings
            lines = []
            
            for ring in rings:
                points = [GeometryPoint(coord[0], coord[1]) for coord in ring]
                line = GeometryLine(*points)
                lines.append(line)
            
            polygon = GeometryPolygon(*lines)
            
            feature = {
                "geometry": polygon,
                "properties": polygon_data.get("properties", {}),
                "id": polygon_data.get("id", f"polygon_{len(polygons)}")
            }
            polygons.append(polygon)
            self.features[layer_id].append(feature)
        
        # Create multi-polygon geometry for the layer
        if len(polygons) > 1:
            multi_polygon = GeometryMultiPolygon(*polygons)
            self.layers[layer_id]["geometries"].append(multi_polygon)
        
        self.layers[layer_id]["feature_count"] += len(polygons_data)
    
    def create_geometry_collection(self, collection_id: str, layer_ids: List[str]):
        """Create a geometry collection from multiple layers"""
        geometries = []
        
        for layer_id in layer_ids:
            if layer_id in self.layers:
                geometries.extend(self.layers[layer_id]["geometries"])
        
        if geometries:
            collection = GeometryCollection(*geometries)
            return collection
        
        return None
    
    def get_layer_summary(self, layer_id: str) -> Dict[str, Any]:
        """Get summary information about a layer"""
        if layer_id not in self.layers:
            return {"error": "Layer not found"}
        
        layer = self.layers[layer_id]
        features = self.features[layer_id]
        
        # Calculate bounding box
        all_coords = []
        for feature in features:
            geom = feature["geometry"]
            if hasattr(geom, 'get_coordinates'):
                coords = geom.get_coordinates()
                if isinstance(coords, tuple):
                    all_coords.append(coords)
                elif isinstance(coords, list):
                    if coords and isinstance(coords[0], tuple):
                        all_coords.extend(coords)
                    elif coords and isinstance(coords[0], list):
                        for coord_list in coords:
                            if isinstance(coord_list[0], tuple):
                                all_coords.extend(coord_list)
        
        if all_coords:
            lons = [coord[0] for coord in all_coords]
            lats = [coord[1] for coord in all_coords]
            bounding_box = {
                "min_lon": min(lons),
                "max_lon": max(lons),
                "min_lat": min(lats),
                "max_lat": max(lats)
            }
        else:
            bounding_box = None
        
        return {
            "layer_id": layer_id,
            "type": layer["type"],
            "description": layer["description"],
            "feature_count": layer["feature_count"],
            "geometry_count": len(layer["geometries"]),
            "bounding_box": bounding_box
        }

# Usage
gis = GISManager()

# Add city points layer
cities_data = [
    {
        "id": "sf",
        "longitude": -122.4194,
        "latitude": 37.7749,
        "properties": {"name": "San Francisco", "population": 883305}
    },
    {
        "id": "la",
        "longitude": -118.2437,
        "latitude": 34.0522,
        "properties": {"name": "Los Angeles", "population": 3971883}
    },
    {
        "id": "sd",
        "longitude": -117.1611,
        "latitude": 32.7157,
        "properties": {"name": "San Diego", "population": 1423851}
    }
]

gis.add_point_features("california_cities", cities_data)

# Add highways layer
highways_data = [
    {
        "id": "i5",
        "coordinates": [
            [-117.1611, 32.7157],  # San Diego
            [-118.2437, 34.0522],  # Los Angeles
            [-122.4194, 37.7749]   # San Francisco
        ],
        "properties": {"name": "Interstate 5", "type": "highway"}
    },
    {
        "id": "i101",
        "coordinates": [
            [-117.2611, 32.8157],
            [-118.3437, 34.1522],
            [-122.5194, 37.8749]
        ],
        "properties": {"name": "US Route 101", "type": "highway"}
    }
]

gis.add_line_features("highways", highways_data)

# Add counties layer
counties_data = [
    {
        "id": "sf_county",
        "rings": [[
            [-122.5194, 37.7049],
            [-122.3194, 37.7049],
            [-122.3194, 37.8449],
            [-122.5194, 37.8449],
            [-122.5194, 37.7049]
        ]],
        "properties": {"name": "San Francisco County", "area_sq_km": 121}
    },
    {
        "id": "la_county",
        "rings": [[
            [-118.3437, 33.9522],
            [-118.1437, 33.9522],
            [-118.1437, 34.1522],
            [-118.3437, 34.1522],
            [-118.3437, 33.9522]
        ]],
        "properties": {"name": "Los Angeles County", "area_sq_km": 12305}
    }
]

gis.add_polygon_features("counties", counties_data)

# Create geometry collection
california_collection = gis.create_geometry_collection(
    "california_map", 
    ["california_cities", "highways", "counties"]
)

print("🗺️  GIS Layers Created:")

# Get layer summaries
for layer_id in ["california_cities", "highways", "counties"]:
    summary = gis.get_layer_summary(layer_id)
    print(f"\n📊 {summary['layer_id']} ({summary['type']}):")
    print(f"  Description: {summary['description']}")
    print(f"  Features: {summary['feature_count']}")
    print(f"  Geometries: {summary['geometry_count']}")
    if summary['bounding_box']:
        bbox = summary['bounding_box']
        print(f"  Bounding Box: ({bbox['min_lon']:.4f}, {bbox['min_lat']:.4f}) to ({bbox['max_lon']:.4f}, {bbox['max_lat']:.4f})")

print(f"\n🎯 Geometry Collection created with {len(california_collection.geometries)} geometry objects")

# Display some feature details
print(f"\n🏙️  City Features:")
for feature in gis.features["california_cities"]:
    coords = feature["geometry"].get_coordinates()
    props = feature["properties"]
    print(f"  {props['name']}: {coords} (Pop: {props['population']:,})")
```

### Example 3: Spatial Analysis System

```python
from surrealdb.data.types.geometry import (
    GeometryPoint, GeometryLine, GeometryPolygon, GeometryCollection
)
import math
from typing import List, Tuple, Optional

class SpatialAnalyzer:
    def __init__(self):
        self.analysis_results = {}
    
    def point_in_polygon(self, point: GeometryPoint, polygon: GeometryPolygon) -> bool:
        """Check if a point is inside a polygon using ray casting algorithm"""
        x, y = point