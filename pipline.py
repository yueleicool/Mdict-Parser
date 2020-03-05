import datetime

from pymongo import MongoClient

from main import *

client = MongoClient('mongodb://49.232.5.176:34541/')
db = client['word']

collection = db['word']

word = 'test'
mdx_parser = Mdx_to_mongodb()
title = m.fetch_title_info(word, generate_soup(word))
contents = m.fetch_collins_content(word, generate_soup(word))

interpretation = contents.interpretation
usage = contents.usage
usage_note = contents.usage_note
word_format = contents.word_format

the_word = {
    'name': title.name,
    'star': title.star,
    'level': title.level,
    'usage': usage,
    'usage_note': usage_note
}

collection.insert(the_word)

# collection.insert(post)

print(title, '\n')
print(contents, '\n')

print('=' * 15, 'Word_Title', '=' * 15)
print('name: ', title.name)
print('star: ', title.star)
print('level: ', title.level)
print('\n')

print('=' * 15, 'Word_Interpretation', '=' * 15)
for _ in interpretation:
    print('en: ', _.en)
    print('cn: ', _.cn)
    print('-' * 15)
print('\n')

print('=' * 15, 'Word_Usage', '=' * 15)
for _ in usage:
    print('description: ', _.description)
    print('examples: ', _.examples)
    print('-' * 15)
print('\n')

print('=' * 15, 'Word_Usage_Note', '=' * 15)
print('en: ', usage_note.en)
print('cn: ', usage_note.cn)
print('-' * 15)
print('\n')
""" print('=' * 15, 'Word_Format', '=' * 15)
for _ in word_format:
    print('en: ', _.format)
    print('cn: ', _.examples)
    print('-' * 15)
print('\n') """