"""
注册、登录模块
设计模式：代理模式
"""
import uuid
from abc import ABCMeta, abstractmethod
from db_manager.manager import UserManager
from db_manager.models import UserModel
# 导入同级目录下的user.py中的User类
from account.user import User
import json
import pandas as pd


# ------------------抽象产品------------------
# 注册
class Register(metaclass=ABCMeta):
    @abstractmethod
    def register(self, username, cn_name, en_name, password, class_id, identity, **private_info):
        """
            user表中，以下字段构成联合主键，不能重复：username, class_id, identity
            :param username: 用户名
            :param cn_name: 中文名
            :param en_name: 英文名
            :param password: 密码
            :param class_id: 所属班级
            :param identity: 例如 'student' 'teacher'
            :param private_info: 私有信息字典，存储为json字符串
                    对学生来说，该字典无嵌套：private_info = {'student_id': '20170101'}
                    对教师来说，该字典有嵌套，key是身份元组，其对应的字典，相当远学生的无嵌套信息：private_info = {(class_id,role):{}, ():{}}
        """
        pass


# 登录
class Login(metaclass=ABCMeta):
    @abstractmethod
    def login(self, username, password):
        pass


# ------------------具体产品------------------
# 注册
class ConcreteRegister(Register):
    def register(self, username, cn_name, en_name, password, class_id, identity, **private_info):
        # 私人信息会被转为json字符串存储
        private_info = json.dumps(private_info)
        new_user = UserModel(username=username, cn_name=cn_name, en_name=en_name, password=password,
                             class_id=class_id,
                             identity=identity, private_info=private_info)
        UserManager().add(new_user)


# 登录
class ConcreteLogin(Login):
    def login(self, username, password):  # 登陆成功后返回user对象
        # 检查用户名和密码是否匹配
        if UserManager().check_user_password(username, password):
            # 登录成功
            pass


# ------------------保护代理------------------
class RegisterProxy:
    def __init__(self, auto_username=False, auto_password=False):
        self.auto_username = auto_username
        self.auto_password = auto_password

    def register(self, username, cn_name, en_name, password, class_id, identity, **private_info):
        # 检查username是否重复或者为None，如果重复或者为None，判断是否自动生成username，如果不自动生成，返回错误信息
        if UserManager().check_user_exist(username) or username is None:
            if self.auto_username:
                username = uuid.uuid4()
                while UserManager().check_user_exist(username):
                    username = uuid.uuid4()
            else:
                return ValueError('username already exist')

        # 检查password是否为字符串且长度大于6，如果不是，判断是否自动生成password，如果不自动生成，返回错误信息
        if isinstance(password, str):
            if len(password) >= 6:
                pass
        else:
            if self.auto_password:
                password = '123456'
            else:
                return ValueError('password must be a string and length must >= 6')

        # 注册
        ConcreteRegister().register(username, cn_name, en_name, password, class_id, identity, **private_info)


class LoginProxy:
    @staticmethod
    def login(username, password):
        # 检查用户名和密码是否匹配，如果匹配，返回user对象
        if UserManager().check_user_password(username, password):
            # 登录成功
            return User(username)
        else:
            raise ValueError('username or password error')


# 通过excel进行批量注册的函数
def register_from_excel(excel_path, auto_username=True, auto_password=True):
    # 读取excel，第一行为列名，第一个字段为cn_name，第二个字段为class_id，第三个字段为identity，其余字段缺失
    df = pd.read_excel(excel_path, sheet_name='Sheet1', header=0)
    # 预设private_info
    private_info = {'zici_max_num': 20,
                    'zici_incorrect_ratio': 0.3,
                    'zici_correct_ratio': 0.2,
                    'zici_new_ratio': 0.5,
                    'zici_learning_speed': 2,
                    'zici_learning_path': [1, 2, 3]}
    # 遍历每一行，进行注册
    for index, row in df.iterrows():
        cn_name = row['cn_name']
        class_id = row['class_id']
        identity = row['identity']
        # 其余字段缺失
        RegisterProxy(auto_username, auto_password).register(username=None, password=None, class_id=class_id,
                                                             identity=identity, cn_name=cn_name, en_name='',
                                                             **private_info)


# ------------------测试------------------
if __name__ == '__main__':
    # 注册
    # private_info = {'荔枝班_chinese': {}}
    # RegisterProxy(auto_username=True, auto_password=True).register(class_id='荔枝班', identity='teacher',
    #                                                                cn_name='李宇', en_name='liyu',
    #                                                                password='123456', username='liyu',
    #                                                                **private_info
    #                                                                )

    # 通过列表批量注册
    my_dict = {'Phelix': '蔡思宇', 'Izzie': '曾一言', 'Simon': '陈彦达', 'Esther': '陈子忻', 'Baymax': '方泽端',
               'August': '龚经桐', 'Frank': '荆炫博', 'Sam': '李铭亮', 'Ian': '李清绎', 'Rory': '刘小鱼',
               'Harry': '刘旭淳', 'Ivan': '刘聿桁', 'Richard': '李炘阳', 'Leo': '李宇轩', 'Melisa': '施想',
               'Summer': '汪蓦然', 'Stacy': '万歆然', 'Felix': '温凯熙', 'Kaylee': '温彦妮', 'Haylee': '温彦娜',
               'Ella': '叶柳'}
    names = ['Kaylee', 'Esther', 'Sam', 'Stacy', 'Izzie', 'Felix', 'Leo', 'Phelix', 'Enzo', 'Richard', 'Rory', 'Ivan',
             'Ella', 'Mia', 'Ian', 'Melisa', 'Harry', 'Summer', 'Baymax', 'Alex', 'Haylee', 'Frank', 'Maggie', 'Simon']
    #
    for en_name in names:
        if en_name in my_dict.keys():
            cn_name = my_dict[en_name]
        else:
            cn_name = '未输入中文名'
        private_info = {'en_word_max_num': 15, 'en_word_render': 'word_four_line_three_grid',
                        'en_word_incorrect_ratio': 0.3, 'en_word_correct_ratio': 0.2, 'en_word_new_ratio': 0.5,
                        'en_word_learning_speed': 2, 'en_word_learning_path': [1, 2, 3], 'en_word_test_result': True}
        RegisterProxy(auto_username=True, auto_password=True).register(class_id='蒲公英班', identity='student',
                                                                       cn_name=cn_name, en_name=en_name,
                                                                       password='123456', username=None,
                                                                       **private_info
                                                                       )

    # # 登录
    # user = LoginProxy().login('zs', '123456')
    # user.current_info['zici_max_num'] = 20
    # user.save_private_info()

    # 通过excel进行批量注册
    # register_from_excel(r'C:\Users\77828\Desktop\小葫芦班.xlsx')

    pass
