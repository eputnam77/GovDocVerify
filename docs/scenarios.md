# Example Scenarios

These short scenarios show common ways to use the tool.

## Single Document via CLI
1. Prepare your Word document.
2. Run `python cli.py --file mydoc.docx --type "Order"`.
3. Review the HTML report saved next to your document.

## Batch Checking with API
1. Start the FastAPI backend.
2. POST each document to `/process` with its type.
3. Consume the JSON results in your own system.

## Integrating into a CI Pipeline
1. Add a job that calls the CLI for each document in your repo.
2. Fail the build on any high severity issues.
