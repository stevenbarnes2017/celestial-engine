from datetime import datetime, timedelta, time

def calculate_horizon_expiration(horizon: str) -> datetime:
    """
    Computes hard calendar boundaries for cache invalidation.
    """
    now = datetime.utcnow()
    
    if horizon == 'daily':
        # Valid until 23:59:59 of the current day
        return datetime.combine(now.date(), time.max)
        
    elif horizon == 'weekly':
        # Valid until Sunday night at 23:59:59
        days_until_sunday = (6 - now.weekday()) % 7
        sunday_date = now.date() + timedelta(days=days_until_sunday)
        return datetime.combine(sunday_date, time.max)
        
    elif horizon == 'monthly':
        # Valid until the last second of the current calendar month
        next_month = now.replace(day=28) + timedelta(days=4) # Rolls into next month safely
        last_day_of_current_month = next_month - timedelta(days=next_month.day)
        return datetime.combine(last_day_of_current_month.date(), time.max)
        
    elif horizon == 'yearly':
        # Valid until December 31st at 23:59:59
        return datetime(now.year, 12, 31, 23, 59, 59)
        
    return now + timedelta(hours=24) # Fallback insulation