import datetime
from hashlib import md5
from urllib.request import Request
from urllib.request import urlopen
from base64 import b64encode
import json


class Cloopen:
    URL = 'https://app.cloopen.com:8883/2013-12-26'

    def __init__(self, sid, token, appid):
        self.sid = sid
        self.token = token
        self.appid = appid
        self.template_ids = []
        self.balance = 0.0

    def load_valid_template_ids(self):
        if self.template_ids:
            return self.template_ids
        resp = self.query_sms_template('')
        if resp['statusCode'] == '000000':
            self.template_ids = [d['id'] for d in resp['TemplateSMS'] if d['status'] == '1']
            return self.template_ids

    def send_sms(self, recvr, template_id, * datas):
        body = {'to': recvr, 'datas': datas, 'templateId': template_id, 'appId': self.appid}
        return self._send_request("/Accounts/" + self.sid+ "/SMS/TemplateSMS", body=json.dumps(body))

    def query_sms_template(self, template_id):
        """
        查询短信模板
        :param template_id 模板Id，不带此参数查询全部可用模板
        """
        body = {'appId': self.appid, 'templateId': template_id}
        return self._send_request('/Accounts/' + self.sid + '/SMS/QuerySMSTemplate', json.dumps(body))

    def query_account_info(self):
        return self._send_request("/Accounts/" + self.sid + "/AccountInfo")

    def _send_request(self, path, body=None):
        # 生成sig
        ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        signature = self.sid + self.token + ts
        sig = md5(signature.encode('utf-8')).hexdigest().upper()
        # basic auth
        req = Request(Cloopen.URL + path + "?sig=" + sig)
        req.add_header('Authorization', b64encode((self.sid+':'+ts).encode('utf-8')).strip())
        req.add_header('Accept', 'application/json')
        req.add_header('Content-Type', 'application/json;charset=utf-8')
        if body:
            req.data = body.encode('utf-8')
        with urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def __str__(self, *args, **kwargs):
        return 'Account: {sid: %s, token: %s, appid: %s, template_ids: %s, balance: %.2f}' % \
               (self.sid, self.token, self.appid, str(self.template_ids), self.balance)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.sid == other.sid
        return False

    def __hash__(self, *args, **kwargs):
        return hash(self.sid)








