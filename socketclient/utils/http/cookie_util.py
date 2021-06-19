from http.cookiejar import CookieJar

from requests import cookies, models

from socketclient.log import logger


def merge_cookies_from_response(cookie_jar, http_response, url):
    p = models.PreparedRequest()
    p.prepare(url=url)
    cookies.extract_cookies_to_jar(cookie_jar, p, http_response)

    # cookie_list_str = http_response.info().getlist('set-cookie')
    # cookie_jar._now = int(time.time())
    # cookie_set = cookiejar.parse_ns_headers(cookie_list_str)
    # cookie_tuples = cookie_jar._normalized_cookie_tuples(cookie_set)
    #
    # for tup in cookie_tuples:
    #     cookie = mark_cookie(tup)
    #     if cookie:
    #         cookie_jar.set_cookie(cookie)

    return cookie_jar


def get_cookies_str(cookie):
    try:
        if isinstance(cookie, CookieJar):
            cookie_array = []
            for _cookie in iter(cookie):
                cookie_array.append(f'{_cookie.name}={_cookie.value};')
            return ''.join(cookie_array)
        elif isinstance(cookie, dict):
            return cookies.cookiejar_from_dict(cookie).__str__()
        elif isinstance(cookie, str):
            return cookie
        else:
            logger.warning('cookie类型不匹配，使用空值')
            return ''
    except Exception as e:
        logger.error('cookie转换异常，信息：%s', e)
        return ''

# def mark_cookie(tup):
#     return None
