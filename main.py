import re
from collections import namedtuple

import bs4
from bs4 import BeautifulSoup

from mdict_query import IndexBuilder

# 测试
builder = IndexBuilder('柯林斯高阶双解.mdx')
with open('./dicta.html', 'w+') as wp:
    wp.write(builder.mdx_lookup('beautiful')[0])

#soup = BeautifulSoup(builder.mdx_lookup('fuck')[0], features="lxml")

Word_Title = namedtuple('Word_Title', 'name star level')
Word_Interpretation = namedtuple('Word_Interpretation', 'en cn')
Word_Format = namedtuple('Word_Format', 'format examples')
Word_Usage = namedtuple('Word_Usage', 'description examples')
Word_Usage_Note = namedtuple('Word_Usage_Note', 'en cm')


def generate_soup(word):
    """产出所查询单词对应的 BeautifulSoup 实例"""

    builder = IndexBuilder('柯林斯高阶双解.mdx')
    the_word = builder.mdx_lookup(str(word))[0]

    return BeautifulSoup(the_word, features='lxml')


class Mdx_to_mongodb():
    def __init__(self):
        self.__builder = IndexBuilder('柯林斯高阶双解.mdx')

    def __star_to_level(self, star):
        """将星级转化为数字"""
        star_list = [('★' * (i + 1) + '☆' * (4 - i)) for i in range(5)]
        star_to_num_dict = {
            star: level + 1
            for star, level in zip(star_list, range(5))
        }

        return star_to_num_dict[star]

    def __normalize_title_info(self, info):
        """以元组形式输出规范化后的单词头信息"""
        return tuple(map(lambda n: n.string.strip(), info))

    def __normalize_tip_en(self, html):
        """以字符串形式输出规范化后的单词英文总释义"""

        str = ''
        for _ in html.descendants:
            if type(_) is bs4.element.NavigableString:
                str += _

        return str

    def __normalize_tip_cn(self, html):
        """以字符串形式输出规范化后的单词中文总释义"""

        return html.string

    def __normalize_multi_word_type(self, info):
        """以元组形式重整不同的单词变化"""
        _ = []

        for i in info:
            title = i.find_all('b', 'text_blue')[0].contents[0]

            ins = i.find_all('p')
            example = list(map(lambda n: self.__parse_eng_part(str(n)), ins))
            example = [example[i:i + 2] for i in range(0, len(example), 2)]
            _.append((title, example))

        return _

    def __normalize_caption(self, html):
        """规范化用法"""
        gram = ''
        en_caption = ''
        result = []
        spans = html.find_all('span')

        if len(spans) == 4:
            result = list(map(lambda n: n.string, spans[:-1]))

            # 处理用法中文提示
            try:
                spans[-1]
            except IndexError:
                # TODO：可能是词组，暂不处理
                pass
            else:
                for i in spans[-1].find('div').descendants:
                    if type(i) is bs4.element.NavigableString:
                        gram += i
                result.append(gram)
            # 处理用法英文提示
            for i in html.children:
                if i.name != 'span' and type(i) is bs4.element.NavigableString:
                    en_caption += i.strip()

            result.append(en_caption)

        elif len(spans) == 3:
            result = list(map(lambda n: n.string, spans[:]))

            for i in html.children:
                if i.name != 'span' and type(i) is bs4.element.NavigableString:
                    en_caption += i.strip()
            result.append(en_caption)

        return result

    def __parse_example_html(self, html):
        _ = []
        for i in html.descendants:
            if type(i) is bs4.element.NavigableString:
                _.append(i)

        return [''.join(_[:-1]), _[-1]]

    def __normalize_example(self, html):

        example = []

        for _ in html:
            # TODO: 将中英文分开
            example.append(self.__normalize_tip_en(_))

        return example

    def __parse_eng_part(self, info):
        """使用正则表达式解析嵌套html"""
        regex = re.compile(r'(?<=>).*?(?=<)')
        return ''.join(regex.findall(info))

    def parse_title_info(self, word, soup):
        """解析单词名与单词星级"""

        name, star = self.__normalize_title_info(soup.find_all('font'))
        star_num = self.__star_to_level(star)

        return (name, star, star_num)

    def parse_collins_content(self, word, soup):
        """分发 collins content 的内容解析"""
        soup = soup.find('div', 'collins_content')
        interpretation = []
        usage = []
        usage_note = ()
        word_format = []

        for _ in soup.children:
            # 字典 html 中，对总释义的标注分为两种情况
            if _.find('div', 'en_tip'):
                interpretation = self.parse_en_tip(_)
            elif _['class'][0] == 'vExplain_s':
                interpretation = self.parse_vExplain_s(_)
            # TODO: usage fuck 中会出现空串，是由于相关词组导致的，需要清洗
            elif _.find('div', 'caption'):
                usage.append(self.parse_collins_en_cn(_))
            elif _['class'][0] == 'vEn_tip':
                usage_note = self.parse_vEn_tip(_)
            elif _['class'][0] == 'vExplain_r':
                word_format = self.parse_vExplain_r(_)

        usage = tuple(usage)

        return (interpretation, usage, usage_note)

    def parse_en_tip(self, soup):
        """解析单词总释义"""

        items = soup('p')

        en = self.__normalize_tip_en(items[0])
        cn = self.__normalize_tip_cn(items[1])

        return (en, cn)

    def parse_collins_en_cn(self, soup):
        """解析单词用法"""

        captions = soup.find('div', 'caption')
        examples = soup.find_all('li')

        caption = self.__normalize_caption(captions)
        example = self.__normalize_example(examples)

        return (caption, example)

    def parse_vExplain_s(self, soup):
        """解析单词总释义"""

        return tuple(map(lambda n: n.strip(), soup.string.split('.')))

    def parse_vExplain_r(self, soup):
        """解析单词变体"""
        title = soup.find('b', 'text_blue').string
        example = []

        _ = soup.find_all('li')

        for ex in _:
            en = self.__normalize_tip_en(ex.find_all('p')[0])
            cn = ex.find_all('p')[1].string.strip()
            example.append((en, cn))

        return (title, example)

    def parse_vEn_tip(self, soup):
        """解析用法提示"""
        try:
            info = soup.find_all('p')

            _ = []
            for i in info:
                for k in i.descendants:
                    if type(k) is bs4.element.NavigableString:
                        _.append(k)

            return tuple([''.join(_[:-1]), _[-1]])

        except AttributeError:
            return ()

    def __repr__(self):
        pass


m = Mdx_to_mongodb()
word = 'nice'

m.parse_collins_content(word, generate_soup(word))
