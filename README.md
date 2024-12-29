# 爬取巨潮资讯网报告

[TOC]

## 直接使用

### 需要安装的模块

```python
import argparse
import datetime
import time
import re
import requests
import os
import shutil
import tempfile
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import jieba
```

### 在文件夹下新建一个 .py 文件，创建一个字典，并填入参数

```python
customer_req = {
    "file_type": "",  # 文件类型
    "root_file_path": "",  # 文件目录
    "start_date": "",  # 起始日期。默认为 2000-01-01,
    "end_date": None,  # None,  # 结束日期。默认为今天
    "interval": 1,  # 起始日期和结束日期之间的间隔。
    "reverseInterval": 1,  # 从后向前爬
    "workers": 20,  # 同时爬取的线程数。建议最大不要超过CPU线程数的150%。
    "file_download": 1,  # 1：下载到本地； 0：保存到文件
}
```

其中各个参数说明如下：

1. file_type：

   指定报告文件的类型。目前可直接选择的有：A 股一季报、A 股年度报告、A 股半年报、A 股一季报、A 股三季报、A 股业绩报告、三板年度报告。

   如需选择上述内容，则不需要修改代码的其他部分。如需要选择其他类型，需要修改常量文件等。

2. root_file_path：
   指定下载文件的保存路径为 root_file_path\file_type，同时，该路径会生成已下载文件的目录，保存路径和命名规则为 root_file_path\file_type\file_type.txt

3. start_date、end_date、interval：
   指定爬取区间的开始日期、结束日期和每次爬取时指定的日期区间长度。因为巨潮爬取的页码数超过 100 时（100 是网站提供的页码的最大值，超过 100 后，就没办法用浏览器导航到网站了），爬虫可能漏数据，所以最好设置一个较小的区间。

4. workers：
   指定同时进行的线程数。建议最大不要超过CPU线程数的150%。

5. file_download：
   指定文件的保存方式。如选择 1，则将文件按原格式保存到指定文件夹；如选择 0，则将文件名和对应的下载路径保存到指定文件夹下的 .csv 文件中。

### 将以下代码复制到文件中，并运行程序

```python
if __name__ == '__main__':
    main(customer_req)
```

## 自定义下载类型

### 进入 constant.py，在 FILE_INFO_JSON 中新增字典

```Python
"报告名称": {
    "search_keys": [""],
    "is_duplicate_not_allowed": 1,
    "cn_info_column": "",
    "cn_info_category": "",
    "stopwords_list": STOP_WORDS_DICT[""],
    "use_keyword": 0
},
```

其中需要修改的各个参数说明如下：

1. 报告名称：
   自定义所爬取的报告的名称。该名称同时用于命名保存路径下报告文件夹的名称、文件保存记录的名称。

1. search_keys：

   指定在获取该报告时所需要的检索关键词，将其作为元素填入 search_keys 列表中。如果可以使用巨潮提供的分类，则该参数可以留空，仅需要在下面的 cn_info_category 参数中指定巨潮分类。**本代码同时要求需要被下载的文件，其文件名中必须包含至少一个指定的 search_keys。这是为了避免巨潮莫名其妙的模糊检索**。

1. is_duplicate_not_allowed：

   指定该报告是否在企业-年度层面不重复。该数值为0，则说明该报告类型在同一年内允许重复（如招股书、业绩快报等），此时，在命名文件时将会把报告发布日期作为主键。其文件名格式形如：“600272\_2001-01-10\_开开实业\_开开实业招股意向书”。如果该值为0，说明该报告类型在同一年内不允许重复（如年度报告、季度报告等），此时在命名文件时将会生成发布年份，将其作为主键。其文件名格式形如：“000002\_2023\_万科A\_2023年年度报告\_2024-03-29”。**注意，该参数不仅影响文件命名形式。当该值为 1 时候，后续下载将跳过同年且日期较远的报告**。

4. cn_info_column、cn_info_category：

   指定爬取时巨潮资讯网的 cn_info_column 和 cn_info_category。其中 cn_info_column  指的是巨潮的板块，如沪深京（szse）、三板（third）；cn_info_category指的是巨潮为报告类型指定的分类，如沪深京年度报告（category_ndbg_szsh）、沪深京三季度报告（category_sjdbg_szsh）。如果巨潮没有为需要获取的报告类型指定 cn_info_category，意味着需要用关键词检索报告类型，cn_info_category 可以为空。

4. stopwords_list：

   指定爬取报告时的停用词。在爬取时，如果文件标题中含有列表中的词，则跳过。

   该停用词列表需要自行搭建，也可以参考现有报告类型的停用词。

4. use_keyword：

   指定爬取报告时的检索策略。该值为 1 时，利用在 search_keys 中指定的关键词进行检索；该值为 0 时，利用在 cn_info_category 中指定的巨潮分类进行检索。*易知，对于巨潮存在分类的文件类型，如年度报告等，既可以采取关键词检索方式，也可以采取巨潮分类检索方式，仅需要在完善 search_keys 和 cn_info_category 后选择 use_keyword 即可。*

### 后续步骤参考 直接使用 章节

## 备注

1. 如需要进一步指定爬取的行业、板块，修改公告/调研/持续督导等，请进一步修改 constant.py 中的 DATA 参数，并在必要的情况下（如增加循环），修改 FuncScraper.py 中的 main 函数。考虑到功能泛用性和重要程度，本代码不支持在上述步骤中修改。
