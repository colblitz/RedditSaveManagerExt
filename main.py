"""Reddit saved posts downloader - Main driver."""
import argparse
import logging
import time
import os
import shutil
from typing import Iterator, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

import praw
from praw.models import Comment

from config import Config
from downloader import MediaDownloader


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class RedditSaveManager:
    """Manage downloading of Reddit saved posts."""

    def __init__(self, config: Config):
        """Initialize Reddit Save Manager.

        Args:
            config: Configuration object
        """
        self.config = config
        self.reddit = self._init_reddit_client(
            config.REDDIT_USERNAME,
            config.REDDIT_PASSWORD
        )

        # Initialize archive account if configured
        self.archive_reddit = None
        if config.ARCHIVE_REDDIT_USERNAME and config.ARCHIVE_REDDIT_PASSWORD:
            try:
                self.archive_reddit = self._init_reddit_client(
                    config.ARCHIVE_REDDIT_USERNAME,
                    config.ARCHIVE_REDDIT_PASSWORD
                )
                # Test the connection
                self.archive_reddit.user.me()
                logger.info(f"Archive account configured: {config.ARCHIVE_REDDIT_USERNAME}")
            except Exception as e:
                logger.error(f"Failed to initialize archive account: {e}")
                logger.error("Archive functionality will be disabled")
                self.archive_reddit = None

    def _init_reddit_client(self, username: str, password: str):
        """Initialize Reddit client.

        Args:
            username: Reddit username
            password: Reddit password

        Returns:
            PRAW Reddit instance
        """
        return praw.Reddit(
            user_agent=self.config.REDDIT_USER_AGENT,
            client_id=self.config.REDDIT_APP_ID,
            client_secret=self.config.REDDIT_APP_SECRET,
            username=username,
            password=password
        )

    def _archive_link(self, link):
        """Archive a link to the archive account.

        Args:
            link: PRAW link object

        Returns:
            bool: True if successfully archived and unsaved, False otherwise
        """
        if not self.archive_reddit:
            logger.info("       - No archive account configured, NOT unsaving")
            return False

        # Generate the comment/submission link for logging
        if isinstance(link, Comment):
            link_url = f"https://reddit.com{link.permalink}"
        else:
            link_url = f"https://reddit.com/comments/{link.id}"

        logger.info(f"       - Archiving to archive account: {link.id} ({link_url})")
        try:
            if isinstance(link, Comment):
                # For comments, we need to get the comment object
                archive_comment = self.archive_reddit.comment(id=link.id)
                archive_comment.save()
            else:
                archive_submission = self.archive_reddit.submission(id=link.id)
                archive_submission.save()
            
            # Successful archive - unsave automatically
            link.unsave()
            logger.info("       - Successfully archived and unsaved")
            return True
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a 400 error indicating deleted/removed content
            if "400" in error_str or "404" in error_str:
                logger.warning(f"       - Content appears deleted/removed (400/404 error)")
                logger.info(f"       - Unsaving deleted content: {link.id}")
                link.unsave()
                return True  # Treat as success since we unsaved it
            
            logger.error(f"       - Failed to archive: {e}")
            logger.error(f"       - NOT unsaving, keeping item saved for review")
            return False

    def get_saved_submissions(self) -> Iterator:
        """Get saved submissions from Reddit.

        Yields:
            PRAW submission objects or Comment objects (to be archived)
        """
        saved = self.reddit.user.me().saved(limit=self.config.BATCH_LIMIT)
        for link in saved:
            # Skip removed comments - unsave automatically
            if isinstance(link, Comment) and link.author is None:
                logger.info(f"{link.id} - Removed comment, unsaving automatically")
                link.unsave()
                continue

            yield link

    def _get_last_processed(self, username: str) -> int:
        """Get the last processed timestamp for a user.

        Args:
            username: Reddit username

        Returns:
            Unix timestamp of last processed submission
        """
        latest = 0
        if os.path.exists("users-saved.txt"):
            with open("users-saved.txt", 'r') as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) >= 2 and username == parts[0]:
                        latest = max(latest, int(parts[1]))
        return latest

    def _update_last_processed(self, username: str, timestamp: int):
        """Update the last processed timestamp for a user.

        Args:
            username: Reddit username
            timestamp: Unix timestamp to save
        """
        with open("users-saved.txt", 'a') as f:
            f.write(f"{username},{timestamp}\n")

    def get_user_submissions(self, username: str, last_processed: int = 0) -> Iterator:
        """Get submissions from a specific user.

        Args:
            username: Reddit username
            last_processed: Only yield submissions newer than this timestamp

        Yields:
            PRAW submission objects
        """
        redditor = self.reddit.redditor(username)
        logger.info(f"Fetching submissions for user: {username}")
        if last_processed > 0:
            logger.info(f"Starting from timestamp: {last_processed}")
        logger.info("Note: Reddit API is limited to approximately 1000 most recent submissions")

        for submission in redditor.submissions.new(limit=None):
            # Stop if we've reached previously processed submissions
            if int(submission.created_utc) <= last_processed:
                logger.info(f"Reached previously processed submissions at {int(submission.created_utc)}")
                break
            yield submission

    def process_submissions(self, submissions: Iterator, downloader: MediaDownloader,
                          unsave_on_success: bool = False, archive_on_skip: bool = False):
        """Process submissions and download media.

        Args:
            submissions: Iterator of PRAW submission objects or Comment objects
            downloader: MediaDownloader instance
            unsave_on_success: Whether to unsave successfully downloaded posts
            archive_on_skip: Whether to archive posts that can't be downloaded

        Returns:
            Tuple of (num_success, skipped_set, errored_set)
        """
        num_success = 0
        skipped = set()
        errored = set()

        for submission in submissions:
            link_id = submission.id

            # Handle comments - archive them (only unsave if archived successfully)
            if isinstance(submission, Comment):
                logger.info(f"{link_id} - comment")
                if archive_on_skip:
                    archived = self._archive_link(submission)
                    if archived:
                        skipped.add(f"{link_id} - Comment (archived)")
                    else:
                        skipped.add(f"{link_id} - Comment (kept saved)")
                else:
                    skipped.add(f"{link_id} - Comment (skipped)")
                continue

            try:
                link_url = submission.url
            except AttributeError:
                logger.info(f"{link_id} - not a link")
                if archive_on_skip:
                    archived = self._archive_link(submission)
                    if archived:
                        skipped.add(f"{link_id} - Not a link (archived)")
                    else:
                        skipped.add(f"{link_id} - Not a link (kept saved)")
                else:
                    skipped.add(f"{link_id} - Not a link (skipped)")
                continue

            # Skip certain subreddits
            if submission.subreddit.display_name in self.config.SKIPPED_SUBREDDITS:
                logger.info(f"{link_id} - skipping {submission.subreddit.display_name}")
                skipped.add(f"{link_id} - Skipping {submission.subreddit.display_name}")
                if archive_on_skip:
                    self._archive_link(submission)
                continue

            # Skip Reddit posts (not direct media) - but can archive them
            if "www.reddit.com/r/" in link_url or "reddit.com/r/" in link_url:
                logger.info(f"{link_id} - Skipping Reddit post")
                skipped.add(f"{link_id} {link_url} - Reddit post")
                if archive_on_skip:
                    self._archive_link(submission)
                continue

            logger.info("")
            logger.info(f"{link_id} - {link_url}")

            # Process the submission
            downloaded, error = downloader.process_submission(submission)

            # Handle results
            if downloaded:
                logger.info("       - Success")
                if unsave_on_success:
                    logger.info(f"       - Unsaving: {link_id}")
                    submission.unsave()
                num_success += 1
            elif error:
                logger.error(f"       - Error: {error}")
                logger.error(f"       - Keeping item saved for review")
                errored.add(f"{link_id} {link_url}: {error} (kept saved)")
            else:
                logger.info("       - Can't handle")
                logger.info("       - Keeping item saved for review")
                skipped.add(f"{link_id} {link_url} - Can't handle (kept saved)")

            # Be nice to Reddit's servers
            time.sleep(0.5)

        return num_success, skipped, errored

    def run_saved_posts(self, dry_run: bool = False, parallel_downloads: int = 1):
        """Download from saved posts.

        Args:
            dry_run: If True, don't actually download files
            parallel_downloads: Number of parallel downloads
        """
        logger.info("------------------------------------------------------------------------")
        logger.info(f"--- Downloading saved posts - {time.strftime('%c')}")

        download_folder = f"downloads-{time.strftime('%Y-%m-%d')}"
        downloader = MediaDownloader(download_folder, dry_run=dry_run, config=self.config)

        total_saved = 0
        total_skipped: Set[str] = set()
        total_errored: Set[str] = set()
        batch_num = 0

        while True:
            batch_num += 1
            logger.info("------------------------------------------------------------------------")
            logger.info(f"Starting batch {batch_num}")

            submissions = self.get_saved_submissions()
            num_success, skipped, errored = self.process_submissions(
                submissions, downloader,
                unsave_on_success=True,
                archive_on_skip=True
            )

            total_skipped.update(skipped)
            total_errored.update(errored)
            total_saved += num_success

            # Check if there was any activity (downloads, archives, or skips)
            batch_activity = num_success + len(skipped) + len(errored)
            
            logger.info(f"Done with batch {batch_num}, saved {num_success}, total activity: {batch_activity}")

            # Stop if there was no activity at all in this batch
            if batch_activity == 0:
                logger.info("No activity in batch, stopping")
                break

        self._print_summary(total_saved, total_skipped, total_errored)

    def run_user_download(self, username: str, dry_run: bool = False, parallel_downloads: int = 1):
        """Download from a specific user's submissions.

        Args:
            username: Reddit username to download from
            dry_run: If True, don't actually download files
            parallel_downloads: Number of parallel downloads
        """
        logger.info("------------------------------------------------------------------------")
        logger.info(f"--- Downloading user: {username} - {time.strftime('%c')}")

        download_folder = f"downloads-{username}"
        downloader = MediaDownloader(download_folder, dry_run=dry_run, config=self.config)

        # Get last processed timestamp
        last_processed = self._get_last_processed(username)
        latest_timestamp = last_processed

        total_success = 0
        total_skipped: Set[str] = set()
        total_errored: Set[str] = set()

        batch_size = 100
        batch_num = 0

        try:
            submissions = self.get_user_submissions(username, last_processed)
            
            # Collect all submissions first, then reverse to process oldest-first
            all_submissions = list(submissions)
            all_submissions.reverse()  # Now oldest submissions are first
            
            logger.info(f"Found {len(all_submissions)} new submissions to process")
            
            # Process in batches
            batch = []
            for submission in all_submissions:
                batch.append(submission)
                
                if len(batch) >= batch_size:
                    batch_num += 1
                    logger.info("------------------------------------------------------------------------")
                    logger.info(f"Starting batch {batch_num}")
                    
                    num_success, skipped, errored, batch_latest = self._process_user_batch(
                        batch, downloader, latest_timestamp, username, parallel_downloads
                    )
                    
                    latest_timestamp = batch_latest
                    total_success += num_success
                    total_skipped.update(skipped)
                    total_errored.update(errored)
                    
                    logger.info(f"Done with batch {batch_num}, saved {num_success}")
                    
                    # Clear batch for next iteration
                    batch = []
                    
                    # Be nice to Reddit's servers between batches
                    time.sleep(2)
            
            # Process remaining submissions in final batch
            if batch:
                batch_num += 1
                logger.info("------------------------------------------------------------------------")
                logger.info(f"Starting batch {batch_num} (final)")
                
                num_success, skipped, errored, batch_latest = self._process_user_batch(
                    batch, downloader, latest_timestamp, username, parallel_downloads
                )
                
                latest_timestamp = batch_latest
                total_success += num_success
                total_skipped.update(skipped)
                total_errored.update(errored)
                
                logger.info(f"Done with batch {batch_num}, saved {num_success}")

            logger.info(f"\nTotal downloads: {total_success}")
            self._print_summary(total_success, total_skipped, total_errored)
            
            # Run deduplication identification after downloads complete
            if not dry_run and total_success > 0:
                logger.info("")
                self.dedupe_identify(download_folder)

        except Exception as e:
            logger.error(f"Error accessing user '{username}': {e}")

    def _process_single_submission(self, submission, downloader, username):
        """Process a single submission.
        
        Args:
            submission: PRAW submission object
            downloader: MediaDownloader instance
            username: Reddit username (for saving progress)
            
        Returns:
            Tuple of (submission, success, skipped_msg, error_msg, timestamp)
        """
        link_id = submission.id
        timestamp = int(submission.created_utc)
        
        try:
            link_url = submission.url
        except AttributeError:
            logger.info(f"{link_id} - not a link")
            return (submission, False, f"{link_id} - Not a link", None, timestamp)

        # Skip certain subreddits
        if submission.subreddit.display_name in self.config.SKIPPED_SUBREDDITS:
            logger.info(f"{link_id} - skipping {submission.subreddit.display_name}")
            return (submission, False, f"{link_id} - Skipping {submission.subreddit.display_name}", None, timestamp)

        # Skip Reddit posts (not direct media)
        if "www.reddit.com/r/" in link_url or "reddit.com/r/" in link_url:
            logger.info(f"{link_id} - Skipping Reddit post")
            return (submission, False, f"{link_id} {link_url} - Reddit post", None, timestamp)

        # Format timestamp for logging
        timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(submission.created_utc))
        
        logger.info("")
        logger.info(f"{link_id} - {timestamp_str} - {link_url}")

        # Process the submission
        downloaded, error = downloader.process_submission(submission)

        # Save progress after each submission
        self._update_last_processed(username, timestamp)

        if downloaded:
            logger.info("       - Success")
            return (submission, True, None, None, timestamp)
        elif error:
            logger.error(f"       - Error: {error}")
            return (submission, False, None, f"{link_id} {link_url}: {error}", timestamp)
        else:
            logger.info("       - Can't handle, skipped")
            return (submission, False, f"{link_id} {link_url} - Skipped", None, timestamp)

    def _process_user_batch(self, batch, downloader, latest_timestamp, username, parallel_downloads=1):
        """Process a batch of user submissions.

        Args:
            batch: List of submission objects
            downloader: MediaDownloader instance
            latest_timestamp: Current latest timestamp
            username: Reddit username (for saving progress)
            parallel_downloads: Number of parallel downloads

        Returns:
            Tuple of (num_success, skipped, errored, latest_timestamp)
        """
        num_success = 0
        skipped = set()
        errored = set()

        if parallel_downloads > 1:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=parallel_downloads) as executor:
                futures = {
                    executor.submit(self._process_single_submission, submission, downloader, username): submission
                    for submission in batch
                }
                
                for future in as_completed(futures):
                    submission, success, skip_msg, error_msg, timestamp = future.result()
                    latest_timestamp = max(latest_timestamp, timestamp)
                    
                    if success:
                        num_success += 1
                    elif error_msg:
                        errored.add(error_msg)
                    elif skip_msg:
                        skipped.add(skip_msg)
                    
                    # Small delay between completions
                    time.sleep(0.1)
        else:
            # Sequential processing
            for submission in batch:
                # Update latest timestamp
                latest_timestamp = max(latest_timestamp, int(submission.created_utc))
                
                link_id = submission.id

                try:
                    link_url = submission.url
                except AttributeError:
                    logger.info(f"{link_id} - not a link")
                    skipped.add(f"{link_id} - Not a link")
                    continue

                # Skip certain subreddits
                if submission.subreddit.display_name in self.config.SKIPPED_SUBREDDITS:
                    logger.info(f"{link_id} - skipping {submission.subreddit.display_name}")
                    skipped.add(f"{link_id} - Skipping {submission.subreddit.display_name}")
                    continue

                # Skip Reddit posts (not direct media)
                if "www.reddit.com/r/" in link_url or "reddit.com/r/" in link_url:
                    logger.info(f"{link_id} - Skipping Reddit post")
                    skipped.add(f"{link_id} {link_url} - Reddit post")
                    continue

                # Format timestamp for logging
                timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(submission.created_utc))
                
                logger.info("")
                logger.info(f"{link_id} - {timestamp_str} - {link_url}")

                # Process the submission
                downloaded, error = downloader.process_submission(submission)

                # Handle results
                if downloaded:
                    logger.info("       - Success")
                    num_success += 1
                elif error:
                    logger.error(f"       - Error: {error}")
                    errored.add(f"{link_id} {link_url}: {error}")
                else:
                    logger.info("       - Can't handle, skipped")
                    skipped.add(f"{link_id} {link_url} - Skipped")

                # Save progress after each submission
                self._update_last_processed(username, latest_timestamp)

                # Be nice to Reddit's servers
                time.sleep(0.5)

        return num_success, skipped, errored, latest_timestamp

    def dedupe_identify(self, folder_path: str):
        """Identify duplicate files and copy to dupe-check folder for review.
        
        Args:
            folder_path: Path to folder to dedupe
            
        Returns:
            Tuple of (num_files_checked, num_deleted_503, num_dupe_groups)
        """
        if not os.path.exists(folder_path):
            logger.error(f"Folder does not exist: {folder_path}")
            return 0, 0, 0
            
        logger.info("------------------------------------------------------------------------")
        logger.info(f"--- Identifying duplicates in: {folder_path}")
        
        sizes = {}
        dupes = {}
        num_deleted = 0
        num_files = 0
        
        # First pass: identify duplicates by size
        for filename in os.listdir(folder_path):
            filepath = os.path.join(folder_path, filename)
            
            # Skip directories
            if os.path.isdir(filepath):
                continue
                
            num_files += 1
            size = os.path.getsize(filepath)
            
            # Delete 503-byte files (common error file size)
            if size == 503:
                logger.info(f"Deleting 503-byte error file: {filename}")
                os.remove(filepath)
                num_deleted += 1
                continue
            
            # Track duplicates by size
            if size in sizes:
                # Mark as duplicate for manual review
                if size not in dupes:
                    dupes[size] = []
                    # Add the original file too
                    dupes[size].append(sizes[size])
                dupes[size].append(filepath)
            else:
                sizes[size] = filepath
        
        logger.info(f"{num_files} files checked, {num_deleted} error files deleted")
        
        total_dupes = sum(len(files) for files in dupes.values())
        logger.info(f"Found {len(dupes)} duplicate size groups, {total_dupes} total files to review")
        
        # Copy all duplicate groups to dupe-check folder
        if total_dupes > 0:
            dupebase = os.path.join(folder_path, "dupe-check")
            if os.path.exists(dupebase):
                logger.info(f"Removing existing dupe-check folder: {dupebase}")
                shutil.rmtree(dupebase)
            os.makedirs(dupebase)
            
            # Also save the mapping for later
            mapping_file = os.path.join(dupebase, ".dedupe_mapping.txt")
            
            logger.info(f"Copying duplicates to: {dupebase}")
            with open(mapping_file, 'w') as f:
                group_num = 0
                for size, filepaths in dupes.items():
                    # Write mapping: group_num -> list of original filepaths
                    f.write(f"{group_num}:{','.join(filepaths)}\n")
                    
                    # Copy all files in this group
                    for filepath in filepaths:
                        filename = os.path.basename(filepath)
                        newname = os.path.join(dupebase, f"{group_num:04d}-{filename}")
                        shutil.copyfile(filepath, newname)
                    
                    group_num += 1
                    if group_num % 100 == 0:
                        logger.info(f"Processed {group_num} duplicate groups...")
            
            logger.info("")
            logger.info("=" * 80)
            logger.info("NEXT STEPS:")
            logger.info(f"1. Review files in: {dupebase}")
            logger.info("2. DELETE files that are TRUE duplicates (select all, uncheck different ones)")
            logger.info("3. KEEP files that are different (but same size)")
            logger.info(f"4. Run: python main.py --dedupe-apply {os.path.basename(folder_path).replace('downloads-', '')}")
            logger.info("=" * 80)
        
        return num_files, num_deleted, len(dupes)

    def dedupe_apply(self, folder_path: str):
        """Apply deduplication based on user's review in dupe-check folder.
        
        Logic:
        - If ALL files in a group were deleted from dupe-check → true duplicates → keep only first, delete rest
        - If ANY files remain in dupe-check → different files → keep all in main folder
        
        Args:
            folder_path: Path to folder to apply deduplication
            
        Returns:
            Tuple of (num_groups_processed, num_files_deleted)
        """
        dupebase = os.path.join(folder_path, "dupe-check")
        mapping_file = os.path.join(dupebase, ".dedupe_mapping.txt")
        
        if not os.path.exists(dupebase):
            logger.error(f"dupe-check folder does not exist: {dupebase}")
            logger.error("Run download first to identify duplicates")
            return 0, 0
            
        if not os.path.exists(mapping_file):
            logger.error(f"Mapping file not found: {mapping_file}")
            logger.error("dupe-check folder may be from old version, please re-run download")
            return 0, 0
        
        logger.info("------------------------------------------------------------------------")
        logger.info(f"--- Applying deduplication for: {folder_path}")
        
        # Read the mapping
        group_mapping = {}
        with open(mapping_file, 'r') as f:
            for line in f:
                parts = line.strip().split(':', 1)
                if len(parts) == 2:
                    group_num = int(parts[0])
                    filepaths = parts[1].split(',')
                    group_mapping[group_num] = filepaths
        
        num_groups = len(group_mapping)
        num_deleted = 0
        
        # Check each group
        for group_num, original_filepaths in group_mapping.items():
            # Check which files remain in dupe-check
            remaining_in_dupecheck = []
            for filepath in original_filepaths:
                filename = os.path.basename(filepath)
                dupe_filepath = os.path.join(dupebase, f"{group_num:04d}-{filename}")
                if os.path.exists(dupe_filepath):
                    remaining_in_dupecheck.append(filepath)
            
            # Decision logic
            if len(remaining_in_dupecheck) == 0:
                # All files deleted from dupe-check → true duplicates
                # Keep only the first file, delete the rest
                logger.info(f"Group {group_num:04d}: True duplicates detected, keeping first file only")
                for i, filepath in enumerate(original_filepaths):
                    if i == 0:
                        logger.info(f"  Keeping: {os.path.basename(filepath)}")
                    else:
                        if os.path.exists(filepath):
                            logger.info(f"  Deleting: {os.path.basename(filepath)}")
                            os.remove(filepath)
                            num_deleted += 1
            else:
                # Some files remain → they're different, keep all
                logger.info(f"Group {group_num:04d}: Different files, keeping all {len(original_filepaths)} files")
        
        # Clean up dupe-check folder
        logger.info(f"Removing dupe-check folder: {dupebase}")
        shutil.rmtree(dupebase)
        
        logger.info("------------------------------------------------------------------------")
        logger.info(f"Processed {num_groups} duplicate groups")
        logger.info(f"Deleted {num_deleted} duplicate files")
        logger.info("Deduplication complete!")
        
        return num_groups, num_deleted

    def _print_summary(self, total_saved: int, total_skipped: Set[str], total_errored: Set[str]):
        """Print summary of downloads.

        Args:
            total_saved: Number of successful downloads
            total_skipped: Set of skipped items
            total_errored: Set of errored items
        """
        logger.info("#######################################################################")
        logger.info("")
        logger.info(f"Skipped: {len(total_skipped)}")
        logger.info("")
        for link in sorted(list(total_skipped), key=lambda s: str(s)[7:]):
            logger.info(link)

        logger.info("#######################################################################")
        logger.info("")
        logger.info(f"Errors: {len(total_errored)}")
        logger.info("")
        for link in sorted(list(total_errored), key=lambda s: str(s)[7:]):
            logger.info(link)

        logger.info("#######################################################################")
        logger.info("")
        logger.info(f"Saved: {total_saved}")
        logger.info("")

        logger.info("#######################################################################")
        logger.info("Done")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Download Reddit media from saved posts or user submissions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download your saved posts
  python main.py

  # Download from a specific user
  python main.py --user username

  # Apply deduplication after review
  python main.py --dedupe-apply username

  # Dry run (test without downloading)
  python main.py --dry-run
  python main.py --user username --dry-run
        """
    )
    parser.add_argument(
        '--user',
        type=str,
        help='Download submissions from a specific Reddit user'
    )
    parser.add_argument(
        '--dedupe-apply',
        type=str,
        metavar='USERNAME',
        help='Apply deduplication for a user after reviewing dupe-check folder'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without actually downloading files'
    )
    parser.add_argument(
        '--parallel',
        type=int,
        default=1,
        metavar='N',
        help='Number of parallel downloads (default: 1, recommended: 3-5)'
    )

    args = parser.parse_args()

    try:
        # Validate configuration (not needed for dedupe-apply)
        if not args.dedupe_apply:
            Config.validate()

        # Create manager (not needed for dedupe-apply)
        manager = RedditSaveManager(Config) if not args.dedupe_apply else None

        # Run appropriate mode
        if args.dedupe_apply:
            # Dedupe apply mode - doesn't need Reddit connection
            temp_manager = type('obj', (object,), {
                'dedupe_apply': RedditSaveManager.dedupe_apply
            })()
            download_folder = f"downloads-{args.dedupe_apply}"
            temp_manager.dedupe_apply(download_folder)
        elif args.user:
            manager.run_user_download(args.user, dry_run=args.dry_run, parallel_downloads=args.parallel)
        else:
            manager.run_saved_posts(dry_run=args.dry_run, parallel_downloads=args.parallel)

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
