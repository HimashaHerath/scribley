"""
Command-line interface implementation for Scribley.
"""

import click
import logging
import sys
import os
import json
from datetime import datetime
from pathlib import Path

from ..api import publish_article, get_user_details
from ..config import get_config, initialize_config
from ..utils.scheduler import schedule_post

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option()
def main():
    """Scribley - Medium article publishing automation tool."""
    pass


@main.command()
def init():
    """Initialize Scribley configuration."""
    try:
        config = initialize_config()
        click.echo(f"Initialized Scribley configuration.")
        
        # Check if API token is set
        if not config["medium"]["api_token"]:
            click.echo("\nWARNING: Medium API token is not set.")
            click.echo("You can set it by:")
            click.echo("1. Setting MEDIUM_API_TOKEN environment variable, or")
            click.echo("2. Creating a .env file with MEDIUM_API_TOKEN=your_token, or")
            click.echo("3. Running 'scribley setup' to configure interactively")
    except Exception as e:
        logger.error(f"Failed to initialize configuration: {e}")
        sys.exit(1)


@main.command()
def setup_token():
    """Interactive setup for Medium API token."""
    try:
        from ..utils.token_setup import setup_medium_token
        result = setup_medium_token()
        if result:
            click.echo(f"Medium API token set up successfully!")
        else:
            click.echo(f"Medium API token setup was cancelled.")
    except Exception as e:
        logger.error(f"Failed to set up token: {e}")
        sys.exit(1)


@main.command()
@click.option('--token', prompt='Medium API token', help='Your Medium API integration token')
@click.option('--publication-id', help='Medium publication ID (optional)')
def setup(token, publication_id):
    """Set up Scribley with your Medium credentials."""
    try:
        # Initialize configuration first
        config = initialize_config()
        
        # Update configuration
        config["medium"]["api_token"] = token
        if publication_id:
            config["medium"]["publication_id"] = publication_id
        
        # Update the config file
        from ..config.config import update_config, update_user_info
        update_config(config)
        
        # Test the API token
        user = get_user_details()
        
        # Save user information
        update_user_info(user)
        
        click.echo(f"\nSetup successful! Connected as: {user.get('name', user.get('username'))}")
        
        # Create necessary directories
        articles_dir = Path(config["paths"]["articles_dir"])
        templates_dir = Path(config["paths"]["templates_dir"])
        
        if not articles_dir.exists():
            articles_dir.mkdir(parents=True)
            click.echo(f"Created articles directory: {articles_dir}")
        
        if not templates_dir.exists():
            templates_dir.mkdir(parents=True)
            click.echo(f"Created templates directory: {templates_dir}")
            
            # Create a sample template
            sample_template = templates_dir / "article-template.md"
            with open(sample_template, 'w') as f:
                f.write("# Article Title\n\n")
                f.write("_By [Your Name](https://medium.com/@yourusername)_\n\n")
                f.write("## Introduction\n\n")
                f.write("Your introduction goes here...\n\n")
                f.write("## Section 1\n\n")
                f.write("Your first section content...\n\n")
                f.write("## Section 2\n\n")
                f.write("Your second section content...\n\n")
                f.write("## Conclusion\n\n")
                f.write("Your conclusion goes here...\n\n")
            
            click.echo(f"Created sample template: {sample_template}")
    
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)


@main.command()
@click.option('--file', required=True, help='Path to the markdown file')
@click.option('--title', help='Title of the article (default: extracted from the file)')
@click.option('--tags', help='Comma-separated list of tags')
@click.option('--status', type=click.Choice(['draft', 'public', 'unlisted']), 
              help='Publication status (default: from config)')
@click.option('--publication-id', help='Medium publication ID (default: from config)')
@click.option('--notify/--no-notify', default=None, 
              help='Whether to notify followers (default: from config)')
def post(file, title, tags, status, publication_id, notify):
    """Post an article to Medium."""
    try:
        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
        
        # Publish the article
        result = publish_article(
            file_path=file,
            title=title,
            tags=tag_list,
            status=status,
            publication_id=publication_id,
            notify_followers=notify
        )
        
        click.echo(f"\nArticle published successfully!")
        click.echo(f"Title: {result.get('title')}")
        click.echo(f"URL: {result.get('url')}")
        click.echo(f"Status: {result.get('publishStatus')}")
        
    except Exception as e:
        logger.error(f"Failed to publish article: {e}")
        sys.exit(1)


