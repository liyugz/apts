"""
激励信息模块

设计模式：模板模式
"""
import math
from abc import ABCMeta, abstractmethod
import random
from renderer.str_render import DoubleSuccessPhraseRender
from renderer.accomplishment_render import AccomplishmentRender
from db_manager.manager import ZiCiRecordManager, ZiCiManager, WordManager, WordRecordManager, KlassManager


# ---------------------------底层抽象---------------------------
# 激励信息接口
class ActivatorBase(metaclass=ABCMeta):
    def __init__(self):
        self.p_name = None

    @abstractmethod
    def set_priority(self, priority):
        """
        设置优先级
        :return:
        """
        pass

    # 获取参考paragraph对象
    def bind_p_name(self, p_name):
        self.p_name = p_name

    @abstractmethod
    def run(self):
        """
        :return:
            有结果：{
                    'render':render_class, 渲染器
                    'kw':{}, 传入渲染器的参数
                    }
            无结果：False
        """
        pass


# 激励信息工具类
class ActivatorUtils:
    # 计算是否获胜，返回值为True或False
    @staticmethod
    def is_win_by_max_error(pre_pass_ratio, question_num, error_num):
        """
        :param pre_pass_ratio: 预设通过率
        :param question_num: 此次测试的题目数量
        :param error_num: 此次测试的错误数量
        :return: True or False
        """
        # 计算最大容错数量，如果有小数，则向上取整
        max_error_num = math.ceil(question_num * (1 - pre_pass_ratio))
        if error_num <= max_error_num:
            return True
        else:
            return False

    @staticmethod
    def is_win_by_min_right(pre_pass_ratio, question_num, right_num):
        """
        :param pre_pass_ratio: 预设通过率
        :param question_num: 此次测试的题目数量
        :param right_num: 此次测试的正确数量
        :return: True or False
        """
        # 计算最小正确数量，如果有小数，则向下取整
        min_right_num = math.floor(question_num * pre_pass_ratio)
        if right_num >= min_right_num:
            return True
        else:
            return False


# ---------------------------抽象功能---------------------------
# 胜利次数：计算总量，不计算连续
class TotalWin(ActivatorUtils, ActivatorBase, metaclass=ABCMeta):
    """
    算法：
        把旧数据数据按照opr_time分组
        每组数据中correct为1的数据所占比例大于等于pre_pass_ratio，则胜利
        逆序遍历分组数据，如果有一组不满足，则失败，返回成功的组数
    """

    def __init__(self):
        super().__init__()

    # 获取题型标志符
    @abstractmethod
    def get_info(self):
        """
        :return: {'item_type': item_type}
        """
        pass

    # 获取former_data
    @abstractmethod
    def get_former_data(self):
        pass

    # 某次测试的预设通过率
    @abstractmethod
    def get_pre_pass_ratio(self):
        pass

    def run(self):  # 不向数据库请求数据
        former_data = self.get_former_data()  # 获取已测试的数据
        if former_data is None:
            return False
        pre_pass_ratio = self.get_pre_pass_ratio()  # 预设通过率
        # 按照opr_time分组
        grouped = former_data.groupby('opr_time', sort=False)
        # 遍历分组数据
        consecutive_wins = 0
        for name, group in grouped:
            # 获取错题数量
            error_num = group[group['correct'] == 0].shape[0]
            # 获取此次测试题目总数
            question_num = group.shape[0]
            # 获胜
            if self.is_win_by_max_error(pre_pass_ratio, question_num, error_num):
                consecutive_wins += 1
        if consecutive_wins == 0:
            return False
        return {
            'render': DoubleSuccessPhraseRender,
            'kw': {'p': self.p_name, 'success_num': consecutive_wins}
        }


