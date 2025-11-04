import re

def sanitize_filename(username: str) -> str:
    """
    Sanitizes a username to be used as a directory or filename.

    - Removes leading/trailing whitespace.
    - Replaces spaces with underscores.
    - Allows only alphanumeric characters, underscores, and hyphens.
    - Converts to lowercase.

    Args:
        username: The raw username string from user input.

    Returns:
        A sanitized, safe string for filesystem operations.
    """
    if not isinstance(username, str):
        return ""
        
    # Remove leading/trailing whitespace and convert to lowercase
    sanitized = username.strip().lower()
    
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    
    # Corrected the regex to allow numbers
    sanitized = re.sub(r'[^a-z0-9_-]', '', sanitized)
    
    return sanitized

