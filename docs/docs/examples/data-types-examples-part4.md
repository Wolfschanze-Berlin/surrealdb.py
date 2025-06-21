# SurrealDB Python SDK Data Types Examples - Part 4 (Final)

This is the final part of comprehensive real-world examples for SurrealDB Python SDK data types.

## Future Examples (Continued)

### Example 1: Asynchronous Task Management (Continued)

```python
from surrealdb.data.types.future import Future
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
import asyncio
import uuid
import random

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
                            combiner_function: Callable = None) -> str:
        """Create a task that depends on other tasks' results"""
        def dependency_combiner():
            # Get results from dependency futures
            dependency_results = []
            for dep_id in dependency_ids:
                if dep_id in self.futures:
                    dep_future = self.futures[dep_id]
                    if dep_future.value is not None:
                        dependency_results.append(dep_future.value)
                    else:
                        raise ValueError(f"Dependency {dep_id} not yet resolved")
            
            # Apply combiner function if provided
            if combiner_function:
                return combiner_function(dependency_results)
            else:
                return dependency_results
        
        return self.create_task(task_name, dependency_combiner, dependency_ids)
    
    def resolve_task(self, task_id: str, result: Any):
        """Resolve a task with its result"""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        task["status"] = "completed"
        task["completed_at"] = datetime.now()
        
        # Update the Future with the result
        task["result_future"].value = result
        self.futures[task_id].value = result
        
        # Move to completed tasks
        self.completed_tasks[task_id] = task
        
        print(f"✅ Task '{task['name']}' completed with result: {result}")
        
        # Check if any dependent tasks can now be executed
        self._check_dependent_tasks()
    
    def fail_task(self, task_id: str, error: str):
        """Mark a task as failed"""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        task["status"] = "failed"
        task["completed_at"] = datetime.now()
        task["error"] = error
        
        # Future remains unresolved (value = None)
        print(f"❌ Task '{task['name']}' failed: {error}")
    
    def _check_dependent_tasks(self):
        """Check if any pending tasks can now be executed"""
        for task_id, task in self.tasks.items():
            if task["status"] == "pending" and task["dependencies"]:
                # Check if all dependencies are resolved
                all_deps_resolved = True
                for dep_id in task["dependencies"]:
                    if dep_id not in self.completed_tasks:
                        all_deps_resolved = False
                        break
                
                if all_deps_resolved:
                    print(f"🔄 Dependencies resolved for task '{task['name']}', ready to execute")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get current status of a task"""
        if task_id not in self.tasks:
            return {"error": "Task not found"}
        
        task = self.tasks[task_id]
        future_value = self.futures[task_id].value
        
        return {
            "id": task["id"],
            "name": task["name"],
            "status": task["status"],
            "created_at": task["created_at"],
            "started_at": task["started_at"],
            "completed_at": task["completed_at"],
            "dependencies": task["dependencies"],
            "future_resolved": future_value is not None,
            "result": future_value,
            "error": task.get("error")
        }
    
    def get_all_futures(self) -> Dict[str, Future]:
        """Get all task futures"""
        return self.futures.copy()
    
    def wait_for_task(self, task_id: str, timeout_seconds: int = 30) -> Any:
        """Wait for a task to complete and return its result"""
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            if task_id in self.completed_tasks:
                return self.futures[task_id].value
            time.sleep(0.1)
        
        raise TimeoutError(f"Task {task_id} did not complete within {timeout_seconds} seconds")

# Usage
task_manager = TaskManager()

# Create independent tasks
data_fetch_task = task_manager.create_task("fetch_user_data")
config_load_task = task_manager.create_task("load_configuration")
auth_task = task_manager.create_task("authenticate_user")

# Create dependent tasks
def combine_user_and_config(results):
    """Combine user data and configuration"""
    user_data, config = results
    return {
        "user": user_data,
        "config": config,
        "combined_at": datetime.now()
    }

setup_task = task_manager.create_dependent_task(
    "setup_user_environment",
    [data_fetch_task, config_load_task],
    combine_user_and_config
)

def finalize_setup(results):
    """Finalize setup with all dependencies"""
    setup_data, auth_result = results
    return {
        "setup": setup_data,
        "auth": auth_result,
        "ready": True,
        "finalized_at": datetime.now()
    }

final_task = task_manager.create_dependent_task(
    "finalize_user_session",
    [setup_task, auth_task],
    finalize_setup
)

print("📋 Task Dependency Chain Created:")
print(f"  1. {data_fetch_task} (fetch_user_data)")
print(f"  2. {config_load_task} (load_configuration)")
print(f"  3. {auth_task} (authenticate_user)")
print(f"  4. {setup_task} (setup_user_environment) - depends on 1,2")
print(f"  5. {final_task} (finalize_user_session) - depends on 3,4")

# Simulate task completion
print(f"\n🔄 Executing tasks...")

# Complete independent tasks
task_manager.resolve_task(data_fetch_task, {
    "user_id": "user_123",
    "name": "John Doe",
    "email": "john@example.com"
})

task_manager.resolve_task(config_load_task, {
    "theme": "dark",
    "language": "en",
    "timezone": "UTC"
})

task_manager.resolve_task(auth_task, {
    "token": "abc123xyz",
    "expires_at": datetime.now(),
    "permissions": ["read", "write"]
})

# The dependent tasks should now be ready to execute
# Simulate their execution
import time
time.sleep(1)  # Simulate processing time

# Get final result
final_status = task_manager.get_task_status(final_task)
print(f"\n📊 Final Task Status:")
for key, value in final_status.items():
    if key == "result" and value:
        print(f"  {key}:")
        for sub_key, sub_value in value.items():
            print(f"    {sub_key}: {sub_value}")
    else:
        print(f"  {key}: {value}")

# Show all futures and their states
print(f"\n🔮 All Task Futures:")
all_futures = task_manager.get_all_futures()
for task_id, future in all_futures.items():
    task_name = task_manager.tasks[task_id]["name"]
    resolved = "✅ Resolved" if future.value is not None else "⏳ Pending"
    print(f"  {task_name}: {resolved}")
```

