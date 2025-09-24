#!/usr/bin/env python3
"""
Quick Analysis Runner

Simple script to run the macro announcement effects analysis with common configurations.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🚀 {description}")
    print(f"📝 Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Success!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def main():
    """Main runner function."""
    print("=" * 60)
    print("📊 MACRO ANNOUNCEMENT EFFECTS - QUICK RUNNER")
    print("=" * 60)
    
    project_root = Path(__file__).parent
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
    else:
        print("⚠️  No virtual environment detected - consider using one")
    
    # Check if main.py exists
    main_script = project_root / "main.py"
    if not main_script.exists():
        print("❌ main.py not found!")
        return
    
    print(f"📁 Working directory: {project_root}")
    
    # Menu options
    print("\n📋 Analysis Options:")
    print("1. 🎯 Run full analysis (recommended)")
    print("2. 📊 Collect data only")
    print("3. 🔍 Run analysis only (requires existing data)")
    print("4. 📅 Run with custom date range")
    print("5. 🔧 Quick test run (last 6 months)")
    print("6. ❌ Exit")
    
    while True:
        try:
            choice = input("\n➡️  Select option (1-6): ").strip()
            
            if choice == "1":
                # Full analysis
                cmd = [sys.executable, str(main_script)]
                if run_command(cmd, "Running full analysis"):
                    print("\n🎉 Full analysis completed! Check the results/ directory.")
                break
                
            elif choice == "2":
                # Data only
                cmd = [sys.executable, str(main_script), "--data-only"]
                if run_command(cmd, "Collecting and preprocessing data"):
                    print("\n✅ Data collection completed! Data saved to data/ directory.")
                break
                
            elif choice == "3":
                # Analysis only
                cmd = [sys.executable, str(main_script), "--analysis-only"]
                if run_command(cmd, "Running analysis on existing data"):
                    print("\n✅ Analysis completed! Check the results/ directory.")
                break
                
            elif choice == "4":
                # Custom date range
                start_date = input("📅 Enter start date (YYYY-MM-DD) or press Enter for default: ").strip()
                end_date = input("📅 Enter end date (YYYY-MM-DD) or press Enter for default: ").strip()
                
                cmd = [sys.executable, str(main_script)]
                if start_date:
                    cmd.extend(["--start-date", start_date])
                if end_date:
                    cmd.extend(["--end-date", end_date])
                
                if run_command(cmd, f"Running analysis with custom date range"):
                    print("\n🎉 Custom analysis completed! Check the results/ directory.")
                break
                
            elif choice == "5":
                # Quick test run
                from datetime import datetime, timedelta
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
                
                cmd = [sys.executable, str(main_script), "--start-date", start_date, "--end-date", end_date]
                if run_command(cmd, f"Running quick test (last 6 months: {start_date} to {end_date})"):
                    print("\n🎉 Quick test completed! Check the results/ directory.")
                break
                
            elif choice == "6":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please select 1-6.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()