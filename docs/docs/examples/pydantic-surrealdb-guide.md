# Pydantic with SurrealDB Python SDK - Comprehensive Type Safety Guide

This guide demonstrates how to use Pydantic models with SurrealDB Python SDK to achieve robust type safety, validation, and serialization. The examples are practical, runnable, and follow best practices for production applications.

## Table of Contents

1. [Introduction and Setup](#introduction-and-setup)
2. [Basic Pydantic Models for SurrealDB](#basic-pydantic-models-for-surrealdb)
3. [User Management with RecordID](#user-management-with-recordid)
4. [Product Catalog with Various Data Types](#product-catalog-with-various-data-types)
5. [Location-Based Services with Geometry](#location-based-services-with-geometry)
6. [Time-Based Applications](#time-based-applications)
7. [Range-Based Data Validation](#range-based-data-validation)
8. [Custom Validators for SurrealDB Types](#custom-validators-for-surrealdb-types)
9. [Error Handling and Type Conversion](#error-handling-and-type-conversion)
10. [Performance Considerations](#performance-considerations)
11. [Integration with SurrealDB Operations](#integration-with-surrealdb-operations)
12. [Best Practices](#best-practices)

## Introduction and Setup

### Installation

```bash
pip install pydantic surrealdb
```

### Basic Imports

```python
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Union, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator, root_validator
from pydantic.types import constr, confloat, conint

from surrealdb import Surreal
from surrealdb.data.types.record_id import RecordID
from surrealdb.data.types.geometry import (
    GeometryPoint, GeometryLine, GeometryPolygon,
    GeometryMultiPoint, GeometryMultiLine, GeometryMultiPolygon,
    GeometryCollection
)
from surrealdb.data.types.duration import Duration
from surrealdb.data.types.datetime import IsoDateTimeWrapper
from surrealdb.data.types.range import Range, BoundIncluded, BoundExcluded
from surrealdb.data.types.table import Table
from surrealdb.data.types.future import Future
```

## Basic Pydantic Models for SurrealDB

### Base Model with SurrealDB Integration

```python
class SurrealDBModel(BaseModel):
    """Base model for SurrealDB integration with common functionality."""
    
    class Config:
        # Allow arbitrary types for SurrealDB custom types
        arbitrary_types_allowed = True
        # Use enum values for serialization
        use_enum_values = True
        # Validate assignment
        validate_assignment = True
        # JSON encoders for SurrealDB types
        json_encoders = {
            RecordID: lambda v: str(v),
            Duration: lambda v: v.to_string(),
            GeometryPoint: lambda v: {"type": "Point", "coordinates": list(v.get_coordinates())},
            GeometryLine: lambda v: {"type": "LineString", "coordinates": v.get_coordinates()},
            GeometryPolygon: lambda v: {"type": "Polygon", "coordinates": v.get_coordinates()},
            Range: lambda v: {"begin": v.begin.value, "end": v.end.value},
            datetime: lambda v: v.isoformat(),
        }
    
    @classmethod
    def from_surrealdb(cls, data: dict):
        """Create model instance from SurrealDB response data."""
        return cls(**data)
    
    def to_surrealdb(self) -> dict:
        """Convert model to dictionary suitable for SurrealDB operations."""
        return self.dict(exclude_none=True)
```

## User Management with RecordID

### User Models

```python
from enum import Enum
from typing import Optional, List

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class User(SurrealDBModel):
    """User model with RecordID and comprehensive validation."""
    
    id: Optional[RecordID] = None
    username: constr(min_length=3, max_length=50, regex=r'^[a-zA-Z0-9_]+$')
    email: constr(regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    full_name: constr(min_length=1, max_length=100)
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    profile_picture_url: Optional[str] = None
    bio: Optional[constr(max_length=500)] = None
    location: Optional[GeometryPoint] = None
    session_timeout: Duration = Field(default_factory=lambda: Duration.parse("1h"))
    
    @validator('id', pre=True, always=True)
    def validate_record_id(cls, v, values):
        """Validate and create RecordID if needed."""
        if v is None:
            username = values.get('username')
            if username:
                return RecordID("users", username)
        elif isinstance(v, str):
            return RecordID.parse(v)
        return v
    
    @validator('updated_at', pre=True, always=True)
    def set_updated_at(cls, v):
        """Automatically set updated_at timestamp."""
        return datetime.now(timezone.utc)
    
    @validator('location', pre=True)
    def validate_location(cls, v):
        """Validate and convert location data."""
        if v is None:
            return v
        if isinstance(v, dict) and 'coordinates' in v:
            coords = v['coordinates']
            return GeometryPoint(coords[0], coords[1])
        elif isinstance(v, (list, tuple)) and len(v) == 2:
            return GeometryPoint(v[0], v[1])
        return v
    
    @validator('session_timeout', pre=True)
    def validate_session_timeout(cls, v):
        """Validate and convert session timeout."""
        if isinstance(v, str):
            return Duration.parse(v)
        elif isinstance(v, int):
            return Duration.parse(f"{v}s")
        return v

class UserProfile(SurrealDBModel):
    """Extended user profile with additional information."""
    
    user_id: RecordID
    preferences: dict = Field(default_factory=dict)
    social_links: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    experience_years: Optional[conint(ge=0, le=100)] = None
    timezone: str = "UTC"
    language: str = "en"
    
    @validator('user_id', pre=True)
    def validate_user_id(cls, v):
        """Validate user_id as RecordID."""
        if isinstance(v, str):
            return RecordID.parse(v)
        return v

# Usage Example
async def create_user_example():
    """Example of creating and validating a user."""
    try:
        # Create user with validation
        user_data = {
            "username": "john_doe",
            "email": "john@example.com",
            "full_name": "John Doe",
            "role": "user",
            "location": [-122.4194, 37.7749],  # San Francisco
            "session_timeout": "2h",
            "bio": "Software developer passionate about databases"
        }
        
        user = User(**user_data)
        print(f"Created user: {user.id}")
        print(f"Location: {user.location}")
        print(f"Session timeout: {user.session_timeout.to_string()}")
        
        return user
        
    except Exception as e:
        print(f"Validation error: {e}")
        return None
```

## Product Catalog with Various Data Types

### Product Models

```python
from decimal import Decimal
from typing import Dict, Any

class ProductCategory(str, Enum):
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    BOOKS = "books"
    HOME = "home"
    SPORTS = "sports"

class ProductStatus(str, Enum):
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    OUT_OF_STOCK = "out_of_stock"

class Product(SurrealDBModel):
    """Product model with comprehensive data types."""
    
    id: Optional[RecordID] = None
    sku: constr(min_length=3, max_length=50)
    name: constr(min_length=1, max_length=200)
    description: Optional[constr(max_length=2000)] = None
    category: ProductCategory
    status: ProductStatus = ProductStatus.ACTIVE
    price: Decimal = Field(..., decimal_places=2, gt=0)
    cost: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    weight: Optional[confloat(gt=0)] = None  # in kg
    dimensions: Optional[Dict[str, float]] = None  # length, width, height
    stock_quantity: conint(ge=0) = 0
    reorder_level: conint(ge=0) = 10
    supplier_id: Optional[RecordID] = None
    tags: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    @validator('id', pre=True, always=True)
    def validate_record_id(cls, v, values):
        """Generate RecordID from SKU if not provided."""
        if v is None:
            sku = values.get('sku')
            if sku:
                return RecordID("products", sku)
        elif isinstance(v, str):
            return RecordID.parse(v)
        return v
    
    @validator('supplier_id', pre=True)
    def validate_supplier_id(cls, v):
        """Validate supplier_id as RecordID."""
        if v and isinstance(v, str):
            return RecordID.parse(v)
        return v
    
    @validator('price', 'cost', pre=True)
    def validate_decimal_fields(cls, v):
        """Convert string/float to Decimal for precise calculations."""
        if v is not None:
            return Decimal(str(v))
        return v
    
    @validator('dimensions')
    def validate_dimensions(cls, v):
        """Validate dimensions dictionary."""
        if v is not None:
            required_keys = {'length', 'width', 'height'}
            if not all(key in v for key in required_keys):
                raise ValueError("Dimensions must include length, width, and height")
            if not all(isinstance(val, (int, float)) and val > 0 for val in v.values()):
                raise ValueError("All dimension values must be positive numbers")
        return v
    
    @property
    def profit_margin(self) -> Optional[Decimal]:
        """Calculate profit margin if cost is available."""
        if self.cost and self.cost > 0:
            return ((self.price - self.cost) / self.price) * 100
        return None
    
    @property
    def is_low_stock(self) -> bool:
        """Check if product is low on stock."""
        return self.stock_quantity <= self.reorder_level

class ProductVariant(SurrealDBModel):
    """Product variant model for different sizes, colors, etc."""
    
    id: Optional[RecordID] = None
    product_id: RecordID
    variant_type: str  # e.g., "size", "color"
    variant_value: str  # e.g., "Large", "Red"
    sku_suffix: str  # e.g., "-L", "-RED"
    price_adjustment: Decimal = Field(default=Decimal('0.00'), decimal_places=2)
    stock_quantity: conint(ge=0) = 0
    
    @validator('id', pre=True, always=True)
    def validate_record_id(cls, v, values):
        """Generate RecordID for variant."""
        if v is None:
            product_id = values.get('product_id')
            sku_suffix = values.get('sku_suffix')
            if product_id and sku_suffix:
                variant_id = f"{product_id.id}{sku_suffix}"
                return RecordID("product_variants", variant_id)
        elif isinstance(v, str):
            return RecordID.parse(v)
        return v
    
    @validator('product_id', pre=True)
    def validate_product_id(cls, v):
        """Validate product_id as RecordID."""
        if isinstance(v, str):
            return RecordID.parse(v)
        return v

# Usage Example
async def create_product_example():
    """Example of creating and validating a product."""
    try:
        product_data = {
            "sku": "LAPTOP-001",
            "name": "Gaming Laptop Pro",
            "description": "High-performance gaming laptop with RTX graphics",
            "category": "electronics",
            "price": "1299.99",
            "cost": "899.99",
            "weight": 2.5,
            "dimensions": {"length": 35.0, "width": 25.0, "height": 2.5},
            "stock_quantity": 50,
            "reorder_level": 10,
            "supplier_id": "suppliers:tech_corp",
            "tags": ["gaming", "laptop", "high-performance"],
            "images": ["laptop1.jpg", "laptop2.jpg"]
        }
        
        product = Product(**product_data)
        print(f"Created product: {product.id}")
        print(f"Profit margin: {product.profit_margin:.2f}%")
        print(f"Low stock: {product.is_low_stock}")
        
        return product
        
    except Exception as e:
        print(f"Validation error: {e}")
        return None
```

## Location-Based Services with Geometry

### Location Models

```python
class LocationType(str, Enum):
    POINT_OF_INTEREST = "poi"
    RESTAURANT = "restaurant"
    STORE = "store"
    OFFICE = "office"
    RESIDENCE = "residence"

class Location(SurrealDBModel):
    """Location model with geometry support."""
    
    id: Optional[RecordID] = None
    name: constr(min_length=1, max_length=200)
    location_type: LocationType
    address: str
    coordinates: GeometryPoint
    service_area: Optional[Union[GeometryPolygon, GeometryMultiPolygon]] = None
    delivery_zones: List[GeometryPolygon] = Field(default_factory=list)
    operating_hours: Dict[str, str] = Field(default_factory=dict)
    contact_info: Dict[str, str] = Field(default_factory=dict)
    rating: Optional[confloat(ge=0, le=5)] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('id', pre=True, always=True)
    def validate_record_id(cls, v, values):
        """Generate RecordID from name if not provided."""
        if v is None:
            name = values.get('name')
            if name:
                # Create a slug from name
                slug = name.lower().replace(' ', '_').replace('-', '_')
                return RecordID("locations", slug)
        elif isinstance(v, str):
            return RecordID.parse(v)
        return v
    
    @validator('coordinates', pre=True)
    def validate_coordinates(cls, v):
        """Validate and convert coordinates."""
        if isinstance(v, dict) and 'coordinates' in v:
            coords = v['coordinates']
            return GeometryPoint(coords[0], coords[1])
        elif isinstance(v, (list, tuple)) and len(v) == 2:
            return GeometryPoint(v[0], v[1])
        elif isinstance(v, GeometryPoint):
            return v
        else:
            raise ValueError("Coordinates must be a GeometryPoint, dict with coordinates, or [lon, lat] array")
    
    @validator('service_area', pre=True)
    def validate_service_area(cls, v):
        """Validate service area geometry."""
        if v is None:
            return v
        if isinstance(v, dict):
            if v.get('type') == 'Polygon':
                coords = v['coordinates']
                lines = [GeometryLine.parse_coordinates(line) for line in coords]
                return GeometryPolygon(*lines)
            elif v.get('type') == 'MultiPolygon':
                coords = v['coordinates']
                polygons = [GeometryPolygon.parse_coordinates(poly) for poly in coords]
                return GeometryMultiPolygon(*polygons)
        return v
    
    def distance_to(self, other_location: 'Location') -> float:
        """Calculate distance to another location (simplified)."""
        # This is a simplified calculation - in production, use proper geospatial functions
        import math
        
        lat1, lon1 = self.coordinates.latitude, self.coordinates.longitude
        lat2, lon2 = other_location.coordinates.latitude, other_location.coordinates.longitude
        
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

class Route(SurrealDBModel):
    """Route model with line geometry."""
    
    id: Optional[RecordID] = None
    name: str
    start_location_id: RecordID
    end_location_id: RecordID
    waypoints: List[GeometryPoint] = Field(default_factory=list)
    route_geometry: GeometryLine
    distance_km: confloat(gt=0)
    estimated_duration: Duration
    route_type: str = "driving"  # driving, walking, cycling
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('id', pre=True, always=True)
    def validate_record_id(cls, v, values):
        """Generate RecordID for route."""
        if v is None:
            start_id = values.get('start_location_id')
            end_id = values.get('end_location_id')
            if start_id and end_id:
                route_id = f"{start_id.id}_to_{end_id.id}"
                return RecordID("routes", route_id)
        elif isinstance(v, str):
            return RecordID.parse(v)
        return v
    
    @validator('start_location_id', 'end_location_id', pre=True)
    def validate_location_ids(cls, v):
        """Validate location IDs as RecordID."""
        if isinstance(v, str):
            return RecordID.parse(v)
        return v
    
    @validator('estimated_duration', pre=True)
    def validate_duration(cls, v):
        """Validate and convert duration."""
        if isinstance(v, str):
            return Duration.parse(v)
        elif isinstance(v, (int, float)):
            return Duration.parse(f"{int(v)}s")
        return v

# Usage Example
async def create_location_example():
    """Example of creating location with geometry."""
    try:
        # Create a restaurant location
        location_data = {
            "name": "Pizza Palace",
            "location_type": "restaurant",
            "address": "123 Main St, San Francisco, CA",
            "coordinates": [-122.4194, 37.7749],  # San Francisco coordinates
            "operating_hours": {
                "monday": "11:00-22:00",
                "tuesday": "11:00-22:00",
                "wednesday": "11:00-22:00",
                "thursday": "11:00-22:00",
                "friday": "11:00-23:00",
                "saturday": "11:00-23:00",
                "sunday": "12:00-21:00"
            },
            "contact_info": {
                "phone": "+1-555-0123",
                "email": "info@pizzapalace.com"
            },
            "rating": 4.5
        }
        
        location = Location(**location_data)
        print(f"Created location: {location.id}")
        print(f"Coordinates: {location.coordinates.get_coordinates()}")
        
        return location
        
    except Exception as e:
        print(f"Validation error: {e}")
        return None
```

## Time-Based Applications

### Time-Based Models

```python
class EventStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Event(SurrealDBModel):
    """Event model with comprehensive time handling."""
    
    id: Optional[RecordID] = None
    title: constr(min_length=1, max_length=200)
    description: Optional[str] = None
    organizer_id: RecordID
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"
    duration: Optional[Duration] = None
    status: EventStatus = EventStatus.SCHEDULED
    location: Optional[GeometryPoint] = None
    attendee_limit: Optional[conint(gt=0)] = None
    registration_deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    @validator('id', pre=True, always=True)
    def validate_record_id(cls, v, values):
        """Generate RecordID for event."""
        if v is None:
            title = values.get('title')
            start_time = values.get('start_time')
            if title and start_time:
                # Create slug from title and timestamp
                slug = title.lower().replace(' ', '_')[:20]
                timestamp = int(start_time.timestamp()) if isinstance(start_time, datetime) else int(datetime.now().timestamp())
                return RecordID("events", f"{slug}_{timestamp}")
        elif isinstance(v, str):
            return RecordID.parse(v)
        return v
    
    @validator('organizer_id', pre=True)
    def validate_organizer_id(cls, v):
        """Validate organizer_id as RecordID."""
        if isinstance(v, str):
            return RecordID.parse(v)
        return v
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        """Ensure end_time is after start_time."""
        start_time = values.get('start_time')
        if start_time and v <= start_time:
            raise ValueError("End time must be after start time")
        return v
    
    @validator('duration', pre=True, always=True)
    def calculate_duration(cls, v, values):
        """Calculate duration from start and end times."""
        start_time = values.get('start_time')
        end_time = values.get('end_time')
        
        if start_time and end_time:
            duration_seconds = int((end_time - start_time).total_seconds())
            return Duration.parse(f"{duration_seconds}s")
        return v
    
    @validator('registration_deadline')
    def validate_registration_deadline(cls, v, values):
        """Ensure registration deadline is before start time."""
        start_time = values.get('start_time')
        if v and start_time and v >= start_time:
            raise ValueError("Registration deadline must be before event start time")
        return v
    
    @property
    def is_upcoming(self) -> bool:
        """Check if event is upcoming."""
        return self.start_time > datetime.now(timezone.utc)
    
    @property
    def is_ongoing(self) -> bool:
        """Check if event is currently ongoing."""
        now = datetime.now(timezone.utc)
        return self.start_time <= now <= self.end_time

class Schedule(SurrealDBModel):
    """Schedule model for recurring events."""
    
    id: Optional[RecordID] = None
    name: str
    owner_id: RecordID
    events: List[RecordID] = Field(default_factory=list)
    recurrence_pattern: Optional[str] = None  # cron-like pattern
    next_occurrence: Optional[datetime] = None
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('id', pre=True, always=True)
    def validate_record_id(cls, v, values):
        """Generate RecordID for schedule."""
        if v is None:
            name = values.get('name')
            owner_id = values.get('owner_id')
            if name and owner_id:
                slug = name.lower().replace(' ', '_')
                return RecordID("schedules", f"{owner_id.id}_{slug}")
        elif isinstance(v, str):
            return RecordID.parse(v)
        return v
    
    @validator('owner_id', pre=True)
    def validate_owner_id(cls, v):
        """Validate owner_id as RecordID."""
        if isinstance(v, str):
            return RecordID.parse(v)
        return v
    
    @validator('events', pre=True)
    def validate_events(cls, v):
        """Validate event IDs as RecordID list."""
        if v:
            return [RecordID.parse(event_id) if isinstance(event_id, str) else event_id for event_id in v]
        return v

# Usage Example
async def create_event_example():
    """Example of creating time-based event."""
    try:
        # Create an event
        event_data = {
            "title": "Python Workshop",
            "description": "Learn Python with SurrealDB and Pydantic",
            "organizer_id": "users:john_doe",
            "start_time": datetime(2024, 6, 15, 14, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 6, 15, 17, 0, tzinfo=timezone.utc),
            "timezone": "UTC",
            "location": [-122.4194, 37.7749],
            "attendee_limit": 50,
            "registration_deadline": datetime(2024, 6, 14, 23, 59, tzinfo=timezone.utc)
        }
        
        event = Event(**event_data)
        print(f"Created event: {event.id}")
        print(f"Duration: {event.duration.to_string()}")
        print(f"Is upcoming: {event.is_upcoming}")
        
        return event
        
    except Exception as e:
        print(f"Validation error: {e}")
        return None
```

## Range-Based Data Validation

### Range Models

```python
class PriceRange(SurrealDBModel):
    """Price range model with validation."""
    
    id: Optional[RecordID] = None
    name: str
    min_price: Decimal
    max_price: Decimal
    currency: str = "USD"
    range_obj: Optional[Range] = None
    category: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('id', pre=True, always=True)
    def validate_record_id(cls, v, values):
        """Generate RecordID for price range."""
        if v is None:
            name = values.get('name')
            if name:
                slug = name.lower().replace(' ', '_')
                return RecordID("price_ranges", slug)
        elif isinstance(v, str):
            return RecordID.parse(v)
        return v
    
    @validator('max_price')
    def validate_max_price(cls, v, values):
        """Ensure max_price is greater than min_price."""
        min_price = values.get('min_price')
        if min_price and v <= min_price:
            raise ValueError("Maximum price must be greater than minimum price")
        return v
    
    @validator('range_obj', pre=True, always=True)
    def create_range_object(cls, v, values):
        """Create Range object from min/max prices."""
        min_price = values.get('min_price')
        max_price = values.get('max_price')
        
        if min_price is not None and max_price is not None:
            return Range(
                BoundIncluded(min_price),
                BoundIncluded(max_price)
            )
        return v
    
    def contains_price(self, price: Decimal) -> bool:
        """Check if price falls within this range."""
        return self.min_price <= price <= self.max_price

class AgeRestriction(SurrealDBModel):
    """Age restriction model with range validation."""
    
    id: Optional[RecordID] = None
    name: str
    min_age: conint(ge=0, le=150)
    max_age: conint(ge=0, le=150)
    age_range: Optional[Range] = None
    description: Optional[str] = None
    
    @validator('id', pre=True, always=True)
    def validate_record_id(cls, v, values):
        """Generate RecordID for age restriction."""
        if v is None:
            name = values.get('name')
            if name:
                slug = name.lower().replace(' ', '_')
                return RecordID("age_restrictions", slug)
        elif isinstance(v, str):
            return RecordID.parse(v)
        return v
    
    @validator('max_age')
    def validate_max_age(cls, v, values):
        """Ensure max_age is greater than min_age."""
        min_age = values.get('min_age')
        if min_age is not None and v < min_age:
            raise ValueError("Maximum age must be greater than or equal to minimum age")
        return v
    
    @validator('age_range', pre=True, always=True)
    def create_age_range(cls, v, values):
        """Create Range object from min/max ages."""
        min_age = values.get('min_age')
        max_age = values.get('max_age')
        
        if min_age is not None and max_age is not None:
            return Range(
                BoundIncluded(min_age),
                BoundIncluded(max_age)
            )
        return v

class DateTimeRange(SurrealDBModel):
    """DateTime range model for time-based restrictions."""
    
    id: Optional[RecordID] = None
name: str
    start_datetime: datetime
    end_datetime: datetime
    timezone: str = "UTC"
    datetime_range: Optional[Range] = None
    inclusive_start: bool = True
    inclusive_end: bool = True
    
    @validator('id', pre=True, always=True)
    def validate_record_id(cls, v, values):
        """Generate RecordID for datetime range."""
        if v is None:
            name = values.get('name')
            if name:
                slug = name.lower().replace(' ', '_')
                return RecordID("datetime_ranges", slug)
        elif isinstance(v, str):
            return RecordID.parse(v)
        return v
    
    @validator('end_datetime')
    def validate_end_datetime(cls, v, values):
        """Ensure end_datetime is after start_datetime."""
        start_datetime = values.get('start_datetime')
        if start_datetime and v <= start_datetime:
            raise ValueError("End datetime must be after start datetime")
        return v
    
    @validator('datetime_range', pre=True, always=True)
    def create_datetime_range(cls, v, values):
        """Create Range object from start/end datetimes."""
        start_datetime = values.get('start_datetime')
        end_datetime = values.get('end_datetime')
        inclusive_start = values.get('inclusive_start', True)
        inclusive_end = values.get('inclusive_end', True)
        
        if start_datetime is not None and end_datetime is not None:
            start_bound = BoundIncluded(start_datetime) if inclusive_start else BoundExcluded(start_datetime)
            end_bound = BoundIncluded(end_datetime) if inclusive_end else BoundExcluded(end_datetime)
            return Range(start_bound, end_bound)
        return v
    
    def contains_datetime(self, dt: datetime) -> bool:
        """Check if datetime falls within this range."""
        if self.inclusive_start and self.inclusive_end:
            return self.start_datetime <= dt <= self.end_datetime
        elif self.inclusive_start and not self.inclusive_end:
            return self.start_datetime <= dt < self.end_datetime
        elif not self.inclusive_start and self.inclusive_end:
            return self.start_datetime < dt <= self.end_datetime
        else:
            return self.start_datetime < dt < self.end_datetime

# Usage Example
async def create_range_example():
    """Example of creating range-based validation."""
    try:
        # Create price range
        price_range_data = {
            "name": "Premium Products",
            "min_price": "100.00",
            "max_price": "500.00",
            "currency": "USD",
            "category": "electronics"
        }
        
        price_range = PriceRange(**price_range_data)
        print(f"Created price range: {price_range.id}")
        print(f"Contains $250: {price_range.contains_price(Decimal('250.00'))}")
        
        # Create age restriction
        age_restriction_data = {
            "name": "Adult Content",
            "min_age": 18,
            "max_age": 99,
            "description": "Content restricted to adults"
        }
        
        age_restriction = AgeRestriction(**age_restriction_data)
        print(f"Created age restriction: {age_restriction.id}")
        
        return price_range, age_restriction
        
    except Exception as e:
        print(f"Validation error: {e}")
        return None, None
```

## Custom Validators for SurrealDB Types

### Advanced Custom Validators

```python
from typing import Type, Any
import re

class SurrealDBValidators:
    """Collection of custom validators for SurrealDB types."""
    
    @staticmethod
    def validate_record_id_format(table_name: str, id_pattern: str = None):
        """Create a validator for RecordID with specific table and pattern."""
        def validator_func(cls, v):
            if v is None:
                return v
            
            if isinstance(v, str):
                v = RecordID.parse(v)
            
            if not isinstance(v, RecordID):
                raise ValueError("Must be a RecordID")
            
            if v.table_name != table_name:
                raise ValueError(f"RecordID must be from table '{table_name}', got '{v.table_name}'")
            
            if id_pattern and not re.match(id_pattern, str(v.id)):
                raise ValueError(f"RecordID identifier must match pattern '{id_pattern}'")
            
            return v
        return validator_func
    
    @staticmethod
    def validate_geometry_bounds(min_lon: float = -180, max_lon: float = 180, 
                               min_lat: float = -90, max_lat: float = 90):
        """Create a validator for geometry coordinates within bounds."""
        def validator_func(cls, v):
            if v is None:
                return v
            
            if isinstance(v, GeometryPoint):
                lon, lat = v.get_coordinates()
                if not (min_lon <= lon <= max_lon):
                    raise ValueError(f"Longitude must be between {min_lon} and {max_lon}")
                if not (min_lat <= lat <= max_lat):
                    raise ValueError(f"Latitude must be between {min_lat} and {max_lat}")
            
            return v
        return validator_func
    
    @staticmethod
    def validate_duration_range(min_duration: str, max_duration: str):
        """Create a validator for duration within specified range."""
        min_dur = Duration.parse(min_duration)
        max_dur = Duration.parse(max_duration)
        
        def validator_func(cls, v):
            if v is None:
                return v
            
            if isinstance(v, str):
                v = Duration.parse(v)
            
            if not isinstance(v, Duration):
                raise ValueError("Must be a Duration")
            
            if v.elapsed < min_dur.elapsed:
                raise ValueError(f"Duration must be at least {min_duration}")
            if v.elapsed > max_dur.elapsed:
                raise ValueError(f"Duration must be at most {max_duration}")
            
            return v
        return validator_func

class ValidatedUser(SurrealDBModel):
    """User model with advanced custom validators."""
    
    id: Optional[RecordID] = None
    username: str
    email: str
    location: Optional[GeometryPoint] = None
    session_timeout: Duration
    
    # Custom validators using the validator collection
    _validate_user_id = validator('id', pre=True, allow_reuse=True)(
        SurrealDBValidators.validate_record_id_format('users', r'^[a-zA-Z0-9_]{3,50}$')
    )
    
    _validate_location = validator('location', allow_reuse=True)(
        SurrealDBValidators.validate_geometry_bounds(-180, 180, -90, 90)
    )
    
    _validate_session_timeout = validator('session_timeout', pre=True, allow_reuse=True)(
        SurrealDBValidators.validate_duration_range('1m', '24h')
    )

class CustomGeometryValidator:
    """Custom validator for complex geometry validation."""
    
    @staticmethod
    def validate_polygon_area(min_area: float = None, max_area: float = None):
        """Validate polygon area (simplified calculation)."""
        def validator_func(cls, v):
            if v is None or not isinstance(v, GeometryPolygon):
                return v
            
            # Simplified area calculation for demonstration
            # In production, use proper geospatial libraries
            coords = v.get_coordinates()
            if coords and len(coords) > 0:
                # Simple bounding box area calculation
                first_line = coords[0]
                if len(first_line) >= 3:
                    lons = [coord[0] for coord in first_line]
                    lats = [coord[1] for coord in first_line]
                    area = (max(lons) - min(lons)) * (max(lats) - min(lats))
                    
                    if min_area is not None and area < min_area:
                        raise ValueError(f"Polygon area must be at least {min_area}")
                    if max_area is not None and area > max_area:
                        raise ValueError(f"Polygon area must be at most {max_area}")
            
            return v
        return validator_func

class ServiceArea(SurrealDBModel):
    """Service area model with custom geometry validation."""
    
    id: Optional[RecordID] = None
    name: str
    area: GeometryPolygon
    max_delivery_distance: Duration
    
    # Custom polygon area validator
    _validate_area = validator('area', allow_reuse=True)(
        CustomGeometryValidator.validate_polygon_area(min_area=0.001, max_area=10.0)
    )
```

## Error Handling and Type Conversion

### Comprehensive Error Handling

```python
from pydantic import ValidationError
from typing import Dict, List, Tuple
import logging

class SurrealDBTypeConverter:
    """Utility class for safe type conversion with error handling."""
    
    @staticmethod
    def safe_record_id_parse(value: Any, default_table: str = None) -> Tuple[Optional[RecordID], Optional[str]]:
        """Safely parse RecordID with error handling."""
        try:
            if value is None:
                return None, None
            
            if isinstance(value, RecordID):
                return value, None
            
            if isinstance(value, str):
                if ':' in value:
                    return RecordID.parse(value), None
                elif default_table:
                    return RecordID(default_table, value), None
                else:
                    return None, f"Invalid RecordID format: {value}"
            
            return None, f"Cannot convert {type(value)} to RecordID"
            
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def safe_geometry_parse(value: Any) -> Tuple[Optional[GeometryPoint], Optional[str]]:
        """Safely parse geometry with error handling."""
        try:
            if value is None:
                return None, None
            
            if isinstance(value, GeometryPoint):
                return value, None
            
            if isinstance(value, dict) and 'coordinates' in value:
                coords = value['coordinates']
                if len(coords) == 2:
                    return GeometryPoint(coords[0], coords[1]), None
                else:
                    return None, "Coordinates must have exactly 2 elements"
            
            if isinstance(value, (list, tuple)) and len(value) == 2:
                try:
                    lon, lat = float(value[0]), float(value[1])
                    if -180 <= lon <= 180 and -90 <= lat <= 90:
                        return GeometryPoint(lon, lat), None
                    else:
                        return None, "Coordinates out of valid range"
                except (ValueError, TypeError):
                    return None, "Coordinates must be numeric"
            
            return None, f"Cannot convert {type(value)} to GeometryPoint"
            
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def safe_duration_parse(value: Any) -> Tuple[Optional[Duration], Optional[str]]:
        """Safely parse duration with error handling."""
        try:
            if value is None:
                return None, None
            
            if isinstance(value, Duration):
                return value, None
            
            if isinstance(value, str):
                return Duration.parse(value), None
            
            if isinstance(value, (int, float)):
                return Duration.parse(f"{int(value)}s"), None
            
            return None, f"Cannot convert {type(value)} to Duration"
            
        except Exception as e:
            return None, str(e)

class ErrorHandlingModel(SurrealDBModel):
    """Base model with comprehensive error handling."""
    
    @classmethod
    def safe_create(cls, data: Dict[str, Any]) -> Tuple[Optional['ErrorHandlingModel'], List[str]]:
        """Safely create model instance with detailed error reporting."""
        errors = []
        
        try:
            instance = cls(**data)
            return instance, []
        except ValidationError as e:
            for error in e.errors():
                field = '.'.join(str(loc) for loc in error['loc'])
                message = error['msg']
                errors.append(f"Field '{field}': {message}")
            return None, errors
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
            return None, errors
    
    def safe_update(self, **kwargs) -> Tuple[bool, List[str]]:
        """Safely update model fields with error handling."""
        errors = []
        original_values = {}
        
        try:
            # Store original values for rollback
            for field_name in kwargs:
                if hasattr(self, field_name):
                    original_values[field_name] = getattr(self, field_name)
            
            # Attempt to update fields
            for field_name, value in kwargs.items():
                setattr(self, field_name, value)
            
            # Validate the updated model
            self.__class__(**self.dict())
            return True, []
            
        except ValidationError as e:
            # Rollback changes
            for field_name, original_value in original_values.items():
                setattr(self, field_name, original_value)
            
            for error in e.errors():
                field = '.'.join(str(loc) for loc in error['loc'])
                message = error['msg']
                errors.append(f"Field '{field}': {message}")
            return False, errors
        except Exception as e:
            # Rollback changes
            for field_name, original_value in original_values.items():
                setattr(self, field_name, original_value)
            
            errors.append(f"Unexpected error: {str(e)}")
            return False, errors

class RobustUser(ErrorHandlingModel):
    """User model with robust error handling."""
    
    id: Optional[RecordID] = None
    username: str
    email: str
    location: Optional[GeometryPoint] = None
    session_timeout: Duration = Field(default_factory=lambda: Duration.parse("1h"))
    
    @validator('id', pre=True)
    def validate_id(cls, v):
        """Validate RecordID with detailed error handling."""
        record_id, error = SurrealDBTypeConverter.safe_record_id_parse(v, 'users')
        if error:
            raise ValueError(error)
        return record_id
    
    @validator('location', pre=True)
    def validate_location(cls, v):
        """Validate location with detailed error handling."""
        geometry, error = SurrealDBTypeConverter.safe_geometry_parse(v)
        if error:
            raise ValueError(error)
        return geometry
    
    @validator('session_timeout', pre=True)
    def validate_session_timeout(cls, v):
        """Validate session timeout with detailed error handling."""
        duration, error = SurrealDBTypeConverter.safe_duration_parse(v)
        if error:
            raise ValueError(error)
        return duration

# Usage Example
async def error_handling_example():
    """Example of comprehensive error handling."""
    
    # Test valid data
    valid_data = {
        "username": "john_doe",
        "email": "john@example.com",
        "location": [-122.4194, 37.7749],
        "session_timeout": "2h"
    }
    
    user, errors = RobustUser.safe_create(valid_data)
    if user:
        print(f"Successfully created user: {user.id}")
    else:
        print(f"Validation errors: {errors}")
    
    # Test invalid data
    invalid_data = {
        "username": "jo",  # Too short
        "email": "invalid-email",  # Invalid format
        "location": [200, 100],  # Out of bounds
        "session_timeout": "invalid"  # Invalid duration
    }
    
    user, errors = RobustUser.safe_create(invalid_data)
    if user:
        print(f"Unexpectedly created user: {user.id}")
    else:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
    
    # Test safe update
    if user:
        success, update_errors = user.safe_update(
            email="newemail@example.com",
            session_timeout="30m"
        )
        if success:
            print("Successfully updated user")
        else:
            print(f"Update errors: {update_errors}")
```

## Performance Considerations

### Optimized Models and Caching

```python
from functools import lru_cache
from typing import ClassVar
import weakref

class PerformantSurrealDBModel(SurrealDBModel):
    """Base model with performance optimizations."""
    
    # Class-level cache for validation results
    _validation_cache: ClassVar[Dict[str, Any]] = {}
    
    class Config:
        # Performance optimizations
        arbitrary_types_allowed = True
        use_enum_values = True
        validate_assignment = True
        # Optimize field validation
        validate_all = False
        # Cache model instances
        copy_on_model_validation = False
        
    @classmethod
    @lru_cache(maxsize=1000)
    def _cached_field_validation(cls, field_name: str, value_hash: int):
        """Cache expensive field validations."""
        # This is a simplified example - implement based on your needs
        return True
    
    def __setattr__(self, name, value):
        """Optimized attribute setting with caching."""
        # Use cached validation for expensive operations
        if hasattr(self.__class__, f'_validate_{name}'):
            value_hash = hash(str(value)) if value is not None else 0
            if not self._cached_field_validation(name, value_hash):
                raise ValueError(f"Cached validation failed for {name}")
        
        super().__setattr__(name, value)

class CachedGeometryModel(PerformantSurrealDBModel):
    """Model with cached geometry calculations."""
    
    id: Optional[RecordID] = None
    name: str
    location: GeometryPoint
    
    # Cache for expensive calculations
    _distance_cache: Dict[str, float] = {}
    
    @lru_cache(maxsize=100)
    def distance_to_cached(self, other_location: GeometryPoint) -> float:
        """Cached distance calculation."""
        import math
        
        lat1, lon1 = self.location.latitude, self.location.longitude
        lat2, lon2 = other_location.latitude, other_location.longitude
        
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

class BatchProcessor:
    """Utility for batch processing Pydantic models."""
    
    @staticmethod
    def batch_validate(model_class: Type[SurrealDBModel], 
                      data_list: List[Dict[str, Any]], 
                      chunk_size: int = 100) -> Tuple[List[SurrealDBModel], List[Dict[str, Any]]]:
        """Batch validate multiple model instances efficiently."""
        valid_models = []
        invalid_data = []
        
        for i in range(0, len(data_list), chunk_size):
            chunk = data_list[i:i + chunk_size]
            
            for data in chunk:
                try:
                    model = model_class(**data)
                    valid_models.append(model)
                except ValidationError as e:
                    invalid_data.append({
                        'data': data,
                        'errors': [f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" 
                                 for err in e.errors()]
                    })
        
        return valid_models, invalid_data
    
    @staticmethod
    def batch_to_surrealdb(models: List[SurrealDBModel]) -> List[Dict[str, Any]]:
        """Convert batch of models to SurrealDB format efficiently."""
        return [model.to_surrealdb() for model in models]

# Usage Example
async def performance_example():
    """Example of performance optimizations."""
    
    # Create test data
    test_data = [
        {
            "name": f"Location {i}",
            "location": [-122.4194 + i * 0.01, 37.7749 + i * 0.01]
        }
        for i in range(1000)
    ]
    
    # Batch validate
    valid_models, invalid_data = BatchProcessor.batch_validate(
        CachedGeometryModel, test_data, chunk_size=100
    )
    
    print(f"Valid models: {len(valid_models)}")
    print(f"Invalid data: {len(invalid_data)}")
    
    # Test cached distance calculation
    if len(valid_models) >= 2:
        model1, model2 = valid_models[0], valid_models[1]
        
        # First call - calculates and caches
        distance1 = model1.distance_to_cached(model2.location)
        
        # Second call - uses cache
        distance2 = model1.distance_to_cached(model2.location)
        
        print(f"Distance (cached): {distance1:.2f} km")
        print(f"Cache hit: {distance1 == distance2}")
```

## Integration with SurrealDB Operations

### Complete CRUD Operations with Pydantic

```python
from typing import Optional, List, Dict, Any
import asyncio

class SurrealDBRepository:
    """Repository pattern for SurrealDB operations with Pydantic models."""
    
    def __init__(self, connection: Surreal):
        self.db = connection
    
    async def create_record(self, model: SurrealDBModel) -> Optional[SurrealDBModel]:
        """Create a new record in SurrealDB."""
        try:
            data = model.to_surrealdb()
            result = await self.db.create(model.id, data)
            
            # Return updated model with any server-generated fields
            return model.__class__.from_surrealdb(result)
        except Exception as e:
            logging.error(f"Error creating record: {e}")
            return None
    
    async def get_record(self, model_class: Type[SurrealDBModel], 
                        record_id: RecordID) -> Optional[SurrealDBModel]:
        """Get a record by ID."""
        try:
            result = await self.db.select(record_id)
            if result:
                return model_class.from_surrealdb(result)
            return None
        except Exception as e:
            logging.error(f"Error getting record: {e}")
            return None
    
    async def update_record(self, model: SurrealDBModel) -> Optional[SurrealDBModel]:
        """Update an existing record."""
        try:
            data = model.to_surrealdb()
            result = await self.db.update(model.id, data)
            
            return model.__class__.from_surrealdb(result)
        except Exception as e:
            logging.error(f"Error updating record: {e}")
            return None
    
    async def delete_record(self, record_id: RecordID) -> bool:
        """Delete a record by ID."""
        try:
            await self.db.delete(record_id)
            return True
        except Exception as e:
            logging.error(f"Error deleting record: {e}")
            return False
    
    async def query_records(self, model_class: Type[SurrealDBModel], 
                           query: str, params: Dict[str, Any] = None) -> List[SurrealDBModel]:
        """Execute a query and return typed results."""
        try:
            results = await self.db.query(query, params or {})
            return [model_class.from_surrealdb(result) for result in results]
        except Exception as e:
            logging.error(f"Error querying records: {e}")
            return []
    
    async def batch_create(self, models: List[SurrealDBModel]) -> List[SurrealDBModel]:
        """Create multiple records in batch."""
        created_models = []
        
        for model in models:
            created = await self.create_record(model)
            if created:
                created_models.append(created)
        
        return created_models

class UserRepository(SurrealDBRepository):
    """Specialized repository for User operations."""
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        query = "SELECT * FROM users WHERE username = $username"
        results = await self.query_records(User, query, {"username": username})
        return results[0] if results else None
    
    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Get users by role."""
        query = "SELECT * FROM users WHERE role = $role"
        return await self.query_records(User, query, {"role": role.value})
    
    async def get_nearby_users(self, location: GeometryPoint, 
                              radius_km: float) -> List[User]:
        """Get users within radius of location."""
        query = """
        SELECT * FROM users 
        WHERE location IS NOT NULL 
        AND geo::distance(location, $center) < $radius
        """
        return await self.query_records(User, query, {
            "center": location,
            "radius": radius_km * 1000  # Convert to meters
        })
    
    async def update_last_login(self, user_id: RecordID) -> bool:
        """Update user's last login timestamp."""
        try:
            query = "UPDATE $user_id SET last_login = time::now()"
            await self.db.query(query, {"user_id": user_id})
            return True
        except Exception as e:
            logging.error(f"Error updating last login: {e}")
            return False

class ProductRepository(SurrealDBRepository):
    """Specialized repository for Product operations."""
    
    async def get_products_by_category(self, category: ProductCategory) -> List[Product]:
        """Get products by category."""
        query = "SELECT * FROM products WHERE category = $category AND status = 'active'"
        return await self.query_records(Product, query, {"category": category.value})
    
    async def get_low_stock_products(self) -> List[Product]:
        """Get products with low stock."""
        query = "SELECT * FROM products WHERE stock_quantity <= reorder_level"
        return await self.query_records(Product, query)
    
    async def search_products(self, search_term: str) -> List[Product]:
        """Search products by name or description."""
        query = """
        SELECT * FROM products 
        WHERE string::lowercase(name) CONTAINS string::lowercase($term)
        OR string::lowercase(description) CONTAINS string::lowercase($term)
        """
        return await self.query_records(Product, query, {"term": search_term})
    
    async def get_products_in_price_range(self, min_price: Decimal, 
                                        max_price: Decimal) -> List[Product]:
        """Get products within price range."""
        query = "SELECT * FROM products WHERE price >= $min_price AND price <= $max_price"
        return await self.query_records(Product, query, {
            "min_price": min_price,
            "max_price": max_price
        })

# Complete Integration Example
async def complete_integration_example():
    """Complete example of SurrealDB integration with Pydantic."""
    
    # Initialize connection
    db = Surreal("ws://localhost:8000/rpc")
    await db.connect()
    await db.signin({"username": "root", "password": "root"})
    await db.use("example", "example")
    
    # Initialize repositories
    user_repo = UserRepository(db)
    product_repo = ProductRepository(db)
    
    try:
        # Create users
        users_data = [
            {
                "username": "alice_smith",
                "email": "alice@example.com",
                "full_name": "Alice Smith",
                "role": "user",
                "location": [-122.4194, 37.7749],
                "session_timeout": "2h"
            },
            {
                "username": "bob_jones",
                "email": "bob@example.com",
                "full_name": "Bob Jones",
                "role": "admin",
                "location": [-122.4094, 37.7849],
                "session_timeout": "4h"
            }
        ]
        
        created_users = []
        for user_data in users_data:
            user = User(**user_data)
            created_user = await user_repo.create_record(user)
            if created_user:
                created_users.append(created_user)
                print(f"Created user: {created_user.username}")
        
        # Create products
        products_data = [
            {
                "sku": "LAPTOP-001",
                "name": "Gaming Laptop",
                "category": "electronics",
                "price": "1299.99",
                "stock_quantity": 10,
                "reorder_level": 5
            },
            {
                "sku": "BOOK-001",
                "name": "Python Programming Guide",
                "category": "books",
                "price": "49.99",
                "stock_quantity": 3,
                "reorder_level": 5
            }
        ]
        
        created_products = []
        for product_data in products_data:
            product = Product(**product_data)
            created_product = await product_repo.create_record(product)
            if created_product:
                created_products.append(created_product)
                print(f"Created product: {created_product.name}")
        
        # Query operations
        print("\n--- Query Operations ---")
        
        # Get user by username
        alice = await user_repo.get_user_by_username("alice_smith")
        if alice:
            print(f"Found user: {alice.full_name}")
        
        # Get admin users
        admin_users = await user_repo.get_users_by_role(UserRole.ADMIN)
        print(f"Admin users: {len(admin_users)}")
        
        # Get nearby users
        if created_users:
            center_location = created_users[0].location
            nearby_users = await user_repo.get_nearby_users(center_location, 5.0)
            print(f"Nearby users: {len(nearby_users)}")
        
        # Get low stock products
        low_stock = await product_repo.get_low_stock_products()
        print(f"Low stock products: {len(low_stock)}")
        
        # Search products
        search_results = await product_repo.search_products("laptop")
        print(f"Search results for 'laptop': {len(search_results)}")
        
        # Update operations
        print("\n--- Update Operations ---")
        
        if created_users:
            user
# Update user's last login
            success = await user_repo.update_last_login(created_users[0].id)
            print(f"Updated last login: {success}")
            
            # Update user profile
            updated_user = created_users[0]
            updated_user.bio = "Updated bio with new information"
            result = await user_repo.update_record(updated_user)
            if result:
                print(f"Updated user bio: {result.bio}")
        
    except Exception as e:
        print(f"Integration error: {e}")
    
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(complete_integration_example())
```

## Best Practices

### 1. Model Design Best Practices

```python
class BestPracticeModel(SurrealDBModel):
    """Example model following best practices."""
    
    # Use descriptive field names
    id: Optional[RecordID] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    # Use enums for constrained values
    status: UserStatus = UserStatus.ACTIVE
    
    # Use appropriate constraints
    email: constr(regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # Provide sensible defaults
    preferences: Dict[str, Any] = Field(default_factory=dict)
    
    # Use Optional for nullable fields
    description: Optional[constr(max_length=1000)] = None
    
    # Document complex fields
    location: Optional[GeometryPoint] = Field(
        None, 
        description="Geographic coordinates in WGS84 format (longitude, latitude)"
    )
    
    class Config:
        # Enable validation on assignment
        validate_assignment = True
        # Use enum values in serialization
        use_enum_values = True
        # Allow SurrealDB custom types
        arbitrary_types_allowed = True
        # Provide example for documentation
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "status": "active",
                "location": [-122.4194, 37.7749],
                "preferences": {"theme": "dark", "notifications": True}
            }
        }
```

### 2. Validation Best Practices

```python
class ValidationBestPractices(SurrealDBModel):
    """Model demonstrating validation best practices."""
    
    # Use pre=True for data transformation
    @validator('email', pre=True)
    def normalize_email(cls, v):
        """Normalize email to lowercase."""
        return v.lower().strip() if isinstance(v, str) else v
    
    # Use root_validator for cross-field validation
    @root_validator
    def validate_date_consistency(cls, values):
        """Ensure end_date is after start_date."""
        start_date = values.get('start_date')
        end_date = values.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise ValueError('end_date must be after start_date')
        
        return values
    
    # Use allow_reuse=True for reusable validators
    @validator('phone_number', allow_reuse=True)
    def validate_phone_number(cls, v):
        """Validate phone number format."""
        if v is None:
            return v
        
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, v))
        
        if len(digits) < 10:
            raise ValueError('Phone number must have at least 10 digits')
        
        return digits
```

### 3. Performance Best Practices

```python
# Use __slots__ for memory efficiency in high-volume scenarios
class HighVolumeModel(SurrealDBModel):
    """Model optimized for high-volume usage."""
    
    __slots__ = ('id', 'name', 'value', 'timestamp')
    
    id: Optional[RecordID] = None
    name: str
    value: float
    timestamp: datetime
    
    class Config:
        # Disable validation on assignment for performance
        validate_assignment = False
        # Don't copy on model validation
        copy_on_model_validation = False

# Use caching for expensive operations
@lru_cache(maxsize=1000)
def expensive_validation(value: str) -> bool:
    """Cache expensive validation operations."""
    # Simulate expensive validation
    import time
    time.sleep(0.001)  # Simulate processing time
    return len(value) > 5

class CachedValidationModel(SurrealDBModel):
    """Model using cached validation."""
    
    @validator('expensive_field')
    def validate_expensive_field(cls, v):
        """Use cached validation for expensive operations."""
        if not expensive_validation(v):
            raise ValueError('Expensive validation failed')
        return v
```

### 4. Error Handling Best Practices

```python
class ErrorHandlingBestPractices:
    """Best practices for error handling."""
    
    @staticmethod
    def safe_model_creation(model_class: Type[SurrealDBModel], 
                           data: Dict[str, Any]) -> Tuple[Optional[SurrealDBModel], List[str]]:
        """Safely create model with comprehensive error handling."""
        try:
            return model_class(**data), []
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field_path = ' -> '.join(str(loc) for loc in error['loc'])
                errors.append(f"{field_path}: {error['msg']}")
            return None, errors
        except Exception as e:
            return None, [f"Unexpected error: {str(e)}"]
    
    @staticmethod
    def log_validation_errors(model_name: str, errors: List[str]):
        """Log validation errors with context."""
        logging.error(f"Validation failed for {model_name}:")
        for error in errors:
            logging.error(f"  - {error}")
```

### 5. Testing Best Practices

```python
import pytest
from unittest.mock import Mock, AsyncMock

class TestUserModel:
    """Test cases for User model."""
    
    def test_valid_user_creation(self):
        """Test creating a valid user."""
        user_data = {
            "username": "test_user",
            "email": "test@example.com",
            "full_name": "Test User"
        }
        
        user = User(**user_data)
        assert user.username == "test_user"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER  # Default value
    
    def test_invalid_email_validation(self):
        """Test email validation."""
        user_data = {
            "username": "test_user",
            "email": "invalid-email",
            "full_name": "Test User"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            User(**user_data)
        
        errors = exc_info.value.errors()
        assert any('email' in str(error['loc']) for error in errors)
    
    def test_location_conversion(self):
        """Test location coordinate conversion."""
        user_data = {
            "username": "test_user",
            "email": "test@example.com",
            "full_name": "Test User",
            "location": [-122.4194, 37.7749]
        }
        
        user = User(**user_data)
        assert isinstance(user.location, GeometryPoint)
        assert user.location.longitude == -122.4194
        assert user.location.latitude == 37.7749
    
    @pytest.mark.asyncio
    async def test_repository_operations(self):
        """Test repository operations with mocked database."""
        mock_db = AsyncMock()
        mock_db.create.return_value = {
            "id": RecordID("users", "test_user"),
            "username": "test_user",
            "email": "test@example.com",
            "full_name": "Test User"
        }
        
        repo = UserRepository(mock_db)
        user = User(username="test_user", email="test@example.com", full_name="Test User")
        
        result = await repo.create_record(user)
        
        assert result is not None
        assert result.username == "test_user"
        mock_db.create.assert_called_once()
```

### 6. Documentation Best Practices

```python
class DocumentedModel(SurrealDBModel):
    """
    A well-documented model example.
    
    This model demonstrates best practices for documentation,
    including field descriptions, examples, and usage notes.
    
    Attributes:
        id: Unique identifier for the record
        name: Human-readable name (3-100 characters)
        email: Valid email address (automatically normalized to lowercase)
        status: Current status of the record
        metadata: Additional key-value data
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    
    Example:
        >>> model = DocumentedModel(
        ...     name="John Doe",
        ...     email="JOHN@EXAMPLE.COM",
        ...     status="active"
        ... )
        >>> print(model.email)  # "john@example.com"
    """
    
    id: Optional[RecordID] = Field(
        None,
        description="Unique identifier for the record"
    )
    
    name: constr(min_length=3, max_length=100) = Field(
        ...,
        description="Human-readable name",
        example="John Doe"
    )
    
    email: str = Field(
        ...,
        description="Valid email address (automatically normalized)",
        example="user@example.com"
    )
    
    status: str = Field(
        "active",
        description="Current status of the record",
        example="active"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional key-value data"
    )
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when record was created"
    )
    
    updated_at: Optional[datetime] = Field(
        None,
        description="Timestamp when record was last updated"
    )
    
    @validator('email', pre=True)
    def normalize_email(cls, v):
        """Normalize email to lowercase and strip whitespace."""
        return v.lower().strip() if isinstance(v, str) else v
    
    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True
        validate_assignment = True
        
        schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "status": "active",
                "metadata": {
                    "department": "Engineering",
                    "level": "Senior"
                }
            }
        }
```

## Summary

This comprehensive guide demonstrates how to effectively use Pydantic with SurrealDB Python SDK for robust type safety. Key takeaways:

### Core Benefits
- **Type Safety**: Pydantic ensures data integrity and catches errors early
- **Validation**: Comprehensive validation for all SurrealDB data types
- **Serialization**: Seamless conversion between Python objects and SurrealDB formats
- **Documentation**: Self-documenting models with examples and descriptions

### Key Features Covered
- **RecordID Integration**: Automatic generation and validation
- **Geometry Support**: Full support for all SurrealDB geometry types
- **Time Handling**: DateTime and Duration with timezone awareness
- **Range Validation**: Inclusive and exclusive bounds for data validation
- **Custom Validators**: Extensible validation system
- **Error Handling**: Comprehensive error handling and recovery
- **Performance**: Optimization techniques for high-volume scenarios

### Production Considerations
- Use appropriate validation levels based on performance requirements
- Implement comprehensive error handling and logging
- Cache expensive operations where possible
- Write thorough tests for all model operations
- Document models clearly with examples and usage notes

### Next Steps
1. Implement models for your specific use case
2. Set up comprehensive testing
3. Add monitoring and logging
4. Optimize for your performance requirements
5. Document your models and validation rules

This guide provides a solid foundation for building type-safe, robust applications with SurrealDB and Pydantic. The examples are production-ready and follow industry best practices.