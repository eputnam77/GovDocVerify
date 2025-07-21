Feature: Upload and results page

  Scenario: Uploading a document displays results
    Given I open the upload page
    When I select a valid DOCX file and submit the form
    Then the results page shows the analysis summary

  Scenario: Download results as DOCX or PDF
    Given the results page is visible
    When I click the "Download DOCX" button
    Then my browser downloads a DOCX file
    When I click the "Download PDF" button
    Then my browser downloads a PDF file
