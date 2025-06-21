"""
Transaction Helper Example for SurrealDB Python SDK

This example demonstrates how to use the new transaction helper functionality
that provides Pythonic transaction management with automatic commit/rollback.
"""

import asyncio
from surrealdb import Surreal, AsyncSurreal


async def async_transaction_example():
    """Example of using transactions with async connections."""
    print("=== Async Transaction Example ===")
    
    # Create an async connection
    db = AsyncSurreal("http://localhost:8000")
    
    try:
        # Sign in and set up database
        await db.signin({"username": "root", "password": "root"})
        await db.use("test", "test")
        
        # Clean up any existing data
        await db.query("DELETE user;")
        
        # Method 1: Context Manager (Recommended)
        print("1. Using transaction context manager:")
        
        async with db.transaction() as tx:
            # All operations within this block are part of the transaction
            user1 = await tx.create("user:john", {
                "name": "John Doe", 
                "email": "john@example.com",
                "balance": 1000
            })
            print(f"Created user: {user1['name']}")
            
            user2 = await tx.create("user:jane", {
                "name": "Jane Smith",
                "email": "jane@example.com", 
                "balance": 500
            })
            print(f"Created user: {user2['name']}")
            
            # If any operation fails or an exception is raised,
            # the entire transaction will be rolled back automatically
            
        # Verify the data was committed
        users = await db.query("SELECT * FROM user ORDER BY id;")
        print(f"Users after transaction: {len(users)} users")
        
        # Method 2: Context Manager with Exception (Rollback)
        print("\n2. Transaction with rollback (simulated error):")
        
        try:
            async with db.transaction() as tx:
                await tx.create("user:bob", {
                    "name": "Bob Wilson",
                    "email": "bob@example.com",
                    "balance": 750
                })
                print("Created user Bob")
                
                # Simulate an error that should trigger rollback
                raise ValueError("Simulated error - this should rollback!")
                
        except ValueError as e:
            print(f"Caught expected error: {e}")
        
        # Verify Bob was NOT created (transaction rolled back)
        users = await db.query("SELECT * FROM user ORDER BY id;")
        print(f"Users after rollback: {len(users)} users (Bob should not exist)")
        
        # Method 3: Manual Transaction Control
        print("\n3. Manual transaction control:")
        
        await db.begin_transaction()
        try:
            # Transfer money between users
            await db.query("UPDATE user:john SET balance = balance - 200;")
            await db.query("UPDATE user:jane SET balance = balance + 200;")
            
            # Check balances
            balances = await db.query("SELECT id, balance FROM user WHERE id IN [user:john, user:jane];")
            print(f"Balances during transaction: {balances}")
            
            # Commit the transaction
            await db.commit_transaction()
            print("Transaction committed successfully")
            
        except Exception as e:
            # Rollback on any error
            await db.rollback_transaction()
            print(f"Transaction rolled back due to error: {e}")
        
        # Verify final state
        final_users = await db.query("SELECT * FROM user ORDER BY id;")
        for user in final_users:
            print(f"Final state - {user['name']}: ${user['balance']}")
        
        # Clean up
        await db.query("DELETE user;")
        
    except Exception as e:
        print(f"Error: {e}")


def sync_transaction_example():
    """Example of using transactions with sync connections."""
    print("\n=== Sync Transaction Example ===")
    
    # Create a sync connection
    db = Surreal("http://localhost:8000")
    
    try:
        # Sign in and set up database
        db.signin({"username": "root", "password": "root"})
        db.use("test", "test")
        
        # Clean up any existing data
        db.query("DELETE product;")
        
        print("Creating products with transaction:")
        
        # Use transaction context manager (sync version)
        with db.transaction() as tx:
            product1 = tx.create("product:laptop", {
                "name": "Gaming Laptop",
                "price": 1200.00,
                "stock": 10
            })
            print(f"Created product: {product1['name']}")
            
            product2 = tx.create("product:mouse", {
                "name": "Wireless Mouse", 
                "price": 25.99,
                "stock": 50
            })
            print(f"Created product: {product2['name']}")
            
            # Update stock levels
            tx.query("UPDATE product:laptop SET stock = stock - 1;")
            tx.query("UPDATE product:mouse SET stock = stock - 2;")
        
        # Verify the transaction was committed
        products = db.query("SELECT * FROM product ORDER BY id;")
        for product in products:
            print(f"Product: {product['name']}, Stock: {product['stock']}")
        
        # Clean up
        db.query("DELETE product;")
        
    except Exception as e:
        print(f"Error: {e}")


async def transaction_error_handling_example():
    """Example of advanced error handling with transactions."""
    print("\n=== Transaction Error Handling Example ===")
    
    db = AsyncSurreal("http://localhost:8000")
    
    try:
        await db.signin({"username": "root", "password": "root"})
        await db.use("test", "test")
        await db.query("DELETE account;")
        
        # Set up initial data
        await db.create("account:savings", {"balance": 1000})
        await db.create("account:checking", {"balance": 500})
        
        # Example: Money transfer with validation
        async def transfer_money(from_account: str, to_account: str, amount: float):
            async with db.transaction() as tx:
                # Get current balances
                from_bal = await tx.select(from_account)
                
                if from_bal["balance"] < amount:
                    raise ValueError(f"Insufficient funds: {from_bal['balance']} < {amount}")
                
                # Perform transfer
                await tx.query(f"UPDATE {from_account} SET balance = balance - {amount};")
                await tx.query(f"UPDATE {to_account} SET balance = balance + {amount};")
                
                print(f"Transferred ${amount} from {from_account} to {to_account}")
        
        # Valid transfer
        print("Attempting valid transfer...")
        await transfer_money("account:savings", "account:checking", 200)
        
        # Invalid transfer (should rollback)
        print("Attempting invalid transfer (insufficient funds)...")
        try:
            await transfer_money("account:checking", "account:savings", 1000)
        except ValueError as e:
            print(f"Transfer failed as expected: {e}")
        
        # Check final balances
        accounts = await db.query("SELECT * FROM account ORDER BY id;")
        for account in accounts:
            print(f"Final balance {account['id']}: ${account['balance']}")
        
        # Clean up
        await db.query("DELETE account;")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("SurrealDB Transaction Helper Examples")
    print("=====================================")
    
    # Run async examples
    asyncio.run(async_transaction_example())
    asyncio.run(transaction_error_handling_example())
    
    # Run sync example
    sync_transaction_example()
    
    print("\nAll examples completed!")