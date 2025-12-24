import os
import argparse
from pathlib import Path
from multiprocessing import Pool, cpu_count
import time

from boardgamegeek import BGGClient
import pandas as pd
from tqdm import tqdm

# Get the project root directory (parent of scripts directory)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
ERROR_LOG_PATH = SCRIPT_DIR / 'bgg_errors.log'
BGG_DATA_PATH = PROJECT_ROOT / 'inputs' / 'bgg_data.csv'


def write_to_err_log(game_title, error):
    """Write game title and error to the error log file."""
    with open(ERROR_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f"{game_title} | {error}\n")


def read_search_results():
    """Read the SearchResults.csv file and extract board game titles."""
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
    return df['Title'].unique().tolist()


def _get_bgg_data_worker(args):
    """Worker function for multiprocessing - creates its own BGG client."""
    game_title, token = args
    # Add delay to avoid overwhelming the API
    delay = 1
    time.sleep(delay)
    
    try:
        bgg_client = BGGClient(access_token=token)
        game = bgg_client.game(game_title)
        
        # Extract BGG data - adjust property names based on actual BGG API response
        bgg_id = getattr(game, 'id', getattr(game, 'game_id', None))
        bgg_name = getattr(game, 'name', getattr(game, 'title', game_title))
        # Try to get rating average
        bgg_rating = getattr(game, 'rating_average', None)
        
        return {
            'Title': game_title,  # Original title for merging with SearchResults
            'BGG_Name': bgg_name,  # Name from BGG API
            'BGG_ID': bgg_id,
            'BGG_Rating': bgg_rating
        }
    except Exception as e:
        write_to_err_log(game_title, e)
        return {
            'Title': game_title,
            'BGG_Name': None,
            'BGG_ID': None,
            'BGG_Rating': None
        }


def fetch_bgg_data(n_processes=None):
    """
    Fetch BGG data for all games in parallel and save to CSV.
    
    Args:
        n_processes: Number of processes to use (default: None = all available CPUs)
    """
    if n_processes is None:
        n_processes = cpu_count()
    print(f"Using {n_processes} processes")
    
    bgg_token = os.environ.get("BGG_token")
    if not bgg_token:
        raise ValueError("BGG_token environment variable not set")
    
    # Get list of game titles
    game_titles = read_search_results()
    print(f"Found {len(game_titles)} board games to fetch")
    
    # Prepare arguments for worker function
    args_list = [(title, bgg_token) for title in game_titles]
    
    # Use multiprocessing to get BGG data in parallel
    with Pool(processes=n_processes) as pool:
        results = list(tqdm(
            pool.imap(_get_bgg_data_worker, args_list),
            total=len(game_titles),
            desc='Fetching BGG data'
        ))
    
    # Convert results to DataFrame
    df_bgg = pd.DataFrame(results)
    
    # Save to CSV
    df_bgg.to_csv(BGG_DATA_PATH, index=False, encoding='utf-8')
    print(f"BGG data saved to: {BGG_DATA_PATH}")
    print(f"Successfully fetched data for {df_bgg['BGG_ID'].notna().sum()} games")

def recompile_ratings():
    """
    Recompile ratings from the existing BGG data CSV using BGG IDs.
    Uses game_list to batch fetch all games at once.
    """
    bgg_token = os.environ.get("BGG_token")
    if not bgg_token:
        raise ValueError("BGG_token environment variable not set")
    
    # Read existing BGG data CSV
    if not BGG_DATA_PATH.exists():
        raise FileNotFoundError(f"BGG data file not found: {BGG_DATA_PATH}")
    
    df_bgg = pd.read_csv(BGG_DATA_PATH)
    print(f"Loaded {len(df_bgg)} games from {BGG_DATA_PATH}")
    
    # Filter to only games with valid BGG_IDs and convert to int
    df_with_ids = df_bgg[df_bgg['BGG_ID'].notna()].copy()
    df_with_ids['BGG_ID'] = df_with_ids['BGG_ID'].astype(int)
    
    print(f"Found {len(df_with_ids)} games with BGG IDs to update")
    
    if len(df_with_ids) == 0:
        print("No games with BGG IDs found. Nothing to update.")
        return
    
    # Get list of game IDs
    game_ids = df_with_ids['BGG_ID'].tolist()
    
    # Initialize BGG client
    bgg_client = BGGClient(access_token=bgg_token)
    
    # Fetch games in batches of 18 (API limitation)
    batch_size = 18
    print(f"Fetching ratings for {len(game_ids)} games in batches of {batch_size}...")
    
    # Create a dictionary mapping BGG_ID to rating_average
    ratings_dict = {}
    
    try:
        # Process game IDs in batches of 18
        for i in range(0, len(game_ids), batch_size):
            batch = game_ids[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(game_ids) + batch_size - 1) // batch_size
            
            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} games)...")
            games = bgg_client.game_list(batch)
            
            for game in games:
                rating_average = getattr(game, 'rating_average', None)
                if rating_average is not None:
                    ratings_dict[game.id] = float(rating_average)
        
        print(f"Successfully fetched ratings for {len(ratings_dict)} games")
        
        # Update the BGG_Rating column
        df_with_ids['BGG_Rating'] = df_with_ids['BGG_ID'].map(ratings_dict)
        
        # Log any games that weren't found
        missing_ids = set(game_ids) - set(ratings_dict.keys())
        if missing_ids:
            print(f"Warning: Could not fetch ratings for {len(missing_ids)} games (IDs: {missing_ids})")
            for missing_id in missing_ids:
                write_to_err_log(f"BGG_ID: {missing_id}", "Game not found or rating_average not available")
        
    except Exception as e:
        print(f"Error fetching games: {e}")
        write_to_err_log("recompile_ratings", e)
        raise
    
    # Merge back with games that don't have BGG IDs
    df_no_ids = df_bgg[df_bgg['BGG_ID'].isna()].copy()
    df_updated = pd.concat([df_with_ids, df_no_ids], ignore_index=True)
    
    # Sort by Title to maintain consistency
    df_updated = df_updated.sort_values(by='Title', ascending=True)
    
    # Save updated CSV
    df_updated.to_csv(BGG_DATA_PATH, index=False, encoding='utf-8')
    print(f"BGG data saved to: {BGG_DATA_PATH}")
    print(f"Successfully recompiled ratings for {df_with_ids['BGG_Rating'].notna().sum()} games")


def main():
    parser = argparse.ArgumentParser(description='Fetch BGG ratings and save to CSV')
    parser.add_argument(
        '--n-processes',
        type=int,
        default=1,
        help=f'Number of processes to use for parallel processing (default: {cpu_count()} - all available CPUs)'
    )
    parser.add_argument(
        '--recompile',
        action='store_true',
        help='Recompile ratings from existing BGG data CSV using BGG IDs'
    )
    args = parser.parse_args()
    
    #clean log file
    if ERROR_LOG_PATH.exists():
        ERROR_LOG_PATH.unlink()
        print(f"Cleaned error log file: {ERROR_LOG_PATH}")

    if args.recompile:
        recompile_ratings()
    else:
        fetch_bgg_data(n_processes=args.n_processes)


if __name__ == "__main__":
    main()

