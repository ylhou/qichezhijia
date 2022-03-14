#!/urs/bin/env python
# -*- coding:utf-8 -*-
"""

:Author:
:Create:  2022/3/13 3:16 PM
"""
import re
import time
from utils import RequestUtils
from http.cookiejar import Cookie
from requests.cookies import RequestsCookieJar
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as Wait
from selenium.webdriver.support import expected_conditions as Expect
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from pandas import DataFrame

class Qichezhijia:
    __headers = {
        'Referer': 'https://www.autohome.com.cn/',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    }
    __cookie = ""
    def __init__(self):
        self.cookies = None
        self.req = RequestUtils(request_interval_mode=True)
        print('开始采用Cookie信息登陆')
        cookie_arr = self.__cookie.split(';')
        cookie_jar = RequestsCookieJar()
        # 默认设30天过期
        expire = round(time.time()) + 60 * 60 * 24 * 30
        for c in cookie_arr:
            pair = c.strip().split('=')
            cookie = Cookie(0, pair[0], pair[1], None, False, 'movie.douban.com', False, False, '/', True, True, expire,
                            False, None,
                            None, [], False)
            cookie_jar.set_cookie(cookie)
        self.cookies = cookie_jar
        # 先访问一次首页，显得像个正常人
        res = self.req.get_res('https://www.autohome.com.cn/beijing/', headers=self.__headers, cookies=cookie_jar)
        self.__set_cookies(res)
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    def end(self):
        self.driver.close()

    def __set_cookies(self, res):
        if self.cookies is None:
            self.cookies = res.cookies

    def search(self):
        result_list = []
        page_url = "/price/list-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-1.html"
        print("开始执行")
        while page_url is not None:
            res = self.req.get_res(
                "https://car.autohome.com.cn%s" % page_url,
                cookies=self.cookies
            )
            text = res.text
            ehtml = etree.HTML(text)
            # 用户评分
            score_list = ehtml.xpath("//div[@class='list-cont']/div/div[@class='list-cont-main']/div[@class='main-title']/div[@class='score-cont']/span/text()")
            # 简称
            nick_name_list = ehtml.xpath("//div[@class='list-cont']/div/div[@class='list-cont-main']/div[@class='main-title']/a/text()")
            # 详情页
            panel_list = ehtml.xpath("//div[@class='list-cont']/div/div[@class='list-cont-main']/div[@class='main-lever']")
            for i in range(len(score_list)):
                result_dict = {}
                # 无评分的不处理
                if score_list[i].strip() == '暂无':
                    continue
                list_a = panel_list[i].xpath('div[@class="main-lever-right"]/div[@class="main-lever-link"]/a')
                if len(list_a) == 4:
                    config_url = list_a[3].get(key="href")
                    result_dict = self.handle_config_page(config_url)
                result_dict["name"] = nick_name_list[i]
                result_list.append(result_dict)
            page_href = ehtml.xpath("//div[@class='price-page']/div/a[@class='page-item-next']/@href")
            if len(page_href) > 0:
                page_url = page_href[0]
                print("开始执行第%s页" % re.findall(r'.*-(\d+).html',page_url)[0])
            else:
                page_url = None
                print("执行结束")
        return result_list

    def handle_config_page(self, url):
        d = self.driver
        d.get("https://car.autohome.com.cn%s" % url)
        Wait(d, 10).until(
            Expect.presence_of_element_located((By.XPATH, '//table[@id="tab_2"]/tbody/tr/td'))
        )
        time.sleep(1)
        res = {}
        # 型号
        names = d.find_elements(By.XPATH, '//div[@class="carbox"]/div/a')
        if len(names) > 0:
            res["xinghao"] = names[0].accessible_name
            res["url"] = names[0].get_attribute("href")
        # 厂商指导价
        prices = d.find_elements(By.XPATH, '//tr[@id="tr_2000"]/td/div')
        if len(prices) > 0:
            res["price"] = prices[0].text
        # 品牌
        brands = d.find_elements(By.XPATH, '//tr[@id="tr_0"]/td')
        if len(brands) > 0:
            res["brand"] = brands[0].accessible_name
        # 级别
        jibies = d.find_elements(By.XPATH, '//tr[@id="tr_1"]/td')
        if len(jibies) > 0:
            res["jibie"] = jibies[0].accessible_name
        list_tr = d.find_elements(By.XPATH, '//table[@id="tab_1"]/tbody/tr')
        for tr in list_tr:
            th_name = tr.find_element(By.XPATH, 'th').accessible_name
            if th_name == '长度(mm)':
                res["length"] = tr.find_element(By.XPATH, 'td').accessible_name
                continue
            if th_name == '宽度(mm)':
                res["width"] = tr.find_element(By.XPATH, 'td').accessible_name
                continue
            if th_name == '高度(mm)':
                res["height"] = tr.find_element(By.XPATH, 'td').accessible_name
                continue
            if th_name == '车身结构':
                res["jiegou"] = tr.find_element(By.XPATH, 'td').accessible_name
                continue
            if th_name == '车门数(个)':
                res["door"] = tr.find_element(By.XPATH, 'td').accessible_name
                continue
            if th_name == '座位数(个)':
                res["seat"] = tr.find_element(By.XPATH, 'td').accessible_name
                continue
        return res

