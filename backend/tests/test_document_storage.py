import unittest
from backend.app.services.document_storage import _safe_filename


class DocumentStorageTests(unittest.TestCase):
    def test_filename_remains_in_a_safe_single_path_component(self):
        self.assertEqual(_safe_filename("../../closing agreement.pdf"), "closingagreement.pdf")
        self.assertEqual(_safe_filename(None), "document")

if __name__ == "__main__": unittest.main()
