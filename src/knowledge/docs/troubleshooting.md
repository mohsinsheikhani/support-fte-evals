# Troubleshooting Guide

## API Errors

### 401 Unauthorized

**Symptoms**: API returns 401 status code

**Causes**:
- Invalid or expired API key
- API key doesn't have required permissions
- Key was regenerated but old key is still in use

**Solutions**:
1. Verify your API key in Dashboard > Settings > API Keys
2. Check that the key hasn't expired
3. Ensure the key has the required scopes for your endpoint
4. Generate a new key if the current one may be compromised

### 429 Too Many Requests

**Symptoms**: Rate limit exceeded error

**Causes**:
- Exceeded plan's API call limit
- Too many requests per minute

**Solutions**:
1. Check current usage in Dashboard > Usage
2. Implement exponential backoff in your code
3. Use bulk endpoints instead of individual calls
4. Consider upgrading to a higher plan
5. Cache responses where possible

### 500 Internal Server Error

**Symptoms**: Server error on our end

**Solutions**:
1. Retry the request after a few seconds
2. Check our status page at status.example.com
3. If persistent, contact support with request ID

## Authentication Issues

### Can't Log In

**Solutions**:
1. Clear browser cache and cookies
2. Try incognito/private browsing mode
3. Reset password via "Forgot Password"
4. Check if your account was deactivated
5. Try a different browser

### Two-Factor Authentication Issues

**Solutions**:
1. Use backup codes (provided during 2FA setup)
2. Contact support with identity verification for 2FA reset
3. Check that device time is synchronized

## Webhook Issues

### Webhooks Not Receiving Events

**Causes**:
- Endpoint URL is incorrect or unreachable
- Endpoint not returning 2xx within 10 seconds
- Firewall blocking our IP addresses
- SSL certificate issues

**Solutions**:
1. Verify endpoint URL is correct and publicly accessible
2. Check endpoint responds quickly (under 10 seconds)
3. Whitelist our IP ranges: 203.0.113.0/24
4. Ensure SSL certificate is valid and not self-signed
5. Check webhook logs in Dashboard > Webhooks

### Webhook Payload Issues

**Solutions**:
1. Verify webhook signature using your webhook secret
2. Handle webhook retries (we retry 3 times with backoff)
3. Respond with 200 before processing (use async processing)

## Data Export Issues

### Export Taking Too Long

**Solutions**:
1. Reduce date range or data scope
2. Use API pagination for programmatic exports
3. Schedule exports during off-peak hours
4. Contact support for large dataset assistance

### Export File Corrupted

**Solutions**:
1. Re-download the file
2. Try a different export format (CSV vs JSON)
3. Check your download wasn't interrupted
4. Contact support with export ID

## Performance Issues

### Slow API Responses

**Solutions**:
1. Check our status page for known issues
2. Use closer regional endpoints if available
3. Optimize your queries (use filters, pagination)
4. Consider Premium plan for priority queue access
5. Cache responses client-side

## Still Need Help?

If your issue isn't covered here:
1. Search our documentation at docs.example.com
2. Check community forums at community.example.com
3. Contact support via chat or email
4. Enterprise customers: Contact your account manager
