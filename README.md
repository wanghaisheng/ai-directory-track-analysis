# AI Directory Track Analysis

This project tracks specified AI directory websites, analyzes changes in their listed URLs, and generates reports.

## Features

- **Domain Tracking**: Monitors a list of AI directory websites specified in `domainlist.csv`.
- **URL Change Detection**: Identifies new URLs added to the tracked directories daily.
- **Data Storage**: Saves all found URLs, daily new URLs, and the last part of URLs (for word frequency analysis) into CSV files within the `results` directory.
- **Reporting Page**: An `index.html` page provides a user interface to:
    - Select a domain and date to view all URLs and newly added URLs.
    - Display a pie chart showing the word frequency analysis of the last parts of URLs, aggregated across all tracked domains for a selected date.

## How it Works

1. **Configuration**: The `domainlist.csv` file contains the list of domains to be tracked.
2. **Tracking Script (`main.py`)**: 
   - Reads the domain list.
   - For each domain, fetches its sitemap or crawls the website to gather URLs.
   - Compares the current URLs with previously stored URLs to identify new additions.
   - Stores data in the `results` directory, organized by domain and date:
     - `[domain]_all.csv`: Contains all URLs ever found for the domain.
     - `[domain]_new_[date].csv`: Contains URLs newly discovered on that date.
     - `[domain]_lastpart_[date].csv`: Contains the last segment of each new URL (split by `/`) for word frequency analysis.
3. **Report Generation (`report.js` and `index.html`)**:
   - `index.html` provides the structure for the report page.
   - `report.js` dynamically populates dropdowns for domain and date selection based on available files in the `results` directory.
   - Fetches and displays data from the corresponding CSV files when a domain and date are selected.
   - Aggregates data from all `_lastpart_[date].csv` files to perform word frequency analysis and renders a pie chart using ECharts.

## Usage

1.  **Setup**: 
    *   Ensure Python is installed.
    *   Install dependencies from `requirements.txt` (if any, primarily for `main.py` execution).
    *   Update `domainlist.csv` with the websites you want to track.
2.  **Run Tracking Script**: Execute `python main.py` to fetch data and generate result files.
3.  **View Report**: Open `index.html` in a web browser to view the analysis report.

## File Structure

- `main.py`: The main Python script for tracking and data generation.
- `domainlist.csv`: List of domains to track.
- `index.html`: The front-end report page.
- `report.js`: JavaScript logic for the report page.
- `ex.md`: An example markdown file (used for populating `domainlist.csv` initially).
- `results/`: Directory containing all generated CSV data files.
  - `[domain]_all.csv`
  - `[domain]_new_[date].csv`
  - `[domain]_lastpart_[date].csv`
- `.github/workflows/`: Contains GitHub Actions workflows for automation (e.g., daily tracking, sitemap pings).

## Contributing

Feel free to contribute by submitting pull requests or opening issues.