### Example 2: Lazy Evaluation System

```python
from surrealdb.data.types.future import Future
from typing import Any, Callable, Dict, List
import time
import functools

class LazyEvaluator:
    def __init__(self):
        self.computations: Dict[str, Future] = {}
        self.computation_functions: Dict[str, Callable] = {}
        self.dependencies: Dict[str, List[str]] = {}
        self.cache: Dict[str, Any] = {}
    
    def register_computation(self, name: str, computation_func: Callable, 
                           dependencies: List[str] = None):
        """Register a lazy computation"""
        # Create a Future to hold the eventual result
        future = Future(None)
        
        self.computations[name] = future
        self.computation_functions[name] = computation_func
        self.dependencies[name] = dependencies or []
        
        print(f"📝 Registered lazy computation: {name}")
        return future
    
    def get_value(self, name: str) -> Any:
        """Get the value of a computation, evaluating if necessary"""
        if name not in self.computations:
            raise ValueError(f"Computation '{name}' not registered")
        
        # Check if already computed
        if self.computations[name].value is not None:
            print(f"💾 Using cached result for: {name}")
            return self.computations[name].value
        
        # Check if dependencies need to be computed first
        for dep_name in self.dependencies[name]:
            if self.computations[dep_name].value is None:
                print(f"🔄 Computing dependency: {dep_name}")
                self.get_value(dep_name)
        
        # Compute the value
        print(f"⚡ Computing: {name}")
        start_time = time.time()
        
        try:
            # Get dependency values
            dep_values = {}
            for dep_name in self.dependencies[name]:
                dep_values[dep_name] = self.computations[dep_name].value
            
            # Execute computation
            if self.dependencies[name]:
                result = self.computation_functions[name](dep_values)
            else:
                result = self.computation_functions[name]()
            
            # Store result in Future
            self.computations[name].value = result
            
            computation_time = time.time() - start_time
            print(f"✅ Computed {name} in {computation_time:.3f}s: {result}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error computing {name}: {e}")
            raise
    
    def invalidate(self, name: str):
        """Invalidate a computation and its dependents"""
        if name not in self.computations:
            return
        
        # Reset the Future
        self.computations[name].value = None
        print(f"🗑️  Invalidated: {name}")
        
        # Find and invalidate dependents
        dependents = self._find_dependents(name)
        for dependent in dependents:
            self.invalidate(dependent)
    
    def _find_dependents(self, name: str) -> List[str]:
        """Find computations that depend on the given computation"""
        dependents = []
        for comp_name, deps in self.dependencies.items():
            if name in deps:
                dependents.append(comp_name)
        return dependents
    
    def get_computation_graph(self) -> Dict[str, Any]:
        """Get the computation dependency graph"""
        graph = {}
        for name in self.computations.keys():
            future = self.computations[name]
            graph[name] = {
                "dependencies": self.dependencies[name],
                "computed": future.value is not None,
                "result": future.value,
                "dependents": self._find_dependents(name)
            }
        return graph
    
    def compute_all(self):
        """Compute all registered computations"""
        print("🚀 Computing all registered computations...")
        for name in self.computations.keys():
            if self.computations[name].value is None:
                self.get_value(name)

# Usage
evaluator = LazyEvaluator()

# Register base computations
def load_raw_data():
    """Simulate loading raw data"""
    time.sleep(0.5)  # Simulate I/O delay
    return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

def load_config():
    """Simulate loading configuration"""
    time.sleep(0.2)
    return {"multiplier": 2, "filter_threshold": 5}

evaluator.register_computation("raw_data", load_raw_data)
evaluator.register_computation("config", load_config)

# Register dependent computations
def filter_data(deps):
    """Filter data based on configuration"""
    raw_data = deps["raw_data"]
    config = deps["config"]
    threshold = config["filter_threshold"]
    
    filtered = [x for x in raw_data if x > threshold]
    time.sleep(0.1)  # Simulate processing
    return filtered

def transform_data(deps):
    """Transform filtered data"""
    filtered_data = deps["filtered_data"]
    config = deps["config"]
    multiplier = config["multiplier"]
    
    transformed = [x * multiplier for x in filtered_data]
    time.sleep(0.1)
    return transformed

def calculate_statistics(deps):
    """Calculate statistics on transformed data"""
    transformed_data = deps["transformed_data"]
    
    stats = {
        "count": len(transformed_data),
        "sum": sum(transformed_data),
        "average": sum(transformed_data) / len(transformed_data) if transformed_data else 0,
        "min": min(transformed_data) if transformed_data else None,
        "max": max(transformed_data) if transformed_data else None
    }
    time.sleep(0.1)
    return stats

evaluator.register_computation("filtered_data", filter_data, ["raw_data", "config"])
evaluator.register_computation("transformed_data", transform_data, ["filtered_data", "config"])
evaluator.register_computation("statistics", calculate_statistics, ["transformed_data"])

# Create a final report computation
def generate_report(deps):
    """Generate final report"""
    stats = deps["statistics"]
    config = deps["config"]
    
    report = {
        "title": "Data Processing Report",
        "generated_at": time.time(),
        "configuration": config,
        "statistics": stats,
        "summary": f"Processed {stats['count']} items with average value {stats['average']:.2f}"
    }
    time.sleep(0.1)
    return report

evaluator.register_computation("final_report", generate_report, ["statistics", "config"])

# Display computation graph
print("📊 Computation Dependency Graph:")
graph = evaluator.get_computation_graph()
for name, info in graph.items():
    deps_str = ", ".join(info["dependencies"]) if info["dependencies"] else "None"
    dependents_str = ", ".join(info["dependents"]) if info["dependents"] else "None"
    status = "✅ Computed" if info["computed"] else "⏳ Pending"
    
    print(f"  {name}: {status}")
    print(f"    Dependencies: {deps_str}")
    print(f"    Dependents: {dependents_str}")

# Test lazy evaluation
print(f"\n🔍 Testing Lazy Evaluation:")

# Request final report - should trigger computation chain
print(f"\n1. Requesting final report...")
report = evaluator.get_value("final_report")
print(f"📄 Final Report Summary: {report['summary']}")

# Request statistics again - should use cached value
print(f"\n2. Requesting statistics again...")
stats = evaluator.get_value("statistics")
print(f"📈 Statistics: {stats}")

# Invalidate raw data and request report again
print(f"\n3. Invalidating raw data and requesting report...")
evaluator.invalidate("raw_data")
new_report = evaluator.get_value("final_report")
print(f"📄 New Report Summary: {new_report['summary']}")

# Show final state of all futures
print(f"\n🔮 Final State of All Futures:")
for name, future in evaluator.computations.items():
    status = "✅ Resolved" if future.value is not None else "⏳ Pending"
    print(f"  {name}: {status}")
    if future.value is not None and isinstance(future.value, dict) and len(str(future.value)) < 100:
        print(f"    Value: {future.value}")
```

