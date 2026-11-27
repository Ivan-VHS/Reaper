from __future__ import annotations

import math
import unittest

from reaper.research_math_contracts import (
    EXPECTED_FUNCTIONS,
    ResearchContractError,
    find_math_kernel,
    load_research_math_catalog,
    prepare_math_kernel_call,
    validate_catalog_document,
    validate_pytyliki_kernel_manifest,
)


class MathematicalResearchContractTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_research_math_catalog()

    def test_catalog_has_17_domains_and_51_unique_functions(self):
        self.assertEqual(len(self.catalog["areas"]), 17)
        functions = [
            function
            for area in self.catalog["areas"]
            for function in area["functions"]
        ]
        self.assertEqual(len(functions), EXPECTED_FUNCTIONS)
        self.assertEqual(len({item["id"] for item in functions}), EXPECTED_FUNCTIONS)
        self.assertEqual(len({item["api"] for item in functions}), EXPECTED_FUNCTIONS)
        self.assertTrue(all(len(area["functions"]) == 3 for area in self.catalog["areas"]))

    def test_riemann_call_plan_is_typed_and_never_executes(self):
        plan = prepare_math_kernel_call(
            "riemann.dirichlet_partial",
            {"sigma": 2.0, "t": 0.0, "terms": 256},
            self.catalog,
        )
        payload = plan.to_payload()
        self.assertEqual(payload["api"], "pl_math_riemann_dirichlet")
        self.assertEqual(payload["backend"], "pytyliki.c11")
        self.assertEqual(payload["claim_status"], "EXPERIMENTAL_EVIDENCE_ONLY")
        self.assertFalse(payload["execution_performed"])

    def test_rejects_boolean_as_integer_and_rejects_non_finite_number(self):
        with self.assertRaises(ResearchContractError):
            prepare_math_kernel_call(
                "riemann.dirichlet_partial",
                {"sigma": 2.0, "t": 0.0, "terms": True},
                self.catalog,
            )
        with self.assertRaises(ResearchContractError):
            prepare_math_kernel_call(
                "riemann.eta_partial",
                {"sigma": 0.5, "t": math.inf, "terms": 32},
                self.catalog,
            )

    def test_rejects_unknown_or_missing_arguments(self):
        with self.assertRaises(ResearchContractError):
            prepare_math_kernel_call(
                "riemann.eta_partial",
                {"sigma": 1.0, "terms": 32},
                self.catalog,
            )
        with self.assertRaises(ResearchContractError):
            find_math_kernel("riemann.prove_all_zeros", self.catalog)

    def test_accepts_a_valid_finite_sat_instance(self):
        plan = prepare_math_kernel_call(
            "complexity.sat_find_bounded",
            {
                "variables": 2,
                "literals": [1, 2, -1],
                "literal_count": 3,
                "clause_offsets": [0, 2, 3],
                "clause_count": 2,
                "assignment_budget": 4,
            },
            self.catalog,
        )
        self.assertEqual(plan.evidence, "bounded_exhaustive_search")

    def test_prime_field_contract_rejects_composite_modulus(self):
        with self.assertRaises(ResearchContractError):
            prepare_math_kernel_call(
                "bsd.curve_point_count_mod_prime",
                {"a": 0, "b": 1, "prime": 9},
                self.catalog,
            )

    def test_matrix_plan_requires_finite_values(self):
        with self.assertRaises(ResearchContractError):
            prepare_math_kernel_call(
                "matrix.multiply_f64",
                {
                    "left": [1.0, 0.0, 0.0, 1.0],
                    "right": [1.0, math.nan, 0.0, 1.0],
                    "dimension": 2,
                },
                self.catalog,
            )

    def test_catalog_rejects_an_unsupported_claim_policy(self):
        altered = {
            **self.catalog,
            "problem_policy": {
                **self.catalog["problem_policy"],
                "open_problem_results": "PROVED",
            },
        }
        with self.assertRaises(ResearchContractError):
            validate_catalog_document(altered)

    def test_pyтиliki_manifest_matches_the_canonical_registry(self):
        manifest = {
            "schema": "pytyliki.mathematical-research-kernels.v1",
            "version": "1.0.0",
            "owner": "Pytyliki",
            "contract_schema": "reaper.mathematical-research-contracts.v1",
            "execution_performed": False,
            "functions": [
                {"id": function["id"], "api": function["api"]}
                for area in self.catalog["areas"]
                for function in area["functions"]
            ],
        }
        validate_pytyliki_kernel_manifest(manifest, self.catalog)
        manifest["functions"][0], manifest["functions"][1] = (
            manifest["functions"][1], manifest["functions"][0]
        )
        with self.assertRaises(ResearchContractError):
            validate_pytyliki_kernel_manifest(manifest, self.catalog)


if __name__ == "__main__":
    unittest.main()
