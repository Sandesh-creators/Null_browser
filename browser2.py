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
    QListWidget, QListWidgetItem, QMenu, QSystemTrayIcon, QFrame
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineSettings

# Enhanced WebEngine configuration
def setup_webengine_settings():
    """Configure WebEngine with comprehensive media and security support"""
    try:
        # Enhanced video codec support
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
            '--disable-web-security',
            '--disable-features=TranslateUI',
            '--enable-smooth-scrolling'
        ]
        
        os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = ' '.join(video_flags)
        
        # Performance optimizations
        if not os.environ.get('QT_AUTO_SCREEN_SCALE_FACTOR'):
            os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
        
        # Memory optimization
        os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '9222'
        
        print("🎬 Enhanced WebEngine configuration loaded")
    except Exception as e:
        print(f"⚠️ WebEngine configuration error: {e}")

setup_webengine_settings()

# Enhanced TOR detection and proxy management
class ProxyManager:
    def __init__(self):
        self.tor_enabled = False
        self.proxy_type = "direct"
        self.tor_port = None
        
    def is_tor_running(self):
        """Check if TOR is running with retry logic"""
        for port in [9050, 9150]:  # Standard TOR ports
            try:
                s = socket.create_connection(("127.0.0.1", port), timeout=3)
                s.close()
                self.tor_port = port
                return True
            except:
                continue
        return False
    
    def get_proxy_config(self):
        """Get proxy configuration"""
        if self.is_tor_running():
            return {"type": "socks5", "host": "127.0.0.1", "port": self.tor_port}
        return {"type": "direct"}

