import os
import time

from account.auth import LoginProxy
from question.request_question import RequestQuestionProxy
from question.strategy import ChZiCi, EnWord
import docx
import datetime
from base_utils.base_funcs import get_folder_path
from renderer.str_render import SimpleStrRender
from renderer.word_utils.word_utils import DeleteParagraph
from renderer.pic_render import OrderRender
from db_manager.manager import UserManager
import logging

# 设定日志格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class Login:
    def __init__(self, _username, _password):
        self.username = _username
        self.password = _password

    def login(self):
        login = LoginProxy()
        proxy_user = login.login(username=self.username, password=self.password)
        return proxy_user


class RequestQuestion:
    def __init__(self, _proxy_user, _target_user, _question_type_list, target_user_info):
        """
        :param _proxy_user: 代理用户，多为老师
        :param _target_user: 一个用户或者多个用户的列表
        :param _question_type_list: 供_target_user使用的题目类型
        """
        self.proxy_user = _proxy_user
        self.target_user = _target_user
        self.question_type_list = _question_type_list

        # target_user为空时，自动获取所有学生
        if not self.target_user:
            self.target_user = target_user_info['username'].tolist()

    def request(self):
        return RequestQuestionProxy().request_question(proxy_user=self.proxy_user, target_user=self.target_user,
                                                       question_type_list=self.question_type_list)


class GetData:
    def __init__(self, _request_info):
        self.request_info = _request_info
        # register_name: question_module
        self.question_modules = {'ch_zici': ChZiCi, 'ch_paragraph': None, 'ch_sentence': None, 'ch_reading': None,
                                 'en_word': EnWord
                                 }

    def get_data(self):
        """
        :return: 一个list，每个元素是一个字典，proxy_user, target_user, 题目数据，形如：
                [
                        {   'proxy_user': proxy_user,
                            'target_user': target_user,
                            'paper_data':
                            [
                                [question_data1,question_renderer1,activate_info1],
                                [question_data2,question_renderer2,activate_info2],
                                ……
                            ]
                        }

                ]
        """
        result = []
        for r in self.request_info:
            _proxy_user = r['proxy_user']  # User对象
            _target_user = r['target_user']  # User对象
            _question_type_list = r['question_type_list']  # list
            result.append({'proxy_user': _proxy_user, 'target_user': _target_user, 'paper_data': []})
            for question_type in _question_type_list:
                # 提取参数
                question_module = self.question_modules[question_type['item_module']](_target_user)  # 获取出题模块，如ChZiCi
                # range_strategy = question_type['range_strategy']  # 范围策略
                set_strategy = question_type['set_strategy']  # 题目策略
                manual_range = question_type['manual_range']  # 手动范围
                grade = question_type['grade']  # 年级
                volume = question_type['volume']  # 学期
                question_render = question_module.render  # 渲染器
                activator = question_module.activator  # 激励器实例
                activator.bind_params(grade=grade, volume=volume)  # 绑定激励器的参数

                # 设置参数
                # question_module.set_range_strategy(range_strategy, manual_range, grade, volume)
                question_module.set_range_strategy(grade=grade, volume=volume, manual_range=manual_range)
                question_module.set_set_strategy(set_strategy)

                # 执行
                question_node_list = question_module.execute()

                # 添加到result
                result[-1]['paper_data'].append(
                    [question_node_list, question_render, activator, question_module.get_register_name()])
        return result


