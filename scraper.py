import requests
import json
import time
import re
import csv
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import time
import logging
from datetime import datetime

# Configuration Variables
maxCursor = 0
minCursor = 9999999999
console = Console()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Referer": "https://www.tiktok.com/",
}

# Set up logging
log_filename = f"failed_checks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

profile_api_url = "https://www.tiktok.com/@{username}"
api_url = (
    "https://www.tiktok.com/api/user/list/?"
    "WebIdLastTime=1734308807&aid=1988&app_language=en&app_name=tiktok_web"
    "&browser_language=en-US&browser_name=Mozilla&browser_online=true"
    "&browser_platform=Win32&browser_version=5.0%20(Windows%20NT%2010.0;%20Win64;%20x64)%20AppleWebKit/537.36"
    "&channel=tiktok_web&cookie_enabled=true&count=30"
    "&data_collection_enabled=true"
    "&device_platform=web_pc&focus_state=false&from_page=user"
    "&history_len=12&is_fullscreen=false&is_page_visible=true"
    "&maxCursor={maxCursor}&minCursor={minCursor}"
    "&secUid={secUid}&tz_name=Pacific%2FAuckland&user_is_login=true"
    "&webcast_language=en"
    "&msToken={msToken}"
)

def log_failure(error_type, details, username=None, secUid=None):
    error_msg = f"Error Type: {error_type}\n"
    if username:
        error_msg += f"Username: {username}\n"
    if secUid:
        error_msg += f"SecUid: {secUid}\n"
    error_msg += f"Details: {details}\n"
    error_msg += "-" * 50
    logging.error(error_msg)
    console.print(f"[bold red]Error logged to {log_filename}[/bold red]")

