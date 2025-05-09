import unittest
from documentcheckertool.checks.content_checks import ContentChecker
from documentcheckertool.models import DocumentType

class TestContentChecker(unittest.TestCase):
    def setUp(self):
        self.checker = ContentChecker()

    def test_boilerplate_text(self):
        """Test required boilerplate text checking."""
        ac_content = """
        This AC is not mandatory and does not constitute a regulation.
        This material does not change or create any additional requirements.
        """
        result = self.checker.check_boilerplate_text(ac_content.split('\n'), DocumentType.ADVISORY_CIRCULAR)
        self.assertTrue(result.success)

    def test_required_language(self):
        """Test required language checking."""
        fr_content = """
        The FAA invites interested people to take part in this rulemaking.
        Paperwork Reduction Act Burden Statement
        """
        result = self.checker.check_required_language(fr_content.split('\n'), DocumentType.FEDERAL_REGISTER_NOTICE)
        self.assertTrue(result.success)
