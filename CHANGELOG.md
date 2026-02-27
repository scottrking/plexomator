# Changelog

All notable changes to Plexomator will be documented in this file.

## [1.0.0] - 2026-02-16

### Added
- Interactive button-based movie selection
- TMDB search integration
- Director information in search results
- Channel notifications when movies are added
- Auto-detection of TMDB IDs in channel posts
- Slash command `/addmovie` support
- @mention support for bot interaction
- Systemd service for background operation
- Automatic installation script
- Duplicate movie detection

### Features
- Socket Mode connection (no public URL needed)
- Support for multiple search methods (title, TMDB ID, direct add)
- Customizable quality profiles and root folders
- Reaction-based feedback (✅ for success)
- Threaded replies to keep channels clean

### Technical
- Python 3.8+ support
- Ubuntu/Linux systemd integration
- Virtual environment isolation
- Comprehensive logging via journald
- Environment-based configuration

## [0.2.0] - 2026-02-15

### Added
- TMDB search with numbered selection
- Director name fetching from TMDB credits API

### Changed
- Updated from basic auto-detection to interactive search

## [0.1.0] - 2026-02-13

### Added
- Initial release
- Basic TMDB ID detection
- Radarr API integration
- Slack Socket Mode setup
- Auto-add functionality
