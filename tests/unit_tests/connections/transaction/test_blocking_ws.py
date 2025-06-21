from unittest import main, TestCase

from surrealdb.connections.blocking_ws import BlockingWsSurrealConnection


class TestBlockingWsTransactions(TestCase):

    def setUp(self):
        self.url = "ws://localhost:8000/rpc"
        self.password = "root"
        self.username = "root"
        self.vars_params = {
            "username": self.username,
            "password": self.password,
        }
        self.database_name = "test_db"
        self.namespace = "test_ns"
        self.connection = BlockingWsSurrealConnection(self.url)
        _ = self.connection.signin(self.vars_params)
        _ = self.connection.use(namespace=self.namespace, database=self.database_name)
        self.connection.query("DELETE transaction_test;")

    def test_manual_transaction_methods(self):
        """Test manual transaction methods: begin, commit, rollback"""
        # Test begin and commit
        self.connection.begin_transaction()
        self.connection.create("transaction_test:1", {"name": "test1"})
        self.connection.commit_transaction()
        
        # Verify data was committed
        result = self.connection.query("SELECT * FROM transaction_test WHERE id = transaction_test:1;")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "test1")
        
        # Test begin and rollback
        self.connection.begin_transaction()
        self.connection.create("transaction_test:2", {"name": "test2"})
        self.connection.rollback_transaction()
        
        # Verify data was rolled back
        result = self.connection.query("SELECT * FROM transaction_test WHERE id = transaction_test:2;")
        self.assertEqual(len(result), 0)
        
        # Clean up
        self.connection.query("DELETE transaction_test;")

    def test_transaction_context_manager_success(self):
        """Test transaction context manager with successful operations"""
        with self.connection.transaction() as tx:
            tx.create("transaction_test:1", {"name": "test1"})
            tx.create("transaction_test:2", {"name": "test2"})
        
        # Verify both records were committed
        result = self.connection.query("SELECT * FROM transaction_test ORDER BY id;")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "test1")
        self.assertEqual(result[1]["name"], "test2")
        
        # Clean up
        self.connection.query("DELETE transaction_test;")

    def test_transaction_context_manager_rollback(self):
        """Test transaction context manager with exception rollback"""
        try:
            with self.connection.transaction() as tx:
                tx.create("transaction_test:1", {"name": "test1"})
                tx.create("transaction_test:2", {"name": "test2"})
                # Simulate an error
                raise ValueError("Test error")
        except ValueError:
            pass  # Expected exception
        
        # Verify no records were committed (rolled back)
        result = self.connection.query("SELECT * FROM transaction_test;")
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    main()