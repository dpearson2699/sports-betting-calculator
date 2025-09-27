# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

The Event Contract Betting Framework maintainer takes security seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

1. **Do NOT** create a public issue
2. Email the maintainers directly (contact information will be provided)
3. Include detailed information about the vulnerability
4. Allow reasonable time for investigation and patching

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested mitigation (if any)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 1 week
- **Resolution**: Varies based on severity and complexity

## Security Considerations

### Input Validation

This framework processes user financial data. Key security measures:

- All numeric inputs are validated and sanitized
- Excel file processing includes format validation
- No arbitrary code execution from user inputs
- File paths are validated to prevent directory traversal

### Data Privacy

- No user data is transmitted over networks
- All processing is local
- No telemetry or analytics collection
- Sample data uses generic team names only

### Financial Safety

- Mathematical calculations are thoroughly tested
- Safety constraints prevent excessive betting amounts
- All financial formulas are academically verified
- Error handling prevents calculation failures

## Known Security Boundaries

### What This Framework Does NOT Do

- Network communication
- Credential storage
- External API access
- User authentication
- Data persistence beyond local files

### Dependencies

We regularly audit dependencies for known vulnerabilities:

- Pandas: Used for data processing
- OpenPyXL: Used for Excel file handling
- Pytest: Used for testing (dev dependency only)

## Best Practices for Contributors

1. **Validate All Inputs**: Never trust user-provided data
2. **Test Edge Cases**: Include boundary value testing
3. **Review Mathematical Logic**: Ensure calculations are correct
4. **Follow Principle of Least Privilege**: Minimal file system access
5. **Document Security Assumptions**: Be explicit about trust boundaries

## Security Updates

Security updates will be:

- Released promptly for high-severity issues
- Documented in release notes
- Tagged with security advisory labels
- Communicated through appropriate channels
