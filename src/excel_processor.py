import pandas as pd
import os
from pathlib import Path

from .betting_framework import user_input_betting_framework
from config import (
    INPUT_DIR, 
    OUTPUT_DIR, 
    DEFAULT_SAMPLE_FILE, 
    DEFAULT_SHEET_NAME, 
    MAX_COLUMN_WIDTH, 
    COLUMN_PADDING, 
    COMMISSION_PER_CONTRACT
)

# Centralized column configuration
COLUMN_CONFIG = {
    # Internal input columns (used for Excel reading and validation)
    'Game': {
        'explanation': 'The game or matchup being analyzed (e.g., "Lakers vs Warriors")',
        'format_type': None,
        'is_input': True
    },
    'Model Win Percentage': {
        'explanation': 'Your model\'s predicted win probability (0-100 or 0-1). Input as either 68 (for 68%) or 0.68.',
        'format_type': None,  # Raw input, not formatted in Excel
        'is_input': True,
        'display_name': 'Win %'
    },
    'Model Margin': {
        'explanation': 'Your model\'s predicted margin of victory (optional field for reference only)',
        'format_type': None,
        'is_input': True,
        'display_name': 'Margin'
    },
    'Contract Price': {
        'explanation': 'The price per contract from the sportsbook (e.g., 0.27 for 27 cents, or 27 for 27 cents)',
        'format_type': None,  # Raw input, not formatted in Excel
        'is_input': True,
        'display_name': 'Contract Price (¢)'
    },
    # Display output columns (used in results)
    'Win %': {
        'explanation': 'Your model\'s predicted probability (converted to decimal format for Excel)',
        'format_type': 'percentage',
        'is_input': False
    },
    'Contract Price (¢)': {
        'explanation': 'The input contract price (displayed as entered)',
        'format_type': None,
        'is_input': False
    },
    'Margin': {
        'explanation': 'Your model\'s predicted margin of victory (optional)',
        'format_type': None,
        'is_input': False
    },
    'EV Percentage': {
        'explanation': 'Expected Value percentage - how much profit you expect per dollar wagered. Must be ≥10% (Wharton threshold)',
        'format_type': 'percentage',
        'is_input': False
    },
    'Net Profit': {
        'explanation': 'Total profit you\'ll receive IF this bet wins (what you actually get back minus your stake)',
        'format_type': 'currency',
        'is_input': False
    },
    'Expected Value EV': {
        'explanation': 'Expected profit in dollars accounting for win/loss probability (long-term average over many bets)',
        'format_type': 'currency',
        'is_input': False
    },
    'Decision': {
        'explanation': 'Framework recommendation: BET (meets all criteria) or NO BET (fails Wharton requirements)',
        'format_type': None,
        'is_input': False
    },
    'Final Recommendation': {
        'explanation': 'Final decision after bankroll allocation (may be PARTIAL BET or SKIP if insufficient funds)',
        'format_type': None,
        'is_input': False
    },
    'Bet Amount': {
        'explanation': 'Actual recommended bet amount in dollars, adjusted for whole contracts only (Robinhood constraint)',
        'format_type': 'currency',
        'is_input': False
    },
    'Cumulative Bet Amount': {
        'explanation': 'Actual allocated amount after considering total weekly bankroll constraints',
        'format_type': 'currency',
        'is_input': False
    },
    'Bet Percentage': {
        'explanation': 'Percentage of your weekly bankroll this bet represents (capped at 15% maximum)',
        'format_type': 'percentage',
        'is_input': False
    },
    'Contracts To Buy': {
        'explanation': 'Number of whole contracts to purchase (rounded down from optimal Kelly amount)',
        'format_type': None,
        'is_input': False
    },
    'Adjusted Price': {
        'explanation': 'Total cost per contract including commission (contract price + $0.02)',
        'format_type': 'currency',
        'is_input': False
    },
    'Target Bet Amount': {
        'explanation': 'Original Kelly/Wharton calculated bet amount before whole contract adjustment',
        'format_type': 'currency',
        'is_input': False
    },
    'Unused Amount': {
        'explanation': 'Money left over due to whole contract constraint (difference between target and actual)',
        'format_type': 'currency',
        'is_input': False
    },
    'Reason': {
        'explanation': 'Explanation for NO BET decisions (e.g., "EV below 10% threshold", "Negative Kelly")',
        'format_type': None,
        'is_input': False
    }
}

