import sys
import socket
import json
import os
import subprocess
import threading
import time
import hashlib
import sqlite3
from datetime import datetime, timedelta
from urllib.parse import urlparse
from PyQt5.QtCore import QUrl, pyqtSignal, QObject, QTimer, pyqtSlot, QThread, QSettings, Qt
from PyQt5.QtGui import QKeySequence, QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QPushButton, QLineEdit, QHBoxLayout, QTabWidget, QToolBar, QAction,
    QShortcut, QMessageBox, QDialog, QLabel, QComboBox, QProgressBar,
    QTextEdit, QCheckBox, QSlider, QSpinBox, QGroupBox, QSplitter,
    QListWidget, QListWidgetItem, QMenu, QSystemTrayIcon, QFrame,
    QDialogButtonBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineSettings

# --- Constants and Configuration ---
APP_NAME = "Null Browser"
APP_VERSION = "3.0 Enhanced"
DEFAULT_TOR_PORTS = [9050, 9150]
DEFAULT_DOWNLOAD_FOLDER_NAME = "NullBrowser_Media"
HISTORY_DB_NAME = "history.db"
BOOKMARKS_FILE_NAME = "bookmarks.json"
BROWSER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".null_browser")

# --- Global Dark Theme Stylesheet (QSS) ---
DARK_THEME_STYLESHEET = """
QMainWindow {
    background-color: #1e1e1e; /* Dark background for main window */
    color: #e0e0e0; /* Light text color */
}
QToolBar {
    background-color: #2d2d2d; /* Darker toolbar background */
    border: none;
    padding: 5px;
    spacing: 5px;
}
QToolButton {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border: 1px solid #4a4a4a;
    border-radius: 5px;
    padding: 5px 8px;
    font-size: 16px;
    min-width: 30px;
    min-height: 30px;
}
QToolButton:hover {
    background-color: #4a4a4a;
    border-color: #5a5a5a;
}
QToolButton:pressed {
    background-color: #2a2a2a;
    border-color: #3a3a3a;
}
QLineEdit {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border: 1px solid #4a4a4a;
    border-radius: 5px;
    padding: 5px;
    selection-background-color: #4285f4;
}
QLineEdit:focus {
    border: 1px solid #4285f4;
}
QTabWidget::pane { /* The tab widget frame */
    border: 1px solid #4a4a4a;
    background-color: #1e1e1e;
}
QTabBar::tab {
    background: #3a3a3a;
    border: 1px solid #4a4a4a;
    border-bottom-color: #3a3a3a; /* Same as pane color */
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 8ex;
    padding: 5px 10px;
    color: #e0e0e0;
}
QTabBar::tab:selected {
    background: #1e1e1e;
    border-bottom-color: #1e1e1e; /* Selected tab blends with pane */
}
QTabBar::tab:hover {
    background: #4a4a4a;
}
QTabBar::close-button {
    image: url(close_icon.png); /* Placeholder for a custom close icon */
    subcontrol-origin: padding;
    subcontrol-position: right;
    width: 16px;
    height: 16px;
    margin-left: 5px;
}
QTabBar::close-button:hover {
    background-color: #ff4444;
    border-radius: 3px;
}
QStatusBar {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border-top: 1px solid #4a4a4a;
    padding: 3px;
}
QDialog {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #4a4a4a;
    border-radius: 5px;
}
QGroupBox {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #4a4a4a;
    border-radius: 5px;
    margin-top: 1ex; /* Space for the title */
    padding-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left; /* Position at top left */
    padding: 0 3px;
    background-color: #2d2d2d;
    color: #e0e0e0;
}
QLabel {
    color: #e0e0e0;
}
QPushButton {
    background-color: #4285f4; /* Google Blue */
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 8px 15px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #3367d6; /* Darker blue on hover */
}
QPushButton:pressed {
    background-color: #2a56c0;
}
QPushButton:disabled {
    background-color: #5a5a5a;
    color: #9a9a9a;
}
QComboBox {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border: 1px solid #4a4a4a;
    border-radius: 5px;
    padding: 3px 5px;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 1px;
    border-left-color: #4a4a4a;
    border-left-style: solid;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
}
QComboBox::down-arrow {
    image: url(down_arrow.png); /* Placeholder for a custom arrow icon */
    width: 12px;
    height: 12px;
}
QComboBox QAbstractItemView {
    background-color: #3a3a3a;
    color: #e0e0e0;
    selection-background-color: #4285f4;
    selection-color: #ffffff;
    border: 1px solid #4a4a4a;
}
QProgressBar {
    border: 1px solid #4a4a4a;
    border-radius: 5px;
    background-color: #3a3a3a;
    text-align: center;
    color: #e0e0e0;
}
QProgressBar::chunk {
    background-color: #34a853; /* Google Green */
    border-radius: 5px;
}
QTextEdit {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border: 1px solid #4a4a4a;
    border-radius: 5px;
    padding: 5px;
}
QCheckBox {
    color: #e0e0e0;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #4a4a4a;
    border-radius: 3px;
    background-color: #3a3a3a;
}
QCheckBox::indicator:checked {
    background-color: #4285f4;
    image: url(check_icon.png); /* Placeholder for a custom check icon */
}
QListWidget {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #4a4a4a;
    border-radius: 5px;
    padding: 5px;
}
QListWidget::item {
    padding: 5px;
}
QListWidget::item:selected {
    background-color: #4285f4;
    color: #ffffff;
}
QListWidget::item:hover {
    background-color: #3a3a3a;
}
QMenu {
    background-color: #2d2d2d;
    border: 1px solid #4a4a4a;
    color: #e0e0e0;
}
QMenu::item {
    padding: 5px 20px 5px 10px;
}
QMenu::item:selected {
    background-color: #4285f4;
    color: #ffffff;
}
QMenu::separator {
    height: 1px;
    background: #4a4a4a;
    margin: 5px 0;
}
QSplitter::handle {
    background-color: #4a4a4a;
    width: 2px;
    height: 2px;
}
QSplitter::handle:hover {
    background-color: #4285f4;
}
/* Scrollbar styling */
QScrollBar:vertical, QScrollBar:horizontal {
    border: 1px solid #4a4a4a;
    background: #3a3a3a;
    width: 12px;
    margin: 0px 0px 0px 0px;
    border-radius: 6px;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #5a5a5a;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: #6a6a6a;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
"""

# --- WebEngine Configuration ---
def setup_webengine_settings():
    """
    Configures QtWebEngine with enhanced media and security support.
    Sets environment variables for Chromium flags and scaling.
    """
    try:
        # Enhanced video codec and GPU acceleration flags
        video_flags = [
            '--enable-features=VaapiVideoDecoder,VaapiVideoEncoder',
            '--use-gl=egl',
            '--enable-accelerated-video-decode',
            '--enable-accelerated-video-encode',
            '--enable-gpu-rasterization',
            '--enable-zero-copy',
            '--ignore-gpu-blacklist',
            '--enable-hardware-overlays',
            '--enable-drdc',
            '--enable-unsafe-webgpu',
            '--disable-web-security',  # WARNING: Disables CORS for local files. Use with caution.
            '--disable-features=TranslateUI',
            '--enable-smooth-scrolling'
        ]
        os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = ' '.join(video_flags)

        # Performance and memory optimizations
        if not os.environ.get('QT_AUTO_SCREEN_SCALE_FACTOR'):
            os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
        # Remote debugging port. If this port is already in use, you'll see a "bind() returned an error" message.
        # You might need to change this port (e.g., '9223') or ensure no other instance is running.
        os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '9222'

        print("🎬 Enhanced WebEngine configuration loaded.")
    except Exception as e:
        print(f"⚠️ WebEngine configuration error: {e}")

setup_webengine_settings()

# --- Proxy Management ---
class ProxyManager:
    """Manages TOR proxy detection and configuration."""
    def __init__(self):
        self.tor_enabled = False
        self.tor_port = None

    def is_tor_running(self) -> bool:
        """
        Checks if a TOR instance is running on standard ports.
        Returns True if TOR is detected, False otherwise.
        """
        for port in DEFAULT_TOR_PORTS:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1) as s:
                    self.tor_port = port
                    self.tor_enabled = True
                    return True
            except (socket.timeout, ConnectionRefusedError):
                continue
        self.tor_enabled = False
        return False

    def get_proxy_config(self) -> dict:
        """
        Returns the current proxy configuration.
        If TOR is running, returns SOCKS5 proxy details; otherwise, returns direct connection.
        """
        if self.is_tor_running():
            return {"type": "socks5", "host": "127.0.0.1", "port": self.tor_port}
        return {"type": "direct"}

