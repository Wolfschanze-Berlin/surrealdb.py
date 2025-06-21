---
sidebar_position: 5
---

# Advanced SurrealDB Queries

This section demonstrates advanced SurrealDB query patterns and techniques for complex data operations in the FastAPI authentication system, showcasing the full power of SurrealDB's query language.

## Complex Relationship Queries

### Multi-Level Relationship Traversal

```python
# app/services/advanced_query_service.py
from surrealdb import Surreal
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class AdvancedQueryService:
    def __init__(self, db: Surreal):
        self.db = db
    
    async def get_users_with_complete_profile_data(self) -> List[Dict]:
        """
        Get users with their profiles and calculated fields
        Demonstrates relationship traversal and computed fields
        """
        
        result = await self.db.query("""
            SELECT *,
                   profile.* AS profile_data,
                   (CASE 
                    WHEN profile.first_name IS NOT NULL AND profile.last_name IS NOT NULL 
                    THEN string::concat(profile.first_name, ' ', profile.last_name)
                    ELSE profile.first_name OR profile.last_name OR username
                    END) AS display_name,
                   (CASE 
                    WHEN profile.date_of_birth IS NOT NULL 
                    THEN math::floor(time::diff(profile.date_of_birth, time::now()) / duration::from::years(1))
                    ELSE NULL
                    END) AS age,
                   (SELECT count() FROM session WHERE user = $parent.id AND expires_at > time::now()) AS active_sessions,
                   time::diff(created_at, time::now()) AS account_age
            FROM user 
            WHERE is_active = true
            ORDER BY created_at DESC
        """)
        
        return result[0]["result"] if result and result[0]["result"] else []
    
    async def get_user_activity_summary(self, user_id: str) -> Dict:
        """
        Get comprehensive user activity summary
        Demonstrates aggregation across multiple tables
        """
        
        result = await self.db.query("""
            LET $user_record = type::thing('user', $user_id);
            
            SELECT 
                $user_record.username AS username,
                $user_record.email AS email,
                $user_record.created_at AS account_created,
                (SELECT count() FROM session WHERE user = $user_record) AS total_sessions,
                (SELECT count() FROM session WHERE user = $user_record AND expires_at > time::now()) AS active_sessions,
                (SELECT created_at FROM session WHERE user = $user_record ORDER BY created_at DESC LIMIT 1)[0] AS last_login,
                (SELECT count() FROM profile WHERE user = $user_record) AS has_profile,
                time::diff($user_record.created_at, time::now()) AS account_age_duration
            FROM $user_record
        """, {"user_id": user_id})
        
        return result[0]["result"][0] if result and result[0]["result"] else {}
```

### Conditional Queries with Dynamic Filtering

```python
async def advanced_user_search(self, 
                             search_params: Dict) -> Dict:
    """
    Advanced user search with dynamic conditions
    Demonstrates conditional query building
    """
    
    # Base query parts
    select_fields = [
        "*",
        "profile.first_name",
        "profile.last_name", 
        "profile.bio",
        "(SELECT count() FROM session WHERE user = $parent.id AND expires_at > time::now()) AS active_sessions"
    ]
    
    conditions = ["is_active = true"]
    params = {}
    
    # Dynamic condition building
    if search_params.get("search_term"):
        conditions.append("""
            (string::lowercase(username) CONTAINS string::lowercase($search_term) 
             OR string::lowercase(email) CONTAINS string::lowercase($search_term)
             OR string::lowercase(profile.first_name) CONTAINS string::lowercase($search_term)
             OR string::lowercase(profile.last_name) CONTAINS string::lowercase($search_term))
        """)
        params["search_term"] = search_params["search_term"]
    
    if search_params.get("is_admin") is not None:
        conditions.append("is_admin = $is_admin")
        params["is_admin"] = search_params["is_admin"]
    
    if search_params.get("has_profile"):
        conditions.append("(SELECT count() FROM profile WHERE user = $parent.id) > 0")
    
    if search_params.get("min_sessions"):
        conditions.append("(SELECT count() FROM session WHERE user = $parent.id) >= $min_sessions")
        params["min_sessions"] = search_params["min_sessions"]
    
    if search_params.get("created_after"):
        conditions.append("created_at > $created_after")
        params["created_after"] = search_params["created_after"]
    
    if search_params.get("age_range"):
        age_min, age_max = search_params["age_range"]
        conditions.append("""
            profile.date_of_birth IS NOT NULL 
            AND profile.date_of_birth <= time::now() - duration::from::years($age_min)
            AND profile.date_of_birth >= time::now() - duration::from::years($age_max)
        """)
        params["age_min"] = age_min
        params["age_max"] = age_max
    
    # Build final query
    select_clause = "SELECT " + ", ".join(select_fields)
    where_clause = " AND ".join(conditions)
    
    query = f"""
        {select_clause}
        FROM user 
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT 100
    """
    
    result = await self.db.query(query, params)
    
    return {
        "results": result[0]["result"] if result and result[0]["result"] else [],
        "search_params": search_params,
        "total_found": len(result[0]["result"]) if result and result[0]["result"] else 0
    }
```

