@e2e
Feature: Upload and results page

  Scenario: Uploading a document displays results
    Given I open the upload page
    When I select a valid DOCX file and submit the form
    Then the results page shows the analysis summary
