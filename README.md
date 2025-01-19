# 🌱 TikTok Recursive Follower Farmer

[![Python Version](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

A powerful Python tool that recursively harvests TikTok user data by traversing through follower networks. Starting with a seed username (0dayctf) it will then grab the followers data. After reaching the end of pagination for a user it will then use the secUid from another user to get their followers (Private accounts will be attempted then moved past gracefully). A new msToken is grabbed when 30 seconds has passed and no new unique users are found to ensure functionality. A unique users list is created and checked names to keep track for future runs if you crash or need to run it again in the future.

```
uniqueId,followerCount,followingCount,videoCount,nickname,secUid,signature
```

## 🎯 Features

- 📊 Recursive follower traversal
- 🔄 Automatic rate limit handling
- 💾 CSV data export
- 📝 Comprehensive error logging
- 🚦 Progress tracking
- 🔒 Session management
- 📈 Real-time statistics

## 🛠️ How It Works

The script follows this process flow:

```mermaid
graph TD
    A[Start with Seed User] --> B[Fetch SecUID]
    B --> C[Get User's Followers]
    C --> D[Store User Data]
    D --> E[Add to Queue]
    E --> F{More Users?}
    F -->|Yes| B
    F -->|No| G[Complete]
```

## 📋 Data Collection

The script collects the following user information:

| Field | Description |
|-------|-------------|
| uniqueId | User's TikTok username |
| followerCount | Number of followers |
| followingCount | Number of accounts followed |
| videoCount | Number of videos posted |
| nickname | Display name |
| secUid | Unique security identifier |
| signature | User's bio |

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/pentestfunctions/tiktok-recursive-follower-farmer.git

# Install required packages
pip install -r requirements.txt

# Install Firefox WebDriver (required for token generation)
# Download geckodriver and place it in the project directory
```

## 📦 Dependencies

- requests
- selenium
- rich
- firefox-webdriver

## 🔧 Usage

1. Set up your environment:
   ```bash
   # Ensure geckodriver is in your project directory
   # Create empty files for data storage
   touch checked_names.txt tiktok_users.csv
   ```

2. Run the script:
   ```bash
   python3 scraper.py
   ```

## 🎛️ Configuration

The script uses several configuration variables that can be modified:

```python
headers = {
    "User-Agent": "Mozilla/5.0 ...",
    "Referer": "https://www.tiktok.com/",
}
```

## 📊 Output Files

| File | Purpose |
|------|---------|
| tiktok_users.csv | Stores all collected user data |
| checked_names.txt | Tracks processed users |
| failed_checks_{timestamp}.log | Records errors and failures |

## 🛡️ Error Handling

The script implements robust error handling:
- ⏳ Automatic retry mechanism for rate limits
- 🔄 Token refresh when needed
- 📝 Detailed error logging
- 🚫 Duplicate user prevention

## 📈 Performance

The script includes real-time performance monitoring:
- Users processed per second
- Users processed per minute
- Total unique users found
- Total accounts checked
- Failed checks counter
- Remaining users to check

## ⚠️ Important Notes

- 🕒 Respects TikTok's rate limits
- 🔑 Requires valid session tokens
- 📱 Uses Firefox in headless mode
- 💻 Supports resume functionality
- 🔍 Implements duplicate checking

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Rich library for beautiful console output
- Selenium for session management
- TikTok's public API structure

## ⚡ Performance Tips

1. Adjust sleep timers based on your needs
2. Monitor rate limiting responses
3. Use appropriate retry counts
4. Keep Firefox WebDriver updated
5. Monitor system resources

## 🔮 Future Improvements

- [ ] Add proxy support
- [ ] Implement multi-threading
- [ ] Add data export formats
- [ ] Improve token management
- [ ] Add user filtering options

Remember to use this tool responsibly and in accordance with TikTok's terms of service.