## Aggregation and Analytics Queries

### User Engagement Analytics

```python
async def get_user_engagement_analytics(self, days: int = 30) -> Dict:
    """
    Comprehensive user engagement analytics
    Demonstrates complex aggregations and time-based analysis
    """
    
    result = await self.db.query("""
        LET $start_date = time::now() - duration::from::days($days);
        
        -- Daily registration trends
        LET $daily_registrations = (
            SELECT 
                time::format(created_at, '%Y-%m-%d') AS date,
                count() AS registrations
            FROM user 
            WHERE created_at >= $start_date
            GROUP BY date
            ORDER BY date
        );
        
        -- Session activity patterns
        LET $session_patterns = (
            SELECT 
                time::format(created_at, '%H') AS hour,
                count() AS sessions,
                count(DISTINCT user) AS unique_users
            FROM session 
            WHERE created_at >= $start_date
            GROUP BY hour
            ORDER BY hour
        );
        
        -- User activity segments
        LET $user_segments = (
            SELECT 
                (CASE 
                    WHEN session_count = 0 THEN 'inactive'
                    WHEN session_count <= 5 THEN 'low_activity'
                    WHEN session_count <= 20 THEN 'medium_activity'
                    ELSE 'high_activity'
                END) AS segment,
                count() AS user_count
            FROM (
                SELECT 
                    id,
                    (SELECT count() FROM session WHERE user = $parent.id AND created_at >= $start_date) AS session_count
                FROM user 
                WHERE is_active = true
            )
            GROUP BY segment
        );
        
        -- Profile completion rates
        LET $profile_completion = (
            SELECT 
                count() AS total_users,
                count(profile.id IS NOT NULL) AS users_with_profile,
                count(profile.first_name IS NOT NULL) AS users_with_first_name,
                count(profile.last_name IS NOT NULL) AS users_with_last_name,
                count(profile.bio IS NOT NULL AND profile.bio != '') AS users_with_bio,
                count(profile.avatar_url IS NOT NULL AND profile.avatar_url != '') AS users_with_avatar,
                count(profile.date_of_birth IS NOT NULL) AS users_with_dob
            FROM user
            LEFT JOIN profile ON profile.user = user.id
            WHERE user.is_active = true
        );
        
        SELECT {
            period_days: $days,
            daily_registrations: $daily_registrations,
            session_patterns: $session_patterns,
            user_segments: $user_segments,
            profile_completion: $profile_completion[0],
            generated_at: time::now()
        } AS analytics
    """, {"days": days})
    
    return result[0]["result"][0]["analytics"] if result and result[0]["result"] else {}
```

### Cohort Analysis

