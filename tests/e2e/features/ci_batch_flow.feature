@e2e
Feature: CI batch processing flow
  Scenario: Process multiple documents in CI
    Given several DOCX files are present
    When the CI job runs govdocverify in batch mode
    Then each document produces a report and failures are reported
