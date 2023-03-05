"""
录入成绩的模块
1、读取文件
2、解析数据
3、写入数据库
"""
import os
import re
from abc import ABCMeta, abstractmethod
from db_manager.manager import ZiCiRecordManager, WordRecordManager
from base_utils.base_funcs import get_folder_path
from account.user import User
import logging

# 设置日志的配置
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler()]
)


# -----------------------------------------------解析数据-----------------------------------------------
class DataParser(metaclass=ABCMeta):
    """
    把username与题号列表转为username与索引bool值列表
    """

    def __init__(self, file_data, opr_time, proxy_user):
        self.proxy_user = proxy_user
        self.opr_time = opr_time
        self.file_data = file_data  # 从文件读取的数据
        self.next = None

    @abstractmethod
    def get_record_module(self):  # 获取测试记录模块，返回管理类名，如ZiCiRecordManager
        pass

    def parse(self):
        result_dict = {}  # {name:[bool元素]}
        for username, item_order in self.file_data.items():
            # 查询username在opr_time测试记录，返回df格式
            item_record = self.get_record_module()().get_record_by_username_opr_time(username, self.opr_time)
            if item_record is None:
                logging.error('username为%s的用户在%s时间没有测试记录' % (username, self.opr_time))
                continue
            else:
                # 获取题目数量
                item_num = len(item_record)
                # 生成索引bool值列表
                if item_order[0] == 'absent':
                    result = [2] * item_num
                elif item_order[0] == '+':
                    result = [1 if i in item_order[1:] else 0 for i in range(1, item_num + 1)]
                elif item_order[0] == '-':
                    result = [0 if i in item_order[1:] else 1 for i in range(1, item_num + 1)]
                else:
                    logging.error('symbol必须是+、-或absent')
                    break
                result_dict[username] = result
        self.next(result_dict, self.opr_time, self.proxy_user).save()


class ZiCiParser(DataParser):
    """
    解析从文件中读取的数据
    """

    def __init__(self, file_data, opr_time, proxy_user):
        super().__init__(file_data, opr_time, proxy_user)
        self.next = ZiCiStorage

    def get_record_module(self):
        return ZiCiRecordManager


class WordParser(DataParser):
    """
    解析从文件中读取的数据
    """

    def __init__(self, file_data, opr_time, proxy_user):
        super().__init__(file_data, opr_time, proxy_user)
        self.next = WordStorage

    def get_record_module(self):
        return WordRecordManager


# -----------------------------------------------读取文件-----------------------------------------------
class ReadFile(metaclass=ABCMeta):
    @abstractmethod
    def read(self):
        pass


