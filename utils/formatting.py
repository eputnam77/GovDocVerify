from typing import Dict, List
from models import DocumentCheckResult

def format_results_to_html(results: Dict[str, List[DocumentCheckResult]]) -> str:
    """Format check results into HTML."""
    html = "<div class='results'>"
    for category, category_results in results.items():
        html += f"<h3>{category}</h3>"
        for result in category_results:
            status = "success" if result.success else "failure"
            html += f"<div class='{status}'>"
            html += f"<p>{result.message}</p>"
            if result.issues:
                html += "<ul>"
                for issue in result.issues:
                    html += f"<li>{issue}</li>"
                html += "</ul>"
            html += "</div>"
    html += "</div>"
    return html 