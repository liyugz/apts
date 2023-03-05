# 单例模式基类
class Singleton:
    """
    单例模式基类
    """

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls)
        return cls._instance


# 单例模式子类
class MyClass(Singleton):
    def __init__(self, a):
        self.a = a


# 调用测试
d = MyClass(1)
f = MyClass(2)
print(d.a)
print(f.a)