class ReadTextFile(ReadFile):
    """
    读取txt文档，返回原始数据，形如：username,cn_name与题号列表
    {username:[symbol,1,2,3,……],username:[symbol,1,2,3,……],……}
    """

    def __init__(self, proxy_user, file_path=None):
        """
        :param proxy_user:
        :param data_parser_class: 数据解析器类,如ZiCiDataParser
        """
        super().__init__()
        self.proxy_user = proxy_user
        self.score_file = file_path
        self.opr_time_str = None  # 应该在read()之后调用
        self.str2parser = {'en_word': WordParser, 'ch_zici': ZiCiParser}

    @staticmethod
    def split_string(s):  # 分割题号字符串，s仅含题号，不含symbol
        # 匹配不定量的空格和逗号
        pattern = r'[,，;\s]+'
        # 使用正则表达式分割字符串
        result = re.split(pattern, s)
        return result

    # 为从文件中读取的数据分类，因为一张paper中可能有多个题型，需要多个数据解析器
    def classify_data(self, result):
        classification_result = {}
        for _username, symbol_score_list in result.items():
            print(_username, symbol_score_list)
            u = User(_username)
            paper_composition = u.current_info[self.opr_time_str]
            _symbol = symbol_score_list[0]
            _sore_list = symbol_score_list[1:]
            q_num_before = 0
            for q_type in paper_composition:
                q = q_type[0]  # 如，ch_zici
                q_num = q_type[1] + q_num_before  # 如，16
                # 如果q_type在classification_result的key中，说明已经有该题型的数据了
                print(55555555555,q_type, list(classification_result.keys()))
                if q in list(classification_result.keys()):
                    print(1111111111111)
                    # _score_list中大于q_num_before，小于等于q_num的元素，都是该题型的
                    classification_result[q][_username] = [_symbol] + [i for i in _sore_list if
                                                                       q_num_before < i <= q_num]
                else:
                    classification_result[q] = {_username: [_symbol] + [i for i in _sore_list if
                                                                        q_num_before < i <= q_num]}
                q_num_before = q_num
        return classification_result

    def read(self):
        result = {}
        score_file, opr_time = self.__search_file()  # 此时，opr_time已经被赋值
        with open(score_file, 'r', encoding='utf-8') as f:
            data = f.readlines()
        for row_data in data:
            symbol = None
            symbol_list = ['+', '-', '＋', '－']
            username = row_data.split('$')[0].strip()  # username
            name_score_data = row_data.split('$')[1].strip()  # 蔡景辰 - 1 25

            # 确定符号
            for ch in symbol_list:
                if ch in row_data.split('$')[1]:
                    symbol = ch
                    break

            # 生成结果
            if symbol is None:  # 无符号
                result[username] = ['absent']
            else:  # 有符号
                score_data_list = name_score_data.split(symbol)  # ['蔡景辰','1 12']
                # 转换为标准符号
                if symbol == '＋':
                    symbol = '+'
                elif symbol == '－':
                    symbol = '-'

                # 处理题号和username
                item_order = self.split_string(score_data_list[1].strip())  # 将题号字符串并转为列表
                item_order = [int(i.strip()) for i in item_order if i.isdigit()]  # 将题号转为int类型,[1, 25]

                result[username] = [symbol] + item_order  # 一个元素：'169bbcb5-3e6b-44df-953e-9c9a9068033f': ['-', 16]
        print(1, result)
        # 根据出题记录，自动适配数据解析器
        for q_type, data in self.classify_data(result).items():
            _parser = self.str2parser[q_type]
            print('使用数据解析器：', _parser)
            _parser(data, self.opr_time_str, self.proxy_user).parse()

    # 搜索score文件
    def __search_file(self):
        """
        从score文件夹中搜索文件，文件名分为三部分，用下划线分隔，从前到后依次为：字符串“score_txt”、字符串教师username、字符串操作时间
        :return: 文件地址
        """
        if self.score_file is None:
            result = []
            for root, dirs, files in os.walk(os.path.join(get_folder_path(), 'file', 'received', 'score_txt')):
                for file in files:
                    if file.startswith('score_'):
                        # 判断文件名教师username是否与代理用户username相同
                        if file.split('_')[1] == self.proxy_user.username:
                            result.append(file)  # 存储文件名
            # 取出最新的文件
            result.sort(reverse=True)
            latest_txt = result[0]
        else:
            latest_txt = self.score_file
        # 将最新文件的操作时间转为2023-01-01 00:00:00格式
        latest_txt = os.path.split(latest_txt)[1]
        latest_txt_time_str = latest_txt.split('_')[2].split('.')[0]
        latest_txt_time = latest_txt_time_str[:4] + '-' + latest_txt_time_str[4:6] + '-' + latest_txt_time_str[
                                                                                           6:8] + ' ' + latest_txt_time_str[
                                                                                                        8:10] + ':' + latest_txt_time_str[
                                                                                                                      10:12] + ':' + latest_txt_time_str[
                                                                                                                                     12:14]
        self.opr_time_str = latest_txt_time_str
        return os.path.join(
            os.path.join(get_folder_path(), 'file', 'received', 'score_txt', latest_txt)), latest_txt_time


# -----------------------------------------------更新成绩-----------------------------------------------
class Storage(metaclass=ABCMeta):
    def __init__(self, result, opr_time, proxy_user):
        self.proxy_user = proxy_user
        self.opr_time = opr_time
        self.result = result
        self.next = None

    @abstractmethod
    def get_record_module(self):  # 获取测试记录模块，返回管理类名，如ZiCiRecordManager
        pass

    def save(self):
        for username, correct_list in self.result.items():
            recorder = self.get_record_module()
            print('使用测试记录模块：', recorder)
            recorder().update_score(username, self.opr_time, correct_list)
        # 删除score文件
        # 删除操作时间self.opr_time里的空格、-、:
        new_opr_time = self.opr_time.replace(' ', '').replace('-', '').replace(':', '')
        file_path = os.path.join(get_folder_path(), 'file', 'received', 'score_txt', 'score_%s_%s.txt' % (
            self.proxy_user.username, new_opr_time))
        os.remove(file_path)


class ZiCiStorage(Storage):
    """
    存储数据
    """

    def get_record_module(self):
        return ZiCiRecordManager

    def __init__(self, result, opr_time, proxy_user):
        super().__init__(result, opr_time, proxy_user)


class WordStorage(Storage):
    """
    存储数据
    """

    def get_record_module(self):
        return WordRecordManager

    def __init__(self, result, opr_time, proxy_user):
        super().__init__(result, opr_time, proxy_user)


# -----------------------------------------------测试-----------------------------------------------
if __name__ == '__main__':
    user = User('tangtang')
    ReadTextFile(user, ZiCiParser).read()
