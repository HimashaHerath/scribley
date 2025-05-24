# Medium API Rate Limiting Documentation

## Overview

This document describes the implementation of rate limiting for the Medium API in the Scribley application. The Medium API doesn't officially document its rate limits, but like most APIs, it has limits to prevent abuse. Our implementation follows best practices to avoid hitting these limits.

## Rate Limiting Strategy

We've implemented a multi-layer rate limiting approach:

### Server-Side Implementation

The server-side rate limiter (`MediumRateLimiter` in `scribley/api/medium.py`) enforces the following limits:

- **Daily limit**: 300 requests per day
- **Hourly limit**: 50 requests per hour
- **Per-minute limit**: 10 requests per minute
- **Minimum interval**: 1 second between consecutive requests

Key features:
- Singleton pattern ensures consistent rate limiting across multiple instances
- Thread-safe implementation with locks
- Smart retry mechanism that adapts wait time based on which limit was hit
- Decorator pattern for easy application to API methods

### Client-Side Implementation

The client-side rate limiting (in `client/src/lib/api.ts`) implements:

- Endpoint-specific rate limiting for Medium API calls
- Request throttling with minimum intervals between requests
- Warning messages when approaching limits
- Different rate limits for various endpoint types

## Caching Strategy

To further reduce API calls, we've implemented a caching system:

### Server-Side Caching

- GET requests responses are cached with a TTL of 5 minutes
- Cache key includes method name and parameters
- Only caches specific GET methods that retrieve relatively static data

### Client-Side Caching

- Enhanced caching with endpoint-specific TTLs:
  - User data: 1 hour
  - Publication data: 1 hour
  - Article content: 5 minutes
  - Other API calls: 30 seconds
- Automatically refreshes cache when TTL expires

## Configuration

The rate limiting parameters can be configured in the application config:

```yaml
medium:
  rate_limit:
    calls_per_day: 300
    calls_per_hour: 50
    calls_per_minute: 10
    min_request_interval: 1
```

## Logging and Monitoring

The implementation includes extensive logging to help track API usage:

- Warning logs when approaching rate limits
- Information logs for cache hits
- Error logs when rate limits are exceeded

## Best Practices for Developers

When working with the Medium API in Scribley:

1. Prefer batch operations over multiple single operations
2. Use caching for frequently accessed data
3. Don't bypass the rate limiters
4. Monitor logs for rate limit warnings
5. Consider implementing retry mechanisms for important operations

## Future Improvements

Potential enhancements to consider:

1. Dynamic rate limiting based on API response headers
2. Shared rate limiting state for distributed deployments
3. Circuit breaker pattern for graceful degradation
4. Analytics dashboard for API usage monitoring 