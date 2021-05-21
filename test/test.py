from socketclient import SocketClient
from socketclient.log import logger
from socketclient.utils import http_util

if __name__ == '__main__':
    client = SocketClient()
    client.init_pool("www.baidu.com", 443, 0, 3)
    client.connect()
    logger.info(1)

    host, port, b_msg = http_util.mark_http_req_byte(url='https://www.baidu.com/', method='GET',
                                                     is_return_host_port=True)
    conn = client.send(host, port, b_msg)
    resp = http_util.get_conn_http_response(conn)
    print(resp.body)

    logger.info(2)
    # time.sleep(1)
    client.close_client()
    logger.info(3)
    exit()
