---
sidebar_position: 1
---

# Basic CRUD Operations

This guide demonstrates how to perform Create, Read, Update, and Delete (CRUD) operations using the SurrealDB Python SDK. These examples cover the most common database operations you'll use in your applications.

## Setup

First, let's establish a connection and set up our environment:

```python
from surrealdb import Surreal
from surrealdb.data import RecordID
from datetime import datetime

# Connect to SurrealDB
with Surreal("ws://localhost:8000/rpc") as db:
    # Authenticate
    db.signin({"username": "root", "password": "root"})
    
    # Select namespace and database
    db.use("examples", "crud")
    
    # Your CRUD operations go here
    pass
```

## Create Operations

### Creating Single Records

```python
from surrealdb import Surreal
from datetime import datetime

def create_single_records():
    """Examples of creating single records"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("examples", "crud")
        
        # Create user with auto-generated ID
        user = db.create("user", {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "active": True,
            "created_at": datetime.now().isoformat()
        })
        
        print(f"Created user: {user[0]['id']}")
        print(f"User name: {user[0]['name']}")
        
        # Create user with specific ID
        admin_user = db.create("user:admin", {
            "name": "Admin User",
            "email": "admin@example.com",
            "role": "administrator",
            "permissions": ["read", "write", "delete"],
            "created_at": datetime.now().isoformat()
        })
        
        print(f"Created admin: {admin_user[0]['id']}")
        
        # Create product with complex data
        product = db.create("product", {
            "name": "Laptop",
            "description": "High-performance laptop",
            "price": 999.99,
            "category": "electronics",
            "specifications": {
                "cpu": "Intel i7",
                "ram": "16GB",
                "storage": "512GB SSD"
            },
            "tags": ["laptop", "computer", "electronics"],
            "in_stock": True,
            "stock_count": 50
        })
        
        print(f"Created product: {product[0]['id']}")
        
        return user[0], admin_user[0], product[0]

# Run the example
created_records = create_single_records()
```

### Creating Multiple Records

```python
from surrealdb import Surreal

def create_multiple_records():
    """Examples of creating multiple records at once"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("examples", "crud")
        
        # Create multiple users with insert
        users_data = [
            {
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "age": 28,
                "department": "Engineering"
            },
            {
                "name": "Bob Smith",
                "email": "bob@example.com", 
                "age": 32,
                "department": "Marketing"
            },
            {
                "name": "Carol Williams",
                "email": "carol@example.com",
                "age": 29,
                "department": "Design"
            }
        ]
        
        users = db.insert("user", users_data)
        print(f"Created {len(users)} users")
        
        # Create multiple products
        products_data = [
            {
                "name": "Smartphone",
                "price": 699.99,
                "category": "electronics",
                "in_stock": True
            },
            {
                "name": "Headphones",
                "price": 199.99,
                "category": "electronics", 
                "in_stock": True
            },
            {
                "name": "Keyboard",
                "price": 89.99,
                "category": "accessories",
                "in_stock": False
            }
        ]
        
        products = db.insert("product", products_data)
        print(f"Created {len(products)} products")
        
        return users, products

# Run the example
users, products = create_multiple_records()
```

### Creating with Relationships

```python
from surrealdb import Surreal
from surrealdb.data import RecordID

def create_with_relationships():
    """Examples of creating records with relationships"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("examples", "crud")
        
        # Create a company
        company = db.create("company", {
            "name": "Tech Corp",
            "industry": "Technology",
            "founded": "2020-01-01"
        })
        
        company_id = company[0]["id"]
        print(f"Created company: {company_id}")
        
        # Create employees with company reference
        employees = db.insert("employee", [
            {
                "name": "John Manager",
                "position": "Manager",
                "company": company_id,  # Reference to company
                "salary": 80000
            },
            {
                "name": "Jane Developer",
                "position": "Developer", 
                "company": company_id,
                "salary": 70000
            }
        ])
        
        print(f"Created {len(employees)} employees")
        
        # Create project with employee references
        project = db.create("project", {
            "name": "Website Redesign",
            "company": company_id,
            "team_lead": employees[0]["id"],
            "team_members": [emp["id"] for emp in employees],
            "status": "active",
            "budget": 50000
        })
        
        print(f"Created project: {project[0]['id']}")
        
        return company[0], employees, project[0]

# Run the example
company, employees, project = create_with_relationships()
```

## Read Operations

### Reading All Records

