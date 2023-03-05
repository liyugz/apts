from sqlalchemy import Column, String, create_engine, ForeignKey, Integer, DateTime, Boolean, Float, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
import os
from base_utils.base_funcs import get_folder_path

# 创建对象的基类:
Base = declarative_base()


# 定义User表:
class UserModel(Base):
    # 表的名字:
    __tablename__ = 'user'

    # 表的结构:
    """
        :param username: 用户名，主键
        :param cn_name: 中文名
        :param en_name: 英文名
        :param password: 密码，非空
        :param vip: 是否为vip用户,True为vip用户，False为普通用户,bool 
        :param class_id: 所属班级
        :param identity: 例如 'student' 'teacher'
        :param private_info: json格式，私有信息字典，存储为json字符串
                对学生来说，该字典无嵌套：private_info = {'student_id': '20170101'}
                对教师来说，该字典有嵌套，key是身份元组，其对应的字典，相当远学生的无嵌套信息：private_info = {(class_id,role):{}, ():{}}
    """
    username = Column(String(100), primary_key=True)
    cn_name = Column(String(20))
    en_name = Column(String(20))
    password = Column(String(64), nullable=False)
    vip = Column(Boolean, default=False)
    class_id = Column(String(20))
    identity = Column(String(20))
    private_info = Column(JSON)


# 定义ZiCi题库表
class ZiCiModel(Base):
    # 表的名字:
    __tablename__ = 'zici'

    # 表的结构:
    """
        :param zici_id: 题目id，主键，数字格式，自增
        :param chinese: 汉语字词，200字以内
        :param pinyin: 汉语拼音, 存储为json格式
        :param sentence:例句，json格式，存储为json字符串
        :param zici_type: 词语类型，分为词语表、写字表、识字表
        :param grade: 年级，数字格式
        :param volume: 上下册，分为1,2,1表示上册，2表示下册，数字格式
        :param unit: 单元，数字格式
        :param lesson: 课时，数字格式
    """
    zici_id = Column(Integer, primary_key=True, autoincrement=True)
    chinese = Column(String(300))
    pinyin = Column(JSON)
    sentence = Column(JSON)
    zici_type = Column(String(20))
    grade = Column(Integer)
    volume = Column(Integer)
    unit = Column(Integer)
    lesson = Column(Integer)


# ZiCiRecordModel
class ZiCiRecordModel(Base):
    # 表的名字:
    __tablename__ = 'zici_record'

    # 表的结构:
    """
        :param zici_id: 被考察的字词id，数字格式，主键，参考外键ZiCiModel的id字段
        :param username: 用户名，主键，参考外键UserModel的username字段
        :param correct: 正确与否，数字格式 0表示错误，1表示正确，2表示未作答
        :param opr_time: 答题时间，时间格式，主键，格式为'2018-01-01 12:00:00',不含毫秒
        :param order: 考察顺序，在测试试卷中的顺序
    """
    zici_id = Column(Integer, ForeignKey('zici.zici_id'), primary_key=True)
    username = Column(String(100), ForeignKey('user.username'), primary_key=True)
    correct = Column(Integer)
    opr_time = Column(DateTime, primary_key=True)
    order = Column(Integer)


# 定义Word题库表：英语单词听写题库
class WordModel(Base):
    # 表的名字:
    __tablename__ = 'word'

    # 表的结构:
    """
        :param word_id: 题目id，主键，数字格式，自增
        :param english: 英文单词，100字以内
        :param chinese: 汉语提示，300字以内
        :param sentence:例句，json格式，存储为json字符串
        :param grade: 年级，数字格式
        :param volume: 上下册，分为1,2。1表示上册，2表示下册，数字格式
        :param unit: 单元，数字格式
        :param lesson: 课时，数字格式
    """
    word_id = Column(Integer, primary_key=True, autoincrement=True)
    english = Column(String(100))
    chinese = Column(String(300))
    sentence = Column(JSON)
    grade = Column(Integer)
    volume = Column(Integer)
    unit = Column(Integer)
    lesson = Column(Integer)


# WordRecordModel
class WordRecordModel(Base):
    # 表的名字:
    __tablename__ = 'word_record'

    # 表的结构:
    """
        :param word_id: 被考察的字词id，数字格式，主键，参考外键ZiCiModel的word_id字段
        :param username: 用户名，主键，参考外键UserModel的username字段
        :param correct: 正确与否，数字格式 0表示错误，1表示正确，2表示未作答
        :param opr_time: 答题时间，时间格式，主键，格式为'2018-01-01 12:00:00',不含毫秒
        :param order: 考察顺序，在测试试卷中的顺序
    """
    word_id = Column(Integer, ForeignKey('word.word_id'), primary_key=True)
    username = Column(String(100), ForeignKey('user.username'), primary_key=True)
    correct = Column(Integer)
    opr_time = Column(DateTime, primary_key=True)
    order = Column(Integer)


# KlassModel
class KlassModel(Base):
    # 表的名字:
    __tablename__ = 'klass'

    # 表的结构:
    """
        :param class_id: 班级id，主键，字符串格式
        :param grade: 年级，数字格式
        :param volume: 学期，数字格式，1表示上学期，2表示下学期
        :param private_info: json格式，私有信息字典，存储为json字符串
    """
    class_id = Column(String(20), primary_key=True)
    grade = Column(Integer)
    volume = Column(Integer)
    private_info = Column(JSON)


if __name__ == '__main__':
    # 建表
    # engine = create_engine('sqlite:///apts.db', echo=True)
    # db_path = os.path.join(os.path.join(get_folder_path(), 'db_manager'), r'apts.db')
    engine = create_engine(r'mysql+pymysql://root:password@localhost:3306/apts?charset=utf8', echo=True)
    # Base.metadata.create_all(bind=engine)
    # 创建表
    # WordRecordModel.__table__.create(bind=engine, checkfirst=True)
    # 创建所有表
    Base.metadata.create_all(bind=engine)
