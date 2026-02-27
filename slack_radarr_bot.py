#!/usr/bin/env python3
"""
Slack Bot for Radarr Integration - v3 with Interactive Buttons
Monitors Slack channels for movie posts and adds them to Radarr automatically.
Also allows users to request movies via Slack commands with interactive button selection.
"""

import os
import re
import logging
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import requests
from typing import Optional, Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Slack app
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Radarr configuration
RADARR_URL = os.environ.get("RADARR_URL", "http://localhost:7878")
RADARR_API_KEY = os.environ.get("RADARR_API_KEY")
RADARR_ROOT_FOLDER = os.environ.get("RADARR_ROOT_FOLDER", "/movies")
RADARR_QUALITY_PROFILE = int(os.environ.get("RADARR_QUALITY_PROFILE", "1"))
MONITORED_CHANNEL = os.environ.get("MONITORED_CHANNEL_ID")

# TMDB configuration
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")


class TMDBClient:
    """Client for interacting with TMDB API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
    
    def search_movies(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for movies by title"""
        try:
            response = requests.get(
                f"{self.base_url}/search/movie",
                params={
                    "api_key": self.api_key,
                    "query": query,
                    "include_adult": False
                },
                timeout=10
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            
            # Enrich results with director info
            enriched_results = []
            for movie in results[:limit]:
                movie_id = movie.get('id')
                director = self.get_director(movie_id)
                movie['director'] = director
                enriched_results.append(movie)
            
            return enriched_results
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching TMDB: {e}")
            return []
    
    def get_director(self, movie_id: int) -> str:
        """Get director name for a movie"""
        try:
            response = requests.get(
                f"{self.base_url}/movie/{movie_id}/credits",
                params={"api_key": self.api_key},
                timeout=10
            )
            response.raise_for_status()
            crew = response.json().get("crew", [])
            
            # Find director(s)
            directors = [person['name'] for person in crew if person.get('job') == 'Director']
            
            if not directors:
                return "Director unknown"
            elif len(directors) == 1:
                return f"Directed by {directors[0]}"
            else:
                # Multiple directors
                return f"Directed by {', '.join(directors)}"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching director for movie {movie_id}: {e}")
            return "Director unknown"


class RadarrClient:
    """Client for interacting with Radarr API"""
    
    def __init__(self, url: str, api_key: str):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.headers = {"X-Api-Key": api_key}
    
    def search_movie(self, tmdb_id: int) -> Optional[Dict[Any, Any]]:
        """Search for a movie by TMDB ID"""
        try:
            response = requests.get(
                f"{self.url}/api/v3/movie/lookup/tmdb",
                params={"tmdbId": tmdb_id},
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching for movie with TMDB ID {tmdb_id}: {e}")
            return None
    
    def add_movie(self, movie_data: Dict[Any, Any], quality_profile: int, root_folder: str) -> bool:
        """Add a movie to Radarr"""
        try:
            payload = {
                "title": movie_data.get("title"),
                "year": movie_data.get("year"),
                "tmdbId": movie_data.get("tmdbId"),
                "qualityProfileId": quality_profile,
                "rootFolderPath": root_folder,
                "monitored": True,
                "addOptions": {
                    "searchForMovie": True
                }
            }
            
            response = requests.post(
                f"{self.url}/api/v3/movie",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Successfully added movie: {movie_data.get('title')} ({movie_data.get('year')})")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error adding movie to Radarr: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return False
    
    def check_if_exists(self, tmdb_id: int) -> bool:
        """Check if a movie already exists in Radarr"""
        try:
            response = requests.get(
                f"{self.url}/api/v3/movie",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            movies = response.json()
            return any(movie.get("tmdbId") == tmdb_id for movie in movies)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking if movie exists: {e}")
            return False


# Initialize clients
tmdb = TMDBClient(TMDB_API_KEY) if TMDB_API_KEY else None
radarr = RadarrClient(RADARR_URL, RADARR_API_KEY)


def extract_movie_info(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract movie information from text.
    Looks for patterns like:
    - "Title (Year) TMDB: 12345"
    - "Title - Year - TMDB:12345"
    - "TMDB ID: 12345"
    """
    # Try to extract TMDB ID first (most important)
    tmdb_match = re.search(r'tmdb[:\s]*(\d+)', text, re.IGNORECASE)
    if not tmdb_match:
        return None
    
    tmdb_id = int(tmdb_match.group(1))
    
    # Try to extract title and year (optional, will fetch from API if not found)
    title_year_match = re.search(r'([^(]+)\s*\((\d{4})\)', text)
    
    result = {"tmdb_id": tmdb_id}
    if title_year_match:
        result["title"] = title_year_match.group(1).strip()
        result["year"] = int(title_year_match.group(2))
    
    return result


def add_movie_to_radarr(tmdb_id: int) -> tuple[bool, str]:
    """
    Add a movie to Radarr by TMDB ID
    Returns (success: bool, message: str)
    """
    # Check if movie already exists
    if radarr.check_if_exists(tmdb_id):
        return False, "Movie already exists in Radarr"
    
    # Search for movie details
    movie_data = radarr.search_movie(tmdb_id)
    if not movie_data:
        return False, f"Could not find movie with TMDB ID {tmdb_id}"
    
    # Add movie to Radarr
    success = radarr.add_movie(movie_data, RADARR_QUALITY_PROFILE, RADARR_ROOT_FOLDER)
    
    if success:
        title = movie_data.get('title', 'Unknown')
        year = movie_data.get('year', 'Unknown')
        return True, f"✅ Added *{title}* ({year}) to Radarr and started searching!"
    else:
        return False, "Failed to add movie to Radarr. Check logs for details."


def format_search_results_with_buttons(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Format TMDB search results as Slack blocks with buttons"""
    if not results:
        return {
            "text": "No movies found. Try a different search term.",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "❌ No movies found. Try a different search term."
                    }
                }
            ]
        }
    
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Select a movie to add:*"
            }
        },
        {"type": "divider"}
    ]
    
    for movie in results:
        title = movie.get('title', 'Unknown')
        year = movie.get('release_date', '')[:4] if movie.get('release_date') else 'Unknown'
        tmdb_id = movie.get('id')
        director = movie.get('director', 'Director unknown')
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{title}* ({year}) • TMDB: {tmdb_id}\n_{director}_"
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Add This"
                },
                "style": "primary",
                "value": str(tmdb_id),
                "action_id": f"add_movie_{tmdb_id}"
            }
        })
    
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "💡 Or use `/addmovie TMDB: [id]` to add directly"
            }
        ]
    })
    
    return {
        "text": "Select a movie to add",
        "blocks": blocks
    }


