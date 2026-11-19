from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class VerifiedPrWorkflowTests(unittest.TestCase):
    def test_workflow_is_review_gated_and_least_privilege(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "reaper-verified-pr.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("pull-requests: write", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertIn("gh pr create", workflow)
        self.assertIn("--draft", workflow)
        self.assertIn("--base main", workflow)
        self.assertNotIn("gh pr merge", workflow)

    def test_workflow_requires_validated_main_ancestor(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "reaper-verified-pr.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("git check-ref-format --branch", workflow)
        self.assertIn("git merge-base --is-ancestor origin/main", workflow)
        self.assertIn("python -m unittest discover -s tests -v", workflow)
        self.assertIn("ctest --test-dir build --output-on-failure", workflow)


if __name__ == "__main__":
    unittest.main()
