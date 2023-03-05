"""
成就框渲染器

1、通过lesson数量渲染方格数量
2、通过方格数量推算成就框宽度和高度
"""

from renderer.abstract_classes import Render
from PIL import Image, ImageFont, ImageDraw
import os
import math
import queue
from base_utils.base_funcs import get_folder_path
from renderer.pic_render import AccomplishmentPicRender


# 通过lesson数量计算各种尺寸，然后渲染成就框
class AccomplishmentRender(Render):
    def __init__(self, **kwargs):
        """
        :param p_name:参考段落
        :param lesson_num: 全册课时数量
        :param text: 文本
        :param pass_ratio: 每个lesson通过率
        """
        self.text = kwargs['text']
        self.lesson_num = kwargs['lesson_num']
        self.p_name = kwargs['p_name']
        self.pass_ratio = kwargs['pass_ratio']
        self.canvas_doc_high = 3.2  # 画布置于文档的高度上的实际高度
        self.small_box_spacing = 50
        self.small_box_width = 100
        self.text_box_high = self.small_box_spacing + self.small_box_width
        self.small_box_num = 10  # 每行小方格的数量
        self.edge = 1  # big_box的边距
        self.font_size = int(self.small_box_width * 0.5)
        self.font_name = '方正楷体GBK.ttf'
        self.save_path = os.path.join(get_folder_path(), r'renderer\file\temp\accomplishment.png')
        self.box_border_color = (128, 128, 128)
        self.small_box_success_fill_color = (48, 161, 78, 255)

        # 整合文本框文字格式
        self.font_style = ImageFont.truetype(os.path.join(get_folder_path(), r'renderer\file\fonts', self.font_name),
                                             self.font_size, encoding="utf-8")

        # 整合small_box文本的字体格式
        self.order_font_style = ImageFont.truetype(
            os.path.join(get_folder_path(), r'renderer\file\fonts', 'arial.ttf'),
            self.font_size, encoding="utf-8")

        # 计算画布尺寸，获得canvas_width和canvas_high
        self.row = math.ceil(self.lesson_num / self.small_box_num)  # 行数

        if self.lesson_num < self.small_box_num:
            self.canvas_width = self.lesson_num * self.small_box_width + (
                    self.lesson_num + 1) * self.small_box_spacing + self.edge * 2
        else:
            self.canvas_width = self.small_box_num * self.small_box_width + (
                    self.small_box_num + 1) * self.small_box_spacing + self.edge * 2
        self.canvas_high = self.text_box_high + self.edge * 2 + self.row * self.small_box_width + (
                self.row + 1) * self.small_box_spacing
        self.canvas = Image.new('RGBA', (self.canvas_width, self.canvas_high), (255, 255, 255, 0))

        # 计算text_box宽度
        self.text_box_width = self.canvas_width - self.edge * 2

        # 计算text_box左上角坐标
        self.text_box_left_pos_x = self.edge
        self.text_box_left_pos_y = self.edge

        # 计算text_box右上角坐标
        self.text_box_right_pos_x = self.canvas_width - self.edge
        self.text_box_right_pos_y = self.edge

    # 计算小方格坐标
    def get_small_box_pox_queue(self):
        small_box_queue = queue.Queue()  # 存储每个小方格的坐标，第一行从右往左，其余行从左往右
        for i in range(self.lesson_num):
            row_num = math.ceil((i + 1) / self.small_box_num)  # 第几行
            pos_y = self.text_box_right_pos_y + self.text_box_high + self.small_box_spacing + (row_num - 1) * (
                    self.small_box_width + self.small_box_spacing)  # 计算y坐标
            if i < self.small_box_num:  # 第一行
                pos_x = self.text_box_right_pos_x - (i + 1) * (self.small_box_spacing + self.small_box_width)
                lesson_order = self.small_box_num - i
            else:  # 其余行
                # 该行第几个小方格
                temp_order = (i + 1) % self.small_box_num
                if temp_order == 0:
                    temp_order = self.small_box_num
                pos_x = self.text_box_left_pos_x + self.small_box_spacing + (temp_order - 1) * (
                        self.small_box_spacing + self.small_box_width)
                lesson_order = i + 1
            small_box_queue.put((pos_x, pos_y, lesson_order, self.pass_ratio[int(lesson_order)]))
        return small_box_queue

    # 计算text_box左上角坐标、宽、高
    def get_text_box_pox_size(self):
        text_box_pos_x = self.text_box_left_pos_x
        text_box_pos_y = self.text_box_left_pos_y
        text_with = self.text_box_width
        text_high = self.text_box_high
        return text_box_pos_x, text_box_pos_y, text_with, text_high

    # 计算左竖线上坐标及长度
    def get_left_line_pos_length(self):
        left_line_pos_x = self.text_box_left_pos_x
        left_line_pos_y = self.text_box_right_pos_y + self.text_box_high
        left_line_length = self.row * self.small_box_width + (self.row + 1) * self.small_box_spacing
        return left_line_pos_x, left_line_pos_y, left_line_length

    # 计算右竖线坐标及长度
    def get_right_line_pos_length(self):
        right_line_pos_x = self.text_box_right_pos_x
        right_line_pos_y = self.text_box_right_pos_y + self.text_box_high
        right_line_length = self.row * self.small_box_width + (self.row + 1) * self.small_box_spacing
        return right_line_pos_x, right_line_pos_y, right_line_length

    # 下横线坐标及长度
    def get_bottom_line_pos_length(self):
        bottom_line_pos_x = self.text_box_left_pos_x
        bottom_line_pos_y = self.canvas_high - self.edge
        bottom_line_width = self.text_box_width
        return bottom_line_pos_x, bottom_line_pos_y, bottom_line_width

    # 文字左起始点坐标，返回文字左端点的坐标
    def get_text_pos(self):
        text_pos_x = self.text_box_left_pos_x + self.small_box_width + 2 * self.small_box_spacing
        text_pos_y = self.text_box_left_pos_y + self.text_box_high / 2 - self.font_size / 2
        return text_pos_x, text_pos_y

    def render(self):
        # 绘制画布
        draw = ImageDraw.Draw(self.canvas)

        # 绘制small_box矩形框,边框颜色为灰色,内部填写lesson序号
        small_box_queue = self.get_small_box_pox_queue()
        while not small_box_queue.empty():
            pos_x, pos_y, lesson_order, pass_raito = small_box_queue.get()  # 改进：增加pass_raito参数
            # 绘制小方格
            if pass_raito > 0:  # 如果pass_ratio大于0，则绘制绿色
                draw.rectangle((pos_x, pos_y, pos_x + self.small_box_width, pos_y + self.small_box_width),
                               outline=self.box_border_color, fill=(48, 161, 78, int(255 * pass_raito)))
            else:  # 如果pass_ratio等于0，否则绘制灰色
                draw.rectangle((pos_x, pos_y, pos_x + self.small_box_width, pos_y + self.small_box_width),
                               outline=self.box_border_color, fill=(0, 0, 0, int(255 * 0.05)))
            # 绘制小方格内的文字
            draw.text((pos_x + self.small_box_width / 2 - self.font_size / 2,
                       pos_y + self.small_box_width / 2 - self.font_size / 2),
                      str(lesson_order), fill=(48, 161, 78, 255), font=self.order_font_style)

        # 绘制TextBox，边框颜色为灰色，内部无颜色
        text_box_pos_x, text_box_pos_y, text_with, text_high = self.get_text_box_pox_size()
        draw.rectangle((text_box_pos_x, text_box_pos_y, text_box_pos_x + text_with, text_box_pos_y + text_high),
                       outline=self.box_border_color, fill=(221, 244, 255, 255))

        # 绘制左竖线
        left_line_pos_x, left_line_pos_y, left_line_length = self.get_left_line_pos_length()
        draw.line((left_line_pos_x, left_line_pos_y, left_line_pos_x, left_line_pos_y + left_line_length),
                  fill=self.box_border_color, width=1)

        # 绘制右竖线
        right_line_pos_x, right_line_pos_y, right_line_length = self.get_right_line_pos_length()
        draw.line((right_line_pos_x, right_line_pos_y, right_line_pos_x, right_line_pos_y + right_line_length),
                  fill=self.box_border_color, width=1)

        # 绘制下横线
        bottom_line_pos_x, bottom_line_pos_y, bottom_line_width = self.get_bottom_line_pos_length()
        draw.line((bottom_line_pos_x, bottom_line_pos_y, bottom_line_pos_x + bottom_line_width, bottom_line_pos_y),
                  fill=self.box_border_color, width=1)

        # 绘制文字
        text_pos_x, text_pos_y = self.get_text_pos()
        draw.text((text_pos_x, text_pos_y), self.text, fill=(0, 0, 0), font=self.font_style)

        # 保存图片
        self.canvas.save(self.save_path)

        canvas_width = self.canvas.size[0] / 96 * 2.54  # 打印图片宽度，用厘米表示
        canvas_high = self.canvas.size[1] / 96 * 2.54  # 打印图片高度，用厘米表示
        canvas_doc_width = canvas_width * self.canvas_doc_high / canvas_high
        canvas_doc_high = None
        if canvas_doc_width < 7.7:
            pos_x = 19.1 - canvas_doc_width
            pos_y = 1
        else:
            canvas_doc_width = 7.7
            canvas_doc_high = canvas_high * canvas_doc_width / canvas_width
            pos_x = 19.1 - canvas_doc_width
            pos_y = 1

        # 在word文档中插入图片
        AccomplishmentPicRender(p=self.p_name, pos_x=pos_x, pos_y=pos_y, canvas_doc_high=canvas_doc_high).render()


# # 绘制圆角矩形，未完成
# class RoundedRectangle:
#     def __init__(self):
#         pass
#
#     def draw(self, pos_tuple, radius_tuple, fill, outline):
#         """
#         :param pos_tuple: 左上角坐标，右下角坐标
#         :param radius_tuple: 左上，右上，右下，左下圆角半径
#         :param fill: 填充颜色
#         :param outline: 边框颜色
#         :return:
#         """
#         pass


if __name__ == '__main__':
    # 生成图片
    pass
