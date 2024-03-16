# -*- encoding: utf-8 -*-
import requests
import re
import datetime
import time
import os
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor
from config import *
from constant import *

# 确定板块
# 根据用户提供的 file_type 参数，从 CATEGORY_AND_NAME 中检索
# 或根据用户自定义的 cnInfoColumn 确定
try:
    DATA['column'] = CATEGORY_AND_NAME[file_type][1]
except KeyError:
    DATA['column'] = cnInfoColumn

# 确定检索模式
# 如果开启了关键词，就不需要再将检索范围限制到巨潮分类里面了，
    # 直接用停用词就能筛掉不需要的报告
# 如果未开启关键词，必须使用巨潮分类。
    # 不然的话就相当于什么限制都没有了，效率很低。
    # 分类也是根据用户提供的 file_type 参数，从 CATEGORY_AND_NAME 中检索
    # 或根据用户自定义的 cnInfoCategory 确定
if 开启包含关键词 == 1:
    DATA['searchkey'] = ";".join(SEARCH_KEY_LIST[file_type])
else:
    try:
        DATA['category'] = CATEGORY_AND_NAME[file_type][0]
    except:
        DATA['category'] = cnInfoCategory

# 确定保存路径
SAVING_PATH = f'{root_file_path}\{file_type}'
LOCK_FILE_PATH = f'{root_file_path}\{file_type}\{file_type}.txt'

# 确定停词列表
# 默认使用 normal_sw 停用词
if file_type == "A股问询函":
    STOP_WORDS = STOP_WORDS_DICT["wenxun_sw"]
elif file_type == "A股招股书":
    STOP_WORDS = STOP_WORDS_DICT["zhaogu_sw"]
elif file_type == "A股业绩预告":
    STOP_WORDS = STOP_WORDS_DICT["yugao_sw"]
elif file_type in ["A股半年报", "A股三季报", "A股一季报"]:
    STOP_WORDS = STOP_WORDS_DICT["quarter_sw"]
else:
    STOP_WORDS = STOP_WORDS_DICT["normal_sw"]


def process_page_for_downloads(pageNum):
    """处理指定页码的公告信息并下载相关文件"""
    DATA['pageNum'] = pageNum

    # 向网站获取内容和总页数，必须分开获取，否则容易报错
    result = retry_on_failure(lambda:
                              requests.post(URL, data=DATA, headers=HEADERS).json()['announcements'])
    maxpage = retry_on_failure(lambda:
                               requests.post(URL, data=DATA, headers=HEADERS).json()['totalpages']) + 1
    if result is None or pageNum > maxpage:
        print(f"第 {pageNum} 页已无内容或超出最大页数，退出")
        return False

    # 决定是否开启多线程
    if ifMultiThread == 1:
        # 开启多线程处理
        print(f'多线程处理第 {pageNum} 页，共 {maxpage} 页')
        with ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(process_announcements, result)
        return True
    else:
        print(f'单线程处理第 {pageNum} 页，共 {maxpage} 页')
        for i in result:
            process_announcements(i)


