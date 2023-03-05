"""
策略模块
包括范围策略和出题策略
设计模式：策略模式混合抽象工厂模式
"""
from abc import ABCMeta, abstractmethod
from random import shuffle
from db_manager.manager import ZiCiRecordManager, ZiCiManager, KlassManager, WordRecordManager, WordManager
from question.utils import TaskAllocator
from question.item_node import ZiCiNode, WordNode
from renderer.table_render import ZiCiParenthesesZiCiDoubleTableRender, ZiCiTianZiCiDoubleTableRender, \
    WordFourLineThreeGridDoubleTableRender
from question.activator import ZiCiActivator, WordActivator


# ----------------------------------------范围策略----------------------------------------
class RangeStrategy(metaclass=ABCMeta):
    def __init__(self, user, grade, volume, manual_range=None):
        self.user = user
        self.manual_range = manual_range
        if grade is None or volume is None:
            self.grade, self.volume = KlassManager().get_grade_and_volume_by_klass_id(
                self.user.class_id)  # 根据当前用户的class_id获取grade和volume
        else:
            self.grade = grade
            self.volume = volume

    @abstractmethod
    def get_resource_manager(self):
        """
        :return: 返回资源管理器,例如ZiCiManager
        """
        pass

    @abstractmethod
    def get_node_class(self):
        """
        :return: 返回对应题型的item_node类，例如ZiCiNode
        """
        pass

    @abstractmethod
    def get_register_name(self):
        """
        :return: 返回出题模块注册名称，字符串格式，例如'ch_zici'
        """
        pass

    @abstractmethod
    def get_record_manager(self):
        """
        :return: 返回RecordManager对象实例
        """
        pass

    @abstractmethod
    def get_lesson_field_name(self):
        """
        :return: 数据表中对应题型的用于界定最小学习单位的名称，字符串格式，例如'lesson'
        """
        pass

    @abstractmethod
    def get_item_description_field_name(self):
        """
        :return: 数据表中item的描述字段，例如'pinyin'，即提示词
        """
        pass

    def get_user(self):
        """
        :return: 返回目标用户User对象
        """
        return self.user

    def get_former_items(self):
        """
        :return: 返回former_items，格式为DataFrame
        """
        return self.get_record_manager().get_record_by_username(self.user.username, self.grade, self.volume)

    def get_item_id_field_name(self):
        """
        :return: 数据表中对应题型的id名称，字符串格式，例如'zici_id'
        """
        return '%s_id' % self.get_register_name().split('_')[1]

    def get_item_by_lesson_constraints(self, lesson_constraints):
        """
        :param lesson_constraints: 根据lesson_constraints获取item对象，返回格式为DataFrame
        :return:
        """
        return self.get_resource_manager().get_item_by_lesson(self.grade, self.volume, lesson_constraints)

    # 获取限定的lesson范围，等同于manual_range
    def get_lesson_constraints(self):
        """
                :return: 列表
                         自动模式：筛出former_data中去重后的lesson，根据learning_path后移两个lesson，并入之前的lesson，返回
        """
        if self.manual_range is None:  # 如果manual_range为空，则未手动设置范围，使用自动模式
            print('自动模式')
            former_items = self.get_former_items()
            lesson_list = []
            if former_items is not None:
                # 获取former_items中lesson字段去重后的列表
                lesson_list = former_items[self.get_lesson_field_name()].drop_duplicates().tolist()
            # 获取user的learning_path
            learning_path = self.user.current_info[self.get_learning_path_field_name()]
            # 从前往后遍历learning_path，找到不存在于lesson_list中的learning_speed个元素，然后停止遍历
            lesson_constraints = lesson_list
            for lesson in learning_path:
                if lesson not in lesson_list:
                    lesson_constraints.append(lesson)
                # learning_speed为n，则表示该生可以向后学习n个lesson的课程，n越大，学习速度越快
                if len(lesson_constraints) == self.user.current_info[self.get_learning_speed_field_name()]:
                    break
            return lesson_constraints
        else:  # 如果manual_range不为空，则手动设置范围，使用手动模式
            return self.manual_range

    # 把df转化为item_node_list
    def get_item_node_list(self, data_to_be_converted, data_for_support):
        """
        :param data_to_be_converted: 待转化数据，格式为DataFrame，均为去重后的数据
        :param data_for_support: 被转化数据所需的原始数据
        :return:
        """
        result = []
        item_id_name = self.get_item_id_field_name()
        if data_for_support is None:
            for index, row in data_to_be_converted.iterrows():
                item_id = row[item_id_name]  # 获取zici_id
                item_node = self.get_node_class()(self.get_user(), item_id, new=True)  # 根据item_id生成一个ItemNode
                result.append(item_node)  # 将item_node存入incorrect_items
        else:
            for index, row in data_to_be_converted.iterrows():
                item_id = row[item_id_name]  # 获取zici_id，
                item_df = data_for_support[
                    data_for_support[item_id_name] == item_id]  # 然后根据zici_id从former_items中提取对应的zici，返回格式为DataFrame
                item_node = self.get_node_class()(self.get_user(), item_id, df_data=item_df)  # 根据item_df生成一个ItemNode
                result.append(item_node)  # 将item_node存入incorrect_items
        return result

    def execute(self):  # 此处需要查询老师设定的学习路径，学习路径存于学生的current_info中
        lesson_constraints = self.get_lesson_constraints()  # lesson约束
        former_items = self.get_former_items()  # 从数据库中查询former_items的数据，返回格式为DataFrame
        item_id_name = self.get_item_id_field_name()  # 获取对应题型的id名称，字符串格式，例如'zici_id'
        items = self.get_item_by_lesson_constraints(lesson_constraints)  # 根据lesson_constraints获取item对象，返回格式为DataFrame

        if former_items is not None:  # 如果former_items不是None，说明用户已经学习过，需要根据范围约束条件进行筛选，将已考察lesson分为三类
            # 从former_items中提取每个item_id的最新一条记录，最新是指opr_time字段离现在最近，返回格式为DataFrame
            former_items_unique = former_items.sort_values(by='opr_time', ascending=False).drop_duplicates(
                subset=item_id_name)

            # 求items与former_items_unique的差集，返回格式为DataFrame
            new_items = items[~items[item_id_name].isin(former_items_unique[item_id_name])]
            # 遍历former_items_one，根据correct字段，将内部元素分别存入former_incorrect_items和former_correct_items，dataframe格式
            former_incorrect_items_unique = former_items_unique[former_items_unique['correct'] == 0]
            former_correct_items_unique = former_items_unique[former_items_unique['correct'] == 1]

            # 生成item_node列表
            incorrect_items = self.get_item_node_list(former_incorrect_items_unique, former_items)
            correct_items = self.get_item_node_list(former_correct_items_unique, former_items)
            new_items = self.get_item_node_list(new_items, None)
        else:
            incorrect_items = []
            correct_items = []
            new_items = self.get_item_node_list(items, None)
        return {'incorrect_items': incorrect_items, 'correct_items': correct_items, 'new_items': new_items}

    def get_learning_path_field_name(self):
        return '%s_learning_path' % self.get_register_name()

    def get_learning_speed_field_name(self):
        return '%s_learning_speed' % self.get_register_name()


