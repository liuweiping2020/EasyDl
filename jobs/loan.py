#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# @Title : 
# @Author : Zackeus
# @File : test.py 
# @Software: PyCharm
# @Time : 2019/4/3 10:52

import requests
from flask import current_app

from extensions import scheduler, db
from models.loan.loan_file import LoanFileModel, LoanFileSchema
from models.loan.img_detail import ImgDetailModel
from models.loan.img_type import ImgTypeModel
from models.file import FileModel

from utils import MyError, is_empty, is_not_empty, abb_str, Assert, codes, split_list, MyThread
from utils.baidu_cloud import Image
from utils.file import ImgUtil


def loan_sort(qps, type_name):
    """
    文件图片文档处理
    :param qps: 并发数
    :param type_name: 贷款类型
    :return:
    """
    with scheduler.app.app_context():
        # 获取待处理贷款流水
        loan_files = LoanFileModel().dao_get_todo(type_name=type_name, limit=10)

        if is_empty(loan_files):
            # 无处理数据，直接结束
            return

        baidu = Image()

        for loan_file in loan_files:
            # 根据贷款流水获取待处理图片明细
            img_details = ImgDetailModel().dao_get_todo_by_loan_file(loan_file)
            # 根据 qps 数进行列表切割
            img_details = split_list(img_details, qps)

            # 线程组
            threads = []

            for img_split_details in img_details:
                t = MyThread(target=process_img, args=(scheduler.app, baidu, img_split_details))
                threads.append(t)

            for i in range(len(threads)):
                threads[i].setDaemon(True)
                threads[i].start()

            for i in range(len(threads)):
                threads[i].join()
                if threads[i].exception:
                    raise threads[i].exception

            with db.auto_commit_db():
                # 更新处理状态
                loan_file.is_handle = True
                loan_file.dao_update()


def process_img(app, baidu, img_split_details):
    with app.app_context():
        for img_detail in img_split_details:
            try:
                img_file = FileModel().dao_get(img_detail.file_id)  # type: FileModel

                with db.auto_commit_db():
                    img_base64 = ImgUtil.img_compress(img_file.file_path)
                    class_info = baidu.to_class(image_bs64=img_base64)

                    if img_detail.id == 'ca5377767b9811e980585800e36a34d8':
                        raise MyError(code=codes.request_limit_reached, msg='调用次数限制')

                    # 分类失败
                    if is_not_empty(class_info.error_code):
                        if class_info.error_code == codes.request_limit_reached:
                            # 调用次数限制
                            raise MyError(code=codes.request_limit_reached, msg=class_info.error_msg)
                        else:
                            raise MyError(code=class_info.error_code, msg=class_info.error_msg)

                    type_code = '[default]'
                    # 判断置信度 大于0.5位准确
                    if class_info.results[0].score > 0.5:
                        type_code = class_info.results[0].name

                    img_type = ImgTypeModel().dao_get_by_code(type_code)  # type: ImgTypeModel
                    if is_empty(img_type):
                        raise MyError(code=requests.codes.server_error, msg='无效的图片类别代号: {0}'.format(type_code))

                    if img_type.is_ocr:
                        # 需要OCR识别 后期扩展
                        pass

                    img_detail.img_type_id = img_type.id
                    img_detail.is_handle = True
                    img_detail.dao_update(nested=True)
            except Exception as e:
                # 判断是否地址池枯竭
                if isinstance(e, MyError) and e.code == str(codes.request_limit_reached):
                    raise e
                else:
                    from utils.response import MyResponse
                    # 实例化异常信息
                    res = MyResponse.init_error(e)

                    with db.auto_commit_db():
                        img_detail.is_handle = True
                        img_detail.err_code = res.code if res.code else str(requests.codes.server_error)
                        img_detail.err_msg = abb_str(res.msg, 100)
                        img_detail.dao_update(nested=True)


def loan_push():
    """
    贷款信息推送
    :return:
    """
    from utils.encodes import Unicode
    from utils.request import ContentType
    from utils.response import MyResponse, MyResponseSchema
    from utils.msg import WXMsg

    with scheduler.app.app_context():
        loan_files = LoanFileModel().dao_get_push()

        if is_empty(loan_files):
            # 无数据推送
            return

        for loan_file in loan_files:
            try:
                loan_dict, errors = LoanFileSchema().dump(loan_file)
                # 对象序列化失败
                Assert.is_true(is_empty(errors), errors)

                res = requests.post(url=loan_file.push_url, json=loan_dict, headers=ContentType.JSON_UTF8.value)
                res.encoding = Unicode.UTF_8.value
                Assert.is_true(res is not None and res.status_code == codes.ok,
                               '推送请求失败, status_code：{0}'.format(res.status_code))

                my_res, errors = MyResponseSchema().load(res.json())
                Assert.is_true(str(codes.success) == my_res.code, '推送失败，code：{0}'.format(my_res.code))

                # 更新推送状态
                loan_file.is_push = True
                loan_file.dao_update()
            except Exception as e:
                # 记录日志
                current_app.logger.exception(e)
                # 发送微信错误报警信息
                err_res = MyResponse.init_error(e)
                WXMsg(
                    msg_content='【贷款文件推送】【{id}】：{msg}'.format(id=loan_file.id, msg=err_res.msg)
                ).send_wx()
            finally:
                # 更新推送次数
                loan_file.push_times += 1
                loan_file.dao_update()