@main.command()
@click.option('--file', required=True, help='Path to the markdown file')
@click.option('--title', help='Title of the article (default: extracted from the file)')
@click.option('--tags', help='Comma-separated list of tags')
@click.option('--status', type=click.Choice(['draft', 'public', 'unlisted']), 
              help='Publication status (default: from config)')
@click.option('--publication-id', help='Medium publication ID (default: from config)')
@click.option('--notify/--no-notify', default=None, 
              help='Whether to notify followers (default: from config)')
@click.option('--publish-at', required=True, 
              help='Publication date and time (YYYY-MM-DD HH:MM)')
def schedule(file, title, tags, status, publication_id, notify, publish_at):
    """Schedule an article to be posted to Medium."""
    try:
        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
        
        # Parse publish_at datetime
        try:
            publish_datetime = datetime.strptime(publish_at, '%Y-%m-%d %H:%M')
        except ValueError:
            click.echo("Error: Invalid date format. Use YYYY-MM-DD HH:MM")
            sys.exit(1)
        
        # Schedule the post
        schedule_post(
            file_path=file,
            publish_at=publish_datetime,
            title=title,
            tags=tag_list,
            status=status,
            publication_id=publication_id,
            notify_followers=notify
        )
        
        click.echo(f"\nArticle scheduled for publication at {publish_at}")
        click.echo(f"File: {file}")
        if title:
            click.echo(f"Title: {title}")
        
    except Exception as e:
        logger.error(f"Failed to schedule article: {e}")
        sys.exit(1)


@main.command()
def whoami():
    """Display current user information."""
    try:
        user = get_user_details()
        click.echo(f"\nConnected to Medium as:")
        click.echo(f"Name: {user.get('name')}")
        click.echo(f"Username: {user.get('username')}")
        click.echo(f"URL: {user.get('url')}")
        
    except Exception as e:
        logger.error(f"Failed to get user details: {e}")
        sys.exit(1)


@main.command()
def publications():
    """List all publications the user contributes to."""
    try:
        from ..api.medium import MediumClient
        
        # Get publications
        client = MediumClient()
        publications_list = client.get_publications()
        
        if not publications_list:
            click.echo("\nYou don't contribute to any publications.")
            return
        
        click.echo("\nYour publications:")
        for i, pub in enumerate(publications_list, 1):
            click.echo(f"{i}. {pub.get('name')} (ID: {pub.get('id')})")
            click.echo(f"   URL: {pub.get('url')}")
            
        click.echo("\nTo post to a publication, use the --publication-id option:")
        click.echo("scribley post --file article.md --publication-id <publication_id>")
        
    except Exception as e:
        logger.error(f"Failed to get publications: {e}")
        sys.exit(1)


@main.command()
@click.argument('template_name', required=False)
def new(template_name=None):
    """Create a new article from a template."""
    config = get_config()
    templates_dir = Path(config["paths"]["templates_dir"])
    articles_dir = Path(config["paths"]["articles_dir"])
    
    # Create directories if they don't exist
    if not templates_dir.exists():
        templates_dir.mkdir(parents=True)
    
    if not articles_dir.exists():
        articles_dir.mkdir(parents=True)
    
    # List templates if no template name provided
    if not template_name:
        templates = list(templates_dir.glob("*.md"))
        if not templates:
            click.echo("No templates found.")
            click.echo(f"Create a template in {templates_dir} directory.")
            return
        
        click.echo("Available templates:")
        for i, template in enumerate(templates, 1):
            click.echo(f"{i}. {template.name}")
        
        # Prompt for template selection
        choice = click.prompt("Select a template (number)", type=int, default=1)
        try:
            template_path = templates[choice - 1]
        except IndexError:
            click.echo("Invalid selection.")
            return
    else:
        # Find the template
        template_path = templates_dir / f"{template_name}.md"
        if not template_path.exists() and not template_name.endswith('.md'):
            template_path = templates_dir / f"{template_name}.md"
        
        if not template_path.exists():
            click.echo(f"Template '{template_name}' not found.")
            return
    
    # Get article title
    title = click.prompt("Article title")
    
    # Create filename from title
    filename = title.lower().replace(' ', '-').replace('/', '-')
    article_path = articles_dir / f"{filename}.md"
    
    # Check if file already exists
    if article_path.exists():
        if not click.confirm(f"File {article_path} already exists. Overwrite?"):
            return
    
    # Copy template to article
    with open(template_path, 'r') as src:
        template_content = src.read()
    
    # Replace template title with actual title
    article_content = template_content.replace("# Article Title", f"# {title}")
    
    # Write the new article
    with open(article_path, 'w') as dest:
        dest.write(article_content)
    
    click.echo(f"Created new article: {article_path}")


