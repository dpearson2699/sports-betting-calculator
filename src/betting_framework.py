def normalize_contract_price(contract_price):
    """
    Normalize contract price to dollar format.
    
    Robinhood displays prices in cents, so this function allows users to input either:
    - Decimal format: 0.27 (for 27 cents)
    - Whole number format: 27 (for 27 cents)
    
    Args:
        contract_price: Price in either cents (whole number) or dollars (decimal)
        
    Returns:
        float: Price normalized to dollars (e.g., 0.27)
    """
    # If price is >= 1.0, assume it's in cents format
    if contract_price >= 1.0:
        return contract_price / 100.0
    else:
        # Already in dollar format
        return contract_price


def calculate_whole_contracts(target_bet_amount, contract_price, commission_per_contract=0.02):
    """
    Calculate whole contracts and adjust bet amount for Robinhood constraints.
    
    Robinhood only allows purchasing whole contracts, and charges commission per contract.
    
    Args:
        target_bet_amount: The ideal bet amount from Kelly/Wharton calculation
        contract_price: Price per contract (normalized to dollars)
        commission_per_contract: Commission fee per contract (default $0.02)
        
    Returns:
        dict: {
            'whole_contracts': int - Number of whole contracts to buy
            'actual_bet_amount': float - Actual amount to spend (including commission)
            'unused_amount': float - Amount that couldn't be used due to whole contract constraint
            'adjusted_price': float - Total cost per contract (price + commission)
        }
    """
    # Calculate adjusted price per contract (original price + commission)
    adjusted_price = contract_price + commission_per_contract
    
    # Calculate how many contracts the target amount would buy
    fractional_contracts = target_bet_amount / adjusted_price
    
    # Round down to get whole contracts
    whole_contracts = int(fractional_contracts)
    
    # Calculate the actual bet amount for whole contracts
    actual_bet_amount = whole_contracts * adjusted_price
    
    # Calculate unused amount due to rounding down
    unused_amount = target_bet_amount - actual_bet_amount
    
    return {
        'whole_contracts': whole_contracts,
        'actual_bet_amount': actual_bet_amount,
        'unused_amount': unused_amount,
        'adjusted_price': adjusted_price
    }


def user_input_betting_framework(weekly_bankroll, model_win_percentage, contract_price, 
                                model_win_margin=None, commission_per_contract=0.02):
    """
    Wharton-optimized framework using ONLY user-provided data.
    Enforces whole contract purchases (Robinhood constraint) with commission.
    
    Your Inputs:
    - weekly_bankroll: Total cash available for all bets this week
    - model_win_percentage: Your model's predicted win probability (0-1 or 0-100)
    - contract_price: Sportsbook event contract price per unit (dollars or cents)
                     Examples: 0.27 or 27 (both represent 27 cents)
    - model_win_margin: Your model's predicted margin (optional, for reference)
    - commission_per_contract: Commission fee per contract (default $0.02)
    
    Returns:
    - Betting decision and amount based on Wharton research
    - Bet amounts are adjusted to purchase only whole contracts (including commission)
    - 'contracts_to_buy' will always be an integer
    - 'unused_amount' shows money left over due to whole contract constraint
    - Commission costs are factored into all calculations
    """
    
    # Handle percentage format (convert if >1)
    win_probability = model_win_percentage if model_win_percentage <= 1 else model_win_percentage / 100
    
    # Normalize contract price to dollars
    normalized_price = normalize_contract_price(contract_price)
    
    # Calculate adjusted price (contract price + commission)
    adjusted_price = normalized_price + commission_per_contract
    
    # Step 1: Calculate Expected Value using adjusted price
    ev_per_dollar = win_probability * (1/adjusted_price) - 1
    ev_percentage = ev_per_dollar * 100
    
    # Step 2: Apply Wharton's 10% EV threshold
    if ev_percentage < 10.0:
        return {
            'decision': 'NO BET',
            'reason': f'EV {ev_percentage:.1f}% below 10% Wharton threshold',
            'ev_percentage': ev_percentage,
            'bet_amount': 0,
            'normalized_price': normalized_price
        }
    
    # Step 3: Calculate Kelly fraction using adjusted price
    b = (1 / adjusted_price) - 1  # Net odds based on total cost
    p = win_probability
    q = 1 - p
    
    full_kelly_fraction = (b * p - q) / b
    
    if full_kelly_fraction <= 0:
        return {
            'decision': 'NO BET',
            'reason': 'Negative Kelly fraction',
            'ev_percentage': ev_percentage,
            'bet_amount': 0,
            'normalized_price': normalized_price
        }
    
    # Step 4: Apply Half Kelly (Wharton optimal)
    half_kelly_fraction = full_kelly_fraction * 0.5
    
    # Step 5: Apply maximum bet constraint (15% of bankroll)
    final_fraction = min(half_kelly_fraction, 0.15)
    
    # Step 6: Calculate bet amount
    target_bet_amount = final_fraction * weekly_bankroll
    
    # Step 7: Adjust for whole contracts (Robinhood constraint with commission)
    contract_info = calculate_whole_contracts(target_bet_amount, normalized_price, commission_per_contract)
    
    # If we can't buy any whole contracts, treat as no bet
    if contract_info['whole_contracts'] == 0:
        return {
            'decision': 'NO BET',
            'reason': f'Target bet amount ${target_bet_amount:.2f} insufficient for 1 whole contract at ${contract_info["adjusted_price"]:.2f} (including commission)',
            'ev_percentage': ev_percentage,
            'bet_amount': 0,
            'normalized_price': normalized_price,
            'target_bet_amount': target_bet_amount,
            'contracts_to_buy': 0,
            'commission_per_contract': commission_per_contract
        }
    
    # Use the actual bet amount for whole contracts (including commission)
    actual_bet_amount = contract_info['actual_bet_amount']
    actual_bet_percentage = (actual_bet_amount / weekly_bankroll) * 100
    
    # Calculate expected profit based on EV
    expected_profit = actual_bet_amount * ev_per_dollar
    
    return {
        'decision': 'BET',
        'bet_amount': actual_bet_amount,
        'bet_percentage': actual_bet_percentage,
        'ev_percentage': ev_percentage,
        'expected_profit': expected_profit,
        'contracts_to_buy': contract_info['whole_contracts'],
        'normalized_price': normalized_price,
        'target_bet_amount': target_bet_amount,
        'unused_amount': contract_info['unused_amount'],
        'adjusted_price': contract_info['adjusted_price'],
        'commission_per_contract': commission_per_contract,
        'wharton_compliant': True,
        'whole_contracts_only': True
    }
