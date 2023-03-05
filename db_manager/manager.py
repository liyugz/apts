"""
数据表操作类
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_manager.models import UserModel, ZiCiModel, ZiCiRecordModel, KlassModel, WordModel, WordRecordModel
import json
import pandas as pd


class DBConnector:
    def __init__(self):
        # 创建数据库引擎
        # self.engine = create_engine(r'mysql+pymysql://root:password@localhost:3306/apts?charset=utf8')
        self.engine = create_engine(r'mysql+pymysql://root_ly:password@120.55.48.49:3306/apts?charset=utf8')

        # 创建会话
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()


class UserManager(DBConnector):
    def __init__(self):
        super().__init__()

    def add(self, model_instance):
        self.session.add(model_instance)
        self.session.commit()

    # 根据cn_name和class_id获取username
    def get_username_by_cn_name_and_class_id(self, cn_name, class_id):
        return self.session.query(UserModel.username).filter(UserModel.cn_name == cn_name,
                                                             UserModel.class_id == class_id).first()[0]

    # 根据class_id获取学生username列表，即identity为student的username
    def get_student_username_by_class_id(self, class_id):
        username_list = self.session.query(UserModel.username).filter(UserModel.identity == 'student',
                                                                      UserModel.class_id == class_id).all()
        # 从元组中取出username
        username_list = [username[0] for username in username_list]
        return username_list

    # 根据class_id获取学生数据，返回dataframe对象
    def get_student_by_class_id(self, class_id):
        student_list = self.session.query(UserModel).filter(UserModel.identity == 'student',
                                                            UserModel.class_id == class_id).all()

        # 将数据转为dataframe格式
        student_df = pd.DataFrame([student.__dict__ for student in student_list])
        # 把json格式的数据转为dict格式，json字段为private_info
        student_df['private_info'] = student_df['private_info'].apply(lambda x: json.loads(x))
        # 删除多余的字段
        student_df = student_df.drop(columns=['_sa_instance_state', 'password'])
        # # 如果'private_info'字段有键值'print_order'，则为学生新增字段'print_order'，并按照'print_order'字段排序，其他字段也跟着变化
        if 'print_order' in student_df['private_info'][0].keys():
            student_df['print_order'] = student_df['private_info'].apply(lambda x: int(x['print_order']))
            student_df = student_df.sort_values(by='print_order')
        # 如果'private_info'字段有键值'group'，则为学生新增字段'group'，并按照'group'字段排序
        elif 'group' in student_df['private_info'][0].keys():
            student_df['group'] = student_df['private_info'].apply(lambda x: x['group'])
            student_df = student_df.sort_values(by='group')
        student_df = student_df.reset_index(drop=True)
        return student_df

    # 检查user是否存在
    def check_user_exist(self, username):
        return self.session.query(UserModel).filter(UserModel.username == username).first() is not None

    # 检查user与password是否匹配
    def check_user_password(self, username, password):
        return self.session.query(UserModel).filter(UserModel.username == username,
                                                    UserModel.password == password).first() is not None

    # 把某username的新password写入数据库
    def update_password(self, username, new_password):
        self.session.query(UserModel).filter(UserModel.username == username).update({'password': new_password})
        self.session.commit()

    # 把某username的新username写入数据库
    def update_username(self, old_username, new_username):
        self.session.query(UserModel).filter(UserModel.username == old_username).update({'username': new_username})
        self.session.commit()

    # 根据username获取私有信息，并将json转为object
    def get_private_info(self, username):
        private_info = self.session.query(UserModel).filter(UserModel.username == username).first().private_info
        return json.loads(private_info)

    # 根据username更新私有信息，私有信息以json格式存储
    def update_private_info(self, username, private_info):
        # 如果key是元组，把private_info的key转为字符串，key为元组，被_分割
        if isinstance(list(private_info.keys())[0], tuple):
            private_info = {f'{k[0]}_{k[1]}': v for k, v in private_info.items()}

        # private_info = {f'{k[0]}_{k[1]}': v for k, v in private_info.items()}
        # 将private_info转为json格式
        private_info = json.dumps(private_info)
        self.session.query(UserModel).filter(UserModel.username == username).update({'private_info': private_info})
        self.session.commit()

    # 根据username获取用户信息，返回UserModel对象
    def get_user_info(self, username):
        user_info = self.session.query(UserModel).filter(UserModel.username == username).first()
        # 将json字段private_info转为object
        user_info.private_info = json.loads(user_info.private_info)
        if user_info.identity == 'teacher':
            # 将private_info中的key转为元组，key为字符串，被__分割，将这两个字符串转为元组
            user_info.private_info = {tuple(k.split('_')): v for k, v in user_info.private_info.items()}
        return user_info


class ZiCiManager(DBConnector):
    def __init__(self):
        super().__init__()

    def add(self, model_instance):
        self.session.add(model_instance)
        self.session.commit()

    # 根据zici_id以update更新某字段，如果是pinyin字段，需要先将object转为json
    def update(self, zici_id, **kwargs):
        for k, v in kwargs.items():
            if k == 'pinyin':
                v = json.dumps(v)
            self.session.query(ZiCiModel).filter(ZiCiModel.zici_id == zici_id).update({k: v})
        self.session.commit()

    # 打印ZiCi表，展示所有字段信息，用prettytable格式化输出
    def show(self):
        zici_list = self.session.query(ZiCiModel).all()
        # 将pinyin字段转为object
        for zici in zici_list:
            zici.pinyin = json.loads(zici.pinyin)
        # 将list转为dataframe
        df = pd.DataFrame([zici.__dict__ for zici in zici_list])
        # 删除多余的字段
        if '_sa_instance_state' in df.columns:
            df = df.drop(['_sa_instance_state'], axis=1)
        # 将dataframe转为prettytable格式
        pt = df.to_string(index=False)

    # 从excel中导入字词信息，excel第一行为列名，与ZiCiModel中的字段名称一致
    def import_from_excel(self, excel_path):
        # 读取excel文件
        df = pd.read_excel(excel_path, sheet_name='Sheet1', header=0)
        # 将pinyin字段转为json格式
        df['pinyin'] = df['pinyin'].apply(lambda x: json.dumps(x))
        # 将df转为list，每个元素为一个字典，字典的key为ZiCiModel中的字段名，value为excel中的值
        zici_list = df.to_dict(orient='records')
        # 将list中的字典转为ZiCiModel实例
        zici_model_list = [ZiCiModel(**zici) for zici in zici_list]
        # 将ZiCiModel实例写入数据库
        self.session.add_all(zici_model_list)
        self.session.commit()

    # 获取单元总量
    def get_lesson_count(self, grade, volume):
        # 获取grade、volume对应的所有lesson，然后去重，最后计算长度
        lesson_count = self.session.query(ZiCiModel.lesson).filter(ZiCiModel.grade == grade,
                                                                   ZiCiModel.volume == volume).distinct().count()
        return lesson_count

    # 根据zici_id获取该字词的信息，返回时要把json字段转为object
    def get_item_by_id(self, zici_id):
        # 如果zici_id不是列表，则转为列表
        if not isinstance(zici_id, list):
            zici_id = [zici_id]
        # 根据zici_id列表从数据库中获取字词信息
        zici_list = self.session.query(ZiCiModel).filter(ZiCiModel.zici_id.in_(zici_id)).all()
        # 转为dataframe
        df = pd.DataFrame([zici.__dict__ for zici in zici_list])
        # 删除多余的字段
        if '_sa_instance_state' in df.columns:
            df = df.drop(['_sa_instance_state'], axis=1)
        # 将json字段转为object
        df['pinyin'] = df['pinyin'].apply(lambda x: json.loads(x))
        return df

    # 根据grade、volume、lesson获取该课程的所有字词信息，返回dataframe
    def get_item_by_lesson(self, grade, volume, lesson):
        """
        :param volume: 上下册
        :param grade: 年级
        :param lesson: 可以是列表，也可以是整形数字
        :return:
        """
        # lesson如果是int，转为list
        if isinstance(lesson, int):
            lesson = [lesson]
        # 根据grade、volume、lesson从数据库中获取字词信息
        print(grade, volume, lesson)
        zici_info = self.session.query(ZiCiModel).filter(ZiCiModel.grade == grade,
                                                         ZiCiModel.volume == volume,
                                                         ZiCiModel.lesson.in_(lesson)).all()
        zici_info = pd.DataFrame([zici.__dict__ for zici in zici_info])
        if '_sa_instance_state' in zici_info.columns:
            zici_info = zici_info.drop(['_sa_instance_state'], axis=1)
        # 将pinyin字段转为object
        zici_info['pinyin'] = zici_info['pinyin'].apply(lambda x: json.loads(x))
        # 打印zici_info中的lesson字段
        print(zici_info['lesson'])
        return zici_info

    # # 根据grade、volume、lesson获取该课程的所有字词信息，返回dataframe
    # def get_zici_by_lesson(self, grade, volume, lesson):
    #     """
    #     :param volume: 上下册
    #     :param grade: 年级
    #     :param lesson: 可以是列表，也可以是整形数字
    #     :return:
    #     """
    #     # lesson如果是int，转为list
    #     if isinstance(lesson, int):
    #         lesson = [lesson]
    #     # 根据grade、volume、lesson从数据库中获取字词信息
    #     zici_info = self.session.query(ZiCiModel).filter(ZiCiModel.grade == grade,
    #                                                      ZiCiModel.volume == volume,
    #                                                      ZiCiModel.lesson.in_(lesson)).all()
    #     zici_info = pd.DataFrame([zici.__dict__ for zici in zici_info])
    #     if '_sa_instance_state' in zici_info.columns:
    #         zici_info = zici_info.drop(['_sa_instance_state'], axis=1)
    #     # 将pinyin字段转为object
    #     zici_info['pinyin'] = zici_info['pinyin'].apply(lambda x: json.loads(x))
    #     return zici_info

    # 根据grade、volume、unit获取该课程的所有字词信息，返回dataframe
    def get_item_by_unit(self, grade, volume, unit):
        """
        :param unit: 可以是列表，也可以是整形数字
        :return:
        """
        # unit如果是int，转为list
        if isinstance(unit, int):
            unit = [unit]
        # 根据grade、volume、unit从数据库中获取字词信息
        zici_info = self.session.query(ZiCiModel).filter(ZiCiModel.grade == grade,
                                                         ZiCiModel.volume == volume,
                                                         ZiCiModel.unit.in_(unit)).all()
        zici_info = pd.DataFrame([zici.__dict__ for zici in zici_info])
        if '_sa_instance_state' in zici_info.columns:
            zici_info = zici_info.drop(['_sa_instance_state'], axis=1)
        # 将pinyin字段转为object
        zici_info['pinyin'] = zici_info['pinyin'].apply(lambda x: json.loads(x))
        return zici_info

    # 根据grade、volume获取该课程的所有字词信息，返回dataframe
    def get_item_by_volume(self, grade, volume):
        """
        :param volume: 上下册
        :param grade: 年级
        :return:
        """
        # 根据grade、volume从数据库中获取字词信息
        zici_info = self.session.query(ZiCiModel).filter(ZiCiModel.grade == grade,
                                                         ZiCiModel.volume == volume).all()
        zici_info = pd.DataFrame([zici.__dict__ for zici in zici_info])
        if '_sa_instance_state' in zici_info.columns:
            zici_info = zici_info.drop(['_sa_instance_state'], axis=1)
        # 将pinyin字段转为object
        zici_info['pinyin'] = zici_info['pinyin'].apply(lambda x: json.loads(x))
        return zici_info