def get_line_count(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", newline="", encoding="utf-8") as file:
                return sum(1 for _ in file)
    except Exception as e:
        error_msg = f"Error counting lines in {file_path}: {e}"
        log_failure("File Operation Error", error_msg)
        return 0
    return 0

def fetch_msToken(url):
    try:
        firefox_options = Options()
        firefox_options.add_argument("--headless")
        firefox_options.add_argument("--disable-gpu")
        firefox_options.add_argument("--no-sandbox")
        
        geckodriver_path = os.path.join(os.getcwd(), "geckodriver")
        service = Service(executable_path=geckodriver_path)
        driver = webdriver.Firefox(service=service, options=firefox_options)
        
        driver.get(url)
        time.sleep(5)
        
        cookies = driver.get_cookies()
        msToken = next((cookie['value'] for cookie in cookies if cookie['name'] == 'msToken'), None)
        
        if msToken:
            console.print(f"[bold green]Successfully fetched new msToken[/bold green]")
        else:
            log_failure("msToken Error", "msToken not found in cookies", url)
        
        driver.quit()
        return msToken
    except Exception as e:
        log_failure("Selenium Error", str(e), url)
        return None

def fetch_secUid(username):
    try:
        url = profile_api_url.format(username=username)
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            log_failure("HTTP Error", f"Status code: {response.status_code}", username)
            return None
            
        match = re.search(r'"secUid":"(.*?)"', response.text)
        if match:
            secUid = match.group(1)
            console.print(f"[bold green]Found secUid for '{username}'[/bold green]")
            return secUid
            
        log_failure("Parse Error", "secUid pattern not found in response", username)
        return None
    except Exception as e:
        log_failure("Request Error", str(e), username)
        return None

# Track the number of users processed and the start time
users_processed_count = 0
last_processed_time = time.time()

# Update the display
def update_user_processing_rate():
    global users_processed_count, last_processed_time

    current_time = time.time()
    
    elapsed_time_seconds = current_time - last_processed_time
    elapsed_time_minutes = elapsed_time_seconds / 60

    if elapsed_time_seconds > 0:
        rate_per_second = users_processed_count / elapsed_time_seconds
        rate_per_minute = users_processed_count / elapsed_time_minutes
    else:
        rate_per_second = 0
        rate_per_minute = 0

    last_processed_time = current_time
    users_processed_count = 0  # Reset count after displaying the rate

    return rate_per_second, rate_per_minute

def update_checked_names(nickname, secUid):
    try:
        with open("checked_names.txt", "a", encoding="utf-8") as file:
            file.write(f"{nickname},{secUid}\n")
        return True
    except Exception as e:
        log_failure("File Write Error", str(e), nickname, secUid)
        return False

def fetch_users(secUid, existing_users=None, max_retries=3, max_empty_pages=3):
    if existing_users is None:
        existing_users = load_existing_users("tiktok_users.csv")  # Load existing users at the start

    global msToken, maxCursor, minCursor, users_processed_count
    last_added_time = time.time()
    users_processed = False
    empty_page_count = 0
    retry_count = 0

    # Start with a high initial minCursor value to ensure last results from follower list pagination
    minCursor = 9999999999

    if not msToken:
        msToken = fetch_msToken("https://www.tiktok.com/@0dayctf")
        if not msToken:
            log_failure("Token Error", "Failed to fetch msToken")
            return False

    try:
        with open("tiktok_users.csv", "a", newline="", encoding="utf-8") as csvfile:
            csv_writer = csv.writer(csvfile)
            if os.stat("tiktok_users.csv").st_size == 0:
                csv_writer.writerow([  # write the header if file is empty
                    "uniqueId", "followerCount", "followingCount", "videoCount",
                    "nickname", "secUid", "signature"
                ])

            while True:
                url = api_url.format(
                    maxCursor=maxCursor,
                    minCursor=minCursor,
                    secUid=secUid,
                    msToken=msToken
                )

                try:
                    response = requests.get(url, headers=headers)

                    if response.status_code == 429:
                        if retry_count < max_retries:
                            retry_count += 1
                            wait_time = 2 ** retry_count
                            console.print(f"[yellow]Rate limited. Waiting {wait_time} seconds...[/yellow]")
                            time.sleep(wait_time)
                            msToken = fetch_msToken("https://www.tiktok.com/@0dayctf")
                            continue
                        else:
                            log_failure("Rate Limit Error", "Max retries reached", secUid=secUid)
                            break

                    if response.status_code != 200:
                        log_failure("API Error", f"Status code: {response.status_code}", secUid=secUid)
                        if retry_count < max_retries:
                            retry_count += 1
                            time.sleep(2)
                            continue
                        break

                    data = response.json()
                    users = data.get("userList", [])

                    if not users:
                        empty_page_count += 1
                        if empty_page_count >= max_empty_pages:
                            console.print("[yellow]Reached maximum empty pages. Moving to next user.[/yellow]")
                            break
                        msToken = fetch_msToken("https://www.tiktok.com/@0dayctf")
                        time.sleep(2)
                        continue

                    empty_page_count = 0
                    retry_count = 0
                    new_users_added = False

                    for user in users:
                        user_info = user.get("user", {})
                        stats = user.get("stats", {})
                        uniqueId = user_info.get("uniqueId")
                        followerCount = stats.get("followerCount", 0)
                        followingCount = stats.get("followingCount", 0)
                        videoCount = stats.get("videoCount", 0)

                        if uniqueId and uniqueId not in existing_users:
                            try:
                                csv_writer.writerow([
                                    uniqueId,
                                    followerCount,
                                    followingCount,
                                    videoCount,
                                    user_info.get("nickname", "Unknown"),
                                    user_info.get("secUid", "Unknown"),
                                    user_info.get("signature", "Unknown")
                                ])
                                csvfile.flush()
                                existing_users.add(uniqueId)  # Add to the in-memory set
                                new_users_added = True
                                users_processed = True
                                last_added_time = time.time()
                                users_processed_count += 1
                            except Exception as e:
                                log_failure("CSV Write Error", str(e), uniqueId, secUid)

                    # update cursors for pagination
                    new_min_cursor = data.get("minCursor")
                    new_max_cursor = data.get("maxCursor")
                    minCursor = new_min_cursor if new_min_cursor else minCursor
                    maxCursor = new_max_cursor if new_max_cursor else maxCursor

                    # check if more users are available
                    if not data.get("hasMore", False):
                        console.print("[yellow]No more users available for this profile. Moving to the next one.[/yellow]")
                        break

                    console.clear()
                    line_count_tiktok = get_line_count("tiktok_users.csv") - 1
                    line_count_checked = get_line_count("checked_names.txt")
                    display_stats_with_rate(line_count_tiktok, line_count_checked)

                    time.sleep(1)

                except Exception as e:
                    log_failure("User Processing Error", str(e), secUid=secUid)
                    if retry_count < max_retries:
                        retry_count += 1
                        time.sleep(2)
                        continue
                    break

    except Exception as e:
        log_failure("File Operation Error", str(e), secUid=secUid)
        return False

    return users_processed

def load_existing_users(file_path):
    """ Load existing users from the CSV file into a set """
    existing_users = set()
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", newline="", encoding="utf-8") as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                for row in reader:
                    existing_users.add(row[0])
    except Exception as e:
        log_failure("File Read Error", str(e), file_path)
    return existing_users

def display_stats_with_rate(line_count_tiktok, line_count_checked):
    failed_checks = get_line_count(log_filename)
    rate_per_second, rate_per_minute = update_user_processing_rate()
    
    stats_panel = Panel(
        f"[bold blue]Total Unique Users Found: {line_count_tiktok}\n"
        f"Total Accounts Checked: {line_count_checked}\n"
        f"Failed Checks: {failed_checks}\n"
        f"Remaining To Check: {max(0, line_count_tiktok - line_count_checked)}\n"
        f"Users Processed Rate: {rate_per_second:.2f} users/second\n"
        f"Users Processed Rate: {rate_per_minute:.2f} users/minute[/bold blue]",
        title="User Check Status",
        border_style="green"
    )
    console.print(stats_panel)

if __name__ == "__main__":
    console.print(f"[bold green]Starting scraper. Logging failures to: {log_filename}[/bold green]")
    
    msToken = fetch_msToken("https://www.tiktok.com/@0dayctf")
    
    # Initialize files if they don't exist
    if not os.path.exists("checked_names.txt"):
        open("checked_names.txt", "w", encoding="utf-8").close()
    
    if not os.path.exists("tiktok_users.csv"):
        with open("tiktok_users.csv", "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                "uniqueId", "followerCount", "followingCount", "videoCount",
                "nickname", "secUid", "signature"
            ])

    checked_users = set()
    with open("checked_names.txt", "r", encoding="utf-8") as file:
        for line in file:
            if "," in line:
                nickname, secUid = line.strip().split(",", 1)
                checked_users.add(secUid)

    starting_username = "0dayctf"
    secUid = fetch_secUid(starting_username)
    
    if secUid and secUid not in checked_users:
        if fetch_users(secUid):
            update_checked_names(starting_username, secUid)
        else:
            log_failure("User Processing Failed", "Failed to process starting user", starting_username, secUid)

    with open("tiktok_users.csv", "r", newline="", encoding="utf-8") as csvfile:
        csv_reader = csv.reader(csvfile)
        next(csv_reader)  # Skip header
        
        for row in csv_reader:
            if len(row) >= 6:  # Ensure row has enough columns
                secUid = row[5]
                nickname = row[4]
                
                if secUid not in checked_users:
                    console.print(f"Processing [bold yellow]{nickname}[/bold yellow]")
                    if fetch_users(secUid):
                        update_checked_names(nickname, secUid)
                    else:
                        log_failure("User Processing Failed", "Failed to process user", nickname, secUid)
                    time.sleep(1)

    line_count_tiktok = get_line_count("tiktok_users.csv") - 1
    line_count_checked = get_line_count("checked_names.txt")
    display_stats_with_rate(line_count_tiktok, line_count_checked)
