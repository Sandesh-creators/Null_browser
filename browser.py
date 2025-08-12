import sys
import socket
import json
import os
from datetime import datetime
from urllib.parse import urlparse
from PyQt5.QtCore import QUrl, pyqtSignal, QObject
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QPushButton, QLineEdit, QHBoxLayout, QTabWidget, QToolBar, QAction,
    QShortcut
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile

# Check if TOR is running
def is_tor_running():
    try:
        s = socket.create_connection(("127.0.0.1", 9050), timeout=2)
        s.close()
        return True
    except:
        return False

class HistoryManager:
    def __init__(self):
        self.history_file = os.path.join(os.path.expanduser("~"), ".null_browser_history.json")
        self.history = self.load_history()
        self.shortcuts = [
            {"name": "Proton Mail", "url": "https://mail.proton.me/u/0/inbox", "icon": "📧"},
            {"name": "YouTube", "url": "https://youtube.com", "icon": "📺"},
            {"name": "GitHub", "url": "https://github.com", "icon": "🐙"},
            {"name": "Netflix", "url": "https://netflix.com", "icon": "🎬"},
            {"name": "Reddit", "url": "https://reddit.com", "icon": "🤖"},
            {"name": "Twitter", "url": "https://twitter.com", "icon": "🐦"},
            {"name": "LinkedIn", "url": "https://linkedin.com", "icon": "💼"},
            {"name": "Amazon", "url": "https://amazon.com", "icon": "📦"}
        ]

    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
        return []

    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_visit(self, url, title):
        if not url or url.startswith('data:') or url.startswith('about:'):
            return
        
        # Remove existing entry for same URL
        self.history = [item for item in self.history if item.get('url') != url]
        
        # Get favicon (simplified)
        domain = urlparse(url).netloc.lower()
        favicon = self.get_favicon_for_domain(domain)
        
        # Add new entry at the beginning
        visit = {
            'title': title or domain,
            'url': url,
            'favicon': favicon,
            'visitTime': datetime.now().isoformat(),
            'domain': domain
        }
        
        self.history.insert(0, visit)
        
        # Keep only last 50 entries
        self.history = self.history[:50]
        
        # Save to file
        self.save_history()

    def get_favicon_for_domain(self, domain):
        # Map common domains to emoji favicons
        favicon_map = {
            'github.com': '🐙',
            'stackoverflow.com': '📚',
            'youtube.com': '📺',
            'reddit.com': '🤖',
            'twitter.com': '🐦',
            'x.com': '🐦',
            'linkedin.com': '💼',
            'amazon.com': '📦',
            'google.com': '🔍',
            'gmail.com': '📧',
            'mail.proton.me': '📧',
            'netflix.com': '🎬',
            'facebook.com': '📘',
            'instagram.com': '📷',
            'wikipedia.org': '📖',
            'developer.mozilla.org': '📖',
            'docs.python.org': '🐍',
            'pypi.org': '🐍',
            'duckduckgo.com': '🦆'
        }
        
        for key, icon in favicon_map.items():
            if key in domain:
                return icon
        
        # Default favicons based on TLD
        if domain.endswith('.edu'):
            return '🎓'
        elif domain.endswith('.gov'):
            return '🏛️'
        elif domain.endswith('.org'):
            return '🌐'
        elif any(domain.endswith(tld) for tld in ['.news', '.blog']):
            return '📰'
        else:
            return '🌐'

    def clear_history(self):
        self.history = []
        self.save_history()

    def get_recent_sites(self, limit=10):
        return self.history[:limit]

class CustomWebPage(QWebEnginePage):
    def __init__(self, profile, browser_instance):
        super().__init__(profile)
        self.browser_instance = browser_instance
        
    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        url_str = url.toString()
        
        # Handle homepage navigation
        if self.url().toString().startswith('data:text/html') and not url_str.startswith('data:'):
            # This is a navigation from our homepage
            if nav_type == QWebEnginePage.NavigationTypeLinkClicked:
                # Navigate to the URL in the same tab
                self.setUrl(url)
                return False  # Prevent default handling
        
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)

class NullBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Null Browser 🌑")
        self.setGeometry(100, 100, 1280, 800)
        
        # Initialize history manager
        self.history_manager = HistoryManager()

        # Web Profile
        self.profile = QWebEngineProfile("NullProfile", self)
        if is_tor_running():
            print("🛡️ Using TOR Proxy")
            self.profile.setHttpProxy("socks5://127.0.0.1:9050")
        else:
            print("⚠️ TOR not found – using regular internet.")

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_url_bar)
        self.setCentralWidget(self.tabs)

        # Toolbar
        nav_bar = QToolBar()
        self.addToolBar(nav_bar)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.load_url)

        go_btn = QAction("Go", self)
        go_btn.triggered.connect(self.load_url)

        new_tab_btn = QAction("New Tab", self)
        new_tab_btn.triggered.connect(self.add_new_tab)
        new_tab_btn.setShortcut(QKeySequence("Ctrl+N"))

        nav_bar.addAction(new_tab_btn)
        nav_bar.addWidget(self.url_bar)
        nav_bar.addAction(go_btn)

        # Keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.add_new_tab)
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(self.close_current_tab)

        # Load initial tab
        self.add_new_tab()

    def get_homepage_html(self):
        # Get recent sites and shortcuts data
        recent_sites = self.history_manager.get_recent_sites()
        shortcuts = self.history_manager.shortcuts
        
        # Convert to JavaScript format
        recent_sites_js = json.dumps(recent_sites, ensure_ascii=False)
        shortcuts_js = json.dumps(shortcuts, ensure_ascii=False)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Null Browser</title>
            <style>
                body {{
                    background: #121212;
                    color: #e0e0e0;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                }}

                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    text-align: center;
                }}

                h1 {{
                    margin-bottom: 30px;
                    font-weight: 300;
                    font-size: 2.5em;
                }}

                .search-section {{
                    margin-bottom: 50px;
                }}

                .search-form input {{
                    width: min(600px, 80%);
                    padding: 15px 20px;
                    font-size: 18px;
                    border-radius: 25px;
                    border: 2px solid #333;
                    background: #1e1e1e;
                    color: #e0e0e0;
                    outline: none;
                    transition: border-color 0.3s ease;
                }}

                .search-form input:focus {{
                    border-color: #4285f4;
                }}

                .search-form input::placeholder {{
                    color: #888;
                }}

                .section-title {{
                    font-size: 1.4em;
                    margin: 40px 0 20px 0;
                    color: #fff;
                    text-align: left;
                    font-weight: 500;
                }}

                .sites-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 15px;
                    margin-bottom: 40px;
                }}

                .site-card {{
                    background: #1e1e1e;
                    border: 1px solid #333;
                    border-radius: 12px;
                    padding: 20px;
                    transition: all 0.3s ease;
                    cursor: pointer;
                    text-decoration: none;
                    color: inherit;
                    display: block;
                }}

                .site-card:hover {{
                    background: #2a2a2a;
                    border-color: #4285f4;
                    transform: translateY(-2px);
                }}

                .site-favicon {{
                    width: 32px;
                    height: 32px;
                    border-radius: 6px;
                    margin-bottom: 12px;
                    background: #333;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 18px;
                }}

                .site-title {{
                    font-weight: 600;
                    margin-bottom: 5px;
                    color: #fff;
                }}

                .site-url {{
                    font-size: 0.9em;
                    color: #888;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}

                .site-time {{
                    font-size: 0.8em;
                    color: #666;
                    margin-top: 8px;
                }}

                .shortcuts-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 15px;
                    max-width: 800px;
                    margin: 0 auto;
                }}

                .shortcut-card {{
                    background: #1e1e1e;
                    border: 1px solid #333;
                    border-radius: 12px;
                    padding: 20px;
                    transition: all 0.3s ease;
                    cursor: pointer;
                    text-decoration: none;
                    color: inherit;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }}

                .shortcut-card:hover {{
                    background: #2a2a2a;
                    border-color: #4285f4;
                    transform: translateY(-2px);
                }}

                .shortcut-icon {{
                    font-size: 32px;
                    margin-bottom: 10px;
                }}

                .shortcut-name {{
                    font-weight: 500;
                    font-size: 0.9em;
                    text-align: center;
                }}

                .clear-btn {{
                    background: #333;
                    color: #e0e0e0;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 0.9em;
                    margin-left: 20px;
                    transition: background 0.3s ease;
                }}

                .clear-btn:hover {{
                    background: #4a4a4a;
                }}

                .empty-state {{
                    text-align: center;
                    color: #666;
                    grid-column: 1 / -1;
                    padding: 40px;
                    font-style: italic;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌑 Welcome to Null Browser</h1>
                
                <div class="search-section">
                    <form class="search-form" onsubmit="handleSearch(event)">
                        <input type="text" name="q" placeholder="Search DuckDuckGo..." autofocus>
                    </form>
                </div>

                <div class="shortcuts-section">
                    <h2 class="section-title">
                        Quick Access
                    </h2>
                    <div class="shortcuts-grid" id="shortcutsGrid">
                        <!-- Shortcuts will be populated by JavaScript -->
                    </div>
                </div>

                <div class="recent-section">
                    <h2 class="section-title">
                        Recently Visited
                        <button class="clear-btn" onclick="clearHistory()">Clear History</button>
                    </h2>
                    <div class="sites-grid" id="recentSites">
                        <!-- Recent sites will be populated by JavaScript -->
                    </div>
                </div>
            </div>

            <script>
                // Load real data from Python backend
                let recentSites = {recent_sites_js};
                const shortcuts = {shortcuts_js};

                function formatTimeAgo(dateString) {{
                    const date = new Date(dateString);
                    const now = new Date();
                    const diffInSeconds = Math.floor((now - date) / 1000);
                    
                    if (diffInSeconds < 60) return 'Just now';
                    if (diffInSeconds < 3600) return `${{Math.floor(diffInSeconds / 60)}} minutes ago`;
                    if (diffInSeconds < 86400) return `${{Math.floor(diffInSeconds / 3600)}} hours ago`;
                    if (diffInSeconds < 604800) return `${{Math.floor(diffInSeconds / 86400)}} days ago`;
                    return date.toLocaleDateString();
                }}

                function renderRecentSites() {{
                    const container = document.getElementById('recentSites');
                    container.innerHTML = '';
                    
                    if (recentSites.length === 0) {{
                        container.innerHTML = '<div class="empty-state">No recent sites visited<br><small>Start browsing to see your history here</small></div>';
                        return;
                    }}
                    
                    recentSites.forEach(site => {{
                        const siteCard = document.createElement('a');
                        siteCard.className = 'site-card';
                        siteCard.href = site.url;
                        siteCard.innerHTML = `
                            <div class="site-favicon">${{site.favicon}}</div>
                            <div class="site-title">${{site.title}}</div>
                            <div class="site-url">${{site.url}}</div>
                            <div class="site-time">${{formatTimeAgo(site.visitTime)}}</div>
                        `;
                        container.appendChild(siteCard);
                    }});
                }}

                function renderShortcuts() {{
                    const container = document.getElementById('shortcutsGrid');
                    container.innerHTML = '';
                    
                    shortcuts.forEach(shortcut => {{
                        const shortcutCard = document.createElement('a');
                        shortcutCard.className = 'shortcut-card';
                        shortcutCard.href = shortcut.url;
                        shortcutCard.innerHTML = `
                            <div class="shortcut-icon">${{shortcut.icon}}</div>
                            <div class="shortcut-name">${{shortcut.name}}</div>
                        `;
                        container.appendChild(shortcutCard);
                    }});
                }}

                function clearHistory() {{
                    if (confirm('Are you sure you want to clear your browsing history?')) {{
                        // Communicate with PyQt to clear history
                        const event = new CustomEvent('clearHistory');
                        document.dispatchEvent(event);
                    }}
                }}

                function handleSearch(e) {{
                    e.preventDefault();
                    const query = e.target.querySelector('input[name="q"]').value;
                    if (query) {{
                        const searchUrl = `https://duckduckgo.com/?q=${{encodeURIComponent(query)}}`;
                        window.location.href = searchUrl;
                    }}
                }}

                // Initialize the page
                renderRecentSites();
                renderShortcuts();
            </script>
        </body>
        </html>
        """

    def add_new_tab(self, url=None, label="New Tab"):
        browser = QWebEngineView()
        page = CustomWebPage(self.profile, self)
        browser.setPage(page)

        # Apply dark mode after page load
        dark_mode_css = """
            * {
                background-color: #121212 !important;
                color: #e0e0e0 !important;
                scrollbar-color: #555 #121212;
            }
            a { color: #80cbc4 !important; }
        """
        js = f"""
        var style = document.createElement('style');
        style.innerHTML = `{dark_mode_css}`;
        document.head.appendChild(style);
        
        // Listen for clear history events
        document.addEventListener('clearHistory', function() {{
            window.location.href = 'data:clear-history';
        }});
        """
        
        def apply_dark_mode():
            browser.page().runJavaScript(js)
        
        browser.loadFinished.connect(apply_dark_mode)

        # Add browser to tab and track its index
        index = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(index)

        # Update tab title dynamically and track history
        def on_title_changed(title):
            self.tabs.setTabText(index, title[:30] + "..." if len(title) > 30 else title)
            # Add to history when title changes (page fully loaded)
            current_url = browser.url().toString()
            if current_url and not current_url.startswith('data:'):
                self.history_manager.add_visit(current_url, title)

        browser.titleChanged.connect(on_title_changed)

        # Handle URL changes for clear history
        def handle_url_change(qurl):
            url_str = qurl.toString()
            if url_str == 'data:clear-history':
                self.history_manager.clear_history()
                # Reload homepage
                browser.setHtml(self.get_homepage_html())

        browser.urlChanged.connect(handle_url_change)

        # Load page
        if url:
            browser.setUrl(QUrl(url))
        else:
            # Load homepage with real history data
            browser.setHtml(self.get_homepage_html())

    def load_url(self):
        url = self.url_bar.text()
        if not url.startswith("http"):
            url = "http://" + url
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.setUrl(QUrl(url))

    def update_url_bar(self, index):
        if index == -1:
            self.url_bar.setText("")
            return
        browser = self.tabs.widget(index)
        if browser:
            url_str = browser.url().toString()
            if not url_str.startswith('data:'):
                self.url_bar.setText(url_str)
            try:
                browser.urlChanged.disconnect(self.sync_url_bar)
            except Exception:
                pass
            browser.urlChanged.connect(self.sync_url_bar)

    def sync_url_bar(self, qurl):
        url_str = qurl.toString()
        if not url_str.startswith('data:'):
            self.url_bar.setText(url_str)

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            self.close()

    def close_current_tab(self):
        idx = self.tabs.currentIndex()
        if idx != -1:
            self.close_tab(idx)

    def closeEvent(self, event):
        # Save history when closing the browser
        self.history_manager.save_history()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = NullBrowser()
    browser.show()
   
sys.exit(app.exec_())