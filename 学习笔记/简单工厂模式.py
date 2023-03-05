from abc import ABCMeta, abstractmethod


# ------抽象产品------
class Payment(metaclass=ABCMeta):
    @abstractmethod
    def pay(self, money):
        pass


# ------具体产品------
class AliPay(Payment):
    def __init__(self, use_huabei=False):
        self.use_huabei = use_huabei

    def pay(self, money):
        if self.use_huabei:
            print(f'花呗支付{money}元')
        print('AliPay pay %s' % money)


class WeChatPay(Payment):
    def pay(self, money):
        print('WeChatPay pay %s' % money)


# ------工厂------
class PaymentFactory():
    def create_payment(self, method):
        if method == 'ali':
            return AliPay()
        elif method == 'huabei':
            return AliPay(use_huabei=True)
        elif method == 'wechat':
            return WeChatPay()
        else:
            raise TypeError('No such payment named %s' % method)


# ------客户端------
pf = PaymentFactory()
p = pf.create_payment('wechat')
p.pay(100)
