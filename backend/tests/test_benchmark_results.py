import unittest

from backend.app.benchmarks.results import (
    BenchmarkStatus,
    BenchmarkStep,
    BenchmarkStepResult,
    BenchmarkWorkflowResult,
)


class BenchmarkResultTests(unittest.TestCase):
    def result(self) -> BenchmarkWorkflowResult:
        return BenchmarkWorkflowResult(
            property_id="realtyapi-1",
            county="Travis County",
            source="realtyapi",
            steps={
                BenchmarkStep.SEARCH: BenchmarkStepResult(status=BenchmarkStatus.PASS),
                BenchmarkStep.DETAIL: BenchmarkStepResult(status=BenchmarkStatus.PASS),
                BenchmarkStep.DEAL_ANALYSIS: BenchmarkStepResult(
                    status=BenchmarkStatus.PARTIAL,
                    message="Debt and repairs are UNKNOWN",
                ),
                BenchmarkStep.OUTREACH: BenchmarkStepResult(status=BenchmarkStatus.UNKNOWN),
            },
        )

    def test_reports_failed_and_incomplete_steps_without_inventing_scores(self):
        result = self.result()
        self.assertEqual(result.failed_steps(), [])
        self.assertEqual(
            result.incomplete_steps(),
            [BenchmarkStep.DEAL_ANALYSIS, BenchmarkStep.OUTREACH],
        )
        self.assertIsNone(result.mao)
        self.assertIsNone(result.arv)

    def test_failure_is_preserved(self):
        result = self.result()
        result.steps[BenchmarkStep.SEARCH] = BenchmarkStepResult(
            status=BenchmarkStatus.FAIL,
            message="Provider unavailable",
        )
        self.assertEqual(result.failed_steps(), [BenchmarkStep.SEARCH])


if __name__ == "__main__":
    unittest.main()