# 成就矩阵
class AchievementsMatrix(ActivatorUtils, ActivatorBase, metaclass=ABCMeta):
    """
    算法：1、获取user旧数据，计算lesson通过率；2、获取lesson总数
    :return {lesson序号：通过率}
    """

    @abstractmethod
    def get_grade(self):
        pass

    @abstractmethod
    def get_volume(self):
        pass

    @abstractmethod
    def get_text(self):
        pass

    @abstractmethod
    def get_lesson_field_name(self):
        """
        :return: 数据表中对应题型的用于界定最小学习单位的名称，字符串格式，例如'lesson'
        """
        pass

    @abstractmethod
    def get_record_manager(self):
        """
        :return: 返回RecordManager对象实例
        """
        pass

    @abstractmethod
    def get_resource_manager(self):
        """
        :return: 返回资源管理器,例如ZiCiManager
        """
        pass

    @abstractmethod
    def get_user(self):
        """
        :return: 返回user对象
        """
        pass

    @abstractmethod
    def get_register_name(self):
        pass

    def get_former_data(self):
        return self.get_record_manager().get_record_by_username(self.get_user().username, grade=self.get_grade(),
                                                                volume=self.get_volume())

    # 获取lesson总数
    def get_lesson_num(self, grade, volume, lesson_num=None):
        if self.get_register_name() == 'en_word':  # 考虑到英语单词没有录入全部学习资源，所以直接返回12
            return 12
        else:
            if lesson_num is None:
                return self.get_resource_manager().get_lesson_count(grade=grade, volume=volume)
            else:
                return lesson_num

    # 获取已掌握的lesson数量
    def get_mastered_words_counts(self):
        data = self.get_record_manager().get_record_by_username(self.get_user().username, grade=self.get_grade(),
                                                                volume=self.get_volume())
        if data is None:
            return False
        # data中如果多条数据的zici_id相同，只取opr_time最大的那条，所以要先排序
        data = data.sort_values(by='opr_time', ascending=False)
        # 去重，保留最新的一条
        data = data.drop_duplicates(subset='%s_id' % self.get_register_name().split('_')[1], keep='first')
        # 计算correct为1的数据总量
        right_num = data[data['correct'] == 1].shape[0]
        return right_num

    def run(self):
        # 获取user旧数据
        former_data = self.get_former_data()  # 返回dataframe
        # 获取lesson总数
        lesson_num = self.get_lesson_num(self.get_grade(), self.get_volume())
        result = {}
        for i in range(1, lesson_num + 1):
            result[i] = 0
        if former_data is None:
            return {
                'render': AccomplishmentRender,
                'kw': {'p_name': self.p_name, 'lesson_num': lesson_num, 'pass_ratio': result, 'text': self.get_text()}
            }
        # 计算lesson通过率
        # 处理数据：如果former_data中，多条数据zici_id字段的值相同，则只保留opr_time最大的那个
        former_data = former_data.sort_values(by='opr_time', ascending=False)
        former_data = former_data.drop_duplicates(subset='%s_id' % self.get_register_name().split('_')[1], keep='first')

        # 按照lesson分组，计算correct为1的数据所占比例-------------------
        # 获取former_data中的item_id字段的值，不重复，存入列表
        item_id_list = former_data['%s_id' % self.get_register_name().split('_')[1]].unique().tolist()
        # 获取item_id_list中的所有数据
        item_df = self.get_resource_manager().get_item_by_id(item_id_list)
        # 通过item_id，获取item的lesson字段的值，构成字典
        item_lesson_dict = {}
        for item_id in item_id_list:
            item_info = item_df[item_df['%s_id' % self.get_register_name().split('_')[1]] == item_id]
            item_lesson_dict[item_id] = item_info['lesson'].values[0]
        # 将item_lesson_dict中的lesson值，添加到former_data中
        former_data['lesson'] = former_data['%s_id' % self.get_register_name().split('_')[1]].map(item_lesson_dict)
        grouped = former_data.groupby(self.get_lesson_field_name(), sort=False)
        # 计算每个lesson的总词数
        lesson_list = former_data['lesson'].unique().tolist()
        lesson_df = self.get_resource_manager().get_item_by_lesson(grade=self.get_grade(), volume=self.get_volume(),
                                                                   lesson=lesson_list)
        for lesson, group in grouped:
            # 计算correct为1的数据所占比例
            pass_ratio = group[group['correct'] == 1].shape[0] / lesson_df[lesson_df['lesson'] == lesson].shape[0]
            result[lesson] = pass_ratio
        return {
            'render': AccomplishmentRender,
            'kw': {'p_name': self.p_name, 'lesson_num': lesson_num, 'pass_ratio': result, 'text': self.get_text()}
        }


# ---------------------------具体功能---------------------------
# 胜利次数
class ZiCiTotalWin(TotalWin):
    def __init__(self, user, grade, volume):
        super().__init__()
        self.user = user
        self.former_data = None
        self.priority = None
        self.grade = grade
        self.volume = volume

    def set_priority(self, priority):
        self.priority = priority

    def get_info(self):
        return {'item_type': 'zici'}

    def get_former_data(self):
        self.former_data = ZiCiRecordManager().get_record_by_username(self.user.username, grade=self.grade,
                                                                      volume=self.volume)
        return self.former_data

    def get_pre_pass_ratio(self):
        return self.user.current_info['ch_zici_pass_ratio']


class WordTotalWin(TotalWin):
    def __init__(self, user, grade, volume):
        super().__init__()
        self.user = user
        self.former_data = None
        self.priority = None
        self.grade = grade
        self.volume = volume

    def set_priority(self, priority):
        self.priority = priority

    def get_info(self):
        return {'item_type': 'word'}

    def get_former_data(self):
        self.former_data = WordRecordManager().get_record_by_username(self.user.username, grade=self.grade,
                                                                      volume=self.volume)
        return self.former_data

    def get_pre_pass_ratio(self):
        return self.user.current_info['en_word_pass_ratio']


# ZiCiAchievementsMatrix
class ZiCiAchievementsMatrix(AchievementsMatrix):
    def __init__(self, user, grade, volume):
        super().__init__()
        self.user = user
        self.priority = None
        self.grade = grade
        self.volume = volume

    def get_grade(self):
        return self.grade

    def get_volume(self):
        return self.volume

    def get_text(self):
        return '已掌握的字词量：%d' % self.get_mastered_words_counts()

    def get_lesson_field_name(self):
        return 'lesson'

    def get_record_manager(self):
        return ZiCiRecordManager()

    def get_resource_manager(self):
        return ZiCiManager()

    def get_user(self):
        return self.user

    def get_register_name(self):
        return 'ch_zici'

    def set_priority(self, priority):
        self.priority = priority


