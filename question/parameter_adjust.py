"""
调节题量、通过率、学习路径等参数的模块
"""

from account.user import User
from db_manager.manager import UserManager, ZiCiRecordManager, WordRecordManager


class AdjustMaxNum:
    """
    调节题量的类，不用考虑年级、学期的限制，孩子的学习能力和态度与时间的相关性更大，三天调节一次
    确保数据是在当前max_num下取得的
    两次调节之间所容纳的记录数不小于adjust_cnt
    """

    def __init__(self, register_name, class_id):
        self.register_name_class_dict = {'ch_zici': ZiCiRecordManager, 'en_word': WordRecordManager}
        self.register_name = register_name
        self.record_manager = self.register_name_class_dict[register_name]()
        self.class_id = class_id
        self.adjust_cnt = 2  # 统计最近n次记录，即下面注释的n
        self.adjust_bottom_line = 0.8  # 调节线，当近n次率低于该值时，题量减少
        self.adjust_top_line = 0.93  # 调节线，当近n次率高于该值时，题量增加

        self.min_num = 5  # 题量下限
        self.max_num = 20  # 题量上限

    def adjust(self):
        # 查询class_id的所有学生username
        username_list = UserManager().get_student_username_by_class_id(self.class_id)
        # 查询每个学生的最近n次记录
        for username in username_list:
            student = User(username)
            student_max_num = student.current_info['%s_max_num' % self.register_name]
            record_df = self.record_manager.get_record_by_username_free(username)
            # 从record_df中抽取去重的opr_time列，并按照opr_time降序排列
            if record_df is None:
                continue
            opr_time_list = record_df['opr_time'].drop_duplicates().sort_values(ascending=False)
            # 将上述opr_time_list转为列表，并取出前adjust_cnt个元素
            opr_time_list = opr_time_list.tolist()[:self.adjust_cnt]
            # print(opr_time_list)
            # 从record_df中获取opr_time与opr_time_list中的元素相同的行，返回新的df
            record_df = record_df[record_df['opr_time'].isin(opr_time_list)]
            # 计算新的df中的通过率，correct为1表示通过
            correct_rate = record_df['correct'].sum() / len(record_df)
            if correct_rate < self.adjust_bottom_line and student_max_num > self.min_num:  # 应该下调且有下调空间
                # 参数调整
                pre_max_num = int(student_max_num * correct_rate)
                if pre_max_num < student_max_num:
                    if pre_max_num > self.min_num:
                        student.current_info['%s_max_num' % self.register_name] = pre_max_num
                    else:
                        student.current_info['%s_max_num' % self.register_name] = self.min_num
            elif correct_rate > self.adjust_top_line and student_max_num < self.max_num:  # 应该上调且有上调空间
                # 参数调整
                pre_max_num = student_max_num + 1
                if pre_max_num <= self.max_num:
                    student.current_info['%s_max_num' % self.register_name] = pre_max_num

                else:
                    student.current_info['%s_max_num' % self.register_name] = self.max_num
            student.save_private_info()


if __name__ == '__main__':
    AdjustMaxNum('ch_zici', '荔枝班').adjust()