# Enhanced database-based history management
class HistoryManager:
    def __init__(self):
        self.db_path = os.path.join(os.path.expanduser("~"), ".null_browser", "history.db")
        self.bookmarks_path = os.path.join(os.path.expanduser("~"), ".null_browser", "bookmarks.json")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_database()
        self.shortcuts = self._get_default_shortcuts()
        self.bookmarks = self.load_bookmarks()

    def init_database(self):
        """Initialize SQLite database for history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT NOT NULL,
                        title TEXT,
                        visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        visit_count INTEGER DEFAULT 1,
                        favicon TEXT,
                        domain TEXT,
                        UNIQUE(url)
                    )
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_visit_time ON history(visit_time DESC)
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_domain ON history(domain)
                ''')
        except Exception as e:
            print(f"Database initialization error: {e}")

    def _get_default_shortcuts(self):
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

    def add_visit(self, url, title):
        """Add visit to database with improved tracking"""
        if not url or url.startswith(('data:', 'about:', 'chrome:', 'devtools:', 'null:')):
            return
            
        try:
            domain = urlparse(url).netloc.lower()
            favicon = self.get_favicon_for_domain(domain)
            
            with sqlite3.connect(self.db_path) as conn:
                # Update existing or insert new
                conn.execute('''
                    INSERT INTO history (url, title, domain, favicon, visit_count)
                    VALUES (?, ?, ?, ?, 1)
                    ON CONFLICT(url) DO UPDATE SET
                        title = ?,
                        visit_time = CURRENT_TIMESTAMP,
                        visit_count = visit_count + 1
                ''', (url, title, domain, favicon, title))
                
        except Exception as e:
            print(f"History add error: {e}")

    def get_recent_sites(self, limit=15):
        """Get recent sites from database"""
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
        except Exception as e:
            print(f"Recent sites error: {e}")
            return []

    def get_most_visited(self, limit=10):
        """Get most visited sites"""
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
        except Exception as e:
            print(f"Most visited error: {e}")
            return []

    def search_history(self, query, limit=20):
        """Search through history"""
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
        except Exception as e:
            print(f"Search history error: {e}")
            return []

    def clear_history(self, days=None):
        """Clear history (all or by days)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if days:
                    cutoff_date = datetime.now() - timedelta(days=days)
                    conn.execute('DELETE FROM history WHERE visit_time < ?', (cutoff_date,))
                else:
                    conn.execute('DELETE FROM history')
        except Exception as e:
            print(f"Clear history error: {e}")

    def load_bookmarks(self):
        """Load bookmarks from JSON file"""
        try:
            if os.path.exists(self.bookmarks_path):
                with open(self.bookmarks_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Bookmarks load error: {e}")
        return []

    def save_bookmarks(self):
        """Save bookmarks to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.bookmarks_path), exist_ok=True)
            with open(self.bookmarks_path, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Bookmarks save error: {e}")

    def add_bookmark(self, url, title, folder="General"):
        """Add bookmark"""
        bookmark = {
            'url': url,
            'title': title,
            'folder': folder,
            'added_time': datetime.now().isoformat(),
            'favicon': self.get_favicon_for_domain(urlparse(url).netloc)
        }
        self.bookmarks.append(bookmark)
        self.save_bookmarks()

    def get_favicon_for_domain(self, domain):
        """Enhanced favicon mapping"""
        favicon_map = {
            # Tech/Dev
            'github.com': '🐙', 'gitlab.com': '🦊', 'stackoverflow.com': '📚',
            'developer.mozilla.org': '🦎', 'docs.python.org': '🐍', 'pypi.org': '🐍',
            
            # Media
            'youtube.com': '📺', 'youtu.be': '📺', 'netflix.com': '🎬', 'twitch.tv': '🎮',
            'vimeo.com': '📹', 'tiktok.com': '🎵', 'spotify.com': '🎵', 'soundcloud.com': '🎵',
            
            # Social
            'reddit.com': '🤖', 'twitter.com': '🐦', 'x.com': '🐦', 'facebook.com': '📘',
            'instagram.com': '📷', 'linkedin.com': '💼', 'discord.com': '💬',
            
            # Email
            'gmail.com': '📧', 'mail.proton.me': '🛡️', 'outlook.com': '📧',
            
            # Search/Reference
            'google.com': '🔍', 'duckduckgo.com': '🦆', 'wikipedia.org': '📖',
            'archive.org': '📚', 'scholar.google.com': '🎓',
            
            # Shopping
            'amazon.com': '📦', 'ebay.com': '🏪', 'etsy.com': '🎨',
            
            # News
            'bbc.com': '📰', 'cnn.com': '📰', 'reuters.com': '📰',
            
            # Privacy/Security
            'protonmail.com': '🛡️', 'signal.org': '🔒', 'torproject.org': '🧅'
        }
        
        for key, icon in favicon_map.items():
            if key in domain.lower():
                return icon
        
        # Enhanced TLD-based icons
        tld_map = {
            '.edu': '🎓', '.gov': '🏛️', '.org': '🌐', '.mil': '⚔️',
            '.news': '📰', '.blog': '📝', '.shop': '🛍️'
        }
        
        for tld, icon in tld_map.items():
            if domain.endswith(tld):
                return icon
                
        return '🌐'

# Enhanced video downloader with more format options
class EnhancedVideoDownloader(QThread):
    """Enhanced video downloader with better progress tracking"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    download_finished = pyqtSignal(bool, str)
    speed_updated = pyqtSignal(str)
    
    def __init__(self, url, format_id=None, audio_only=False, quality='best'):
        super().__init__()
        self.url = url
        self.format_id = format_id
        self.audio_only = audio_only
        self.quality = quality
        self.should_stop = False
        self.download_folder = os.path.join(os.path.expanduser("~"), "Downloads", "NullBrowser_Media")
        os.makedirs(self.download_folder, exist_ok=True)
    
    def stop(self):
        self.should_stop = True
    
    def run(self):
        try:
            # Check yt-dlp availability
            if not self.check_yt_dlp():
                self.download_finished.emit(False, "yt-dlp not found. Please install it with: pip install yt-dlp")
                return
            
            self.status_updated.emit("Preparing download...")
            
            # Build command
            cmd = ['yt-dlp', '--newline']
            
            # Format selection
            if self.audio_only:
                cmd.extend(['-f', 'bestaudio', '--extract-audio', '--audio-format', 'mp3', '--audio-quality', '0'])
                self.status_updated.emit("Downloading audio (MP3)...")
            elif self.format_id:
                cmd.extend(['-f', self.format_id])
            else:
                # Smart format selection based on quality
                quality_formats = {
                    'best': 'best[ext=mp4]/best[ext=webm]/best',
                    '1080p': 'best[height<=1080][ext=mp4]/best[height<=1080]',
                    '720p': 'best[height<=720][ext=mp4]/best[height<=720]',
                    '480p': 'best[height<=480][ext=mp4]/best[height<=480]'
                }
                cmd.extend(['-f', quality_formats.get(self.quality, quality_formats['best'])])
            
            # Output template with sanitization
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
                '--no-check-certificate',
                self.url
            ])
            
            self.status_updated.emit("Starting download process...")
            
            # Execute download
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, universal_newlines=True, bufsize=1
            )
            
            for line in iter(process.stdout.readline, ''):
                if self.should_stop:
                    process.terminate()
                    break
                
                line = line.strip()
                if line:
                    self.parse_progress_line(line)
            
            return_code = process.wait()
            
            if self.should_stop:
                self.download_finished.emit(False, "Download cancelled")
            elif return_code == 0:
                self.download_finished.emit(True, f"Downloaded to: {self.download_folder}")
            else:
                self.download_finished.emit(False, f"Download failed (code: {return_code})")
                
        except Exception as e:
            self.download_finished.emit(False, f"Error: {str(e)}")
    
    def parse_progress_line(self, line):
        """Parse yt-dlp output for progress information"""
        self.status_updated.emit(line)
        
        if '[download]' in line:
            # Extract percentage
            if '%' in line:
                try:
                    parts = line.split()
                    for part in parts:
                        if '%' in part and part.replace('%', '').replace('.', '').isdigit():
                            percent = float(part.replace('%', ''))
                            self.progress_updated.emit(int(percent))
                            break
                except ValueError:
                    pass
            
            # Extract speed
            if '/s' in line:
                try:
                    speed_part = [p for p in line.split() if '/s' in p and any(c.isdigit() for c in p)]
                    if speed_part:
                        self.speed_updated.emit(speed_part[0])
                except:
                    pass
    
    def check_yt_dlp(self):
        """Check if yt-dlp is available"""
        try:
            subprocess.run(['yt-dlp', '--version'], capture_output=True, timeout=5)
            return True
        except:
            return False

