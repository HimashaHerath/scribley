# Sample Article: Getting Started with Medium API

_By [Your Name](https://medium.com/@yourusername)_

## Introduction

This is a sample article created with Scribley, a tool for automating Medium article publishing. In this article, we'll explore how to use the Medium API to programmatically publish content to your Medium account.

## What is the Medium API?

Medium provides a REST API that allows developers to integrate with the Medium platform. With the API, you can:

- Get information about the authenticated user
- Create posts
- Publish to publications
- Manage your content

## Getting Started

To use the Medium API, you'll need to:

1. Create a Medium account if you don't already have one
2. Get an integration token from your Medium settings page
3. Use the token to authenticate your requests

## Example: Creating a Post with Python

Here's a simple example of creating a post using Python and the requests library:

```python
import requests
import json

# Set up the API client
token = "your-integration-token"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Get user ID
response = requests.get("https://api.medium.com/v1/me", headers=headers)
user_data = response.json()
user_id = user_data["data"]["id"]

# Create a post
post_data = {
    "title": "My First API Post",
    "contentFormat": "html",
    "content": "<h1>Hello Medium!</h1><p>This is my first post via the API.</p>",
    "publishStatus": "draft"
}

response = requests.post(
    f"https://api.medium.com/v1/users/{user_id}/posts",
    headers=headers,
    data=json.dumps(post_data)
)

# Print the result
print(json.dumps(response.json(), indent=2))
```

## Conclusion

The Medium API opens up many possibilities for automating your content publishing workflow. With tools like Scribley, you can schedule posts, manage your content, and integrate Medium publishing into your existing systems.

Happy publishing! 