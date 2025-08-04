@e2e
Feature: End-to-end CLI processing
  Scenario: Process a document via the command line
    Given a sample DOCX file is available
    When I run govdocverify on the file
    Then a structured report is produced without errors
