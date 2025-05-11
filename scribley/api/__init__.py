"""
Scribley API package
"""

# Try-except block to handle potential import errors
try:
    from .medium import MediumAPIClient, publish_article, get_user_details
except ImportError as e:
    print(f"Warning: Unable to import from medium module: {e}")
    # Define placeholder classes/functions
    MediumAPIClient = None
    publish_article = None
    get_user_details = None 