class WordRangeStrategy(RangeStrategy):  # 单词范围策略
    def __init__(self, user, grade, volume, manual_range=None):
        super().__init__(user, manual_range=manual_range, grade=grade, volume=volume)

    def get_register_name(self):
        return 'en_word'

    def get_lesson_field_name(self):
        return 'unit'

    def get_item_description_field_name(self):  # 提示词
        return 'chinese'

    def get_record_manager(self):
        return WordRecordManager()

    def get_resource_manager(self):
        return WordManager()

    def get_node_class(self):
        return WordNode


class ZiCiRangeStrategy(RangeStrategy):  # 字词范围策略
    def __init__(self, user, grade, volume, manual_range=None):
        super().__init__(user, manual_range=manual_range, grade=grade, volume=volume)

    def get_register_name(self):
        return 'ch_zici'

    def get_item_description_field_name(self):
        return 'pinyin'

    def get_lesson_field_name(self):
        return 'lesson'

    def get_node_class(self):
        return ZiCiNode

    def get_resource_manager(self):
        return ZiCiManager()

    def get_record_manager(self):
        return ZiCiRecordManager()


# ----------------------------------------出题策略----------------------------------------
class SetStrategy(metaclass=ABCMeta):
    def __init__(self, user):
        self.user = user

    def get_user(self):
        return self.user

    def execute(self, item_data_raw):
        """
        0、item_data_raw为RangeStrategy的结果
        1、对RangeStrategy的结果进行进一步处理，例如，火箭模式下删除'former_correct_items'
        2、对RangeStrategy的结果进行排序，紧迫度、艾宾浩斯、难度等
        3、返回最终的题目列表
        :return: [item_node,……]
        """
        item_data = self.get_item_data(item_data_raw)  # 获得已排序的item_data
        item_max_num = self.get_item_max_num()  # 获得最大题目数
        item_ratio_dict = self.get_ratio()  # 获得出题比例

        result = []
        while item_max_num > 0:
            item_num_dic = TaskAllocator(item_max_num, **item_ratio_dict).allocate()
            for item_type in item_data.keys():
                result.extend(item_data[item_type][:item_num_dic[item_type]])
                item_max_num -= len(item_data[item_type][:item_num_dic[item_type]])
                del item_data[item_type][:item_num_dic[item_type]]
                if len(item_data['incorrect_items']) == 0 and len(item_data['correct_items']) == 0 and len(
                        item_data['new_items']) == 0:
                    item_max_num = 0
        return result

    @abstractmethod
    def get_mode(self):
        """
        :return: 火箭模式、均衡模式
        """
        pass

    def get_item_data(self, item_data_raw):
        """
        :return: 根据模式不同，决定是否删除correct_items

        """
        # 对incorrect_items按照challenge_value 降序排列
        item_data_raw['incorrect_items'].sort(key=lambda x: x.challenge_value, reverse=True)
        # 令new_items列表中的元素乱序
        shuffle(item_data_raw['new_items'])
        # 如果是均衡模式
        if self.get_mode() in ['均衡', '艾宾浩斯', 'Equalization']:
            # 对former_correct_items按照 memory_value 降序排列
            item_data_raw['correct_items'].sort(key=lambda x: x.memory_value, reverse=True)
            return {'incorrect_items': item_data_raw['incorrect_items'],
                    'correct_items': item_data_raw['correct_items'],
                    'new_items': item_data_raw['new_items']}
        elif self.get_mode() in ['火箭', 'rocket']:
            return {'incorrect_items': item_data_raw['incorrect_items'],
                    'correct_items': [],
                    'new_items': item_data_raw['new_items']}
        else:
            raise Exception('错误的出题模式：%s' % self.get_mode())

    def get_item_max_num(self):
        """
        :return: 返回最大题目数
        """
        return self.get_user().current_info['%s_max_num' % self.get_register_name()]

    @abstractmethod
    def get_register_name(self):
        """
        :return:题目模块的注册名，例如：'en_word'
        """
        pass

    def get_ratio(self):
        """
        :return: 返回出题比例，例如：
                 {'incorrect_items': 0.5, 'correct_items': 0.3, 'new_items': 0.2}
        """
        user = self.get_user()
        return {'incorrect_items': user.current_info['%s_incorrect_ratio' % self.get_register_name()],
                'correct_items': user.current_info['%s_correct_ratio' % self.get_register_name()],
                'new_items': user.current_info['%s_new_ratio' % self.get_register_name()]}


