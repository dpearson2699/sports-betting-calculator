#!/usr/bin/env python3
"""
Basic Usage Example - Sports Betting Calculator Framework

This example demonstrates the basic usage of the betting framework
for a single bet analysis.
"""

from pathlib import Path

from ..betting_framework import user_input_betting_framework


def basic_single_bet_example():
    """Example of analyzing a single bet"""
    print("=== Single Bet Analysis Example ===\n")
    
    # Example parameters
    weekly_bankroll = 100.00  # $100 weekly bankroll
    model_win_percentage = 68.0  # 68% win probability from your model
    contract_price = 0.45  # 45 cents per contract
    
    print(f"Analyzing bet with:")
    print(f"  Weekly Bankroll: ${weekly_bankroll}")
    print(f"  Model Win Probability: {model_win_percentage}%")
    print(f"  Contract Price: ${contract_price}")
    print()
    
    # Run the analysis
    result = user_input_betting_framework(
        weekly_bankroll=weekly_bankroll,
        model_win_percentage=model_win_percentage,
        contract_price=contract_price
    )
    
    # Display results
    print("RESULTS:")
    print("-" * 40)
    print(f"Decision: {result['decision']}")
    print(f"Expected Value: {result['ev_percentage']:.1f}%")
    
    if result['decision'] == 'BET':
        print(f"Recommended Bet: ${result['bet_amount']:.2f}")
        print(f"Contracts to Buy: {result['contracts_to_buy']}")
        print(f"Expected Profit: ${result['expected_profit']:.2f}")
        print(f"Bankroll Percentage: {result['bet_percentage']:.1f}%")
        
        # Show safety constraints in action
        print("\nSafety Constraints Applied:")
        print(f"  ✓ EV above 10% threshold: {result['ev_percentage']:.1f}%")
        print(f"  ✓ Half-Kelly sizing for reduced volatility")
        print(f"  ✓ Whole contracts only (Robinhood constraint)")
        print(f"  ✓ Commission included: $0.02 per contract")
    else:
        print(f"Reason: {result['reason']}")
        print("\nThis bet doesn't meet Wharton safety criteria.")
    
    return result


def demonstrate_safety_constraints():
    """Demonstrate how safety constraints work"""
    print("\n=== Safety Constraints Demonstration ===\n")
    
    test_cases = [
        {
            "name": "Low EV (Below 10% threshold)",
            "bankroll": 100,
            "win_pct": 55,
            "price": 0.50,
            "expected": "NO BET"
        },
        {
            "name": "High EV (Should be capped at 15% bankroll)",
            "bankroll": 1000,
            "win_pct": 90,
            "price": 0.05,
            "expected": "BET (capped)"
        },
        {
            "name": "Good EV (Should get normal Kelly sizing)",
            "bankroll": 100,
            "win_pct": 70,
            "price": 0.40,
            "expected": "BET"
        }
    ]
    
    for case in test_cases:
        print(f"Testing: {case['name']}")
        result = user_input_betting_framework(
            weekly_bankroll=case['bankroll'],
            model_win_percentage=case['win_pct'],
            contract_price=case['price']
        )
        
        print(f"  Win%: {case['win_pct']}%, Price: ${case['price']}")
        print(f"  Result: {result['decision']}")
        print(f"  EV: {result['ev_percentage']:.1f}%")
        
        if result['decision'] == 'BET':
            print(f"  Bet: ${result['bet_amount']:.2f} ({result['bet_percentage']:.1f}% of bankroll)")
        else:
            print(f"  Reason: {result['reason']}")
        print()


def dual_format_input_example():
    """Demonstrate dual format input handling"""
    print("=== Dual Format Input Example ===\n")
    
    # Same bet analyzed with different input formats
    bankroll = 100
    
    formats = [
        {"win_pct": 68, "price": 45, "description": "Percentage format (68) and cents (45)"},
        {"win_pct": 0.68, "price": 0.45, "description": "Decimal format (0.68) and dollars (0.45)"},
        {"win_pct": 68.0, "price": 0.45, "description": "Mixed format (68.0) and dollars (0.45)"}
    ]
    
    print("Testing same bet with different input formats:")
    print("All should produce identical results...\n")
    
    for i, fmt in enumerate(formats, 1):
        print(f"Format {i}: {fmt['description']}")
        result = user_input_betting_framework(
            weekly_bankroll=bankroll,
            model_win_percentage=fmt['win_pct'],
            contract_price=fmt['price']
        )
        
        print(f"  EV: {result['ev_percentage']:.1f}%")
        print(f"  Decision: {result['decision']}")
        if result['decision'] == 'BET':
            print(f"  Bet Amount: ${result['bet_amount']:.2f}")
        print()


if __name__ == "__main__":
    # Run all examples
    basic_single_bet_example()
    demonstrate_safety_constraints()
    dual_format_input_example()
    
    print("=" * 50)
    print("Examples complete!")
    print("Next steps:")
    print("1. Try running: python run.py")
    print("2. Use Excel batch mode for multiple games")
    print("3. See README.md for full documentation")