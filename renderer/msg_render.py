"""
msg_center渲染器
输入：文本
输出：圆角矩形图片

1、先根据文字，创建一张图片，计算出图片的长度
2、根据长度，计算出图片的尺寸
3、根据尺寸，创建一张图片，包含圆角矩形

定义：
high：圆角矩形的高，也是圆弧的直径，外生变量
pre_width：文字的宽，渲染后的测量量，内生变量
edge：页边距，外生变量
"""
from abc import ABCMeta, abstractmethod
from PIL import Image, ImageFont, ImageDraw
import os
from renderer.pic_render import MsgPicRender
from renderer.abstract_classes import Render
from base_utils.base_funcs import get_folder_path


# 左圆弧
class LeftArc:
    @staticmethod
    def get_left_arc(edge, high):  # 返回左圆弧的坐标
        return edge, edge, edge + high, edge + high


# 右圆弧
class RightArc:
    @staticmethod
    def get_right_arc(edge, high, pre_width):  # 返回右圆弧的坐标
        return edge + pre_width, edge, edge + high + pre_width, edge + high


# 上横线
class TopLine:
    @staticmethod
    def get_top_line(edge, high, pre_width):  # 返回上横线的坐标
        return edge + high / 2, edge, edge + high / 2 + pre_width, edge


# 下横线
class BottomLine:
    @staticmethod
    def get_bottom_line(edge, high, pre_width):  # 返回下横线的坐标
        return edge + high / 2, edge + high, edge + high / 2 + pre_width, edge + high


# 文字左端点
class TextLeftPoint:
    @staticmethod
    def get_text_left_point(edge, high, font_size):  # 返回文字左端点的坐标
        return edge + high / 2 - 15, edge + high / 2 - font_size / 2


# 文字左端点
class TextCircleImgLeftPoint:
    @staticmethod
    def get_text_left_point(edge, high, font_size):  # 返回文字左端点的坐标
        return edge + high, edge + high / 2 - font_size / 2


# 获取文字长度
class PreLen:
    def run(self, msg, edge, high, font_style):
        return self.fast_strategy(msg, edge, high, font_style)

    @staticmethod
    def fast_strategy(msg, edge, high, font_style):
        canvas = Image.new('RGB', (3000, edge + high + edge))
        draw = ImageDraw.Draw(canvas)
        draw.text((0, 0), msg, font=font_style, fill=(0, 255, 0))
        bbox = canvas.getbbox()
        # 宽高
        size = (bbox[2] - bbox[0], bbox[3] - bbox[1])
        return size[0]  # width


class FontStyle:
    @staticmethod
    def get_font_style(font_size, font_name):
        font_style = ImageFont.truetype(os.path.join(get_folder_path(), r'renderer\file\fonts', font_name),
                                        font_size, encoding="utf-8")
        return font_style


