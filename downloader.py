"""Media downloader for various platforms."""
import os
import re
import json
import time
import shutil
import logging
import urllib.request
from urllib.request import urlopen
from html import unescape
from typing import Tuple
from functools import wraps

import requests
from bs4 import BeautifulSoup
from redvid import Downloader as RDownloader
from redgifs import API as RedgifsAPI

from config import Config


logger = logging.getLogger(__name__)


def retry_on_error(max_retries=3, delay=1, backoff=2):
    """Retry decorator with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_str = str(e).lower()
                    
                    # Don't retry on permanent errors
                    if any(code in error_str for code in ['404', '403', '401']):
                        logger.warning(f"Permanent error, not retrying: {e}")
                        raise
                    
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {current_delay}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} attempts failed")
            
            raise last_exception
        return wrapper
    return decorator


def get_request(url):
    """Create a request with appropriate headers."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'
    }
    return urllib.request.Request(url, data=None, headers=headers)


def url_read(url):
    """Read URL content."""
    return urlopen(get_request(url)).read()


@retry_on_error(max_retries=3, delay=1, backoff=2)
def url_download(url, filepath):
    """Download URL to filepath."""
    if os.path.isfile(filepath):
        logger.info(f"File exists, skipping: {filepath}")
        return

    with urllib.request.urlopen(get_request(url)) as response, open(filepath, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)


def get_filename(url):
    """Extract filename from URL."""
    return url.split('/')[-1].split('#')[0].split('?')[0]


def get_album_filename(album_id, index, url):
    """Generate filename for album item."""
    return f"{album_id}-{index:04d}-{get_filename(url)}"


def get_imgur_album_links(album_id):
    """Get image links from Imgur album."""
    if not Config.IMGUR_CLIENT_ID:
        raise ValueError("IMGUR_CLIENT_ID not configured")

    info_url = f'https://api.imgur.com/3/album/{album_id}/images'
    headers = {'Authorization': f'Client-ID {Config.IMGUR_CLIENT_ID}'}
    resp = requests.get(url=info_url, headers=headers)
    data = resp.json()

    return [image['link'] for image in data['data']]


def get_gfycat_url(link_url):
    """Get MP4 URL from Gfycat link."""
    gfy_id = link_url.split('/')[-1]
    info_url = f'https://api.gfycat.com/v1/gfycats/{gfy_id}'
    resp = requests.get(url=info_url)
    data = resp.json()
    return str(data['gfyItem']['mp4Url'])


def get_gdn_url(link_url):
    """Get video URL from GifDeliveryNetwork."""
    soup = BeautifulSoup(url_read(link_url), "html.parser")
    return soup.find(id="mp4Source").get("src")