```python
from surrealdb import Surreal

def read_all_records():
    """Examples of reading all records from tables"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("examples", "crud")
        
        # Select all users
        all_users = db.select("user")
        print(f"Total users: {len(all_users)}")
        
        for user in all_users:
            print(f"  - {user['name']} ({user['email']})")
        
        # Select all products
        all_products = db.select("product")
        print(f"\nTotal products: {len(all_products)}")
        
        for product in all_products:
            print(f"  - {product['name']}: ${product['price']}")
        
        # Select all companies
        all_companies = db.select("company")
        print(f"\nTotal companies: {len(all_companies)}")
        
        return all_users, all_products, all_companies

# Run the example
users, products, companies = read_all_records()
```

### Reading Specific Records

```python
from surrealdb import Surreal
from surrealdb.data import RecordID

def read_specific_records():
    """Examples of reading specific records by ID"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("examples", "crud")
        
        # Get all users first to have IDs to work with
        all_users = db.select("user")
        
        if all_users:
            # Select specific user by string ID
            user_id = all_users[0]["id"]
            specific_user = db.select(user_id)
            print(f"User by string ID: {specific_user[0]['name']}")
            
            # Select using RecordID object
            record_id = RecordID.parse(str(user_id))
            user_by_record_id = db.select(record_id)
            print(f"User by RecordID: {user_by_record_id[0]['name']}")
        
        # Try to select admin user (if it exists)
        try:
            admin_user = db.select("user:admin")
            print(f"Admin user: {admin_user[0]['name']}")
        except:
            print("Admin user not found")
        
        return specific_user if all_users else None

# Run the example
specific_user = read_specific_records()
```

### Reading with Queries

```python
from surrealdb import Surreal

def read_with_queries():
    """Examples of reading records using SurrealQL queries"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("examples", "crud")
        
        # Query users by age
        young_users = db.query("SELECT * FROM user WHERE age < 30")
        print(f"Users under 30: {len(young_users)}")
        
        # Query with parameters
        min_age = 25
        filtered_users = db.query(
            "SELECT * FROM user WHERE age >= $min_age ORDER BY age",
            {"min_age": min_age}
        )
        print(f"Users {min_age}+: {len(filtered_users)}")
        
        # Query products in stock
        in_stock_products = db.query(
            "SELECT name, price FROM product WHERE in_stock = true ORDER BY price DESC"
        )
        print(f"Products in stock: {len(in_stock_products)}")
        
        # Complex query with aggregation
        user_stats = db.query("""
            SELECT 
                count() as total_users,
                math::mean(age) as average_age,
                math::min(age) as youngest,
                math::max(age) as oldest
            FROM user
            GROUP ALL
        """)
        
        if user_stats:
            stats = user_stats[0]
            print(f"\nUser Statistics:")
            print(f"  Total: {stats['total_users']}")
            print(f"  Average age: {stats['average_age']:.1f}")
            print(f"  Age range: {stats['youngest']} - {stats['oldest']}")
        
        return young_users, filtered_users, in_stock_products

# Run the example
young_users, filtered_users, products = read_with_queries()
```

## Update Operations

### Updating Entire Records

```python
from surrealdb import Surreal

def update_entire_records():
    """Examples of updating entire records (replace content)"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("examples", "crud")
        
        # Get a user to update
        users = db.select("user")
        if not users:
            print("No users found to update")
            return
        
        user_id = users[0]["id"]
        print(f"Updating user: {user_id}")
        
        # Update entire record (replaces all content)
        updated_user = db.update(user_id, {
            "name": "John Updated",
            "email": "john.updated@example.com",
            "age": 31,
            "active": True,
            "last_updated": datetime.now().isoformat(),
            "profile": {
                "bio": "Updated bio",
                "interests": ["coding", "music", "travel"]
            }
        })
        
        print(f"Updated user: {updated_user[0]['name']}")
        print(f"New email: {updated_user[0]['email']}")
        
        # Update all users in a table (be careful!)
        # updated_all = db.update("user", {"last_bulk_update": datetime.now().isoformat()})
        # print(f"Bulk updated {len(updated_all)} users")
        
        return updated_user[0]

# Run the example
updated_user = update_entire_records()
```

### Merging Data

```python
from surrealdb import Surreal

def merge_data():
    """Examples of merging data into existing records"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("examples", "crud")
        
        # Get a user to merge data into
        users = db.select("user")
        if not users:
            print("No users found to merge")
            return
        
        user_id = users[0]["id"]
        print(f"Merging data for user: {user_id}")
        
        # Merge additional data (preserves existing fields)
        merged_user = db.merge(user_id, {
            "last_login": datetime.now().isoformat(),
            "login_count": 1,
            "preferences": {
                "theme": "dark",
                "notifications": True,
                "language": "en"
            }
        })
        
        print(f"Merged data for: {merged_user[0]['name']}")
        print(f"Last login: {merged_user[0].get('last_login')}")
        
        # Merge data for multiple records
        all_users = db.select("user")
        for user in all_users[:3]:  # Update first 3 users
            db.merge(user["id"], {
                "updated_at": datetime.now().isoformat(),
                "status": "active"
            })
        
        print(f"Merged status for {min(3, len(all_users))} users")
        
        return merged_user[0]

# Run the example
merged_user = merge_data()
```

