"""
抽象工厂模式之抽象产品、抽象工厂
"""

from abc import ABCMeta, abstractmethod


# ------抽象功能------
class Render(metaclass=ABCMeta):  # 渲染功能
    @abstractmethod
    def render(self):
        """
        :return: 渲染过程
        """
        pass
