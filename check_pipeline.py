import sys
sys.path.insert(0, '.')

# Load fresh pipeline data
from pipeline import run_pipeline

print("Running pipeline...")
df = run_pipeline(verbose=True)

print(f"\n{'='*80}")
print("COLUMN CHECK")
print(f"{'='*80}")
print(f"Total columns: {len(df.columns)}")
print(f"\nAll columns: {list(df.columns)}")

llm_cols = [c for c in df.columns if 'llm' in c.lower()]
print(f"\nLLM columns ({len(llm_cols)}): {llm_cols}")

if len(df) > 0:
    print(f"\n{'='*80}")
    print("FIRST ROW LLM DATA")
    print(f"{'='*80}")
    for col in llm_cols:
        val = df.iloc[0][col]
        if val and str(val) != 'nan':
            print(f"\n{col}:")
            print(f"  {str(val)[:150]}...")
        else:
            print(f"\n{col}: <EMPTY>")
