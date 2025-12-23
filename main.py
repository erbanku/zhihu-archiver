import datetime
import os
from shutil import copyfile

from fetcher import fetch

base_path = "docs"


def sort_year_month_dirs(path):
    """Sort year-month directories (e.g., '2022-1', '2022-10') numerically."""
    if '-' in path and all(p.isdigit() for p in path.split('-')):
        return tuple(map(int, path.split('-')))
    return (float('inf'),)


def sort_day_files(filename):
    """Sort day files (e.g., '01.md', '02.md') numerically by day."""
    day = filename.split('.')[0]
    return int(day) if day.isdigit() else float('inf')


def write_content(data, title, time, path):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n")
        f.write(f"抓取于：`{time}`\n\n")
        for i, item in enumerate(data):
            link = item['link']
            title = item['title']
            description = item['description']
            hot = item['hot']
            f.write(f"### [{i + 1}. {title}]({link})\n")
            f.write(f"{hot} 链接：[{link}]({link})\n\n")
            f.write(f"{description}\n\n")


def build_toc():
    with open(os.path.join(base_path, 'toc.md'), 'w', encoding='utf-8') as f:
        f.write(f"* [介绍](/)\n")
        paths = os.listdir(base_path)
        paths.sort(key=sort_year_month_dirs, reverse=True)
        for path in paths:
            full_path = os.path.join(base_path, path)
            if not os.path.isdir(full_path):
                continue
            year, month = path.split('-')
            f.write(f"* [{year} 年 {month} 月]({path}/)\n")
            sub_files = os.listdir(full_path)
            sub_files.sort(key=sort_day_files, reverse=True)
            for file in sub_files:
                if file == 'README.md':
                    continue
                day = file.split('.')[0]
                f.write(f"  * [{month} 月 {day} 日]({path}/{file})\n")


def build_latest():
    """Create a latest.md file that redirects to the most recent scrape."""
    paths = os.listdir(base_path)
    paths = [p for p in paths if os.path.isdir(os.path.join(base_path, p)) and '-' in p]
    paths.sort(key=sort_year_month_dirs, reverse=True)
    
    if not paths:
        return
    
    latest_month = paths[0]
    month_path = os.path.join(base_path, latest_month)
    sub_files = [f for f in os.listdir(month_path) if f.endswith('.md') and f != 'README.md']
    sub_files.sort(key=sort_day_files, reverse=True)
    
    if not sub_files:
        return
    
    latest_file = sub_files[0]
    year, month = latest_month.split('-')
    day = latest_file.split('.')[0]
    
    with open(os.path.join(base_path, 'latest.md'), 'w', encoding='utf-8') as f:
        f.write(f"# 最新热榜存档\n\n")
        f.write(f"正在跳转到最新的热榜存档：[{year} 年 {month} 月 {day} 日]({latest_month}/{latest_file})\n\n")
        f.write(f'<meta http-equiv="refresh" content="0; url=#/{latest_month}/{latest_file}">\n')
        f.write(f'<script>window.location.href = "#/{latest_month}/{latest_file}";</script>\n')


def update_chapter(chapter_str):
    with open(os.path.join(base_path, chapter_str, "README.md"), 'w', encoding='utf-8') as f:
        year, month = chapter_str.split('-')
        f.write(f"# {year} 年 {month} 月\n\n")
        paths = os.listdir(os.path.join(base_path, chapter_str))
        paths.sort(key=sort_day_files)
        for path in paths:
            if path == 'README.md':
                continue
            day = path.split('.')[0]
            f.write(f"+ [{month} 月 {day} 日的知乎热榜存档](/{chapter_str}/{day})\n")


def main():
    data = fetch()
    time = datetime.datetime.now()
    year, month, day = time.year, time.month, time.day
    time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    chapter_str = f"{year}-{month}"
    page_str = f"{day:02}.md"
    title = f"{year} 年 {month} 月 {day} 日的知乎热榜存档"
    if not os.path.exists(os.path.join(base_path, chapter_str)):
        os.mkdir(os.path.join(base_path, chapter_str))

    file_path = os.path.join(base_path, chapter_str, page_str)
    write_content(data, title, time_str, file_path)
    update_chapter(chapter_str)
    copyfile("./README.md", "./docs/README.md")
    build_toc()
    build_latest()


if __name__ == '__main__':
    main()
