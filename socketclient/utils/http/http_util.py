from http import client

from urllib3 import HTTPResponse

from socketclient.Connector import Connector
from socketclient.SocketClient import SocketClient
from socketclient.utils import cookie_util
from socketclient.log import logger


DEFAULT_HEADERS = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'


def get_host_and_port(url, return_uri=False):
    # http协议处理
    port = None
    if url.startswith('https://'):
        url = url[8:]
        port = 443
    elif url.startswith('http://'):
        url = url[7:]
        # TODO 处理其他端口
        port = 80
    url_split = url.split('/', 1)
    host = url_split[0]
    if return_uri:
        if len(url_split) > 1:
            return host, port, url_split[1]
        else:
            return host, port, ''
    else:
        return host, port


def mark_http_req_byte(url, method='GET', params=None, data=None, headers=None, cookies=None,
                       is_return_host_port=False):
    host, port, uri = get_host_and_port(url, True)
    uri_list = ['/', uri]
    if params:
        uri_list.append('?')
        if isinstance(params, dict):
            params_list = []
            for key, value in params.items():
                params_list.append(f'&{key}={value}')
            uri_list.append(''.join(params_list)[1:])
        elif isinstance(params, str):
            uri_list.append(params)
    # 处理报文
    b_msg_array = bytearray()
    if isinstance(headers, dict):
        headers_list = []
        for key, value in headers.items():
            if key.lower() == 'cookie' and cookies is None:
                cookies = value
            else:
                headers_list.append(f'{key}: {value}\r\n')
        headers_str = ''.join(headers_list)
    elif isinstance(headers, str):
        headers_str = headers
    else:
        # 默认添加请求头
        headers_str = f'{DEFAULT_HEADERS}\r\n'
    msg_list = [f'{method} {"".join(uri_list)} HTTP/1.1\r\nHost: {host}\r\n']
    if cookies is not None and cookies != '':
        headers_str = f'{headers_str}Cookie: {cookie_util.get_cookies_str(cookies)}\r\n'
    if data:
        content_len = 0
        data_bytes = None
        if isinstance(data, dict):
            data_list = []
            for key, value in data.items():
                data_list.append(f'&{key}={value}')
            data_bytes = ''.join(data_list)[1:].encode()
            headers_str = f'{headers_str}Content-Type: application/x-www-form-urlencoded;charset=UTF-8\r\n'
        elif isinstance(data, str):
            data_bytes = data.encode()
            headers_str = f'{headers_str}Content-Type: application/json;charset=UTF-8\r\n'
        if data_bytes is not None:
            content_len = len(data_bytes)
        msg_list.append(f'{headers_str}Content-Length: {content_len}\r\nConnection: keep-alive\r\n\r\n')
        b_msg_array.extend(''.join(msg_list).encode())
        if content_len != 0:
            b_msg_array.extend(data_bytes)
    else:
        msg_list.append(f'{headers_str}Connection: keep-alive\r\n\r\n')
        b_msg_array.extend(''.join(msg_list).encode())
    if is_return_host_port:
        return host, port, bytes(b_msg_array)
    else:
        return bytes(b_msg_array)


def get_conn_http_response(conn: Connector):
    return conn.do_func(get_socket_http_response)


def get_socket_http_response(sock):
    charset = 'utf-8'
    _UNKNOWN = 'UNKNOWN'
    http_response = None
    # 接收html字节数据
    r = client.HTTPResponse(sock)
    try:
        try:
            r.begin()
        except ConnectionError as ce:
            logger.error('拉取数据异常：%s', ce)
        will_close = r.will_close
        http_response = HTTPResponse.from_httplib(r)
        if will_close and will_close != _UNKNOWN:
            # logger.debug('数据已接收，主机关闭了连接')
            sock.close()
    except Exception as e:
        logger.error('数据接收异常：%s', e)
    finally:
        r.close()
        # print('response：')
        # print(response.decode(charset))
        # 保持连接
        if http_response is not None:
            setattr(http_response, "body", http_response.data.decode(charset))
            return http_response
        else:
            return None


def send_http_request(sc: SocketClient, url, method='GET', params=None, data=None, headers=None, cookies=None,
                      res_func=None):
    host, port, byte_msg = mark_http_req_byte(url, method, params, data, headers, cookies, True)
    with sc.get_connect(host, port) as conn:
        # 发送报文
        # logger.info('发送')
        conn.send(byte_msg)
        # logger.info('已发送')
        # print(byte_msg)
        # 读取报文
        if res_func:
            response = res_func(conn)
        else:
            response = conn.do_func(get_socket_http_response)
    return response
