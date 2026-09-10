import unittest
from pydantic import ValidationError
from backend.app.data.workflow_models import TransactionCreate


class WorkflowModelTests(unittest.TestCase):
    def test_transaction_supports_documented_exit_strategies_only(self):
        self.assertEqual(TransactionCreate(deal_id="deal", buyer_id="buyer", exit_strategy="assignment").exit_strategy, "assignment")
        with self.assertRaises(ValidationError):
            TransactionCreate(deal_id="deal", buyer_id="buyer", exit_strategy="unsupported")

if __name__ == "__main__": unittest.main()
