#!/usr/bin/env python3
"""Wharton Betting Framework - Main Interface"""

from pathlib import Path

from .betting_framework import user_input_betting_framework
from .excel_processor import (
    process_betting_excel, 
    create_sample_excel_in_input_dir, 
    list_available_input_files,
    get_input_file_path
)
from .commission_manager import commission_manager
from .config.settings import INPUT_DIR, OUTPUT_DIR

def interactive_single_bet() -> None:
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
        
        print("\n" + "=" * 50)
        print("BETTING RECOMMENDATION")
        print("=" * 50)
        
        # Commission Impact Section
        print("COMMISSION DETAILS:")
        print(f"  Platform: {commission_manager.get_current_platform()}")
        print(f"  Commission Rate: ${commission_manager.get_commission_rate():.2f} per contract")
        if 'adjusted_price' in result:
            print(f"  Contract Price: ${result['normalized_price']:.2f}")
            print(f"  Total Cost per Contract: ${result['adjusted_price']:.2f} (price + commission)")
        print("-" * 50)
        
        print(f"DECISION: {result['decision']}")
        
        if result['decision'] == 'NO BET':
            print(f"Reason: {result['reason']}")
            
            # Show commission impact details for NO BET decisions
            if 'commission_impact' in result and result['commission_impact'] > 0.1:
                print(f"\nCommission Impact Analysis:")
                print(f"  EV without commission: {result['ev_without_commission']:.1f}%")
                print(f"  EV with commission: {result['ev_percentage']:.1f}%")
                print(f"  Commission reduced EV by: {result['commission_impact']:.1f}%")
            
            if 'commission_increase_pct' in result and result['commission_increase_pct'] > 1:
                print(f"\nMinimum Bet Impact:")
                print(f"  Contract price alone: ${result['normalized_price']:.2f}")
                print(f"  With commission: ${result['adjusted_price']:.2f}")
                print(f"  Commission increases minimum bet by: {result['commission_increase_pct']:.0f}%")
                
        else:
            print(f"\nBET DETAILS:")
            print(f"  Bet Amount: ${result['bet_amount']:.2f}")
            print(f"  Bet Percentage: {result['bet_percentage']:.1f}% of bankroll")
            print(f"  Contracts to Buy: {result['contracts_to_buy']} (whole contracts only)")
            print(f"  Expected Profit: ${result['expected_profit']:.2f}")
            
            # Show commission impact on profitable bets
            if 'adjusted_price' in result:
                commission_cost = result['contracts_to_buy'] * commission_manager.get_commission_rate()
                print(f"\nCommission Impact:")
                print(f"  Total commission cost: ${commission_cost:.2f}")
                print(f"  Commission as % of bet: {(commission_cost / result['bet_amount']) * 100:.1f}%")
            
            # Show whole contract adjustment info if available
            if 'target_bet_amount' in result and 'unused_amount' in result:
                target_amount = result['target_bet_amount']
                unused_amount = result['unused_amount']
                if unused_amount > 0.01:  # Only show if meaningful unused amount
                    print(f"\nWhole Contract Adjustment:")
                    print(f"  Original Target: ${target_amount:.2f}")
                    print(f"  Actual Bet: ${result['bet_amount']:.2f}")
                    print(f"  Unused Amount: ${unused_amount:.2f} (due to whole contract constraint)")
        
        print(f"\nEXPECTED VALUE: {result['ev_percentage']:.1f}%")
        print("=" * 50)
        
    except ValueError as e:
        print(f"Error: Please enter valid numeric values. {e}")
    except Exception as e:
        print(f"Error: {e}")

