"""
外观模式
"""


# 子系统类

class CPU:
    def run(self):
        print("cpu startup")

    def stop(self):
        print("cpu shutdown")


class Disk:
    def run(self):
        print("disk startup")

    def stop(self):
        print("disk shutdown")


class Memory:
    def run(self):
        print("memory startup")

    def stop(self):
        print("memory shutdown")


# 外观类
class Computer:
    def __init__(self):
        self.cpu = CPU()
        self.disk = Disk()
        self.memory = Memory()

    def run(self):
        print("start the computer")
        self.cpu.run()
        self.disk.run()
        self.memory.run()

    def stop(self):
        print("shutdown the computer")
        self.cpu.stop()
        self.disk.stop()
        self.memory.stop()


# 客户端
if __name__ == '__main__':
    computer = Computer()
    computer.run()
    computer.stop()
