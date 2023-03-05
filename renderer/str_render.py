"""
字符串渲染器
"""

import docx
import random
from renderer.abstract_classes import Render


class SimpleStrRender(Render):
    def __init__(self, **kwargs):
        """
        :param p:
        :param my_str:
        """
        self.p = kwargs['p']
        self.my_str = kwargs['my_str']

        self.italics = False
        if 'italics' in kwargs:
            self.italics = kwargs['italics']

    def render(self):
        """
        :return:返回段落对象
        """
        # 判断p是否是段落对象实例
        if isinstance(self.p, docx.text.paragraph.Paragraph):
            p = self.p.add_run(' ' + self.my_str)  # 返回run对象
            p.style = 'basic_run'
            if self.italics:
                p.italic = True
            return p
        # 判断p是否是文档对象实例
        elif isinstance(self.p, docx.document.Document):
            p = self.p.add_paragraph(self.my_str)  # 返回paragraph对象
            p.style = 'basic'
            if self.italics:
                p.italic = True
            return p
        else:
            raise TypeError('p must be a paragraph object or a document object')


# 本次未胜，只返回emoji
class SuccessPhraseRender(Render):
    """
    渲染胜利总次数，将胜利次数转换为红旗和奖杯
    """

    def __init__(self, **kwargs):
        """
        :param p:
        :param success_num:
        """
        self.p = kwargs['p']
        self.success_num = kwargs['success_num']

    # 将数字转换为红旗和奖杯
    def success2emoji(self):
        class_one = '🚩'
        class_two = '🏆'
        # 转换率
        exchange_rate = 5
        # 计算红旗的数量
        class_one_num = self.success_num % exchange_rate
        # 计算奖杯的数量
        class_two_num = self.success_num // exchange_rate
        # 拼接字符串
        emoji_str = class_two * class_two_num + class_one * class_one_num
        return emoji_str

    def success_phrase(self):  # 胜利次数增加时，返回取胜短语：本次胜利，则胜利次数一定增加，所以不需要传入参数
        return ''

    def render(self):
        return SimpleStrRender(p=self.p, my_str=self.success2emoji() + self.success_phrase(), italics=True).render()


# 本次胜利，返回：emoji + 取胜短语
class DoubleSuccessPhraseRender(SuccessPhraseRender):
    """
    渲染胜利总次数，将胜利次数转换为红旗和奖杯
    """

    def __init__(self, **kwargs):
        """
        :param p:
        :param success_num:
        """
        super().__init__(p=kwargs['p'], success_num=kwargs['success_num'])

    def success_phrase(self):  # 胜利次数增加时，返回取胜短语：本次胜利，则胜利次数一定增加，所以不需要传入参数
        phrase = {
            1: ['首胜！', 'First Blood！', '旗开得胜！'],
            2: ['两胜！', 'Double kill！'],
            3: ['三捷！', 'Triple kill！', '勇冠三军！'],
            4: ['Quadra kill！', '技惊四座！'],
            5: ['Penta kill！', '过五关！'],
            6: ['666！', '斩六将!'],
            7: ['七进七出！', '西北望，射天狼！'],
            8: ['八胜，越战越勇！', '八面威风！'],
            9: ['九层之台，起于累土', 'Unstoppable！', '连战皆捷！'],
            10: ['Legendary！', '十胜！', '龙城飞将！'],
            11: ['十一胜！', '横扫千军！', '无人能挡！'],
            12: ['十二胜！', '超神！', '沙场点兵！'],
            13: ['十三胜！', '不教胡马度阴山!'],
            14: ['十四胜！', '卓越！', '攀上巅峰！'],
            15: ['十五胜！', '无敌！', '一剑曾当百万师'],
            16: ['十六胜！', '气吞山河！'],
            17: ['十七胜！', '马作的卢飞快！'],
            18: ['十八胜！', '无坚不摧！', '弓如霹雳弦惊！'],
            19: ['十九胜！', '谈笑凯歌还！'],
        }
        # 如果胜利次数在字典中，则从列表中随机返回一个字符串
        if self.success_num in phrase:
            return random.choice(phrase[self.success_num])
        # 如果胜利次数不在字典中，则返回数字+胜
        else:
            return str(self.success_num) + '胜！'
