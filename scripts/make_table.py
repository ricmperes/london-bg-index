import os
import argparse
from pathlib import Path
from multiprocessing import Pool, cpu_count, current_process
import time
import random

from boardgamegeek import BGGClient
import numpy as np
import pandas as pd
from tqdm import tqdm

# Get the project root directory (parent of scripts directory)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
ERROR_LOG_PATH = SCRIPT_DIR / 'bgg_errors.log'


def write_to_err_log(game_title, error):
    """Write game title and error to the error log file."""
    with open(ERROR_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f"{game_title} | {error}\n")


def read_file():
    # Try to find the CSV file in inputs directory or current directory
    csv_path = PROJECT_ROOT / 'inputs' / 'SearchResults.csv'
    if not csv_path.exists():
        csv_path = PROJECT_ROOT / 'SearchResults.csv'
    if not csv_path.exists():
        # Fallback to current directory
        csv_path = Path('inputs/SearchResults.csv')
        if not csv_path.exists():
            csv_path = Path('SearchResults.csv')
    
    df = pd.read_csv(csv_path)
    df = df[df['Format'] == 'Board Game']
    df.pop('Location & Call Number')
    df.pop('Place of Publication')
    df.pop('Format')

    # Move the left-most column to the right-most position
    first_col = df.columns[0]
    df = df[[col for col in df.columns if col != first_col] + [first_col]]
    df['Publish Date'] = df['Publish Date'].astype('Int64')
    #df['BGG_rank'] = np.zeros(len(df))
    df.sort_values(by='Title', ascending=True, inplace=True)
    return df

def make_html_page(df):    
    # Convert Link column to active hyperlinks
    if 'Link' in df.columns:
        df = df.copy()  # Avoid modifying the original dataframe
        df['Link'] = df['Link'].apply(
            lambda x: f'<a href="{x}" target="_blank">View Details</a>' if pd.notna(x) and x else ''
        )
    
    # Convert dataframe to HTML table
    table_html = df.to_html(classes='data-table', table_id='board-games-table', 
                            index=False, escape=False, float_format='%.2f')
    
    # Create the full HTML page with navbar
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>K&S Libraries BG Index - Catalogue</title>
    <link rel="stylesheet" href="../css/style.css">
</head>
<body>
    <!-- Navbar will be loaded here -->
    <div id="navbar-container"></div>

    <!-- Main Content -->
    <div class="container">
        <div class="page-header">
            <h1>Board Games Catalogue</h1>
            <p>Click on any column header to sort the table</p>
        </div>
        {table_html}
    </div>
    
    <!-- Footer will be loaded here -->
    <div id="footer-container"></div>
    
    <script src="../js/navbar-loader.js"></script>
    <script src="../js/footer-loader.js"></script>
    <script src="../js/table-sort.js"></script>
</body>
</html>"""
    
    # Write to HTML file in the pages directory
    output_path = PROJECT_ROOT / 'pages' / 'table.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML page created: {output_path}")

def _get_rank_worker(args):
    """Worker function for multiprocessing - creates its own BGG client."""
    game_title, token = args
    # Add process-specific delay to avoid simultaneous requests
    # This prevents HTTP responses from getting mixed between processes
    #process_id = current_process().pid
    #random.seed(process_id)  # Seed based on process ID for consistency
    #delay = random.uniform(0.05, 0.15)  # Random delay between 50-150ms
    delay = 1
    time.sleep(delay)
    
    try:
        bgg_client = BGGClient(access_token=token)
        game = bgg_client.game(game_title)
        return float(game.rating_average)
    except Exception as e:
        write_to_err_log(game_title,e)
        return np.nan


def make_bgg_rank_column(df, n_processes=None):
    """
    Get BGG ranks for all games in parallel.
    
    Args:
        df: DataFrame with 'Title' column
        n_processes: Number of processes to use (default: None = all available CPUs)
    
    Returns:
        DataFrame with 'BGG_Rank' column added
    """
    if n_processes is None:
        n_processes = cpu_count()
    print(f"Using {n_processes} processes")
    bgg_token = os.environ.get("BGG_token")
    
    # Prepare arguments for worker function
    game_titles = df['Title'].tolist()
    args_list = [(title, bgg_token) for title in game_titles]
    
    # Use multiprocessing to get ranks in parallel
    with Pool(processes=n_processes) as pool:
        ranks = list(tqdm(
            pool.imap(_get_rank_worker, args_list),
            total=len(game_titles),
            desc='Getting BGG ranks'
        ))
    
    # Assign ranks to dataframe
    df['BGG_Rank'] = ranks
    return df

def main():
    parser = argparse.ArgumentParser(description='Generate board games table with BGG ranks')
    parser.add_argument(
        '--n-processes',
        type=int,
        default=None,
        help=f'Number of processes to use for parallel processing (default: {cpu_count()} - all available CPUs)'
    )
    args = parser.parse_args()
    
    df = read_file()

    bgg_token = os.environ.get("BGG_token")
    global bgg 
    bgg = BGGClient(access_token=bgg_token)
    df = make_bgg_rank_column(df, n_processes=args.n_processes)
    make_html_page(df)

if __name__ == "__main__":
    main()