

import time
import pandas as pd
import polars as pl
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Configuration ---
N_ROWS = 5_000_000
N_COLS = 5
FIGURES_DIR = "figures"
DATA_DIR = "data"
PARQUET_PATH_PD = os.path.join(DATA_DIR, "data_pd.parquet")
PARQUET_PATH_PL = os.path.join(DATA_DIR, "data_pl.parquet")
PARQUET_PATH_FD = os.path.join(DATA_DIR, "data_fd.parquet")

# --- Data Generation ---
def generate_data(n_rows):
    """Generates a Pandas DataFrame with random data."""
    data = {
        f'col_{i}': np.random.rand(n_rows) for i in range(N_COLS - 1)
    }
    data['group'] = np.random.randint(0, 100, size=n_rows)
    data['id'] = np.arange(n_rows)
    return pd.DataFrame(data)

# --- Benchmarking Utility ---
def benchmark(func, df, framework_name, results_list, **kwargs):
    """Times the execution of a function and records the result."""
    start_time = time.time()
    result = func(df, **kwargs)
    end_time = time.time()
    duration = end_time - start_time
    results_list.append({
        'Framework': framework_name,
        'Operation': func.__name__,
        'Time': duration
    })
    print(f"{framework_name:<10} | {func.__name__:<22} | {duration:.4f} seconds")
    return result

# --- Operation Functions ---
def filter_data(df):
    if isinstance(df, pd.DataFrame):
        return df[df['col_0'] > 0.5]
    elif isinstance(df, pl.DataFrame):
        return df.filter(pl.col('col_0') > 0.5)

def aggregate_data(df):
    if isinstance(df, pd.DataFrame):
        return df.groupby('group').agg({'col_1': 'mean', 'col_2': 'sum'})
    elif isinstance(df, pl.DataFrame):
        return df.group_by('group').agg([pl.mean('col_1'), pl.sum('col_2')])

def sort_data(df):
    return df.sort_values(by='col_3') if isinstance(df, pd.DataFrame) else df.sort('col_3')

def join_data(df):
    if isinstance(df, pd.DataFrame):
        other_df = df[['id', 'col_0']].head(1000).copy()
        other_df.columns = ['id', 'new_col']
        return df.merge(other_df, on='id', how='inner')
    elif isinstance(df, pl.DataFrame):
        other_df = df[['id', 'col_0']].slice(0, 1000).rename({'col_0': 'new_col'})
        return df.join(other_df, on='id', how='inner')

def string_manipulation(df):
    if isinstance(df, pd.DataFrame):
        df_copy = df.copy()
        df_copy['group_str'] = df_copy['group'].astype(str) + '_str'
        return df_copy
    elif isinstance(df, pl.DataFrame):
        return df.with_columns((pl.col('group').cast(pl.Utf8) + '_str').alias('group_str'))

def write_parquet(df, path):
    if isinstance(df, pd.DataFrame):
        df.to_parquet(path)
    elif isinstance(df, pl.DataFrame):
        df.write_parquet(path)

def read_parquet(df, path):
    if isinstance(df, pd.DataFrame):
        return pd.read_parquet(path)
    elif isinstance(df, pl.DataFrame):
        return pl.read_parquet(path)

def rolling_average(df):
    if isinstance(df, pd.DataFrame):
        return df.sort_values('id').set_index('id')[['col_1']].rolling(window=10).mean()
    elif isinstance(df, pl.DataFrame):
        return df.sort('id').select(pl.col('col_1').rolling_mean(window_size=10))

def custom_apply(df):
    def custom_function(x):
        return x * 2 + 1
    if isinstance(df, pd.DataFrame):
        df_copy = df.copy()
        df_copy['col_0_applied'] = df_copy['col_0'].apply(custom_function)
        return df_copy
    elif isinstance(df, pl.DataFrame):
        return df.with_columns(((pl.col('col_0') * 2) + 1).alias('col_0_applied'))