### Example 3: Promise-like Async Operations

```python
from surrealdb.data.types.future import Future
from typing import Any, Callable, List
import asyncio
import random
from datetime import datetime

class AsyncPromise:
    def __init__(self):
        self.futures: List[Future] = []
        self.callbacks: List[Callable] = []
        self.error_handlers: List[Callable] = []
    
    def create_promise(self, async_operation: Callable) -> Future:
        """Create a promise for an async operation"""
        future = Future(None)
        self.futures.append(future)
        
        # Store the operation to be executed
        future._operation = async_operation
        future._promise = self
        
        return future
    
    async def resolve_promise(self, future: Future, *args, **kwargs):
        """Resolve a promise by executing its operation"""
        try:
            if hasattr(future, '_operation'):
                result = await future._operation(*args, **kwargs)
                future.value = result
                
                # Execute callbacks
                for callback in self.callbacks:
                    try:
                        await callback(result)
                    except Exception as e:
                        print(f"⚠️  Callback error: {e}")
                
                return result
        except Exception as e:
            # Execute error handlers
            for error_handler in self.error_handlers:
                try:
                    await error_handler(e)
                except Exception as handler_error:
                    print(f"⚠️  Error handler failed: {handler_error}")
            raise
    
    def then(self, callback: Callable):
        """Add a callback to be executed when promises resolve"""
        self.callbacks.append(callback)
        return self
    
    def catch(self, error_handler: Callable):
        """Add an error handler"""
        self.error_handlers.append(error_handler)
        return self
    
    async def all(self, futures: List[Future]) -> List[Any]:
        """Wait for all futures to resolve"""
        results = []
        for future in futures:
            if future.value is None and hasattr(future, '_operation'):
                await self.resolve_promise(future)
            results.append(future.value)
        return results
    
    async def race(self, futures: List[Future]) -> Any:
        """Return the first future to resolve"""
        tasks = []
        for future in futures:
            if future.value is None and hasattr(future, '_operation'):
                task = asyncio.create_task(self.resolve_promise(future))
                tasks.append((task, future))
        
        if tasks:
            done, pending = await asyncio.wait(
                [task for task, _ in tasks], 
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            # Return the first completed result
            completed_task = list(done)[0]
            return await completed_task
        
        # If no tasks to wait for, return first resolved future
        for future in futures:
            if future.value is not None:
                return future.value
        
        return None

# Usage
async def main():
    promise_manager = AsyncPromise()
    
    # Define async operations
    async def fetch_user_data(user_id: str):
        """Simulate fetching user data"""
        await asyncio.sleep(random.uniform(0.5, 1.5))
        return {
            "user_id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com",
            "fetched_at": datetime.now()
        }
    
    async def fetch_user_posts(user_id: str):
        """Simulate fetching user posts"""
        await asyncio.sleep(random.uniform(0.3, 1.0))
        post_count = random.randint(1, 5)
        return [
            {
                "id": f"post_{i}",
                "title": f"Post {i} by User {user_id}",
                "content": f"Content of post {i}",
                "created_at": datetime.now()
            }
            for i in range(post_count)
        ]
    
    async def fetch_user_settings(user_id: str):
        """Simulate fetching user settings"""
        await asyncio.sleep(random.uniform(0.2, 0.8))
        return {
            "user_id": user_id,
            "theme": random.choice(["light", "dark"]),
            "language": random.choice(["en", "es", "fr"]),
            "notifications": random.choice([True, False])
        }
    
    # Create promises
    user_data_future = promise_manager.create_promise(fetch_user_data)
    user_posts_future = promise_manager.create_promise(fetch_user_posts)
    user_settings_future = promise_manager.create_promise(fetch_user_settings)
    
    # Add callbacks and error handlers
    async def on_success(result):
        print(f"✅ Operation completed: {type(result).__name__}")
    
    async def on_error(error):
        print(f"❌ Operation failed: {error}")
    
    promise_manager.then(on_success).catch(on_error)
    
    print("🚀 Starting async operations...")
    
    # Test Promise.all - wait for all operations
    print("\n📊 Testing Promise.all (wait for all):")
    start_time = datetime.now()
    
    all_results = await promise_manager.all([
        promise_manager.resolve_promise(user_data_future, "123"),
        promise_manager.resolve_promise(user_posts_future, "123"),
        promise_manager.resolve_promise(user_settings_future, "123")
    ])
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"⏱️  All operations completed in {duration:.2f} seconds")
    print(f"📦 Results:")
    for i, result in enumerate(all_results):
        print(f"  {i+1}. {type(result).__name__}: {len(str(result))} chars")
    
    # Test Promise.race - first to complete wins
    print(f"\n🏁 Testing Promise.race (first to complete):")
    
    # Create new futures for race test
    race_futures = [
        promise_manager.create_promise(fetch_user_data),
        promise_manager.create_promise(fetch_user_posts),
        promise_manager.create_promise(fetch_user_settings)
    ]
    
    start_time = datetime.now()
    
    # Start all operations but only wait for the first
    race_tasks = [
        promise_manager.resolve_promise(race_futures[0], "456"),
        promise_manager.resolve_promise(race_futures[1], "456"),
        promise_manager.resolve_promise(race_futures[2], "456")
    ]
    
    first_result = await promise_manager.race(race_futures)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"⏱️  First operation completed in {duration:.2f} seconds")
    print(f"🏆 Winner: {type(first_result).__name__}")
    
    # Show final state of all futures
    print(f"\n🔮 Final Future States:")
    all_test_futures = [user_data_future, user_posts_future, user_settings_future] + race_futures
    
    for i, future in enumerate(all_test_futures):
        status = "✅ Resolved" if future.value is not None else "⏳ Pending"
        future_type = "Promise.all" if i < 3 else "Promise.race"
        print(f"  Future {i+1} ({future_type}): {status}")

# Run the async example
if __name__ == "__main__":
    print("🔮 Future-based Promise System Demo")
    print("=" * 50)
    asyncio.run(main())
```

