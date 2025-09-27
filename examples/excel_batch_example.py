#!/usr/bin/env python3
"""
Excel Batch Processing Example - Sports Betting Calculator Framework

This example demonstrates how to process multiple games from Excel files
and apply bankroll allocation logic.
"""

from pathlib import Path
import pandas as pd
import tempfile
import os

from src.excel_processor import process_betting_excel


def create_example_excel_data():
    """Create sample Excel data for demonstration"""
    return pd.DataFrame({
        'Game': [
            'Lakers vs Warriors',
            'Cowboys vs Giants', 
            'Yankees vs Red Sox',
            'Chiefs vs Bills',
            'Celtics vs Heat',
            'Low EV Game'
        ],
        'Model Win Percentage': [68.0, 75.0, 55.0, 80.0, 63.0, 52.0],
        'Contract Price': [0.45, 0.20, 0.50, 0.10, 0.48, 0.49],
        'Model Margin': [5.5, 8.2, 2.1, 15.3, 4.1, 1.2]
    })


def excel_batch_processing_example():
    """Demonstrate Excel batch processing with bankroll allocation"""
    print("=== Excel Batch Processing Example ===\n")
    
    # Create sample data
    sample_data = create_example_excel_data()
    print("Created sample data with 6 games:")
    print(sample_data[['Game', 'Model Win Percentage', 'Contract Price']].to_string(index=False))
    print()
    
    # Create temporary Excel file
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        sample_data.to_excel(tmp.name, sheet_name='Games', index=False)
        temp_file = tmp.name
    
    try:
        # Process with different bankroll amounts to show allocation logic
        bankrolls = [50, 100, 200]
        
        for bankroll in bankrolls:
            print(f"Processing with ${bankroll} bankroll:")
            print("-" * 40)
            
            # Create temporary output directory
            with tempfile.TemporaryDirectory() as temp_output_dir:
                # Mock the OUTPUT_DIR for this example
                import excel_processor
                original_output_dir = excel_processor.OUTPUT_DIR
                excel_processor.OUTPUT_DIR = Path(temp_output_dir)
                
                try:
                    result_df, output_file = process_betting_excel(temp_file, bankroll)
                    
                    if result_df is not None:
                        # Show key results
                        print("Results Summary:")
                        total_allocated = result_df['Cumulative Bet Amount'].sum()
                        bet_count = len(result_df[result_df['Final Recommendation'] == 'BET'])
                        
                        print(f"  Total Allocated: ${total_allocated:.2f}")
                        print(f"  Remaining: ${bankroll - total_allocated:.2f}")
                        print(f"  Games with BET recommendation: {bet_count}")
                        
                        # Show individual recommendations
                        print("\n  Game Recommendations:")
                        for _, row in result_df.head(3).iterrows():  # Show top 3
                            game = row['Game']
                            ev = row['EV Percentage'] * 100  # Convert back to percentage
                            recommendation = row['Final Recommendation']
                            allocated = row['Cumulative Bet Amount']
                            
                            print(f"    {game}: {recommendation}")
                            print(f"      EV: {ev:.1f}%, Allocated: ${allocated:.2f}")
                        
                        if len(result_df) > 3:
                            print(f"    ... and {len(result_df) - 3} more games")
                    
                    print()
                
                finally:
                    # Restore original OUTPUT_DIR
                    excel_processor.OUTPUT_DIR = original_output_dir
    
    finally:
        # Clean up temporary file
        os.unlink(temp_file)


