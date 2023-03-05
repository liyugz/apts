生成类图的方法：

pyreverse code/

dot -Tpdf classes.dot -o classes.pdf

新增模块：
1、定义词库资源数据表，WordModel
2、定义测试记录数据表，WordRecordModel
3、创建WordManager
4、创建WordRecordManager
5、增加WordRangeStrategy类，用于生成单词范围
6、增加WordManualRangeStrategy类
7、增加WordRandomAutoStrategy类
8、增加WordSetStrategy类，用于生成单词集合
9、增加WordRocketSetStrategy类
10、增加WordEqualizationSetStrategy类
11、增加EnWord类（Context）
12、增加WordActivator类
13、增加ItemNode类

增加record_score