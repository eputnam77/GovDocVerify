Feature: Metadata Extraction & Display
  Scenario: Document all metadata fields
    Given the README documentation
    When I review the metadata section
    Then it lists Title, Author, Last Modified By, Created, and Modified
    And installation instructions mention using a single dependency file or Poetry
