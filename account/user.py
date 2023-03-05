"""
User类
设计模式：外观模式

start point: 登录后
"""
from db_manager.manager import UserManager


# ------------------功能类------------------
# 注销登录
class Logout:
    def __init__(self, user):
        self.user = user

    def logout(self):
        # 将所有属性置为None
        self.user.username = None
        self.user.cn_name = None
        self.user.en_name = None
        self.user.password = None
        self.user.class_id = None
        self.user.identity = None
        self.user.private_info = None


# 修改密码
class ChangePassword:
    def __init__(self, user):
        self.user = user

    def change_password(self, new_password):
        self.user.password = new_password
        # 更新数据库
        UserManager().update_password(self.user.username, new_password)


# 修改用户名
class ChangeUsername:
    def __init__(self, user):
        self.user = user

    def change_username(self, new_username):
        # 检查用户名是否存在
        if UserManager().check_user_exist(new_username):
            raise ValueError("username already exists")
        else:
            self.user.username = new_username
            # 更新数据库
            UserManager().update_username(self.user.username, new_username)


# 保存私有信息
class SavePrivateInfo:
    def __init__(self, user):
        self.user = user

    def save_private_info(self):
        # 更新数据库
        UserManager().update_private_info(self.user.username, self.user.private_info)


# 具体外观类基类
class User:
    def __init__(self, username):
        self.username = username
        self.cn_name = None
        self.en_name = None
        self.class_id = None
        self.identity = None
        self.private_info = None

        # 绑定用户角色
        self.current_role = None
        self.current_class_id = None
        self.current_info = None

        # 填充属性
        self.__fill_attributes()
        self.bind_role()

    def __eq__(self, other):
        return self.username == other.username and self.current_role == other.current_role and self.current_class_id == other.current_class_id

    def __str__(self):
        # 获取类名
        return "identity: %s\nusername: %s\ncn_name: %s" % (self.identity, self.username, self.cn_name)

    def show_name(self, name_type):
        if name_type == "ch":
            return self.cn_name
        elif name_type == "en":
            return self.en_name
        else:
            raise ValueError("name_type must be cn or en")

    def logout(self):
        Logout(self).logout()

    def change_password(self, new_password):
        ChangePassword(self).change_password(new_password)

    def change_username(self, new_username):
        ChangeUsername(self).change_username(new_username)

    def __fill_attributes(self):
        # 获取用户信息
        user_info = UserManager().get_user_info(self.username)
        # 填充属性
        self.cn_name = user_info.cn_name
        self.en_name = user_info.en_name
        self.class_id = user_info.class_id
        self.identity = user_info.identity
        self.private_info = user_info.private_info

    # 更新私有信息字段
    def save_private_info(self):
        if self.identity == "teacher":
            self.private_info[(self.current_class_id, self.current_role)] = self.current_info
        else:
            self.private_info = self.current_info
        SavePrivateInfo(self).save_private_info()

    # 删除私有信息指定字段
    def delete_private_info(self, key):
        if self.identity == "teacher":
            del self.private_info[(self.current_class_id, self.current_role)][key]
        else:
            del self.private_info[key]
        SavePrivateInfo(self).save_private_info()

    def bind_role(self, role=None, class_id=None):
        """
        :param role: 对于学生，role为student，对于老师，role为en_teacher, cn_teacher, math_teacher
        :param class_id:
        :return:
        """
        if self.identity == "teacher":
            # 如果class_id为None，且role不为None
            if class_id is None and role is not None:
                # 如果self.private_info的各个key中只有一个value与role相同，那么就将class_id设置为该key的第一个元素
                for key, value in self.private_info.items():
                    if role == key[1]:
                        self.current_class_id = key[0]
                        self.current_role = key[1]
                        self.current_info = self.private_info[key]
                        break
                if self.current_class_id is None:
                    raise ValueError("role not found")
            # 如果class_id不为None，且role为None
            elif class_id is not None and role is None:
                # 如果self.private_info的各个key中只有一个value与class_id相同，那么就将role设置为该key的第二个元素
                for key, value in self.private_info.items():
                    if class_id == key[0]:
                        self.current_class_id = key[0]
                        self.current_role = key[1]
                        self.current_info = self.private_info[key]
                        break
                if self.current_role is None:
                    raise ValueError("class_id not found")
            # 如果class_id为None，且role为None
            elif class_id is None and role is None:
                if len(self.private_info) == 1:
                    # 取出字典中唯一的key
                    key = list(self.private_info.keys())[0]
                    self.current_class_id = key[0]
                    self.current_role = key[1]
                    self.current_info = self.private_info[key]
                else:
                    raise ValueError("class_id and role can not be None at the same time")
            else:
                self.current_role = role
                self.current_class_id = class_id
                self.current_info = self.private_info[(class_id, role)]
        else:
            self.current_role = self.identity
            self.current_class_id = self.class_id
            self.current_info = self.private_info

    # clear private info
    def clear_private_info(self):
        self.current_info = {}
        self.save_private_info()

    # update self private info
    def update_private_info(self, **kwargs):
        for key, value in kwargs.items():
            self.current_info[key] = value
        self.save_private_info()

    # 批量修改学生的私有信息
    def update_student_private_info(self, **kwargs):
        # 如果是老师
        if self.identity == "teacher":
            student_username = UserManager().get_student_username_by_class_id(
                self.current_class_id)  # 获取current_class_id的所有学生
            student_user = [User(username) for username in student_username]  # 转为User对象
            for s_user in student_user:  # 遍历
                for key, value in kwargs.items():  # 遍历kwargs
                    s_user.current_info[key] = value
                s_user.save_private_info()
        # 如果是学生，无权限
        else:
            raise ValueError("permission denied")

    # 批量修改学生的私有信息的字段名，不修改字段值
    def update_student_private_info_key(self, original_key, new_key):
        # 如果是老师
        if self.identity == "teacher":
            student_username = UserManager().get_student_username_by_class_id(
                self.current_class_id)  # 获取current_class_id的所有学生
            student_user = [User(username) for username in student_username]  # 转为User对象
            for s_user in student_user:  # 遍历
                # 如果原字段名存在
                if original_key in s_user.current_info:
                    s_user.current_info[new_key] = s_user.current_info[original_key]
                    del s_user.current_info[original_key]
                    s_user.save_private_info()
                else:
                    raise ValueError("original key not found")
        # 如果是学生，无权限
        else:
            raise ValueError("permission denied")


