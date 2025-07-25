import cProfile
import pstats
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# Minimal DocumentCheckResult class
@dataclass
class DocumentCheckResult:
    success: bool = True
    issues: List[Dict[str, Any]] = field(default_factory=list)
    checker_name: Optional[str] = None
    score: float = 1.0
    severity: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    per_check_results: Optional[Dict[str, Dict[str, Any]]] = None


def _check_results_have_issues(results_dict: Dict[str, Dict[str, Any]]) -> bool:
    for checks in results_dict.values():
        for res in checks.values():
            issues = getattr(res, "issues", []) if hasattr(res, "issues") else res.get("issues", [])
            if issues:
                return True
    return False


def _create_fallback_results_dict(results: DocumentCheckResult) -> Dict[str, Dict[str, Any]]:
    return {
        "all": {
            "all": {
                "success": results.success,
                "issues": results.issues,
                "details": getattr(results, "details", {}),
            }
        }
    }


def build_results_dict(results: DocumentCheckResult) -> Dict[str, Dict[str, Any]]:
    results_dict = getattr(results, "per_check_results", None)
    if not results_dict:
        return _create_fallback_results_dict(results)
    has_issues = _check_results_have_issues(results_dict)
    if not has_issues and results.issues:
        return _create_fallback_results_dict(results)
    return results_dict


# Create sample result
res = DocumentCheckResult(success=False)
for i in range(1000):
    res.issues.append({"message": "msg", "severity": i % 3})
res.per_check_results = None

profile_path = "perf/artifacts/build_results_dict.pstats"
cProfile.run("build_results_dict(res)", profile_path)

stats = pstats.Stats(profile_path)
stats.sort_stats("cumulative").print_stats(10)