```python
async def get_user_cohort_analysis(self, months: int = 12) -> Dict:
    """
    User cohort analysis showing retention patterns
    Demonstrates advanced date manipulation and cohort calculations
    """
    
    result = await self.db.query("""
        LET $start_date = time::now() - duration::from::days($months * 30);
        
        -- Create cohorts based on registration month
        LET $cohorts = (
            SELECT 
                time::format(created_at, '%Y-%m') AS cohort_month,
                count() AS cohort_size,
                array::group(id) AS user_ids
            FROM user 
            WHERE created_at >= $start_date AND is_active = true
            GROUP BY cohort_month
            ORDER BY cohort_month
        );
        
        -- Calculate retention for each cohort
        LET $retention_data = (
            FOR $cohort IN $cohorts {
                LET $cohort_users = $cohort.user_ids;
                LET $cohort_month = $cohort.cohort_month;
                
                -- Calculate retention for each subsequent month
                LET $retention_months = (
                    FOR $month_offset IN [1, 2, 3, 6, 12] {
                        LET $target_month = time::format(
                            time::add(time::parse($cohort_month, '%Y-%m'), duration::from::days($month_offset * 30)),
                            '%Y-%m'
                        );
                        
                        LET $active_users = (
                            SELECT count() AS active_count
                            FROM session 
                            WHERE user IN $cohort_users 
                            AND time::format(created_at, '%Y-%m') = $target_month
                        )[0].active_count;
                        
                        SELECT {
                            month_offset: $month_offset,
                            target_month: $target_month,
                            active_users: $active_users,
                            retention_rate: math::round($active_users / $cohort.cohort_size * 100, 2)
                        }
                    }
                );
                
                SELECT {
                    cohort_month: $cohort_month,
                    cohort_size: $cohort.cohort_size,
                    retention_by_month: $retention_months
                }
            }
        );
        
        SELECT {
            analysis_period_months: $months,
            cohorts: $retention_data,
            generated_at: time::now()
        } AS cohort_analysis
    """, {"months": months})
    
    return result[0]["result"][0]["cohort_analysis"] if result and result[0]["result"] else {}
```

## Advanced Data Manipulation

### Bulk Operations with Transactions

```python
async def bulk_user_operations(self, operations: List[Dict]) -> Dict:
    """
    Perform bulk operations with transaction safety
    Demonstrates SurrealDB transaction handling
    """
    
    try:
        # Start transaction
        await self.db.query("BEGIN TRANSACTION")
        
        results = {
            "created": [],
            "updated": [],
            "deleted": [],
            "errors": []
        }
        
        for operation in operations:
            try:
                op_type = operation.get("type")
                op_data = operation.get("data", {})
                
                if op_type == "create_user":
                    result = await self.db.query("""
                        CREATE user CONTENT {
                            email: $email,
                            username: $username,
                            password_hash: $password_hash,
                            is_active: true,
                            is_admin: false,
                            created_at: time::now(),
                            updated_at: time::now()
                        }
                    """, op_data)
                    
                    if result and result[0]["result"]:
                        results["created"].append(result[0]["result"][0])
                
                elif op_type == "update_user":
                    user_id = op_data.pop("user_id")
                    op_data["updated_at"] = "time::now()"
                    
                    result = await self.db.query(f"""
                        UPDATE user:{user_id} MERGE $update_data
                    """, {"update_data": op_data})
                    
                    if result and result[0]["result"]:
                        results["updated"].append(result[0]["result"][0])
                
                elif op_type == "delete_user":
                    user_id = op_data["user_id"]
                    
                    # Soft delete with cascade to related records
                    result = await self.db.query(f"""
                        UPDATE user:{user_id} SET is_active = false, updated_at = time::now();
                        DELETE FROM session WHERE user = user:{user_id};
                    """)
                    
                    results["deleted"].append(user_id)
                
            except Exception as e:
                results["errors"].append({
                    "operation": operation,
                    "error": str(e)
                })
        
        # Commit transaction if no errors, rollback otherwise
        if results["errors"]:
            await self.db.query("CANCEL TRANSACTION")
            return {
                "success": False,
                "message": "Transaction rolled back due to errors",
                "results": results
            }
        else:
            await self.db.query("COMMIT TRANSACTION")
            return {
                "success": True,
                "message": "All operations completed successfully",
                "results": results
            }
            
    except Exception as e:
        await self.db.query("CANCEL TRANSACTION")
        return {
            "success": False,
            "message": f"Transaction failed: {str(e)}",
            "results": {"errors": [str(e)]}
        }
```

### Data Migration and Transformation