# Quick view column mapping (original -> shortened)
QUICK_VIEW_MAPPING = {
    'Game': 'Game',
    'Win %': 'Win %',
    'Contract Price (¢)': 'Price (¢)',
    'EV Percentage': 'Edge %',
    'Expected Value EV': 'EV $',
    'Adjusted Price': 'Contract Cost',
    'Cumulative Bet Amount': 'Allocated $',
    'Net Profit': 'Win Profit $',
    'Contracts To Buy': 'Contracts',
    'Bet Percentage': 'Stake % Bankroll',
    'Final Recommendation': 'Final',
    'Reason': 'Reason'
}

def get_required_input_columns():
    """Get list of required input columns from COLUMN_CONFIG."""
    return [col for col, config in COLUMN_CONFIG.items() 
            if config.get('is_input', False) and col != 'Model Margin']  # Model Margin is optional

def apply_excel_formatting(worksheet, df, format_mapping=None):
    """Apply formatting to Excel worksheet based on column types."""
    from openpyxl.comments import Comment
    from openpyxl.styles import Alignment
    
    # Use COLUMN_CONFIG if no custom mapping provided
    config = format_mapping or COLUMN_CONFIG
    
    for col_name, col_config in config.items():
        if col_name in df.columns:
            col_idx = df.columns.get_loc(col_name) + 1
            col_letter = worksheet.cell(row=1, column=col_idx).column_letter
            
            # Apply number formatting based on type
            format_type = col_config.get('format_type')
            if format_type == 'percentage':
                for row in range(2, len(df) + 2):
                    worksheet[f"{col_letter}{row}"].number_format = '0.00%'
            elif format_type == 'currency':
                for row in range(2, len(df) + 2):
                    worksheet[f"{col_letter}{row}"].number_format = '$0.00'
            
            # Apply text alignment for specific columns (Quick View sheet)
            if col_name in ['Final', 'Reason']:
                for row in range(1, len(df) + 2):  # Include header row
                    cell = worksheet[f"{col_letter}{row}"]
                    cell.alignment = Alignment(horizontal='right')
            
            # Add explanatory comment to header
            if 'explanation' in col_config:
                header_cell = worksheet[f"{col_letter}1"]
                comment = Comment(col_config['explanation'], "Wharton Betting Framework")
                comment.width = 300
                comment.height = 100
                header_cell.comment = comment