class Render:
    def __init__(self, data):
        self.data = data

        self.document = docx.Document(os.path.join(get_folder_path(), r'renderer\file', 'document', 'template1.docx'))
        self.opr_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.opr_time_str = self.opr_time.replace(':', '').replace(' ', '').replace('-', '')  # 无连接符的时间字符串

    def render(self):
        cnt = 0
        _proxy_user = self.data[0]['proxy_user']
        for ch in self.data:
            logging.info('Rendering Paper:\t%s' % ch['target_user'].cn_name)

            # 提取数据
            _target_user = ch['target_user']
            paper_data = ch['paper_data']
            cnt += 1

            # 渲染
            p_name = SimpleStrRender(p=self.document, my_str=_target_user.show_name(
                _proxy_user.current_info['show_name'])).render()  # 添加姓名
            SimpleStrRender(p=self.document, my_str='时间：%s' % self.opr_time).render()  # 添加时间
            OrderRender(p=p_name, order=str(cnt), width=1.5, pos_x=1.19, pos_y=1).render()  # 添加序号

            for paper in paper_data:
                question_node_list = paper[0]
                question_renderer = paper[1]
                activator = paper[2]  # 激励器实例
                register_name = paper[3]  # 题目类型
                activator.bind_p_name(p_name=p_name)  # 绑定激励器的参考

                # 记录测试记录，如{'ch_zici':10,'ch_sentence':5}
                self.record_question_type(register_name, question_node_list, _target_user)

                question_renderer(data=question_node_list, document=self.document,
                                  opr_time=self.opr_time).render()  # 渲染题目,渲染题目的渲染器必须有左边三个参数
                activator.bind_p_name(p_name=p_name)
                activator_info = activator.execute()  # 获取激励器信息
                # 如果activator_info不为None或空，渲染激励器
                if activator_info:
                    for activator in activator_info:
                        activator['render'](**activator['kw']).render()  # 渲染激励器
            # 如果不是最后一个学生，添加分页符
            if cnt != len(self.data):
                self.document.add_page_break()
        self.save(_proxy_user)

    def record_question_type(self, question_type, question_node_list, _target_user):
        # 记录测试记录，如{'ch_zici':10,'ch_sentence':5}
        if self.opr_time_str in _target_user.current_info.keys():
            _target_user.current_info[self.opr_time_str].append((question_type, len(question_node_list)))
        else:
            _target_user.current_info[self.opr_time_str] = [(question_type, len(question_node_list))]
        _target_user.save_private_info()

    def save(self, _proxy_user):
        # 为文件命名并保存
        file_name = '%s_%s' % (_proxy_user.username, self.opr_time_str)
        file_path = os.path.join(get_folder_path(), r'file', 'send', 'document', '%s.docx' % file_name)
        # 删除全文第一个段落
        DeleteParagraph(self.document.paragraphs[0]).delete()
        self.document.save(file_path)

        # 生成score.txt文件
        score_file_path = os.path.join(get_folder_path(), r'file', 'send', 'score_txt', 'score_%s.txt' % file_name)
        with open(score_file_path, 'w', encoding='utf-8') as f:
            # 根据班级获取学生姓名
            student_df = UserManager().get_student_by_class_id(_proxy_user.class_id)
            # 从student_df中提取username和cn_name，生成元组列表
            student_list = list(zip(student_df['username'], student_df['cn_name']))
            for student in student_list:
                f.write('%s$\t%s\n' % (student[0], student[1]))

        # 保存文件路径
        _proxy_user.update_private_info(paper_path=file_path)
        _proxy_user.update_private_info(score_path=score_file_path)


def main(_username, _password, _class_id, _target_user, _question_type_list):
    # 开始
    start_time = time.time()

    # 登录并绑定身份
    proxy_user = Login(_username, _password).login()
    proxy_user.bind_role(_class_id)
    target_user_info = UserManager().get_student_by_class_id(_class_id)

    # 发起请求
    request = RequestQuestion(proxy_user, _target_user, _question_type_list, target_user_info).request()
    logging.info('请求数据 ok')

    # 获取数据
    data = GetData(request).get_data()
    logging.info('获取数据 ok')

    # 渲染
    Render(data).render()
    logging.info('渲染文档 ok')

    # 结束：打印时间
    end_time = time.time()
    consumer_time = end_time - start_time
    print('耗时：%s' % consumer_time)
    return consumer_time


if __name__ == "__main__":
    # 登录
    username = 'tangtang'
    password = '123456'

    # role
    class_id = '满天星班'  # 绑定身份
    target_user = ['083df789-282e-44be-a2c0-1223142e7946']  # 目标用户：cn_name

    # 请求
    question_type_list = [
        {'item_module': 'ch_zici',
         'grade': 2,
         'volume': 1,
         'set_strategy': '均衡',
         'manual_range': [4, 5, 6, 7, 8, 9, 10]}
    ]  # 请求题型

    main(username, password, class_id, target_user, question_type_list)