# Enhanced video download dialog
class EnhancedVideoDownloadDialog(QDialog):
    def __init__(self, parent, url):
        super().__init__(parent)
        self.url = url
        self.download_worker = None
        self.setWindowTitle("🎥 Enhanced Video Downloader")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # URL section
        url_group = QGroupBox("Source URL")
        url_layout = QVBoxLayout()
        url_label = QLabel(self.url)
        url_label.setWordWrap(True)
        url_label.setStyleSheet("padding: 10px; background: #f0f0f0; border-radius: 5px;")
        url_layout.addWidget(url_label)
        url_group.setLayout(url_layout)
        layout.addWidget(url_group)
        
        # Options section
        options_group = QGroupBox("Download Options")
        options_layout = QVBoxLayout()
        
        # Quality selection
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(['best', '1080p', '720p', '480p'])
        quality_layout.addWidget(self.quality_combo)
        options_layout.addLayout(quality_layout)
        
        # Audio only checkbox
        self.audio_only = QCheckBox("Download audio only (MP3)")
        options_layout.addWidget(self.audio_only)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        # Speed and status
        info_layout = QHBoxLayout()
        self.speed_label = QLabel("Speed: --")
        self.status_label = QLabel("Ready to download")
        info_layout.addWidget(self.speed_label)
        info_layout.addStretch()
        info_layout.addWidget(self.status_label)
        progress_layout.addLayout(info_layout)
        
        # Log area
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(150)
        progress_layout.addWidget(self.log_area)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.download_btn = QPushButton("📥 Start Download")
        self.download_btn.clicked.connect(self.start_download)
        
        self.cancel_btn = QPushButton("⏹️ Cancel")
        self.cancel_btn.clicked.connect(self.cancel_download)
        self.cancel_btn.setEnabled(False)
        
        self.close_btn = QPushButton("❌ Close")
        self.close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.download_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def log(self, message):
        """Add message to log area"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")
        
        # Auto-scroll
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def start_download(self):
        """Start the download process"""
        quality = self.quality_combo.currentText()
        audio_only = self.audio_only.isChecked()
        
        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        
        self.download_worker = EnhancedVideoDownloader(
            self.url, quality=quality, audio_only=audio_only
        )
        
        # Connect signals
        self.download_worker.progress_updated.connect(self.progress_bar.setValue)
        self.download_worker.status_updated.connect(self.log)
        self.download_worker.speed_updated.connect(lambda s: self.speed_label.setText(f"Speed: {s}"))
        self.download_worker.download_finished.connect(self.download_finished)
        
        self.download_worker.start()
        self.log("Download started...")
    
    def cancel_download(self):
        """Cancel download"""
        if self.download_worker:
            self.download_worker.stop()
            self.cancel_btn.setEnabled(False)
            self.log("Cancelling download...")
    
    def download_finished(self, success, message):
        """Handle download completion"""
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        if success:
            self.status_label.setText("✅ Download completed!")
            self.log(f"✅ {message}")
            
            # Try to open download folder
            try:
                download_folder = self.download_worker.download_folder
                if os.name == 'nt':
                    os.startfile(download_folder)
                else:
                    subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', download_folder])
            except:
                pass
        else:
            self.status_label.setText("❌ Download failed")
            self.log(f"❌ {message}")

# Enhanced custom web page with better security and features
class EnhancedWebPage(QWebEnginePage):
    def __init__(self, profile, browser_instance):
        super().__init__(profile)
        self.browser_instance = browser_instance
        self.setup_enhanced_settings()
        
    def setup_enhanced_settings(self):
        """Configure enhanced web page settings"""
        settings = self.settings()
        
        # Enhanced media support
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        
        # Security enhancements
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, False)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, False)
        
        # Performance improvements
        settings.setAttribute(QWebEngineSettings.HyperlinkAuditingEnabled, False)
        settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)
        
    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        """Handle special URLs and navigation"""
        url_str = url.toString()
        
        # Handle custom protocol URLs
        if url_str.startswith('null://'):
            self.handle_custom_url(url_str)
            return False
            
        return super().acceptNavigationRequest(url, navigation_type, is_main_frame)
    
    def handle_custom_url(self, url):
        """Handle custom protocol URLs"""
        if url == 'null://clear-history':
            self.browser_instance.clear_browsing_data()
        elif url == 'null://settings':
            self.browser_instance.show_settings()
        elif url == 'null://downloads':
            self.browser_instance.show_downloads()

# Enhanced main browser class
class EnhancedNullBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Null Browser 🌑 - Enhanced Edition")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize managers
        self.proxy_manager = ProxyManager()
        self.history_manager = HistoryManager()
        self.settings = QSettings("NullBrowser", "Enhanced")
        self.closed_tabs = []  # Store closed tabs for restore functionality
        
        # Setup UI components
        self.setup_profile()
        self.setup_ui()
        self.setup_shortcuts()
        self.restore_settings()
        
        print("🚀 Enhanced Null Browser initialized")

    def setup_profile(self):
        """Setup enhanced web engine profile"""
        self.profile = QWebEngineProfile("EnhancedNullProfile", self)
        
        # Configure proxy
        proxy_config = self.proxy_manager.get_proxy_config()
        if proxy_config["type"] == "socks5":
            print(f"🛡️ Using TOR proxy: {proxy_config['host']}:{proxy_config['port']}")
        else:
            print("🌐 Using direct connection")
            
        # Enhanced cache and storage settings
        cache_path = os.path.join(os.path.expanduser("~"), ".null_browser", "cache")
        os.makedirs(cache_path, exist_ok=True)
        self.profile.setCachePath(cache_path)
        self.profile.setPersistentStoragePath(cache_path)

    def setup_ui(self):
        """Setup enhanced user interface"""
        # Main layout with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Horizontal)
        
        # Optional sidebar (can be toggled)
        self.sidebar = self.create_sidebar()
        self.sidebar.setMaximumWidth(250)
        self.sidebar.setVisible(False)  # Hidden by default
        splitter.addWidget(self.sidebar)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_url_bar)
        splitter.addWidget(self.tabs)
        
        main_layout.addWidget(splitter)
        
        # Enhanced toolbar
        self.setup_enhanced_toolbar()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Load initial tab
        self.add_new_tab()

    def create_sidebar(self):
        """Create sidebar with bookmarks and history"""
        sidebar = QFrame()
        layout = QVBoxLayout(sidebar)
        
        # Bookmarks section
        bookmarks_label = QLabel("📚 Bookmarks")
        bookmarks_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(bookmarks_label)
        
        self.bookmarks_list = QListWidget()
        self.bookmarks_list.itemDoubleClicked.connect(self.open_bookmark)
        layout.addWidget(self.bookmarks_list)
        
        # History section
        history_label = QLabel("📜 Recent History")
        history_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(history_label)
        
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.open_history_item)
        layout.addWidget(self.history_list)
        
        self.refresh_sidebar()
        return sidebar

    def refresh_sidebar(self):
        """Refresh sidebar content"""
        # Update bookmarks
        self.bookmarks_list.clear()
        for bookmark in self.history_manager.bookmarks:
            item = QListWidgetItem(f"{bookmark.get('favicon', '🌐')} {bookmark['title']}")
            item.setData(Qt.UserRole, bookmark['url'])
            self.bookmarks_list.addItem(item)
        
        # Update recent history
        self.history_list.clear()
        recent = self.history_manager.get_recent_sites(10)
        for site in recent:
            item = QListWidgetItem(f"{site['favicon']} {site['title']}")
            item.setData(Qt.UserRole, site['url'])
            self.history_list.addItem(item)

    def open_bookmark(self, item):
        """Open bookmark in current tab"""
        url = item.data(Qt.UserRole)
        if url:
            self.load_url_in_current_tab(url)

    def open_history_item(self, item):
        """Open history item in current tab"""
        url = item.data(Qt.UserRole)
        if url:
            self.load_url_in_current_tab(url)

    def setup_enhanced_toolbar(self):
        """Setup enhanced toolbar with more features"""
        nav_bar = QToolBar()
        nav_bar.setMovable(False)
        self.addToolBar(nav_bar)
        
        # Navigation buttons
        back_btn = QAction("⬅️", self)
        back_btn.setToolTip("Back (Alt+Left)")
        back_btn.triggered.connect(self.go_back)
        nav_bar.addAction(back_btn)
        
        forward_btn = QAction("➡️", self)
        forward_btn.setToolTip("Forward (Alt+Right)")
        forward_btn.triggered.connect(self.go_forward)
        nav_bar.addAction(forward_btn)
        
        refresh_btn = QAction("🔄", self)
        refresh_btn.setToolTip("Refresh (F5)")
        refresh_btn.triggered.connect(self.refresh_page)
        nav_bar.addAction(refresh_btn)
        
        home_btn = QAction("🏠", self)
        home_btn.setToolTip("Home (Alt+Home)")
        home_btn.triggered.connect(self.go_home)
        nav_bar.addAction(home_btn)
        
        nav_bar.addSeparator()
        
        # Enhanced URL bar with suggestions
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL or search...")
        self.url_bar.returnPressed.connect(self.load_url)
        self.url_bar.textChanged.connect(self.on_url_text_changed)
        nav_bar.addWidget(self.url_bar)
        
        # Security indicator
        self.security_indicator = QLabel("🔒")
        self.security_indicator.setToolTip("Connection security")
        nav_bar.addWidget(self.security_indicator)
        
        nav_bar.addSeparator()
        
        # Feature buttons
        bookmark_btn = QAction("⭐", self)
        bookmark_btn.setToolTip("Bookmark this page (Ctrl+D)")
        bookmark_btn.triggered.connect(self.bookmark_page)
        nav_bar.addAction(bookmark_btn)
        
        download_btn = QAction("📥", self)
        download_btn.setToolTip("Download video (Ctrl+Shift+D)")
        download_btn.triggered.connect(self.download_current_video)
        nav_bar.addAction(download_btn)
        
        new_tab_btn = QAction("➕", self)
        new_tab_btn.setToolTip("New Tab (Ctrl+T)")
        new_tab_btn.triggered.connect(self.add_new_tab)
        nav_bar.addAction(new_tab_btn)
        
        nav_bar.addSeparator()
        
        # Sidebar toggle
        sidebar_btn = QAction("📋", self)
        sidebar_btn.setToolTip("Toggle Sidebar (Ctrl+B)")
        sidebar_btn.triggered.connect(self.toggle_sidebar)
        nav_bar.addAction(sidebar_btn)
        
        # Settings/Menu
        menu_btn = QAction("⚙️", self)
        menu_btn.setToolTip("Settings")
        menu_btn.triggered.connect(self.show_settings)
        nav_bar.addAction(menu_btn)

    def setup_shortcuts(self):
        """Setup comprehensive keyboard shortcuts"""
        shortcuts = [
            ("Ctrl+T", self.add_new_tab),
            ("Ctrl+W", self.close_current_tab),
            ("Ctrl+Shift+T", self.restore_closed_tab),
            ("Ctrl+D", self.bookmark_page),
            ("Ctrl+Shift+D", self.download_current_video),
            ("Ctrl+B", self.toggle_sidebar),
            ("Ctrl+H", self.show_history),
            ("Ctrl+Shift+Delete", self.clear_browsing_data),
            ("F5", self.refresh_page),
            ("Ctrl+R", self.refresh_page),
            ("Alt+Left", self.go_back),
            ("Alt+Right", self.go_forward),
            ("Alt+Home", self.go_home),
            ("Ctrl+L", self.focus_url_bar),
            ("Ctrl+F", self.find_in_page),
            ("F11", self.toggle_fullscreen),
            ("Ctrl+Shift+I", self.open_dev_tools)
        ]
        
        for shortcut, callback in shortcuts:
            QShortcut(QKeySequence(shortcut), self).activated.connect(callback)

    def restore_settings(self):
        """Restore saved settings"""
        # Window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Sidebar visibility
        sidebar_visible = self.settings.value("sidebar_visible", False, type=bool)
        self.sidebar.setVisible(sidebar_visible)

    def save_settings(self):
        """Save current settings"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("sidebar_visible", self.sidebar.isVisible())

    def on_url_text_changed(self, text):
        """Handle URL bar text changes for suggestions"""
        if len(text) > 2:
            # Simple history-based suggestions could be implemented here
            pass

    def update_security_indicator(self, url):
        """Update security indicator based on URL"""
        if url.startswith("https://"):
            self.security_indicator.setText("🔒")
            self.security_indicator.setToolTip("Secure connection (HTTPS)")
        elif url.startswith("http://"):
            self.security_indicator.setText("⚠️")
            self.security_indicator.setToolTip("Insecure connection (HTTP)")
        else:
            self.security_indicator.setText("ℹ️")
            self.security_indicator.setToolTip("Local or special page")

    def get_enhanced_homepage_html(self):
        """Generate enhanced homepage with better styling and features"""
        recent_sites = self.history_manager.get_recent_sites(12)
        most_visited = self.history_manager.get_most_visited(8)
        shortcuts = self.history_manager.shortcuts
        
        recent_sites_js = json.dumps(recent_sites, ensure_ascii=False)
        most_visited_js = json.dumps(most_visited, ensure_ascii=False)
        shortcuts_js = json.dumps(shortcuts, ensure_ascii=False)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Null Browser - Enhanced</title>
            <meta charset="UTF-8">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}

                body {{
                    background: linear-gradient(135deg, #0c0c0c 0%, #1a1a1a 100%);
                    color: #e0e0e0;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
                    margin: 0;
                    padding: 0;
                    min-height: 100vh;
                    overflow-x: hidden;
                }}

                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 20px;
                    text-align: center;
                }}

                .header {{
                    margin-bottom: 50px;
                }}

                .logo {{
                    font-size: 3.5em;
                    font-weight: 300;
                    margin-bottom: 10px;
                    background: linear-gradient(45deg, #4285f4, #34a853, #fbbc05, #ea4335);
                    background-size: 400% 400%;
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    animation: gradientShift 8s ease infinite;
                }}

                @keyframes gradientShift {{
                    0% {{ background-position: 0% 50%; }}
                    50% {{ background-position: 100% 50%; }}
                    100% {{ background-position: 0% 50%; }}
                }}

                .tagline {{
                    font-size: 1.1em;
                    color: #888;
                    margin-bottom: 30px;
                }}

                .search-section {{
                    margin-bottom: 60px;
                    position: relative;
                }}

                .search-container {{
                    position: relative;
                    max-width: 700px;
                    margin: 0 auto;
                }}

                .search-input {{
                    width: 100%;
                    padding: 20px 25px;
                    font-size: 18px;
                    border-radius: 50px;
                    border: 2px solid transparent;
                    background: rgba(30, 30, 30, 0.8);
                    backdrop-filter: blur(10px);
                    color: #e0e0e0;
                    outline: none;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }}

                .search-input:focus {{
                    border-color: #4285f4;
                    box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.1), 0 12px 40px rgba(0, 0, 0, 0.4);
                    transform: translateY(-2px);
                }}

                .search-input::placeholder {{
                    color: #888;
                }}

                .search-engines {{
                    display: flex;
                    justify-content: center;
                    gap: 15px;
                    margin-top: 20px;
                }}

                .search-engine {{
                    padding: 8px 16px;
                    border-radius: 20px;
                    background: rgba(40, 40, 40, 0.6);
                    border: 1px solid #333;
                    color: #ccc;
                    text-decoration: none;
                    font-size: 0.9em;
                    transition: all 0.3s ease;
                }}

                .search-engine:hover {{
                    background: rgba(66, 133, 244, 0.2);
                    border-color: #4285f4;
                    color: #fff;
                    transform: translateY(-1px);
                }}

                .section {{
                    margin-bottom: 50px;
                    text-align: left;
                }}

                .section-title {{
                    font-size: 1.6em;
                    margin-bottom: 25px;
                    color: #fff;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}

                .section-title::after {{
                    content: '';
                    flex: 1;
                    height: 1px;
                    background: linear-gradient(90deg, #333, transparent);
                }}

                .cards-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
                    gap: 20px;
                }}

                .shortcuts-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                    gap: 20px;
                    max-width: 900px;
                    margin: 0 auto;
                }}

                .card {{
                    background: rgba(30, 30, 30, 0.6);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 16px;
                    padding: 24px;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    cursor: pointer;
                    text-decoration: none;
                    color: inherit;
                    display: block;
                    position: relative;
                    overflow: hidden;
                }}

                .card::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: linear-gradient(45deg, transparent, rgba(66, 133, 244, 0.1), transparent);
                    opacity: 0;
                    transition: opacity 0.3s ease;
                }}

                .card:hover {{
                    transform: translateY(-4px) scale(1.02);
                    border-color: rgba(66, 133, 244, 0.3);
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
                }}

                .card:hover::before {{
                    opacity: 1;
                }}

                .card-favicon {{
                    width: 48px;
                    height: 48px;
                    border-radius: 12px;
                    margin-bottom: 15px;
                    background: rgba(255, 255, 255, 0.1);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    position: relative;
                    z-index: 1;
                }}

                .card-title {{
                    font-weight: 600;
                    margin-bottom: 8px;
                    color: #fff;
                    font-size: 1.1em;
                    position: relative;
                    z-index: 1;
                }}

                .card-url {{
                    font-size: 0.9em;
                    color: #888;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    margin-bottom: 5px;
                    position: relative;
                    z-index: 1;
                }}

                .card-meta {{
                    font-size: 0.8em;
                    color: #666;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    position: relative;
                    z-index: 1;
                }}

                .visit-count {{
                    background: rgba(66, 133, 244, 0.2);
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 0.75em;
                }}

                .shortcut-card {{
                    background: rgba(30, 30, 30, 0.6);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 16px;
                    padding: 25px 20px;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    cursor: pointer;
                    text-decoration: none;
                    color: inherit;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    text-align: center;
                    position: relative;
                    overflow: hidden;
                }}

                .shortcut-card::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: linear-gradient(135deg, rgba(66, 133, 244, 0.1), rgba(52, 168, 83, 0.1));
                    opacity: 0;
                    transition: opacity 0.3s ease;
                }}

                .shortcut-card:hover {{
                    transform: translateY(-3px) scale(1.05);
                    border-color: rgba(66, 133, 244, 0.3);
                    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.3);
                }}

                .shortcut-card:hover::before {{
                    opacity: 1;
                }}

                .shortcut-icon {{
                    font-size: 36px;
                    margin-bottom: 12px;
                    position: relative;
                    z-index: 1;
                }}

                .shortcut-name {{
                    font-weight: 500;
                    font-size: 0.95em;
                    position: relative;
                    z-index: 1;
                }}

                .shortcut-category {{
                    font-size: 0.8em;
                    color: #666;
                    margin-top: 5px;
                    position: relative;
                    z-index: 1;
                }}

                .actions {{
                    display: flex;
                    justify-content: center;
                    gap: 20px;
                    margin-top: 30px;
                    flex-wrap: wrap;
                }}

                .action-btn {{
                    background: rgba(66, 133, 244, 0.2);
                    border: 1px solid rgba(66, 133, 244, 0.3);
                    color: #e0e0e0;
                    padding: 12px 24px;
                    border-radius: 25px;
                    cursor: pointer;
                    font-size: 0.9em;
                    transition: all 0.3s ease;
                    text-decoration: none;
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                }}

                .action-btn:hover {{
                    background: rgba(66, 133, 244, 0.3);
                    border-color: #4285f4;
                    transform: translateY(-2px);
                    box-shadow: 0 8px 20px rgba(66, 133, 244, 0.2);
                }}

                .empty-state {{
                    text-align: center;
                    color: #666;
                    grid-column: 1 / -1;
                    padding: 60px 20px;
                    font-style: italic;
                }}

                .empty-state .icon {{
                    font-size: 4em;
                    margin-bottom: 20px;
                    opacity: 0.5;
                }}

                .features-banner {{
                    background: linear-gradient(135deg, rgba(66, 133, 244, 0.1), rgba(52, 168, 83, 0.1));
                    border: 1px solid rgba(66, 133, 244, 0.2);
                    border-radius: 16px;
                    padding: 25px;
                    margin: 30px 0;
                    text-align: left;
                }}

                .features-banner h3 {{
                    color: #4285f4;
                    margin-bottom: 15px;
                    font-size: 1.3em;
                }}

                .features-list {{
                    list-style: none;
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 10px;
                }}

                .features-list li {{
                    padding: 8px 0;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}

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

                <div class="section" id="mostVisitedSection" style="display: none;">
                    <h2 class="section-title">⭐ Most Visited</h2>
                    <div class="cards-grid" id="mostVisitedGrid"></div>
                </div>

                <div class="section" id="recentSection" style="display: none;">
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
                    const engines = {{
                        'duckduckgo': 'https://duckduckgo.com/?q=',
                        'google': 'https://www.google.com/search?q=',
                        'bing': 'https://www.bing.com/search?q=',
                        'startpage': 'https://www.startpage.com/sp/search?query='
                    }};
                    
                    if (query.includes('.') && !query.includes(' ')) {{
                        // Looks like a URL
                        const url = query.startsWith('http') ? query : `https://${{query}}`;
                        window.location.href = url;
                    }} else {{
                        // Search query
                        const searchUrl = engines[engine] + encodeURIComponent(query);
                        window.location.href = searchUrl;
                    }}
                }}

                function clearHistory() {{
                    if (confirm('Clear all browsing history? This cannot be undone.')) {{
                        window.location.href = 'null://clear-history';
                    }}
                }}

                function showSettings() {{
                    window.location.href = 'null://settings';
                }}

                function showDownloads() {{
                    window.location.href = 'null://downloads';
                }}

                // Event listeners
                document.querySelector('.search-input').addEventListener('keypress', (e) => {{
                    if (e.key === 'Enter') {{
                        handleSearch(e.target.value);
                    }}
                }});

                document.querySelectorAll('.search-engine').forEach(engine => {{
                    engine.addEventListener('click', (e) => {{
                        e.preventDefault();
                        const query = document.querySelector('.search-input').value;
                        if (query) {{
                            handleSearch(query, e.target.dataset.engine);
                        }}
                    }});
                }});

                // Initialize
                renderShortcuts();
                renderMostVisited();
                renderRecent();

                // Add some smooth scrolling
                document.documentElement.style.scrollBehavior = 'smooth';
            </script>
        </body>
        </html>
        """

    # Navigation methods
    def go_back(self):
        current_browser = self.tabs.currentWidget()
        if current_browser and hasattr(current_browser, 'history') and current_browser.history().canGoBack():
            current_browser.back()

    def go_forward(self):
        current_browser = self.tabs.currentWidget()
        if current_browser and hasattr(current_browser, 'history') and current_browser.history().canGoForward():
            current_browser.forward()

    def refresh_page(self):
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.reload()

    def go_home(self):
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.setHtml(self.get_enhanced_homepage_html())

    def focus_url_bar(self):
        self.url_bar.setFocus()
        self.url_bar.selectAll()

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def open_dev_tools(self):
        """Open developer tools"""
        current_browser = self.tabs.currentWidget()
        if current_browser and hasattr(current_browser, 'page'):
            # This would need additional implementation for dev tools
            QMessageBox.information(self, "Dev Tools", "Developer tools feature would be implemented here")

    def find_in_page(self):
        """Find text in current page"""
        text, ok = QMessageBox.getText(self, "Find in Page", "Enter text to find:")
        if ok and text:
            current_browser = self.tabs.currentWidget()
            if current_browser:
                current_browser.findText(text)

    # Tab management
    def add_new_tab(self, url=None, label="New Tab"):
        browser = QWebEngineView()
        page = EnhancedWebPage(self.profile, self)
        browser.setPage(page)

        # Enhanced JavaScript injection
        def inject_enhancements():
            js_code = """
                // Dark mode CSS
                var style = document.createElement('style');
                style.innerHTML = `
                    * {
                        scrollbar-width: thin;
                        scrollbar-color: #555 #222;
                    }
                    ::-webkit-scrollbar { width: 12px; }
                    ::-webkit-scrollbar-track { background: #222; }
                    ::-webkit-scrollbar-thumb { background: #555; border-radius: 6px; }
                    ::-webkit-scrollbar-thumb:hover { background: #666; }
                `;
                document.head.appendChild(style);
            """
            browser.page().runJavaScript(js_code)

        # Connect signals
        browser.titleChanged.connect(lambda title, browser=browser: self.update_tab_title(browser, title))
        browser.urlChanged.connect(lambda qurl, browser=browser: self.update_tab_url(browser, qurl))
        browser.loadFinished.connect(lambda: inject_enhancements())
        browser.loadFinished.connect(self.on_page_loaded)

        # Add tab
        tab_index = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(tab_index)

        # Load URL or homepage
        if url:
            browser.setUrl(QUrl(url))
        else:
            browser.setHtml(self.get_enhanced_homepage_html())

        return browser

    def close_tab(self, index):
        """Close tab and store for restore functionality"""
        if self.tabs.count() <= 1:
            return  # Don't close the last tab
        
        # Store closed tab info
        browser = self.tabs.widget(index)
        if browser:
            url = browser.url().toString()
            title = browser.page().title()
            self.closed_tabs.append({"url": url, "title": title})
            
            # Keep only last 10 closed tabs
            if len(self.closed_tabs) > 10:
                self.closed_tabs.pop(0)
        
        self.tabs.removeTab(index)

    def close_current_tab(self):
        """Close currently active tab"""
        current_index = self.tabs.currentIndex()
        if current_index >= 0:
            self.close_tab(current_index)

    def restore_closed_tab(self):
        """Restore last closed tab"""
        if self.closed_tabs:
            tab_info = self.closed_tabs.pop()
            self.add_new_tab(tab_info["url"], tab_info["title"])

    def update_tab_title(self, browser, title):
        """Update tab title"""
        for i in range(self.tabs.count()):
            if self.tabs.widget(i) == browser:
                self.tabs.setTabText(i, title[:30] + "..." if len(title) > 30 else title)
                break

    def update_tab_url(self, browser, qurl):
        """Update URL bar when tab changes"""
        url = qurl.toString()
        if browser == self.tabs.currentWidget():
            self.url_bar.setText(url)
            self.update_security_indicator(url)
            
            # Add to history
            title = browser.page().title()
            self.history_manager.add_visit(url, title)

    def update_url_bar(self):
        """Update URL bar when switching tabs"""
        current_browser = self.tabs.currentWidget()
        if current_browser:
            url = current_browser.url().toString()
            self.url_bar.setText(url)
            self.update_security_indicator(url)

    def on_page_loaded(self):
        """Handle page load completion"""
        self.refresh_sidebar()

    def load_url(self):
        """Load URL from address bar"""
        url = self.url_bar.text().strip()
        if url:
            self.load_url_in_current_tab(url)

    def load_url_in_current_tab(self, url):
        """Load URL in current tab"""
        current_browser = self.tabs.currentWidget()
        if not current_browser:
            return

        # Smart URL handling
        if not url.startswith(('http://', 'https://', 'file://', 'about:')):
            if '.' in url and ' ' not in url:
                url = 'https://' + url
            else:
                # Search query
                url = f'https://duckduckgo.com/?q={url.replace(" ", "+")}'

        current_browser.setUrl(QUrl(url))

    # Bookmark and history management
    def bookmark_page(self):
        """Bookmark current page"""
        current_browser = self.tabs.currentWidget()
        if not current_browser:
            return

        url = current_browser.url().toString()
        title = current_browser.page().title()
        
        if url and not url.startswith(('about:', 'data:')):
            self.history_manager.add_bookmark(url, title)
            QMessageBox.information(self, "Bookmarked", f"Page '{title}' has been bookmarked!")
            self.refresh_sidebar()

    def show_history(self):
        """Show history dialog"""
        dialog = HistoryDialog(self, self.history_manager)
        dialog.exec_()

    def clear_browsing_data(self):
        """Clear browsing data dialog"""
        dialog = ClearDataDialog(self, self.history_manager)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_sidebar()
            # Refresh current page if it's the homepage
            current_browser = self.tabs.currentWidget()
            if current_browser and current_browser.url().toString().startswith('data:'):
                current_browser.setHtml(self.get_enhanced_homepage_html())

    def download_current_video(self):
        """Download video from current page"""
        current_browser = self.tabs.currentWidget()
        if not current_browser:
            return

        url = current_browser.url().toString()
        if url:
            dialog = EnhancedVideoDownloadDialog(self, url)
            dialog.exec_()

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
        dialog.exec_()

    def show_downloads(self):
        """Show downloads folder"""
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads", "NullBrowser_Media")
        try:
            if os.name == 'nt':
                os.startfile(downloads_folder)
            else:
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', downloads_folder])
        except Exception as e:
            QMessageBox.information(self, "Downloads", f"Downloads folder: {downloads_folder}")

    def closeEvent(self, event):
        """Handle application close"""
        self.save_settings()
        event.accept()


# Additional dialog classes
class HistoryDialog(QDialog):
    def __init__(self, parent, history_manager):
        super().__init__(parent)
        self.history_manager = history_manager
        self.setWindowTitle("📜 Browser History")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.search_history)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # History list
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.open_history_item)
        layout.addWidget(self.history_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        clear_btn = QPushButton("🗑️ Clear All")
        clear_btn.clicked.connect(self.clear_all_history)
        button_layout.addWidget(clear_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.load_history()

    def load_history(self):
        """Load history into list"""
        self.history_list.clear()
        recent_sites = self.history_manager.get_recent_sites(100)
        
        for site in recent_sites:
            item_text = f"{site['favicon']} {site['title']} - {site['url']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, site['url'])
            self.history_list.addItem(item)

    def search_history(self, query):
        """Search history"""
        self.history_list.clear()
        if query:
            results = self.history_manager.search_history(query, 50)
        else:
            results = self.history_manager.get_recent_sites(100)
        
        for site in results:
            item_text = f"{site['favicon']} {site['title']} - {site['url']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, site['url'])
            self.history_list.addItem(item)

    def open_history_item(self, item):
        """Open selected history item"""
        url = item.data(Qt.UserRole)
        if url:
            self.parent().add_new_tab(url)
            self.close()

    def clear_all_history(self):
        """Clear all history"""
        reply = QMessageBox.question(self, "Clear History", 
                                   "Are you sure you want to clear all history?")
        if reply == QMessageBox.Yes:
            self.history_manager.clear_history()
            self.load_history()


class ClearDataDialog(QDialog):
    def __init__(self, parent, history_manager):
        super().__init__(parent)
        self.history_manager = history_manager
        self.setWindowTitle("🗑️ Clear Browsing Data")
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Select data to clear:"))
        
        # Checkboxes
        self.history_cb = QCheckBox("Browsing History")
        self.history_cb.setChecked(True)
        layout.addWidget(self.history_cb)
        
        self.bookmarks_cb = QCheckBox("Bookmarks")
        layout.addWidget(self.bookmarks_cb)
        
        # Time range
        layout.addWidget(QLabel("Time range:"))
        self.time_combo = QComboBox()
        self.time_combo.addItems(["All time", "Last 7 days", "Last 30 days"])
        layout.addWidget(self.time_combo)
        
        # Buttons
        button_layout = QHBoxLayout()
        clear_btn = QPushButton("Clear Data")
        clear_btn.clicked.connect(self.clear_data)
        button_layout.addWidget(clear_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def clear_data(self):
        """Clear selected data"""
        if self.history_cb.isChecked():
            time_range = self.time_combo.currentText()
            days = None
            if time_range == "Last 7 days":
                days = 7
            elif time_range == "Last 30 days":
                days = 30
            
            self.history_manager.clear_history(days)
        
        if self.bookmarks_cb.isChecked():
            self.history_manager.bookmarks.clear()
            self.history_manager.save_bookmarks()
        
        QMessageBox.information(self, "Cleared", "Selected data has been cleared!")
        self.accept()


class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_browser = parent
        self.setWindowTitle("⚙️ Browser Settings")
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # General settings
        general_group = QGroupBox("General")
        general_layout = QVBoxLayout()
        
        # Homepage setting
        homepage_layout = QHBoxLayout()
        homepage_layout.addWidget(QLabel("Homepage:"))
        self.homepage_input = QLineEdit()
        self.homepage_input.setText("Enhanced Start Page")
        self.homepage_input.setReadOnly(True)
        homepage_layout.addWidget(self.homepage_input)
        general_layout.addLayout(homepage_layout)
        
        # Search engine
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Default Search:"))
        self.search_combo = QComboBox()
        self.search_combo.addItems(["DuckDuckGo", "Google", "Bing", "StartPage"])
        search_layout.addWidget(self.search_combo)
        general_layout.addLayout(search_layout)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Privacy settings
        privacy_group = QGroupBox("Privacy")
        privacy_layout = QVBoxLayout()
        
        self.tor_cb = QCheckBox("Use TOR proxy (if available)")
        self.tor_cb.setChecked(self.parent_browser.proxy_manager.is_tor_running())
        privacy_layout.addWidget(self.tor_cb)
        
        self.javascript_cb = QCheckBox("Enable JavaScript")
        self.javascript_cb.setChecked(True)
        privacy_layout.addWidget(self.javascript_cb)
        
        privacy_group.setLayout(privacy_layout)
        layout.addWidget(privacy_group)
        
        # Download settings
        download_group = QGroupBox("Downloads")
        download_layout = QVBoxLayout()
        
        download_path_layout = QHBoxLayout()
        download_path_layout.addWidget(QLabel("Download Folder:"))
        self.download_path = QLabel(os.path.join(os.path.expanduser("~"), "Downloads", "NullBrowser_Media"))
        download_path_layout.addWidget(self.download_path)
        download_layout.addLayout(download_path_layout)
        
        download_group.setLayout(download_layout)
        layout.addWidget(download_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def save_settings(self):
        """Save settings"""
        # Settings would be saved here
        QMessageBox.information(self, "Settings", "Settings saved successfully!")
        self.accept()


# Main application
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Enhanced Null Browser")
    app.setApplicationVersion("2.0")
    
    # Set application icon (you can add an icon file)
    # app.setWindowIcon(QIcon("icon.png"))
    
    # Create and show browser
    browser = EnhancedNullBrowser()
    browser.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()