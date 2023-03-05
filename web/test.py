import openai

openai.api_key = "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"


def generate_response(prompt):
    completions = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )
    message = completions.choices[0].text
    return message.strip()


print(generate_response("请你扮演一名中国的小学语文教师，向学生解释，怎么样才能更容易记住\"瞻\"字"))



# import zipfile
#
#
# # 要压缩的文件列表
#
# # 压缩文件地址为file_path的文件地址，不含后缀
#
#
# def create_zip_file(file_list, archive_name):
#     with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
#         for file_path in file_list:
#             zip_file.write(file_path)
#
#
# # 要压缩的文件列表
# files_to_compress = [r'C:\Users\77828\Desktop\ChatGPT分享.txt', r'C:\Users\77828\Desktop\ChatGPT分享.pptx']
#
# # 压缩后的zip文件名
# zip_file_name = 'my_files.zip'
#
# create_zip_file(files_to_compress, zip_file_name)
