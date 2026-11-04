"""离线协议测试与本机 CLI 端到端测试，无真实付费请求。"""
import base64
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.error

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/generate.py'
spec = importlib.util.spec_from_file_location('generate', SCRIPT)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j5XcAAAAASUVORK5CYII=')
RESPONSE = json.dumps({'data': [{'b64_json': base64.b64encode(PNG).decode()}]}).encode()


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.env = patch.dict(os.environ, {'OPENAI_BASE_URL': 'https://example.com/custom/v1/', 'OPENAI_API_KEY': 'test-secret'}, clear=True)
        self.env.start()
        self.default = patch.object(g, 'DEFAULT_CONFIG', self.root / 'absent.json')
        self.default.start()

    def tearDown(self):
        self.default.stop()
        self.env.stop()
        self.tmp.cleanup()

    def args(self, *extra):
        return g.parser().parse_args(['--prompt', '测试', '--output', str(self.root / 'image.png'), *extra])

    def test_models_and_endpoint(self):
        for model in g.MODELS:
            with self.subTest(model=model), patch.object(g, 'fetch', return_value=RESPONSE) as call:
                result = g.generate(self.args('--model', model))
                url, body, key = call.call_args.args
                self.assertEqual(url, 'https://example.com/custom/v1/images/generations')
                self.assertEqual(json.loads(body), {'model': model, 'prompt': '测试', 'size': '1024x1024'})
                self.assertEqual(key, 'test-secret')
                self.assertEqual(Path(result['file']).read_bytes(), PNG)
                Path(result['file']).unlink()
        self.assertEqual(g.settings(self.args())['model'], g.MODELS[1])

    def test_configuration_priority(self):
        config = self.root / 'config.json'
        config.write_text(json.dumps({'base_url': 'https://config.example/v1', 'api_key': 'config-key', 'model': g.MODELS[0]}))
        config.chmod(0o600)
        args = self.args('--config', str(config))
        self.assertEqual(g.settings(args)['api_key'], 'test-secret')
        os.environ['OPENAI_IMAGE_MODEL'] = g.MODELS[2]
        self.assertEqual(g.settings(args)['model'], g.MODELS[2])
        self.assertEqual(g.settings(self.args('--config', str(config), '--model', g.MODELS[1]))['model'], g.MODELS[1])
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(g.settings(args)['api_key'], 'config-key')
        config.chmod(0o644)
        with self.assertRaises(g.Error):
            g.settings(args)

    def test_url_response_has_no_key(self):
        response = json.dumps({'data': [{'url': 'https://cdn.example/image.png?sig=test'}]}).encode()
        with patch.object(g, 'fetch', side_effect=[response, PNG]) as call:
            g.generate(self.args())
            self.assertEqual(call.call_args_list[1].args, ('https://cdn.example/image.png?sig=test',))

    def test_invalid_responses(self):
        for response in (b'{}', b'{"data":[]}', b'{"data":[{}]}', b'null', b'not-json', b'{"data":[{"b64_json":"%%%"}]}', b'{"data":[{"b64_json":"aGVsbG8="}]}'):
            with self.subTest(response=response), patch.object(g, 'fetch', return_value=response):
                with self.assertRaises(g.Error):
                    g.generate(self.args())
                self.assertFalse((self.root / 'image.png').exists())

    def test_preflight_errors_send_nothing(self):
        for extra in (('--size', '1x1'), ('--base-url', 'http://remote.example/v1'), ('--base-url', 'https://example.com/v1?key=x'), ('--base-url', 'https://user:pass@example.com/v1'), ('--base-url', 'https://example.com/v1/images/generations')):
            with self.subTest(extra=extra), patch.object(g, 'fetch') as call:
                with self.assertRaises(g.Error):
                    g.generate(self.args(*extra))
                call.assert_not_called()
        output = self.root / 'image.png'
        output.symlink_to(self.root / 'missing')
        with patch.object(g, 'fetch') as call, self.assertRaises(g.Error):
            g.generate(self.args())
        call.assert_not_called()

    def test_http_errors_no_retry_and_no_secret(self):
        for code in (400, 401, 403, 429, 500, 302):
            opener = unittest.mock.Mock()
            opener.open.side_effect = urllib.error.HTTPError('https://example.com', code, 'test-secret', {}, io.BytesIO(b'test-secret'))
            with patch.object(g.urllib.request, 'build_opener', return_value=opener):
                with self.assertRaises(g.Error) as error:
                    g.fetch('https://example.com/v1', b'{}', 'test-secret')
                self.assertNotIn('test-secret', str(error.exception))
                self.assertIn(str(code), str(error.exception))
                opener.open.assert_called_once()
        opener.open.reset_mock()
        opener.open.side_effect = TimeoutError('test-secret')
        with patch.object(g.urllib.request, 'build_opener', return_value=opener):
            with self.assertRaises(g.Error):
                g.fetch('https://example.com/v1', b'{}', 'test-secret')
            opener.open.assert_called_once()

    def test_missing_config_and_empty_prompt(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(g, 'fetch') as call:
            with self.assertRaises(g.Error):
                g.generate(self.args())
            call.assert_not_called()
        with self.assertRaises(g.Error):
            g.generate(self.args('--prompt', ' '))

    def test_cli_end_to_end(self):
        seen = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                seen.append((self.path, self.headers.get('Authorization'), json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(RESPONSE)
            def log_message(self, *args):
                pass
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            env = dict(os.environ, OPENAI_BASE_URL=f'http://127.0.0.1:{server.server_port}/custom/v1')
            config = self.root / 'empty.json'
            config.write_text('{}')
            run = subprocess.run([sys.executable, str(SCRIPT), '--config', str(config), '--prompt', '猫', '--output', str(self.root / 'cli.png')], env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertTrue(json.loads(run.stdout)['ok'])
            self.assertEqual(seen[0][0], '/custom/v1/images/generations')
            self.assertEqual(seen[0][1], 'Bearer test-secret')
            self.assertEqual(seen[0][2]['model'], g.MODELS[1])
            self.assertEqual((self.root / 'cli.png').read_bytes(), PNG)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
