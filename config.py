file_type = "A股社会责任"
cnInfoColumn = "szse"
cnInfoCategory = ""

root_file_path = "E:\[待整理]Source_for_sale"

使用关键词而非巨潮分类 = 1  # 0：不含关键词
开启报告不允许年度重复 = 1


start_date = '2023-12-01'  # 起始日期。默认为2000-01-01
end_date = None  # 默认为今天
interval = 20  # 起始日期和结束日期之间的间隔。
reverseInterval = 1

ifMultiThread = 1

"""
解释：

file_type：
    指定报告文件的类型。目前有：
    A股一季报 、 A股年报 、 A股半年报 、 A股三季报 、 A股业绩报告 、 三板年度报告
    选择上述内容后，将自动填充 DATA 参数中的 板块 和 巨潮分类
    如果需要新增，则需要在 cnInfoColumn、和 cnInfoCategory 中添加相应的信息

cnInfoColumn 和 cnInfoCategory：
    指定报告文件的板块和巨潮分类
    在指定了已存在的 file_type 后，这两个变量不生效
    板块默认填写了 szse 即主板，cnInfoColumn 默认为空
    
root_file_path：
    指定下载文件的保存路径为 root_file_path\file_type，同时有
    下载文件的记录表，保存路径为 root_file_path\file_type\file_type.txt

开启包含关键词：
    这个数据用于指定在爬取时是按照巨潮分类爬取还是按照人工提供的关键词爬取
    0：不含关键词，此时使用巨潮提供的 category 参数获取下载列表
    1：包含关键词，此时使用人工提供的 SEARCH_KEY_LIST 组成搜索关键词，这个表在constant.py中
    
开启报告不允许年度重复：
    这个数据用于指定爬取和更新时的逻辑。
    对于问询函、招股书、业绩预告等报告，企业一年不止发布一份，
        此时只需要做到将文件保存下来即可，
    但如年报、季报，企业一年只有一份，此时下载时需要注意只下载最新版
    0：允许年度重复。此时，文件命名格式形如'000625_2004-08-17_长安汽车_长安汽车招股意向书'
    1：不允许年度重复。此时，文件命名格式形如'000016_2011_深康佳A_2011年年度报告_2012-04-26'

start_date、end_date、interval
    指定爬取区间的开始日期、结束日期和跨越区间。
    因为巨潮爬取的页码数超过 100 时
        （100 是网站提供的页码的最大值，超过100后，就没办法用浏览器导航到网站了），
        爬虫可能漏数据，所以最好设置一个较小的区间。

reverseInterval：
    指定是否将时间序列倒过来，也就是从最近的到最早的。
    适合更新数据时使用。

"""