class ZiCiRecordManager(DBConnector):
    def __init__(self):
        super().__init__()

    def add_new_record(self, username, item_id, correct, opr_time, order):
        """
        :param order: 顺序
        :param opr_time: 操作时间
        :param username: 用户名
        :param item_id: 字词id
        :param correct: 正确与否，0：错误，1：正确
        :return:
        """
        zici_record = ZiCiRecordModel(username=username, zici_id=item_id, correct=correct, opr_time=opr_time,
                                      order=order)
        self.session.add(zici_record)
        self.session.commit()

    # 根据username、opr_time、zici_id更新correct字段
    def update_score(self, username, opr_time, correct_list):
        """
        :param username: 学生用户名
        :param opr_time: 测试时间
        :param correct_list: 枚举列表，1表示正确，0表示错误，2表示未测试
        :return:
        """
        print(username, opr_time, correct_list)
        item_order = 0
        for correct in correct_list:
            item_order += 1
            if correct == 2:  # 不用插入数据
                continue
            else:  # 更新数据
                self.session.query(ZiCiRecordModel).filter(ZiCiRecordModel.username == username,
                                                           ZiCiRecordModel.opr_time == opr_time,
                                                           ZiCiRecordModel.order == item_order).update(
                    {ZiCiRecordModel.correct: correct})
        self.session.commit()

    # # 根据username获取该用户的所有correct不为2的字词记录，返回dataframe，不考虑年级、学习
    def get_record_by_username_free(self, username):
        # 根据username、zici_id_list获取该用户的所有correct不为2的字词记录
        zici_record = self.session.query(ZiCiRecordModel).filter(ZiCiRecordModel.username == username,
                                                                 ZiCiRecordModel.correct != 2).all()
        if not zici_record:
            return None
        else:
            # 将zici_record转为dataframe
            zici_record = pd.DataFrame([record.__dict__ for record in zici_record])
            if '_sa_instance_state' in zici_record.columns:
                zici_record = zici_record.drop(['_sa_instance_state'], axis=1)
            return zici_record

    # 根据username获取该用户的所有correct不为2的字词记录，返回dataframe
    def get_record_by_username(self, username, grade, volume):
        # 根据grade, volume获取ZiCiManager对应的zici_id
        zici_manager = ZiCiManager()
        zici_info = zici_manager.get_item_by_volume(grade, volume)
        zici_id_list = zici_info['zici_id'].tolist()
        # 根据username、zici_id_list获取该用户的所有correct不为2的字词记录
        zici_record = self.session.query(ZiCiRecordModel).filter(ZiCiRecordModel.username == username,
                                                                 ZiCiRecordModel.zici_id.in_(zici_id_list),
                                                                 ZiCiRecordModel.correct != 2).all()
        if not zici_record:
            return None
        else:
            # 将zici_record转为dataframe
            zici_record = pd.DataFrame([zici_record[i].__dict__ for i in range(len(zici_record))])
            # 如果有_sa_instance_state和id，则删除多余的字段
            if '_sa_instance_state' in zici_record.columns:
                zici_record = zici_record.drop(['_sa_instance_state'], axis=1)
            return zici_record

    # 根据username和lesson列表获取该用户的所有correct不为2的字词记录，返回dataframe
    def get_record_by_lesson(self, username, lesson):
        # 如果lesson是整型数字
        if isinstance(lesson, int):
            lesson = [lesson]
        # 获取该用户的字词记录，自此记录符合以下条件：
        # 1、username为username；
        # 2、zici_id在ZiCiModel中对应的lesson字段在lesson列表中；
        # 3、ZiCiRecordModel的correct不为2
        zici_record = self.session.query(ZiCiRecordModel).filter(ZiCiRecordModel.username == username,
                                                                 ZiCiModel.zici_id == ZiCiRecordModel.zici_id,
                                                                 ZiCiModel.lesson.in_(lesson),
                                                                 ZiCiRecordModel.correct != 2).all()
        if not zici_record:
            return None
        else:
            # 将zici_record转为dataframe
            zici_record = pd.DataFrame([zici_record[i].__dict__ for i in range(len(zici_record))])
            # 删除多余的字段
            if '_sa_instance_state' in zici_record.columns:
                zici_record = zici_record.drop(['_sa_instance_state'], axis=1)
            return zici_record

    # 根据zici_id查询username该字词的测试记录，要求correct不为2，返回DataFrame
    def get_record_by_item_id(self, username, zici_id):
        zici_record = self.session.query(ZiCiRecordModel).filter(ZiCiRecordModel.username == username,
                                                                 ZiCiRecordModel.zici_id == zici_id,
                                                                 ZiCiRecordModel.correct != 2).all()
        if not zici_record:
            return None
        else:
            zici_record = pd.DataFrame([zici_record[i].__dict__ for i in range(len(zici_record))])
            zici_record = zici_record.drop(['_sa_instance_state', 'id'], axis=1)
            return zici_record

    # 根据username和unit获取该用户的所有correct不为2的字词记录，返回dataframe，unit在ZiCiModel中对应的lesson字段在unit列表中
    def get_record_by_unit(self, username, unit):
        # 如果unit是整型数字
        if isinstance(unit, int):
            unit = [unit]
        # 获取该用户的字词记录，自此记录符合以下条件：
        # 1、username为username；
        # 2、zici_id在ZiCiModel中对应的unit字段在unit列表中；
        # 3、ZiCiRecordModel的correct不为2
        zici_record = self.session.query(ZiCiRecordModel).filter(ZiCiRecordModel.username == username,
                                                                 ZiCiModel.zici_id == ZiCiRecordModel.zici_id,
                                                                 ZiCiModel.unit.in_(unit),
                                                                 ZiCiRecordModel.correct != 2).all()
        if not zici_record:
            return None
        else:
            # 将zici_record转为dataframe
            zici_record = pd.DataFrame([zici_record[i].__dict__ for i in range(len(zici_record))])
            # 删除多余的字段
            if '_sa_instance_state' in zici_record.columns:
                zici_record = zici_record.drop(['_sa_instance_state'], axis=1)
            return zici_record

    # 根据username列表和opr_time获取列表内所有用户的测试数据，返回dataframe
    def get_record_by_username_opr_time(self, username, opr_time):
        if isinstance(username, str):
            username = [username]
        zici_record = self.session.query(ZiCiRecordModel).filter(ZiCiRecordModel.username.in_(username),
                                                                 ZiCiRecordModel.opr_time == opr_time).all()
        if not zici_record:
            return None
        else:
            zici_record = pd.DataFrame([zici_record[i].__dict__ for i in range(len(zici_record))])
            if '_sa_instance_state' in zici_record.columns:
                zici_record = zici_record.drop(['_sa_instance_state'], axis=1)
            return zici_record