def process_announcements(i):
    """处理返回的json文件"""
    # 处理标题
    title = i['announcementTitle']
    title = re.sub(r'(<em>|</em>|[\/:*?"<>| ])', '', title)
    # 获取下载链接
    downloadUrl = 'http://static.cninfo.com.cn/' + i['adjunctUrl']
    # 处理时间
    announcementTime = i["announcementTime"]/1000
    announcementTime = datetime.datetime.fromtimestamp(
        announcementTime).strftime('%Y-%m-%d')
    # 处理简称
    secName = i['secName'] if i['secName'] is not None else 'None'
    secName = re.sub(r'\*ST', '＊ST', secName)
    secName = re.sub(r'(<em>|</em>|em|[\/:*?"<>| ])', '', secName)
    secName = re.sub(r'Ａ', 'A', secName)
    secName = re.sub(r'Ｂ', 'B', secName)
    # 处理代码。如果代码为空，则从企业唯一的id获得
    secCode = i['secCode']
    if secCode == None:
        secCode = i['orgId'][5:11]
    # 处理文件后缀
    file_type = 'html' if i['adjunctType'] == None else 'pdf'
    # 整合文件名
    # fileName：保存到本地的文件名
    # fileShortName：输出打印时显示的名字
    if 开启报告不允许年度重复 == 1:
        # 开启报告不允许年度重复时，用企业-年份作为主键
        # 默认从标题中检索年份数据，
        # 如果标题中没说，就从发布日期中减1
        # 因为一年发布一份的报告一般是次年更新，所以年份减1
        seYear = re.search(r'20\d{2}', title)
        seYear = str(int(announcementTime[0:4])
                     ) if seYear is None else seYear.group()
        fileShortName = f'{secCode}_{seYear}_{secName}'
        fileName = f'{fileShortName}_{title}_{announcementTime}.{file_type}'
    else:
        fileShortName = f'{secCode}_{announcementTime}_{secName}'
        fileName = f'{fileShortName}_{title}.{file_type}'

    # 接下来开始执行下载前的判断

    # 1. 如果要求标题中带有关键词，则跳过下载不包含关键词的报告
    if 开启包含关键词 == 1:
        if not any(re.search(k, title) for k in SEARCH_KEY_LIST[file_type]):
            print(f'{fileShortName}：\t不含关键词 ({title})')
            return

    # 2. 对于标题包含停用词的报告，跳过下载
    if any(re.search(k, title) for k in STOP_WORDS):
        print(f'{fileShortName}：\t包括停用词 ({title})')
        return

    # 3. 对于当前目录下已经存在的报告，跳过下载
        # # 如果没有保存路径，则创建之
    if not os.path.exists(SAVING_PATH):
        os.makedirs(SAVING_PATH)
    filePath = os.path.join(SAVING_PATH, fileName)
    if os.path.exists(filePath):
        # # 判断是否存在
        print(f'{fileShortName}：\t已存在，跳过下载')
        return

    # 4. 对于记录在文件中的报告，跳过下载
        # # 如果没有记录文件，则创建之
    if not os.path.exists(LOCK_FILE_PATH):
        with open(LOCK_FILE_PATH, 'w') as file:
            pass
        # # 对于已经记录在表中的文件，跳过下载
    with open(LOCK_FILE_PATH, 'r', encoding='utf-8', errors='ignore') as lock_file:
        downloaded_files = lock_file.readlines()
        if f'{fileName}\n' in downloaded_files:
            print(f'{fileShortName}：\t已记录在文件中')
            return
    # 在不允许年度重复的情况下，对于没有记录但是已经有同一代码、同一时间报告的文件，比对日期，如果日期更新则下载，否则不下载
    if 开启报告不允许年度重复 == 1:
        # # 根据企业的代码和年份，在记录中寻找其发布日期，保存到 matching_files
        pattern = re.compile(
            rf"{re.escape(f'{secCode}_{seYear}')}_.*_.*_(\d{{4}}-\d{{2}}-\d{{2}}).*")
        matching_files = [
            f for f in downloaded_files if pattern.match(f)]
        # # 如果存在这样的文件，执行比对
        if len(matching_files) != 0:
            # # 获取存在的文件的最大日期 latest_announcement_time，
            # # 以及对应文件 latest_file
            # # 尽管记录中的文件极大概率是不重复的，但也不一定，比如pdf和txt的文件都在里面，或者里面有历史文件的下载记录。
            latest_file = max(matching_files, key=lambda x: datetime.datetime.strptime(
                re.search(r"_(\d{4}\-\d{2}\-\d{2})\.\w+", x).group(1), "%Y-%m-%d"))
            latest_announcement_time = datetime.datetime.strptime(
                re.search(r"_(\d{4}-\d{2}-\d{2})\.\w+", latest_file).group(1), "%Y-%m-%d")
            # # 获取当前可能需要下载的报告日期，并减去1天，因为不同来源或下载时记录的文件，由于四舍五入会差一天
            file_time = datetime.datetime.strptime(
                announcementTime, "%Y-%m-%d") - datetime.timedelta(days=1)
            # # 如果日期更新，则下载，否则不下载
            if file_time > latest_announcement_time:
                print(
                    f'{fileShortName}：\t有新版不下载:{str(latest_announcement_time)[:10]}')
                return
            print(f'{fileShortName}：\t需要更新:{latest_announcement_time}')
    # 一切都符合要求，分块下载文件，并只在下载完成后才保存到本地
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


def CircleScrape():
    pageNum = 1
    while True:
        if not process_page_for_downloads(pageNum):
            break
        # 有时候会出现奇怪的bug导致迟迟无法结束，故设定500页的最大值强行停止
        if pageNum >= 500:
            break
        pageNum += 1


def create_date_intervals(interval, start_date="2000-01-01", end_date=None):
    # 将字符串日期转换为datetime对象
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


if __name__ == '__main__':
    DATA_RANGE = create_date_intervals(interval, start_date, end_date)
    if reverseInterval == 1:
        DATA_RANGE = DATA_RANGE[::-1]
    for i, seDate in enumerate(DATA_RANGE):
        DATA['seDate'] = seDate
        print(f"当前爬取区间：{seDate}，为列表第 {i+1}/{len(DATA_RANGE)} 个")
        CircleScrape()
        if seDate[3] != seDate[14]:
            print(f'{seDate[:4]} 年的年报已下载完毕.')
