import concurrent.futures
import requests
import re
import urllib3
import argparse
import colored
from colored import stylize

urllib3.disable_warnings()

parser = argparse.ArgumentParser(description='JS Secret & Link Scanner')
parser.add_argument('-f', '--file',   help='File containing URLs to scan', required=True)
parser.add_argument('-r', '--regex',  help='File containing regex patterns', required=True)
parser.add_argument('-o', '--output', help='Output file to store matches', default='out.txt')
args = parser.parse_args()

# Carrega URLs
with open(args.file, 'r') as f:
    urls = [line.strip() for line in f if line.strip()]

# Carrega patterns uma única vez (não dentro do loop)
with open(args.regex, 'r') as f:
    patterns = [line.strip() for line in f if line.strip()]

print(colored.fg("cyan") + f"[*] Loaded {len(urls)} URLs and {len(patterns)} patterns")
print(colored.fg("cyan") + f"[*] Output: {args.output}\n")

def scan_url(url):
    results = []
    try:
        response = requests.get(
            url,
            verify=False,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )
        content = response.text

        for pattern in patterns:
            try:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for matchNum, match in enumerate(matches, start=1):
                    result = {
                        "url": url,
                        "pattern": pattern,
                        "match": match.group(),
                        "matchNum": matchNum
                    }
                    results.append(result)
            except re.error as e:
                print(colored.fg("yellow") + f"[!] Invalid regex '{pattern}': {e}")

    except requests.exceptions.RequestException as e:
        print(colored.fg("yellow") + f"[!] Error fetching {url}: {e}")

    return results

# Processa URLs em paralelo
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    future_to_url = {executor.submit(scan_url, url): url for url in urls}

    with open(args.output, 'a') as out_file:
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            print(colored.fg("white") + f"[*] Scanning: {url}")

            try:
                findings = future.result()
                for f in findings:
                    print(colored.fg("green")  + f"    [+] Pattern : {f['pattern']}")
                    print(colored.fg("red")    + f"    [+] Match {f['matchNum']}: {f['match']}\n")

                    out_file.write(f"URL: {f['url']}\n")
                    out_file.write(f"Pattern: {f['pattern']}\n")
                    out_file.write(f"Match {f['matchNum']}: {f['match']}\n")
                    out_file.write("-" * 60 + "\n")

            except Exception as e:
                print(colored.fg("yellow") + f"[!] Exception for {url}: {e}")