## Summary and Best Practices

### Key Takeaways

1. **RecordID**: Essential for uniquely identifying database records
   - Use meaningful table names and identifiers
   - Parse string representations safely
   - Leverage for relationships between records

2. **Table**: Useful for dynamic table operations
   - Great for multi-tenant applications
   - Helpful in migration systems
   - Enables flexible schema management

3. **Duration**: Precise time interval handling
   - Perfect for performance monitoring
   - Useful in scheduling systems
   - Supports various time units with nanosecond precision

4. **DateTime**: ISO 8601 datetime handling
   - Always use timezone-aware datetimes
   - Essential for audit logs and time series data
   - Proper serialization for database storage

5. **Geometry**: Comprehensive spatial data support
   - Points, lines, polygons, and collections
   - Ideal for location-based services
   - Supports complex spatial analysis

6. **Range**: Bounded range operations
   - Inclusive and exclusive bounds
   - Perfect for validation systems
   - Useful in access control and time-based rules

7. **Future**: Placeholder for async values
   - Lazy evaluation patterns
   - Task dependency management
   - Promise-like async operations

### Best Practices

1. **Type Safety**: Always validate data types before operations
2. **Error Handling**: Implement proper error handling for all operations
3. **Performance**: Use appropriate data structures for your use case
4. **Documentation**: Comment your code to explain complex operations
5. **Testing**: Create comprehensive tests for all data type operations
6. **Serialization**: Ensure proper serialization/deserialization for database storage

### Integration with SurrealDB

These data types are designed to work seamlessly with SurrealDB operations:

```python
# Example integration
from surrealdb import Surreal
from surrealdb.data.types import RecordID, Duration, GeometryPoint

async def example_integration():
    db = Surreal("ws://localhost:8000/rpc")
    await db.connect()
    await db.use("test", "test")
    
    # Create record with typed data
    user_id = RecordID("users", "john_doe")
    location = GeometryPoint(-122.4194, 37.7749)
    session_duration = Duration.parse("2h")
    
    await db.create(user_id, {
        "name": "John Doe",
        "location": location,
        "session_duration": session_duration
    })
    
    # Query with typed parameters
    result = await db.select(user_id)
    print(f"User: {result}")
```

This comprehensive guide provides real-world examples for all SurrealDB Python SDK data types, demonstrating their practical applications and best practices for effective usage in your applications.