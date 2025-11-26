# GitHub API Usage

## Rate Limiting
- Unauthenticated: 60 requests/hour
- Authenticated: 5000 requests/hour

## Caching Strategy
- Cache timeout: 30 minutes
- Cache key format: `github_api:{endpoint}:{params}`

## Error Handling
1. Network timeout → Retry with exponential backoff
2. Rate limit exceeded → Wait until reset
3. Repository not found → Return 404