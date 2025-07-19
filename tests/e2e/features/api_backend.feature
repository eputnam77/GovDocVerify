Feature: API Backend

  Scenario: Document FastAPI endpoint
    Given the README documentation
    When I look at the API section
    Then it describes parameters for the /process endpoint
    And it includes a curl example showing how to call it

  Scenario: Start FastAPI service via CLI
    Given the run.py entry point
    When I execute the script from the command line
    Then it launches the FastAPI app with uvicorn