def adjust_column_widths(worksheet):
    """Auto-adjust column widths for better readability with appropriate sizing per column type."""
    
    # Define minimum and maximum widths for ALL column types (Quick View and Full Results)
    # Optimized for the new logical column organization
    column_width_rules = {
        # === INPUT COLUMNS ===
        'Game': {'min': 10, 'max': 25},  # Slightly wider for team names
        'Model Win Percentage': {'min': 15, 'max': 20},
        'Model Margin': {'min': 10, 'max': 15},
        'Contract Price': {'min': 12, 'max': 18},
        
        # === DISPLAY OUTPUT COLUMNS (Full Results Sheet) ===
        # Group 1: Game Identification & Input
        'Win %': {'min': 8, 'max': 10}, 
        'Contract Price (¢)': {'min': 12, 'max': 18},
        'Price (¢)': {'min': 8, 'max': 12},  # Quick View version
        'Margin': {'min': 8, 'max': 15},
        
        # Group 2: Profitability Analysis (key metrics)
        'EV Percentage': {'min': 10, 'max': 15},
        'Edge %': {'min': 8, 'max': 10},  # Quick View version
        'Expected Value EV': {'min': 10, 'max': 18},
        'EV $': {'min': 8, 'max': 12},  # Quick View version
        'Net Profit': {'min': 10, 'max': 15},
        'Win Profit $': {'min': 10, 'max': 15},  # Quick View version
        
        # Group 3: Bet Sizing Calculations (financial columns)
        'Target Bet Amount': {'min': 12, 'max': 18},  # Clear differentiation
        'Bet Amount': {'min': 10, 'max': 15},
        'Cumulative Bet Amount': {'min': 15, 'max': 22},  # Header is 20 chars - needs more space
        'Allocated $': {'min': 10, 'max': 15},  # Quick View version
        'Bet Percentage': {'min': 12, 'max': 18},
        'Stake % Bankroll': {'min': 12, 'max': 18},  # Quick View version
        'Unused Amount': {'min': 10, 'max': 15},
        
        # Group 4: Contract Implementation
        'Contracts To Buy': {'min': 10, 'max': 15},
        'Contracts': {'min': 8, 'max': 12},  # Quick View version
        'Adjusted Price': {'min': 10, 'max': 15},
        'Contract Cost': {'min': 10, 'max': 15},  # Quick View version
        
        # Group 5: Final Decisions (text columns - need more space)
        'Decision': {'min': 10, 'max': 16},
        'Final Recommendation': {'min': 15, 'max': 30},  # Wider for full text
        'Final': {'min': 8, 'max': 25},  # Quick View version
        'Reason': {'min': 15, 'max': 40},  # Wider for explanations
        
        # Default for any column not specified above
        'default': {'min': 8, 'max': 25}
    }
    
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        header_name = str(column[0].value) if column[0].value else ""
        
        # Calculate the actual content width needed
        for cell in column:
            try:
                cell_length = len(str(cell.value)) if cell.value is not None else 0
                if cell_length > max_length:
                    max_length = cell_length
            except:
                pass
        
        # Get the width rules for this column (use default if not found)
        rules = column_width_rules.get(header_name, column_width_rules['default'])
        
        # Calculate optimal width: content + padding, within min/max bounds
        content_width = max_length + COLUMN_PADDING
        optimal_width = max(rules['min'], min(content_width, rules['max']))
        
        worksheet.column_dimensions[column_letter].width = optimal_width

def list_available_input_files():
    """List all Excel files in the input directory."""
    excel_files = list(INPUT_DIR.glob("*.xlsx"))
    return [f.name for f in excel_files if not f.name.startswith("~")]  # Exclude temp files

def get_input_file_path(filename):
    """Get full path for an input file."""
    return INPUT_DIR / filename

def create_sample_excel_in_input_dir():
    """Create a sample Excel file in the input directory."""
    sample_data = {
        'Game': [
            'Lakers vs Warriors',
            'Cowboys vs Giants', 
            'Yankees vs Red Sox',
            'Chiefs vs Bills',
            'Celtics vs Heat',
            'Dodgers vs Padres'
        ],
        'Model Win Percentage': [68, 72, 55, 75, 63, 58],
        'Model Margin': [3.5, 7.2, 1.8, 10.5, 4.1, 2.3],
        'Contract Price': [45, 0.40, 52, 0.35, 48, 0.51]  # Mixed format: cents and dollars
    }
    
    df = pd.DataFrame(sample_data)
    sample_file_path = INPUT_DIR / DEFAULT_SAMPLE_FILE
    df.to_excel(sample_file_path, sheet_name=DEFAULT_SHEET_NAME, index=False)
    print(f"Sample Excel file created: {sample_file_path}")
    return sample_file_path

