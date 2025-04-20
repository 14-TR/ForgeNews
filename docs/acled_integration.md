# ACLED API Integration Guide

This guide describes how to configure Cursor AI to interact with the Armed Conflict Location & Event Data Project (ACLED) API.

## 1. Register and Obtain API Credentials

- **Register**: Visit the [ACLED Access Portal](https://acleddata.com/register/) to create a free account.
- **Generate API Key**: After registration, log in to your account to generate a unique API access key.

## 2. Understand API Structure

- **Base URL**: `https://api.acleddata.com/acled/read`
- **Request Method**: HTTP GET
- **Authentication**: Include your email and API key as query parameters.

**Example Request**:
```
https://api.acleddata.com/acled/read?email=your_email@example.com&key=your_api_key&country=Kenya&event_date=2022-01-01
```

## 3. Construct API Requests

Build requests by appending query parameters:

- `email`: Your registered email address.
- `key`: Your API access key.
- `country`: Country name (e.g., `Kenya`).
- `event_date`: Specific date (`2022-01-01`) or range (`2022-01-01:2022-01-31`).
- `event_type`: Type of event (e.g., `Protests`).
- `limit`: Number of records to retrieve.
- `offset`: For pagination.

**Example**:
```
https://api.acleddata.com/acled/read?email=your_email&key=your_key&country=Kenya&event_date=2022-01-01:2022-01-31&event_type=Protests&limit=100
```

## 4. Handle Pagination

Use `limit` and `offset` to paginate:
```
https://api.acleddata.com/acled/read?email=...&key=...&country=Kenya&limit=100&offset=100
```

## 5. Integrate with Cursor AI

1. **Load Credentials**: Use a `.env` file or env vars for `ACLED_API_KEY` and `ACLED_EMAIL`. Cursor AI auto-loads `.env`.
2. **Fetch Function**: `get_conflict_feed` in `src/agents/conflict_agent.py` constructs and sends the HTTP request.
3. **Date Overrides**: Use env vars (`ACLED_START_DATE`, `ACLED_END_DATE`) or CLI flags to specify dates.
4. **Region Overrides**: Use `ACLED_REGION` env var or CLI flags.
5. **Data Persistence**: Raw JSON is saved to `data/raw/conflict_<date>.json`.

## 6. Best Practices

- **Secure Credentials**: Never hardcode public keys.
- **Rate Limits**: Respect any ACLED API limits.
- **Error Handling**: Handle non-200 responses and timeouts.
- **Input Validation**: Sanitize all filters.

## 7. Resources

- **ACLED API User Guide**: https://developer.acleddata.com/rehd/.../API-User-Guide.pdf  
- **ACLED Access Guide**: https://acleddata.com/knowledge-base/acled-access-guide/  
- **ACLED Terms**: https://developer.acleddata.com/rehd/.../ACLED_Terms-of-Use.pdf  