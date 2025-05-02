#!/usr/bin/env python3
"""
System maintenance utility that checks and truncates large log files.
"""
import os
import time
import threading

# Constants
LOG_DIRECTORY = '/var/log'
THRESHOLD_MB = 500
CHECK_INTERVAL = 3600  # Check every hour

def check_large_files(directory, threshold_mb=THRESHOLD_MB): 
    """
    Check for large files in the specified directory and truncate them if they exceed the threshold.
    
    Args:
        directory (str): Directory to check for large files
        threshold_mb (int): Size threshold in MB
    
    Returns:
        list: List of truncated files
    """
    large_files = [] 
    threshold_bytes = threshold_mb * 1024 * 1024  # Convert MB to bytes 
    
    try:
        for root, dirs, files in os.walk(directory): 
            for file in files: 
                file_path = os.path.join(root, file) 
                try:
                    if os.path.isfile(file_path) and os.path.getsize(file_path) > threshold_bytes: 
                        large_files.append(file_path)
                        truncate_log(file_path)
                except (FileNotFoundError, PermissionError) as e:
                    print(f"Error checking file {file_path}: {e}")
    except Exception as e:
        print(f"Error walking directory {directory}: {e}")
    
    if large_files: 
        print(f"Files larger than {threshold_mb}MB found and truncated:")
        os.system('sudo find /var/log -type f -size +500M -exec truncate -s 0 {} \;')
        for large_file in large_files:
            print(large_file)
    else: 
        print(f"No files larger than {threshold_mb}MB found.")
        
    return large_files

def truncate_log(file_path):
    """
    Truncates the log file to zero size.

    Args:
        file_path (str): Path to the log file.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Truncating {file_path}, size: {os.path.getsize(file_path) / (1024 * 1024):.2f} MB")
        # Method 1: Using Python's file handling
        with open(file_path, 'w') as f:
            pass  # Empty the file content (truncate)
        return True
    except (FileNotFoundError, PermissionError):
        # Method 2: Try using system command if Python method fails
        try:
            os.system(f'sudo truncate -s 0 "{file_path}"')
            time.sleep(3)  # Wait for the file to be truncated
            os.system('sudo find /var/log -type f -size +500M -exec truncate -s 0 {} \;')
            print(f"Truncated {file_path} using system command")
            
            return True
        except Exception as e:
            print(f"{file_path} could not be truncated: {e}")
            return False

def truncate_large_system_logs():
    """
    Use system command to find and truncate large log files.
    This is a backup method that uses sudo privileges.
    """
    try:
        print("Checking for large system log files using system command...")
        os.system(f'sudo find {LOG_DIRECTORY} -type f -size +{THRESHOLD_MB}M -exec truncate -s 0 {{}} \\;')
        print("System command completed")
    except Exception as e:
        print(f"Error in system command: {e}")

def run_maintenance():
    """Main maintenance function that runs all checks"""
    try:
        print("Starting system maintenance checks")
        
        # First try the Python method
        large_files = check_large_files(LOG_DIRECTORY)
        
        # If no files were found or truncated, try the system command as backup
        if not large_files:
            truncate_large_system_logs()
        
        print("Maintenance checks completed")
    except Exception as e:
        print(f"Error in maintenance routine: {e}")

def main():
    """Main function to run the maintenance script"""
    print("Starting log truncation service")
    
    while True:
        try:
            run_maintenance()
            print(f"Sleeping for {CHECK_INTERVAL} seconds")
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("Service stopped by user")
            break
        except Exception as e:
            print(f"Unexpected error in main loop: {e}")
            time.sleep(60)  # Wait a minute before retrying if there's an error

if __name__ == "__main__":
    main()