def demonstrate_bankroll_allocation_priority():
    """Show how games are prioritized by EV percentage"""
    print("=== Bankroll Allocation Priority Example ===\n")
    
    # Create data with clear EV hierarchy
    priority_data = pd.DataFrame({
        'Game': ['High EV Game', 'Medium EV Game', 'Low EV Game', 'Very Low EV'],
        'Model Win Percentage': [85.0, 70.0, 65.0, 55.0],
        'Contract Price': [0.15, 0.40, 0.45, 0.50],  # Different prices for different EVs
    })
    
    print("Testing priority allocation with limited bankroll:")
    print(priority_data.to_string(index=False))
    print()
    
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        priority_data.to_excel(tmp.name, sheet_name='Games', index=False)
        temp_file = tmp.name
    
    try:
        # Use small bankroll to force prioritization
        small_bankroll = 50
        
        with tempfile.TemporaryDirectory() as temp_output_dir:
            import excel_processor
            original_output_dir = excel_processor.OUTPUT_DIR
            excel_processor.OUTPUT_DIR = Path(temp_output_dir)
            
            try:
                result_df, _ = process_betting_excel(temp_file, small_bankroll)
                
                if result_df is not None:
                    print(f"With ${small_bankroll} bankroll, priority allocation:")
                    print()
                    
                    for _, row in result_df.iterrows():
                        game = row['Game']
                        ev = row['EV Percentage'] * 100
                        recommendation = row['Final Recommendation']
                        allocated = row['Cumulative Bet Amount']
                        
                        status = "✓" if recommendation == 'BET' else "✗"
                        print(f"{status} {game}")
                        print(f"    EV: {ev:.1f}%, Status: {recommendation}")
                        if allocated > 0:
                            print(f"    Allocated: ${allocated:.2f}")
                        print()
            
            finally:
                excel_processor.OUTPUT_DIR = original_output_dir
    
    finally:
        os.unlink(temp_file)


def show_wharton_constraints_in_batch():
    """Demonstrate Wharton constraints in batch processing"""
    print("=== Wharton Constraints in Batch Processing ===\n")
    
    # Create data that will trigger various constraint responses
    constraint_data = pd.DataFrame({
        'Game': [
            'Wharton Compliant',
            'Below EV Threshold', 
            'High EV (Will be Capped)',
            'Marginal EV',
            'Very High EV'
        ],
        'Model Win Percentage': [68.0, 55.0, 95.0, 61.0, 90.0],
        'Contract Price': [0.45, 0.50, 0.05, 0.48, 0.10]
    })
    
    print("Testing various constraint scenarios:")
    print(constraint_data.to_string(index=False))
    print()
    
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        constraint_data.to_excel(tmp.name, sheet_name='Games', index=False)
        temp_file = tmp.name
    
    try:
        with tempfile.TemporaryDirectory() as temp_output_dir:
            import excel_processor
            original_output_dir = excel_processor.OUTPUT_DIR
            excel_processor.OUTPUT_DIR = Path(temp_output_dir)
            
            try:
                result_df, _ = process_betting_excel(temp_file, 100)
                
                if result_df is not None:
                    print("Constraint Analysis Results:")
                    print()
                    
                    for _, row in result_df.iterrows():
                        game = row['Game']
                        ev = row['EV Percentage'] * 100
                        decision = row['Decision']
                        bet_pct = row['Bet Percentage'] * 100
                        reason = row.get('Reason', '')
                        
                        print(f"Game: {game}")
                        print(f"  Expected Value: {ev:.1f}%")
                        print(f"  Decision: {decision}")
                        
                        if decision == 'BET':
                            print(f"  Bet Percentage: {bet_pct:.1f}% of bankroll")
                            if bet_pct >= 14.9:  # Close to 15% cap
                                print("  ⚠️  Capped at 15% maximum")
                        elif reason:
                            print(f"  Reason: {reason}")
                        
                        print()
            
            finally:
                excel_processor.OUTPUT_DIR = original_output_dir
    
    finally:
        os.unlink(temp_file)


if __name__ == "__main__":
    # Run all examples
    excel_batch_processing_example()
    demonstrate_bankroll_allocation_priority()
    show_wharton_constraints_in_batch()
    
    print("=" * 50)
    print("Excel examples complete!")
    print("\nKey Takeaways:")
    print("• Games are automatically ranked by Expected Value")
    print("• Higher EV games get bankroll allocation priority")
    print("• Wharton constraints (10% EV, 15% cap) are enforced")
    print("• Whole contract adjustments are automatically applied")
    print("• Commission costs ($0.02/contract) are included")
    print("\nTry the real Excel mode: python run.py → Option 1")