# msg渲染器模板
class MsgRender(Render, metaclass=ABCMeta):
    def pre_render(self):
        # 计算画布尺寸，并绘制画布
        width = self.get_pre_len() + self.get_edge() + self.get_high() + self.get_edge()
        high = self.get_high() + self.get_edge() + self.get_edge()
        img = Image.new("RGB", (int(width), int(high)), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        # 绘制左圆弧
        draw.arc(self.get_left_arc(), start=90, end=270, fill=self.get_border_color(), width=3)
        # 绘制右圆弧
        draw.arc(self.get_right_arc(), start=270, end=90, fill=self.get_border_color(), width=3)
        # 绘制上边框
        draw.line(self.get_top_line(), fill=self.get_border_color(), width=3)
        # 绘制下边框
        draw.line(self.get_bottom_line(), fill=self.get_border_color(), width=3)
        # 填充文字
        draw.text(self.get_text_left_point(), self.get_msg(), font=self.get_font_style(), fill=self.get_font_color())
        # 返回图片
        return img

    def render(self):
        img = self.pre_render()
        circle_img = self.get_circle()  # 图片地址
        if circle_img:
            circle = Image.open(circle_img)  # 根据图片地址读取图片
            # 图片的宽高
            circle_with = self.get_high() - 3
            circle_high = self.get_high() - 3
            circle = circle.resize((circle_with, circle_high))  # 将图片尺寸缩放至self.get_high() * self.get_high()
            img.paste(circle, (self.get_edge() + 3, self.get_edge() + 3), mask=circle.split()[3])  # 将图片粘贴到img上
        # 保存图片
        img.save(os.path.join(get_folder_path(), r'renderer\file\temp', 'msg.png'))
        # 如果self.get_p_name()不为none，将图片插入到document中
        if self.get_p_name():
            MsgPicRender(p=self.get_p_name()).render()

    @abstractmethod
    def get_p_name(self):  # 返回document对象p_name对象
        pass

    @abstractmethod
    def get_font_color(self):
        pass

    @abstractmethod
    def get_border_color(self):
        pass

    @abstractmethod
    def get_edge(self):
        pass

    @abstractmethod
    def get_high(self):
        pass

    @abstractmethod
    def get_msg(self):
        pass

    @abstractmethod
    def get_right_arc(self):
        pass

    @abstractmethod
    def get_top_line(self):
        pass

    @abstractmethod
    def get_bottom_line(self):
        pass

    @abstractmethod
    def get_text_left_point(self):
        pass

    @abstractmethod
    def get_font_style(self):
        pass

    @abstractmethod
    def get_pre_len(self):
        pass

    @abstractmethod
    def get_left_arc(self):
        pass

    @abstractmethod
    def get_circle(self):
        pass


# 纯文本渲染器
class TextMsgRender(MsgRender):
    def __init__(self, **kwargs):
        """
        :param msg:
        :param p_name:
        """
        self.msg = kwargs['msg']  # 文字
        self.p_name = kwargs['p_name']  # document对象p_name对象

        self.edge = 3  # 页边距
        self.high = 300  # 圆角矩形的高，也是圆弧的直径
        self.font_size = 180  # 字体大小
        self.font_name = '方正喵呜体.ttf'  # 字体
        self.font_color = (0, 0, 0)  # 字体颜色
        self.border_color = (0, 0, 0)  # 边框颜色

        self.get_font_name()
        self.pre_width = self.get_pre_len()  # 文字的宽，渲染后的测量量

    def get_p_name(self):
        return self.p_name

    def get_border_color(self):
        return self.border_color

    @staticmethod
    def check_character_can_render(character, font_style):
        """
        :param font_style:
        :param character: 需要检测的字符
        :return:
        """
        font = font_style
        if font.getmask(character):
            return True
        else:
            return False

    # 字体和线框颜色
    def get_font_color(self):
        return self.font_color

    def get_circle(self):
        return False

    def get_edge(self):
        return self.edge

    def get_high(self):
        return self.high

    def get_msg(self):
        return self.msg

    def get_left_arc(self):
        return LeftArc.get_left_arc(self.edge, self.high)

    def get_right_arc(self):
        return RightArc.get_right_arc(self.edge, self.high, self.pre_width)

    def get_top_line(self):
        return TopLine.get_top_line(self.edge, self.high, self.pre_width)

    def get_bottom_line(self):
        return BottomLine.get_bottom_line(self.edge, self.high, self.pre_width)

    def get_text_left_point(self):
        return TextLeftPoint.get_text_left_point(self.edge, self.high, self.font_size)

    def get_font_style(self):
        return FontStyle.get_font_style(self.font_size, self.font_name)

    # 确定字体名称
    def get_font_name(self):
        font_style = FontStyle.get_font_style(self.font_size, self.font_name)
        flag = True
        for ch in self.msg:
            if not self.check_character_can_render(ch, font_style):
                flag = False
                break
        if not flag:
            self.font_name = '方正楷体GBK.ttf'

    def get_pre_len(self):
        self.pre_width = PreLen().run(self.msg, self.edge, self.high, self.get_font_style())
        return self.pre_width


# 文本+圆形图片msg渲染器，在纯文本渲染器的基础上添加圆形图片，并修改左文字的起始位置函数、文字预渲染长度函数
class TextAndCircleImgMsgRender(TextMsgRender):
    def __init__(self, **kwargs):
        """
        :param msg:
        :param circle_img:
        :param p_name:
        """
        super().__init__(msg=kwargs['msg'], p_name=kwargs['p_name'])
        self.circle_img = kwargs['circle_img']  # 图片地址

    def get_circle(self):
        return self.circle_img

    def get_text_left_point(self):
        result = TextCircleImgLeftPoint.get_text_left_point(self.edge, self.high, self.font_size)
        return result

    def get_pre_len(self):
        self.pre_width = PreLen().run(self.msg, self.edge, self.high, self.get_font_style()) + self.high / 2
        return self.pre_width


if __name__ == '__main__':
    TextMsgRender(msg='鲲鹏展翅九万里！周悦橦！！', p_name=None).render()
    # TextAndCircleImgMsgRender('我们热爱曲面',
    #                           r'C:\Users\77828\PycharmProjects\APTS\renderer\file\st_photos\孙哲瀚.png').render()