### Patching Records

```python
from surrealdb import Surreal

def patch_records():
    """Examples of patching records using JSON Patch operations"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("examples", "crud")
        
        # Get a user to patch
        users = db.select("user")
        if not users:
            print("No users found to patch")
            return
        
        user_id = users[0]["id"]
        print(f"Patching user: {user_id}")
        
        # Apply JSON Patch operations
        patched_user = db.patch(user_id, [
            # Replace age
            {"op": "replace", "path": "/age", "value": 35},
            
            # Add new field
            {"op": "add", "path": "/department", "value": "Engineering"},
            
            # Add to array (if tags exist)
            {"op": "add", "path": "/tags", "value": ["python", "developer"]},
            
            # Remove field (if it exists)
            {"op": "remove", "path": "/temp_field"},
            
            # Replace nested value
            {"op": "replace", "path": "/preferences/theme", "value": "light"}
        ])
        
        print(f"Patched user: {patched_user[0]['name']}")
        print(f"New age: {patched_user[0]['age']}")
        print(f"Department: {patched_user[0].get('department')}")
        
        return patched_user[0]

# Run the example
patched_user = patch_records()
```

### Upserting Records

```python
from surrealdb import Surreal

def upsert_records():
    """Examples of upserting (insert or update) records"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("examples", "crud")
        
        # Upsert with specific ID (will create if doesn't exist)
        upserted_user = db.upsert("user:special", {
            "name": "Special User",
            "email": "special@example.com",
            "role": "special",
            "created_at": datetime.now().isoformat()
        })
        
        print(f"Upserted user: {upserted_user[0]['name']}")
        
        # Upsert again (will update existing)
        updated_special = db.upsert("user:special", {
            "name": "Updated Special User",
            "email": "special.updated@example.com",
            "role": "super_special",
            "updated_at": datetime.now().isoformat()
        })
        
        print(f"Updated special user: {updated_special[0]['name']}")
        
        # Upsert multiple records
        config_data = [
            {"key": "app_name", "value": "My App"},
            {"key": "version", "value": "1.0.0"},
            {"key": "debug", "value": False}
        ]
        
        for config in config_data:
            db.upsert(f"config:{config['key']}", config)
        
        print("Upserted configuration data")
        
        return updated_special[0]

# Run the example
upserted_user = upsert_records()
```

## Delete Operations

### Deleting Specific Records

```python
from surrealdb import Surreal

def delete_specific_records():
    """Examples of deleting specific records"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("examples", "crud")
        
        # Create a test record to delete
        test_user = db.create("user", {
            "name": "Test User",
            "email": "test@example.com",
            "temporary": True
        })
        
        test_user_id = test_user[0]["id"]
        print(f"Created test user: {test_user_id}")
        
        # Delete the specific record
        deleted_user = db.delete(test_user_id)
        print(f"Deleted user: {deleted_user[0]['name']}")
        
        # Try to delete a record that doesn't exist
        try:
            non_existent = db.delete("user:nonexistent")
            print(f"Deleted non-existent: {non_existent}")
        except:
            print("Non-existent record not found (expected)")
        
        # Delete using string format
        if db.select("user:special"):
            deleted_special = db.delete("user:special")
            print(f"Deleted special user: {deleted_special[0]['name']}")
        
        return deleted_user[0] if deleted_user else None

# Run the example
deleted_record = delete_specific_records()
```

### Deleting with Conditions

```python
from surrealdb import Surreal

def delete_with_conditions():
    """Examples of deleting records based on conditions"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("examples", "crud")
        
        # Create some test records
        test_users = db.insert("user", [
            {"name": "Temp User 1", "temporary": True, "age": 20},
            {"name": "Temp User 2", "temporary": True, "age": 25},
            {"name": "Permanent User", "temporary": False, "age": 30}
        ])
        
        print(f"Created {len(test_users)} test users")
        
        # Delete records using query
        deleted_temp = db.query("DELETE user WHERE temporary = true")
        print(f"Deleted temporary users: {len(deleted_temp)}")
        
        # Delete records older than certain age
        deleted_old = db.query("DELETE user WHERE age > $max_age", {"max_age": 50})
        print(f"Deleted users over 50: {len(deleted_old)}")
        
        # Delete with complex conditions
        deleted_complex = db.query("""
            DELETE user 
            WHERE age < 25 
            AND (email CONTAINS 'temp' OR name CONTAINS 'test')
        """)
        print(f"Deleted with complex conditions: {len(deleted_complex)}")
        
        return deleted_temp

# Run the example
deleted_records = delete_with_conditions()
```

