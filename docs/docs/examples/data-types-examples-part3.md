# SurrealDB Python SDK Data Types Examples - Part 3

This is the final part of comprehensive real-world examples for SurrealDB Python SDK data types.

## Geometry Examples (Continued)

### Example 3: Spatial Analysis System (Continued)

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
        x, y = point.get_coordinates()
        
        # Get the first boundary of the polygon
        if not polygon.geometry_lines:
            return False
        
        boundary = polygon.geometry_lines[0]  # Use first boundary
        vertices = boundary.get_coordinates()
        
        n = len(vertices)
        inside = False
        
        p1x, p1y = vertices[0]
        for i in range(1, n + 1):
            p2x, p2y = vertices[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def calculate_polygon_area(self, polygon: GeometryPolygon) -> float:
        """Calculate polygon area using shoelace formula"""
        if not polygon.geometry_lines:
            return 0.0
        
        boundary = polygon.geometry_lines[0]
        vertices = boundary.get_coordinates()
        
        n = len(vertices)
        area = 0.0
        
        for i in range(n):
            j = (i + 1) % n
            area += vertices[i][0] * vertices[j][1]
            area -= vertices[j][0] * vertices[i][1]
        
        return abs(area) / 2.0
    
    def calculate_line_length(self, line: GeometryLine) -> float:
        """Calculate total length of a line"""
        coordinates = line.get_coordinates()
        total_length = 0.0
        
        for i in range(len(coordinates) - 1):
            x1, y1 = coordinates[i]
            x2, y2 = coordinates[i + 1]
            segment_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            total_length += segment_length
        
        return total_length
    
    def find_polygon_centroid(self, polygon: GeometryPolygon) -> GeometryPoint:
        """Calculate polygon centroid"""
        if not polygon.geometry_lines:
            return GeometryPoint(0, 0)
        
        boundary = polygon.geometry_lines[0]
        vertices = boundary.get_coordinates()
        
        n = len(vertices)
        cx = cy = 0.0
        area = self.calculate_polygon_area(polygon)
        
        if area == 0:
            # Fallback to simple average
            cx = sum(v[0] for v in vertices) / n
            cy = sum(v[1] for v in vertices) / n
        else:
            for i in range(n):
                j = (i + 1) % n
                factor = vertices[i][0] * vertices[j][1] - vertices[j][0] * vertices[i][1]
                cx += (vertices[i][0] + vertices[j][0]) * factor
                cy += (vertices[i][1] + vertices[j][1]) * factor
            
            cx /= (6.0 * area)
            cy /= (6.0 * area)
        
        return GeometryPoint(cx, cy)
    
    def analyze_spatial_relationships(self, geometries: List[Tuple[str, any]]) -> dict:
        """Analyze relationships between multiple geometries"""
        results = {
            "total_geometries": len(geometries),
            "points": [],
            "lines": [],
            "polygons": [],
            "relationships": []
        }
        
        # Categorize geometries
        for name, geom in geometries:
            if isinstance(geom, GeometryPoint):
                results["points"].append({
                    "name": name,
                    "coordinates": geom.get_coordinates()
                })
            elif isinstance(geom, GeometryLine):
                results["lines"].append({
                    "name": name,
                    "length": self.calculate_line_length(geom),
                    "waypoints": len(geom.geometry_points)
                })
            elif isinstance(geom, GeometryPolygon):
                area = self.calculate_polygon_area(geom)
                centroid = self.find_polygon_centroid(geom)
                results["polygons"].append({
                    "name": name,
                    "area": area,
                    "centroid": centroid.get_coordinates()
                })
        
        # Analyze point-polygon relationships
        for point_info in results["points"]:
            point = GeometryPoint(*point_info["coordinates"])
            for polygon_info in results["polygons"]:
                # Find the original polygon geometry
                polygon_geom = next(geom for name, geom in geometries 
                                  if name == polygon_info["name"] and isinstance(geom, GeometryPolygon))
                
                if self.point_in_polygon(point, polygon_geom):
                    results["relationships"].append({
                        "type": "point_in_polygon",
                        "point": point_info["name"],
                        "polygon": polygon_info["name"]
                    })
        
        return results

# Usage
analyzer = SpatialAnalyzer()

# Create test geometries
test_geometries = [
    ("headquarters", GeometryPoint(-122.4194, 37.7749)),
    ("branch_office", GeometryPoint(-122.4100, 37.7800)),
    ("warehouse", GeometryPoint(-122.4300, 37.7600)),
    ("delivery_route", GeometryLine(
        GeometryPoint(-122.4194, 37.7749),
        GeometryPoint(-122.4100, 37.7800),
        GeometryPoint(-122.4300, 37.7600)
    )),
    ("service_area", GeometryPolygon(
        GeometryLine(
            GeometryPoint(-122.4300, 37.7600),
            GeometryPoint(-122.4000, 37.7600),
            GeometryPoint(-122.4000, 37.7900),
            GeometryPoint(-122.4300, 37.7900),
            GeometryPoint(-122.4300, 37.7600)
        )
    ))
]

# Perform spatial analysis
analysis = analyzer.analyze_spatial_relationships(test_geometries)

print("🔍 Spatial Analysis Results:")
print(f"Total geometries analyzed: {analysis['total_geometries']}")

print(f"\n📍 Points ({len(analysis['points'])}):")
for point in analysis['points']:
    print(f"  {point['name']}: {point['coordinates']}")

print(f"\n📏 Lines ({len(analysis['lines'])}):")
for line in analysis['lines']:
    print(f"  {line['name']}: {line['length']:.4f} units, {line['waypoints']} waypoints")

print(f"\n🔷 Polygons ({len(analysis['polygons'])}):")
for polygon in analysis['polygons']:
    print(f"  {polygon['name']}: Area {polygon['area']:.6f}, Centroid {polygon['centroid']}")

print(f"\n🔗 Spatial Relationships ({len(analysis['relationships'])}):")
for rel in analysis['relationships']:
    print(f"  {rel['point']} is inside {rel['polygon']}")

# Test specific point-in-polygon checks
service_area_polygon = next(geom for name, geom in test_geometries 
                           if name == "service_area" and isinstance(geom, GeometryPolygon))

test_points = [
    ("inside_point", GeometryPoint(-122.4150, 37.7750)),
    ("outside_point", GeometryPoint(-122.3900, 37.7500)),
    ("headquarters", GeometryPoint(-122.4194, 37.7749))
]

print(f"\n🎯 Point-in-Polygon Tests:")
for name, point in test_points:
    is_inside = analyzer.point_in_polygon(point, service_area_polygon)
    status = "✅ Inside" if is_inside else "❌ Outside"
    print(f"  {name} {point.get_coordinates()}: {status} service area")
```

## Range Examples

The range classes represent bounded ranges with inclusive and exclusive bounds.

### Example 1: Data Validation System

```python
from surrealdb.data.types.range import Range, BoundIncluded, BoundExcluded
from datetime import datetime, date
from typing import Any, Union

class DataValidator:
    def __init__(self):
        self.validation_rules = {}
    
    def add_numeric_range_rule(self, field_name: str, min_value: float, max_value: float,
                              min_inclusive: bool = True, max_inclusive: bool = True):
        """Add numeric range validation rule"""
        min_bound = BoundIncluded(min_value) if min_inclusive else BoundExcluded(min_value)
        max_bound = BoundIncluded(max_value) if max_inclusive else BoundExcluded(max_value)
        
        self.validation_rules[field_name] = {
            "type": "numeric_range",
            "range": Range(min_bound, max_bound),
            "description": f"Value must be between {min_value} and {max_value}"
        }
    
    def add_date_range_rule(self, field_name: str, start_date: date, end_date: date,
                           start_inclusive: bool = True, end_inclusive: bool = True):
        """Add date range validation rule"""
        start_bound = BoundIncluded(start_date) if start_inclusive else BoundExcluded(start_date)
        end_bound = BoundIncluded(end_date) if end_inclusive else BoundExcluded(end_date)
        
        self.validation_rules[field_name] = {
            "type": "date_range",
            "range": Range(start_bound, end_bound),
            "description": f"Date must be between {start_date} and {end_date}"
        }
    
    def validate_value(self, field_name: str, value: Any) -> dict:
        """Validate a value against its range rule"""
        if field_name not in self.validation_rules:
            return {"valid": True, "message": "No validation rule defined"}
        
        rule = self.validation_rules[field_name]
        range_obj = rule["range"]
        
        # Check bounds
        valid = True
        messages = []
        
        # Check lower bound
        if isinstance(range_obj.begin, BoundIncluded):
            if value < range_obj.begin.value:
                valid = False
                messages.append(f"Value {value} is below minimum {range_obj.begin.value}")
        elif isinstance(range_obj.begin, BoundExcluded):
            if value <= range_obj.begin.value:
                valid = False
                messages.append(f"Value {value} must be greater than {range_obj.begin.value}")
        
        # Check upper bound
        if isinstance(range_obj.end, BoundIncluded):
            if value > range_obj.end.value:
                valid = False
                messages.append(f"Value {value} is above maximum {range_obj.end.value}")
        elif isinstance(range_obj.end, BoundExcluded):
            if value >= range_obj.end.value:
                valid = False
                messages.append(f"Value {value} must be less than {range_obj.end.value}")
        
        return {
            "valid": valid,
            "messages": messages,
            "rule_description": rule["description"]
        }
    
    def validate_record(self, record: dict) -> dict:
        """Validate an entire record against all rules"""
        results = {
            "valid": True,
            "field_results": {},
            "errors": []
        }
        
        for field_name, value in record.items():
            if field_name in self.validation_rules:
                field_result = self.validate_value(field_name, value)
                results["field_results"][field_name] = field_result
                
                if not field_result["valid"]:
                    results["valid"] = False
                    results["errors"].extend(field_result["messages"])
        
        return results
    
    def get_validation_summary(self) -> dict:
        """Get summary of all validation rules"""
        summary = {
            "total_rules": len(self.validation_rules),
            "rules": {}
        }
        
        for field_name, rule in self.validation_rules.items():
            range_obj = rule["range"]
            
            begin_type = "inclusive" if isinstance(range_obj.begin, BoundIncluded) else "exclusive"
            end_type = "inclusive" if isinstance(range_obj.end, BoundIncluded) else "exclusive"
            
            summary["rules"][field_name] = {
                "type": rule["type"],
                "description": rule["description"],
                "begin_value": range_obj.begin.value,
                "begin_type": begin_type,
                "end_value": range_obj.end.value,
                "end_type": end_type
            }
        
        return summary

# Usage
validator = DataValidator()

# Add validation rules
validator.add_numeric_range_rule("age", 0, 120, min_inclusive=True, max_inclusive=True)
validator.add_numeric_range_rule("score", 0.0, 100.0, min_inclusive=True, max_inclusive=True)
validator.add_numeric_range_rule("temperature", -273.15, 1000.0, min_inclusive=False, max_inclusive=True)

# Add date range rules
validator.add_date_range_rule("birth_date", 
                             date(1900, 1, 1), 
                             date.today(), 
                             start_inclusive=True, 
                             end_inclusive=True)

validator.add_date_range_rule("event_date", 
                             date.today(), 
                             date(2030, 12, 31), 
                             start_inclusive=False, 
                             end_inclusive=True)

# Test validation
test_records = [
    {
        "name": "John Doe",
        "age": 25,
        "score": 85.5,
        "temperature": 36.5,
        "birth_date": date(1998, 5, 15),
        "event_date": date(2024, 12, 25)
    },
    {
        "name": "Invalid User",
        "age": -5,  # Invalid: below minimum
        "score": 105.0,  # Invalid: above maximum
        "temperature": -273.15,  # Invalid: exclusive bound
        "birth_date": date(2025, 1, 1),  # Invalid: future birth date
        "event_date": date(2020, 1, 1)  # Invalid: past event date
    }
]

print("🔍 Data Validation Results:")

for i, record in enumerate(test_records, 1):
    print(f"\n📋 Record {i}: {record['name']}")
    validation_result = validator.validate_record(record)
    
    if validation_result["valid"]:
        print("  ✅ All validations passed")
    else:
        print("  ❌ Validation failed:")
        for error in validation_result["errors"]:
            print(f"    - {error}")
    
    # Show field-by-field results
    for field_name, field_result in validation_result["field_results"].items():
        status = "✅" if field_result["valid"] else "❌"
        print(f"    {status} {field_name}: {record[field_name]}")

# Display validation rules summary
print(f"\n📊 Validation Rules Summary:")
summary = validator.get_validation_summary()
print(f"Total rules: {summary['total_rules']}")

for field_name, rule_info in summary["rules"].items():
    print(f"\n  {field_name} ({rule_info['type']}):")
    print(f"    Range: {rule_info['begin_value']} ({rule_info['begin_type']}) to {rule_info['end_value']} ({rule_info['end_type']})")
    print(f"    Description: {rule_info['description']}")
```

### Example 2: Time-based Access Control

```python
from surrealdb.data.types.range import Range, BoundIncluded, BoundExcluded
from datetime import datetime, time, timedelta
from typing import List, Dict, Any

class AccessControlManager:
    def __init__(self):
        self.access_rules: Dict[str, List[Dict[str, Any]]] = {}
        self.access_logs: List[Dict[str, Any]] = []
    
    def add_time_based_rule(self, user_id: str, resource: str, 
                           start_time: time, end_time: time,
                           start_inclusive: bool = True, end_inclusive: bool = False):
        """Add time-based access rule"""
        start_bound = BoundIncluded(start_time) if start_inclusive else BoundExcluded(start_time)
        end_bound = BoundIncluded(end_time) if end_inclusive else BoundExcluded(end_time)
        
        time_range = Range(start_bound, end_bound)
        
        if user_id not in self.access_rules:
            self.access_rules[user_id] = []
        
        rule = {
            "resource": resource,
            "time_range": time_range,
            "created_at": datetime.now(),
            "active": True
        }
        
        self.access_rules[user_id].append(rule)
        return rule
    
    def add_date_range_rule(self, user_id: str, resource: str,
                           start_date: datetime, end_date: datetime,
                           start_inclusive: bool = True, end_inclusive: bool = True):
        """Add date range access rule"""
        start_bound = BoundIncluded(start_date) if start_inclusive else BoundExcluded(start_date)
        end_bound = BoundIncluded(end_date) if end_inclusive else BoundExcluded(end_date)
        
        date_range = Range(start_bound, end_bound)
        
        if user_id not in self.access_rules:
            self.access_rules[user_id] = []
        
        rule = {
            "resource": resource,
            "date_range": date_range,
            "created_at": datetime.now(),
            "active": True
        }
        
        self.access_rules[user_id].append(rule)
        return rule
    
    def check_access(self, user_id: str, resource: str, access_time: datetime = None) -> dict:
        """Check if user has access to resource at given time"""
        if access_time is None:
            access_time = datetime.now()
        
        if user_id not in self.access_rules:
            return {
                "allowed": False,
                "reason": "No access rules defined for user",
                "user_id": user_id,
                "resource": resource,
                "access_time": access_time
            }
        
        user_rules = [rule for rule in self.access_rules[user_id] 
                     if rule["resource"] == resource and rule["active"]]
        
        if not user_rules:
            return {
                "allowed": False,
                "reason": "No access rules for this resource",
                "user_id": user_id,
                "resource": resource,
                "access_time": access_time
            }
        
        # Check each rule
        for rule in user_rules:
            if "time_range" in rule:
                # Time-based rule (daily recurring)
                current_time = access_time.time()
                time_range = rule["time_range"]
                
                allowed = self._check_time_in_range(current_time, time_range)
                if allowed:
                    self._log_access(user_id, resource, access_time, True, "Time-based rule matched")
                    return {
                        "allowed": True,
                        "reason": "Time-based access granted",
                        "rule_type": "time_range",
                        "user_id": user_id,
                        "resource": resource,
                        "access_time": access_time
                    }
            
            elif "date_range" in rule:
                # Date range rule
                date_range = rule["date_range"]
                
                allowed = self._check_datetime_in_range(access_time, date_range)
                if allowed:
                    self._log_access(user_id, resource, access_time, True, "Date range rule matched")
                    return {
                        "allowed": True,
                        "reason": "Date range access granted",
                        "rule_type": "date_range",
                        "user_id": user_id,
                        "resource": resource,
                        "access_time": access_time
                    }
        
        # No rules matched
        self._log_access(user_id, resource, access_time, False, "No matching access rules")
        return {
            "allowed": False,
            "reason": "Access denied - no matching rules",
            "user_id": user_id,
            "resource": resource,
            "access_time": access_time
        }
    
    def _check_time_in_range(self, check_time: time, time_range: Range) -> bool:
        """Check if time falls within range"""
        # Convert time to minutes for easier comparison
        check_minutes = check_time.hour * 60 + check_time.minute
        
        start_time = time_range.begin.value
        start_minutes = start_time.hour * 60 + start_time.minute
        
        end_time = time_range.end.value
        end_minutes = end_time.hour * 60 + end_time.minute
        
        # Handle inclusive/exclusive bounds
        if isinstance(time_range.begin, BoundIncluded):
            start_ok = check_minutes >= start_minutes
        else:
            start_ok = check_minutes > start_minutes
        
        if isinstance(time_range.end, BoundIncluded):
            end_ok = check_minutes <= end_minutes
        else:
            end_ok = check_minutes < end_minutes
        
        return start_ok and end_ok
    
    def _check_datetime_in_range(self, check_datetime: datetime, date_range: Range) -> bool:
        """Check if datetime falls within range"""
        start_datetime = date_range.begin.value
        end_datetime = date_range.end.value
        
        # Handle inclusive/exclusive bounds
        if isinstance(date_range.begin, BoundIncluded):
            start_ok = check_datetime >= start_datetime
        else:
            start_ok = check_datetime > start_datetime
        
        if isinstance(date_range.end, BoundIncluded):
            end_ok = check_datetime <= end_datetime
        else:
            end_ok = check_datetime < end_datetime
        
        return start_ok and end_ok
    
    def _log_access(self, user_id: str, resource: str, access_time: datetime, 
                   allowed: bool, reason: str):
        """Log access attempt"""
        log_entry = {
            "user_id": user_id,
            "resource": resource,
            "access_time": access_time,
            "allowed": allowed,
            "reason": reason,
            "logged_at": datetime.now()
        }
        self.access_logs.append(log_entry)
    
    def get_user_rules_summary(self, user_id: str) -> dict:
        """Get summary of user's access rules"""
        if user_id not in self.access_rules:
            return {"user_id": user_id, "rules": []}
        
        rules_summary = []
        for rule in self.access_rules[user_id]:
            if not rule["active"]:
                continue
            
            rule_info = {
                "resource": rule["resource"],
                "created_at": rule["created_at"]
            }
            
            if "time_range" in rule:
                time_range = rule["time_range"]
                rule_info.update({
                    "type": "time_range",
                    "start_time": time_range.begin.value.strftime("%H:%M"),
                    "end_time": time_range.end.value.strftime("%H:%M"),
                    "start_inclusive": isinstance(time_range.begin, BoundIncluded),
                    "end_inclusive": isinstance(time_range.end, BoundIncluded)
                })
            
            elif "date_range" in rule:
                date_range = rule["date_range"]
                rule_info.update({
                    "type": "date_range",
                    "start_date": date_range.begin.value.strftime("%Y-%m-%d %H:%M"),
                    "end_date": date_range.end.value.strftime("%Y-%m-%d %H:%M"),
                    "start_inclusive": isinstance(date_range.begin, BoundIncluded),
                    "end_inclusive": isinstance(date_range.end, BoundIncluded)
                })
            
            rules_summary.append(rule_info)
        
        return {
            "user_id": user_id,
            "total_rules": len(rules_summary),
            "rules": rules_summary
        }

# Usage
access_manager = AccessControlManager()

# Add time-based rules (daily recurring)
access_manager.add_time_based_rule("employee_001", "office_system", 
                                  time(9, 0), time(17, 0),  # 9 AM to 5 PM
                                  start_inclusive=True, end_inclusive=False)

access_manager.add_time_based_rule("security_guard", "security_system", 
                                  time(22, 0), time(6, 0),  # 10 PM to 6 AM
                                  start_inclusive=True, end_inclusive=False)

# Add date range rules (temporary access)
temp_start = datetime.now()
temp_end = temp_start + timedelta(days=7)

access_manager.add_date_range_rule("contractor_001", "project_files",
                                  temp_start, temp_end,
                                  start_inclusive=True, end_inclusive=True)

# Test access at different times
test_scenarios = [
    ("employee_001", "office_system", datetime.now().replace(hour=10, minute=30)),  # During work hours
    ("employee_001", "office_system", datetime.now().replace(hour=20, minute=0)),   # After hours
    ("security_guard", "security_system", datetime.now().replace(hour=23, minute=0)), # Night shift
    ("contractor_001", "project_files", datetime.now()),  # Within date range
    ("unauthorized_user", "office_system", datetime.now()),  # No rules
]

print("🔐 Access Control Test Results:")

for user_id, resource, test_time in test_scenarios:
    result = access_manager.check_access(user_id, resource, test_time)
    status = "✅ ALLOWED" if result["allowed"] else "❌ DENIED"
    
    print(f"\n{status}")
    print(f"  User: {result['user_id']}")
    print(f"  Resource: {result['resource']}")
    print(f"  Time: {result['access_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Reason: {result['reason']}")

# Display user rules summary
print(f"\n📋 User Access Rules Summary:")
for user_id in ["employee_001", "security_guard", "contractor_001"]:
    summary = access_manager.get_user_rules_summary(user_id)
    print(f"\n👤 {summary['user_id']} ({summary['total_rules']} rules):")
    
    for rule in summary["rules"]:
        print(f"  📄 {rule['resource']} ({rule['type']}):")
        if rule["type"] == "time_range":
            start_bracket = "[" if rule["start_inclusive"] else "("
            end_bracket = "]" if rule["end_inclusive"] else ")"
            print(f"    Time: {start_bracket}{rule['start_time']} - {rule['end_time']}{end_bracket}")
        elif rule["type"] == "date_range":
            start_bracket = "[" if rule["start_inclusive"] else "("
            end_bracket = "]" if rule["end_inclusive"] else ")"
            print(f"    Date: {start_bracket}{rule['start_date']} - {rule['end_date']}{end_bracket}")

# Show recent access logs
print(f"\n📊 Recent Access Logs:")
for log in access_manager.access_logs[-5:]:  # Show last 5 logs
    status = "✅" if log["allowed"] else "❌"
    print(f"  {status} {log['user_id']} -> {log['resource']} at {log['access_time'].strftime('%H:%M:%S')}")
    print(f"    Reason: {log['reason']}")
```

## Future Examples

The `Future` class represents a placeholder for values that may be resolved later.

### Example 1: Asynchronous Task Management

```python
from surrealdb.data.types.future import Future
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
import asyncio
import uuid

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.futures: Dict[str, Future] = {}
        self.completed_tasks: Dict[str, Any] = {}
    
    def create_task(self, task_name: str, task_function: Callable = None, 
                   dependencies: List[str] = None) -> str:
        """Create a new task and return its ID"""
        task_id = str(uuid.uuid4())
        
        # Create a Future to hold the eventual result
        task_future = Future(None)  # Initially unresolved
        
        task_data = {
            "id": task_id,
            "name": task_name,
            "function": task_function,
            "dependencies": dependencies or [],
            "status": "pending",
            "created_at": datetime.now(),
            "started_at": None,
            "completed_at": None,
            "result_future": task_future,
            "error": None
        }
        
        self.tasks[task_id] = task_data
        self.futures[task_id] = task_future
        
        return task_id
    
    def create_dependent_task(self, task_name: str, dependency_ids: List[str],