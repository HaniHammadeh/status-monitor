import os
import sys
import time
from pathlib import Path
from google import genai

MODEL = "gemini-2.5-flash"
OUTPUT_FILE = "security-report.md"
MAX_RETRIES = 5

PROMPT = """
You are a Senior Application Security Engineer.

Perform a comprehensive security review of the supplied source code.

Review for:
- OWASP Top 10
- Authentication & Authorization
- SQL Injection
- XSS
- Command Injection
- SSRF
- CSRF
- Path Traversal
- File Upload Vulnerabilities
- Hardcoded Secrets
- Sensitive Information Disclosure
- Insecure Cryptography
- Business Logic Vulnerabilities
- Input Validation
- Dangerous Shell Commands
- Dependency Risks
- Docker Security
- Kubernetes Security
- GitHub Actions Security

Return the result in Markdown.

For every finding include:
- Severity
- CWE
- Line Number
- Description
- Exploitation Scenario
- Recommendation

At the end provide:

# Summary

Critical:
High:
Medium:
Low:

If no security issues are found, explicitly state that no vulnerabilities were identified.
"""

def review_file(client, filename, code):
    request = f"""
File:
{filename}

{PROMPT}

Source Code:

```text
{code}
```
"""

    for attempt in range(MAX_RETRIES):
        try:
            interaction = client.interactions.create(
                model=MODEL,
                input=request,
                generation_config={
                    "thinking_level": "high",
                    "thinking_summaries": "auto",
                    "temperature": 0.1,
                },
            )
            return interaction.output_text
        except Exception as ex:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = 2 ** attempt
            print(f"Attempt {attempt + 1} failed: {ex}")
            print(f"Retrying in {wait} seconds...")
            time.sleep(wait)

def main():
    if len(sys.argv) != 2:
        print("Usage: python security_review.py <source_file>")
        sys.exit(1)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    code = file_path.read_text(encoding="utf-8", errors="ignore")
    client = genai.Client(api_key=api_key)

    print(f"Reviewing {file_path} ...")
    report = review_file(client, str(file_path), code)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)

    if "Critical" in report:
        sys.exit(2)

if __name__ == "__main__":
    main()