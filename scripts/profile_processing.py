import cProfile
import pstats

from govdocverify.models import DocumentCheckResult, Severity

# create a sample DocumentCheckResult with some issues
res = DocumentCheckResult(success=False)
for i in range(1000):
    res.add_issue(f"msg{i}", Severity.ERROR, line_number=i, category="test")

profile_path = "perf/artifacts/build_results_dict.pstats"
cProfile.run("build_results_dict(res)", profile_path)

stats = pstats.Stats(profile_path)
stats.sort_stats("cumulative").print_stats(10)
