from datetime import datetime, timedelta

def parse_iso_datetime(datetime_str):
    """Parse ISO datetime string to datetime object"""
    if not datetime_str:
        return None
    
    # Handle 'Z' timezone indicator
    if datetime_str.endswith('Z'):
        datetime_str = datetime_str[:-1] + '+00:00'
    
    return datetime.fromisoformat(datetime_str)

def format_iso_datetime(dt):
    """Format datetime object to ISO datetime string"""
    if not dt:
        return None
    
    return dt.isoformat() + 'Z'

def get_date_range(days=7):
    """Get date range for the last N days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date

def parse_power_string(power_str):
    """Parse power string (e.g., '100 W') to numeric value in watts"""
    if not power_str:
        return 0
    
    # Remove whitespace and convert to lowercase
    power_str = power_str.strip().lower()
    
    # Extract numeric part
    numeric_part = ''.join(c for c in power_str if c.isdigit() or c == '.')
    
    try:
        value = float(numeric_part)
    except ValueError:
        return 0
    
    # Determine unit and convert to watts
    if 'kw' in power_str:
        return value * 1000
    elif 'mw' in power_str:
        return value * 1000000
    else:  # Assume watts
        return value