### Bulk Delete Operations

```python
from surrealdb import Surreal

def bulk_delete_operations():
    """Examples of bulk delete operations"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("examples", "crud")
        
        # Create test data for bulk operations
        test_products = []
        for i in range(10):
            product = db.create("test_product", {
                "name": f"Test Product {i}",
                "price": 10.0 + i,
                "category": "test",
                "batch": "bulk_test"
            })
            test_products.append(product[0])
        
        print(f"Created {len(test_products)} test products")
        
        # Delete all products in test category
        deleted_category = db.query("DELETE test_product WHERE category = 'test'")
        print(f"Deleted test category products: {len(deleted_category)}")
        
        # Create more test data
        for i in range(5):
            db.create("temp_log", {
                "message": f"Log entry {i}",
                "level": "debug",
                "timestamp": datetime.now().isoformat()
            })
        
        # Delete entire table (be very careful!)
        deleted_logs = db.delete("temp_log")
        print(f"Deleted entire temp_log table: {len(deleted_logs)}")
        
        return deleted_category, deleted_logs

# Run the example
deleted_category, deleted_logs = bulk_delete_operations()
```

## Complete CRUD Example

Here's a complete example that demonstrates all CRUD operations in a realistic scenario:

```python
from surrealdb import Surreal
from surrealdb.data import RecordID
from datetime import datetime

def complete_crud_example():
    """Complete CRUD example: Blog management system"""
    
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("examples", "blog")
        
        print("🚀 Starting Complete CRUD Example: Blog Management")
        
        # 1. CREATE - Set up blog data
        print("\n📝 Creating blog data...")
        
        # Create authors
        authors = db.insert("author", [
            {
                "name": "Alice Johnson",
                "email": "alice@blog.com",
                "bio": "Tech writer and developer",
                "joined": datetime.now().isoformat()
            },
            {
                "name": "Bob Smith", 
                "email": "bob@blog.com",
                "bio": "Marketing expert and blogger",
                "joined": datetime.now().isoformat()
            }
        ])
        
        print(f"✅ Created {len(authors)} authors")
        
        # Create categories
        categories = db.insert("category", [
            {"name": "Technology", "description": "Tech articles and tutorials"},
            {"name": "Marketing", "description": "Marketing tips and strategies"},
            {"name": "General", "description": "General blog posts"}
        ])
        
        print(f"✅ Created {len(categories)} categories")
        
        # Create blog posts
        posts = []
        for i, author in enumerate(authors):
            post = db.create("post", {
                "title": f"Amazing Post {i + 1}",
                "content": f"This is the content of post {i + 1}...",
                "author": author["id"],
                "category": categories[i % len(categories)]["id"],
                "published": True,
                "created_at": datetime.now().isoformat(),
                "tags": ["blog", "example", f"post{i+1}"],
                "views": 0,
                "likes": 0
            })
            posts.append(post[0])
        
        print(f"✅ Created {len(posts)} blog posts")
        
        # 2. READ - Query blog data
        print("\n📖 Reading blog data...")
        
        # Get all published posts with author info
        published_posts = db.query("""
            SELECT 
                *,
                author.name as author_name,
                author.email as author_email,
                category.name as category_name
            FROM post 
            WHERE published = true
            ORDER BY created_at DESC
        """)
        
        print(f"📊 Found {len(published_posts)} published posts")
        for post in published_posts:
            print(f"  - '{post['title']}' by {post['author_name']} in {post['category_name']}")
        
        # Get author statistics
        author_stats = db.query("""
            SELECT 
                author.name as author_name,
                count() as post_count,
                array::unique(category.name) as categories
            FROM post
            GROUP BY author
        """)
        
        print(f"\n👥 Author statistics:")
        for stat in author_stats:
            print(f"  - {stat['author_name']}: {stat['post_count']} posts in {stat['categories']}")
        
        # 3. UPDATE - Modify blog data
        print("\n✏️ Updating blog data...")
        
        # Update post views and likes
        for post in posts:
            updated_post = db.merge(post["id"], {
                "views": 42 + posts.index(post) * 10,
                "likes": 5 + posts.index(post) * 2,
                "last_updated": datetime.now().isoformat()
            })
            print(f"📈 Updated views/likes for: {updated_post[0]['title']}")
        
        # Update author bio using patch
        if authors:
            patched_author = db.patch(authors[0]["id"], [
                {"op": "replace", "path": "/bio", "value": "Senior tech writer and full-stack developer"},
                {"op": "add", "path": "/social", "value": {"twitter": "@alice_dev", "github": "alice-dev"}}
            ])
            print(f"👤 Updated author bio: {patched_author[0]['name']}")
        
        # 4. Advanced READ - Complex queries
        print("\n🔍 Advanced queries...")
        
        # Most popular posts
        popular_posts = db.query("""
            SELECT title, views, likes, author.name as author_name
            FROM post
            ORDER BY views DESC, likes DESC
            LIMIT 3
        """)
        
        print("🏆 Most popular posts:")
        for i, post in enumerate(popular_posts, 1):
            print(f"  {i}. '{post['title']}' by {post['author_name']} - {post['views']} views, {post['likes']} likes")
        
        # Posts by category
        category_breakdown = db.query("""
            SELECT 
                category.name as category_name,
                count() as post_count,
                math::sum(views) as total_views
            FROM post
            GROUP BY category
            ORDER BY post_count DESC
        """)
        
        print("\n📂 Posts by category:")
        for cat in category_breakdown:
            print(f"  - {cat['category_name']}: {cat['post_count']} posts, {cat['total_views']} total views")
        
        # 5. DELETE - Clean up test data
        print("\n🧹 Cleaning up...")
        
        # Delete posts with low engagement
        low_engagement = db.query("DELETE post WHERE views < 30 AND likes < 3")
        print(f"🗑️ Deleted {len(low_engagement)} low-engagement posts")
        
        # Delete test categories (if any)
        test_categories = db.query("DELETE category WHERE name CONTAINS 'test'")
        if test_categories:
            print(f"🗑️ Deleted {len(test_categories)} test categories")
        
        # Final statistics
        final_stats = db.query("""
            SELECT 
                (SELECT count() FROM author)[0] as authors,
                (SELECT count() FROM category)[0] as categories,
                (SELECT count() FROM post)[0] as posts,
                (SELECT math::sum(views) FROM post)[0] as total_views
        """)
        
        if final_stats:
            stats = final_stats[0]
            print(f"\n📊 Final Statistics:")
            print(f"  Authors: {stats['authors']}")
            print(f"  Categories: {stats['categories']}")
            print(f"  Posts: {stats['posts']}")
            print(f"  Total Views: {stats['total_views']}")
        
        print("\n🎉 Complete CRUD example finished!")
        
        return {
            "authors": len(authors),
            "categories": len(categories),
            "posts": len(posts),
            "final_stats": final_stats[0] if final_stats else None
        }

# Run the complete example
if __name__ == "__main__":
    result = complete_crud_example()
    print(f"\nExample completed with: {result}")
```

