"""
代理模式，实现了保护代理
"""

from abc import ABCMeta, abstractmethod


# 抽象实体
class Subject(metaclass=ABCMeta):
    @abstractmethod
    def get_content(self):
        pass

    @abstractmethod
    def set_content(self, content):
        pass


# 具体实体
class RealSubject(Subject):
    def __init__(self, content):
        """
        :param content: 一段字符串
        """
        self.content = content  # 初始化文本

    def get_content(self):
        return self.content  # 获取文本

    def set_content(self, content):
        self.content = content  # 修改文本


# 保护代理
class ProtectProxy(Subject):
    def __init__(self, user, content):
        self.user = user
        self.real_subject = RealSubject(content)  # 初始化真实实体

    def get_content(self):
        return self.real_subject.get_content()  # 获取文本

    def set_content(self, content):
        if self.user.role == 'teacher':
            self.real_subject.set_content(content)  # 修改文本
        else:
            raise PermissionError('只有老师才能修改文本')
