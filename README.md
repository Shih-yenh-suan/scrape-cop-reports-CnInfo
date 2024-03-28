# 爬取企业报告

## 使用方法：

**1. 新建一个 py 文件，创建一个字典，并填入参数**

```python
customer_req = {
    "file_type": "A股年报",  # 文件类型
    "root_file_path": "E:\[待整理]Source_for_sale",  # 文件目录
    "使用关键词而非巨潮分类": 0,
    "start_date": "2023-12-01",  # 起始日期。默认为2000-01-01,
    "end_date": None,  # 结束日期。默认为今天
    "interval": 20,  # 起始日期和结束日期之间的间隔。
    "reverseInterval": 1,  # 从后向前爬
    "ifMultiThread": 1,  # 多线程
}

```

其中各个参数说明如下：

1. file_type：
   指定报告文件的类型。目前有：
   A 股一季报、A 股年度报告、A 股半年报、A 股一季报、A 股三季报、A 股业绩报告、三板年度报告
   选择上述内容后，将自动填充 DATA 参数中的 板块 和 巨潮分类
   如果需要新增，则需要在 cnInfoColumn、和 cnInfoCategory 中添加相应的信息

2. root_file_path：
   指定下载文件的保存路径为 root_file_path\file_type，同时有
   下载文件的记录表，保存路径为 root_file_path\file_type\file_type.txt

3. 使用关键词而非巨潮分类：
   这个数据用于指定在爬取时是按照巨潮分类爬取还是按照人工提供的关键词爬取
   0：不含关键词，此时使用巨潮提供的 category 参数获取下载列表
   1：包含关键词，此时使用人工提供的 SEARCH_KEY_LIST 组成搜索关键词，这个表在 constant.py 中
   如果提供的 file_type 不在上面，则需要在主函数中添加相应的信息；特别地，
   如果使用关键词，还需要在 constant 中更新关键词

4. start_date、end_date、interval
   指定爬取区间的开始日期、结束日期和跨越区间。
   因为巨潮爬取的页码数超过 100 时
   （100 是网站提供的页码的最大值，超过 100 后，就没办法用浏览器导航到网站了），
   爬虫可能漏数据，所以最好设置一个较小的区间。

5. reverseInterval：
   指定是否将时间序列倒过来，也就是从最近的到最早的。
   适合更新数据时使用。

6. ifMultiThread:
   指定是否使用多线程。

**2. 使用如下方式进行爬取**

```python
from FuncScraper import *
if __name__ == '__main__':
    DATA_RANGE = create_date_intervals(
        customer_req["interval"], customer_req["start_date"], customer_req["end_date"])
    if customer_req["reverseInterval"] == 1:
        DATA_RANGE = DATA_RANGE[::-1]
    if customer_req["使用关键词而非巨潮分类"] == 1:
        for searchkey in FILE_INFO_JSON[customer_req["file_type"]]["search_keys"]:
            print(f"当前检索关键词：{searchkey}")
            DATA['searchkey'] = searchkey
            FuncScraper(customer_req).CircleScrape(DATA_RANGE)
    else:
        FuncScraper(customer_req).CircleScrape(DATA_RANGE)
    print('下载完毕')
```
