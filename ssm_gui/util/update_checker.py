import urllib.request
import urllib.error
import json
from PySide6.QtCore import QThread, Signal

class UpdateCheckerThread(QThread):
    """
    Background thread to check GitHub for new releases.
    Emits update_available(version, url) if a newer tag is found.
    """
    update_available = Signal(str, str)

    def __init__(self, current_version, repo_owner, repo_name):
        super().__init__()
        self.current_version = current_version
        self.repo_owner = repo_owner
        self.repo_name = repo_name

    def run(self):
        api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
        try:
            # Add a timeout so it doesn't hang indefinitely if network is slow
            req = urllib.request.Request(api_url, headers={'User-Agent': 'ssm_viewer'})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    latest_tag = data.get('tag_name', '').strip()
                    release_url = data.get('html_url', '')

                    import re
                    
                    # Extract only the numeric semantic version x.y.z
                    def extract_semver(v):
                        match = re.search(r"(\d+)\.(\d+)\.(\d+)", v)
                        if match:
                            return tuple(map(int, match.groups()))
                        return (0, 0, 0)
                    
                    semver_latest = extract_semver(latest_tag)
                    semver_current = extract_semver(self.current_version)

                    if semver_latest > semver_current:
                        self.update_available.emit(latest_tag, release_url)

        except (urllib.error.URLError, json.JSONDecodeError, Exception) as e:
            # Fail silently on network errors so we don't bother the user
            print(f"Update check failed: {e}")