def process_betting_excel(excel_file_path, weekly_bankroll, sheet_name=DEFAULT_SHEET_NAME):
    """
    Process an Excel file with game data through the betting framework.
    
    Expected Excel columns (in this order):
    - Game: Game identifier (e.g., "Team A vs Team B")
    - Model Win Percentage: Your model's win probability (0-100 or 0-1)
    - Model Margin: Optional predicted margin (for reference)
    - Contract Price: Price per unit from sportsbook (dollars or cents)
                     Examples: 0.27 or 27 (both represent 27 cents)
    
    The script will add these columns:
    - Decision: BET or NO BET
    - EV Percentage: Expected value percentage
    - Bet Amount: Actual bet amount (adjusted for whole contracts)
    - Bet Percentage: Percentage of bankroll
    - Net Profit: Profit if bet wins (what you actually win)
    - Expected Value EV: Expected value in dollars (long-term average)
    - Contracts_To_Buy: Number of whole contracts to purchase
    - Target_Bet_Amount: Original Kelly/Wharton recommended amount
    - Unused_Amount: Amount unused due to whole contract constraint
    - Reason: Reason for NO BET decisions
    - Final_Recommendation: After bankroll allocation
    """
    
    try:
        # Read the Excel file
        print(f"Reading Excel file: {excel_file_path}")
        df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
        print(f"Found {len(df)} games to analyze")
        
        # Validate required columns using centralized config
        required_columns = get_required_input_columns()
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Process each game through the betting framework
        results = []
        for index, row in df.iterrows():
            game = row['Game']
            win_pct = row['Model Win Percentage']
            contract_price = row['Contract Price']
            
            # Handle margin value - check if column exists and has non-null value
            win_margin = None
            if 'Model Margin' in df.columns:
                margin_val = row.get('Model Margin', None)
                # Only use the value if it's not null/nan
                if pd.notna(margin_val):
                    win_margin = margin_val
            
            print(f"Processing: {game}")
            
            # Run through betting framework
            result = user_input_betting_framework(
                weekly_bankroll=weekly_bankroll,
                model_win_percentage=win_pct,
                contract_price=contract_price,
                model_win_margin=win_margin,
                commission_per_contract=COMMISSION_PER_CONTRACT
            )
            
            # Calculate Net Profit (what you win if bet hits, accounting for total cost)
            net_profit = 0
            if result['decision'] == 'BET':
                contracts = result.get('contracts_to_buy', 0)
                adjusted_price = result.get('adjusted_price', 0)
                total_cost = contracts * adjusted_price
                payout_if_win = contracts * 1.0  # $1 per contract if win
                net_profit = payout_if_win - total_cost
            
            # Store results using final column names directly
            result_row = {
                'Game': game,
                'Win %': win_pct / 100 if win_pct > 1 else win_pct,  # Convert to decimal if > 1
                'Contract Price (¢)': contract_price,
                'Decision': result['decision'],
                'EV Percentage': result['ev_percentage'] / 100,  # Store as decimal for Excel formatting
                'Bet Amount': result['bet_amount'],
                'Bet Percentage': result.get('bet_percentage', 0) / 100,  # Store as decimal for Excel formatting
                'Net Profit': net_profit,
                'Expected Value EV': result.get('expected_profit', 0),
                'Contracts To Buy': result.get('contracts_to_buy', 0),
                'Adjusted Price': result.get('adjusted_price', 0),
                'Target Bet Amount': result.get('target_bet_amount', result['bet_amount']),
                'Unused Amount': result.get('unused_amount', 0),
                'Reason': result.get('reason', ''),
                'Final Recommendation': '',  # Will be filled by allocation logic
                'Cumulative Bet Amount': 0.0   # Will be filled by allocation logic
            }
            
            # Only add Margin column if we have margin data
            if win_margin is not None:
                result_row['Margin'] = win_margin
            
            results.append(result_row)
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        # Sort by EV percentage (highest first) for bet allocation
        results_df = results_df.sort_values('EV Percentage', ascending=False).reset_index(drop=True)
        
        # Apply bankroll allocation logic
        results_df = apply_bankroll_allocation(results_df, weekly_bankroll)
        
        # Reorder columns for improved readability (inputs -> core metrics -> decisions -> sizing diagnostics -> notes)
        # Only include Margin column if input data had margin values
        has_margin_data = 'Model Margin' in df.columns and not df['Model Margin'].isnull().all()
        
        # Logically organized column order for better analysis flow
        preferred_order = [
            # GROUP 1: Game Identification & Input Data
            'Game', 'Win %', 'Contract Price (¢)',
        ]
        if has_margin_data:
            preferred_order.append('Margin')
        
        preferred_order.extend([
            # GROUP 2: Profitability Analysis (core betting metrics)
            'EV Percentage', 'Expected Value EV', 'Net Profit',
            
            # GROUP 3: Bet Sizing Calculations (Kelly → Adjustment → Allocation)
            'Target Bet Amount',        # Original Kelly calculation
            'Bet Amount',              # After whole contract adjustment  
            'Cumulative Bet Amount',   # After bankroll allocation
            'Bet Percentage',          # % of bankroll
            'Unused Amount',           # Money left due to whole contract constraint
            
            # GROUP 4: Contract Implementation Details
            'Contracts To Buy', 'Adjusted Price',
            
            # GROUP 5: Final Decisions & Explanations
            'Decision', 'Final Recommendation', 'Reason'
        ])
        
        # Reorder columns, keeping any extra columns at the end
        existing_cols = [c for c in preferred_order if c in results_df.columns]
        remaining_cols = [c for c in results_df.columns if c not in existing_cols]
        results_df = results_df[existing_cols + remaining_cols]

        # Save results back to Excel in output directory
        input_file = Path(excel_file_path)
        output_file = OUTPUT_DIR / f"{input_file.stem}_RESULTS.xlsx"
        print(f"\nSaving results to: {output_file}")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Create simplified quick-view sheet FIRST using centralized mapping
            quick_cols = [col for col in QUICK_VIEW_MAPPING.keys() if col in results_df.columns]
            quick_df = results_df[quick_cols].copy().rename(columns=QUICK_VIEW_MAPPING)
            quick_df.to_excel(writer, sheet_name='Quick_View', index=False)
            
            # Apply formatting to quick view sheet
            quick_ws = writer.sheets['Quick_View']
            
            # Create format mapping for quick view columns with explanations
            quick_format_mapping = {
                'Game': {
                    'format_type': None,
                    'explanation': 'The game or matchup being analyzed (e.g., "Lakers vs Warriors")'
                },
                'Win %': {
                    'format_type': 'percentage',
                    'explanation': 'Your model\'s predicted probability that this team/outcome will win'
                },
                'Price (¢)': {
                    'format_type': None,
                    'explanation': 'Contract price from sportsbook (in cents or dollars)'
                },
                'Edge %': {
                    'format_type': 'percentage',
                    'explanation': 'Expected Value percentage - your edge over the market (must be ≥10% for Wharton threshold)'
                },
                'Stake $': {
                    'format_type': 'currency',
                    'explanation': 'Recommended bet amount (adjusted for whole contracts and safety constraints)'
                },
                'Allocated $': {
                    'format_type': 'currency',
                    'explanation': 'Actual amount allocated after considering total bankroll limits'
                },
                'Stake % Bankroll': {
                    'format_type': 'percentage',
                    'explanation': 'Percentage of your weekly bankroll this bet represents (capped at 15% maximum)'
                },
                'Win Profit $': {
                    'format_type': 'currency',
                    'explanation': 'Total profit you\'ll receive IF this bet wins (payout minus your stake)'
                },
                'EV $': {
                    'format_type': 'currency',
                    'explanation': 'Expected profit in dollars accounting for win/loss probability (long-term average)'
                },
                'Contracts': {
                    'format_type': None,
                    'explanation': 'Number of whole contracts to purchase (rounded down from optimal Kelly amount)'
                },
                'Contract Cost': {
                    'format_type': 'currency',
                    'explanation': 'Total cost per contract including $0.02 commission (contract price + commission)'
                },
                'Final': {
                    'format_type': None,
                    'explanation': 'Final recommendation after bankroll allocation (BET, PARTIAL BET, or SKIP)'
                },
                'Reason': {
                    'format_type': None,
                    'explanation': 'Explanation for NO BET decisions (e.g., "EV below 10% threshold")'
                }
            }
            
            apply_excel_formatting(quick_ws, quick_df, quick_format_mapping)
            adjust_column_widths(quick_ws)

            # Create detailed results sheet SECOND
            results_df.to_excel(writer, sheet_name='Betting_Results', index=False)
            
            # Apply formatting using helper function
            worksheet = writer.sheets['Betting_Results']
            apply_excel_formatting(worksheet, results_df)
            adjust_column_widths(worksheet)
        
        # Display summary
        display_summary(results_df, weekly_bankroll)
        
        return results_df, output_file
        
    except Exception as e:
        print(f"Error processing Excel file: {e}")
        return None, None

