#!/usr/bin/env python3
"""
PluG2 Metadata Statistics Analyzer
Extracts and analyzes statistics from the PluG2 linguistic corpus metadata.
"""

import pandas as pd
import numpy as np
from collections import Counter
import json
from datetime import datetime
import sys
import argparse


class MetadataStatistics:
    """Class for analyzing PluG2 metadata statistics"""
    
    def __init__(self, metadata_file='PluG2_metadata.psv'):
        """Initialize with metadata file path"""
        self.metadata_file = metadata_file
        self.df = None
        self.load_data()
    
    def load_data(self):
        """Load and preprocess the metadata file"""
        try:
            print(f"Loading metadata from {self.metadata_file}...")
            self.df = pd.read_csv(self.metadata_file, sep='|', low_memory=False)
            print(f"✓ Loaded {len(self.df):,} records")
            
            # Convert Publication Year to numeric
            self.df['Publication Year'] = pd.to_numeric(self.df['Publication Year'], errors='coerce')
            
            # Count valid publication years
            valid_years = self.df['Publication Year'].notna().sum()
            print(f"✓ Found {valid_years:,} records with valid publication years")
            
        except Exception as e:
            print(f"✗ Error loading metadata: {e}")
            sys.exit(1)
    
    def publication_year_statistics(self):
        """Analyze Publication Year statistics"""
        print("\n" + "="*60)
        print("PUBLICATION YEAR STATISTICS")
        print("="*60)
        
        # Filter out NaN values for analysis
        years = self.df['Publication Year'].dropna()
        
        if len(years) == 0:
            print("No valid publication years found!")
            return {}
        
        # Basic statistics
        stats = {
            'total_records_with_years': len(years),
            'total_records': len(self.df),
            'coverage_percentage': (len(years) / len(self.df)) * 100,
            'earliest_year': int(years.min()),
            'latest_year': int(years.max()),
            'year_range': int(years.max() - years.min()),
            'mean_year': round(years.mean(), 1),
            'median_year': int(years.median()),
            'mode_year': int(years.mode().iloc[0]) if not years.mode().empty else None
        }
        
        print(f"📊 BASIC STATISTICS:")
        print(f"   Total records with publication years: {stats['total_records_with_years']:,}")
        print(f"   Coverage: {stats['coverage_percentage']:.1f}% of all records")
        print(f"   Year range: {stats['earliest_year']} - {stats['latest_year']} ({stats['year_range']} years)")
        print(f"   Mean year: {stats['mean_year']}")
        print(f"   Median year: {stats['median_year']}")
        if stats['mode_year']:
            print(f"   Most common year: {stats['mode_year']}")
        
        # Year distribution
        year_counts = years.value_counts().sort_index()
        
        print(f"\n📈 YEAR DISTRIBUTION:")
        print(f"   Unique years: {len(year_counts)}")
        print(f"   Years with most publications:")
        
        top_years = year_counts.head(10)
        for year, count in top_years.items():
            print(f"      {int(year)}: {count:,} publications")
        
        # Decade analysis
        print(f"\n📅 DECADE ANALYSIS:")
        decades = {}
        for year in years:
            decade = int(year // 10 * 10)
            decades[decade] = decades.get(decade, 0) + 1
        
        decade_stats = []
        for decade in sorted(decades.keys()):
            decade_end = decade + 9
            count = decades[decade]
            percentage = (count / len(years)) * 100
            decade_stats.append({
                'decade': f"{decade}s",
                'decade_range': f"{decade}-{decade_end}",
                'count': count,
                'percentage': percentage
            })
            print(f"   {decade}s ({decade}-{decade_end}): {count:,} publications ({percentage:.1f}%)")
        
        # Century analysis
        print(f"\n🏛️ CENTURY ANALYSIS:")
        centuries = {}
        for year in years:
            century = int((year - 1) // 100 + 1)
            centuries[century] = centuries.get(century, 0) + 1
        
        century_stats = []
        for century in sorted(centuries.keys()):
            count = centuries[century]
            percentage = (count / len(years)) * 100
            century_name = self._get_century_name(century)
            century_stats.append({
                'century': century,
                'century_name': century_name,
                'count': count,
                'percentage': percentage
            })
            print(f"   {century_name} century: {count:,} publications ({percentage:.1f}%)")
        
        # Gaps and sparse periods
        print(f"\n🕳️ TEMPORAL GAPS:")
        all_years = set(range(stats['earliest_year'], stats['latest_year'] + 1))
        present_years = set(year_counts.index.astype(int))
        missing_years = sorted(all_years - present_years)
        
        if missing_years:
            print(f"   Years with no publications: {len(missing_years)}")
            if len(missing_years) <= 20:
                print(f"   Missing years: {missing_years}")
            else:
                print(f"   First 10 missing years: {missing_years[:10]}")
                print(f"   Last 10 missing years: {missing_years[-10:]}")
        else:
            print("   No gaps found - publications exist for every year in the range!")
        
        # Years with few publications
        sparse_threshold = max(1, int(np.percentile(year_counts.values, 10)))
        sparse_years = year_counts[year_counts <= sparse_threshold]
        
        if len(sparse_years) > 0:
            print(f"\n📉 SPARSE PUBLICATION YEARS (≤{sparse_threshold} publications):")
            print(f"   Number of sparse years: {len(sparse_years)}")
            if len(sparse_years) <= 15:
                for year, count in sparse_years.items():
                    print(f"      {int(year)}: {count} publication(s)")
        
        # Productivity periods
        print(f"\n🚀 PRODUCTIVITY PERIODS:")
        
        # Calculate moving averages for trend analysis
        if len(year_counts) >= 5:
            year_counts_df = year_counts.reset_index()
            year_counts_df.columns = ['Year', 'Count']
            year_counts_df['MA_5'] = year_counts_df['Count'].rolling(window=5, center=True).mean()
            
            # Find peak periods (5-year moving average)
            peak_threshold = np.percentile(year_counts_df['MA_5'].dropna(), 80)
            peak_periods = year_counts_df[year_counts_df['MA_5'] >= peak_threshold]
            
            if not peak_periods.empty:
                print(f"   High-productivity periods (5-year moving average ≥ {peak_threshold:.1f}):")
                for _, row in peak_periods.iterrows():
                    print(f"      {int(row['Year'])}: {row['Count']} publications (MA: {row['MA_5']:.1f})")
        
        # Store statistics for return
        stats.update({
            'year_distribution': year_counts.to_dict(),
            'decade_stats': decade_stats,
            'century_stats': century_stats,
            'missing_years': missing_years,
            'sparse_years': sparse_years.to_dict() if len(sparse_years) > 0 else {}
        })
        
        return stats
    
    def _get_century_name(self, century):
        """Convert century number to ordinal name"""
        ordinals = {
            1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th",
            6: "6th", 7: "7th", 8: "8th", 9: "9th", 10: "10th",
            11: "11th", 12: "12th", 13: "13th", 14: "14th", 15: "15th",
            16: "16th", 17: "17th", 18: "18th", 19: "19th", 20: "20th",
            21: "21st", 22: "22nd", 23: "23rd"
        }
        return ordinals.get(century, f"{century}th")
    
    def save_statistics(self, stats, output_file=None):
        """Save statistics to JSON file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"publication_year_stats_{timestamp}.json"
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            return obj
        
        converted_stats = convert_types(stats)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(converted_stats, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Statistics saved to: {output_file}")
        except Exception as e:
            print(f"✗ Error saving statistics: {e}")
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        print("\n" + "="*60)
        print("COMPREHENSIVE METADATA SUMMARY")
        print("="*60)
        
        print(f"📋 DATASET OVERVIEW:")
        print(f"   Total records: {len(self.df):,}")
        print(f"   Total columns: {len(self.df.columns)}")
        print(f"   File size: ~{self.metadata_file}")
        
        # Column completeness
        print(f"\n📊 DATA COMPLETENESS:")
        completeness = {}
        key_columns = ['Name', 'Publication Year', 'Genre Code', 'Author 1 Name', 
                      'Author 1 Sex', 'Publication City', 'Language Code']
        
        for col in key_columns:
            if col in self.df.columns:
                non_empty = self.df[col].notna().sum()
                percentage = (non_empty / len(self.df)) * 100
                completeness[col] = {'count': non_empty, 'percentage': percentage}
                print(f"   {col}: {non_empty:,}/{len(self.df):,} ({percentage:.1f}%)")
        
        return completeness


def main():
    """Main function to run the statistics analysis"""
    parser = argparse.ArgumentParser(description='Analyze PluG2 metadata statistics')
    parser.add_argument('--file', '-f', default='PluG2_metadata.psv',
                       help='Path to metadata file (default: PluG2_metadata.psv)')
    parser.add_argument('--output', '-o', help='Output JSON file for statistics')
    parser.add_argument('--summary', '-s', action='store_true',
                       help='Include general summary report')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = MetadataStatistics(args.file)
    
    # Generate summary if requested
    if args.summary:
        analyzer.generate_summary_report()
    
    # Analyze publication years
    pub_year_stats = analyzer.publication_year_statistics()
    
    # Save statistics if output file specified
    if args.output:
        analyzer.save_statistics(pub_year_stats, args.output)
    
    # print(f"\n🎉 Analysis complete!")
    # print(f"📈 Analyzed {pub_year_stats['total_records_with_years']:,} records with publication years")
    # print(f"📅 Time span: {pub_year_stats['year_range']} years ({pub_year_stats['earliest_year']}-{pub_year_stats['latest_year']})")
    print(retreive_all_publications_by_year(195, analyzer))

def retreive_all_publications_by_year(year, analyzer):
    """Retreive all publications by year"""
    return analyzer.df[analyzer.df['Publication Year'] == year].to_dict('records')


if __name__ == "__main__":
    main()
