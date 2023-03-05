from abc import ABCMeta, abstractmethod


# ------抽象产品------

class CPU(metaclass=ABCMeta):
    @abstractmethod
    def show_cpu(self):
        pass


class OS(metaclass=ABCMeta):
    @abstractmethod
    def show_os(self):
        pass


class PhoneShell(metaclass=ABCMeta):
    @abstractmethod
    def show_shell(self):
        pass


# ------抽象工厂------

class PhoneFactory(metaclass=ABCMeta):
    @abstractmethod
    def create_cpu(self):
        pass

    @abstractmethod
    def create_os(self):
        pass

    @abstractmethod
    def create_shell(self):
        pass


# ------具体产品------
class AppleCPU(CPU):
    def show_cpu(self):
        print('Apple CPU')


class SnapdragonCPU(CPU):
    def show_cpu(self):
        print('Snapdragon CPU')


class MediaTekCPU(CPU):
    def show_cpu(self):
        print('MediaTek CPU')


class AppleOS(OS):
    def show_os(self):
        print('Apple OS')


class AndroidOS(OS):
    def show_os(self):
        print('Android OS')


class SmallShell(PhoneShell):
    def show_shell(self):
        print('Small Shell')


class BigShell(PhoneShell):
    def show_shell(self):
        print('Big Shell')


# ------具体工厂------

class AppleFactory(PhoneFactory):
    def create_cpu(self):
        return AppleCPU()

    def create_os(self):
        return AppleOS()

    def create_shell(self):
        return BigShell()


class MiFactory(PhoneFactory):
    def create_cpu(self):
        return SnapdragonCPU()

    def create_os(self):
        return AndroidOS()

    def create_shell(self):
        return SmallShell()


# ------客户端------
class Phone:
    def __init__(self, factory):
        self.factory = factory
        self.cpu = factory.create_cpu()
        self.os = factory.create_os()
        self.shell = factory.create_shell()

    def show_info(self):
        self.cpu.show_cpu()
        self.os.show_os()
        self.shell.show_shell()


p = Phone(AppleFactory())
p.show_info()
