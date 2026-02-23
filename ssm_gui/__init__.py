import sys
import os

__version__ = "1.0.0"
__dev_state__ = 'beta'
__build_date__= "23.02.2026"


def resource_path(relative_path):
    """Resolve a relative path to a resource file.
    Works both when running from source and as a PyInstaller bundle."""
    if getattr(sys, '_MEIPASS', None):
        # PyInstaller bundle: files are extracted to _MEIPASS
        base_path = sys._MEIPASS
    else:
        # Running from source: resolve relative to the ssm_gui package dir
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
