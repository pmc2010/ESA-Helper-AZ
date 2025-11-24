# Security Considerations for ESA Helper

This document outlines the security posture of ESA Helper and recommendations for safe use.

## ⚠️ Current Security Status

**ESA Helper is designed for personal family use on trusted computers.** It is not suitable for:
- Multi-user environments
- Shared computers
- Production business use
- Systems handling highly sensitive data

## Known Security Issues

### Plaintext Credentials Storage
**Severity: MEDIUM**

Credentials are stored in `config.json` in plaintext:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Current Protection:** File permissions (only readable by owner)

**Recommendation:**
- Only use on personal computers with strong OS-level security
- Change ClassWallet password regularly
- Consider changing password when sharing computer with others
- Don't commit `config.json` to version control (it's in `.gitignore`)

### No Web Interface Authentication
**Severity: MEDIUM**

The web interface has no login system. Anyone with access to `http://localhost:5000` can:
- View student/vendor data
- Submit reimbursement forms
- Modify templates
- Change credentials

**Recommendation:**
- Only access from your computer
- Don't share localhost URL with others
- Use OS firewall to block port 5000 from network access

### Limited Input Validation
**Severity: MEDIUM**

Not all user inputs are validated for:
- Email format
- Phone format
- Numeric ranges (tax rates, amounts)
- File path safety

**Recommendation:**
- Carefully review data before submitting
- Watch for error messages indicating validation failures
- Test with sample data first

### File Path Traversal Potential
**Severity: LOW**

File browser could potentially be manipulated to access unintended directories.

**Recommendation:**
- Only use verified file paths
- Use absolute paths, not relative paths
- Keep document folder separate from sensitive system files

## Safe Usage Guidelines

### Setup
1. ✓ Install on your personal computer only
2. ✓ Use a strong OS password
3. ✓ Enable disk encryption (FileVault on Mac, BitLocker on Windows)
4. ✓ Keep OS and Chrome updated
5. ✓ Create a separate data folder for documents

### Daily Use
1. ✓ Close browser when not in use
2. ✓ Lock computer when away
3. ✓ Run on local network only (not exposed to internet)
4. ✓ Keep credentials secure in `config.json`
5. ✓ Review all data before submission

### Data Protection
1. ✓ Regular backups of `data/` folder
2. ✓ Use cloud backup service for backup copies (Dropbox, Google Drive)
3. ✓ Keep `config.json` secure
4. ✓ Don't share credentials with others
5. ✓ Each person should have their own project folder

## If You Share This Tool with Others

**IMPORTANT:** Each family/person should:

1. **Clone the repository separately**
   ```bash
   git clone https://github.com/pmc2010/ESA-Helper-AZ.git ESA-Helper-AZ-Family-A
   git clone https://github.com/pmc2010/ESA-Helper-AZ.git ESA-Helper-AZ-Family-B
   ```

2. **Create separate data files**
   - Copy sample data to active files
   - Don't share `data/` directories between users

3. **Manage credentials independently**
   - Each person has their own `config.json`
   - Each person uses their own ClassWallet account

4. **Keep projects isolated**
   - Don't run multiple instances on same computer
   - Use different user accounts if sharing computer

## Network Security

### Port 5000 is Only Accessible Locally

The app binds to `127.0.0.1:5000` which means:
- ✓ Only your computer can access it
- ✓ Not accessible from other computers on your network
- ✓ Not accessible from the internet

### Credentials NOT Sent Elsewhere

ClassWallet credentials are ONLY used for:
- Logging into ClassWallet website via Selenium
- Not sent to any other service
- Not uploaded to any cloud service
- Not shared with third parties

## Selenium Browser Automation Safety

The app uses Selenium WebDriver to automate ClassWallet submissions:

**Safe practices:**
- ✓ Browser launches with limited permissions
- ✓ Only navigates to ClassWallet.com
- ✓ Closes automatically after submission
- ✓ No extensions or plugins installed

**Don't:**
- ✗ Don't manually browse other sites in the automated browser
- ✗ Don't install browser extensions
- ✗ Don't modify browser settings during automation

## Checklist Before Production Use

Before sharing with families or using long-term, ensure:

- [ ] You've read this security document
- [ ] You're running on a trusted computer
- [ ] You have backups of all data
- [ ] You've changed default passwords
- [ ] File permissions are correct (owner read/write only)
- [ ] Network firewall blocks port 5000 from external access
- [ ] You test with sample data first
- [ ] You understand the known limitations
- [ ] You keep the app updated with latest code

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do NOT** publish it publicly
2. **Do NOT** commit code that exposes vulnerabilities
3. Email the maintainer privately with details
4. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix if you have one

## Future Security Improvements

The code review identified these improvements (not yet implemented):

**High Priority:**
- [ ] Implement environment variable configuration
- [ ] Add web interface authentication
- [ ] Implement CSRF protection
- [ ] Add comprehensive input validation
- [ ] Encrypt stored credentials

**Medium Priority:**
- [ ] Add security headers
- [ ] Implement audit logging
- [ ] Add rate limiting
- [ ] Sanitize file logs
- [ ] Add data encryption at rest

**Low Priority:**
- [ ] Security testing framework
- [ ] Penetration testing
- [ ] Automated security scanning
- [ ] Regular security audits

## Summary

ESA Helper is designed for personal, family use. While it includes security features:
- It is NOT suitable for high-security scenarios
- It requires users to maintain good security practices
- It should only run on trusted computers
- It should NOT be exposed to the internet or untrusted users

For family use on personal computers with the guidelines above, it provides a reasonable level of security while automating tedious reimbursement submissions.

---

**Last Updated:** November 2025
**Status:** Designed for personal family use

Questions? Check the main [README.md](README.md) or [SETUP.md](SETUP.md).