def commission_configuration() -> None:
    """Interactive commission configuration interface"""
    print("Commission Configuration")
    print("-" * 30)
    
    # Show current settings
    current_platform = commission_manager.get_current_platform()
    current_rate = commission_manager.get_commission_rate()
    print(f"Current Platform: {current_platform}")
    print(f"Current Commission Rate: ${current_rate:.2f} per contract")
    print()
    
    # Show available platforms
    presets = commission_manager.get_platform_presets()
    print("Available Platforms:")
    platform_list = list(presets.keys())
    
    for i, platform in enumerate(platform_list, 1):
        rate = presets[platform]
        marker = " (current)" if platform == current_platform else ""
        print(f"{i}. {platform}: ${rate:.2f} per contract{marker}")
    
    print(f"{len(platform_list) + 1}. Custom rate")
    print(f"{len(platform_list) + 2}. Reset to default (Robinhood)")
    print(f"{len(platform_list) + 3}. Back to main menu")
    
    while True:
        try:
            choice = input(f"\nSelect option (1-{len(platform_list) + 3}): ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(platform_list):
                # Platform preset selected
                selected_platform = platform_list[choice_num - 1]
                if selected_platform == current_platform:
                    print(f"Already using {selected_platform}. No changes made.")
                else:
                    commission_manager.set_platform(selected_platform)
                    new_rate = commission_manager.get_commission_rate()
                    print(f"✓ Platform changed to {selected_platform} (${new_rate:.2f} per contract)")
                break
                
            elif choice_num == len(platform_list) + 1:
                # Custom rate
                while True:
                    try:
                        rate_input = input("Enter custom commission rate per contract ($): $").strip()
                        custom_rate = float(rate_input)
                        commission_manager.set_commission_rate(custom_rate, "Custom")
                        print(f"✓ Custom commission rate set to ${custom_rate:.2f} per contract")
                        break
                    except ValueError as e:
                        if "Commission rate must be between" in str(e):
                            print(f"Error: {e}")
                        else:
                            print("Error: Please enter a valid number")
                    except Exception as e:
                        print(f"Error: {e}")
                break
                
            elif choice_num == len(platform_list) + 2:
                # Reset to default
                if current_platform == "Robinhood" and current_rate == 0.02:
                    print("Already using default settings. No changes made.")
                else:
                    commission_manager.reset_to_default()
                    print("✓ Commission settings reset to default (Robinhood: $0.02 per contract)")
                break
                
            elif choice_num == len(platform_list) + 3:
                # Back to main menu
                print("Returning to main menu...")
                break
                
            else:
                print(f"Please enter a number between 1 and {len(platform_list) + 3}")
                
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nReturning to main menu...")
            break
        except Exception as e:
            print(f"Error: {e}")

def excel_batch_mode() -> None:
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
        
        # Show commission impact summary
        commission_rate = commission_manager.get_commission_rate()
        platform = commission_manager.get_current_platform()
        print(f"\nCommission Impact Summary:")
        print(f"  Platform used: {platform}")
        print(f"  Commission rate: ${commission_rate:.2f} per contract")
        
        if commission_rate > 0 and hasattr(results_df, 'columns') and hasattr(results_df.columns, '__contains__'):
            try:
                if 'Final Recommendation' in results_df.columns and 'Contracts To Buy' in results_df.columns:
                    total_contracts = results_df[results_df['Final Recommendation'] == 'BET']['Contracts To Buy'].sum()
                    total_commission = total_contracts * commission_rate
                    if total_commission > 0:
                        print(f"  Total commission cost: ${total_commission:.2f}")
                        print(f"  Commission-related columns are highlighted in yellow")
            except (TypeError, AttributeError):
                # Handle cases where results_df is a Mock or doesn't have expected structure
                pass
        
        print("\nOpen the _RESULTS.xlsx file to see detailed analysis and rankings!")
        print("• Quick_View sheet: Simplified results with commission impact")
        print("• Betting_Results sheet: Full details with commission analysis")
    else:
        print("Processing failed. Please check your Excel file format.")

def display_main_menu() -> None:
    """Display the main menu header and options"""
    print("\n" + "=" * 50)
    print("   WHARTON BETTING FRAMEWORK")
    print("=" * 50)
    print(f"Input files: {INPUT_DIR}")
    print(f"Output files: {OUTPUT_DIR}")
    print("-" * 50)
    # Show current commission settings prominently
    current_platform = commission_manager.get_current_platform()
    current_rate = commission_manager.get_commission_rate()
    print("COMMISSION SETTINGS:")
    print(f"  Platform: {current_platform}")
    print(f"  Rate: ${current_rate:.2f} per contract")
    if current_rate > 0:
        print(f"  Impact: Commission affects all bet calculations")
    else:
        print(f"  Impact: No commission fees (built into spread)")
    print("=" * 50)
    print("Choose an option:")
    print("1. Excel Batch Processing (multiple games)")
    print("2. Single Bet Analysis (interactive)")
    print("3. Commission Configuration")
    print("4. Exit")

def main() -> None:
    """Main application interface"""
    display_main_menu()
    
    while True:
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                excel_batch_mode()
                display_main_menu()
            elif choice == '2':
                interactive_single_bet()
                display_main_menu()
            elif choice == '3':
                commission_configuration()
                display_main_menu()
            elif choice == '4':
                print("Goodbye!")
                break
            else:
                print("Please enter 1, 2, 3, or 4")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    main()