# --- Plotting ---
def plot_results(results_df):
    if not os.path.exists(FIGURES_DIR):
        os.makedirs(FIGURES_DIR)

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(18, 10))

    sns.barplot(x='Operation', y='Time', hue='Framework', data=results_df, ax=ax, palette='viridis')

    ax.set_title('Framework Performance Comparison', fontsize=20, fontweight='bold')
    ax.set_xlabel('Data Operation', fontsize=14)
    ax.set_ylabel('Execution Time (seconds) - Log Scale', fontsize=14)
    ax.tick_params(axis='x', rotation=45, labelsize=12)
    ax.legend(title='Framework', fontsize=12)
    ax.set_yscale('log') # Use log scale for better visualization

    for p in ax.patches:
        ax.annotate(f'{p.get_height():.3f}',
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center', 
                    xytext=(0, 9),
                    textcoords='offset points', fontsize=9)

    plt.tight_layout()
    save_path = os.path.join(FIGURES_DIR, 'benchmark_comparison_extended.png')
    plt.savefig(save_path)
    print(f"\nChart saved to {save_path}")

# --- Main Execution ---
def main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    print(f"Generating data ({N_ROWS} rows)...")
    pd_df = generate_data(N_ROWS)
    pl_df = pl.from_pandas(pd_df)
    fd_df = pd_df

    results = []

    print("\n--- Benchmarks ---")
    print(f"{'Framework':<10} | {'Operation':<22} | {'Time':<20}")
    print("-" * 60)

    # --- Pandas ---
    benchmark(filter_data, pd_df, 'Pandas', results)
    benchmark(aggregate_data, pd_df, 'Pandas', results)
    benchmark(sort_data, pd_df, 'Pandas', results)
    benchmark(join_data, pd_df, 'Pandas', results)
    benchmark(string_manipulation, pd_df, 'Pandas', results)
    benchmark(write_parquet, pd_df, 'Pandas', results, path=PARQUET_PATH_PD)
    benchmark(read_parquet, pd_df, 'Pandas', results, path=PARQUET_PATH_PD)
    benchmark(rolling_average, pd_df, 'Pandas', results)
    benchmark(custom_apply, pd_df, 'Pandas', results)

    # --- Polars ---
    benchmark(filter_data, pl_df, 'Polars', results)
    benchmark(aggregate_data, pl_df, 'Polars', results)
    benchmark(sort_data, pl_df, 'Polars', results)
    benchmark(join_data, pl_df, 'Polars', results)
    benchmark(string_manipulation, pl_df, 'Polars', results)
    benchmark(write_parquet, pl_df, 'Polars', results, path=PARQUET_PATH_PL)
    benchmark(read_parquet, pl_df, 'Polars', results, path=PARQUET_PATH_PL)
    benchmark(rolling_average, pl_df, 'Polars', results)
    benchmark(custom_apply, pl_df, 'Polars', results)

    # --- Fireducks ---
    import fireducks  # noqa: F401
    benchmark(filter_data, fd_df, 'Fireducks', results)
    benchmark(aggregate_data, fd_df, 'Fireducks', results)
    benchmark(sort_data, fd_df, 'Fireducks', results)
    benchmark(join_data, fd_df, 'Fireducks', results)
    benchmark(string_manipulation, fd_df, 'Fireducks', results)
    benchmark(write_parquet, fd_df, 'Fireducks', results, path=PARQUET_PATH_FD)
    benchmark(read_parquet, fd_df, 'Fireducks', results, path=PARQUET_PATH_FD)
    benchmark(rolling_average, fd_df, 'Fireducks', results)
    benchmark(custom_apply, fd_df, 'Fireducks', results)

    results_df = pd.DataFrame(results)
    plot_results(results_df)

    # Store raw results for README update
    results_df.to_csv(os.path.join(FIGURES_DIR, 'benchmark_results.csv'), index=False)

if __name__ == "__main__":
    main()
