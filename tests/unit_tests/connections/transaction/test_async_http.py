from unittest import main, IsolatedAsyncioTestCase

from surrealdb.connections.async_http import AsyncHttpSurrealConnection


class TestAsyncHttpTransactions(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.url = "http://localhost:8000"
        self.password = "root"
        self.username = "root"
        self.vars_params = {
            "username": self.username,
            "password": self.password,
        }
        self.database_name = "test_db"
        self.namespace = "test_ns"
        self.connection = AsyncHttpSurrealConnection(self.url)
        _ = await self.connection.signin(self.vars_params)
        _ = await self.connection.use(namespace=self.namespace, database=self.database_name)
        await self.connection.query("DELETE transaction_test;")

    async def test_manual_transaction_methods(self):
        """Test manual transaction methods: begin, commit, rollback"""
        # Test begin and commit
        await self.connection.begin_transaction()
        await self.connection.create("transaction_test:1", {"name": "test1"})
        await self.connection.commit_transaction()
        
        # Verify data was committed
        result = await self.connection.query("SELECT * FROM transaction_test WHERE id = transaction_test:1;")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "test1")
        
        # Test begin and rollback
        await self.connection.begin_transaction()
        await self.connection.create("transaction_test:2", {"name": "test2"})
        await self.connection.rollback_transaction()
        
        # Verify data was rolled back
        result = await self.connection.query("SELECT * FROM transaction_test WHERE id = transaction_test:2;")
        self.assertEqual(len(result), 0)
        
        # Clean up
        await self.connection.query("DELETE transaction_test;")

    async def test_transaction_context_manager_success(self):
        """Test transaction context manager with successful operations"""
        async with self.connection.transaction() as tx:
            await tx.create("transaction_test:1", {"name": "test1"})
            await tx.create("transaction_test:2", {"name": "test2"})
        
        # Verify both records were committed
        result = await self.connection.query("SELECT * FROM transaction_test ORDER BY id;")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "test1")
        self.assertEqual(result[1]["name"], "test2")
        
        # Clean up
        await self.connection.query("DELETE transaction_test;")

    async def test_transaction_context_manager_rollback(self):
        """Test transaction context manager with exception rollback"""
        try:
            async with self.connection.transaction() as tx:
                await tx.create("transaction_test:1", {"name": "test1"})
                await tx.create("transaction_test:2", {"name": "test2"})
                # Simulate an error
                raise ValueError("Test error")
        except ValueError:
            pass  # Expected exception
        
        # Verify no records were committed (rolled back)
        result = await self.connection.query("SELECT * FROM transaction_test;")
        self.assertEqual(len(result), 0)

    async def test_transaction_crud_operations(self):
        """Test various CRUD operations within a transaction"""
        async with self.connection.transaction() as tx:
            # Create
            created = await tx.create("transaction_test:1", {"name": "original", "value": 100})
            self.assertEqual(created["name"], "original")
            
            # Update
            updated = await tx.update("transaction_test:1", {"name": "updated"})
            self.assertEqual(updated["name"], "updated")
            self.assertEqual(updated["value"], 100)  # Should preserve other fields
            
            # Merge
            merged = await tx.merge("transaction_test:1", {"status": "active"})
            self.assertEqual(merged["name"], "updated")
            self.assertEqual(merged["status"], "active")
            
            # Select within transaction
            selected = await tx.select("transaction_test:1")
            self.assertEqual(selected["name"], "updated")
            self.assertEqual(selected["status"], "active")
        
        # Verify changes were committed
        result = await self.connection.query("SELECT * FROM transaction_test:1;")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "updated")
        self.assertEqual(result[0]["status"], "active")
        
        # Clean up
        await self.connection.query("DELETE transaction_test;")

    async def test_transaction_query_operations(self):
        """Test raw query operations within a transaction"""
        async with self.connection.transaction() as tx:
            # Use query method within transaction
            await tx.query("CREATE transaction_test:1 SET name = 'query_test', value = 200;")
            await tx.query("CREATE transaction_test:2 SET name = 'query_test2', value = 300;")
            
            # Query within transaction
            result = await tx.query("SELECT * FROM transaction_test WHERE name CONTAINS 'query';")
            self.assertEqual(len(result), 2)
        
        # Verify changes were committed
        result = await self.connection.query("SELECT * FROM transaction_test ORDER BY id;")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "query_test")
        self.assertEqual(result[1]["name"], "query_test2")
        
        # Clean up
        await self.connection.query("DELETE transaction_test;")


if __name__ == "__main__":
    main()