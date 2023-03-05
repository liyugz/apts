"""
策略模式
"""

from abc import ABCMeta, abstractmethod


# 抽象策略
class Strategy(metaclass=ABCMeta):
    @abstractmethod
    def execute(self, data):
        pass


# 具体策略
class FastStrategy(Strategy):
    def execute(self, data):
        print('fast strategy %s' % data)


class SlowStrategy(Strategy):
    def execute(self, data):
        print('slow strategy %s' % data)


# 上下文
class Context:
    def __init__(self, strategy, data):
        self.strategy = strategy
        self.data = data

    def set_strategy(self, strategy):
        self.strategy = strategy

    def do_strategy(self):
        self.strategy.execute(self.data)


# 客户端
if __name__ == '__main__':
    data = 'data'
    s1 = FastStrategy()
    s2 = SlowStrategy()

    # 使用FastStrategy
    context = Context(s1, data)
    context.do_strategy()

    # 使用SlowStrategy
    context.set_strategy(s2)  # 切换策略
    context.do_strategy()