```python
async def migrate_user_data(self, migration_type: str) -> Dict:
    """
    Data migration operations
    Demonstrates data transformation and schema evolution
    """
    
    if migration_type == "add_user_preferences":
        # Add preferences field to existing users
        result = await self.db.query("""
            UPDATE user SET preferences = {
                theme: 'light',
                notifications: {
                    email: true,
                    push: false,
                    sms: false
                },
                privacy: {
                    profile_visibility: 'public',
                    show_email: false
                }
            } WHERE preferences IS NULL
        """)
        
        affected_count = len(result[0]["result"]) if result and result[0]["result"] else 0
        
        return {
            "migration": "add_user_preferences",
            "affected_users": affected_count,
            "completed_at": datetime.utcnow().isoformat()
        }
    
    elif migration_type == "normalize_profile_data":
        # Normalize profile data format
        result = await self.db.query("""
            FOR $profile IN (SELECT * FROM profile WHERE first_name IS NOT NULL OR last_name IS NOT NULL) {
                UPDATE $profile.id SET 
                    display_name = string::trim(string::concat(
                        $profile.first_name OR '', 
                        ' ', 
                        $profile.last_name OR ''
                    )),
                    name_updated_at = time::now()
            }
        """)
        
        return {
            "migration": "normalize_profile_data",
            "processed_profiles": len(result[0]["result"]) if result and result[0]["result"] else 0,
            "completed_at": datetime.utcnow().isoformat()
        }
    
    else:
        return {
            "error": f"Unknown migration type: {migration_type}"
        }
```

## Performance Optimization Queries

### Query Optimization with Indexes

```python
async def optimize_database_performance(self) -> Dict:
    """
    Database optimization operations
    Demonstrates index management and query optimization
    """
    
    # Create additional indexes for better performance
    optimization_queries = [
        # Composite indexes for common query patterns
        "DEFINE INDEX user_active_created ON TABLE user COLUMNS is_active, created_at",
        "DEFINE INDEX user_admin_active ON TABLE user COLUMNS is_admin, is_active",
        "DEFINE INDEX session_user_expires ON TABLE session COLUMNS user, expires_at",
        "DEFINE INDEX profile_user_created ON TABLE profile COLUMNS user, created_at",
        
        # Text search indexes
        "DEFINE INDEX user_search ON TABLE user COLUMNS username, email",
        "DEFINE INDEX profile_search ON TABLE profile COLUMNS first_name, last_name, bio",
        
        # Date-based indexes for analytics
        "DEFINE INDEX user_created_date ON TABLE user COLUMNS created_at",
        "DEFINE INDEX session_created_date ON TABLE session COLUMNS created_at",
    ]
    
    results = []
    for query in optimization_queries:
        try:
            await self.db.query(query)
            results.append({"query": query, "status": "success"})
        except Exception as e:
            results.append({"query": query, "status": "error", "error": str(e)})
    
    return {
        "optimization_results": results,
        "completed_at": datetime.utcnow().isoformat()
    }

async def get_query_performance_stats(self) -> Dict:
    """
    Get database performance statistics
    """
    
    result = await self.db.query("""
        -- Table statistics
        SELECT 
            'user' AS table_name,
            count() AS total_records,
            count(is_active = true) AS active_records,
            count(created_at > time::now() - 30d) AS recent_records
        FROM user
        UNION
        SELECT 
            'profile' AS table_name,
            count() AS total_records,
            count() AS active_records,
            count(created_at > time::now() - 30d) AS recent_records
        FROM profile
        UNION
        SELECT 
            'session' AS table_name,
            count() AS total_records,
            count(expires_at > time::now()) AS active_records,
            count(created_at > time::now() - 30d) AS recent_records
        FROM session;
        
        -- Index usage statistics (if available)
        INFO FOR DB;
    """)
    
    table_stats = result[0]["result"] if result and result[0]["result"] else []
    db_info = result[1]["result"] if result and len(result) > 1 else {}
    
    return {
        "table_statistics": table_stats,
        "database_info": db_info,
        "generated_at": datetime.utcnow().isoformat()
    }
```

## Real-time Query Patterns

### Live Query Implementations

