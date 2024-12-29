from constant import *


def create_date_intervals(interval, start_date="2000-01-01", end_date=None):
    """将字符串日期转换为datetime对象"""
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    # 如果没有提供结束日期，则默认为今天
    if end_date is None:
        end = datetime.datetime.today()
    else:
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    # 初始化日期列表
    intervals = []
    # 当前开始日期
    current_start = start
    while current_start < end:
        # 计算当前结束日期
        current_end = current_start + datetime.timedelta(days=interval)
        # 如果当前结束日期超过了总结束日期，就将其设置为总结束日期
        if current_end > end:
            current_end = end
        # 将当前日期区间添加到列表
        intervals.append(
            f"{current_start.strftime('%Y-%m-%d')}~{current_end.strftime('%Y-%m-%d')}")
        # 更新下一个区间的开始日期
        current_start = current_end + datetime.timedelta(days=1)
    return intervals


def retry_on_failure(func):
    """对于请求失败的情况，暂停一段时间"""
    pause_time = 3
    try:
        result = func()
        return result
    except Exception as e:
        print(f'Error: {e}, 暂停 {pause_time} 秒')
        time.sleep(pause_time)
        return retry_on_failure(func)


def get_CSR_tag(title):
    csr_dict = ["社会责任", "CSR"]
    esg_dict = ["ESG", "管治", "治理"]
    sd_dict = ["可持续"]
    env_dict = ["环境报告书"]
    tags = []
    for csr_word in csr_dict:
        if csr_word in title:
            tags.append("#CSR")
            break
    for esg_word in esg_dict:
        if esg_word in title:
            tags.append("#ESG")
            break
    for sd_word in sd_dict:
        if sd_word in title:
            tags.append("#SD")
            break
    for env_dict in env_dict:
        if env_dict in title:
            tags.append("#ENV")
            break
    return ''.join(tags)


def compare_latest_report(downloaded_files, announcementTime, fileShortName):
    # 根据企业的代码和年份，在记录中寻找其发布日期，保存到 matching_files
    pattern = re.compile(
        rf"{re.escape(f'{fileShortName}')}_.*_(\d{{4}}-\d{{2}}-\d{{2}}).*")
    matching_files = [
        f for f in downloaded_files if pattern.match(f)]
    # 如果存在这样的文件，执行比对
    if len(matching_files) != 0:
        # 获取存在的文件的最大日期 time_in_downloaded_files，
        # 以及对应文件 latest_file
        # 尽管记录中的文件极大概率是不重复的，但也不一定，比如pdf和txt的文件都在里面，或者里面有历史文件的下载记录。
        latest_file = max(matching_files, key=lambda x: datetime.datetime.strptime(
            re.search(r"_(\d{4}\-\d{2}\-\d{2})\.\w+", x).group(1), "%Y-%m-%d"))
        time_in_downloaded_files = datetime.datetime.strptime(
            re.search(r"_(\d{4}-\d{2}-\d{2})\.\w+", latest_file).group(1), "%Y-%m-%d")
        # 获取当前可能需要下载的报告日期，并减去1天，因为不同来源或下载时记录的文件，由于四舍五入会差一天
        time_of_downloading_file = datetime.datetime.strptime(
            announcementTime, "%Y-%m-%d")
        # 如果日期更新，则下载，否则不下载
        if time_of_downloading_file - time_in_downloaded_files <= datetime.timedelta(days=1):
            print(
                f'{fileShortName}：\t有新版不下载:{str(time_in_downloaded_files)[:10]}')
            return False
        print(f'{fileShortName}：\t需要更新:{time_in_downloaded_files}')


def download_file(downloadUrl, filePath, fileShortName, LOCK_FILE_PATH, fileName):
    """分块下载文件，并只在下载完成后才保存到本地"""
    try:
        with requests.get(downloadUrl, stream=True) as r:
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
                temp_name = tmp_file.name
        shutil.move(temp_name, filePath)
        print(f'{fileShortName}：\t已下载到 {filePath}')
        # 下载完成后，保存文件名到记录中。
        with open(LOCK_FILE_PATH, 'a', encoding='utf-8', errors='ignore') as lock_file:
            lock_file.write(f'{fileName}\n')
    except Exception as e:
        print(f'{fileShortName}： \t下载失败: {e}')


def save_to_csv(downloadUrl, fileName, fileShortName, root_file_path, file_type):
    # 从fileName中获取内容
    fileName = os.path.splitext(fileName)[0]
    # 分列文件名，获取各个列
    split_name = fileName.split('_')

    # 根据分列的结果来决定列名和是否继续
    if len(split_name) == 6:
        column_names = ['股票代码', '年份', '类型', '股票简称', '文件标题', '发布日期']
    elif len(split_name) == 5:
        column_names = ['股票代码', '年份', '股票简称', '文件标题', '发布日期']
    elif len(split_name) == 4:
        column_names = ['股票代码', '发布日期', '股票简称', '文件标题']
    else:
        print("文件名分列结果不符合要求，跳过。")
        return
    new_entry = dict(zip(column_names, split_name))
    new_entry['下载链接'] = downloadUrl

    # 检查CSV文件是否存在，如果存在就加载，否则创建一个空的DataFrame
    csv_filename = f'{root_file_path}\{file_type}\{file_type}.csv'
    if not os.path.exists(csv_filename):
        df = pd.DataFrame(columns=new_entry.keys())
        df.to_csv(csv_filename, index=False)
    df = pd.read_csv(csv_filename, encoding='utf-8-sig',
                     encoding_errors="ignore", dtype=str)
    # 检查文件是否存在。在这里可以用链接作为主键
    if downloadUrl in df['下载链接'].values:
        print(f'{fileShortName}：\t链接已存在')
        return

    # 将新的文件名和下载链接添加到DataFrame中
    df = pd.DataFrame([new_entry], columns=new_entry.keys())

    # 将DataFrame保存到CSV文件中
    df.to_csv(csv_filename, mode='a', header=False, index=False)
    print(f'{fileShortName}：\t已保存记录')


# 使用示例
# save_to_csv('example_file.txt', 'http://example.com/download/link')
