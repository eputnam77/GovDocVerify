from typing import Dict, List
from documentcheckertool.models import DocumentCheckResult

def format_results_to_html(results: DocumentCheckResult) -> str:
    """Format check results as HTML."""
    return results.to_html()