import pandas as pd

print("PIPELINE OUTPUT SUMMARY")
print("=" * 50)

df = pd.read_csv("agent_recommendations.csv")

print(f"Total SKUs: {len(df)}")
print(f"Total Columns: {len(df.columns)}")
print(f"Profitable: {(df['profit_per_unit'] > 0).sum()}")
print(f"Loss Makers: {(df['profit_per_unit'] < 0).sum()}")
print(f"Critical Risk: {(df['risk_level'] == 'CRITICAL').sum()}")
print(f"Warning Risk: {(df['risk_level'] == 'WARNING').sum()}")
print(f"Has Seasonal: {'seasonal_index_current' in df.columns}")

print("\n" + "=" * 50)
print("COLUMNS:")
print(df.columns.tolist())

print("\n" + "=" * 50)
print("TOP 5 BY IMPACT SCORE:")
print(df[['product_name', 'profit_per_unit', 'risk_level', 'impact_score', 'recommended_action']].head(5).to_string())