# --- History and Bookmark Management ---
class HistoryManager:
    """Manages browsing history and bookmarks using SQLite and JSON."""
    def __init__(self):
        os.makedirs(BROWSER_DATA_DIR, exist_ok=True)
        self.db_path = os.path.join(BROWSER_DATA_DIR, HISTORY_DB_NAME)
        self.bookmarks_path = os.path.join(BROWSER_DATA_DIR, BOOKMARKS_FILE_NAME)
        self.init_database()
        self.shortcuts = self._get_default_shortcuts()
        self.bookmarks = self.load_bookmarks()

    def init_database(self):
        """Initializes the SQLite database for history storage."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT NOT NULL UNIQUE,
                        title TEXT,
                        visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        visit_count INTEGER DEFAULT 1,
                        favicon TEXT,
                        domain TEXT
                    )
                ''')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_visit_time ON history(visit_time DESC)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_domain ON history(domain)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_url_title ON history(url, title)')
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
            QMessageBox.critical(None, "Database Error", f"Failed to initialize history database: {e}")

    def _get_default_shortcuts(self) -> list:
        """Returns a list of predefined shortcuts for quick access."""
        return [
            {"name": "Proton Mail", "url": "https://mail.proton.me", "icon": "📧", "category": "Email"},
            {"name": "YouTube", "url": "https://youtube.com", "icon": "📺", "category": "Media"},
            {"name": "GitHub", "url": "https://github.com", "icon": "🐙", "category": "Dev"},
            {"name": "Netflix", "url": "https://netflix.com", "icon": "🎬", "category": "Media"},
            {"name": "Reddit", "url": "https://reddit.com", "icon": "🤖", "category": "Social"},
            {"name": "Twitter/X", "url": "https://x.com", "icon": "🐦", "category": "Social"},
            {"name": "LinkedIn", "url": "https://linkedin.com", "icon": "💼", "category": "Professional"},
            {"name": "Amazon", "url": "https://amazon.com", "icon": "📦", "category": "Shopping"},
            {"name": "Wikipedia", "url": "https://wikipedia.org", "icon": "📖", "category": "Reference"},
            {"name": "DuckDuckGo", "url": "https://duckduckgo.com", "icon": "🦆", "category": "Search"}
        ]

    def add_visit(self, url: str, title: str):
        """
        Adds or updates a browsing visit in the history database.
        Increments visit count if URL already exists.
        """
        if not url or url.startswith(('data:', 'about:', 'chrome:', 'devtools:', 'null:')):
            return

        try:
            domain = urlparse(url).netloc.lower()
            favicon = self.get_favicon_for_domain(domain)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO history (url, title, domain, favicon, visit_count)
                    VALUES (?, ?, ?, ?, 1)
                    ON CONFLICT(url) DO UPDATE SET
                        title = ?,
                        visit_time = CURRENT_TIMESTAMP,
                        visit_count = visit_count + 1
                ''', (url, title, domain, favicon, title))
        except sqlite3.Error as e:
            print(f"History add error: {e}")

    def get_recent_sites(self, limit: int = 15) -> list:
        """Retrieves a list of recently visited sites from the history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT url, title, visit_time, favicon, domain, visit_count
                    FROM history
                    ORDER BY visit_time DESC
                    LIMIT ?
                ''', (limit,))
                return [{
                    'url': row[0],
                    'title': row[1] or urlparse(row[0]).netloc,
                    'visitTime': row[2],
                    'favicon': row[3],
                    'domain': row[4],
                    'visitCount': row[5]
                } for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Recent sites error: {e}")
            return []

    def get_most_visited(self, limit: int = 10) -> list:
        """Retrieves a list of most frequently visited sites."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT url, title, visit_count, favicon, domain
                    FROM history
                    WHERE visit_count > 1
                    ORDER BY visit_count DESC, visit_time DESC
                    LIMIT ?
                ''', (limit,))
                return [{
                    'url': row[0],
                    'title': row[1] or urlparse(row[0]).netloc,
                    'visitCount': row[2],
                    'favicon': row[3],
                    'domain': row[4]
                } for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Most visited error: {e}")
            return []

    def search_history(self, query: str, limit: int = 20) -> list:
        """Searches the browsing history by title, URL, or domain."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT url, title, visit_time, favicon, domain
                    FROM history
                    WHERE title LIKE ? OR url LIKE ? OR domain LIKE ?
                    ORDER BY visit_count DESC, visit_time DESC
                    LIMIT ?
                ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
                return [{
                    'url': row[0],
                    'title': row[1] or urlparse(row[0]).netloc,
                    'visitTime': row[2],
                    'favicon': row[3],
                    'domain': row[4]
                } for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Search history error: {e}")
            return []

    def clear_history(self, days: int = None):
        """
        Clears browsing history.
        If 'days' is specified, clears history older than that many days.
        Otherwise, clears all history.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                if days is not None:
                    cutoff_date = datetime.now() - timedelta(days=days)
                    conn.execute('DELETE FROM history WHERE visit_time < ?', (cutoff_date.isoformat(),))
                else:
                    conn.execute('DELETE FROM history')
        except sqlite3.Error as e:
            print(f"Clear history error: {e}")

    def delete_history_entry(self, url: str):
        """Deletes a specific history entry by URL."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM history WHERE url = ?', (url,))
        except sqlite3.Error as e:
            print(f"Delete history entry error: {e}")

    def load_bookmarks(self) -> list:
        """Loads bookmarks from the JSON file."""
        try:
            if os.path.exists(self.bookmarks_path):
                with open(self.bookmarks_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Bookmarks load error: {e}")
        return []

    def save_bookmarks(self):
        """Saves current bookmarks to the JSON file."""
        try:
            os.makedirs(os.path.dirname(self.bookmarks_path), exist_ok=True)
            with open(self.bookmarks_path, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Bookmarks save error: {e}")

    def add_bookmark(self, url: str, title: str, folder: str = "General"):
        """Adds a new bookmark."""
        # Check if bookmark already exists to prevent duplicates
        for bookmark in self.bookmarks:
            if bookmark['url'] == url:
                QMessageBox.information(None, "Bookmark Exists", "This page is already bookmarked.")
                return

        bookmark = {
            'url': url,
            'title': title,
            'folder': folder,
            'added_time': datetime.now().isoformat(),
            'favicon': self.get_favicon_for_domain(urlparse(url).netloc)
        }
        self.bookmarks.append(bookmark)
        self.save_bookmarks()

    def remove_bookmark(self, url: str):
        """Removes a bookmark by its URL."""
        initial_count = len(self.bookmarks)
        self.bookmarks = [b for b in self.bookmarks if b['url'] != url]
        if len(self.bookmarks) < initial_count:
            self.save_bookmarks()
            return True
        return False

    def get_favicon_for_domain(self, domain: str) -> str:
        """
        Returns a suitable emoji favicon for a given domain.
        Prioritizes specific domain mappings, then TLD mappings.
        """
        favicon_map = {
            'github.com': '🐙', 'gitlab.com': '🦊', 'stackoverflow.com': '📚',
            'developer.mozilla.org': '🦎', 'docs.python.org': '🐍', 'pypi.org': '🐍',
            'youtube.com': '📺', 'youtu.be': '📺', 'netflix.com': '🎬', 'twitch.tv': '🎮',
            'vimeo.com': '📹', 'tiktok.com': '🎵', 'spotify.com': '🎵', 'soundcloud.com': '🎵',
            'reddit.com': '🤖', 'twitter.com': '🐦', 'x.com': '🐦', 'facebook.com': '📘',
            'instagram.com': '📷', 'linkedin.com': '💼', 'discord.com': '💬',
            'gmail.com': '📧', 'mail.proton.me': '🛡️', 'outlook.com': '📧',
            'google.com': '🔍', 'duckduckgo.com': '🦆', 'wikipedia.org': '📖',
            'archive.org': '📚', 'scholar.google.com': '🎓',
            'amazon.com': '📦', 'ebay.com': '🏪', 'etsy.com': '🎨',
            'bbc.com': '📰', 'cnn.com': '📰', 'reuters.com': '📰',
            'protonmail.com': '🛡️', 'signal.org': '🔒', 'torproject.org': '🧅'
        }

        for key, icon in favicon_map.items():
            if key in domain.lower():
                return icon

        tld_map = {
            '.edu': '🎓', '.gov': '🏛️', '.org': '🌐', '.mil': '⚔️',
            '.news': '📰', '.blog': '📝', '.shop': '🛍️'
        }
        for tld, icon in tld_map.items():
            if domain.endswith(tld):
                return icon

        return '🌐'

# --- Video Downloader ---
class EnhancedVideoDownloader(QThread):
    """
    A QThread-based video downloader using yt-dlp, with progress and status signals.
    """
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    download_finished = pyqtSignal(bool, str)
    speed_updated = pyqtSignal(str)

    def __init__(self, url: str, format_id: str = None, audio_only: bool = False, quality: str = 'best'):
        super().__init__()
        self.url = url
        self.format_id = format_id
        self.audio_only = audio_only
        self.quality = quality
        self.should_stop = False
        self.download_folder = os.path.join(os.path.expanduser("~"), "Downloads", DEFAULT_DOWNLOAD_FOLDER_NAME)
        os.makedirs(self.download_folder, exist_ok=True)
        self.process = None # Store subprocess object

    def stop(self):
        """Sets a flag to stop the download process and terminates the subprocess."""
        self.should_stop = True
        if self.process and self.process.poll() is None: # If process is still running
            self.process.terminate()
            self.process.wait(timeout=1) # Give it a moment to terminate
            if self.process.poll() is None: # If still not terminated
                self.process.kill()
        print("Download stop requested.")

    def run(self):
        """Executes the yt-dlp command and parses its output."""
        try:
            if not self._check_yt_dlp():
                self.download_finished.emit(False, "yt-dlp not found. Please install it (e.g., 'pip install yt-dlp').")
                return

            self.status_updated.emit("Preparing download...")
            cmd = ['yt-dlp', '--newline']

            if self.audio_only:
                cmd.extend(['-f', 'bestaudio', '--extract-audio', '--audio-format', 'mp3', '--audio-quality', '0'])
                self.status_updated.emit("Downloading audio (MP3)...")
            elif self.format_id:
                cmd.extend(['-f', self.format_id])
            else:
                quality_formats = {
                    'best': 'best[ext=mp4]/best[ext=webm]/best',
                    '1080p': 'best[height<=1080][ext=mp4]/best[height<=1080]',
                    '720p': 'best[height<=720][ext=mp4]/best[height<=720]',
                    '480p': 'best[height<=480][ext=mp4]/best[height<=480]'
                }
                cmd.extend(['-f', quality_formats.get(self.quality, quality_formats['best'])])

            output_template = os.path.join(self.download_folder, '%(uploader)s - %(title)s.%(ext)s')
            cmd.extend([
                '-o', output_template,
                '--no-playlist',
                '--write-description',
                '--write-info-json',
                '--write-thumbnail',
                '--embed-subs',
                '--write-auto-sub',
                '--sub-lang', 'en,es,fr,de',
                '--merge-output-format', 'mp4',
                '--no-check-certificate', # Use with caution, disables SSL certificate validation
                self.url
            ])

            self.status_updated.emit("Starting download process...")
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, universal_newlines=True, bufsize=1
            )

            for line in iter(self.process.stdout.readline, ''):
                if self.should_stop:
                    break # Exit loop if stop requested
                self._parse_progress_line(line.strip())

            return_code = self.process.wait()

            if self.should_stop:
                self.download_finished.emit(False, "Download cancelled by user.")
            elif return_code == 0:
                self.download_finished.emit(True, f"Downloaded to: {self.download_folder}")
            else:
                self.download_finished.emit(False, f"Download failed (yt-dlp exited with code: {return_code}).")

        except Exception as e:
            self.download_finished.emit(False, f"Error during download: {str(e)}")
        finally:
            if self.process:
                self.process.stdout.close()
                self.process = None # Clear reference

    def _parse_progress_line(self, line: str):
        """Parses a line from yt-dlp output to extract progress and speed."""
        self.status_updated.emit(line)

        if '[download]' in line:
            # Extract percentage
            if '%' in line:
                try:
                    percent_str = next((p for p in line.split() if '%' in p and p.replace('%', '').replace('.', '').isdigit()), None)
                    if percent_str:
                        self.progress_updated.emit(int(float(percent_str.replace('%', ''))))
                except ValueError:
                    pass

            # Extract speed
            if '/s' in line:
                try:
                    speed_part = next((p for p in line.split() if '/s' in p and any(c.isdigit() for c in p)), None)
                    if speed_part:
                        self.speed_updated.emit(speed_part)
                except:
                    pass

    def _check_yt_dlp(self) -> bool:
        """Checks if yt-dlp executable is available in the system's PATH."""
        try:
            # Use shell=True on Windows for better command finding, but generally avoid for security
            # For cross-platform, it's better to rely on PATH or provide full path
            subprocess.run(['yt-dlp', '--version'], capture_output=True, timeout=5, check=True,
                           shell=(sys.platform == "win32"))
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            print(f"yt-dlp check failed: {e}")
            return False

# --- Dialogs ---
class EnhancedVideoDownloadDialog(QDialog):
    """Dialog for configuring and monitoring video downloads."""
    def __init__(self, parent: QWidget, url: str):
        super().__init__(parent)
        self.url = url
        self.download_worker = None
        self.setWindowTitle("🎥 Enhanced Video Downloader")
        self.setModal(True)
        self.resize(600, 500)
        self._setup_ui()

    def _setup_ui(self):
        """Sets up the user interface for the download dialog."""
        layout = QVBoxLayout(self)

        # URL section
        url_group = QGroupBox("Source URL")
        url_layout = QVBoxLayout(url_group)
        url_label = QLabel(self.url)
        url_label.setWordWrap(True)
        url_label.setStyleSheet("padding: 10px; background: #3a3a3a; border-radius: 5px; color: #e0e0e0;")
        url_layout.addWidget(url_label)
        layout.addWidget(url_group)

        # Options section
        options_group = QGroupBox("Download Options")
        options_layout = QVBoxLayout(options_group)

        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(['best', '1080p', '720p', '480p'])
        quality_layout.addWidget(self.quality_combo)
        options_layout.addLayout(quality_layout)

        self.audio_only_checkbox = QCheckBox("Download audio only (MP3)")
        options_layout.addWidget(self.audio_only_checkbox)
        layout.addWidget(options_group)

        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        info_layout = QHBoxLayout()
        self.speed_label = QLabel("Speed: --")
        self.status_label = QLabel("Ready to download")
        info_layout.addWidget(self.speed_label)
        info_layout.addStretch()
        info_layout.addWidget(self.status_label)
        progress_layout.addLayout(info_layout)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(150)
        progress_layout.addWidget(self.log_area)
        layout.addWidget(progress_group)

        # Buttons
        button_layout = QHBoxLayout()
        self.download_btn = QPushButton("📥 Start Download")
        self.download_btn.clicked.connect(self._start_download)

        self.cancel_btn = QPushButton("⏹️ Cancel")
        self.cancel_btn.clicked.connect(self._cancel_download)
        self.cancel_btn.setEnabled(False)

        self.clear_log_btn = QPushButton("🧹 Clear Log")
        self.clear_log_btn.clicked.connect(self.log_area.clear)

        self.close_btn = QPushButton("❌ Close")
        self.close_btn.clicked.connect(self.close)

        button_layout.addWidget(self.download_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.clear_log_btn)
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)

    def _log_message(self, message: str):
        """Appends a timestamped message to the log area."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def _start_download(self):
        """Initiates the video download process."""
        quality = self.quality_combo.currentText()
        audio_only = self.audio_only_checkbox.isChecked()

        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_area.clear()
        self.status_label.setText("Downloading...")
        self.speed_label.setText("Speed: --")

        self.download_worker = EnhancedVideoDownloader(
            self.url, quality=quality, audio_only=audio_only
        )
        self.download_worker.progress_updated.connect(self.progress_bar.setValue)
        self.download_worker.status_updated.connect(self._log_message)
        self.download_worker.speed_updated.connect(lambda s: self.speed_label.setText(f"Speed: {s}"))
        self.download_worker.download_finished.connect(self._download_finished)
        self.download_worker.start()
        self._log_message("Download started...")

    def _cancel_download(self):
        """Cancels the ongoing download."""
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.stop()
            self.cancel_btn.setEnabled(False)
            self._log_message("Cancelling download...")
            self.status_label.setText("Download cancelled.")
            self.progress_bar.setValue(0) # Reset progress bar on cancel

    def _download_finished(self, success: bool, message: str):
        """Handles the completion of a download."""
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.speed_label.setText("Speed: --")

        if success:
            self.status_label.setText("✅ Download completed!")
            self._log_message(f"✅ {message}")
            self._open_download_folder()
        else:
            self.status_label.setText("❌ Download failed")
            self._log_message(f"❌ {message}")
            self.progress_bar.setValue(0) # Reset progress bar on failure

    def _open_download_folder(self):
        """Opens the download folder in the system's file explorer."""
        try:
            download_folder = os.path.join(os.path.expanduser("~"), "Downloads", DEFAULT_DOWNLOAD_FOLDER_NAME)
            if os.name == 'nt':  # Windows
                os.startfile(download_folder)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', download_folder])
            else:  # Linux
                subprocess.run(['xdg-open', download_folder])
        except Exception as e:
            self._log_message(f"Could not open download folder: {e}")
            QMessageBox.warning(self, "Error", f"Could not open download folder: {e}")