if __name__ == '__main__':

    # df = DataFrame(
    #     [{'xinghao': '金杯T22 2021款 1.2L基本型SWC12M', 'url': 'https://www.autohome.com.cn/spec/1009773/#pvareaid=2042249',
    #       'price': '3.79', 'brand': '华晨鑫源', 'jibie': '微卡', 'length': '4795', 'width': '1580', 'height': '1900',
    #       'jiegou': '货车',
    #       'door': '4', 'seat': '5', 'name': '金杯T22'},
    #      {'xinghao': '鑫卡S50 2021款 1.6L标准型SWD16MS', 'url': 'https://www.autohome.com.cn/spec/1010908/#pvareaid=2042249',
    #       'price': '4.98', 'brand': '华晨鑫源', 'jibie': '微卡', 'length': '5288', 'width': '1770', 'height': '2065',
    #       'jiegou': '货车',
    #       'door': '2', 'seat': '2', 'name': '鑫卡S50'},
    #      {'xinghao': '鑫卡S52 2021款 1.6L标准型SWD16MS', 'url': 'https://www.autohome.com.cn/spec/1010909/#pvareaid=2042249',
    #       'price': '5.28', 'brand': '华晨鑫源', 'jibie': '微卡', 'length': '5488', 'width': '1770', 'height': '2075',
    #       'jiegou': '货车',
    #       'door': '4', 'seat': '5', 'name': '鑫卡S52'},
    #      {'xinghao': '鑫卡T50 PLUS 2021款 2.0L标准型3.4米SWE20MS',
    #       'url': 'https://www.autohome.com.cn/spec/1010813/#pvareaid=2042249',
    #       'price': '5.88', 'brand': '华晨鑫源', 'jibie': '微卡', 'length': '5772', 'width': '1770', 'height': '2160',
    #       'jiegou': '货车',
    #       'door': '2', 'seat': '2', 'name': '鑫卡T50 PLUS'}])
    q = Qichezhijia()
    res = q.search()
    df = DataFrame(res)
    columns = ['名称', '品牌', '型号', '级别', '长度(mm)', '宽度(mm)', '高度(mm)', '车身结构', '车门数', '座位数', '价格(万元)', '详情页链接']
    df = df.rename(
         columns={'name': '名称', 'brand': '品牌', 'xinghao': '型号', 'jibie': '级别', 'length': '长度(mm)', 'width': '宽度(mm)',
                  'height': '高度(mm)',
                  'jiegou': '车身结构', 'door': '车门数', 'seat': '座位数', 'price': '价格(万元)', 'url': '详情页链接'})
    df.to_excel("result.xlsx", encoding="utf_8", index=False, columns=columns)
    df.to_csv("result.csv", encoding="utf_8", index=False, columns=columns)
    q.end()