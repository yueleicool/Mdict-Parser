import re

import bs4
from bs4 import BeautifulSoup

from mdict_query import IndexBuilder

# 测试
builder = IndexBuilder('柯林斯高阶双解.mdx')

""" soup = BeautifulSoup(builder.mdx_lookup('beautiful')[0], features="lxml")
print(soup.find_all('div', 'vExplain_r')[0].contents) """


""" with open('./dicta.html', 'w+') as wp:
    wp.write(builder.mdx_lookup('fuck')[0]) """


class Mdx_to_mongodb():

    def __init__(self):
        self.__builder = IndexBuilder('柯林斯高阶双解.mdx')
        self.__star_parse_dict = {
            star: level+1 for star, level in zip(self.__generate_star(), range(5))}

    def __generate_star(self):
        """生成星级序列"""
        return [('★' * (i+1) + '☆' * (4-i)) for i in range(5)]

    def __generate_soup(self, word):
        """产出 BeautifulSoup 实例"""
        return BeautifulSoup(
            self.__builder.mdx_lookup(str(word))[0], features="lxml")

    def __normalize_title_info(self, info):
        """以元组形式输出规范化后的单词头信息"""
        return tuple(map(lambda n: n.string.strip(), info))

    def __normalize_main_en_info(self, info):
        """以字符串形式输出规范化后的单词英文总释义"""
        return ' '.join([item.string.strip() for item in info])

    def __normalize_multi_word_type(self, info):
        """以元组形式重整不同的单词变化"""
        _ = []

        for i in info:
            title = i.find_all('b', 'text_blue')[0].contents[0]

            ins = i.find_all('p')
            example = list(map(lambda n: self.__parse_eng_part(str(n)), ins))
            example = [example[i:i+2] for i in range(0, len(example), 2)]
            _.append((title, example))

        return _

    def __normalize_caption(self, info):
        """"""
        spans = info.find('div', 'caption').find_all('span')
        _ = list(map(lambda n: n.string, spans[:-1]))

        # 搭配模式等存在多层嵌套
        if (len(spans) != 3):
            for i in spans[-1].find('div').descendants:
                if type(i) is bs4.element.NavigableString:
                    _.append(i)

        usage_en = [
            i.string
            for i in info.find('div', 'caption').contents[3:-1]
        ]
        _.append(''.join(usage_en))

        return _

    def __parse_example_html(self, html):
        _ = []
        for i in html.descendants:
            if type(i) is bs4.element.NavigableString:
                _.append(i)

        return [''.join(_[:-1]), _[-1]]

    def __normalize_example(self, info):
        _ = []
        li = info.find_all('li')

        return list(map(self.__parse_example_html, li))

    def __generate_word_detail(self, word, _class='collins_content', multi=False):
        """单词详情搜索封装"""
        if multi:
            return tuple(self.__generate_soup(word).find_all('div', _class))
        else:
            return tuple(self.__generate_soup(word).find_all('div', _class)[0].contents)

    def __parse_eng_part(self, info):
        """使用正则表达式解析嵌套html"""
        regex = re.compile(r'(?<=>).*?(?=<)')
        return ''.join(regex.findall(info))

    def parse_title_info(self, word):
        """解析单词名与单词星级"""
        _ = self.__generate_soup(word).find_all('font')
        name, star = self.__normalize_title_info(_)
        star_num = self.__star_parse_dict[star]

        return (name, star, star_num)

    def parse_en_tip(self, word):
        """解析单词总释义"""
        if len(self.__generate_soup(word).find_all(
                'div', 'en_tip')) != 0:
            _ = self.__generate_word_detail(
                word, _class='collins_content')[0]
            eng = self.__normalize_main_en_info(_.find_all('p')[0].contents)
            cn = _.find_all('p')[1].string
            return (eng, cn)
        else:
            return ('', '')

    def parse_collins_en_cn(self, soup):
        """解析单词用法"""
        info = self.__generate_soup(word).find_all('div', 'collins_en_cn')

        if info[0].find('div', 'en_tip'):
            # 测试单一
            captions = list(map(self.__normalize_caption, info[1:]))
            examples = list(map(self.__normalize_example, info[1:]))
        else:
            captions = list(map(self.__normalize_caption, info[0:]))
            examples = list(map(self.__normalize_example, info[0:]))

        return [(caption, example) for caption, example in zip(captions, examples)]

    def parse_vExplain_r(self, word):
        """解析单词变体"""

        _ = self.__generate_word_detail(
            word, _class='vExplain_r', multi=True)
        _ = self.__normalize_multi_word_type(_)
        return _

    def parse_vEn_tip(self, word):
        """解析用法提示"""
        info = self.__generate_soup(word).find('div', 'vEn_tip').find_all('p')

        _ = []
        for i in info:
            for k in i.descendants:
                if type(k) is bs4.element.NavigableString:
                    _.append(k)

        return [''.join(_[:-1]), _[-1]]

    def __repr__(self):
        pass


m = Mdx_to_mongodb()
word = 'beautiful'
# print('title-info: ', m.parse_title_info(word), '\n')
# print('en-tip: ', m.parse_en_tip(word), '\n')
# print('vExplain_r: ', m.parse_vExplain_r(word), '\n')
# print('collins_en_cn: ', m.parse_collins_en_cn(word), '\n')
print('parse_vEn_tip', m.parse_vEn_tip(word), '\n')
