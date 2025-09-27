#!/usr/bin/env python3
"""Wharton Betting Framework - Main Interface"""

import sys
from pathlib import Path

# Add parent directory to path for config imports
sys.path.append(str(Path(__file__).parent.parent))

from betting_framework import user_input_betting_framework
from excel_processor import (
    process_betting_excel, 
    create_sample_excel_in_input_dir, 
    list_available_input_files,
    get_input_file_path
)
from config.settings import INPUT_DIR, OUTPUT_DIR

def interactive_single_bet():
    """Interactive mode for single bet analysis"""
    print("Single Bet Analysis")
    print("-" * 30)
    
    try:
        weekly_bankroll = float(input("Enter your weekly bankroll ($): "))
        model_win_percentage = float(input("Enter your model's win percentage (0-1 or 0-100): "))
        contract_price = float(input("Enter the contract price (e.g., 0.27 or 27 for 27 cents): "))
        
        margin_input = input("Enter predicted margin (optional, press Enter to skip): ")
        model_win_margin = float(margin_input) if margin_input.strip() else None
        
        result = user_input_betting_framework(
            weekly_bankroll=weekly_bankroll,
            model_win_percentage=model_win_percentage,
            contract_price=contract_price,
            model_win_margin=model_win_margin
        )
        
        print("\n" + "=" * 40)
        print("BETTING RECOMMENDATION")
        print("=" * 40)
        print(f"Decision: {result['decision']}")
        
        if result['decision'] == 'NO BET':
            print(f"Reason: {result['reason']}")
        else:
            print(f"Bet Amount: ${result['bet_amount']:.2f}")
            print(f"Bet Percentage: {result['bet_percentage']:.1f}% of bankroll")
            print(f"Contracts to Buy: {result['contracts_to_buy']} (whole contracts only)")
            print(f"Expected Profit: ${result['expected_profit']:.2f}")
            
            # Show whole contract adjustment info if available
            if 'target_bet_amount' in result and 'unused_amount' in result:
                target_amount = result['target_bet_amount']
                unused_amount = result['unused_amount']
                if unused_amount > 0.01:  # Only show if meaningful unused amount
                    print(f"Original Target: ${target_amount:.2f}")
                    print(f"Unused Amount: ${unused_amount:.2f} (due to whole contract constraint)")
        
        print(f"Expected Value: {result['ev_percentage']:.1f}%")
        
    except ValueError as e:
        print(f"Error: Please enter valid numeric values. {e}")
    except Exception as e:
        print(f"Error: {e}")

def excel_batch_mode():
    """Excel batch processing mode with improved file handling"""
    print("Excel Batch Processing")
    print("-" * 30)
    
    # Check for existing files in input directory
    available_files = list_available_input_files()
    
    if not available_files:
        print("No Excel files found in data/input/ directory.")
        create_sample = input("Create sample Excel file? (y/n): ").lower().strip() == 'y'
        if create_sample:
            sample_file = create_sample_excel_in_input_dir()
            print(f"\nSample file created: {sample_file}")
            print("You can edit this file with your actual game data, then run this option again.")
            return
        else:
            print("Please add Excel files to the data/input/ directory and try again.")
            return
    
    # Display available files
    print(f"\nAvailable Excel files in data/input/:")
    for i, filename in enumerate(available_files, 1):
        print(f"{i}. {filename}")
    
    print(f"{len(available_files) + 1}. Create new sample file")
    print(f"{len(available_files) + 2}. Use custom file path")
    
    try:
        choice = int(input(f"\nSelect file (1-{len(available_files) + 2}): "))
        
        if choice == len(available_files) + 1:
            # Create sample file
            sample_file = create_sample_excel_in_input_dir()
            print(f"\nSample file created: {sample_file}")
            return
        elif choice == len(available_files) + 2:
            # Custom file path
            excel_file = input("Enter full path to Excel file: ").strip().strip('\"')
            if not Path(excel_file).exists():
                print(f"Error: File not found: {excel_file}")
                return
        else:
            # Selected file from list
            if 1 <= choice <= len(available_files):
                selected_file = available_files[choice - 1]
                excel_file = get_input_file_path(selected_file)
                print(f"Selected: {selected_file}")
            else:
                print("Invalid selection.")
                return
        
    except ValueError:
        print("Error: Please enter a valid number")
        return
    
    try:
        weekly_bankroll = float(input("Enter weekly bankroll ($): "))
    except ValueError:
        print("Error: Please enter a valid number for bankroll")
        return
    
    results_df, output_file = process_betting_excel(excel_file, weekly_bankroll)
    
    if results_df is not None:
        print(f"\nProcessing complete! Results saved to: {output_file}")
        print(f"Results location: {OUTPUT_DIR}")
        print("\nOpen the _RESULTS.xlsx file to see detailed analysis and rankings!")
    else:
        print("Processing failed. Please check your Excel file format.")

def main():
    """Main application interface"""
    print("\n" + "=" * 50)
    print("   WHARTON BETTING FRAMEWORK")
    print("=" * 50)
    print(f"Input files: {INPUT_DIR}")
    print(f"Output files: {OUTPUT_DIR}")
    print("=" * 50)
    print("Choose an option:")
    print("1. Excel Batch Processing (multiple games)")
    print("2. Single Bet Analysis (interactive)")
    print("3. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == '1':
                excel_batch_mode()
                break
            elif choice == '2':
                interactive_single_bet()
                break
            elif choice == '3':
                print("Goodbye!")
                break
            else:
                print("Please enter 1, 2, or 3")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    main()
