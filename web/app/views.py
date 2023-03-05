import os
import zipfile
import sys
sys.path.append(r'C:\Users\77828\PycharmProjects\APTS')
from datetime import timedelta
from renderer.pdf_render import render_pdf

from flask import render_template, request, send_file, Flask, session, redirect, url_for
from account.auth import LoginProxy
from account.user import User
from director.start import main
from question.record_score import ReadTextFile, ZiCiParser, WordParser
from base_utils.base_funcs import get_folder_path

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'


@app.route("/")
def index():
    if 'username' in session:
        print('%s未点击登录按钮，直接登录' % session['username'])
        return redirect(url_for('manager'))
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        print('get login')
        return render_template('login.html')
    if request.method == 'POST':
        print('post login')
        username = request.form.get('username')
        password = request.form.get('password')
        _user = LoginProxy().login(username, password)
        if not _user:
            return 'Login Failed'

        # 保存用户信息到 session 中，并设置过期时间
        session['username'] = _user.username
        print(request.form.get('remember'))
        if request.form.get('remember'):
            session.permanent = True
            app.permanent_session_lifetime = timedelta(days=14)
            print('session True')
        else:
            print('session False')
            session.permanent = False

        return redirect(url_for('manager'))


@app.route('/manager')
def manager():
    if 'username' in session:
        username = session['username']
        _user = User(username)
        if _user is not None:
            return render_template("manager1.html", username=username, term=int(_user.current_info['term']),
                                   grade=int(_user.current_info['grade']), subject=_user.current_info['subject'],
                                   default_textbook=str(_user.current_info['textbook']))
    return render_template("login.html")


@app.route('/submit', methods=['POST', 'GET'])
def submit():
    username = session['username']
    subject = request.form['subject']
    grade = request.form['grade']
    term = request.form['term']
    text = request.form['textbook'].strip()

    t = User(username)
    t.current_info['subject'] = subject  # 科目
    t.current_info['grade'] = grade  # 年级
    t.current_info['term'] = term  # 学期
    t.current_info['textbook'] = text  # 范围
    t.save_private_info()

    subject_dic = {'语文': 'ch_zici', '英语': 'en_word'}

    target_user = []
    question_type_list = [
        {'item_module': subject_dic[subject],
         'grade': int(grade),
         'volume': int(term),
         'range_strategy': 'manual',
         'set_strategy': '均衡',
         'manual_range': [int(x) for x in text.split(' ')]}
    ]
    # 获取数据
    main(username, 123456, t.current_class_id, target_user, question_type_list)

    # 返回文件
    return render_template("download.html", username=username)


@app.route("/download/<username>")
def download(username):
    user = User(username)
    file_path = user.current_info['paper_path']
    return send_file(file_path, as_attachment=True)


@app.route("/download_pdf/<username>")
def download_pdf(username):
    user = User(username)
    paper_path = user.current_info['paper_path']
    paper_pdf = render_pdf(paper_path)
    return send_file(paper_pdf, as_attachment=True)


@app.route("/download_score_txt/<username>")
def download_score_txt(username):
    user = User(username)
    score_path = user.current_info['score_path']
    return send_file(score_path, as_attachment=True)


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    username = file.filename.split('_')[1]
    # 保存文件
    save_path = os.path.join(get_folder_path(), 'file', 'received', 'score_txt', file.filename)
    file.save(save_path)
    # 录入数据库
    ReadTextFile(User(username), file_path=save_path).read()
    return 'success'


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000)