class KlassManager(DBConnector):
    def __init__(self):
        super().__init__()

    # 新增数据
    def add(self, class_id, grade, volume, private_info=None):
        if not private_info:
            private_info = {}
        # 将private_info转为json字符串
        private_info = json.dumps(private_info)
        klass = KlassModel(class_id=class_id, grade=grade, volume=volume, private_info=private_info)
        self.session.add(klass)
        self.session.commit()
        return klass.class_id

    # 根据klass_id从klass表中获取grade和volume
    def get_grade_and_volume_by_klass_id(self, class_id):
        result = self.session.query(KlassModel).filter(KlassModel.class_id == class_id).first()
        # 把private_info转为dict
        if result.private_info:
            result.private_info = json.loads(result.private_info)
        if not result:
            return None
        else:
            return result.grade, result.volume


class WordManager(DBConnector):
    def __init__(self):
        super().__init__()

    # 通过excel文件导入单词
    def import_from_excel(self, file_path):
        # 读取excel文件，excel文件第一行为表头，第一列为chinese，第二列为english，第三列为lesson，第四列为unit，第五列为grade，第六列为volume，第七列为sentence
        df = pd.read_excel(file_path)
        # 将dataframe转为list
        word_list = df.values.tolist()
        # 为每个元素的子元素进行stirp操作
        for word in word_list:
            for i in range(len(word)):
                if isinstance(word[i], str):
                    word[i] = word[i].strip()
        # 将list中的每个元素转为WordModel对象
        word_list = [WordModel(chinese=word[0], english=word[1], lesson=word[2], unit=word[3], grade=word[4],
                               volume=word[5], sentence=json.dumps([word[6]])) for word in word_list]
        # 将WordModel对象列表批量插入数据库
        self.session.add_all(word_list)
        self.session.commit()

    # 获取单元总量
    def get_lesson_count(self, grade, volume):
        # 获取grade、volume对应的所有lesson，然后去重，最后计算长度
        lesson_count = self.session.query(WordModel.unit).filter(WordModel.grade == grade,
                                                                 WordModel.volume == volume).distinct().count()
        return lesson_count

    # 根据grade、volume、lesson获取该课程的所有字词信息，返回dataframe
    def get_item_by_lesson(self, grade, volume, lesson):
        # 如果lesson是整型数字
        if isinstance(lesson, int):
            lesson = [lesson]
        # 查询lesson列表中的所有lesson
        word = self.session.query(WordModel).filter(WordModel.grade == grade, WordModel.volume == volume,
                                                    WordModel.lesson.in_(lesson)).all()
        # sentence字段为json字符串，需要转为dict
        for i in range(len(word)):
            if word[i].sentence:
                word[i].sentence = json.loads(word[i].sentence)

        if not word:
            return None
        else:
            word = pd.DataFrame([word[i].__dict__ for i in range(len(word))])
            if '_sa_instance_state' in word.columns:
                word = word.drop(['_sa_instance_state'], axis=1)
            return word

    # 根据word_id获取单词所有信息，并返回dataframe
    def get_item_by_id(self, word_id):
        # 如果word_id不是列表
        if not isinstance(word_id, list):
            word_id = [word_id]
        # 查询word_id列表中的所有word_id
        word = self.session.query(WordModel).filter(WordModel.word_id.in_(word_id)).all()
        # sentence字段为json字符串，需要转为dict
        for i in range(len(word)):
            if word[i].sentence:
                word[i].sentence = json.loads(word[i].sentence)
        if not word:
            return None
        else:
            word = pd.DataFrame([word[i].__dict__ for i in range(len(word))])
            if '_sa_instance_state' in word.columns:
                word = word.drop(['_sa_instance_state'], axis=1)
            return word

    def get_item_by_volume(self, grade, volume):
        word = self.session.query(WordModel).filter(WordModel.grade == grade, WordModel.volume == volume).all()
        # sentence字段为json字符串，需要转为dict
        for i in range(len(word)):
            if word[i].sentence:
                word[i].sentence = json.loads(word[i].sentence)
        if not word:
            return None
        else:
            word = pd.DataFrame([word[i].__dict__ for i in range(len(word))])
            if '_sa_instance_state' in word.columns:
                word = word.drop(['_sa_instance_state'], axis=1)
            return word