# Listen for messages in monitored channel
@app.message(re.compile(r".*", re.IGNORECASE))
def handle_movie_post(message, say, logger):
    """Handle messages in the monitored channel"""
    # Only process messages in the monitored channel
    if MONITORED_CHANNEL and message.get('channel') != MONITORED_CHANNEL:
        return
    
    text = message.get('text', '')
    
    # Extract movie info
    movie_info = extract_movie_info(text)
    if not movie_info:
        return  # Not a movie post, ignore silently
    
    logger.info(f"Detected movie post: {text}")
    
    # Add to Radarr
    success, msg = add_movie_to_radarr(movie_info['tmdb_id'])
    
    # React to the message
    if success:
        try:
            app.client.reactions_add(
                channel=message['channel'],
                timestamp=message['ts'],
                name='white_check_mark'
            )
        except Exception as e:
            logger.error(f"Could not add reaction: {e}")
        
        # Post confirmation
        say(msg, thread_ts=message['ts'])
    else:
        if "already exists" in msg.lower():
            try:
                app.client.reactions_add(
                    channel=message['channel'],
                    timestamp=message['ts'],
                    name='heavy_check_mark'
                )
            except Exception as e:
                logger.error(f"Could not add reaction: {e}")
        else:
            logger.warning(f"Failed to add movie: {msg}")


# Slash command to add movies
@app.command("/addmovie")
def handle_add_movie_command(ack, command, respond):
    """Handle /addmovie slash command with search support"""
    ack()
    
    text = command.get('text', '').strip()
    
    if not text:
        respond("⚠️ Please provide either a TMDB ID or a movie title.\n"
                "Examples:\n"
                "• `/addmovie TMDB: 550`\n"
                "• `/addmovie Fight Club`\n"
                "• `/addmovie The Matrix 1999`")
        return
    
    # Check if it has a TMDB ID
    movie_info = extract_movie_info(text)
    
    if movie_info:
        # Has TMDB ID, add directly
        success, msg = add_movie_to_radarr(movie_info['tmdb_id'])
        respond(msg)
    else:
        # No TMDB ID, search for it
        if not tmdb:
            respond("⚠️ TMDB search is not configured. Please provide a TMDB ID.\n"
                   "Example: `/addmovie TMDB: 550`")
            return
        
        # Search TMDB
        results = tmdb.search_movies(text)
        
        if not results:
            respond(f"❌ No movies found for '{text}'. Try a different search term.")
            return
        
        # Format and display results with buttons
        message = format_search_results_with_buttons(results)
        respond(message)


