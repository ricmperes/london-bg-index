from pathlib import Path

import numpy as np
import pandas as pd

# Get the project root directory (parent of scripts directory)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

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
    df['BGG_rank'] = np.zeros(len(df))
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
    table_html = df.to_html(classes='data-table', table_id='board-games-table', index=False, escape=False)
    
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


def main():
    df = read_file()
    make_html_page(df)


if __name__ == "__main__":
    main()