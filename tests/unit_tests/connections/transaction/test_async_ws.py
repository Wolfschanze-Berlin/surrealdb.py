from unittest import main, IsolatedAsyncioTestCase

from surrealdb.connections.async_ws import AsyncWsSurrealConnection


class TestAsyncWsTransactions(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.url = "ws://localhost:8000/rpc"
        self.password = "root"
        self.username = "root"
        self.vars_params = {
            "username": self.username,
            "password": self.password,
        }
        self.database_name = "test_db"
        self.namespace = "test_ns"
        self.connection = AsyncWsSurrealConnection(self.url)
        await self.connection.connect()
        _ = await self.connection.signin(self.vars_params)
        _ = await self.connection.use(namespace=self.namespace, database=self.database_name)
        await self.connection.query("DELETE transaction_test;")

    async def asyncTearDown(self):
        if hasattr(self, 'connection'):
            await self.connection.close()

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


if __name__ == "__main__":
    main()