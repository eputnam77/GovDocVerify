from typing import List
import re
import logging

logger = logging.getLogger(__name__)
from documentcheckertool.models import DocumentCheckResult, Severity

class FormattingChecker:
    def check_section_symbol_usage(self, lines: List[str]) -> DocumentCheckResult:
        """Check for proper section symbol usage."""
        logger.debug("Starting section symbol check")
        issues = []

        # Pattern for valid single section symbol usage
        valid_single_pattern = re.compile(r'§\s+\d+(?:\.\d+)*(?:\([a-z0-9]+\))*')
        logger.debug(f"Valid single pattern: {valid_single_pattern.pattern}")

        # Pattern for valid "or" pattern with single section symbol
        valid_or_pattern = re.compile(r'§\s+\d+(?:\.\d+)*(?:\([a-z0-9]+\))*\s+or\s+\d+(?:\.\d+)*(?:\([a-z0-9]+\))*')
        logger.debug(f"Valid 'or' pattern: {valid_or_pattern.pattern}")

        # Pattern for invalid multiple section symbols (should be caught)
        invalid_multiple_pattern = re.compile(r'§§\s+\d+(?:\.\d+)*(?:\([a-z0-9]+\))*(?:\s+or\s+\d+(?:\.\d+)*(?:\([a-z0-9]+\))*)?')
        logger.debug(f"Invalid multiple pattern: {invalid_multiple_pattern.pattern}")

        for i, line in enumerate(lines, 1):
            logger.debug(f"Processing line {i}: '{line}'")

            # Skip U.S.C. and 14 CFR citations
            if re.search(r'U\.S\.C\.\s*(?:§|§§)', line) or re.search(r'14 CFR\s*§', line):
                logger.debug(f"Line {i} contains U.S.C. or 14 CFR citation - skipping")
                continue

            # Check for invalid multiple section symbols (should be caught)
            if '§§' in line:
                logger.debug(f"Line {i} contains multiple section symbols")
                if invalid_multiple_pattern.search(line):
                    logger.debug(f"Found incorrect multiple section symbol usage in line {i}")
                    issues.append({
                        "message": f"Incorrect multiple section symbol usage in line {i} - use single § for multiple sections",
                        "severity": Severity.WARNING,
                        "line_number": i,
                        "checker": "FormattingChecker"
                    })
            # Check for single section symbol
            elif '§' in line:
                logger.debug(f"Line {i} contains single section symbol")
                # Check for valid "or" pattern first
                if valid_or_pattern.search(line):
                    logger.debug(f"Line {i} matches valid 'or' pattern - skipping")
                    continue

                # Then check for valid single section pattern
                if not valid_single_pattern.search(line):
                    logger.debug(f"Found incorrect section symbol usage in line {i}")
                    issues.append({
                        "message": f"Incorrect section symbol usage in line {i}",
                        "severity": Severity.WARNING,
                        "line_number": i,
                        "checker": "FormattingChecker"
                    })

        logger.debug(f"Section symbol check complete. Found {len(issues)} issues")
        return DocumentCheckResult(success=len(issues) == 0, severity=Severity.WARNING if issues else None, issues=issues)