# Handle button clicks
@app.action(re.compile(r"add_movie_(\d+)"))
def handle_add_movie_button(ack, action, respond, body):
    """Handle when user clicks 'Add This' button"""
    ack()
    
    # Extract TMDB ID from action_id
    tmdb_id = int(action['value'])
    
    # Get user info
    user_id = body['user']['id']
    channel_id = body['channel']['id']
    
    # Get movie details for the channel message
    movie_data = radarr.search_movie(tmdb_id)
    
    # Add to Radarr
    success, msg = add_movie_to_radarr(tmdb_id)
    
    # Update the ephemeral message to show result
    respond(
        text=msg,
        replace_original=True,
        response_type="ephemeral"
    )
    
    # Also post to the channel if successful
    if success and movie_data:
        try:
            title = movie_data.get('title', 'Unknown')
            year = movie_data.get('year', 'Unknown')
            
            # Get director from TMDB if available
            if tmdb:
                credits_response = requests.get(
                    f"{tmdb.base_url}/movie/{tmdb_id}/credits",
                    params={"api_key": tmdb.api_key},
                    timeout=10
                )
                if credits_response.status_code == 200:
                    crew = credits_response.json().get("crew", [])
                    directors = [person['name'] for person in crew if person.get('job') == 'Director']
                    
                    if directors:
                        if len(directors) == 1:
                            director_text = f"Directed by {directors[0]}"
                        else:
                            # Join with "and" for last director
                            if len(directors) == 2:
                                director_text = f"Directed by {directors[0]} and {directors[1]}"
                            else:
                                director_text = f"Directed by {', '.join(directors[:-1])} and {directors[-1]}"
                    else:
                        director_text = ""
                else:
                    director_text = ""
            else:
                director_text = ""
            
            # Format the message
            if director_text:
                channel_msg = f"*{title}* ({year}) • {director_text}. Added to Plex by <@{user_id}>."
            else:
                channel_msg = f"*{title}* ({year}). Added to Plex by <@{user_id}>."
            
            app.client.chat_postMessage(
                channel=channel_id,
                text=channel_msg
            )
        except Exception as e:
            logger.error(f"Could not post to channel: {e}")


# App mention handler - allows users to @mention the bot
@app.event("app_mention")
def handle_mention(event, say):
    """Handle when the bot is mentioned"""
    text = event.get('text', '')
    
    # Extract movie info
    movie_info = extract_movie_info(text)
    
    if movie_info:
        # Has TMDB ID, add directly
        success, msg = add_movie_to_radarr(movie_info['tmdb_id'])
        say(msg, thread_ts=event['ts'])
    else:
        # Try to extract search query (remove the @mention)
        query = re.sub(r'<@[A-Z0-9]+>', '', text).strip()
        
        if not query:
            say(
                "Hi! You can:\n"
                "• Mention me with a TMDB ID: `@Plexomator TMDB: 550`\n"
                "• Search for a movie: `@Plexomator Fight Club`\n"
                "• Use the slash command: `/addmovie The Matrix`",
                thread_ts=event['ts']
            )
            return
        
        # Search TMDB
        if not tmdb:
            say(
                "Search is not configured. Please use: `@Plexomator TMDB: [id]`",
                thread_ts=event['ts']
            )
            return
        
        results = tmdb.search_movies(query)
        
        if not results:
            say(f"❌ No movies found for '{query}'", thread_ts=event['ts'])
            return
        
        # Display results with buttons
        message = format_search_results_with_buttons(results)
        say(**message, thread_ts=event['ts'])


# Health check for monitoring
@app.event("message")
def handle_message_events(body, logger):
    """Log all message events for debugging (can be removed in production)"""
    pass


if __name__ == "__main__":
    # Verify required environment variables
    required_vars = ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "RADARR_API_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)
    
    # TMDB is optional but recommended
    if not TMDB_API_KEY:
        logger.warning("TMDB_API_KEY not set. Search functionality will be disabled.")
    
    logger.info("Starting Slack Radarr Bot v3...")
    logger.info(f"Radarr URL: {RADARR_URL}")
    logger.info(f"Monitored Channel ID: {MONITORED_CHANNEL}")
    logger.info(f"TMDB Search: {'Enabled' if TMDB_API_KEY else 'Disabled'}")
    
    # Start the bot using Socket Mode
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