def apply_bankroll_allocation(df, weekly_bankroll):
    """
    Apply bankroll allocation logic to ensure total bets don't exceed weekly bankroll.
    Games are prioritized by EV percentage (highest first).
    """
    remaining_bankroll = weekly_bankroll
    cumulative_bet = 0
    
    for index, row in df.iterrows():
        if row['Decision'] == 'BET':
            if remaining_bankroll > 0:
                # Check if we can afford this bet
                bet_amount = row['Bet Amount']
                
                if bet_amount <= remaining_bankroll:
                    # Can afford full bet
                    df.loc[index, 'Final Recommendation'] = 'BET'
                    df.loc[index, 'Cumulative Bet Amount'] = float(bet_amount)
                    remaining_bankroll -= bet_amount
                    cumulative_bet += bet_amount
                else:
                    # Can't afford full bet - could do partial or skip
                    if remaining_bankroll >= (weekly_bankroll * 0.01):  # At least 1% of bankroll
                        df.loc[index, 'Final Recommendation'] = f'PARTIAL BET (${remaining_bankroll:.2f})'
                        df.loc[index, 'Cumulative Bet Amount'] = float(remaining_bankroll)
                        cumulative_bet += remaining_bankroll
                        remaining_bankroll = 0
                    else:
                        df.loc[index, 'Final Recommendation'] = 'SKIP - Insufficient Bankroll'
                        df.loc[index, 'Cumulative Bet Amount'] = 0.0
            else:
                # No bankroll remaining - skip all remaining BET decisions
                df.loc[index, 'Final Recommendation'] = 'SKIP - Insufficient Bankroll'
                df.loc[index, 'Cumulative Bet Amount'] = 0.0
        else:
            # Non-BET decisions (e.g., 'NO BET') pass through unchanged
            df.loc[index, 'Final Recommendation'] = row['Decision']
            df.loc[index, 'Cumulative Bet Amount'] = 0.0
    
    return df

