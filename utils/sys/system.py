#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# @Title : 系统工具类
# @Author : Zackeus
# @File : system.py 
# @Software: PyCharm
# @Time : 2019/4/30 15:39


import html
from utils.digests import get_salt, digest

HASH_ALGORITHM = 'sha1'
HASH_INTERATIONS = 1024
SALT_SIZE = 8


def entrypt_password(plain_password):
    """
    生成安全的密码，生成随机的16位salt并经过1024次 sha-1 hash
    :param str plain_password: 明文密码
    :return:
    """
    # Html 解码
    plain_password = html.unescape(plain_password)
    salt = get_salt(SALT_SIZE)
    hash_password = digest(plain_password, salt, HASH_ALGORITHM, HASH_INTERATIONS)
    return salt.hex() + hash_password.hex()


def validate_password(plain_password, hash_password):
    """
    验证密码
    :param plain_password: 明文密码
    :param hash_password: 密文密码
    :return:
    """
    plain_password = html.unescape(plain_password)
    salt = bytes.fromhex(hash_password[0:16])
    new_hash_password = digest(plain_password, salt, HASH_ALGORITHM, HASH_INTERATIONS)
    return hash_password == (salt.hex() + new_hash_password.hex())


if __name__ == '__main__':
    # cc1c05fa659f3f27c25a6db39204df3489e81f23b181ec4d6809a34a
    # print(entrypt_password('a1!'))

    print(validate_password('a1!', 'cc1c05fa659f3f27c25a6db39204df3489e81f23b181ec4d6809a34a'))