# WordAchievementsMatrix
class WordAchievementsMatrix(AchievementsMatrix):
    def __init__(self, user, grade, volume):
        super().__init__()
        self.user = user
        self.priority = None
        self.grade = grade
        self.volume = volume

    def get_grade(self):
        return self.grade

    def get_volume(self):
        return self.volume

    def get_text(self):
        return '已掌握的单词总量：%d' % self.get_mastered_words_counts()

    def get_lesson_field_name(self):
        return 'lesson'

    def get_record_manager(self):
        return WordRecordManager()

    def get_resource_manager(self):
        return WordManager()

    def get_user(self):
        return self.user

    def get_register_name(self):
        return 'en_word'

    def set_priority(self, priority):
        self.priority = priority


# ---------------------------各类型题的调用界面---------------------------
# 抽象类
class Interface(metaclass=ABCMeta):
    def __init__(self, user):
        self.user = user

    @abstractmethod
    def bind_params(self, grade, volume):
        pass

    def bind_p_name(self, p_name):
        for attr in dir(self):
            # 如果attr是ActivatorWin的实例
            if isinstance(getattr(self, attr), ActivatorBase):
                # 绑定p_name
                getattr(self, attr).bind_p_name(p_name)

    def execute(self):  # 返回用于render的数据
        mid_result = {'required': []}
        # 获取所有属性
        for attr in dir(self):
            # 如果attr是ActivatorWin的实例
            if isinstance(getattr(self, attr), ActivatorBase):
                # 获取该实例的优先级
                priority = getattr(self, attr).priority
                # 如果优先级等于0，且运行结果不为False，则加入key为required的result中列表中
                if priority == 0:
                    run_result = getattr(self, attr).run()
                    if run_result is not False:
                        mid_result['required'].append(run_result)
                if priority > 0:
                    # 则将运行结果加入key为priority的result中列表中
                    run_result = getattr(self, attr).run()
                    if run_result is not False:
                        if priority not in mid_result:
                            mid_result[priority] = []
                        mid_result[priority].append(run_result)
        result = []  # 返回结果为字典列表，字典中的render为渲染器
        # 将mid_result中key为required的列表中的元素加入result中
        result.extend(mid_result['required'])
        # 将mid_result中key为priority的列表中的元素加入result中，每个列表中的元素随机选一个
        for priority in mid_result.keys():
            if priority != 'required':
                result.append(random.choice(mid_result[priority]))
        return result


# 具体类
class ZiCiActivator(Interface):
    def __init__(self, user):
        super().__init__(user)
        self.grade = None
        self.volume = None
        self.total_win = None
        self.achievements_matrix = None

    def bind_params(self, grade, volume):
        self.grade = grade
        self.volume = volume
        self.total_win = ZiCiTotalWin(self.user, self.grade, self.volume)
        self.achievements_matrix = ZiCiAchievementsMatrix(self.user, self.grade, self.volume)
        self.set_priority()

    # 为各激励类型设定优先级
    def set_priority(self):
        """
        数字大于0，数字相同，则优先级相同，同一优先级的激励随机展示一个
        数字等于0，必选
        :return:
        """
        # 默认优先级
        self.total_win.set_priority(0)
        self.achievements_matrix.set_priority(0)

        # 激励模块列表
        activate_name_dic = {'ch_zici_total_wins': self.total_win,
                             'ch_zici_achievements_matrix': self.achievements_matrix}

        # 学生定制：True展示，False不展示
        for activate_name, activate in activate_name_dic.items():
            # 如果存在
            if activate_name in self.user.current_info:
                if self.user.current_info[activate_name] is True:
                    activate.set_priority(0)
                elif self.user.current_info[activate_name] is False:
                    activate.set_priority(-1)


class WordActivator(Interface):
    def __init__(self, user):
        super().__init__(user)
        self.grade = None
        self.volume = None
        self.total_win = None
        self.achievements_matrix = None

    def bind_params(self, grade, volume):
        self.grade = grade
        self.volume = volume
        self.total_win = WordTotalWin(self.user, self.grade, self.volume)
        self.achievements_matrix = WordAchievementsMatrix(self.user, self.grade, self.volume)
        self.set_priority()

    # 为各激励类型设定优先级
    def set_priority(self):
        """
        数字大于0，数字相同，则优先级相同，同一优先级的激励随机展示一个
        数字等于0，必选
        :return:
        """
        # 默认优先级
        self.total_win.set_priority(0)
        self.achievements_matrix.set_priority(0)

        # 激励模块列表
        activate_name_dic = {'en_word_total_wins': self.total_win,
                             'en_word_achievements_matrix': self.achievements_matrix}

        # 学生定制：True展示，False不展示
        for activate_name, activate in activate_name_dic.items():
            # 如果存在
            if activate_name in self.user.current_info:
                if self.user.current_info[activate_name] is True:
                    activate.set_priority(0)
                elif self.user.current_info[activate_name] is False:
                    activate.set_priority(-1)
