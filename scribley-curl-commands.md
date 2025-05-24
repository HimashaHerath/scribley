# Scribley API Curl Commands

This document contains curl commands for testing the Scribley API endpoints, with a focus on the Ollama/LLM integration.

## Setup

First, set your base URL and auth token:

```bash
export API_BASE_URL="http://localhost:8080/api"
export AUTH_TOKEN="your-auth-token-here"
```

## LLM Features

### Get LLM Providers

```bash
curl -X GET \
  "$API_BASE_URL/llm/providers" \
  -H "Authorization: Bearer $AUTH_TOKEN"
```

### Get Ollama Models

```bash
curl -X GET \
  "$API_BASE_URL/llm/ollama/models" \
  -H "Authorization: Bearer $AUTH_TOKEN"
```

### Summarize Text

```bash
curl -X POST \
  "$API_BASE_URL/llm/summarize" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Artificial intelligence has rapidly transformed industries across the globe. From healthcare to finance, AI is enabling new possibilities and efficiencies. However, with these advancements come significant ethical considerations that must be addressed by policymakers and technologists alike.",
    "max_length": 50,
    "provider": "ollama",
    "model": "llama3"
  }'
```

### Generate Tags

```bash
curl -X POST \
  "$API_BASE_URL/llm/tags" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Artificial intelligence has rapidly transformed industries across the globe. From healthcare to finance, AI is enabling new possibilities and efficiencies. However, with these advancements come significant ethical considerations that must be addressed by policymakers and technologists alike.",
    "max_tags": 5,
    "provider": "ollama",
    "model": "llama3"
  }'
```

### Improve Title

```bash
curl -X POST \
  "$API_BASE_URL/llm/improve-title" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI and Ethics",
    "text": "Artificial intelligence has rapidly transformed industries across the globe. From healthcare to finance, AI is enabling new possibilities and efficiencies. However, with these advancements come significant ethical considerations that must be addressed by policymakers and technologists alike.",
    "provider": "ollama",
    "model": "llama3"
  }'
```

### Check Issues

```bash
curl -X POST \
  "$API_BASE_URL/llm/check-issues" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Artificial intelligence has rapidly transformed industries across the globe. From healthcare to finance, AI is enabling new possibilities and efficiencies. However, with these advancements come significant ethical considerations that must be addressed by policymakers and technologists alike.",
    "provider": "ollama",
    "model": "llama3"
  }'
```

### Generate Social Post

```bash
curl -X POST \
  "$API_BASE_URL/llm/social-post" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Future of AI Ethics",
    "text": "Artificial intelligence has rapidly transformed industries across the globe. From healthcare to finance, AI is enabling new possibilities and efficiencies. However, with these advancements come significant ethical considerations that must be addressed by policymakers and technologists alike.",
    "platform": "twitter",
    "provider": "ollama",
    "model": "llama3"
  }'
```

### Draft Article

```bash
curl -X POST \
  "$API_BASE_URL/llm/draft-article" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "The Future of AI Ethics",
    "outline": ["Introduction to AI ethics", "Current challenges", "Regulatory approaches", "Industry self-regulation", "Future outlook"],
    "length": "medium",
    "style": "informative",
    "provider": "ollama",
    "model": "llama3"
  }'
```

## Articles

### Get All Articles

```bash
curl -X GET \
  "$API_BASE_URL/articles" \
  -H "Authorization: Bearer $AUTH_TOKEN"
```

### Get Article by ID

```bash
export ARTICLE_ID="your-article-id"
curl -X GET \
  "$API_BASE_URL/articles/$ARTICLE_ID" \
  -H "Authorization: Bearer $AUTH_TOKEN"
```

### Create Article

```bash
curl -X POST \
  "$API_BASE_URL/articles" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Article Title",
    "subtitle": "Optional subtitle",
    "content": "The content of the article goes here...",
    "tags": ["tag1", "tag2"],
    "status": "draft",
    "publication_id": null
  }'
```

### Update Article

```bash
export ARTICLE_ID="your-article-id"
curl -X PUT \
  "$API_BASE_URL/articles/$ARTICLE_ID" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Article Title",
    "subtitle": "Updated subtitle",
    "content": "The updated content of the article goes here...",
    "tags": ["updated-tag1", "updated-tag2"],
    "status": "public",
    "publication_id": null
  }'
```

### Delete Article

```bash
export ARTICLE_ID="your-article-id"
curl -X DELETE \
  "$API_BASE_URL/articles/$ARTICLE_ID" \
  -H "Authorization: Bearer $AUTH_TOKEN"
```

## Publications

### Get All Publications

```bash
curl -X GET \
  "$API_BASE_URL/publications" \
  -H "Authorization: Bearer $AUTH_TOKEN"
```

### Get Publication by ID

```bash
export PUBLICATION_ID="your-publication-id"
curl -X GET \
  "$API_BASE_URL/publications/$PUBLICATION_ID" \
  -H "Authorization: Bearer $AUTH_TOKEN"
```

### Get Publication Contributors

```bash
export PUBLICATION_ID="your-publication-id"
curl -X GET \
  "$API_BASE_URL/publications/$PUBLICATION_ID/contributors" \
  -H "Authorization: Bearer $AUTH_TOKEN"
```

## User

### Get Current User

```bash
curl -X GET \
  "$API_BASE_URL/users/me" \
  -H "Authorization: Bearer $AUTH_TOKEN"
```

### Get User Publications

```bash
curl -X GET \
  "$API_BASE_URL/users/me/publications" \
  -H "Authorization: Bearer $AUTH_TOKEN"
```

## Images

### Upload Image

```bash
curl -X POST \
  "$API_BASE_URL/images/upload" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -F "file=@/path/to/local/image.jpg"
``` 