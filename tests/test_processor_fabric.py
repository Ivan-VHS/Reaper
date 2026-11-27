import unittest

from reaper.processor_fabric import (
    ProcessorFabricTypedIRError,
    ProcessorInputBinding,
    ProcessorResourceBinding,
    ProcessorSemanticBinding,
    lower_processor_fabric,
)


def valid_input():
    source = "device sensor { read status }\n".encode("utf-8")
    report = {
        "schema": "reaper.processor-fabric-import-report.v1",
        "source": {
            "sha256": __import__("hashlib").sha256(source).hexdigest(),
            "byte_length": len(source),
            "offset_unit": "utf8-byte",
        },
        "host_evidence": {"generation": 7},
        "fabric": {
            "generation": 7,
            "node_count": 4,
            "edge_count": 2,
            "nodes": [
                {"id": 1, "kind": "process-pool", "state": "declared",
                 "parent_id": None, "generation": 7},
                {"id": 2, "kind": "process", "state": "ready",
                 "parent_id": 1, "generation": 7},
                {"id": 3, "kind": "device", "state": "declared",
                 "parent_id": None, "generation": 7, "semantic_ref": "sensor-device"},
                {"id": 4, "kind": "process", "state": "ready",
                 "parent_id": 1, "generation": 7},
            ],
            "edges": [
                {"from_id": 2, "to_id": 3, "kind": "uses"},
                {"from_id": 2, "to_id": 4, "kind": "depends-on"},
            ],
        },
        "constructs": [{
            "processId": 2,
            "semanticId": "pytyliki.device.v1",
            "kind": "device",
            "name": "sensor",
            "sourceSpan": {"start": 0, "length": len(source) - 1},
            "bodySpan": {"start": source.index(b"{"), "length": len(b"{ read status }")},
            "resourceRefs": [3],
            "dependencyRefs": [4],
        }],
        "resource_contract": {
            "schema": "pytyliki.hardware-resource-contract.v1",
            "version": 1,
            "generation": 7,
            "devices": [{"id": "sensor-device", "generation": 7}],
            "address_spaces": [],
            "memory_regions": [],
            "register_banks": [],
            "dma_buffers": [],
        },
        "semantic_admission": {"canonical_ir_emitted": False},
        "execution_performed": False,
        "hardware_access_performed": False,
    }
    semantic = {
        "pytyliki.device.v1": ProcessorSemanticBinding(
            semantic_id="pytyliki.device.v1",
            operation="sensor.read",
            input_types=("Device<sensor>",),
            output_type="u32",
            effects=("device.read",),
            inputs=(ProcessorInputBinding("resource", 3, 0),),
        )
    }
    resources = {
        3: ProcessorResourceBinding(
            ppf_node_id=3,
            semantic_ref="sensor-device",
            kind="device",
            value_type="Device<sensor>",
            effects=(),
            owner="shared",
            generation=7,
        )
    }
    return source, report, semantic, resources


class ProcessorFabricTypedIRTests(unittest.TestCase):
    def lower(self, *, effects=("device.read",), report=None, semantic=None,
              resources=None, source=None):
        base_source, base_report, base_semantic, base_resources = valid_input()
        return lower_processor_fabric(
            report or base_report,
            base_source if source is None else source,
            semantic_bindings=base_semantic if semantic is None else semantic,
            resource_bindings=base_resources if resources is None else resources,
            granted_effects=effects,
        )

    def test_lowers_to_reaper_typed_semantic_graph_and_preserves_byte_spans(self):
        result = self.lower()
        self.assertEqual(result["schema"], "reaper.processor-fabric-typed-ir.v1")
        self.assertTrue(result["verification"]["canonical_typed_ir_emitted"])
        self.assertFalse(result["verification"]["stack_vm_bytecode_emitted"])
        self.assertEqual(result["source"]["offset_unit"], "utf8-byte")
        self.assertEqual(result["constructs"][0]["source_span"]["start"], 0)
        source, _, _, _ = valid_input()
        self.assertEqual(result["constructs"][0]["body_span"]["start"], source.index(b"{"))
        self.assertEqual(len(result["semantic_graph"]["nodes"]), 2)
        self.assertEqual(result["semantic_graph"]["edges"][0]["target_port"], 0)
        self.assertEqual(result["control_dependencies"], [{
            "process_id": 2, "requires_process_id": 4
        }])

    def test_rejects_ungranted_effects(self):
        with self.assertRaisesRegex(ProcessorFabricTypedIRError, "RPR-PFT-0041"):
            self.lower(effects=())

    def test_rejects_source_digest_and_generation_mismatch(self):
        source, report, semantic, resources = valid_input()
        with self.assertRaisesRegex(ProcessorFabricTypedIRError, "RPR-PFT-0006"):
            self.lower(source=source + b"# changed\n")
        report["fabric"]["generation"] = 8
        with self.assertRaisesRegex(ProcessorFabricTypedIRError, "RPR-PFT-0009"):
            self.lower(report=report)

    def test_rejects_unresolved_semantic_binding(self):
        source, report, _semantic, resources = valid_input()
        with self.assertRaisesRegex(ProcessorFabricTypedIRError, "RPR-PFT-0039"):
            self.lower(semantic={})

    def test_rejects_dma_device_ownership_and_unknown_coherency(self):
        source, report, semantic, resources = valid_input()
        report["fabric"]["nodes"][2]["kind"] = "dma-buffer"
        report["fabric"]["nodes"][2]["semantic_ref"] = "dma0"
        report["resource_contract"]["dma_buffers"] = [{"id": "dma0", "generation": 7}]
        resources[3] = ProcessorResourceBinding(
            ppf_node_id=3, semantic_ref="dma0", kind="dma-buffer",
            value_type="DmaBuffer", effects=("dma.read",), owner="shared",
            generation=7, dma_state="device_owned", coherency="unknown"
        )
        semantic["pytyliki.device.v1"] = ProcessorSemanticBinding(
            semantic_id="pytyliki.device.v1", operation="dma.consume",
            input_types=("DmaBuffer",), output_type="u32", effects=("dma.read",),
            inputs=(ProcessorInputBinding("resource", 3, 0),)
        )
        with self.assertRaisesRegex(ProcessorFabricTypedIRError, "RPR-PFT-0033"):
            self.lower(report=report, semantic=semantic, resources=resources,
                       effects=("dma.read",))

    def test_rejects_missing_input_and_type_mismatch(self):
        source, report, semantic, resources = valid_input()
        semantic["pytyliki.device.v1"] = ProcessorSemanticBinding(
            semantic_id="pytyliki.device.v1", operation="sensor.read",
            input_types=("u64",), output_type="u32", effects=("device.read",),
            inputs=(ProcessorInputBinding("resource", 3, 0),)
        )
        with self.assertRaisesRegex(ProcessorFabricTypedIRError, "RPR-PFT-0049"):
            self.lower(semantic=semantic)

    def test_rejects_process_dependency_cycles(self):
        source, report, semantic, resources = valid_input()
        report["fabric"]["edges"].append(
            {"from_id": 4, "to_id": 2, "kind": "depends-on"}
        )
        report["fabric"]["edge_count"] += 1
        with self.assertRaisesRegex(ProcessorFabricTypedIRError, "RPR-PFT-0004"):
            self.lower(report=report)


if __name__ == "__main__":
    unittest.main()