# 测试
if __name__ == '__main__':
    # 通过列表批量修改学生的私有信息
    # names = ['周悦橦', '万雨希', '刘城弘', '张亦弛', '周及舜', '周茉', '孙哲瀚', '毛与之', '林小淳', '杨宝怡', '郑晴晴',
    #          '刘芸初', '蔡景辰', '杜雨宸', '焦韵嘉', '李茉莉', '邹艺洋', '韩沛霖', '雷宇轩', '罗广锐', '刘幽微',
    #          '龙子瞻']
    # private_info = {'ch_zici_max_num': 15, 'ch_zici_render': 'zici_()',
    #                 'ch_zici_incorrect_ratio': 0.3, 'ch_zici_correct_ratio': 0.2, 'ch_zici_new_ratio': 0.5,
    #                 'ch_zici_learning_speed': 2, 'ch_zici_learning_path': [1, 2, 3], 'ch_zici_test_result': True}
    # for name in names:
    #     # 根据name和class_id查找username
    #     username = UserManager().get_username_by_cn_name_and_class_id(name, '荔枝班')
    #     # 根据username创建User对象
    #     user = User(username)
    #     # 修改私有信息
    #     user.update_private_info(**private_info)

    # 通过英文名列表批量修改学生的私有信息
    # en_names = ['Kaylee', 'Esther', 'Sam', 'Stacy', 'Izzie', 'Felix', 'Leo', 'Phelix', 'Enzo', 'Richard', 'Rory',
    #             'Ivan', 'Ella', 'Mia', 'Ian', 'Melisa', 'Harry', 'Summer', 'Baymax', 'Alex', 'Haylee', 'Frank',
    #             'Maggie', 'Simon']
    #
    # class_id = '蒲公英班'
    # student_info = UserManager().get_student_username_by_class_id(class_id)
    # for username in student_info:
    #     u = User(username)
    #     cnt = 0
    #     for en_name in en_names:
    #         cnt += 1
    #         if en_name == u.en_name:
    #             u.current_info['print_order'] = cnt
    #             u.save_private_info()
    #             # print(cnt)
    #             break

    # 通过教师user对象批量修改学生的私有信息
    t = User('liyu')
    t.update_student_private_info(ch_zici_max_num=15)

    # 通过教师user对象批量修改学生的私有信息的字段名，不修改字段值
    # t = User('Emily')
    # t.clear_private_info()
    # t.current_info['show_name'] = 'en'
    # t.save_private_info()

    # 展示某班学生private_info
    # t = User('tangtang')
    # t.update_student_private_info_key('zici_max_num', 'ch_zici_max_num')
    # t.update_student_private_info_key('zici_render', 'ch_zici_render')
    # t.update_student_private_info_key('zici_incorrect_ratio', 'ch_zici_incorrect_ratio')
    # t.update_student_private_info_key('zici_correct_ratio', 'ch_zici_correct_ratio')
    # t.update_student_private_info_key('zici_new_ratio', 'ch_zici_new_ratio')
    # t.update_student_private_info_key('zici_learning_speed', 'ch_zici_learning_speed')
    # t.update_student_private_info_key('zici_learning_path', 'ch_zici_learning_path')
    # t.update_student_private_info_key('ch_test_result', 'ch_zici_test_result')

    # 展示某生私有信息
    # s = User('083df789-282e-44be-a2c0-1223142e7946')
    # for k, v in s.private_info.items():
    #     print(k, v)
    #
    # u = User('liyu')
    # u.delete_private_info('score_parser')
    # u.save_private_info()

    # 展示某班学生private_info中某个字段
    # class_id = '荔枝班'
    # student_info = UserManager().get_student_username_by_class_id(class_id)
    # for student in student_info:
    #     u = User(student)
    #     print(u.cn_name, u.private_info['ch_zici_max_num'])
    #
    # User('083df789-282e-44be-a2c0-1223142e7946').current_info['en_word_render'] = 'en_word_()'
    pass