## Best Practices

### ✅ Do

- Use context managers for automatic connection cleanup
- Validate data before creating records
- Use appropriate methods for different operations (merge vs update vs patch)
- Handle errors gracefully
- Use transactions for related operations
- Index frequently queried fields

### ❌ Don't

- Forget to authenticate before operations
- Use update when you mean merge
- Delete entire tables without confirmation
- Ignore error handling
- Create records without validation
- Use string concatenation for queries (use parameters instead)

### Error Handling Example

```python
from surrealdb import Surreal
from surrealdb.errors import SurrealDBMethodError

def safe_crud_operations():
    """Example of CRUD operations with proper error handling"""
    
    try:
        with Surreal("ws://localhost:8000/rpc") as db:
            db.signin({"username": "root", "password": "root"})
            db.use("examples", "safe")
            
            # Safe create
            try:
                user = db.create("user", {"name": "Safe User", "email": "safe@example.com"})
                print(f"✅ Created user: {user[0]['id']}")
            except SurrealDBMethodError as e:
                print(f"❌ Failed to create user: {e}")
                return
            
            # Safe read
            try:
                users = db.select("user")
                print(f"✅ Found {len(users)} users")
            except SurrealDBMethodError as e:
                print(f"❌ Failed to read users: {e}")
            
            # Safe update
            if users:
                try:
                    updated = db.merge(users[0]["id"], {"last_access": datetime.now().isoformat()})
                    print(f"✅ Updated user: {updated[0]['name']}")
                except SurrealDBMethodError as e:
                    print(f"❌ Failed to update user: {e}")
            
            # Safe delete
            try:
                deleted = db.delete("user:nonexistent")
                print(f"✅ Deleted: {deleted}")
            except SurrealDBMethodError as e: