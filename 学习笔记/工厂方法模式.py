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


# ------抽象工厂------
class PaymentFactory(metaclass=ABCMeta):
    @abstractmethod
    def create_payment(self):
        pass


# ------具体工厂------
class AliPayFactory(PaymentFactory):
    def create_payment(self):
        return AliPay()


class HuabeiFactory(PaymentFactory):
    def create_payment(self):
        return AliPay(use_huabei=True)


class WeChatPayFactory(PaymentFactory):
    def create_payment(self):
        return WeChatPay()


# ------客户端------
pf = AliPayFactory()
p = pf.create_payment()
p.pay(100)
