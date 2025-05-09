import os
import csv
import sys
from datetime import datetime
import requests
import re
# sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from parse_url_from_sitemap import collect_all_url_details_from_sitemap

def read_domains(domain_file):
    with open(domain_file, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

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

def aggregate_all_domains(domain_file, output_file):
    domains = read_domains(domain_file)
    all_url_details = []
    today = datetime.now().strftime('%Y-%m-%d')
    for domain in domains:
        sitemap_url = get_sitemap_url(domain)
        sitemap_urls_to_try = [sitemap_url]
        if not check_url_200(sitemap_url):
            print(f"Default sitemap not found for {domain}, checking robots.txt...")
            robots_sitemaps = get_robots_sitemaps(domain)
            if robots_sitemaps:
                sitemap_urls_to_try = robots_sitemaps
            else:
                print(f"No sitemap found in robots.txt for {domain}")
                continue
        for sitemap_url in sitemap_urls_to_try:
            print(f'Processing {sitemap_url}')
            try:
                url_details = collect_all_url_details_from_sitemap(sitemap_url, today=today)
                for d in url_details:
                    d['domain'] = domain
                all_url_details.extend(url_details)
                break  # Only process the first working sitemap
            except Exception as e:
                print(f'Failed to process {sitemap_url}: {e}')
    # Save all results
    if all_url_details:
        fieldnames = ['domain', 'loc', 'lastmodified', 'added_date']
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for d in all_url_details:
                writer.writerow(d)
        print(f"Aggregated {len(all_url_details)} URLs from {len(domains)} domains. Saved to {output_file}")
    else:
        print("No URLs found.")

def main():
    domain_file = 'domainlist.csv'
    output_file = 'all_domains_url_details.csv'
    aggregate_all_domains(domain_file, output_file)

if __name__ == '__main__':
    main()