class WordRecordManager(DBConnector):
    def __init__(self):
        super().__init__()

    # 根据word_id查询username该字词的测试记录，要求correct不为2，返回DataFrame
    def get_record_by_item_id(self, username, word_id):
        result = self.session.query(WordRecordModel).filter(WordRecordModel.username == username,
                                                            WordRecordModel.word_id == word_id,
                                                            WordRecordModel.correct != 2).all()
        if not result:
            return None
        else:
            result = pd.DataFrame([result[i].__dict__ for i in range(len(result))])
            if '_sa_instance_state' in result.columns:
                result = result.drop(['_sa_instance_state'], axis=1)
            return result

    def add_new_record(self, username, item_id, correct, opr_time, order):
        """
        :param order: 顺序
        :param opr_time: 操作时间
        :param username: 用户名
        :param item_id: 字词id
        :param correct: 正确与否，0：错误，1：正确
        :return:
        """
        word_record = WordRecordModel(username=username, word_id=item_id, correct=correct, opr_time=opr_time,
                                      order=order)
        self.session.add(word_record)
        self.session.commit()

    # update_score
    def update_score(self, username, opr_time, correct_list):
        """
        :param username: 学生用户名
        :param opr_time: 测试时间
        :param correct_list: 枚举列表，1表示正确，0表示错误，2表示未测试
        :return:
        """
        item_order = 0
        for correct in correct_list:

            item_order += 1
            if correct == 2:  # 不用插入数据
                continue
            else:  # 更新数据
                if username == '09a16cab-ee8f-4edd-ae02-058e735a460a':
                    print(username, opr_time, item_order, correct)
                self.session.query(WordRecordModel).filter(WordRecordModel.username == username,
                                                           WordRecordModel.opr_time == opr_time,
                                                           WordRecordModel.order == item_order).update(
                    {WordRecordModel.correct: correct})
        self.session.commit()

    # 根据username和word_id获取该用户的该单词的记录
    def get_record_by_username_and_item_id(self, username, word_id):
        result = self.session.query(WordRecordModel).filter(WordRecordModel.username == username,
                                                            WordRecordModel.word_id == word_id).first()
        if not result:
            return None
        else:
            return result

    # 根据username列表和opr_time获取列表内所有用户的测试数据，返回dataframe
    def get_record_by_username_opr_time(self, username, opr_time):
        if isinstance(username, str):
            username = [username]
        # 根据username获取该用户的所有correct不为2的字词记录，返回dataframe
        word_record = self.session.query(WordRecordModel).filter(WordRecordModel.username.in_(username),
                                                                 WordRecordModel.opr_time == opr_time).all()
        if not word_record:
            return None
        else:
            # 将zici_record转为dataframe
            word_record = pd.DataFrame([word_record[i].__dict__ for i in range(len(word_record))])
            if '_sa_instance_state' in word_record.columns:
                word_record = word_record.drop(['_sa_instance_state'], axis=1)
            return word_record

    # # 根据username获取该用户的所有correct不为2的字词记录，返回dataframe，不考虑年级、学习
    def get_record_by_username_free(self, username):
        # 根据username获取该用户的所有correct不为2的字词记录，返回dataframe
        word_record = self.session.query(WordRecordModel).filter(WordRecordModel.username == username,
                                                                 WordRecordModel.correct != 2).all()

        if not word_record:
            return None
        else:
            # 将zici_record转为dataframe
            word_record = pd.DataFrame([word_record[i].__dict__ for i in range(len(word_record))])
            if '_sa_instance_state' in word_record.columns:
                word_record = word_record.drop(['_sa_instance_state'], axis=1)
            return word_record

    # 根据username获取该用户的所有correct不为2的字词记录，返回dataframe
    def get_record_by_username(self, username, grade, volume):
        # 根据grade, volume获取WordManager对应的word_id
        word_manager = WordManager()
        word_info = word_manager.get_item_by_volume(grade, volume)
        word_id_list = word_info['word_id'].tolist()
        # 根据username、word_id_list获取该用户的所有correct不为2的字词记录
        word_record = self.session.query(WordRecordModel).filter(WordRecordModel.username == username,
                                                                 WordRecordModel.word_id.in_(word_id_list),
                                                                 WordRecordModel.correct != 2).all()
        if not word_record:
            return None
        else:
            # 将zici_record转为dataframe
            word_record = pd.DataFrame([word_record[i].__dict__ for i in range(len(word_record))])
            # 如果有_sa_instance_state和id，则删除多余的字段
            if '_sa_instance_state' in word_record.columns:
                word_record = word_record.drop(['_sa_instance_state'], axis=1)
            return word_record

    # 根据username和word_id获取该用户的该单词的correct
    def get_correct_by_username_and_word_id(self, username, word_id):
        result = self.session.query(WordRecordModel).filter(WordRecordModel.username == username,
                                                            WordRecordModel.word_id == word_id).first()
        if not result:
            return None
        else:
            return result.correct

    # 根据username和word_id获取该用户的该单词的opr_time
    def get_opr_time_by_username_and_word_id(self, username, word_id):
        result = self.session.query(WordRecordModel).filter(WordRecordModel.username == username,
                                                            WordRecordModel.word_id == word_id).first()
        if not result:
            return None
        else:
            return result.opr_time

    # 根据username和word_id获取该用户的该单词的opr_type
    def get_opr_type_by_username_and_word_id(self, username, word_id):
        result = self.session.query(WordRecordModel).filter(WordRecordModel.username == username,
                                                            WordRecordModel.word_id == word_id).first()
        if not result:
            return None
        else:
            return result.opr_type


if __name__ == '__main__':
    # WordManager().import_from_excel(r'C:\Users\77828\Desktop\APTS批量录入实例\G4S2第1-2单元单词.xlsx')

    WordManager().temp()
    # k = KlassManager().add('蒲公英班', 3, 2)
    # u = UserManager().get_student_by_class_id('蒲公英班')  # 返回dataframe
    # # 打印每个用户的en_name、cn_name字段
    # for i in range(len(u)):
    #     print(u['en_name'][i], u['cn_name'][i])

    # zi = ZiCiManager().update(6, pinyin='xī shū')
