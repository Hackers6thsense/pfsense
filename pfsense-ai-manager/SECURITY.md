# Security & API Key Management

## Environment Variables

Store all sensitive data in `.env` file, never in code:

```env
# pfSense
PFSENSE_HOST=192.168.1.1
PFSENSE_USERNAME=admin
PFSENSE_PASSWORD=***
PFSENSE_API_KEY=***

# AI Providers
MISTRAL_API_KEY=***
GROQ_API_KEY=***
GEMINI_API_KEY=***
```

## API Key Security Best Practices

1. **Never commit `.env` to git**
   - Add to `.gitignore`
   - Use `.env.example` as template

2. **Rotate API keys regularly**
   - Update monthly
   - Immediately if compromised

3. **Use strong passwords**
   - pfSense admin password
   - Database credentials

4. **HTTPS only in production**
   - Enable SSL/TLS
   - Use valid certificates

5. **Rate limiting**
   - Implement in production
   - Prevent API abuse

6. **Access control**
   - Use IP whitelisting
   - Implement authentication
   - Log all API access

## Credential Rotation

To rotate credentials:

1. **Generate new API keys** from each provider's dashboard
2. **Update `.env`** with new keys
3. **Restart application** to apply changes
4. **Revoke old keys** from provider dashboards
5. **Monitor logs** for any auth errors

## Incident Response

If credentials are compromised:

1. **Immediately revoke** old API keys
2. **Generate new keys** from all providers
3. **Update `.env`** with new credentials
4. **Restart application**
5. **Review logs** for unauthorized access
6. **Update firewall rules** if needed

## Production Security Checklist

- [ ] Use HTTPS/TLS only
- [ ] Strong firewall admin password
- [ ] API keys in secure `.env` file
- [ ] File permissions: 644 files, 755 directories
- [ ] Regular backups of configuration
- [ ] Intrusion detection enabled
- [ ] Logs monitored for errors
- [ ] Rate limiting configured
- [ ] IP whitelisting enabled
- [ ] Regular security audits
