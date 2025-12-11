"""Configuration template for Reddit Downloader.

Copy this file to config.py and fill in your credentials.
"""

class Config:
    """Configuration class for Reddit Downloader."""

    # ============================================================================
    # REQUIRED: Reddit API Credentials
    # ============================================================================
    # Get these from: https://www.reddit.com/prefs/apps
    # 1. Click "Create App" or "Create Another App"
    # 2. Choose "script" type
    # 3. Copy the client ID (under "personal use script") and secret

    REDDIT_USER_AGENT = 'RedditDownloader/1.0'
    REDDIT_APP_ID = 'your_app_id_here'
    REDDIT_APP_SECRET = 'your_app_secret_here'
    REDDIT_USERNAME = 'your_username_here'
    REDDIT_PASSWORD = 'your_password_here'

    # ============================================================================
    # OPTIONAL: Archive Reddit Account
    # ============================================================================
    # Posts that cannot be downloaded (not direct links) will be:
    # - Unsaved from main account
    # - Saved to archive account (if configured)

    ARCHIVE_REDDIT_USERNAME = None
    ARCHIVE_REDDIT_PASSWORD = None

    # ============================================================================
    # OPTIONAL: Imgur API (for album downloads)
    # ============================================================================
    # Get from: https://api.imgur.com/oauth2/addclient

    IMGUR_CLIENT_ID = None

    # ============================================================================
    # OPTIONAL: RedGifs API Token
    # ============================================================================
    # Note: This token expires periodically and needs to be refreshed
    # To get a new token:
    # 1. Open any RedGifs video in your browser
    # 2. Open Developer Tools (F12) -> Network tab
    # 3. Refresh the page
    # 4. Look for API calls to api.redgifs.com
    # 5. Find the Authorization header
    # 6. Copy the token (everything after "Bearer ")

    REDGIF_TOKEN = None

    # ============================================================================
    # Download Settings
    # ============================================================================

    BATCH_LIMIT = 500           # Number of posts to fetch per batch
    ALBUM_SLEEP = 0.05          # Delay between album image downloads (seconds)

    # ============================================================================
    # Skipped Subreddits
    # ============================================================================
    # Add subreddit names (without r/) that you want to skip

    SKIPPED_SUBREDDITS = ['doujinshi']

    # ============================================================================
    # Validation (do not modify)
    # ============================================================================

    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        required = [
            'REDDIT_APP_ID',
            'REDDIT_APP_SECRET',
            'REDDIT_USERNAME',
            'REDDIT_PASSWORD',
        ]

        missing = []
        for key in required:
            value = getattr(cls, key)
            if not value or value.startswith('your_'):
                missing.append(key)

        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}\n"
                "Please edit config.py and add your Reddit API credentials.\n"
                "Get credentials at: https://www.reddit.com/prefs/apps"
            )

        return True
