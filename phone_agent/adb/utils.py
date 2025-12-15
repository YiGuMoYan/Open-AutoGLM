
import os
import sys

def get_adb_path() -> str:
    """
    Get the absolute path to the bundled ADB executable.
    """
    # Assuming code is in phone_agent/adb/utils.py
    # Project root is ../../../
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
    
    # Check for adb directory in project root
    adb_dir = os.path.join(project_root, "adb")
    
    if sys.platform == "win32":
        adb_exe = os.path.join(adb_dir, "adb.exe")
    else:
        adb_exe = os.path.join(adb_dir, "adb")
        
    if os.path.exists(adb_exe):
        return adb_exe
    
    # Fallback to system adb if bundled one not found (e.g. during dev if folder moved)
    return "adb"

def get_adb_prefix(device_id: str | None = None) -> list[str]:
    """Get ADB command prefix with correct executable path."""
    adb_path = get_adb_path()
    if device_id:
        return [adb_path, "-s", device_id]
    return [adb_path]
