import os
import csv
from datetime import datetime
import requests
import re
import glob # For finding file patterns
from parse_url_from_sitemap import collect_all_url_details_from_sitemap

def read_domains(domain_file):
    with open(domain_file, 'r', encoding='utf-8') as f:
        return [line.strip().replace('www.','') for line in f if line.strip()]

def get_sitemap_url(domain):
    if domain.startswith('http://') or domain.startswith('https://'):
        base = domain
    else:
        base = 'https://' + domain
    return base.rstrip('/') + '/sitemap.xml'

def check_url_200(url):
    try:
        resp = requests.head(url, timeout=10, allow_redirects=True)
        return resp.status_code == 200
    except Exception:
        return False

def get_robots_sitemaps(domain):
    if domain.startswith('http://') or domain.startswith('https://'):
        base = domain
    else:
        base = 'https://' + domain
    robots_url = base.rstrip('/') + '/robots.txt'
    try:
        resp = requests.get(robots_url, timeout=10)
        if resp.status_code == 200:
            sitemaps = re.findall(r'^Sitemap:\s*(\S+)', resp.text, re.MULTILINE)
            return sitemaps
    except Exception:
        pass
    return []

def get_url_last_part(url):
    url = url.split('?')[0].split('&')[0]
    parts = url.rstrip('/').split('/')
    return parts[-1] if parts else ''

def aggregate_all_domains(domain_file):
    domains = read_domains(domain_file)
    today = datetime.now().strftime('%Y-%m-%d')
    date_folder = f"results"
    if not os.path.exists(date_folder):
        os.makedirs(date_folder)
    progress_file = os.path.join(date_folder, f'domain_progress_{today}.txt')
    failed_file = os.path.join(date_folder, f'failed_domains_{today}.txt')
    processed_domains = set()
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as pf:
            processed_domains = set([line.strip() for line in pf if line.strip()])
    failed_domains = set()
    if os.path.exists(failed_file):
        with open(failed_file, 'r', encoding='utf-8') as ff:
            failed_domains = set([line.strip() for line in ff if line.strip()])
    for domain in domains:
        if domain in processed_domains:
            continue
        print(f"Processing {domain}")
        domain_base_name = domain.replace('.', '_') # Used for consistent file naming
        sitemap_url = get_sitemap_url(domain)
        sitemap_urls_to_try = [sitemap_url]
        if not check_url_200(sitemap_url):
            print(f"Default sitemap not found for {domain}, checking robots.txt...")
            robots_sitemaps = get_robots_sitemaps(domain)
            if robots_sitemaps:
                sitemap_urls_to_try = robots_sitemaps
            else:
                print(f"No sitemap found in robots.txt for {domain}")
                failed_domains.add(domain)
                with open(failed_file, 'a', encoding='utf-8') as ff:
                    ff.write(domain + '\n')
                with open(progress_file, 'a', encoding='utf-8') as pf:
                    pf.write(domain + '\n')
                continue
        success = False
        for sitemap_url in sitemap_urls_to_try:
            try:
                url_details = collect_all_url_details_from_sitemap(sitemap_url, today=today)
                urls = set([d['loc'] for d in url_details if 'loc' in d])
                
                # Path for the main "_all.csv" file which acts as the current/hot storage
                domain_all_file_path = os.path.join(date_folder, f"{domain_base_name}_all.csv")
                
                existing_urls = set()
                
                # Read from the main _all.csv (current/hot data)
                if os.path.exists(domain_all_file_path):
                    try:
                        with open(domain_all_file_path, 'r', encoding='utf-8') as f:
                            reader = csv.reader(f)
                            for row in reader:
                                if row: # Ensure row is not empty
                                    existing_urls.add(row[0])
                    except Exception as e:
                        print(f"Error reading existing URLs from {domain_all_file_path}: {e}")

                # Read from part files (archived data)
                part_file_pattern = os.path.join(date_folder, f"{domain_base_name}_all_part*.csv")
                part_files = sorted(glob.glob(part_file_pattern))
                for part_file in part_files:
                    try:
                        with open(part_file, 'r', encoding='utf-8') as f:
                            reader = csv.reader(f)
                            for row in reader:
                                if row: # Ensure row is not empty
                                    existing_urls.add(row[0])
                    except Exception as e:
                        print(f"Error reading existing URLs from part file {part_file}: {e}")

                new_urls = urls - existing_urls
                
                # 追加新url到域名文件 (always domain_all_file_path, which is the "_all.csv")
                if new_urls:
                    try:
                        with open(domain_all_file_path, 'a', encoding='utf-8', newline='') as f:
                            writer = csv.writer(f)
                            for url_to_add in sorted(list(new_urls)):
                                writer.writerow([url_to_add])
                    except Exception as e:
                        print(f"Error appending new URLs to {domain_all_file_path}: {e}")
                
                # Check if domain_all_file_path (the "hot" _all.csv) needs to be archived due to size
                max_file_size_bytes = 50 * 1024 * 1024  # 90MB
                if os.path.exists(domain_all_file_path) and os.path.getsize(domain_all_file_path) > max_file_size_bytes:
                    current_size_mb = os.path.getsize(domain_all_file_path) / (1024 * 1024)
                    print(f"{domain_all_file_path} (size: {current_size_mb:.2f}MB) exceeds {max_file_size_bytes / (1024*1024):.0f}MB limit, archiving...")
                    
                    part_num = 1
                    while True:
                        new_part_file_path = os.path.join(date_folder, f"{domain_base_name}_all_part{part_num}.csv")
                        if not os.path.exists(new_part_file_path):
                            break
                        part_num += 1
                    
                    try:
                        print(f"Renaming {domain_all_file_path} to {new_part_file_path}")
                        os.rename(domain_all_file_path, new_part_file_path)
                    except Exception as e:
                        print(f"Error renaming/archiving {domain_all_file_path} to {new_part_file_path}: {e}")

                # 每日新增url文件
                daily_new_file = os.path.join(date_folder, f"{domain_base_name}_new_{today}.csv")
                if new_urls:
                    with open(daily_new_file, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f)
                        for url_item in sorted(list(new_urls)):
                            writer.writerow([url_item])
                else:
                    open(daily_new_file, 'w', encoding='utf-8').close() # Create/clear the file

                # 每日新增url最后一段文件
                daily_lastpart_file = os.path.join(date_folder, f"{domain_base_name}_lastpart_{today}.csv")
                if new_urls:
                    with open(daily_lastpart_file, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f)
                        for url_item in sorted(list(new_urls)):
                            writer.writerow([get_url_last_part(url_item)])
                else:
                    open(daily_lastpart_file, 'w', encoding='utf-8').close() # Create/clear the file
                success = True
                break
            except Exception as e:
                print(f'Failed to process {sitemap_url}: {e}')
        if not success:
            failed_domains.add(domain)
            with open(failed_file, 'a', encoding='utf-8') as ff:
                ff.write(domain + '\n')
        with open(progress_file, 'a', encoding='utf-8') as pf:
            pf.write(domain + '\n')

def main():
    domain_file = 'domainlist.csv'
    aggregate_all_domains(domain_file)

if __name__ == '__main__':
    main()