class ZiCiSetStrategy(SetStrategy, metaclass=ABCMeta):  # 字词出题策略
    def __init__(self, user, mode='均衡'):
        """
        :param user: 目标用户
        :param mode: 均衡模式、火箭模式
        """
        super().__init__(user)
        self.mode = mode

    def get_register_name(self):
        return 'ch_zici'

    def get_mode(self):
        return self.mode


class WordSetStrategy(SetStrategy, metaclass=ABCMeta):  # 单词出题策略
    def __init__(self, user, mode='均衡'):
        super().__init__(user)
        self.mode = mode

    def get_mode(self):
        return self.mode

    def get_register_name(self):
        return 'en_word'


# ----------------------------------------上下文----------------------------------------
# 记忆类题型抽象上下文
class MemoryContext(metaclass=ABCMeta):
    def __init__(self, user):
        self.render_dict = {
            'zici_tian': ZiCiTianZiCiDoubleTableRender,
            'zici_()': ZiCiParenthesesZiCiDoubleTableRender,
            'word_four_line_three_grid': WordFourLineThreeGridDoubleTableRender,
        }
        self.activator_dict = {
            'ch_zici': ZiCiActivator,
            'en_word': WordActivator
        }

        self.user = user  # 目标用户的User类实例
        self.range_strategy = None  # 传入范围策略类
        self.set_strategy = None  # 传入出题策略类
        self.manual_range = None  # 手动模式下，用户手动确定出题范围

        self.render = self.get_render()
        self.activator = self.get_activator()

    @abstractmethod
    def get_register_name(self):
        pass

    @abstractmethod
    def get_range_class(self):
        """
        :return:范围策略类，例如：ZiCiRangeStrategy
        """
        pass

    @abstractmethod
    def get_set_class(self):
        """
        :return: 出题策略类，例如：ZiCiSetStrategy
        """
        pass

    # 返回激励器实例
    def get_activator(self):
        return self.activator_dict[self.get_register_name()](self.user)

    # 返回渲染器实例
    def get_render(self):
        return self.render_dict[self.user.current_info['%s_render' % self.get_register_name()]]

    def set_range_strategy(self, grade, volume, manual_range):
        """
        :param grade: 年级
        :param volume: 上下学期
        :param manual_range: 手动模式下，用户手动确定出题范围
        :return:
        """
        # 如果manual_range为None，说明是自动模式
        if manual_range is None:
            self.range_strategy = self.get_range_class()(user=self.user, grade=grade, volume=volume)
        # 如果manual_range不为None，说明是手动模式
        else:
            self.manual_range = manual_range
            self.range_strategy = self.get_range_class()(user=self.user, manual_range=self.manual_range, grade=grade,
                                                         volume=volume)

    def set_set_strategy(self, set_strategy):
        self.set_strategy = self.get_set_class()(self.user, mode=set_strategy)

    def execute(self):
        """
        range策略获取题目总集，set策略获取排序后的有效题目集，execute返回最终的题目集
        """
        # 检查是否设定了策略
        if self.range_strategy is None:
            raise ValueError('未设定范围策略')
        if self.set_strategy is None:
            raise ValueError('未设定出题策略')

        # 获取题目总集（饱和）
        range_data = self.range_strategy.execute()
        # 获取排序后的有效题目集
        return self.set_strategy.execute(range_data)


# ZiCi模块的策略上下文
class ChZiCi(MemoryContext):
    def __init__(self, user):
        super().__init__(user)

    def get_register_name(self):
        return 'ch_zici'

    def get_set_class(self):
        return ZiCiSetStrategy

    def get_range_class(self):
        return ZiCiRangeStrategy


# ZiCi模块的策略上下文
class EnWord(MemoryContext):
    def __init__(self, user):
        super().__init__(user)

    def get_register_name(self):
        return 'en_word'

    def get_set_class(self):
        return WordSetStrategy

    def get_range_class(self):
        return WordRangeStrategy


# 测试
if __name__ == '__main__':
    from account.user import User

    m = EnWord(User('646e9421-0efa-4435-a001-78ed9a689a68'))
    m.set_range_strategy(grade='4', volume='2', manual_range=1)
    m.set_set_strategy(set_strategy='均衡')
    print(m.execute())