```python
async def setup_live_queries(self) -> Dict:
    """
    Set up live queries for real-time monitoring
    Demonstrates SurrealDB's live query capabilities
    """
    
    live_queries = {}
    
    try:
        # Live query for user registrations
        user_live = await self.db.live("user", callback=self._handle_user_changes)
        live_queries["user_changes"] = str(user_live)
        
        # Live query for session activity
        session_live = await self.db.live("session", callback=self._handle_session_changes)
        live_queries["session_changes"] = str(session_live)
        
        # Live query for profile updates
        profile_live = await self.db.live("profile", callback=self._handle_profile_changes)
        live_queries["profile_changes"] = str(profile_live)
        
        return {
            "live_queries": live_queries,
            "status": "active",
            "setup_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "error": f"Failed to setup live queries: {str(e)}",
            "status": "failed"
        }

async def _handle_user_changes(self, change):
    """Handle user table changes"""
    print(f"User change detected: {change['action']} - {change.get('result', {}).get('username', 'Unknown')}")

async def _handle_session_changes(self, change):
    """Handle session table changes"""
    print(f"Session change detected: {change['action']} - User: {change.get('result', {}).get('user', 'Unknown')}")

async def _handle_profile_changes(self, change):
    """Handle profile table changes"""
    print(f"Profile change detected: {change['action']} - Profile ID: {change.get('result', {}).get('id', 'Unknown')}")
```

## Custom Functions and Procedures

### Stored Procedures in SurrealDB

```python
async def define_custom_functions(self) -> Dict:
    """
    Define custom functions for reusable query logic
    """
    
    functions = [
        # Function to calculate user engagement score
        """
        DEFINE FUNCTION fn::user_engagement_score($user_id: record) {
            LET $sessions = (SELECT count() FROM session WHERE user = $user_id AND created_at > time::now() - 30d);
            LET $profile_completeness = (
                SELECT 
                    (count(first_name IS NOT NULL) + 
                     count(last_name IS NOT NULL) + 
                     count(bio IS NOT NULL AND bio != '') + 
                     count(avatar_url IS NOT NULL AND avatar_url != '') + 
                     count(date_of_birth IS NOT NULL)) * 20 AS score
                FROM profile WHERE user = $user_id
            )[0].score OR 0;
            
            RETURN ($sessions * 10) + $profile_completeness;
        };
        """,
        
        # Function to get user's full display name
        """
        DEFINE FUNCTION fn::user_display_name($user_id: record) {
            LET $user = (SELECT username FROM $user_id)[0];
            LET $profile = (SELECT first_name, last_name FROM profile WHERE user = $user_id)[0];
            
            RETURN CASE 
                WHEN $profile.first_name IS NOT NULL AND $profile.last_name IS NOT NULL 
                THEN string::concat($profile.first_name, ' ', $profile.last_name)
                WHEN $profile.first_name IS NOT NULL 
                THEN $profile.first_name
                ELSE $user.username
            END;
        };
        """,
        
        # Function to check if user is active in last N days
        """
        DEFINE FUNCTION fn::user_active_in_days($user_id: record, $days: number) {
            LET $recent_sessions = (
                SELECT count() FROM session 
                WHERE user = $user_id 
                AND created_at > time::now() - duration::from::days($days)
            );
            
            RETURN $recent_sessions > 0;
        };
        """
    ]
    
    results = []
    for func in functions:
        try:
            await self.db.query(func)
            results.append({"function": func.split('\n')[1].strip(), "status": "created"})
        except Exception as e:
            results.append({"function": func.split('\n')[1].strip(), "status": "error", "error": str(e)})
    
    return {
        "custom_functions": results,
        "created_at": datetime.utcnow().isoformat()
    }

async def use_custom_functions_example(self) -> Dict:
    """
    Example usage of custom functions
    """
    
    result = await self.db.query("""
        SELECT 
            id,
            username,
            fn::user_display_name(id) AS display_name,
            fn::user_engagement_score(id) AS engagement_score,
            fn::user_active_in_days(id, 7) AS active_last_week,
            fn::user_active_in_days(id, 30) AS active_last_month
        FROM user 
        WHERE is_active = true
        ORDER BY engagement_score DESC
        LIMIT 10
    """)
    
    return {
        "top_engaged_users": result[0]["result"] if result and result[0]["result"] else [],
        "generated_at": datetime.utcnow().isoformat()
    }
```

These advanced query patterns demonstrate SurrealDB's powerful capabilities for complex data operations, analytics, real-time monitoring, and performance optimization in a FastAPI application context.