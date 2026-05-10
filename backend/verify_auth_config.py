import os
import sys
from unittest.mock import patch
import unittest

# We need to mock the dependencies of auth.py since they are not installed in this environment
# and we only care about the module-level SECRET_KEY logic.

class TestAuthConfig(unittest.TestCase):
    def test_missing_secret_key(self):
        """Test that importing auth raises RuntimeError when JWT_SECRET_KEY is missing."""
        # Use a fresh environment for the import
        with patch.dict(os.environ, clear=True):
            # Ensure JWT_SECRET_KEY is NOT in os.environ
            if "JWT_SECRET_KEY" in os.environ:
                del os.environ["JWT_SECRET_KEY"]

            # Mock the modules that auth.py imports but we don't have installed
            with patch.dict(sys.modules, {
                'jose': unittest.mock.MagicMock(),
                'passlib': unittest.mock.MagicMock(),
                'passlib.context': unittest.mock.MagicMock(),
                'fastapi': unittest.mock.MagicMock(),
                'fastapi.security': unittest.mock.MagicMock(),
                'sqlalchemy': unittest.mock.MagicMock(),
                'sqlalchemy.orm': unittest.mock.MagicMock(),
                'database': unittest.mock.MagicMock(),
                'models': unittest.mock.MagicMock(),
                'schemas': unittest.mock.MagicMock(),
                'dotenv': unittest.mock.MagicMock(),
            }):
                # We need to force a reload or a fresh import because auth might already be in sys.modules
                if 'auth' in sys.modules:
                    del sys.modules['auth']

                with self.assertRaises(RuntimeError) as cm:
                    import auth

                self.assertIn("JWT_SECRET_KEY environment variable is not set", str(cm.exception))

    def test_present_secret_key(self):
        """Test that auth module loads correctly when JWT_SECRET_KEY is present."""
        test_secret = "test-secret-key-12345"
        with patch.dict(os.environ, {"JWT_SECRET_KEY": test_secret}):
            with patch.dict(sys.modules, {
                'jose': unittest.mock.MagicMock(),
                'passlib': unittest.mock.MagicMock(),
                'passlib.context': unittest.mock.MagicMock(),
                'fastapi': unittest.mock.MagicMock(),
                'fastapi.security': unittest.mock.MagicMock(),
                'sqlalchemy': unittest.mock.MagicMock(),
                'sqlalchemy.orm': unittest.mock.MagicMock(),
                'database': unittest.mock.MagicMock(),
                'models': unittest.mock.MagicMock(),
                'schemas': unittest.mock.MagicMock(),
                'dotenv': unittest.mock.MagicMock(),
            }):
                if 'auth' in sys.modules:
                    del sys.modules['auth']

                import auth
                self.assertEqual(auth.SECRET_KEY, test_secret)

if __name__ == "__main__":
    unittest.main()
