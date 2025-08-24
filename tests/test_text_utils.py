# python -m pytest tests/test_text_utils.py -v --cov=govdocverify.utils.text_utils

import pytest

from govdocverify.utils.terminology_utils import TerminologyManager
from govdocverify.utils.text_utils import (
    calculate_passive_voice_percentage,
    calculate_readability_metrics,
    count_syllables,
    count_words,
    get_valid_words,
    normalize_document_type,
    normalize_heading,
    normalize_reference,
    split_into_sentences,
    split_sentences,
)


class TestTextUtils:
    """Test cases for text utility functions."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.terminology_manager = TerminologyManager()

    def test_split_sentences_basic(self):
        """Test basic sentence splitting."""
        # Empty text
        assert split_sentences("") == []

        # Single sentence
        assert split_sentences("This is a test.") == ["This is a test."]

        # Multiple sentences
        text = "This is sentence one. This is sentence two."
        assert split_sentences(text) == ["This is sentence one.", "This is sentence two."]

        # Multiple punctuation types
        text = "What? This is amazing! Really?"
        assert split_sentences(text) == ["What?", "This is amazing!", "Really?"]

    def test_split_sentences_handles_closing_parentheses(self):
        """Punctuation followed by a closing bracket should still end the sentence."""
        text = "First sentence.) Second one."
        assert split_sentences(text) == ["First sentence.", "Second one."]

    def test_split_sentences_abbreviations(self):
        """Test sentence splitting with abbreviations."""
        # Common abbreviations
        text = "Dr. Smith is here. Mr. Jones too."
        assert split_sentences(text) == ["Dr. Smith is here.", "Mr. Jones too."]

        # Multiple abbreviations
        text = "Dr. Smith went to the U.S. He visited the FAA."
        assert split_sentences(text) == ["Dr. Smith went to the U.S.", "He visited the FAA."]

        # Abbreviations at end
        text = "He works for the U.S."
        assert split_sentences(text) == ["He works for the U.S."]

    def test_count_words_basic(self):
        """Test basic word counting."""
        # Empty text
        assert count_words("") == 0

        # Single word
        assert count_words("hello") == 1

        # Multiple words
        assert count_words("Hello world") == 2
        assert count_words("Hello, world!") == 2

    def test_count_words_special(self):
        """Test word counting with special cases."""
        # Hyphenated words
        assert count_words("well-known example") == 2

        # Numbers and special characters
        assert count_words("123 test-case") == 2

        # Email addresses
        assert count_words("test@example.com") == 1
        assert count_words("Send to test@example.com today") == 3

        # Multiple spaces
        assert count_words("  multiple   spaces  ") == 2

    def test_count_words_numbers_with_decimals_and_signs(self):
        """Decimals and signed numbers count as single words."""
        text = "pi is about 3.14 and temp is -4.5"
        assert count_words(text) == 8

    def test_count_words_contractions(self):
        """Contractions should count as single words."""
        assert count_words("Don't stop") == 2
        assert count_words("We're testing") == 2

    def test_normalize_reference(self):
        """Test reference normalization."""
        # Empty text
        assert normalize_reference("") == ""

        # Basic normalization
        assert normalize_reference("Test Reference") == "test reference"
        assert normalize_reference("  Extra  Spaces  ") == "extra spaces"

        # Special characters
        assert normalize_reference("Test-Reference!") == "test reference"
        assert normalize_reference("Test & Reference") == "test reference"
        assert normalize_reference("Test/Reference\\Path") == "test reference path"

    def test_count_syllables(self):
        """Test syllable counting."""
        # Basic words
        assert count_syllables("hello") == 2
        assert count_syllables("world") == 1
        assert count_syllables("beautiful") == 3

        # Words ending in 'e'
        assert count_syllables("make") == 1
        assert count_syllables("time") == 1

        # Single letters
        assert count_syllables("a") == 1
        assert count_syllables("I") == 1

        # Words with no vowels
        assert count_syllables("rhythm") == 1

        # Complex words
        assert count_syllables("education") == 4
        assert count_syllables("university") == 5

    def test_normalize_heading(self):
        """Test heading normalization."""
        # Empty text
        assert normalize_heading("") == ""

        # Basic normalization
        assert normalize_heading("Test Heading") == "Test Heading"
        assert normalize_heading("  Extra  Spaces  ") == "Extra Spaces"

        # Multiple periods
        assert normalize_heading("Heading...") == "Heading."
        assert normalize_heading("Heading .") == "Heading."
        assert normalize_heading("Heading. . .") == "Heading."

        # Mixed whitespace
        assert normalize_heading("Heading\t.\n") == "Heading."

    def test_split_into_sentences(self):
        """Test basic sentence splitting."""
        # Empty text
        assert split_into_sentences("") == []

        # Single sentence
        assert split_into_sentences("This is a test.") == ["This is a test"]

        # Multiple sentences
        text = "First sentence. Second sentence!"
        sentences = split_into_sentences(text)
        assert len(sentences) == 2
        assert "First sentence" in sentences[0]
        assert "Second sentence" in sentences[1]

        # Multiple punctuation
        text = "What?! This is amazing! Really?"
        sentences = split_into_sentences(text)
        assert len(sentences) == 3

        # No punctuation
        assert split_into_sentences("Just text") == ["Just text"]

    def test_calculate_passive_voice_percentage_detects_passive(self):
        """Passive voice is reported when present."""
        text = "The ball was thrown by the boy. The boy ate lunch."
        assert calculate_passive_voice_percentage(text) == 50.0

    def test_calculate_passive_voice_percentage_ignores_adjectives(self):
        """Simple "is" + adjective should not be flagged."""
        assert calculate_passive_voice_percentage("The car is red.") == 0.0

    def test_extract_acronyms(self):
        """Test acronym extraction."""
        # Empty text
        assert self.terminology_manager.extract_acronyms("") == []

        # Basic acronyms
        text = "The FAA and NASA are agencies."
        acronyms = self.terminology_manager.extract_acronyms(text)
        assert "FAA" in acronyms
        assert "NASA" in acronyms

        # Single letters (should not be included)
        text = "A and B are letters."
        acronyms = self.terminology_manager.extract_acronyms(text)
        assert len(acronyms) == 0

        # Mixed case (should not be included)
        text = "The FaA and NaSa are agencies."
        acronyms = self.terminology_manager.extract_acronyms(text)
        assert len(acronyms) == 0

        # Multiple occurrences
        text = "FAA FAA FAA"
        assert len(self.terminology_manager.extract_acronyms(text)) == 3

    def test_find_acronym_definition(self):
        """Test acronym definition finding."""
        # Empty text
        assert self.terminology_manager.find_acronym_definition("", "FAA") is None

        # Basic definition
        text = "The FAA (Federal Aviation Administration) is an agency."
        assert (
            self.terminology_manager.find_acronym_definition(text, "FAA")
            == "Federal Aviation Administration"
        )

        # No definition
        text = "The FAA is an agency."
        assert self.terminology_manager.find_acronym_definition(text, "FAA") is None

        # Multiple definitions (should find first)
        text = "The FAA (Federal Aviation Administration) and FAA (Federal Aviation Agency)."
        assert (
            self.terminology_manager.find_acronym_definition(text, "FAA")
            == "Federal Aviation Administration"
        )

        # Non-existent acronym
        assert self.terminology_manager.find_acronym_definition("Some text", "XYZ") is None

    def test_split_sentences_complex_abbreviations(self):
        """Test sentence splitting with complex abbreviation scenarios."""
        # Consecutive abbreviations
        text = "Dr. Mr. Smith went home. Ms. Dr. Jones arrived."
        assert split_sentences(text) == ["Dr. Mr. Smith went home.", "Ms. Dr. Jones arrived."]

        # Abbreviations at sentence boundaries
        text = "He works at the U.S. The FAA is there too."
        assert split_sentences(text) == ["He works at the U.S.", "The FAA is there too."]

        # Mixed case abbreviations
        text = "dr. Smith and DR. Jones met Prof. Wilson."
        assert split_sentences(text) == ["dr. Smith and DR. Jones met Prof. Wilson."]

        # Special punctuation with abbreviations
        text = "Visit the U.S.! Dr. Smith said ok. Really?"
        assert split_sentences(text) == ["Visit the U.S.!", "Dr. Smith said ok.", "Really?"]

    def test_count_words_complex_email(self):
        """Test word counting with complex email scenarios."""
        # Multiple email addresses
        text = "Contact user@example.com or admin@test.com today"
        assert count_words(text) == 4  # 2 emails + 'or' + 'today'

        # Email with hyphenation
        text = "my-email@example.com is well-known"
        assert count_words(text) == 3  # email + 'is' + 'well-known'

        # Complex mixed scenario
        text = "first-user@example.com and second-user@test.com are well-known users"
        assert count_words(text) == 6  # 2 emails + 'and' + 'are' + 'well-known' + 'users'

        # Email with special characters
        text = "user.name+tag@example.com is active"
        assert count_words(text) == 3  # email + 'is' + 'active'

    def test_normalize_reference_complex(self):
        """Test reference normalization with complex scenarios."""
        # International characters
        assert normalize_reference("résumé and café") == "resume and cafe"

        # Multiple consecutive special characters
        assert normalize_reference("test!!!and???reference") == "test and reference"

        # Numbers and mixed content
        assert (
            normalize_reference("Chapter 2.3: Test-Case & Examples")
            == "chapter 2 3 test case examples"
        )

        # URLs and technical content
        assert (
            normalize_reference("https://example.com/path?query=123")
            == "https example com path query 123"
        )

        # Mixed punctuation and spaces
        assert normalize_reference("First  ---  Second,,, Third...") == "first second third"

    def test_count_syllables_edge_cases(self):
        """Test syllable counting with edge cases."""
        # Words with consecutive vowels
        assert count_syllables("queen") == 1
        assert count_syllables("audio") == 3

        # Words with 'y' as vowel and consonant
        assert count_syllables("yellow") == 2
        assert count_syllables("myth") == 1

        # Complex compound words
        assert count_syllables("worldwide") == 2
        assert count_syllables("nevertheless") == 3

        # Technical terms
        assert count_syllables("API") == 3
        assert count_syllables("GUI") == 2

    def test_normalize_heading_edge_cases(self):
        """Test heading normalization with edge cases."""
        # Multiple types of whitespace
        assert normalize_heading("Title\n\t  Subtitle") == "Title Subtitle"

        # Mixed periods and other punctuation
        assert normalize_heading("Section 1.2.3...!") == "Section 1.2.3."

        # Unicode whitespace and special characters
        assert normalize_heading("Title\u2003Subtitle\u2002.") == "Title Subtitle."

        # Numbers and special characters
        assert normalize_heading("Chapter 1-2: Overview.") == "Chapter 1-2: Overview."

    def test_normalize_document_type(self):
        assert normalize_document_type("advisory circular") == "Advisory Circular"
        assert normalize_document_type("POLICY STATEMENT") == "Policy Statement"
        assert normalize_document_type("policy-statement") == "Policy Statement"
        assert normalize_document_type("policy_statement") == "Policy Statement"

    def test_calculate_readability_metrics(self):
        metrics = calculate_readability_metrics(100, 10, 150)
        assert "flesch_reading_ease" in metrics
        assert "flesch_kincaid_grade" in metrics
        assert "gunning_fog_index" in metrics

    def test_get_valid_words(self):
        valid_words = get_valid_words()
        assert isinstance(valid_words, set)
        assert len(valid_words) > 0

    def test_calculate_passive_voice_percentage(self):
        text = "The process was completed by the team. The team completed the process."
        pct = calculate_passive_voice_percentage(text)
        assert pct == 50.0
