@e2e
Feature: End-to-end web upload flow
  Scenario: Upload a document through the frontend
    Given the upload form is displayed
    When a DOCX file is selected and submitted
    Then the backend returns validation results