def display_summary(df, weekly_bankroll):
    """Display a summary of the betting analysis"""
    print("\n" + "="*60)
    print("BETTING ANALYSIS SUMMARY")
    print("="*60)
    
    total_games = len(df)
    bet_opportunities = len(df[df['Decision'] == 'BET'])
    no_bet_games = len(df[df['Decision'] == 'NO BET'])
    final_bets = len(df[df['Final Recommendation'] == 'BET'])
    
    total_allocated = df['Cumulative Bet Amount'].sum()
    total_expected_profit = df[df['Final Recommendation'] == 'BET']['Expected Value EV'].sum()
    
    print(f"Total Games Analyzed: {total_games}")
    print(f"Initial BET Opportunities: {bet_opportunities}")
    print(f"NO BET Games: {no_bet_games}")
    print(f"Final Recommended Bets: {final_bets}")
    print(f"Weekly Bankroll: ${weekly_bankroll:.2f}")
    print(f"Total Allocated: ${total_allocated:.2f}")
    print(f"Remaining Bankroll: ${weekly_bankroll - total_allocated:.2f}")
    print(f"Total Expected Profit: ${total_expected_profit:.2f}")
    
    if final_bets > 0:
        print(f"\nTOP 5 RECOMMENDED BETS (by EV%):")
        print("-" * 40)
        top_bets = df[df['Final Recommendation'] == 'BET'].head()
        for _, row in top_bets.iterrows():
            ev_pct = row['EV Percentage'] * 100  # Convert back to percentage for display
            print(f"{row['Game']}: ${row['Cumulative Bet Amount']:.2f} (EV: {ev_pct:.2f}%)")

def create_sample_excel():
    """Legacy function - redirects to new create_sample_excel_in_input_dir()"""
    return create_sample_excel_in_input_dir()