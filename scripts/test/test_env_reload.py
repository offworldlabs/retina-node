#!/usr/bin/env python3
"""
Tests for the ArtifactCommit_Leave_10_retina_env_reload Mender state script.

It runs after every retina-node install is committed, so each test runs the
real script under /bin/sh with a stub `docker` that records the directory and
arguments of every call.
"""

import os
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'mender-state-scripts', 'ArtifactCommit_Leave_10_retina_env_reload')

STUB_DOCKER = r'''#!/bin/sh
echo "$(pwd) | $*" >> "$STUB/calls"
if [ -f "$STUB/compose_fails" ]; then echo "Error response from daemon: boom" >&2; exit 1; fi
exit 0
'''


class TestEnvReload(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.stub = os.path.join(self.dir, 'stub')
        self.bin = os.path.join(self.dir, 'bin')
        self.root = os.path.join(self.dir, 'mender-docker-compose')
        self.manifests = os.path.join(self.root, 'current', 'manifests')
        for d in (self.stub, self.bin, self.manifests):
            os.makedirs(d)
        docker = os.path.join(self.bin, 'docker')
        with open(docker, 'w') as f:
            f.write(STUB_DOCKER)
        os.chmod(docker, 0o755)

    def tearDown(self):
        shutil.rmtree(self.dir)

    def run_reload(self):
        env = dict(os.environ,
                   PATH=f"{self.bin}:{os.environ['PATH']}",
                   STUB=self.stub,
                   RETINA_ENV_RELOAD_COMPOSE_ROOT=self.root)
        result = subprocess.run(['/bin/sh', SCRIPT], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stderr

    def calls(self):
        path = os.path.join(self.stub, 'calls')
        if not os.path.exists(path):
            return []
        with open(path) as f:
            return f.read().splitlines()

    def write_env(self):
        with open(os.path.join(self.manifests, '.env'), 'w') as f:
            f.write('RECEIVER_LAT=51.5\n')

    def test_recreates_only_tar1090_from_the_committed_manifests(self):
        self.write_env()

        stderr = self.run_reload()

        self.assertEqual(self.calls(),
                         [f'{os.path.realpath(self.manifests)} | compose -p retina-node up -d --no-deps tar1090'])
        self.assertIn('tar1090 matches', stderr)

    def test_does_nothing_without_an_env(self):
        # Recreating tar1090 would only apply the same defaults again.
        stderr = self.run_reload()

        self.assertEqual(self.calls(), [])
        self.assertIn('no ', stderr)

    def test_does_nothing_without_a_committed_composition(self):
        shutil.rmtree(os.path.join(self.root, 'current'))
        self.run_reload()
        self.assertEqual(self.calls(), [])

    def test_a_compose_failure_is_reported_and_does_not_fail_the_deployment(self):
        self.write_env()
        open(os.path.join(self.stub, 'compose_fails'), 'w').close()

        stderr = self.run_reload()

        self.assertIn('could not update tar1090', stderr)
        self.assertIn('boom', stderr)


if __name__ == '__main__':
    unittest.main()
