import os
import subprocess
import fitz


def word_to_pdf(input_file, output_file):
    """
    使用LibreOffice将Word文档转换为PDF
    """
    # 检查文件是否存在
    if not os.path.isfile(input_file):
        print(f"{input_file} 文件不存在")
        return

    # 检查输出文件是否存在
    if os.path.isfile(output_file):
        print(f"{output_file} 已经存在")
        return

    # 使用LibreOffice将Word文档转换为PDF
    command = ['libreoffice', '--headless', '--convert-to', 'pdf', input_file, '--outdir', os.path.dirname(output_file)]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 检查转换是否成功
    if not os.path.isfile(output_file):
        print("转换失败")
        return

    # 将PDF文件打开并保存一次以压缩PDF文件大小
    doc = fitz.open(output_file)
    doc.save(output_file)
    doc.close()
