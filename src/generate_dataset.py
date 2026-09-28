"""
Synthetic Transaction Dataset Generator
========================================
Generates a realistic synthetic bank transaction dataset
matching the PRD §7 schema for development and testing.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def generate_transactions(
    n_transactions: int = 50000,
    n_customers: int = 2000,
    start_date: str = "2023-01-01",
    end_date: str = "2024-12-31",
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate a synthetic bank transaction dataset.

    Parameters
    ----------
    n_transactions : int
        Number of transactions to generate.
    n_customers : int
        Number of unique customers.
    start_date : str
        Start date for transaction range.
    end_date : str
        End date for transaction range.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Synthetic transaction dataset matching PRD §7 schema.
    """
    rng = np.random.default_rng(seed)

    # --- Customer IDs ---
    customer_ids = [f"CUST-{i:04d}" for i in range(1, n_customers + 1)]

    # --- Transaction IDs ---
    transaction_ids = [f"TXN-{i:06d}" for i in range(1, n_transactions + 1)]

    # --- Dates (with realistic weekday/hour patterns) ---
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    date_range_days = (end - start).days

    # Generate dates with slight weekday bias
    random_days = rng.integers(0, date_range_days, size=n_transactions)
    base_dates = pd.to_datetime(start) + pd.to_timedelta(random_days, unit="D")

    # Generate hours with realistic banking pattern (peak 9-17)
    hour_weights = np.array([
        0.5, 0.3, 0.2, 0.2, 0.3, 0.5,   # 0-5 AM (low)
        1.0, 2.0, 4.0, 5.0, 5.5, 5.0,    # 6-11 AM (rising)
        4.5, 5.0, 5.5, 5.0, 4.5, 4.0,    # 12-5 PM (peak)
        3.5, 3.0, 2.5, 2.0, 1.5, 1.0,    # 6-11 PM (declining)
    ])
    hour_weights = hour_weights / hour_weights.sum()
    hours = rng.choice(24, size=n_transactions, p=hour_weights)
    minutes = rng.integers(0, 60, size=n_transactions)
    seconds = rng.integers(0, 60, size=n_transactions)

    transaction_dates = base_dates + pd.to_timedelta(hours, unit="h") + \
                        pd.to_timedelta(minutes, unit="m") + \
                        pd.to_timedelta(seconds, unit="s")

    # --- Transaction Types ---
    transaction_types = ["Deposit", "Withdrawal", "Transfer", "Payment", "Refund"]
    type_weights = [0.20, 0.25, 0.20, 0.30, 0.05]
    types = rng.choice(transaction_types, size=n_transactions, p=type_weights)

    # --- Amounts (right-skewed, realistic banking distribution) ---
    amounts = np.zeros(n_transactions)
    for i in range(n_transactions):
        t = types[i]
        if t == "Deposit":
            # Deposits: salary-like (large) + small deposits
            if rng.random() < 0.3:
                amounts[i] = rng.lognormal(mean=10.5, sigma=0.5)  # Salary range
            else:
                amounts[i] = rng.lognormal(mean=7.0, sigma=1.2)
        elif t == "Withdrawal":
            amounts[i] = -rng.lognormal(mean=7.5, sigma=1.0)
        elif t == "Transfer":
            if rng.random() < 0.5:
                amounts[i] = rng.lognormal(mean=8.0, sigma=1.5)
            else:
                amounts[i] = -rng.lognormal(mean=8.0, sigma=1.5)
        elif t == "Payment":
            amounts[i] = -rng.lognormal(mean=6.5, sigma=1.3)
        elif t == "Refund":
            amounts[i] = rng.lognormal(mean=6.0, sigma=1.0)

    # Clip to reasonable banking amounts
    amounts = np.clip(amounts, -500000, 500000)
    amounts = np.round(amounts, 2)

    # --- Status ---
    statuses = ["Completed", "Failed", "Reversed", "Pending"]
    status_weights = [0.85, 0.05, 0.03, 0.07]
    status_col = rng.choice(statuses, size=n_transactions, p=status_weights)

    # --- Categories ---
    categories = [
        "Salary", "Food & Dining", "Shopping", "Utilities", "Travel",
        "Entertainment", "Healthcare", "Education", "Rent", "Insurance",
        "Investment", "Groceries", "Fuel", "Subscriptions", "Other"
    ]
    cat_weights = [0.08, 0.14, 0.15, 0.10, 0.06, 0.07, 0.05, 0.04,
                   0.08, 0.04, 0.05, 0.06, 0.04, 0.02, 0.02]
    category_col = rng.choice(categories, size=n_transactions, p=cat_weights)

    # --- Channels ---
    channels = ["ATM", "Branch", "Mobile", "Web", "POS"]
    channel_weights = [0.15, 0.10, 0.35, 0.25, 0.15]
    channel_col = rng.choice(channels, size=n_transactions, p=channel_weights)

    # --- Payment Methods ---
    payment_methods = ["Card", "UPI", "Bank Transfer", "Cash", "Net Banking"]
    pm_weights = [0.25, 0.30, 0.20, 0.10, 0.15]
    payment_method_col = rng.choice(payment_methods, size=n_transactions, p=pm_weights)

    # --- Merchants ---
    merchants = [
        "Amazon", "Flipkart", "Zomato", "Swiggy", "BigBasket",
        "Paytm", "PhonePe", "HDFC Bank", "SBI", "ICICI Bank",
        "Reliance Fresh", "DMart", "Uber", "Ola", "Airtel",
        "Jio", "Netflix", "Spotify", "BookMyShow", "MakeMyTrip",
        "Electricity Board", "Water Authority", "Gas Company",
        "Hospital A", "Pharmacy B", "School C", "University D",
        "Landlord", "Insurance Corp", "Mutual Fund Co", "Other Merchant"
    ]
    merchant_col = rng.choice(merchants, size=n_transactions)

    # --- Locations ---
    locations = [
        "Mumbai", "Delhi", "Bengaluru", "Chennai", "Hyderabad",
        "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow",
        "Chandigarh", "Kochi", "Indore", "Bhopal", "Nagpur"
    ]
    loc_weights = [0.18, 0.15, 0.14, 0.10, 0.10, 0.08, 0.06,
                   0.05, 0.04, 0.03, 0.02, 0.02, 0.01, 0.01, 0.01]
    location_col = rng.choice(locations, size=n_transactions, p=loc_weights)

    # --- Customer assignment (some customers more active than others) ---
    # Use Pareto-like distribution for customer activity
    customer_activity = rng.pareto(a=1.5, size=n_customers) + 1
    customer_activity = customer_activity / customer_activity.sum()
    customer_col = rng.choice(customer_ids, size=n_transactions, p=customer_activity)

    # --- Build DataFrame ---
    df = pd.DataFrame({
        "transaction_id": transaction_ids,
        "customer_id": customer_col,
        "transaction_date": transaction_dates,
        "amount": amounts,
        "transaction_type": types,
        "status": status_col,
        "category": category_col,
        "channel": channel_col,
        "payment_method": payment_method_col,
        "merchant": merchant_col,
        "location": location_col,
        "currency": "INR",
    })

    # --- Inject realistic data quality issues (for testing cleaning pipeline) ---
    n_issues = int(n_transactions * 0.02)  # ~2% dirty data

    # Missing customer_id (0.5%)
    null_cust_idx = rng.choice(n_transactions, size=int(n_transactions * 0.005), replace=False)
    df.loc[null_cust_idx, "customer_id"] = np.nan

    # Missing amounts (0.3%)
    null_amt_idx = rng.choice(n_transactions, size=int(n_transactions * 0.003), replace=False)
    df.loc[null_amt_idx, "amount"] = np.nan

    # Invalid dates — future dates (0.2%)
    future_idx = rng.choice(n_transactions, size=int(n_transactions * 0.002), replace=False)
    df.loc[future_idx, "transaction_date"] = pd.Timestamp("2027-06-15 10:30:00")

    # Category typos / inconsistencies (0.5%)
    typo_idx = rng.choice(n_transactions, size=int(n_transactions * 0.005), replace=False)
    typos = ["food & dining", "SHOPPING", "  Utilities ", "trvel", "entertainmnet"]
    df.loc[typo_idx, "category"] = rng.choice(typos, size=len(typo_idx))

    # Duplicate transaction_ids (0.2%)
    dup_idx = rng.choice(n_transactions, size=int(n_transactions * 0.002), replace=False)
    dup_source = rng.choice(n_transactions, size=len(dup_idx), replace=False)
    df.loc[dup_idx, "transaction_id"] = df.loc[dup_source, "transaction_id"].values

    # Sort by date
    df = df.sort_values("transaction_date").reset_index(drop=True)

    return df


def main():
    """Generate and save the synthetic dataset."""
    print("Generating synthetic transaction dataset...")
    print("=" * 50)

    df = generate_transactions(n_transactions=50000, n_customers=2000)

    # Save to CSV
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "sample"
    )
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "transactions.csv")
    df.to_csv(output_path, index=False)

    print(f"Dataset saved to: {output_path}")
    print(f"Total records: {len(df):,}")
    print(f"Unique customers: {df['customer_id'].nunique():,}")
    print(f"Date range: {df['transaction_date'].min()} to {df['transaction_date'].max()}")
    print(f"Amount range: {df['amount'].min():,.2f} to {df['amount'].max():,.2f}")
    print(f"\nColumn types:")
    print(df.dtypes)
    print(f"\nNull counts:")
    print(df.isnull().sum())
    print(f"\nSample rows:")
    print(df.head(5).to_string())


if __name__ == "__main__":
    main()
