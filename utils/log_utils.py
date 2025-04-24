# utils/log_utils.py
import os
import glob
from datetime import datetime, timedelta
import logging

def list_log_files(log_dir="logs", days=7):
    """List log files in the specified directory, sorted by modification time
    
    Args:
        log_dir (str): Directory containing log files
        days (int): Only show logs from the last N days
        
    Returns:
        list: List of log files with metadata (path, size, date)
    """
    if not os.path.exists(log_dir):
        print(f"Log directory '{log_dir}' does not exist")
        return []
    
    # Get all log files
    log_files = glob.glob(f"{log_dir}/*.log")
    
    # Filter by date if specified
    if days > 0:
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_files = []
        
        for log_file in log_files:
            mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
            if mod_time >= cutoff_date:
                filtered_files.append(log_file)
        
        log_files = filtered_files
    
    # Build file metadata
    log_data = []
    for log_file in log_files:
        file_size = os.path.getsize(log_file) / 1024  # Size in KB
        mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
        
        log_data.append({
            'path': log_file,
            'name': os.path.basename(log_file),
            'size_kb': round(file_size, 2),
            'date': mod_time.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # Sort by modification time (newest first)
    log_data.sort(key=lambda x: x['date'], reverse=True)
    return log_data

def clean_old_logs(log_dir="logs", days_to_keep=30):
    """Delete log files older than the specified number of days
    
    Args:
        log_dir (str): Directory containing log files
        days_to_keep (int): Keep logs from the last N days
        
    Returns:
        tuple: (deleted_count, deleted_size_kb)
    """
    if not os.path.exists(log_dir):
        print(f"Log directory '{log_dir}' does not exist")
        return (0, 0)
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    deleted_count = 0
    deleted_size = 0
    
    log_files = glob.glob(f"{log_dir}/*.log")
    
    for log_file in log_files:
        mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
        if mod_time < cutoff_date:
            file_size = os.path.getsize(log_file) / 1024  # Size in KB
            try:
                os.remove(log_file)
                deleted_count += 1
                deleted_size += file_size
                print(f"Deleted old log: {log_file}")
            except Exception as e:
                print(f"Failed to delete {log_file}: {str(e)}")
    
    return (deleted_count, round(deleted_size, 2))

def view_recent_logs(log_file=None, log_dir="logs", lines=50):
    """View the most recent lines from a log file or the most recent log file
    
    Args:
        log_file (str, optional): Specific log file to view
        log_dir (str): Directory containing log files
        lines (int): Number of lines to show
        
    Returns:
        list: The last N lines of the log file
    """
    # If no specific file provided, get the most recent log file
    if log_file is None:
        log_files = list_log_files(log_dir, days=7)
        if not log_files:
            print("No log files found")
            return []
        log_file = log_files[0]['path']
    
    try:
        with open(log_file, 'r') as f:
            # Read all lines and get the last N lines
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return recent_lines
    except Exception as e:
        print(f"Error reading log file {log_file}: {str(e)}")
        return []

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Log management utility")
    parser.add_argument('--action', choices=['list', 'clean', 'view'], default='list',
                        help='Action to perform (list, clean, view)')
    parser.add_argument('--dir', default='logs', help='Log directory')
    parser.add_argument('--days', type=int, default=7, help='Days filter for listing')
    parser.add_argument('--keep', type=int, default=30, help='Days to keep when cleaning')
    parser.add_argument('--lines', type=int, default=50, help='Lines to show when viewing')
    parser.add_argument('--file', help='Specific log file to view')
    
    args = parser.parse_args()
    
    if args.action == 'list':
        logs = list_log_files(args.dir, args.days)
        if logs:
            print(f"Found {len(logs)} log files in the last {args.days} days:")
            for log in logs:
                print(f"{log['date']} - {log['name']} ({log['size_kb']} KB)")
        else:
            print(f"No log files found in {args.dir} from the last {args.days} days")
    
    elif args.action == 'clean':
        count, size = clean_old_logs(args.dir, args.keep)
        print(f"Cleaned {count} log files ({size} KB) older than {args.keep} days")
    
    elif args.action == 'view':
        lines = view_recent_logs(args.file, args.dir, args.lines)
        if lines:
            print(f"Showing last {len(lines)} lines" + (f" from {args.file}" if args.file else ""))
            print("=" * 80)
            for line in lines:
                print(line.rstrip())
        else:
            print("No log content to display")