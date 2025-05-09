#!/usr/bin/env python3
"""
System maintenance utility that checks and truncates large log files.
Also monitors camera directory size and cleans up images when needed.
"""
import os
import time
import threading
import glob
import shutil

# Constants
LOG_DIRECTORY = '/var/log'
THRESHOLD_MB = 500
CHECK_INTERVAL = 3600  # Check every hour
CAMERA_DIRECTORY = '/home/user/camera'
CAMERA_SIZE_THRESHOLD_GB = 1  # 1GB threshold for camera directory

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

def check_camera_directory_size():
    """
    Check if the camera directory exceeds the threshold size (1GB)
    and delete all images if it does.
    """
    try:
        if not os.path.exists(CAMERA_DIRECTORY):
            print(f"Camera directory {CAMERA_DIRECTORY} does not exist")
            return
        
        # Calculate directory size in bytes
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(CAMERA_DIRECTORY):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
        
        # Convert to GB
        total_size_gb = total_size / (1024 * 1024 * 1024)
        
        print(f"Camera directory size: {total_size_gb:.2f} GB")
        
        # If directory size exceeds threshold, delete all image files
        if total_size_gb > CAMERA_SIZE_THRESHOLD_GB:
            print(f"Camera directory exceeds {CAMERA_SIZE_THRESHOLD_GB}GB threshold, cleaning up images...")
            
            # Find and delete all image files
            image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif']
            deleted_count = 0
            
            for ext in image_extensions:
                image_files = glob.glob(os.path.join(CAMERA_DIRECTORY, ext))
                image_files += glob.glob(os.path.join(CAMERA_DIRECTORY, '**', ext), recursive=True)
                
                for img_file in image_files:
                    try:
                        os.remove(img_file)
                        deleted_count += 1
                    except Exception as e:
                        print(f"Error deleting {img_file}: {e}")
            
            print(f"Deleted {deleted_count} image files from camera directory")
        else:
            print(f"Camera directory size is below {CAMERA_SIZE_THRESHOLD_GB}GB threshold, no cleanup needed")
    
    except Exception as e:
        print(f"Error checking camera directory size: {e}")

def run_maintenance():
    """Main maintenance function that runs all checks"""
    try:
        print("Starting system maintenance checks")
        
        # First try the Python method for log files
        large_files = check_large_files(LOG_DIRECTORY)
        
        # If no files were found or truncated, try the system command as backup
        if not large_files:
            truncate_large_system_logs()
        
        # Check camera directory size and clean up if needed
        check_camera_directory_size()
        
        print("Maintenance checks completed")
    except Exception as e:
        print(f"Error in maintenance routine: {e}")

def main():
    """Main function to run the maintenance script"""
    print("Starting log truncation and camera directory monitoring service")
    
    while True:
        try:
            #run_maintenance()
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