import pandas as pd
import json
import math

def get_discount_percentage(loan_type, principal, dpd, chat_text):
    """
    Calculates the maximum discount percentage based on policy rules.
    """
    chat_text_lower = chat_text.lower()
    
    # Check for keywords
    job_loss = "job loss" in chat_text_lower or "unemployment" in chat_text_lower or "lost my job" in chat_text_lower
    medical = "hospital" in chat_text_lower or "medical" in chat_text_lower
    
    if loan_type == "Personal Loan":
        if job_loss:
            return 0.50
        elif medical:
            return 0.45
        elif dpd > 90:
            return 0.35
        else:
            return 0.20
            
    elif loan_type == "Credit Card":
        # Small Balance Rule (Highest Priority for CC based on interpretation)
        if principal < 50000:
            return 0.10
        elif dpd > 90:
            return 0.50
        else:
            return 0.30
            
    return 0.0 # Should not happen based on data

def calculate_min_offer(principal, discount_percent):
    """
    Calculates the minimum acceptable offer and rounds to the nearest 100.
    """
    max_discount_amount = principal * discount_percent
    min_offer = principal - max_discount_amount
    
    # Round to nearest 100
    # Standard rounding: 150 -> 200, 149 -> 100
    # Python's round() rounds to nearest even number for .5 cases, so we use standard math rounding
    rounded_offer = math.ceil(min_offer / 100) * 100 
    # Wait, "rounded to the nearest 100" usually means standard rounding, not ceiling.
    # Let's check Python's round behavior or implement standard rounding.
    # int(x + 0.5) approach for positive numbers.
    
    # Re-reading policy: "All offers must be rounded to the nearest 100."
    # Let's use standard rounding.
    rounded_offer = round(min_offer / 100) * 100
    
    # "Never accept an offer lower than the calculated limit."
    # This implies the floor price is the limit.
    # If the rounded offer is slightly lower than the raw min_offer, is that allowed?
    # "Strictly allowed counter-offer"
    # Usually in these problems, you calculate the exact limit, then round that limit.
    # Let's stick to rounding the result.
    
    return int(rounded_offer)

def solve():
    # Load data
    print("Loading data...")
    borrower_df = pd.read_csv('data/borrower_data.csv')
    
    # Create a dictionary for faster lookup
    borrower_dict = borrower_df.set_index('borrower_id').to_dict('index')
    
    with open('data/chat_scenarios.json', 'r') as f:
        scenarios = json.load(f)
        
    results = []
    
    print("Processing scenarios...")
    for scenario in scenarios:
        scenario_id = scenario['scenario_id']
        borrower_id = scenario['borrower_id']
        chat_history = scenario['chat_history']
        
        # Get borrower details
        borrower = borrower_dict.get(borrower_id)
        if not borrower:
            print(f"Warning: Borrower {borrower_id} not found.")
            continue
            
        loan_type = borrower['loan_type']
        principal = borrower['principal_outstanding']
        dpd = borrower['dpd']
        
        # Combine user messages for keyword search
        user_text = " ".join([msg['content'] for msg in chat_history if msg['role'] == 'user'])
        
        # Calculate discount
        discount_percent = get_discount_percentage(loan_type, principal, dpd, user_text)
        
        # Calculate min offer
        min_offer = calculate_min_offer(principal, discount_percent)
        
        results.append({
            'scenario_id': scenario_id,
            'min_acceptable_offer': min_offer
        })
        
    # Create DataFrame and save
    submission_df = pd.DataFrame(results)
    submission_df.to_csv('submission.csv', index=False)
    print(f"Saved {len(submission_df)} results to submission.csv")

if __name__ == "__main__":
    solve()
