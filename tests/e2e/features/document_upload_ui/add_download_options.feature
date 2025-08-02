@e2e
Feature: Add download options for results

  Scenario: Download results as DOCX or PDF
    Given the results page is visible
    When I click the DOCX download option
    Then a DOCX file is downloaded
    When I click the PDF download option
    Then a PDF file is downloaded