@main.command()
@click.option('--set-default', is_flag=True, help='Set the selected publication as default')
def select_publication(set_default):
    """Interactively select a publication to post to."""
    try:
        from ..api.medium import MediumClient
        from ..config.config import update_config
        
        # Get publications
        client = MediumClient()
        publications_list = client.get_publications()
        
        if not publications_list:
            click.echo("\nYou don't contribute to any publications.")
            return
        
        click.echo("\nSelect a publication:")
        for i, pub in enumerate(publications_list, 1):
            click.echo(f"{i}. {pub.get('name')} ({pub.get('url')})")
        
        # Prompt for publication selection
        choice = click.prompt("Select a publication (number)", type=int, default=1)
        try:
            selected_pub = publications_list[choice - 1]
        except IndexError:
            click.echo("Invalid selection.")
            return
        
        pub_id = selected_pub.get('id')
        pub_name = selected_pub.get('name')
        
        if set_default:
            # Set as default in config
            config = get_config()
            config["medium"]["publication_id"] = pub_id
            update_config(config)
            click.echo(f"\nSet '{pub_name}' as your default publication.")
        
        click.echo(f"\nSelected publication: {pub_name}")
        click.echo(f"Publication ID: {pub_id}")
        click.echo(f"To use this publication, add --publication-id {pub_id} to your post command.")
        
    except Exception as e:
        logger.error(f"Failed to select publication: {e}")
        sys.exit(1)


@main.command()
@click.option('--edit', is_flag=True, help='Edit the configuration file')
@click.option('--get', help='Get a specific configuration value (dot notation, e.g., medium.default_status)')
@click.option('--set', help='Set a specific configuration value (use together with --value)')
@click.option('--value', help='Value to set (use together with --set)')
def config(edit, get, set, value):
    """View or edit configuration."""
    try:
        from ..config.config import get_config, update_config, get_config_file_path
        
        config_data = get_config()
        
        # Edit configuration in editor
        if edit:
            config_path = get_config_file_path()
            click.echo(f"Opening configuration file: {config_path}")
            click.launch(str(config_path))
            return
        
        # Get specific value
        if get:
            keys = get.split('.')
            current = config_data
            for key in keys:
                if key in current:
                    current = current[key]
                else:
                    click.echo(f"Configuration key '{get}' not found.")
                    return
            
            # Format output nicely
            if isinstance(current, (dict, list)):
                click.echo(json.dumps(current, indent=2))
            else:
                click.echo(current)
            return
        
        # Set specific value
        if set and value:
            keys = set.split('.')
            current = config_data
            
            # Navigate to the right level
            for i, key in enumerate(keys[:-1]):
                if key not in current:
                    click.echo(f"Configuration key '{'.'.join(keys[:i+1])}' not found.")
                    return
                current = current[key]
            
            # Convert value to the right type
            if value.lower() == 'true':
                typed_value = True
            elif value.lower() == 'false':
                typed_value = False
            elif value.isdigit():
                typed_value = int(value)
            elif value.replace('.', '', 1).isdigit() and value.count('.') == 1:
                typed_value = float(value)
            else:
                # Try to parse as JSON for lists and dicts
                try:
                    typed_value = json.loads(value)
                except json.JSONDecodeError:
                    typed_value = value
            
            # Set the value
            current[keys[-1]] = typed_value
            update_config(config_data)
            click.echo(f"Set {set} = {typed_value}")
            return
        
        # Show all configuration
        click.echo("\nCurrent configuration:")
        click.echo(json.dumps(config_data, indent=2))
        
        click.echo("\nUsage examples:")
        click.echo("  View configuration: scribley config")
        click.echo("  Edit configuration: scribley config --edit")
        click.echo("  Get specific value: scribley config --get medium.default_status")
        click.echo("  Set specific value: scribley config --set medium.default_status --value public")
        
    except Exception as e:
        logger.error(f"Failed to access configuration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 