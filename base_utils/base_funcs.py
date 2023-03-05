"""
一些通用的函数
"""

import os
import pypinyin
from cnradical import Radical, RunOption
import hashlib
import json


# 根据文件夹名，从当前文件路径中获取文件夹路径，当文件夹名为 APTS 时，返回的是该项目的根目录，默认值为 APTS
def get_folder_path(folder_name='APTS'):
    # 获取当前文件的路径
    current_file_path = os.path.abspath(__file__)
    # 从文件路径中查找文件夹名的位置
    folder_name_index = current_file_path.find(folder_name)
    if not folder_name_index == -1:  # 说明找到了文件夹名
        # 从文件路径中获取文件夹路径
        folder_path = current_file_path[:folder_name_index + len(folder_name)]
        return folder_path
    else:
        raise Exception('未找到指定文件 %s 的路径' % folder_name)


# 传入字符串，返回拼音
def get_pinyin(text):
    # 如果传入的不是字符串，则不做处理
    if isinstance(text, str):
        result = pypinyin.pinyin(text)

        # 拼音列表各元素之间用空格隔开
        result = ' '.join([''.join(item) for item in result])
        return result


# 传入汉字，返回汉字的部首
def get_radical(text):
    if not isinstance(text, str):
        raise Exception('传入的参数不是字符串')
    elif len(text) != 1:
        raise Exception('传入的字符串长度不为1')
    else:
        radical = Radical(RunOption.Radical)  # 获取偏旁
        radical_out = radical.trans_ch(text)
        return radical_out


# 传入汉字，返回笔画数
def get_strokes(text):
    if not isinstance(text, str):
        raise Exception('传入的参数不是字符串')
    elif len(text) != 1:
        raise Exception('传入的字符串长度不为1')
    else:
        # 如果返回 0, 则也是在unicode中不存在kTotalStrokes字段
        strokes = []
        strokes_path = os.path.join(os.path.join(get_folder_path(), 'base_utils'), r'strokes.txt')
        with open(strokes_path, 'r') as fr:
            for line in fr:
                strokes.append(int(line.strip()))

        unicode_ = ord(text)

        if 13312 <= unicode_ <= 64045:
            return strokes[unicode_ - 13312]
        elif 131072 <= unicode_ <= 194998:
            return strokes[unicode_ - 80338]
        else:
            return 0


# 传入password，使用sha256返回加密后的密码
def encrypt(password):
    encrypted_string = hashlib.sha256(password.encode()).hexdigest()
    return encrypted_string  # 输出加密后的字符串


# 用于解析 json 字符串：传入 json 字符串，返回解析后的数据
def parse_json(json_str):
    # 使用 json.loads() 函数解析 json 字符串
    data = json.loads(json_str)
    # 返回解析后的数据
    return data


# 输入：类名，返回：该类的所有子类名称及类构成的字典
def get_subclasses(cls):
    subclasses = {}
    for subclass in cls.__subclasses__():
        subclasses[subclass.__name__] = subclass
    return subclasses


# 测试
if __name__ == '__main__':
    print(get_strokes('好'))
