#!/usr/bin/env python3
"""
Performance monitoring script for Project-Siesta
"""
import psutil
import time
import os
import sys
from datetime import datetime

def get_system_stats():
    """Get current system statistics"""
    stats = {
        'timestamp': datetime.now().isoformat(),
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory': psutil.virtual_memory()._asdict(),
        'disk': psutil.disk_usage('/')._asdict(),
        'network': psutil.net_io_counters()._asdict(),
        'processes': len(psutil.pids())
    }
    return stats

def format_bytes(bytes_value):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def print_stats(stats):
    """Print formatted system statistics"""
    print(f"\n{'='*60}")
    print(f"System Monitor - {stats['timestamp']}")
    print(f"{'='*60}")
    
    print(f"CPU Usage: {stats['cpu_percent']:.1f}%")
    
    memory = stats['memory']
    print(f"Memory: {memory['percent']:.1f}% used ({format_bytes(memory['used'])} / {format_bytes(memory['total'])})")
    
    disk = stats['disk']
    print(f"Disk: {disk['percent']:.1f}% used ({format_bytes(disk['used'])} / {format_bytes(disk['total'])})")
    
    network = stats['network']
    print(f"Network: RX {format_bytes(network['bytes_recv'])}, TX {format_bytes(network['bytes_sent'])}")
    
    print(f"Processes: {stats['processes']}")
    
    # Check for bot processes
    bot_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'bot' in cmdline or 'project-siesta' in cmdline:
                    bot_processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if bot_processes:
        print(f"\nBot Processes:")
        for proc in bot_processes:
            print(f"  PID {proc['pid']}: {' '.join(proc['cmdline'] or [])}")
    else:
        print(f"\nNo bot processes detected")

def check_bot_health():
    """Check if bot is running and healthy"""
    try:
        # Check if bot log file exists and is recent
        log_file = "./bot/bot_logs.log"
        if os.path.exists(log_file):
            stat = os.stat(log_file)
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            time_diff = datetime.now() - last_modified
            
            if time_diff.total_seconds() < 300:  # 5 minutes
                print("✅ Bot appears to be running (recent log activity)")
                return True
            else:
                print(f"⚠️  Bot may be inactive (last log: {time_diff.total_seconds():.0f}s ago)")
                return False
        else:
            print("❌ Bot log file not found")
            return False
    except Exception as e:
        print(f"❌ Error checking bot health: {e}")
        return False

def main():
    """Main monitoring loop"""
    print("🔍 Project-Siesta System Monitor")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            stats = get_system_stats()
            print_stats(stats)
            check_bot_health()
            
            print(f"\nNext update in 30 seconds...")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()