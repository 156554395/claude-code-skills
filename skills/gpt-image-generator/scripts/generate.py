#!/usr/bin/env python3
"""通过兼容 OpenAI Images 的服务生成单张图片；仅使用标准库。"""
import argparse
import base64
import binascii
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

MODELS = ('gpt-image-2', 'gpt-image-2.5-flare', 'gpt-image-2.5-sunburst')
DEFAULT_CONFIG = Path.home() / '.config/gpt-image-generator/config.json'
LIMIT = 64 * 1024 * 1024


class Error(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prompt', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--model', choices=MODELS)
    p.add_argument('--base-url')
    p.add_argument('--size')
    p.add_argument('--quality', choices=('auto', 'low', 'medium', 'high'))
    p.add_argument('--config', type=Path)
    return p


def settings(args):
    path = args.config or DEFAULT_CONFIG
    config = {}
    if path.exists():
        try:
            config = json.loads(path.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            raise Error('配置文件读取失败或 JSON 无效。') from None
        if not isinstance(config, dict):
            raise Error('配置必须为 JSON 对象。')
        if config.get('api_key') and path.stat().st_mode & 0o077:
            raise Error('含密钥的配置文件权限须为 0600，请先运行 chmod 600。')
    elif args.config:
        raise Error('指定的配置文件不存在。')
    result = {}
    for key, env, default in (
        ('base_url', 'OPENAI_BASE_URL', ''),
        ('api_key', 'OPENAI_API_KEY', ''),
        ('model', 'OPENAI_IMAGE_MODEL', MODELS[1]),
        ('size', 'GPT_IMAGE_SIZE', '1024x1024'),
        ('quality', 'GPT_IMAGE_QUALITY', None),
    ):
        value = getattr(args, key, None) or os.environ.get(env) or config.get(key) or default
        if value is not None and not isinstance(value, str):
            raise Error(f'配置字段 {key} 必须是字符串。')
        result[key] = value
    return result


def validate_url(url):
    try:
        u = urllib.parse.urlsplit(url)
        _ = u.port
        valid = (u.scheme == 'https' or (u.scheme == 'http' and u.hostname in ('127.0.0.1', '::1', 'localhost')))
        if not valid or not u.hostname or u.username or u.password or u.fragment:
            raise ValueError()
        if any(ord(c) <= 32 for c in url):
            raise ValueError()
    except ValueError:
        raise Error('地址无效：使用 HTTPS，不允许 URL 内嵌凭证或 fragment；HTTP 仅限本机。') from None
    return u


def fetch(url, body=None, key=None):
    validate_url(url)
    headers = {}
    if body is not None:
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {key}'}
    request = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=180) as response:
            data = response.read(LIMIT + 1)
    except urllib.error.HTTPError as exc:
        raise Error(f'服务返回 HTTP {exc.code}；检查权限、模型、额度或地址。未自动重试。') from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise Error('网络请求失败或超时；服务端可能已计费，未自动重试。') from None
    if len(data) > LIMIT:
        raise Error('响应超过 64 MiB 限制。')
    return data


def image_suffix(data):
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return '.png'
    if data.startswith(b'\xff\xd8\xff'):
        return '.jpg'
    if data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        return '.webp'
    raise Error('返回内容不是可识别的 PNG/JPEG/WebP 图片。')


def generate(args):
    cfg = settings(args)
    if not cfg['base_url'] or not cfg['api_key']:
        raise Error('请配置 OPENAI_BASE_URL 和 OPENAI_API_KEY，或用户级 config.json。')
    if '\n' in cfg['api_key'] or '\r' in cfg['api_key']:
        raise Error('API Key 含非法换行。')
    if cfg['model'] not in MODELS:
        raise Error('模型不在允许列表中。')
    if not args.prompt.strip():
        raise Error('提示词不能为空。')
    base = cfg['base_url'].rstrip('/')
    if validate_url(base).query or base.endswith('/images/generations'):
        raise Error('baseurl 应为无 query 的 API 前缀，不含 /images/generations。')
    size = cfg['size']
    if size != 'auto':
        match = re.fullmatch(r'(\d{1,4})x(\d{1,4})', size)
        if not match:
            raise Error('size 应为 auto 或 宽x高，例如 1024x1024。')
        w, h = map(int, match.groups())
        if not (w and h and w % 16 == h % 16 == 0 and max(w, h) <= 3840
                and max(w, h) / min(w, h) <= 3 and 655360 <= w * h <= 8294400):
            raise Error('尺寸须为16的倍数，最长边≤3840，比例≤3:1，总像素655360–8294400。')
    if cfg['quality'] not in (None, 'auto', 'low', 'medium', 'high'):
        raise Error('quality 应为 auto/low/medium/high。')
    output = Path(args.output).expanduser().absolute()
    if os.path.lexists(output):
        raise Error('输出路径已存在，拒绝覆盖；请选择新文件名。')
    if not output.parent.is_dir() or not os.access(output.parent, os.W_OK):
        raise Error('输出目录不存在或不可写，请先准备目录。')
    if output.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp'):
        raise Error('输出扩展名须为 .png/.jpg/.jpeg/.webp。')
    body = {'model': cfg['model'], 'prompt': args.prompt, 'size': size}
    if cfg['quality']:
        body['quality'] = cfg['quality']
    raw = fetch(base + '/images/generations', json.dumps(body).encode(), cfg['api_key'])
    try:
        result = json.loads(raw)
        item = result['data'][0]
        if item.get('b64_json'):
            data = base64.b64decode(item['b64_json'], validate=True)
        elif isinstance(item.get('url'), str):
            data = fetch(item['url'])
        else:
            raise ValueError()
    except (ValueError, KeyError, IndexError, TypeError, AttributeError, binascii.Error):
        raise Error('响应缺少有效 data[0].b64_json/url 或 JSON/base64 无效。') from None
    suffix = image_suffix(data)
    if output.suffix.lower().replace('.jpeg', '.jpg') != suffix:
        raise Error(f'实际图片格式是 {suffix}，与输出扩展名不符；未保存，勿自动重新生成。')
    try:
        with output.open('xb') as f:
            f.write(data)
    except OSError:
        raise Error('图片保存失败（可能文件已存在）；未重试生成。') from None
    return {'ok': True, 'model': cfg['model'], 'file': str(output), 'bytes': len(data)}


def main():
    args = parser().parse_args()
    try:
        print(json.dumps(generate(args), ensure_ascii=False))
        return 0
    except (Error, OSError):
        exc = sys.exc_info()[1]
        message = str(exc) if isinstance(exc, Error) else '本地文件操作失败。'
        print(json.dumps({'ok': False, 'error': message}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
