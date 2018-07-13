from github import Github, ContentFile
from getpass import getpass
from queue import Queue
import logging
from .cloopen import Cloopen
import re

client = Github(login_or_token=input('User name for github: '), password=getpass(), per_page=20)


def extract(content):
    """
    从搜索结果中抽取字段
    """

    # 提取主要字段
    def search_field(keyword_and_pattern):
        keyword, pattern = keyword_and_pattern
        for line in content.split('\n'):
            if re.search(keyword, line, re.IGNORECASE):
                match = re.search(pattern, line)
                if match:
                    return match.group(0)

    account_sid, account_token, appid = map(search_field, [('sid', '[a-z0-9]{32}'),
                                                           ('token', '[a-z0-9]{32}'),
                                                           ('app.?id', '[a-z0-9]{32}')])
    if all([account_sid, account_token, appid]):
        return account_sid, account_token, appid


def search_all(keyword, max_page=10, greenlet_count=4):
    """
    通过协程并发搜索
    :param max_page 最大页数
    :param greenlet_count 协程数量
    """
    paging = client.search_code(keyword)
    total_page = min(max_page, paging.totalCount / 20)
    tasks = Queue()
    for i in range(1, total_page + 1):
        tasks.put(i)
    accounts = set()

    def _search():
        while not tasks.empty():
            try:
                page_no = tasks.get(block=False)
                logging.info('正在搜索第%d页' % page_no)
                contents = map(lambda x: x.decoded_content.decode('utf-8'), paging.get_page(page_no))
                accounts.update({Cloopen(*p) for p in map(extract, contents) if p})
            except Exception as err:
                logging.error(err)
                break

    import gevent
    gevent.joinall([gevent.spawn(_search) for _ in range(greenlet_count)])
    return accounts


def search(keyword='app.cloopen.com', **qulifiers):
    """
    同步搜索
    """
    paging = client.search_code(keyword, **qulifiers)
    # 最多只能查看1000条搜索结果
    for i in range(1, min(50, paging.totalCount / 20)):
        for item in paging.get_page(i):
            extracted = extract(item.decoded_content.decode('utf-8'))
            if extracted:
                yield extracted
