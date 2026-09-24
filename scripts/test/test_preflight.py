#!/usr/bin/env python3
"""
Tests for the ArtifactInstall_Enter_10_retina_preflight Mender state script.

The script runs as root on every node, before the docker-compose Update Module
stops the running stack, so each test runs the real script under /bin/sh with a
stub `docker` on PATH that records every call.
"""

import io
import os
import shutil
import subprocess
import tarfile
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'mender-state-scripts', 'ArtifactInstall_Enter_10_retina_preflight')

STUB_DOCKER = r'''#!/bin/sh
echo "$*" >> "$STUB/calls"
for last; do :; done
case "$1" in
    inspect)
        [ -f "$STUB/containers/$last" ] || exit 1
        cat "$STUB/containers/$last" ;;
    rename)
        [ -f "$STUB/rename_fails" ] && exit 1
        mv "$STUB/containers/$2" "$STUB/containers/$3" ;;
    compose)
        if [ -f "$STUB/compose_error" ]; then cat "$STUB/compose_error" >&2; exit 1; fi ;;
esac
exit 0
'''

MANIFEST = '''services:
  blah2:
    image: ghcr.io/offworldlabs/blah2:v0.6.0
    container_name: blah2
  tar1090:
    image: ghcr.io/offworldlabs/tar1090-node:v0.2.1
    container_name: "tar1090"
'''


class TestPreflight(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.stub = os.path.join(self.dir, 'stub')
        self.bin = os.path.join(self.dir, 'bin')
        self.root = os.path.join(self.dir, 'mender-docker-compose')
        self.payload = os.path.join(self.dir, 'payload')
        self.manifests = os.path.join(self.root, 'current', 'manifests')
        for d in (os.path.join(self.stub, 'containers'), self.bin, self.manifests, self.payload):
            os.makedirs(d)
        docker = os.path.join(self.bin, 'docker')
        with open(docker, 'w') as f:
            f.write(STUB_DOCKER)
        os.chmod(docker, 0o755)
        self.write(os.path.join(self.manifests, 'docker-compose.yaml'), MANIFEST)

    def tearDown(self):
        shutil.rmtree(self.dir)

    def write(self, path, text, mode='w'):
        with open(path, mode) as f:
            f.write(text)

    def container(self, name, project):
        self.write(os.path.join(self.stub, 'containers', name), project + '\n')

    def run_preflight(self):
        env = dict(os.environ,
                   PATH=f"{self.bin}:{os.environ['PATH']}",
                   STUB=self.stub,
                   RETINA_PREFLIGHT_COMPOSE_ROOT=self.root,
                   RETINA_PREFLIGHT_PAYLOAD_FILES=self.payload)
        result = subprocess.run(['/bin/sh', SCRIPT], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stderr

    def calls(self):
        path = os.path.join(self.stub, 'calls')
        if not os.path.exists(path):
            return []
        with open(path) as f:
            return f.read().splitlines()

    def containers(self):
        return sorted(os.listdir(os.path.join(self.stub, 'containers')))

    # --- clean node ---------------------------------------------------------------

    def test_a_clean_node_is_left_alone(self):
        self.write(os.path.join(self.manifests, '.env'), 'RECEIVER_LAT=51.5\n')
        self.container('blah2', 'retina-node')
        self.container('tar1090', 'retina-node')

        stderr = self.run_preflight()

        self.assertEqual(stderr, '')
        self.assertTrue(os.path.exists(os.path.join(self.manifests, '.env')))
        self.assertEqual(self.containers(), ['blah2', 'tar1090'])
        self.assertFalse(any(c.split()[0] in ('update', 'stop', 'rename') for c in self.calls()))

    def test_a_node_with_no_stack_yet_exits_cleanly(self):
        shutil.rmtree(os.path.join(self.root, 'current'))
        self.assertEqual(self.run_preflight(), '')

    # --- .env ---------------------------------------------------------------------

    def test_a_nul_filled_env_is_set_aside(self):
        env = os.path.join(self.manifests, '.env')
        self.write(env, b'\x00' * 208, mode='wb')

        stderr = self.run_preflight()

        self.assertFalse(os.path.exists(env))
        aside = [f for f in os.listdir(self.manifests) if f.startswith('.env.corrupt-')]
        self.assertEqual(len(aside), 1)
        with open(os.path.join(self.manifests, aside[0]), 'rb') as f:
            self.assertEqual(f.read(), b'\x00' * 208)
        self.assertIn('NUL bytes', stderr)

    def test_an_env_compose_cannot_parse_is_set_aside(self):
        env = os.path.join(self.manifests, '.env')
        self.write(env, 'NOT VALID\n')
        self.write(os.path.join(self.stub, 'compose_error'),
                   f'failed to read {env}: line 1: unexpected character " " in variable name\n')

        stderr = self.run_preflight()

        self.assertFalse(os.path.exists(env))
        self.assertIn('compose cannot parse it', stderr)

    def test_an_unrelated_compose_error_leaves_env_alone(self):
        env = os.path.join(self.manifests, '.env')
        self.write(env, 'RECEIVER_LAT=51.5\n')
        self.write(os.path.join(self.stub, 'compose_error'), 'service "x" has neither an image nor a build\n')

        self.run_preflight()

        self.assertTrue(os.path.exists(env))

    # --- stray containers ---------------------------------------------------------

    def test_a_stray_container_on_a_project_name_is_parked(self):
        # Josh Test Node, 2026-09-23: a hand-run blah2:specfold held "blah2".
        self.container('blah2', '')
        self.container('tar1090', 'retina-node')

        stderr = self.run_preflight()

        names = self.containers()
        self.assertIn('tar1090', names)
        self.assertNotIn('blah2', names)
        parked = [n for n in names if n.startswith('blah2-parked-')]
        self.assertEqual(len(parked), 1)
        self.assertIn('update --restart=no blah2', self.calls())
        self.assertIn('stop -t 10 blah2', self.calls())
        self.assertIn('parked container blah2', stderr)

    def test_a_container_from_another_compose_project_is_parked(self):
        self.container('tar1090', 'someone-elses-project')
        self.run_preflight()
        self.assertNotIn('tar1090', self.containers())

    def test_the_projects_own_containers_are_never_touched(self):
        self.container('blah2', 'retina-node')
        self.run_preflight()
        self.assertEqual(self.containers(), ['blah2'])

    def test_names_come_from_the_incoming_manifest_too(self):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode='w') as tar:
            data = b'services:\n  telemetry:\n    container_name: retina-telemetry\n'
            info = tarfile.TarInfo('manifests/docker-compose.yaml')
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        self.write(os.path.join(self.payload, 'manifests.tar'), buf.getvalue(), mode='wb')
        self.container('retina-telemetry', '')

        self.run_preflight()

        self.assertNotIn('retina-telemetry', self.containers())

    def test_a_failed_park_is_reported_and_does_not_abort(self):
        self.container('blah2', '')
        self.write(os.path.join(self.stub, 'rename_fails'), '')

        stderr = self.run_preflight()

        self.assertIn('could not park container blah2', stderr)

    # --- local record -------------------------------------------------------------

    def test_the_local_log_is_capped(self):
        log = os.path.join(self.root, 'preflight.log')
        self.write(log, ''.join(f'old line {i}\n' for i in range(500)))
        self.container('blah2', '')

        self.run_preflight()

        with open(log) as f:
            lines = f.read().splitlines()
        self.assertEqual(len(lines), 200)
        self.assertIn('parked container blah2', lines[-1])


if __name__ == '__main__':
    unittest.main()
