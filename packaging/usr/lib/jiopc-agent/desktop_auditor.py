import time
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

def _find_desktop_file(filename: str) -> Optional[Path]:
    """Searches standard Linux launcher directories for a desktop file."""
    search_dirs = [
        Path.home() / ".local" / "share" / "applications",
        Path("/usr") / "share" / "applications",
        Path("/var/lib/snapd/desktop/applications"),
        Path.home() / "Desktop"
    ]
    
    for directory in search_dirs:
        filepath = directory / filename
        if filepath.is_file():
            return filepath
            
    return None

def _parse_desktop_file(filepath: Path) -> Dict[str, str]:
    """Parses key-value pairs from a desktop file.
    
    Gracefully handles malformed desktop files. Missing fields 
    are returned as empty strings.
    """
    info = {"Type": "", "Categories": ""}
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == "Type" and not info["Type"]:
                        info["Type"] = value
                    elif key == "Categories" and not info["Categories"]:
                        info["Categories"] = value
    except OSError:
        pass
                
    return info

def _validate_launcher(desktop_info: Dict[str, str], expected_category: str) -> Tuple[str, str]:
    """Validates the parsed desktop file information.
    
    Returns:
        A tuple of (result, detail).
    """
    if desktop_info.get("Type") != "Application":
        return "MISPLACED", "Desktop file type is not Application."
        
    categories_str = desktop_info.get("Categories", "")
    if not categories_str:
        return "MISPLACED", "Categories field missing."
        
    categories = [cat.strip() for cat in categories_str.split(";") if cat.strip()]
    
    if expected_category and expected_category not in categories:
        return "MISPLACED", f"Expected category {expected_category} not found."
        
    return "PASS", "Launcher present and correctly configured."

def run_desktop_audit(config: Dict[str, Any], logger: Any) -> int:
    """Runs the desktop presence audit.
    
    Verifies that every expected application launcher exists and 
    is correctly configured for the Linux desktop environment.
    """
    failures = 0
    apps = config.get("desktop_presence") or []
    
    for app in apps:
        start_time = time.perf_counter()
        
        name = app.get("name", "Unknown")
        filename = app.get("desktop_file", "")
        expected_category = app.get("menu_category", "")
        
        try:
            if not filename:
                result = "MISPLACED"
                detail = "Configuration missing desktop_file."
            else:
                filepath = _find_desktop_file(filename)
                
                if not filepath:
                    result = "MISSING"
                    detail = f"Desktop launcher {filename} not found."
                else:
                    desktop_info = _parse_desktop_file(filepath)
                    result, detail = _validate_launcher(desktop_info, expected_category)
                    
        except Exception as e:
            result = "MISPLACED"
            detail = f"Unexpected exception: {e}"
            
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        if result != "PASS":
            failures += 1
            
        logger.log(
            component="C",
            test_name=name,
            result=result,
            duration_ms=duration_ms,
            detail=detail
        )
        
        print(f"[C] {name}: {result} — {detail}")
        
    return failures
