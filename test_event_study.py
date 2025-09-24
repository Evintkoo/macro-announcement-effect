#!/usr/bin/env python3
"""
Quick test of the event study analysis.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path('.') / 'src'))

from analysis.event_study import EventStudyAnalyzer
from utils.helpers import setup_logging
import pandas as pd

def test_event_study():
    # Setup logging
    setup_logging('INFO', 'logs/test.log')

    # Load processed data
    data = pd.read_csv('data/processed/aligned_data.csv', index_col=0, parse_dates=True)
    print(f'Loaded data: {data.shape}')

    # Initialize analyzer
    analyzer = EventStudyAnalyzer()

    # Sample events
    sample_events = [
        pd.to_datetime('2022-03-16'), 
        pd.to_datetime('2022-06-15'), 
        pd.to_datetime('2023-03-22'),
        pd.to_datetime('2023-05-03')
    ]

    print(f'Testing with {len(sample_events)} events')
    results = analyzer.analyze_events(data, sample_events, event_window_days=2, estimation_window=50)
    
    if results and 'error' not in results:
        print('✅ Event study successful!')
        print(f'Results keys: {list(results.keys())}')
        
        if 'average_cumulative_abnormal_returns' in results:
            cars = results['average_cumulative_abnormal_returns']
            print(f'Average CARs shape: {cars.shape if not cars.empty else "Empty"}')
            if not cars.empty:
                print(f'CARs columns: {list(cars.columns)}')
                print(f'Final CARs:\n{cars.iloc[-1]}')
            
        return True
    else:
        print(f'❌ Event study failed: {results}')
        return False

if __name__ == "__main__":
    success = test_event_study()
    if success:
        print("\n🎯 Now testing visualization...")
        from visualization.plot_generator import PlotGenerator
        
        # Load results again for plotting
        analyzer = EventStudyAnalyzer()
        data = pd.read_csv('data/processed/aligned_data.csv', index_col=0, parse_dates=True)
        sample_events = [
            pd.to_datetime('2022-03-16'), 
            pd.to_datetime('2022-06-15'), 
            pd.to_datetime('2023-03-22')
        ]
        
        results = analyzer.analyze_events(data, sample_events, event_window_days=2, estimation_window=50)
        
        if results and 'error' not in results:
            plotter = PlotGenerator()
            try:
                plotter.plot_event_study_results(results)
                print("✅ Event study plots generated!")
            except Exception as e:
                print(f"❌ Plotting failed: {e}")
                import traceback
                traceback.print_exc()