class MediaDownloader:
    """Download media from various platforms."""

    def __init__(self, download_folder, dry_run=False, config=None):
        """Initialize downloader.

        Args:
            download_folder: Base folder for downloads
            dry_run: If True, don't actually download files
            config: Config object for settings
        """
        self.base = download_folder
        self.dry_run = dry_run
        self.config = config
        self.redvid_downloader = RDownloader(max_q=True, path=self.base, log=False)

        # Create directories
        if not os.path.exists(self.base):
            logger.info(f"Creating directory: {self.base}")
            os.makedirs(self.base)

        logger.info("MediaDownloader initialized")

    def get_filepath(self, url, filename=None, extension=None, prefix=None):
        """Get filepath for download.

        Args:
            url: Source URL
            filename: Override filename
            extension: Override extension
            prefix: Prefix to add to filename

        Returns:
            Full filepath for download
        """
        filename = filename if filename else get_filename(url)

        if prefix:
            filename = f"{prefix}-{filename}"

        if extension:
            filename = os.path.splitext(filename)[0] + extension
            logger.info(f"Downloading as: {filename}")

        return os.path.join(self.base, filename)

    def _download_file(self, url, filename=None, extension=None, prefix=None):
        """Actually download a file."""
        filepath = self.get_filepath(url, filename=filename, extension=extension, prefix=prefix)
        if not self.dry_run:
            url_download(url, filepath)

    def _process_imgur_album(self, album_url):
        """Process Imgur album - saves with prefixed filenames like Reddit galleries."""
        album_id = get_filename(album_url)
        links = get_imgur_album_links(album_id)

        for i, image_url in enumerate(links):
            # Use album ID as prefix, similar to Reddit galleries
            prefix = f"{album_id}-{i:02}"
            self._download_file(image_url, prefix=prefix)
            time.sleep(Config.ALBUM_SLEEP)

        logger.info(f"Downloaded imgur album of size {len(links)}")

    def download_redgif_url(self, redgifs_url):
        """Download RedGifs video using redgifs package."""
        logger.info(f"RedGifs URL: {redgifs_url}")
        
        # Extract the gif ID from URL
        # URLs can be like: https://redgifs.com/watch/gifname or https://www.redgifs.com/watch/gifname
        redgifs_id = redgifs_url.split("/")[-1].split('#')[0].split('?')[0]
        logger.info(f"RedGifs ID: {redgifs_id}")

        try:
            # Use the redgifs package API
            api = RedgifsAPI()
            api.login()  # This handles authentication automatically
            
            # Get the gif info
            gif = api.get_gif(redgifs_id)
            
            # Get the HD video URL
            hd_video_url = gif.urls.hd
            logger.info(f"HD video URL: {hd_video_url}")

            filepath = self.get_filepath(hd_video_url, filename=f"{redgifs_id}.mp4")
            logger.info(f"Saving as {filepath}")

            if not self.dry_run:
                # Download the video
                with requests.get(hd_video_url, stream=True) as r:
                    r.raise_for_status()
                    with open(filepath, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
            
            api.close()
            
        except Exception as e:
            logger.error(f"Error downloading RedGifs video: {e}")
            raise

    def download_video_url(self, url):
        """Download Reddit video."""
        logger.info(f"Downloading video: {url}")

        if ".mp4" in url:
            url = "/".join(url.split('/')[:-1])

        logger.info(f"Setting URL to: {url}")
        self.redvid_downloader.url = url

        if not self.dry_run:
            self.redvid_downloader.download()
            
            # Clean up redvid temp folder
            temp_dir = os.path.join(self.base, "temp")
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temp directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp directory: {e}")

        return True, None

    def download_gallery(self, submission) -> Tuple[bool, str]:
        """Download Reddit gallery post.

        Args:
            submission: PRAW submission object with gallery

        Returns:
            Tuple of (success: bool, error: str or None)
        """
        if not hasattr(submission, 'media_metadata') or not submission.media_metadata:
            return False, "Gallery metadata missing"

        all_downloaded = True
        errors = []

        for i, media in enumerate(submission.media_metadata.values()):
            media_source = media.get('s', {})
            if 'u' not in media_source:
                continue

            # Unescape HTML entities like &amp; to &
            link_url = unescape(media_source['u'])
            logger.info(f"       Gallery image {i+1}: {link_url}")

            prefix = f"{submission.id}-{i:02}"
            downloaded, error = self.download_url(link_url, prefix=prefix)

            all_downloaded = all_downloaded and downloaded
            if error:
                errors.append(str(error))

        error_msg = " | ".join(errors) if errors else None
        return all_downloaded, error_msg

    def get_video_url(self, submission):
        """Extract video URL from Reddit submission.

        Args:
            submission: PRAW submission object

        Returns:
            Video URL string or None
        """
        if not submission.is_video:
            return None

        if (not hasattr(submission, "media") or
            submission.media is None or
            'reddit_video' not in submission.media or
            'fallback_url' not in submission.media['reddit_video']):
            return None

        import re
        match = re.search(
            r"https?://v.redd.it/\w+/\w+.mp4",
            submission.media['reddit_video']['fallback_url']
        )

        return match.group(0) if match else None

    def process_submission(self, submission):
        """Process a Reddit submission and download media.

        Args:
            submission: PRAW submission object

        Returns:
            Tuple of (downloaded: bool, error: str or None)
        """
        # Check if it's a gallery
        if hasattr(submission, "is_gallery") and submission.is_gallery and hasattr(submission, "media_metadata"):
            logger.info("       - Gallery")
            return self.download_gallery(submission)

        # Check if it's a video
        video_url = self.get_video_url(submission)
        if video_url:
            logger.info("       - Video")
            return self.download_video_url(video_url)

        # Try to download as regular URL
        try:
            link_url = submission.url
            return self.download_url(link_url)
        except AttributeError:
            return False, "No URL attribute"

    def download_url(self, link_url, prefix=None):
        """Download media from URL.

        Args:
            link_url: URL to download
            prefix: Optional prefix for filename

        Returns:
            Tuple of (success: bool, error: Exception or None)
        """
        result, error = False, None

        try:
            # Handle Reddit gallery URLs
            if "reddit.com/gallery/" in link_url:
                logger.info(f"Reddit gallery URL detected but no metadata available: {link_url}")
                return False, None

            if "i.imgur.com" in link_url:
                if ".png" in link_url:
                    self._download_file(link_url, extension=".jpg")
                elif ".gifv" in link_url:
                    self._download_file(link_url.replace(".gifv", ".mp4"))
                else:
                    self._download_file(link_url)
                result = True

            elif "imgur.com" in link_url and ("/a/" in link_url or "/gallery/" in link_url):
                self._process_imgur_album(link_url)
                result = True

            elif "imgur.com" in link_url and "." not in get_filename(link_url):
                self._download_file(link_url.replace("imgur.com", "i.imgur.com") + ".jpg")
                result = True

            elif "gfycat" in link_url:
                if link_url.endswith(".mp4"):
                    self._download_file(link_url)
                else:
                    try:
                        mp4_url = get_gfycat_url(link_url)
                        logger.info(f"MP4 URL for gfycat {link_url}: {mp4_url}")
                        self._download_file(mp4_url)
                    except Exception:
                        gdn_url = link_url.replace("gfycat.com", "www.gifdeliverynetwork.com")
                        mp4_url = get_gdn_url(gdn_url)
                        logger.info(f"MP4 URL for GDN gfycat {link_url}: {mp4_url}")
                        self._download_file(mp4_url)
                result = True

            elif "redgifs" in link_url:
                # Check if it's a direct media file (i.redgifs.com/i/...)
                if "/i/" in link_url and any(ext in link_url for ext in [".jpg", ".jpeg", ".png", ".gif", ".mp4", ".webm"]):
                    logger.info(f"Direct RedGifs media file: {link_url}")
                    self._download_file(link_url, prefix=prefix)
                    result = True
                else:
                    # It's a RedGifs page URL that needs API access
                    clean_url = link_url.split('#')[0]
                    logger.info(f"Attempting RedGifs API download: {clean_url}")
                    
                    # Use the redgifs package (no token needed, handles auth automatically)
                    if not self.dry_run:
                        self.download_redgif_url(clean_url)
                    result = True

            elif "i.reddituploads.com" in link_url:
                self._download_file(link_url, extension=".jpg")
                result = True

            elif "preview.redd.it" in link_url or "i.redd.it" in link_url:
                if ".png" in link_url:
                    self._download_file(link_url, extension=".jpg", prefix=prefix)
                else:
                    self._download_file(link_url, prefix=prefix)
                result = True

            elif link_url[-4:] in [".jpg", ".png", ".gif", ".mp4"]:
                self._download_file(link_url)
                result = True

            elif "v.redd.it" in link_url:
                return self.download_video_url(link_url)

            else:
                logger.info(f"Unhandled URL: {link_url}")

        except Exception as e:
            logger.error(f"Error downloading {link_url}: {e}")
            error = e

        return result, error
