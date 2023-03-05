"""
document文档上添加各类型图片，除了msg_render、table_render中的图片

1、等级徽章，从低到高的等级设计，强调上升
2、过程徽章，强调词量的覆盖面

设计：
1、学习过且未达标的单元设置进度条
2、首次达标的单元放大显示
"""
from renderer.abstract_classes import Render
from abc import ABCMeta, abstractmethod
from renderer.word_utils.add_float_picture import add_float_picture
from docx.shared import Cm
from base_utils.base_funcs import get_folder_path
import os
import queue
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT


# 抽象类
class PicRender(Render, metaclass=ABCMeta):
    def __init__(self, **kwargs):
        """
        :param pos_x:
        :param pos_y:
        """
        self.pos_x = None
        self.pos_y = None
        if 'pos_x' in kwargs:
            self.pos_x = kwargs['pos_x']
        if 'pos_y' in kwargs:
            self.pos_y = kwargs['pos_y']

    def get_pos_x(self):
        return Cm(self.pos_x)

    def get_pos_y(self):
        return Cm(self.pos_y)

    def render(self):
        if self.get_height():
            add_float_picture(self.get_p(),
                              self.get_pic_path(),
                              height=self.get_height(),
                              pos_x=self.get_pos_x(),
                              pos_y=self.get_pos_y())
        else:
            add_float_picture(self.get_p(),
                              self.get_pic_path(),
                              width=self.get_width(),
                              pos_x=self.get_pos_x(),
                              pos_y=self.get_pos_y())

    @abstractmethod
    def get_p(self):
        pass

    @abstractmethod
    def get_height(self):
        """
        :return: 与width互斥，只能有一个
        """
        pass

    @abstractmethod
    def get_width(self):
        """
        :return: 与height互斥，只能有一个
        """
        pass

    @abstractmethod
    def get_pic_path(self):
        pass


# MsgRender中的图片
class MsgPicRender(PicRender):
    def __init__(self, **kwargs):
        super().__init__(pos_x=3.56, pos_y=1.37)
        self.p = kwargs['p']  # 获得p_name的paragraph对象

    def __del__(self):
        os.remove(self.get_pic_path())

    def get_p(self):
        return self.p

    def get_height(self):
        return Cm(0.8)

    def get_width(self):
        return False

    def get_pic_path(self):
        return os.path.join(get_folder_path(), r'renderer\file\temp', 'msg.png')


# TableRender中的序号图片
class TableOrderPicRender(PicRender):
    def __init__(self, **kwargs):
        """
        :param p:
        :param order:
        :param width:
        :param pos_x:
        :param pos_y:
        """
        self.p = kwargs['p']
        self.order = None
        self.width = None
        self.pos_x = None
        self.pos_y = None
        if 'order' in kwargs:
            self.order = kwargs['order']
        if 'width' in kwargs:
            self.width = kwargs['width']
        if 'pos_x' in kwargs:
            self.pos_x = kwargs['pos_x']
        if 'pos_y' in kwargs:
            self.pos_y = kwargs['pos_y']

        super().__init__(pos_x=self.pos_x, pos_y=self.pos_y)

    def get_p(self):
        return self.p

    def get_height(self):
        return False

    def get_width(self):
        return Cm(self.width)

    def get_pic_path(self):
        return os.path.join(get_folder_path(), r'renderer\file', 'num', '%s.png' % self.order)


# TableRender中的正确/总量比图片
class TableSuccessRatePicRender(PicRender):
    def __init__(self, **kwargs):
        """
        :param p:
        :param width:
        :param pos_x:
        :param pos_y:
        """
        self.p = kwargs['p']
        self.width = None
        self.pos_x = None
        self.pos_y = None

        if 'width' in kwargs:
            self.width = kwargs['width']
        if 'pos_x' in kwargs:
            self.pos_x = kwargs['pos_x']
        if 'pos_y' in kwargs:
            self.pos_y = kwargs['pos_y']

        super().__init__(pos_x=self.pos_x, pos_y=self.pos_y)

    def __del__(self):
        os.remove(self.get_pic_path())

    def get_p(self):
        return self.p

    def get_height(self):
        return False

    def get_width(self):
        return Cm(self.width)

    def get_pic_path(self):
        return os.path.join(get_folder_path(), r'renderer\file', 'temp', 'test_result.png')


class TableAnswerSpacePicRender(Render):
    def __init__(self, **kwargs):
        """
        :param p:
        :param pic_name:
        :param height:
        """
        self.p = kwargs['p']
        self.pic_name = None
        self.height = None
        if 'pic_name' in kwargs:
            self.pic_name = kwargs['pic_name']
        if 'height' in kwargs:
            self.height = kwargs['height']

    def render(self):
        p_run = self.p.add_run()
        p_run.add_picture(os.path.join(get_folder_path(), r'renderer\file', 'answer_space', self.pic_name),
                          height=Cm(self.height))
        self.p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER


# OrderRender渲染器
class OrderRender(PicRender):
    def __init__(self, **kwargs):
        """
        :param p:
        :param order:
        :param width:
        :param pos_x:
        :param pos_y:
        """

        self.p = kwargs['p']
        self.order = kwargs['order']
        self.width = None
        self.pos_x = None
        self.pos_y = None
        if 'width' in kwargs:
            self.width = kwargs['width']
        if 'pos_x' in kwargs:
            self.pos_x = kwargs['pos_x']
        if 'pos_y' in kwargs:
            self.pos_y = kwargs['pos_y']

        super().__init__(pos_x=self.pos_x, pos_y=self.pos_y)

    def get_p(self):
        return self.p

    def get_height(self):
        return False

    def get_width(self):
        return Cm(self.width)

    def get_pic_path(self):
        return os.path.join(get_folder_path(), r'renderer\file', 'num', '%s.png' % self.order)


class AccomplishmentPicRender(PicRender):
    def __init__(self, **kwargs):
        """
        :param p:
        :param pos_x:
        :param pos_y:
        :param canvas_doc_high:
        """

        self.p = kwargs['p']
        self.pos_x = None
        self.pos_y = None
        self.canvas_doc_high = None
        if 'pos_x' in kwargs:
            self.pos_x = kwargs['pos_x']
        if 'pos_y' in kwargs:
            self.pos_y = kwargs['pos_y']
        if 'canvas_doc_high' in kwargs:
            self.canvas_doc_high = kwargs['canvas_doc_high']

        self.height = 3.2
        super().__init__(pos_x=self.pos_x, pos_y=self.pos_y)

    def get_p(self):
        return self.p

    def get_height(self):
        if self.canvas_doc_high is None:
            return Cm(self.height)
        else:
            return Cm(self.canvas_doc_high)

    def get_width(self):
        return False

    def get_pic_path(self):
        return os.path.join(get_folder_path(), r'renderer\file', 'temp', 'accomplishment.png')
