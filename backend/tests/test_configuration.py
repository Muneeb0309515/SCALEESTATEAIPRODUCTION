import os
import unittest
from backend.app.core.config import Settings


class ConfigurationTests(unittest.TestCase):
    def test_connection_requires_explicit_project_validation(self):
        original = os.environ.pop("SUPABASE_PROJECT_VALIDATED", None)
        try:
            settings = Settings(supabase_url="https://project.supabase.co", supabase_key="server-key")
            self.assertFalse(settings.has_project_supabase_connection)
        finally:
            if original is not None:
                os.environ["SUPABASE_PROJECT_VALIDATED"] = original

if __name__ == "__main__": unittest.main()
