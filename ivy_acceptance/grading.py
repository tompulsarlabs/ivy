"""Deterministic citation controls; semantic assessment remains independent work."""
import hashlib
from .canonical import digest


def check_citations(output, visible_files):
    failures = []
    if type(output) is not dict or set(output) != {"findings"} or type(output["findings"]) is not list:
        failures.append("invalid_output_schema")
    else:
        for finding in output["findings"]:
            if (type(finding) is not dict or set(finding) != {"path", "line", "explanation"}
                    or type(finding["path"]) is not str or type(finding["line"]) is not int
                    or type(finding["explanation"]) is not str or not finding["explanation"].strip()):
                failures.append("invalid_finding_schema")
                continue
            source = visible_files.get("fixture/" + finding["path"])
            if source is None:
                failures.append("citation_source_missing")
            elif not 1 <= finding["line"] <= len(source.splitlines()):
                failures.append("citation_line_out_of_range")
    return {"schema_version": 1, "criterion": "citation_integrity", "output_sha256": digest(output),
            "visible_files_sha256": digest({name: hashlib.sha256(body).hexdigest()
                                            for name, body in sorted(visible_files.items())}),
            "status": "fail" if failures else "pass", "failures": failures,
            "semantic_status": "unverified", "benchmark_status": "evidence_incomplete"}