class HistoryDialog(QDialog):
    """Dialog for viewing and managing browsing history."""
    def __init__(self, parent: QWidget, history_manager: HistoryManager):
        super().__init__(parent)
        self.history_manager = history_manager
        self.setWindowTitle("📜 Browser History")
        self.setModal(True)
        self.resize(800, 600)
        self._setup_ui()
        self._load_history()

    def _setup_ui(self):
        """Sets up the user interface for the history dialog."""
        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search history...")
        self.search_input.textChanged.connect(self._search_history)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self._open_history_item)
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.history_list)

        button_layout = QHBoxLayout()
        clear_btn = QPushButton("🗑️ Clear All")
        clear_btn.clicked.connect(self._clear_all_history)
        button_layout.addWidget(clear_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

    def _load_history(self):
        """Loads recent history items into the list widget."""
        self.history_list.clear()
        recent_sites = self.history_manager.get_recent_sites(200) # Increased limit for history view

        for site in recent_sites:
            item_text = f"{site['favicon']} {site['title']} - {site['url']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, site['url']) # Store URL
            item.setData(Qt.UserRole + 1, site['title']) # Store title
            self.history_list.addItem(item)

    def _search_history(self, query: str):
        """Performs a search on the history and updates the list."""
        self.history_list.clear()
        results = self.history_manager.search_history(query, 100) if query else self.history_manager.get_recent_sites(200)

        for site in results:
            item_text = f"{site['favicon']} {site['title']} - {site['url']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, site['url'])
            item.setData(Qt.UserRole + 1, site['title'])
            self.history_list.addItem(item)

    def _open_history_item(self, item: QListWidgetItem):
        """Opens the selected history item in a new tab."""
        url = item.data(Qt.UserRole)
        if url and isinstance(self.parent(), QMainWindow): # Check if parent is QMainWindow
            self.parent().add_new_tab(url)
            self.close()

    def _show_context_menu(self, pos):
        """Displays a context menu for history list items."""
        item = self.history_list.itemAt(pos)
        if item:
            menu = QMenu(self)
            open_action = menu.addAction("Open in New Tab")
            delete_action = menu.addAction("Delete Entry")

            action = menu.exec_(self.history_list.mapToGlobal(pos))

            if action == open_action:
                self._open_history_item(item)
            elif action == delete_action:
                self._delete_history_entry(item)

    def _delete_history_entry(self, item: QListWidgetItem):
        """Deletes a selected history entry."""
        url_to_delete = item.data(Qt.UserRole)
        title_to_delete = item.data(Qt.UserRole + 1)

        reply = QMessageBox.question(self, "Delete History Entry",
                                   f"Are you sure you want to delete '{title_to_delete}' from history?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.history_manager.delete_history_entry(url_to_delete)
            self._load_history() # Reload history after deletion
            if isinstance(self.parent(), QMainWindow):
                self.parent().refresh_sidebar() # Refresh sidebar as well

    def _clear_all_history(self):
        """Prompts for confirmation and clears all browsing history."""
        reply = QMessageBox.question(self, "Clear History",
                                   "Are you sure you want to clear ALL browsing history? This cannot be undone.",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.history_manager.clear_history()
            self._load_history()
            QMessageBox.information(self, "History Cleared", "All browsing history has been cleared.")
            if isinstance(self.parent(), QMainWindow):
                self.parent().refresh_sidebar() # Refresh sidebar after clearing history

class ClearDataDialog(QDialog):
    """Dialog for clearing various types of browsing data."""
    def __init__(self, parent: QWidget, history_manager: HistoryManager):
        super().__init__(parent)
        self.history_manager = history_manager
        self.setWindowTitle("🗑️ Clear Browsing Data")
        self.setModal(True)
        self.resize(400, 350)
        self._setup_ui()

    def _setup_ui(self):
        """Sets up the user interface for the clear data dialog."""
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Select data to clear:"))

        self.history_cb = QCheckBox("Browsing History")
        self.history_cb.setChecked(True)
        layout.addWidget(self.history_cb)

        self.bookmarks_cb = QCheckBox("Bookmarks")
        layout.addWidget(self.bookmarks_cb)

        self.cache_cb = QCheckBox("Cached images and files")
        layout.addWidget(self.cache_cb)

        self.cookies_cb = QCheckBox("Cookies and site data")
        layout.addWidget(self.cookies_cb)

        layout.addWidget(QLabel("Time range:"))
        self.time_combo = QComboBox()
        self.time_combo.addItems(["All time", "Last hour", "Last 24 hours", "Last 7 days", "Last 30 days"])
        layout.addWidget(self.time_combo)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._clear_data)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _clear_data(self):
        """Clears selected browsing data based on user choices."""
        parent_browser = self.parent()
        if not isinstance(parent_browser, QMainWindow):
            QMessageBox.critical(self, "Error", "Parent browser instance not found.")
            self.reject()
            return

        # Determine cutoff time for history
        days_to_clear = None
        time_range = self.time_combo.currentText()
        if time_range == "Last hour":
            # For history, this would require more granular timestamp filtering
            # For now, we'll treat it as "last 24 hours" or skip if not supported by HistoryManager
            days_to_clear = 1 # Treat as last 24 hours for simplicity
        elif time_range == "Last 24 hours":
            days_to_clear = 1
        elif time_range == "Last 7 days":
            days_to_clear = 7
        elif time_range == "Last 30 days":
            days_to_clear = 30
        # "All time" means days_to_clear remains None

        cleared_items = []

        if self.history_cb.isChecked():
            self.history_manager.clear_history(days_to_clear)
            cleared_items.append("Browsing History")

        if self.bookmarks_cb.isChecked():
            reply = QMessageBox.question(self, "Clear Bookmarks",
                                       "Are you sure you want to clear ALL bookmarks? This cannot be undone.",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.history_manager.bookmarks.clear()
                self.history_manager.save_bookmarks()
                cleared_items.append("Bookmarks")
            else:
                # If user cancels bookmark clear, don't proceed with other clears
                QMessageBox.information(self, "Cancelled", "Operation cancelled.")
                self.reject()
                return

        # Clear cache and cookies (requires QWebEngineProfile access)
        profile = parent_browser.profile # Access the profile from the main browser
        if self.cache_cb.isChecked():
            profile.clearHttpCache()
            cleared_items.append("Cached images and files")

        if self.cookies_cb.isChecked():
            # QWebEngineProfile.cookieStore() provides access to cookies
            # Clearing all cookies might be done via cookieStore().deleteAllCookies()
            profile.cookieStore().deleteAllCookies()
            cleared_items.append("Cookies and site data")

        if cleared_items:
            QMessageBox.information(self, "Cleared", f"Successfully cleared: {', '.join(cleared_items)}.")
            self.accept()
        else:
            QMessageBox.information(self, "No Selection", "No data selected to clear.")
            self.reject()

class SettingsDialog(QDialog):
    """Dialog for managing browser settings."""
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.parent_browser = parent
        self.setWindowTitle("⚙️ Browser Settings")
        self.setModal(True)
        self.resize(500, 450)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Sets up the user interface for the settings dialog."""
        layout = QVBoxLayout(self)

        # General settings
        general_group = QGroupBox("General")
        general_layout = QVBoxLayout(general_group)

        homepage_layout = QHBoxLayout()
        homepage_layout.addWidget(QLabel("Homepage:"))
        self.homepage_input = QLineEdit("Enhanced Start Page")
        self.homepage_input.setReadOnly(True) # Homepage is fixed for now
        homepage_layout.addWidget(self.homepage_input)
        general_layout.addLayout(homepage_layout)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Default Search:"))
        self.search_combo = QComboBox()
        self.search_combo.addItems(["DuckDuckGo", "Google", "Bing", "StartPage"])
        search_layout.addWidget(self.search_combo)
        general_layout.addLayout(search_layout)
        layout.addWidget(general_group)

        # Privacy settings
        privacy_group = QGroupBox("Privacy")
        privacy_layout = QVBoxLayout(privacy_group)

        self.tor_cb = QCheckBox("Use TOR proxy (if available)")
        privacy_layout.addWidget(self.tor_cb)

        self.javascript_cb = QCheckBox("Enable JavaScript")
        privacy_layout.addWidget(self.javascript_cb)
        layout.addWidget(privacy_group)

        # Download settings
        download_group = QGroupBox("Downloads")
        download_layout = QVBoxLayout(download_group)

        download_path_layout = QHBoxLayout()
        download_path_layout.addWidget(QLabel("Download Folder:"))
        self.download_path_label = QLabel(os.path.join(os.path.expanduser("~"), "Downloads", DEFAULT_DOWNLOAD_FOLDER_NAME))
        download_path_layout.addWidget(self.download_path_label)
        download_layout.addLayout(download_path_layout)
        layout.addWidget(download_group)

        # Maintenance
        maintenance_group = QGroupBox("Maintenance")
        maintenance_layout = QVBoxLayout(maintenance_group)
        self.clear_cache_btn = QPushButton("Clear Browser Cache")
        self.clear_cache_btn.clicked.connect(self._clear_browser_cache)
        maintenance_layout.addWidget(self.clear_cache_btn)
        layout.addWidget(maintenance_group)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults)
        button_box.accepted.connect(self._save_settings)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self._reset_to_defaults)
        layout.addWidget(button_box)

    def _load_settings(self):
        """Loads settings into the dialog fields."""
        if isinstance(self.parent_browser, EnhancedNullBrowser):
            # Load TOR status
            self.tor_cb.setChecked(self.parent_browser.proxy_manager.tor_enabled)
            # Load JavaScript status (from QWebEngineSettings, if implemented)
            # For now, assume it's always enabled as per EnhancedWebPage
            # To make this truly functional, you'd need to get the current JS setting from the profile
            # For example: self.javascript_cb.setChecked(self.parent_browser.profile.settings().testAttribute(QWebEngineSettings.JavascriptEnabled))
            self.javascript_cb.setChecked(True) # Placeholder

            # Load default search engine (if saved)
            saved_search_engine = self.parent_browser.app_settings.value("default_search_engine", "DuckDuckGo")
            self.search_combo.setCurrentText(saved_search_engine)

    def _save_settings(self):
        """Saves settings from the dialog fields."""
        if isinstance(self.parent_browser, EnhancedNullBrowser):
            # Save default search engine
            self.parent_browser.app_settings.setValue("default_search_engine", self.search_combo.currentText())

            # Apply JavaScript setting
            # This requires getting the current page's settings and updating them.
            # For simplicity, we'll apply it to the profile's default settings.
            # Note: Existing pages might not update immediately.
            self.parent_browser.profile.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, self.javascript_cb.isChecked())
            print(f"JavaScript enabled: {self.javascript_cb.isChecked()}")

            # TOR setting is read-only based on detection, not user-settable here.
            # If it were user-settable, it would involve restarting the browser or profile.

        QMessageBox.information(self, "Settings", "Settings saved successfully! (Some settings require browser restart or are placeholders.)")
        self.accept()

    def _reset_to_defaults(self):
        """Resets settings to their default values."""
        reply = QMessageBox.question(self, "Reset Settings",
                                   "Are you sure you want to reset all settings to their default values?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.search_combo.setCurrentText("DuckDuckGo")
            self.tor_cb.setChecked(False) # Default to no TOR
            self.javascript_cb.setChecked(True) # Default to JS enabled
            QMessageBox.information(self, "Settings Reset", "Settings have been reset to defaults.")
            # In a real app, you'd also clear QSettings values here.
            if isinstance(self.parent_browser, EnhancedNullBrowser):
                self.parent_browser.app_settings.clear() # Clear all saved settings

    def _clear_browser_cache(self):
        """Clears the browser's HTTP cache."""
        if isinstance(self.parent_browser, EnhancedNullBrowser):
            reply = QMessageBox.question(self, "Clear Cache",
                                       "Are you sure you want to clear the browser's HTTP cache?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.parent_browser.profile.clearHttpCache()
                QMessageBox.information(self, "Cache Cleared", "Browser cache has been cleared.")
        else:
            QMessageBox.critical(self, "Error", "Could not access browser profile to clear cache.")

# --- WebEngine Page ---
class EnhancedWebPage(QWebEnginePage):
    """Custom QWebEnginePage with enhanced settings and custom URL handling."""
    def __init__(self, profile: QWebEngineProfile, browser_instance: 'EnhancedNullBrowser'):
        super().__init__(profile)
        self.browser_instance = browser_instance
        self._setup_enhanced_settings()
        self.featurePermissionRequested.connect(self._handle_feature_permission)
        # The javaScriptConsoleMessage method is overridden directly below, no .connect() needed.

    def _setup_enhanced_settings(self):
        """Configures enhanced web page settings."""
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        # JavaScriptEnabled will be controlled by the SettingsDialog
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True) # Default to True
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False) # Corrected attribute name
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, False)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, False)
        settings.setAttribute(QWebEngineSettings.HyperlinkAuditingEnabled, False)
        settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)


    def acceptNavigationRequest(self, url: QUrl, navigation_type: QWebEnginePage.NavigationType, is_main_frame: bool) -> bool:
        """
        Intercepts navigation requests to handle custom protocols.
        Returns False if the navigation is handled internally, True otherwise.
        """
        url_str = url.toString()
        print(f"Attempting to navigate to: {url_str}")  # Log the URL being navigated to

        if url_str.startswith('null://'):
            self._handle_custom_url(url_str)
            return False # Navigation handled
        return super().acceptNavigationRequest(url, navigation_type, is_main_frame)

    def _handle_custom_url(self, url: str):
        """Dispatches custom 'null://' URLs to appropriate browser actions."""
        if url == 'null://clear-history':
            self.browser_instance.clear_browsing_data()
        elif url == 'null://settings':
            self.browser_instance.show_settings()
        elif url == 'null://downloads':
            self.browser_instance.show_downloads()
        else:
            print(f"Unhandled custom URL: {url}")
            QMessageBox.warning(self.browser_instance, "Custom URL Error", f"Unknown custom URL: {url}")

    def createWindow(self, type: QWebEnginePage.WebWindowType):
        """Handles requests to open new windows/tabs."""
        if type == QWebEnginePage.WebBrowserTab:
            return self.browser_instance.add_new_tab().page()
        elif type == QWebEnginePage.WebBrowserWindow:
            # For new windows, you might create a new QMainWindow instance
            new_browser_window = EnhancedNullBrowser()
            new_browser_window.show()
            return new_browser_window.tabs.currentWidget().page()
        return super().createWindow(type)

    def setHtml(self, html: str, baseUrl: QUrl = QUrl()):
        """Overrides setHtml to inject dark mode stylesheet for local content."""
        # Inject custom CSS for scrollbars and general dark mode consistency
        injected_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                /* Apply dark theme to local HTML content */
                body {{
                    background-color: #1e1e1e !important;
                    color: #e0e0e0 !important;
                }}
                a {{ color: #4285f4 !important; }}
                /* Custom scrollbar for dark theme */
                * {{
                    scrollbar-width: thin;
                    scrollbar-color: #555 #222;
                }}
                ::-webkit-scrollbar {{ width: 12px; height: 12px; }}
                ::-webkit-scrollbar-track {{ background: #222; border-radius: 6px; }}
                ::-webkit-scrollbar-thumb {{ background: #555; border-radius: 6px; }}
                ::-webkit-scrollbar-thumb:hover {{ background: #666; }}
            </style>
        </head>
        <body>
        {html}
        </body>
        </html>
        """
        super().setHtml(injected_html, baseUrl)

    def _handle_feature_permission(self, securityOrigin: QUrl, feature: QWebEnginePage.Feature):
        """Handles requests for web features like geolocation, camera, microphone."""
        # For simplicity, auto-grant all permissions. In a real browser, prompt the user.
        self.setFeaturePermission(securityOrigin, feature, QWebEnginePage.PermissionGrantedByUser)
        print(f"Permission granted for {feature} on {securityOrigin.host()}")

    # CORRECT: This method is an override, not a signal connection.
    def javaScriptConsoleMessage(self, level: QWebEnginePage.JavaScriptConsoleMessageLevel,
                                   message: str, line_number: int, source_id: str):
        """Logs JavaScript console messages to the Python console."""
        level_map = {
            QWebEnginePage.InfoMessageLevel: "INFO",
            QWebEnginePage.WarningMessageLevel: "WARN",
            QWebEnginePage.ErrorMessageLevel: "ERROR"
            # DebugMessageLevel is not a standard attribute in QWebEnginePage
        }
        # Use .get() with a default value to handle cases where 'level' might not be in level_map
        level_str = level_map.get(level, f"UNKNOWN({level})")
        print(f"JS Console [{level_str}]: {message} (Line: {line_number}, Source: {source_id})")


# --- Main Browser Window ---
class EnhancedNullBrowser(QMainWindow):
    """The main browser application window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} - {APP_VERSION}")
        self.setGeometry(100, 100, 1400, 900)
        # self.setWindowIcon(QIcon(":/icons/browser_icon.png")) # Placeholder for a custom icon. Requires resource file.

        self.proxy_manager = ProxyManager()
        self.history_manager = HistoryManager()
        self.app_settings = QSettings("NullBrowser", "Enhanced")
        self.closed_tabs = []
        self.find_text_input = None # For find in page functionality

        self._setup_profile()
        self._setup_ui()
        self._setup_shortcuts()
        self._restore_settings()

        print("🚀 Enhanced Null Browser initialized.")

    def _setup_profile(self):
        """Sets up the QWebEngineProfile with cache paths and proxy configuration."""
        self.profile = QWebEngineProfile("EnhancedNullProfile", self)

        proxy_config = self.proxy_manager.get_proxy_config()
        if proxy_config["type"] == "socks5":
            print(f"🛡️ Using TOR proxy: {proxy_config['host']}:{proxy_config['port']}")
            # Note: Setting proxy via QWebEngineProfile requires a QWebEngineUrlRequestInterceptor
            # or setting environment variables before QApplication starts.
            # For simplicity, relying on QTWEBENGINE_CHROMIUM_FLAGS for now if set globally.
            # A more robust solution would involve:
            # self.profile.setHttpProxy(QWebEngineSettings.Socks5Proxy, proxy_config['host'], proxy_config['port'])
        else:
            print("🌐 Using direct connection.")

        cache_path = os.path.join(BROWSER_DATA_DIR, "cache")
        os.makedirs(cache_path, exist_ok=True)
        self.profile.setCachePath(cache_path)
        self.profile.setPersistentStoragePath(cache_path)

    def _setup_ui(self):
        """Sets up the main user interface components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Horizontal)

        self.sidebar = self._create_sidebar()
        self.sidebar.setMaximumWidth(250)
        self.sidebar.setVisible(False)
        splitter.addWidget(self.sidebar)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._update_url_bar_and_security)
        splitter.addWidget(self.tabs)

        main_layout.addWidget(splitter)

        self._setup_toolbar()
        self.statusBar().showMessage("Ready")
        self.add_new_tab() # Load initial tab

    def _create_sidebar(self) -> QFrame:
        """Creates and populates the sidebar with bookmarks and history lists."""
        sidebar = QFrame()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar.setFrameShape(QFrame.StyledPanel)
        sidebar.setFrameShadow(QFrame.Raised)
        sidebar.setStyleSheet("QFrame { border: 1px solid #4a4a4a; border-radius: 5px; }") # Dark border for sidebar

        bookmarks_label = QLabel("📚 Bookmarks")
        bookmarks_label.setStyleSheet("font-weight: bold; padding: 5px; border-bottom: 1px solid #333; color: #e0e0e0;")
        sidebar_layout.addWidget(bookmarks_label)

        self.bookmarks_list = QListWidget()
        self.bookmarks_list.itemDoubleClicked.connect(self._open_bookmark)
        # Enable custom context menu for bookmarks list
        self.bookmarks_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bookmarks_list.customContextMenuRequested.connect(self._show_bookmark_context_menu)
        sidebar_layout.addWidget(self.bookmarks_list)

        history_label = QLabel("📜 Recent History")
        history_label.setStyleSheet("font-weight: bold; padding: 5px; border-bottom: 1px solid #333; color: #e0e0e0;")
        sidebar_layout.addWidget(history_label)

        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self._open_history_item)
        sidebar_layout.addWidget(self.history_list)

        self.refresh_sidebar()
        return sidebar

    def refresh_sidebar(self):
        """Refreshes the content of the bookmarks and history lists in the sidebar."""
        self.bookmarks_list.clear()
        for bookmark in self.history_manager.bookmarks:
            item = QListWidgetItem(f"{bookmark.get('favicon', '🌐')} {bookmark['title']}")
            item.setData(Qt.UserRole, bookmark['url']) # Store URL
            item.setData(Qt.UserRole + 1, bookmark['title']) # Store Title for context menu
            self.bookmarks_list.addItem(item)

        self.history_list.clear()
        recent = self.history_manager.get_recent_sites(10)
        for site in recent:
            item = QListWidgetItem(f"{site['favicon']} {site['title']}")
            item.setData(Qt.UserRole, site['url'])
            self.history_list.addItem(item)

    def _open_bookmark(self, item: QListWidgetItem):
        """Opens the URL of the selected bookmark in the current tab."""
        url = item.data(Qt.UserRole)
        if url:
            self._load_url_in_current_tab(url)

    def _show_bookmark_context_menu(self, pos):
        """Displays a context menu for bookmark list items."""
        item = self.bookmarks_list.itemAt(pos)
        if item:
            menu = QMenu(self)
            open_action = menu.addAction("Open")
            remove_action = menu.addAction("Remove")

            action = menu.exec_(self.bookmarks_list.mapToGlobal(pos))

            if action == open_action:
                self._open_bookmark(item)
            elif action == remove_action:
                self._remove_bookmark_from_list(item)

    def _remove_bookmark_from_list(self, item: QListWidgetItem):
        """Removes the selected bookmark from the list and data."""
        url_to_remove = item.data(Qt.UserRole)
        title_to_remove = item.data(Qt.UserRole + 1)

        reply = QMessageBox.question(self, "Remove Bookmark",
                                   f"Are you sure you want to remove '{title_to_remove}' from your bookmarks?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.history_manager.remove_bookmark(url_to_remove):
                QMessageBox.information(self, "Bookmark Removed", f"'{title_to_remove}' has been removed from bookmarks.")
                self.refresh_sidebar() # Refresh the list
            else:
                QMessageBox.warning(self, "Error", "Could not remove bookmark.")


    def _open_history_item(self, item: QListWidgetItem):
        """Opens the URL of the selected history item in the current tab."""
        url = item.data(Qt.UserRole)
        if url:
            self._load_url_in_current_tab(url)

    def _setup_toolbar(self):
        """Sets up the main toolbar with navigation and feature buttons."""
        nav_bar = QToolBar("Navigation")
        nav_bar.setMovable(False)
        self.addToolBar(nav_bar)

        # Navigation buttons
        self._add_action_to_toolbar(nav_bar, "⬅️", "Back (Alt+Left)", self.go_back)
        self._add_action_to_toolbar(nav_bar, "➡️", "Forward (Alt+Right)", self.go_forward)
        self._add_action_to_toolbar(nav_bar, "🔄", "Refresh (F5)", self.refresh_page)
        self._add_action_to_toolbar(nav_bar, "🏠", "Home (Alt+Home)", self.go_home)
        nav_bar.addSeparator()

        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL or search...")
        self.url_bar.returnPressed.connect(self._load_url_from_bar)
        self.url_bar.textChanged.connect(self._on_url_text_changed) # For future suggestions
        nav_bar.addWidget(self.url_bar)

        self.security_indicator = QLabel("🌐")
        self.security_indicator.setToolTip("Connection security status")
        nav_bar.addWidget(self.security_indicator)
        nav_bar.addSeparator()

        # Feature buttons
        self._add_action_to_toolbar(nav_bar, "⭐", "Bookmark this page (Ctrl+D)", self.bookmark_page)
        self._add_action_to_toolbar(nav_bar, "📥", "Download video (Ctrl+Shift+D)", self.download_current_video)
        self._add_action_to_toolbar(nav_bar, "➕", "New Tab (Ctrl+T)", self.add_new_tab)
        nav_bar.addSeparator()

        # Utility buttons
        self._add_action_to_toolbar(nav_bar, "📋", "Toggle Sidebar (Ctrl+B)", self.toggle_sidebar)
        self._add_action_to_toolbar(nav_bar, "⚙️", "Settings", self.show_settings)
        self._add_action_to_toolbar(nav_bar, "🖥️", "Toggle Fullscreen (F11)", self.toggle_fullscreen) # Fullscreen button

    def _add_action_to_toolbar(self, toolbar: QToolBar, icon: str, tooltip: str, callback):
        """Helper to add an action to a toolbar."""
        action = QAction(icon, self)
        action.setToolTip(tooltip)
        action.triggered.connect(callback)
        toolbar.addAction(action)

    def _setup_shortcuts(self):
        """Sets up global keyboard shortcuts for common browser actions."""
        shortcuts_map = {
            "Ctrl+T": self.add_new_tab,
            "Ctrl+W": self.close_current_tab,
            "Ctrl+Shift+T": self.restore_closed_tab,
            "Ctrl+D": self.bookmark_page,
            "Ctrl+Shift+D": self.download_current_video,
            "Ctrl+B": self.toggle_sidebar,
            "Ctrl+H": self.show_history,
            "Ctrl+Shift+Delete": self.clear_browsing_data,
            "F5": self.refresh_page,
            "Ctrl+R": self.refresh_page,
            "Alt+Left": self.go_back,
            "Alt+Right": self.go_forward,
            "Alt+Home": self.go_home,
            "Ctrl+L": self.focus_url_bar,
            "Ctrl+F": self.find_in_page,
            "F11": self.toggle_fullscreen,
            "Ctrl+Shift+I": self.open_dev_tools
        }
        for shortcut_key, callback_func in shortcuts_map.items():
            QShortcut(QKeySequence(shortcut_key), self).activated.connect(callback_func)

    def _restore_settings(self):
        """Restores application settings from QSettings."""
        geometry = self.app_settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        sidebar_visible = self.app_settings.value("sidebar_visible", False, type=bool)
        self.sidebar.setVisible(sidebar_visible)

    def _save_settings(self):
        """Saves current application settings to QSettings."""
        self.app_settings.setValue("geometry", self.saveGeometry())
        self.app_settings.setValue("sidebar_visible", self.sidebar.isVisible())

    def _on_url_text_changed(self, text: str):
        """Handles URL bar text changes (placeholder for suggestions)."""
        # Future: Implement history-based or search suggestions here.
        pass

    def _update_security_indicator(self, url: str):
        """Updates the security indicator based on the current URL's scheme."""
        if url.startswith("https://"):
            self.security_indicator.setText("🔒")
            self.security_indicator.setToolTip("Secure connection (HTTPS)")
        elif url.startswith("http://"):
            self.security_indicator.setText("⚠️")
            self.security_indicator.setToolTip("Insecure connection (HTTP)")
        else:
            self.security_indicator.setText("ℹ️")
            self.security_indicator.setToolTip("Local or special page")

    def _get_enhanced_homepage_html(self) -> str:
        """Generates the HTML content for the enhanced homepage."""
        recent_sites_js = json.dumps(self.history_manager.get_recent_sites(12), ensure_ascii=False)
        most_visited_js = json.dumps(self.history_manager.get_most_visited(8), ensure_ascii=False)
        shortcuts_js = json.dumps(self.history_manager.shortcuts, ensure_ascii=False)

        # The HTML content is kept largely the same as it's already well-structured.
        # Minor adjustments for consistency with Python variable names.
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Null Browser - Enhanced</title>
            <meta charset="UTF-8">
            <style>
                /* Basic reset and body styling */
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    background: linear-gradient(135deg, #0c0c0c 0%, #1a1a1a 100%);
                    color: #e0e0e0;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
                    min-height: 100vh; overflow-x: hidden;
                    display: flex; flex-direction: column; align-items: center;
                    padding-top: 50px; /* Space for potential top bar */
                }}

                /* Main container */
                .container {{
                    max-width: 1400px;
                    width: 100%;
                    margin: 0 auto;
                    padding: 20px;
                    text-align: center;
                }}

                /* Header and Logo */
                .header {{ margin-bottom: 50px; }}
                .logo {{
                    font-size: 3.5em; font-weight: 300; margin-bottom: 10px;
                    background: linear-gradient(45deg, #4285f4, #34a853, #fbbc05, #ea4335);
                    background-size: 400% 400%;
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    animation: gradientShift 8s ease infinite;
                }}
                @keyframes gradientShift {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} 100% {{ background-position: 0% 50%; }} }}
                .tagline {{ font-size: 1.1em; color: #888; margin-bottom: 30px; }}

                /* Search Section */
                .search-section {{ margin-bottom: 60px; position: relative; }}
                .search-container {{ position: relative; max-width: 700px; margin: 0 auto; }}
                .search-input {{
                    width: 100%; padding: 20px 25px; font-size: 18px; border-radius: 50px;
                    border: 2px solid transparent; background: rgba(30, 30, 30, 0.8);
                    backdrop-filter: blur(10px); color: #e0e0e0; outline: none;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }}
                .search-input:focus {{
                    border-color: #4285f4;
                    box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.1), 0 12px 40px rgba(0, 0, 0, 0.4);
                    transform: translateY(-2px);
                }}
                .search-input::placeholder {{ color: #888; }}
                .search-engines {{ display: flex; justify-content: center; gap: 15px; margin-top: 20px; }}
                .search-engine {{
                    padding: 8px 16px; border-radius: 20px; background: rgba(40, 40, 40, 0.6);
                    border: 1px solid #333; color: #ccc; text-decoration: none; font-size: 0.9em;
                    transition: all 0.3s ease;
                }}
                .search-engine:hover {{
                    background: rgba(66, 133, 244, 0.2); border-color: #4285f4; color: #fff;
                    transform: translateY(-1px);
                }}
                .loading-indicator {{
                    position: absolute; right: 20px; top: 50%; transform: translateY(-50%);
                    color: #4285f4; font-size: 1.2em; display: none;
                }}

                /* Sections */
                .section {{ margin-bottom: 50px; text-align: left; width: 100%; }}
                .section-title {{
                    font-size: 1.6em; margin-bottom: 25px; color: #fff; font-weight: 600;
                    display: flex; align-items: center; gap: 10px;
                }}
                .section-title::after {{ content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, #333, transparent); }}

                /* Grids */
                .cards-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
                .shortcuts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 20px; max-width: 900px; margin: 0 auto; }}

                /* Cards */
                .card, .shortcut-card {{
                    background: rgba(30, 30, 30, 0.6); backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px;
                    padding: 24px; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    cursor: pointer; text-decoration: none; color: inherit;
                    display: flex; flex-direction: column; align-items: flex-start; /* Align items to start for cards */
                    position: relative; overflow: hidden;
                }}
                .shortcut-card {{ align-items: center; text-align: center; }} /* Center for shortcuts */

                .card::before, .shortcut-card::before {{
                    content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
                    background: linear-gradient(45deg, transparent, rgba(66, 133, 244, 0.1), transparent);
                    opacity: 0; transition: opacity 0.3s ease;
                }}
                .card:hover, .shortcut-card:hover {{
                    transform: translateY(-4px) scale(1.02);
                    border-color: rgba(66, 133, 244, 0.3);
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
                }}
                .card:hover::before, .shortcut-card:hover::before {{ opacity: 1; }}

                .card-favicon, .shortcut-icon {{
                    width: 48px; height: 48px; border-radius: 12px; margin-bottom: 15px;
                    background: rgba(255, 255, 255, 0.1); display: flex; align-items: center;
                    justify-content: center; font-size: 24px; position: relative; z-index: 1;
                }}
                .shortcut-icon {{ font-size: 36px; margin-bottom: 12px; }}

                .card-title, .shortcut-name {{
                    font-weight: 600; margin-bottom: 8px; color: #fff; font-size: 1.1em;
                    position: relative; z-index: 1;
                }}
                .shortcut-name {{ font-size: 0.95em; }}

                .card-url {{
                    font-size: 0.9em; color: #888; overflow: hidden; text-overflow: ellipsis;
                    white-space: nowrap; margin-bottom: 5px; position: relative; z-index: 1;
                    width: 100%; /* Ensure URL takes full width for ellipsis */
                }}

                .card-meta {{
                    font-size: 0.8em; color: #666; display: flex; justify-content: space-between;
                    align-items: center; position: relative; z-index: 1; width: 100%;
                }}
                .visit-count {{
                    background: rgba(66, 133, 244, 0.2); padding: 2px 8px; border-radius: 12px;
                    font-size: 0.75em;
                }}
                .shortcut-category {{ font-size: 0.8em; color: #666; margin-top: 5px; position: relative; z-index: 1; }}

                /* Actions */
                .actions {{
                    display: flex; justify-content: center; gap: 20px; margin-top: 30px; flex-wrap: wrap;
                }}
                .action-btn {{
                    background: rgba(66, 133, 244, 0.2); border: 1px solid rgba(66, 133, 244, 0.3);
                    color: #e0e0e0; padding: 12px 24px; border-radius: 25px; cursor: pointer;
                    font-size: 0.9em; transition: all 0.3s ease; text-decoration: none;
                    display: inline-flex; align-items: center; gap: 8px;
                }}
                .action-btn:hover {{
                    background: rgba(66, 133, 244, 0.3); border-color: #4285f4;
                    transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
                }}

                /* Empty State */
                .empty-state {{
                    text-align: center; color: #666; grid-column: 1 / -1; padding: 60px 20px;
                    font-style: italic;
                }}
                .empty-state .icon {{ font-size: 4em; margin-bottom: 20px; opacity: 0.5; }}

                /* Features Banner */
                .features-banner {{
                    background: linear-gradient(135deg, rgba(66, 133, 244, 0.1), rgba(52, 168, 83, 0.1));
                    border: 1px solid rgba(66, 133, 244, 0.2); border-radius: 16px;
                    padding: 25px; margin: 30px 0; text-align: left;
                }}
                .features-banner h3 {{ color: #4285f4; margin-bottom: 15px; font-size: 1.3em; }}
                .features-list {{
                    list-style: none; display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 10px;
                }}
                .features-list li {{ padding: 8px 0; display: flex; align-items: center; gap: 10px; }}

                /* Responsive adjustments */
                @media (max-width: 768px) {{
                    .container {{ padding: 15px; }}
                    .logo {{ font-size: 2.5em; }}
                    .cards-grid {{ grid-template-columns: 1fr; }}
                    .shortcuts-grid {{ grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); }}
                    .search-engines {{ flex-wrap: wrap; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 class="logo">🌑 Null Browser</h1>
                    <p class="tagline">Enhanced Edition - Privacy-focused browsing with advanced features</p>
                </div>

                <div class="features-banner">
                    <h3>🚀 Enhanced Features</h3>
                    <ul class="features-list">
                        <li>🎥 Advanced video downloader with multiple quality options</li>
                        <li>🔒 Enhanced privacy with TOR support</li>
                        <li>📚 Smart bookmarks and history management</li>
                        <li>⚡ Performance optimizations and smooth scrolling</li>
                        <li>🎨 Beautiful dark theme with modern design</li>
                        <li>⌨️ Comprehensive keyboard shortcuts</li>
                    </ul>
                </div>

                <div class="search-section">
                    <div class="search-container">
                        <input type="text" class="search-input" placeholder="Search the web or enter a URL..." autofocus>
                        <span class="loading-indicator">Loading...</span>
                        <div class="search-engines">
                            <a href="#" class="search-engine" data-engine="duckduckgo">🦆 DuckDuckGo</a>
                            <a href="#" class="search-engine" data-engine="google">🔍 Google</a>
                            <a href="#" class="search-engine" data-engine="bing">🅱️ Bing</a>
                            <a href="#" class="search-engine" data-engine="startpage">🔒 StartPage</a>
                        </div>
                    </div>
                </div>

                <div class="section">
                    <h2 class="section-title">🚀 Quick Access</h2>
                    <div class="shortcuts-grid" id="shortcutsGrid"></div>
                </div>

                <div class="section" id="mostVisitedSection">
                    <h2 class="section-title">⭐ Most Visited</h2>
                    <div class="cards-grid" id="mostVisitedGrid"></div>
                </div>

                <div class="section" id="recentSection">
                    <h2 class="section-title">📜 Recently Visited</h2>
                    <div class="cards-grid" id="recentGrid"></div>
                </div>

                <div class="actions">
                    <button class="action-btn" onclick="clearHistory()">
                        🗑️ Clear History
                    </button>
                    <button class="action-btn" onclick="showSettings()">
                        ⚙️ Settings
                    </button>
                    <button class="action-btn" onclick="showDownloads()">
                        📥 Downloads
                    </button>
                </div>
            </div>

            <script>
                const recentSites = {recent_sites_js};
                const mostVisited = {most_visited_js};
                const shortcuts = {shortcuts_js};
                const searchInput = document.querySelector('.search-input');
                const loadingIndicator = document.querySelector('.loading-indicator');

                function formatTimeAgo(dateString) {{
                    const date = new Date(dateString);
                    const now = new Date();
                    const diffInSeconds = Math.floor((now - date) / 1000);

                    if (diffInSeconds < 60) return 'Just now';
                    if (diffInSeconds < 3600) return `${{Math.floor(diffInSeconds / 60)}}m ago`;
                    if (diffInSeconds < 86400) return `${{Math.floor(diffInSeconds / 3600)}}h ago`;
                    if (diffInSeconds < 604800) return `${{Math.floor(diffInSeconds / 86400)}}d ago`;
                    return date.toLocaleDateString();
                }}

                function renderShortcuts() {{
                    const container = document.getElementById('shortcutsGrid');
                    container.innerHTML = '';
                    if (shortcuts.length === 0) {{
                        container.innerHTML = '<div class="empty-state"><span class="icon">✨</span><p>No shortcuts yet. Add your favorites!</p></div>';
                        return;
                    }}
                    shortcuts.forEach(shortcut => {{
                        const card = document.createElement('a');
                        card.className = 'shortcut-card';
                        card.href = shortcut.url;
                        card.innerHTML = `
                            <div class="shortcut-icon">${{shortcut.icon}}</div>
                            <div class="shortcut-name">${{shortcut.name}}</div>
                            <div class="shortcut-category">${{shortcut.category || ''}}</div>
                        `;
                        container.appendChild(card);
                    }});
                }}

                function renderMostVisited() {{
                    const container = document.getElementById('mostVisitedGrid');
                    const section = document.getElementById('mostVisitedSection');
                    if (mostVisited.length === 0) {{
                        section.style.display = 'none';
                        return;
                    }}
                    section.style.display = 'block';
                    container.innerHTML = '';
                    mostVisited.forEach(site => {{
                        const card = document.createElement('a');
                        card.className = 'card';
                        card.href = site.url;
                        card.innerHTML = `
                            <div class="card-favicon">${{site.favicon}}</div>
                            <div class="card-title">${{site.title}}</div>
                            <div class="card-url">${{site.url}}</div>
                            <div class="card-meta">
                                <span class="visit-count">${{site.visitCount}} visits</span>
                            </div>
                        `;
                        container.appendChild(card);
                    }});
                }}

                function renderRecent() {{
                    const container = document.getElementById('recentGrid');
                    const section = document.getElementById('recentSection');
                    if (recentSites.length === 0) {{
                        section.style.display = 'none';
                        return;
                    }}
                    section.style.display = 'block';
                    container.innerHTML = '';
                    recentSites.forEach(site => {{
                        const card = document.createElement('a');
                        card.className = 'card';
                        card.href = site.url;
                        card.innerHTML = `
                            <div class="card-favicon">${{site.favicon}}</div>
                            <div class="card-title">${{site.title}}</div>
                            <div class="card-url">${{site.url}}</div>
                            <div class="card-meta">
                                <span>${{formatTimeAgo(site.visitTime)}}</span>
                                ${{site.visitCount > 1 ? `<span class="visit-count">${{site.visitCount}} visits</span>` : ''}}
                            </div>
                        `;
                        container.appendChild(card);
                    }});
                }}

                function handleSearch(query, engine = 'duckduckgo') {{
                    loadingIndicator.style.display = 'inline'; // Show loading indicator
                    const engines = {{
                        'duckduckgo': 'https://duckduckgo.com/?q=',
                        'google': 'https://www.google.com/search?q=',
                        'bing': 'https://www.bing.com/search?q=',
                        'startpage': 'https://www.startpage.com/sp/search?query='
                    }};
                    if (query.includes('.') && !query.includes(' ')) {{
                        const url = query.startsWith('http') ? query : `https://${{query}}`;
                        window.location.href = url;
                    }} else {{
                        const searchUrl = engines[engine] + encodeURIComponent(query);
                        window.location.href = searchUrl;
                    }}
                }}

                function clearHistory() {{ window.location.href = 'null://clear-history'; }}
                function showSettings() {{ window.location.href = 'null://settings'; }}
                function showDownloads() {{ window.location.href = 'null://downloads'; }}

                searchInput.addEventListener('keypress', (e) => {{
                    if (e.key === 'Enter') {{ handleSearch(e.target.value); }}
                }});
                document.querySelectorAll('.search-engine').forEach(engine => {{
                    engine.addEventListener('click', (e) => {{
                        e.preventDefault();
                        const query = searchInput.value;
                        if (query) {{ handleSearch(query, e.target.dataset.engine); }}
                    }});
                }});

                // Hide loading indicator if page loads without search
                window.addEventListener('load', () => {{
                    loadingIndicator.style.display = 'none';
                }});

                renderShortcuts();
                renderMostVisited();
                renderRecent();
            </script>
        </body>
        </html>
        """

    # --- Navigation Methods ---
    def go_back(self):
        """Navigates back in the current tab's history."""
        current_browser = self.tabs.currentWidget()
        if current_browser and current_browser.page().history().canGoBack():
            current_browser.back()
            self.statusBar().showMessage("Navigated back.")

    def go_forward(self):
        """Navigates forward in the current tab's history."""
        current_browser = self.tabs.currentWidget()
        if current_browser and current_browser.page().history().canGoForward():
            current_browser.forward()
            self.statusBar().showMessage("Navigated forward.")

    def refresh_page(self):
        """Reloads the current page."""
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.reload()
            self.statusBar().showMessage("Page refreshed.")

    def go_home(self):
        """Navigates the current tab to the enhanced homepage."""
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.setHtml(self._get_enhanced_homepage_html())
            self.statusBar().showMessage("Navigated to homepage.")

    def focus_url_bar(self):
        """Sets focus to the URL bar and selects its content."""
        self.url_bar.setFocus()
        self.url_bar.selectAll()
        self.statusBar().showMessage("URL bar focused.")

    def toggle_sidebar(self):
        """Toggles the visibility of the sidebar."""
        self.sidebar.setVisible(not self.sidebar.isVisible())
        self.statusBar().showMessage(f"Sidebar {'shown' if self.sidebar.isVisible() else 'hidden'}.")

    def toggle_fullscreen(self):
        """Toggles fullscreen mode for the main window."""
        if self.isFullScreen():
            self.showNormal()
            self.statusBar().showMessage("Exited fullscreen.")
        else:
            self.showFullScreen()
            self.statusBar().showMessage("Entered fullscreen.")

    def open_dev_tools(self):
        """Opens developer tools for the current web page."""
        current_browser = self.tabs.currentWidget()
        if current_browser and current_browser.page():
            dev_tools_page = QWebEnginePage(self.profile)
            dev_tools_view = QWebEngineView()
            dev_tools_view.setPage(dev_tools_page)
            dev_tools_page.setInspectedPage(current_browser.page())

            dev_tools_window = QMainWindow(self)
            dev_tools_window.setWindowTitle("Developer Tools")
            dev_tools_window.setCentralWidget(dev_tools_view)
            dev_tools_window.resize(1000, 700)
            dev_tools_window.show()
            self.statusBar().showMessage("Developer tools opened.")
        else:
            QMessageBox.warning(self, "Dev Tools", "No active page to inspect.")

    def find_in_page(self):
        """Prompts for text and finds it on the current page, highlighting results."""
        current_browser = self.tabs.currentWidget()
        if not current_browser:
            QMessageBox.warning(self, "Find", "No page open to search.")
            return

        # If a find input already exists, focus it
        if self.find_text_input:
            self.find_text_input.setFocus()
            self.find_text_input.selectAll()
            return

        # Create a temporary find bar
        find_bar = QToolBar("Find")
        find_bar.setStyleSheet("QToolBar { background-color: #3a3a3a; border: 1px solid #4a4a4a; border-radius: 5px; padding: 5px; }")
        self.addToolBar(Qt.BottomToolBarArea, find_bar)

        self.find_text_input = QLineEdit()
        self.find_text_input.setPlaceholderText("Find in page...")
        self.find_text_input.returnPressed.connect(self._perform_find)
        self.find_text_input.textChanged.connect(lambda text: current_browser.findText(text)) # Live search
        find_bar.addWidget(self.find_text_input)

        find_prev_btn = QAction("⬆️", self)
        find_prev_btn.setToolTip("Find Previous")
        find_prev_btn.triggered.connect(lambda: current_browser.findText(self.find_text_input.text(), QWebEnginePage.FindBackward))
        find_bar.addAction(find_prev_btn)

        find_next_btn = QAction("⬇️", self)
        find_next_btn.setToolTip("Find Next")
        find_next_btn.triggered.connect(lambda: current_browser.findText(self.find_text_input.text()))
        find_bar.addAction(find_next_btn)

        close_find_btn = QAction("✖️", self)
        close_find_btn.setToolTip("Close Find Bar")
        close_find_btn.triggered.connect(lambda: self._close_find_bar(find_bar))
        find_bar.addAction(close_find_btn)

        self.find_text_input.setFocus()
        self.statusBar().showMessage("Find in page activated.")

    def _perform_find(self):
        """Performs the find operation when Enter is pressed."""
        current_browser = self.tabs.currentWidget()
        if current_browser and self.find_text_input:
            current_browser.findText(self.find_text_input.text())

    def _close_find_bar(self, find_bar: QToolBar):
        """Closes the find in page bar and clears highlights."""
        current_browser = self.tabs.currentWidget()
        if current_browser:
            # Attempt to clear highlights. QWebEnginePage.FindClearSelection might not exist in all versions.
            # Passing an empty string usually clears the selection.
            current_browser.findText("")
        self.removeToolBar(find_bar)
        find_bar.deleteLater()
        self.find_text_input = None
        self.statusBar().showMessage("Find in page closed.")

    # --- Tab Management ---
    def add_new_tab(self, url: str = None, label: str = "New Tab"):
        """
        Adds a new tab to the browser.
        If a URL is provided, loads it; otherwise, loads the homepage.
        """
        browser_view = QWebEngineView()
        web_page = EnhancedWebPage(self.profile, self)
        browser_view.setPage(web_page)

        # Connect signals for tab management
        browser_view.titleChanged.connect(lambda title, b=browser_view: self._update_tab_title(b, title))
        browser_view.urlChanged.connect(lambda qurl, b=browser_view: self._update_tab_url(b, qurl))
        browser_view.loadFinished.connect(self._on_page_load_finished)
        browser_view.loadStarted.connect(lambda: self.statusBar().showMessage(f"Loading {browser_view.url().host()}..."))
        browser_view.loadProgress.connect(lambda p: self.statusBar().showMessage(f"Loading {browser_view.url().host()}... {p}%"))


        tab_index = self.tabs.addTab(browser_view, label)
        self.tabs.setCurrentIndex(tab_index)

        if url:
            browser_view.setUrl(QUrl(url))
        else:
            browser_view.setHtml(self._get_enhanced_homepage_html())

        self.statusBar().showMessage(f"New tab opened: {url if url else 'Homepage'}")
        return browser_view

    def _close_tab(self, index: int):
        """
        Closes a tab and stores its information for potential restoration.
        Prevents closing the last remaining tab.
        """
        if self.tabs.count() <= 1:
            QMessageBox.information(self, "Cannot Close", "Cannot close the last tab.")
            return

        browser_to_close = self.tabs.widget(index)
        if browser_to_close:
            url = browser_to_close.url().toString()
            title = browser_to_close.page().title()
            self.closed_tabs.append({"url": url, "title": title})
            # Keep only the last 10 closed tabs
            if len(self.closed_tabs) > 10:
                self.closed_tabs.pop(0)

        self.tabs.removeTab(index)
        browser_to_close.deleteLater() # Ensure widget is properly deleted
        self.statusBar().showMessage("Tab closed.")

    def close_current_tab(self):
        """Closes the currently active tab."""
        current_index = self.tabs.currentIndex()
        if current_index >= 0:
            self._close_tab(current_index)

    def restore_closed_tab(self):
        """Restores the most recently closed tab."""
        if self.closed_tabs:
            tab_info = self.closed_tabs.pop()
            self.add_new_tab(tab_info["url"], tab_info["title"])
            self.statusBar().showMessage(f"Restored tab: {tab_info['title']}")
        else:
            QMessageBox.information(self, "No Closed Tabs", "No recently closed tabs to restore.")
            self.statusBar().showMessage("No tabs to restore.")

    def _update_tab_title(self, browser_view: QWebEngineView, title: str):
        """Updates the title of a specific tab."""
        for i in range(self.tabs.count()):
            if self.tabs.widget(i) == browser_view:
                display_title = title if len(title) <= 30 else title[:27] + "..."
                self.tabs.setTabText(i, display_title)
                break

    def _update_tab_url(self, browser_view: QWebEngineView, qurl: QUrl):
        """
        Updates the URL bar and security indicator when a tab's URL changes.
        Also adds the visit to history.
        """
        url_str = qurl.toString()
        if browser_view == self.tabs.currentWidget():
            self.url_bar.setText(url_str)
            self._update_security_indicator(url_str)

        # Add to history only for valid web pages
        if not url_str.startswith(('data:', 'about:', 'chrome:', 'devtools:', 'null:')):
            title = browser_view.page().title()
            self.history_manager.add_visit(url_str, title)

    def _update_url_bar_and_security(self):
        """Updates the URL bar and security indicator when the active tab changes."""
        current_browser = self.tabs.currentWidget()
        if current_browser:
            url_str = current_browser.url().toString()
            self.url_bar.setText(url_str)
            self._update_security_indicator(url_str)
            self.statusBar().showMessage(f"Current tab: {current_browser.page().title()}")

    def _on_page_load_finished(self, success: bool):
        """Callback when a page finishes loading."""
        self.refresh_sidebar() # Refresh sidebar to show updated history/bookmarks
        current_browser = self.tabs.currentWidget()
        if current_browser:
            if success:
                self.statusBar().showMessage(f"Page loaded: {current_browser.page().title()}")
            else:
                self.statusBar().showMessage(f"Page failed to load: {current_browser.url().toString()}")
                # Optionally, show an error page or message
                # current_browser.setHtml("<h1>Page Load Error</h1><p>Could not load the requested page.</p>")

    def _load_url_from_bar(self):
        """Loads the URL entered in the address bar."""
        url_input = self.url_bar.text().strip()
        if url_input:
            self._load_url_in_current_tab(url_input)
        else:
            self.statusBar().showMessage("Please enter a URL or search query.")

    def _load_url_in_current_tab(self, url_str: str):
        """
        Loads a given URL in the current active tab, with smart URL handling.
        """
        current_browser = self.tabs.currentWidget()
        if not current_browser:
            current_browser = self.add_new_tab(url_str) # Create new tab if none exists

        # Smart URL handling: add https:// if it looks like a domain, otherwise search
        if not url_str.startswith(('http://', 'https://', 'file://', 'about:')):
            if '.' in url_str and ' ' not in url_str:
                url_to_load = 'https://' + url_str
            else:
                # Default to DuckDuckGo for search queries
                default_search_engine = self.app_settings.value("default_search_engine", "DuckDuckGo")
                search_engines = {
                    "DuckDuckGo": "https://duckduckgo.com/?q=",
                    "Google": "https://www.google.com/search?q=",
                    "Bing": "https://www.bing.com/search?q=",
                    "StartPage": "https://www.startpage.com/sp/search?query="
                }
                search_url_prefix = search_engines.get(default_search_engine, search_engines["DuckDuckGo"])
                url_to_load = f'{search_url_prefix}{url_str.replace(" ", "+")}'
        else:
            url_to_load = url_str

        current_browser.setUrl(QUrl(url_to_load))
        self.statusBar().showMessage(f"Loading: {url_to_load}")

        # Clear URL bar after a short delay if page fails to load (e.g., invalid URL)
        # This is a simple heuristic; more robust error handling is needed for production
        QTimer.singleShot(3000, lambda: self._check_url_bar_after_load(current_browser, url_to_load))

    def _check_url_bar_after_load(self, browser_view: QWebEngineView, original_url: str):
        """Checks if the URL bar still shows the original URL after a delay, implying a failed load."""
        if browser_view == self.tabs.currentWidget() and browser_view.url().toString() == original_url:
            # If the URL hasn't changed, it might be a failed load or a very slow one
            # For now, we just update status, but could show an error page
            self.statusBar().showMessage(f"Load attempt finished for: {original_url}")


    # --- Feature Actions ---
    def bookmark_page(self):
        """Bookmarks the current page."""
        current_browser = self.tabs.currentWidget()
        if not current_browser:
            self.statusBar().showMessage("No page open to bookmark.")
            return

        url = current_browser.url().toString()
        title = current_browser.page().title()

        if url and not url.startswith(('about:', 'data:', 'null:')):
            self.history_manager.add_bookmark(url, title)
            QMessageBox.information(self, "Bookmarked", f"Page '{title}' has been bookmarked!")
            self.refresh_sidebar()
            self.statusBar().showMessage(f"Bookmarked: {title}")
        else:
            QMessageBox.warning(self, "Cannot Bookmark", "This type of page cannot be bookmarked.")
            self.statusBar().showMessage("Cannot bookmark current page.")

    def show_history(self):
        """Displays the history dialog."""
        dialog = HistoryDialog(self, self.history_manager)
        dialog.exec_()
        self.statusBar().showMessage("History dialog opened.")

    def clear_browsing_data(self):
        """Displays the clear browsing data dialog."""
        dialog = ClearDataDialog(self, self.history_manager)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_sidebar()
            # If the current page is the homepage, refresh it to reflect cleared data
            current_browser = self.tabs.currentWidget()
            if current_browser and current_browser.url().toString().startswith('data:'):
                current_browser.setHtml(self._get_enhanced_homepage_html())
            self.statusBar().showMessage("Browsing data cleared.")
        else:
            self.statusBar().showMessage("Clear data operation cancelled.")

    def download_current_video(self):
        """Initiates a video download for the current page's URL."""
        current_browser = self.tabs.currentWidget()
        if not current_browser:
            QMessageBox.warning(self, "No Page", "No page is currently open to download from.")
            self.statusBar().showMessage("No page to download from.")
            return

        url = current_browser.url().toString()
        if url and (url.startswith('http://') or url.startswith('https://')):
            dialog = EnhancedVideoDownloadDialog(self, url)
            dialog.exec_()
            self.statusBar().showMessage("Video download dialog opened.")
        else:
            QMessageBox.warning(self, "Invalid URL", "Cannot download from this type of URL.")
            self.statusBar().showMessage("Invalid URL for download.")

    def show_settings(self):
        """Displays the settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec_()
        self.statusBar().showMessage("Settings dialog opened.")

    def show_downloads(self):
        """Opens the default download folder in the system's file explorer."""
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads", DEFAULT_DOWNLOAD_FOLDER_NAME)
        try:
            os.makedirs(downloads_folder, exist_ok=True) # Ensure folder exists before opening
            if os.name == 'nt':
                os.startfile(downloads_folder)
            elif sys.platform == 'darwin':
                subprocess.run(['open', downloads_folder])
            else:
                subprocess.run(['xdg-open', downloads_folder])
            self.statusBar().showMessage(f"Opened downloads folder: {downloads_folder}")
        except Exception as e:
            QMessageBox.critical(self, "Error Opening Folder", f"Could not open downloads folder: {e}")
            self.statusBar().showMessage("Failed to open downloads folder.")

    def closeEvent(self, event):
        """Handles the application close event, saving settings."""
        self._save_settings()
        event.accept()

# --- Main Application Entry Point ---
def main():
    """Main function to initialize and run the application."""
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # Apply the global dark theme stylesheet
    app.setStyleSheet(DARK_THEME_STYLESHEET)

    # Optional: Set application icon (requires a .ico or .png file)
    # app.setWindowIcon(QIcon("path/to/your/icon.png"))

    browser = EnhancedNullBrowser()
    browser.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
