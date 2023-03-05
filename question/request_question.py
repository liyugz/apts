"""
为用户提供请求问题的功能
设计模式：代理模式
"""

from abc import ABCMeta, abstractmethod
from account.user import User


# ------------------抽象产品------------------
# 请求题目类
class RequestQuestion(metaclass=ABCMeta):
    @abstractmethod
    def request_question(self, proxy_user, target_user, question_type_list):
        """
        请求题目
        :param proxy_user: 代理用户，即请求题目的用户
        :param target_user: 目标用户，可以是一个User对象，也可以是User对象构成的列表
        :param question_type_list: 题目类型列表
                [
                    {
                        item_module:'zici',
                        grade:2,
                        volume:10,
                        set_strategy:'rocket',
                        range_strategy:'manual',
                        manual_range:[1,23]
                    }
                ]
        :return:列表，列表中的元素为字典，每个字典都是一名学生的请求信息
                [
                    {
                        'proxy_user': proxy_user,
                        'target_user': target_user,
                        'question_type_list': question_type_list
                    }
                ]
        """
        pass


# ------------------具体产品------------------
# 具体请求题目类
class ConcreteRequestQuestion(RequestQuestion):
    def request_question(self, proxy_user, target_user, question_type_list):
        return {'proxy_user': proxy_user,
                'target_user': target_user,
                'question_type_list': question_type_list}


# ------------------代理类------------------
# 保护代理
class RequestQuestionProxy(RequestQuestion):
    def request_question(self, proxy_user, target_user, question_type_list):
        """
        不同身份的用户请求题目的权限不同
        :param proxy_user:
        :param target_user: 目标用户，如果proxy_user是老师，那么target_user可以是一个User对象，也可以是只有一个User对象的列表
        :param question_type_list:
        :return: 字典元素构成的列表，每个字段元素都是一个学生的请求信息，每个字典格式如下：
                {
                    'proxy_user': proxy_user,
                    'target_user': target_user,
                    'question_type_list': question_type_list
                }
        """
        # 判断target_user是否是列表,如果不是,则将其转换为列表
        if not isinstance(target_user, list):
            target_user = [target_user]

        # 定义存储请求信息的列表
        request_question_info = []
        # 获得请求器
        question_requestor = ConcreteRequestQuestion()

        # 请求者是老师
        if proxy_user.identity == 'teacher':
            for stu in target_user:
                # 判断stu是否为User对象，如果不是，则将其转换为User对象
                if not isinstance(stu, User):
                    stu = User(stu)
                request_question_info.append(
                    question_requestor.request_question(proxy_user, stu, question_type_list))
        # 请求者是学生
        else:
            if len(target_user) == 1:  # 判断目标用户是否只有一个
                # 判断目标用户是否为User对象，如果不是，则将其转换为User对象
                if not isinstance(target_user[0], User):
                    target_user[0] = User(target_user[0])
                # 判断请求者是否为目标用户
                if proxy_user == target_user[0]:
                    request_question_info.append(
                        question_requestor.request_question(proxy_user, target_user[0], question_type_list))
            else:
                raise PermissionError('学生只能请求自己的题目')

        # 返回请求题目信息
        return request_question_info
