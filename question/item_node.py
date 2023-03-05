"""
设计模式：接口和具体实现
用于保存单个题目信息的数据结构，以下为属性全集，各类题型的属性是属性全集的子集：

    self.item_id = item_id  # 题目id 必选
    self.item_description = None  # 题目描述 必选
    self.quote_text = None  # 引文
    self.num_attempts = None  # 尝试次数
    self.num_success = None  # 正确次数
    self.answer = None  # 答案，即item_description的对应的谜底
    self.latest_is_success = None  # 最近一次是否正确，针对记忆类题目，如听写
    self.latest_success_ratio = None  # 最近一次测试中该题型正确率，对于非记忆类题目，如计算题
"""
from abc import ABCMeta, abstractmethod
import datetime
import random

from db_manager.manager import ZiCiRecordManager, ZiCiManager, WordManager, WordRecordManager


# ---------------------------接口---------------------------
class ItemNode(metaclass=ABCMeta):
    def __init__(self, user, item_id, num_attempts=0, num_success=0, latest_is_success=None, challenge_value=0,
                 memory_value=0, df_data=None, new=False):
        item_info = self.get_resource_class().get_item_by_id(item_id)
        self.user = user
        self.item_id = item_id  # 题目id
        description_field_name = self.get_description_field_name()

        # 如果description_field_name是一个tuple，说明有两类提示词
        if isinstance(description_field_name, tuple):
            # 从item_info中提取sentence字符串
            try:
                pre_description = random.choice(item_info.loc[0, description_field_name[0]])  # 句子
            except IndexError:
                # 列表为空时的异常处理
                pre_description = []
            pre_deputy_description = item_info.loc[0, description_field_name[1]]  # 单词
            print('1\tpre_description\t', pre_description, type(pre_description))
            print('1\tpre_deputy_description\t', type(pre_deputy_description))
            if not pre_description:  # 句子为空，只有单词
                self.item_description = pre_deputy_description
                self.deputy_item_description = None
            else:  # 句子不为空，单词和句子都有
                self.item_description = pre_description
                self.deputy_item_description = pre_deputy_description

            # self.item_description = item_info.loc[0, description_field_name[0]] or item_info.loc[
            #     0, description_field_name[1]]  # 题目描述，即提示词
            # self.deputy_item_description = item_info.loc[0, description_field_name[1]] or item_info.loc[
            #     0, description_field_name[0]]
            print('2\tdescription\t', self.item_description)
            print('2\tdeputy_description\t', self.item_description)
        else:
            self.item_description = item_info.loc[0, description_field_name]  # 题目描述，即提示词
            self.deputy_item_description = None  # 副题目描述，即提示词

        self.answer = item_info.loc[0, self.get_answer_field_name()]
        self.num_attempts = num_attempts  # 尝试次数
        self.num_success = num_success  # 正确次数
        self.latest_is_success = latest_is_success  # 最近一次听写是否正确
        self.lesson = item_info.loc[0, self.get_lesson_field_name()]
        self.df_data = df_data  # 该题目历史数据
        self.new = new  # user没有见过改题目，则new为True，否则为False，默认为False，即，默认user见过该题目

        """
            challenge_value表示挑战价值，该值越大，越值得练习，因为学生掌握越差，衡量方法为挑战因子加和，date_difference为距离今天的天数
            作对，挑战因子为 -1/date_difference
            做错，挑战因子为 1/date_difference
        """
        self.challenge_value = challenge_value
        self.memory_value = memory_value

        # 如果是旧题，则填充参数
        if not self.new:
            self.fill_attributes()

    @abstractmethod
    def get_answer_field_name(self):
        pass

    @abstractmethod
    def get_resource_class(self):
        """
        获取题目资源类，返回类名，如ZiCiManager实例对象
        :return:
        """
        pass

    @abstractmethod
    def get_description_field_name(self):
        """
        获取题目描述字段名，返回字符串，如'pinyin'
        :return:
        """
        pass

    @abstractmethod
    def get_lesson_field_name(self):
        """
        数据表中对应题型的用于界定最小学习单位的名称，字符串格式，例如'lesson'
        :return:
        """
        pass

    @abstractmethod
    def get_record_manager(self):
        """
        :return: 返回RecordManager对象实例
        """
        pass

    def __str__(self):
        return self.item_description

    def __eq__(self, other):
        # account、item_id相同，即为同一题目
        return self.user == other.user and self.item_id == other.item_id

    # 把新出的测试题数据存储到ZiCiRecord，此时correct为2，表示未测试
    def save_to_record(self, opr_time, order):
        # 保存到数据库
        self.get_record_manager().add_new_record(username=self.user.username, item_id=self.item_id, correct=2,
                                                 opr_time=opr_time, order=order)

    # 获取尝试次数
    def __fill_num_attempts(self):
        # 查询self.df_data中有多少数据，然后再赋值给self.num_attempts
        self.num_attempts = len(self.df_data)

    # 获取正确次数
    def __fill_num_success(self):
        # 查询self.df_data中有多少数据，然后再赋值给self.num_attempts
        self.num_success = len(self.df_data[self.df_data['correct'] == 1])

    # 获取最近一次是否正确
    def __fill_latest_is_success(self):
        # 查询self.df_data中按照opr_time降序排列，取第一条数据，然后再赋值给self.latest_is_success
        self.latest_is_success = self.df_data.iloc[0]['correct']

    # 获取挑战价值
    def __fill_challenge_value(self):
        # 计算挑战价值
        """
            challenge_value表示挑战价值，该值越大，越值得练习，因为学生掌握越差，衡量方法为挑战因子加和，date_difference为距离今天的天数
            作对，挑战因子为 -1/date_difference
            做错，挑战因子为 1/date_difference
        :return:
        """
        # 遍历self.df_data
        result = 0
        for index, row in self.df_data.iterrows():
            # 计算两日之差，返回分钟数，按照是12小时的多少倍计算
            date_difference = (datetime.datetime.now() - row['opr_time']).total_seconds() / 3600 / 12
            if row['correct'] == 1:
                # 作对，挑战因子为 -1/date_difference
                result += -1 / date_difference
            else:
                # 做错，挑战因子为 1/date_difference
                result += 1 / date_difference
        self.challenge_value = result

    # 获取记忆价值
    def __fill_memory_value(self):
        """
            memory_value表示记忆价值，该值越大，越值得练习
            计算方法：
                假设最佳记忆天数为[1,2,3,5,7,10,15,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200]
                第一次作对的时间为t0,今天为now,date_difference为now-t0
                如果date_difference为1.3，发现处于1,2之间，且距离1最近，那么记忆价值为0.3，这个值越小，越值得练习，为了方便计算，取其倒数
                如果为0，值设定为inf（即无穷大）
        :return:
        """
        # 遍历self.df_data
        result = 0
        df_data_asc = self.df_data.sort_values(by='opr_time', ascending=True, inplace=False)
        for index, row in df_data_asc.iterrows():
            if row['correct'] == 1:
                date_difference = (datetime.datetime.now() - row['opr_time']).days
                memory_node = [1, 2, 3, 5, 7, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150,
                               160,
                               170, 180, 190, 200]
                # 查找与date_difference最接近的值，并返回差值，存储于result
                min_value = min(memory_node, key=lambda x: abs(x - date_difference))
                result = abs(min_value - date_difference)
                break
        # 为了方便计算，取其倒数
        if result == 0:
            self.memory_value = float('inf')
        else:
            self.memory_value = 1 / result

    def fill_attributes(self):
        """
        填充题目的其他参数
        :return:
        """
        # 检查属性是否有None，有则全部重新填充
        if self.num_attempts is None or self.num_success is None or self.latest_is_success is None or self.challenge_value is None or self.memory_value is None or self.lesson is None:
            if self.df_data is None:
                # 获取历史数据
                self.df_data = self.get_record_manager().get_record_by_item_id(self.user, self.item_id)
            if self.df_data is None:
                # 如果没有历史数据，设置默认值
                self.num_attempts = self.num_attempts
                self.num_success = self.num_success
                self.latest_is_success = self.latest_is_success
                self.challenge_value = self.challenge_value
                self.memory_value = self.memory_value
            else:
                # 按照opr_time降序排列
                self.df_data = self.df_data.sort_values(by='opr_time', ascending=False)
                # 根据历史数据填充属性
                self.__fill_num_attempts()
                self.__fill_num_success()
                self.__fill_latest_is_success()
                self.__fill_challenge_value()
                self.__fill_memory_value()


# ---------------------------实现---------------------------
# ZiCiNode
class ZiCiNode(ItemNode):
    def get_answer_field_name(self):
        return 'chinese'

    def get_description_field_name(self):
        return 'pinyin'

    def get_lesson_field_name(self):
        return 'lesson'

    def get_resource_class(self):
        return ZiCiManager()

    def get_record_manager(self):
        return ZiCiRecordManager()


# WordNode
class WordNode(ItemNode):
    def get_answer_field_name(self):
        return 'english'

    def get_description_field_name(self):
        return 'sentence', 'chinese'

    def get_lesson_field_name(self):
        return 'lesson'

    def get_resource_class(self):
        return WordManager()

    def get_record_manager(self):
        return WordRecordManager()
