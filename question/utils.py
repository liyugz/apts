"""
question模块的工具函数或类
"""


# 为不同类型的题目分配数量
class TaskAllocator:
    def __init__(self, total_num, **kwargs):
        self.total_num = total_num  # 可供分配的总额度
        self.kwargs = kwargs  # 格式为{题目类型: 占比}

    def allocate(self):
        """
        分配题目数量
        :return: 返回字典，格式为{题目类型: 数量}
        """
        # 计算总占比
        total_ratio = 0
        for ratio in self.kwargs.values():
            total_ratio += ratio

        # 计算各题目类型的数量
        result = {}
        for item_type, ratio in self.kwargs.items():
            item_num = int(self.total_num * ratio / total_ratio)  # 向下取整
            if item_num == 0:
                item_num = 1
            result[item_type] = item_num

        return result
