#!/usr/bin/env python3
"""
Tests for merge_config.py in retina-node config-merger

Adapted from blah2-arm tests for the simplified 3-argument version.
"""

import unittest
import tempfile
import shutil
import os
import sys
import yaml

class TestConfigMerge(unittest.TestCase):

    def setUp(self):
        """Create temporary directories for each test"""
        self.test_dir = tempfile.mkdtemp()
        self.defaults_dir = os.path.join(self.test_dir, 'defaults')
        self.config_dir = os.path.join(self.test_dir, 'config')
        os.makedirs(self.defaults_dir)
        os.makedirs(self.config_dir)

    def tearDown(self):
        """Clean up temporary directories"""
        shutil.rmtree(self.test_dir)

    def write_yaml(self, path, data):
        """Helper to write YAML file"""
        with open(path, 'w') as f:
            yaml.dump(data, f)

    def read_yaml(self, path):
        """Helper to read YAML file"""
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def run_merge(self):
        """Run the merge script"""
        import subprocess

        # Find merge_config.py relative to test file
        test_dir = os.path.dirname(__file__)                    # config-merger/test/
        merger_dir = os.path.dirname(test_dir)                  # config-merger/
        script_path = os.path.join(merger_dir, 'script', 'merge_config.py')

        user_yml = os.path.join(self.config_dir, 'user.yml')
        output_yml = os.path.join(self.config_dir, 'config.yml')

        # Note: Only 3 arguments (removed debug_yml parameter)
        result = subprocess.run([
            'python3', script_path,
            self.defaults_dir, user_yml, output_yml
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")

        self.assertEqual(result.returncode, 0, f"Merge script failed: {result.stderr}")

        return output_yml

    def test_defaults_only(self):
        """Test merge with only default.yml"""
        default_config = {
            'process': {'detection': {'pfa': 0.001}},
            'network': {'ip': '0.0.0.0'}
        }
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})

        output_yml = self.run_merge()

        # user.yml should be created
        user_yml = os.path.join(self.config_dir, 'user.yml')
        self.assertTrue(os.path.exists(user_yml))

        # Output should match defaults
        output = self.read_yaml(output_yml)
        self.assertEqual(output['process']['detection']['pfa'], 0.001)
        self.assertEqual(output['network']['ip'], '0.0.0.0')

    def test_user_override(self):
        """Test that user.yml overrides defaults"""
        default_config = {
            'process': {'detection': {'pfa': 0.001, 'minDelay': 5}},
            'network': {'ip': '0.0.0.0'}
        }
        user_config = {
            'process': {'detection': {'pfa': 0.0001}}  # Override pfa only
        }

        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})
        self.write_yaml(os.path.join(self.config_dir, 'user.yml'), user_config)

        output_yml = self.run_merge()
        output = self.read_yaml(output_yml)

        # User override should apply
        self.assertEqual(output['process']['detection']['pfa'], 0.0001)
        # Other defaults should remain
        self.assertEqual(output['process']['detection']['minDelay'], 5)
        self.assertEqual(output['network']['ip'], '0.0.0.0')

    def test_forced_override(self):
        """Test that forced.yml overrides everything"""
        default_config = {
            'process': {'detection': {'pfa': 0.001}},
            'network': {'ip': '0.0.0.0'}
        }
        user_config = {
            'process': {'detection': {'pfa': 0.0001}}
        }
        forced_config = {
            'process': {'detection': {'pfa': 0.00001}}  # Force different value
        }

        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), forced_config)
        self.write_yaml(os.path.join(self.config_dir, 'user.yml'), user_config)

        output_yml = self.run_merge()
        output = self.read_yaml(output_yml)

        # Forced should override user
        self.assertEqual(output['process']['detection']['pfa'], 0.00001)

    def test_deep_merge(self):
        """Test deep merging of nested dictionaries"""
        default_config = {
            'location': {
                'rx': {'latitude': 0, 'longitude': 0, 'altitude': 0},
                'tx': {'latitude': 0, 'longitude': 0, 'altitude': 0}
            }
        }
        user_config = {
            'location': {
                'rx': {'latitude': 37.7749}  # Only override latitude
            }
        }

        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})
        self.write_yaml(os.path.join(self.config_dir, 'user.yml'), user_config)

        output_yml = self.run_merge()
        output = self.read_yaml(output_yml)

        # Deep merge should preserve other values
        self.assertEqual(output['location']['rx']['latitude'], 37.7749)
        self.assertEqual(output['location']['rx']['longitude'], 0)
        self.assertEqual(output['location']['rx']['altitude'], 0)
        self.assertIn('tx', output['location'])

    def test_empty_user_config(self):
        """Test with empty user.yml"""
        default_config = {'process': {'detection': {'pfa': 0.001}}}

        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})
        self.write_yaml(os.path.join(self.config_dir, 'user.yml'), {})

        output_yml = self.run_merge()
        output = self.read_yaml(output_yml)

        # Should just use defaults
        self.assertEqual(output['process']['detection']['pfa'], 0.001)

    def test_missing_forced_config(self):
        """Test that missing forced.yml doesn't break merge"""
        default_config = {'process': {'detection': {'pfa': 0.001}}}

        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        # Don't create forced.yml

        output_yml = self.run_merge()
        output = self.read_yaml(output_yml)

        # Should still work with just defaults
        self.assertEqual(output['process']['detection']['pfa'], 0.001)

    def test_list_replacement_not_merge(self):
        """Test that lists are replaced, not merged"""
        default_config = {
            'list_items': [1, 2, 3],
            'other': 'value'
        }
        user_config = {
            'list_items': [4, 5]
        }

        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})
        self.write_yaml(os.path.join(self.config_dir, 'user.yml'), user_config)

        output_yml = self.run_merge()
        output = self.read_yaml(output_yml)

        # List should be replaced, not merged
        self.assertEqual(output['list_items'], [4, 5])

    def test_tar1090_env_generated(self):
        """Test that tar1090.env is generated when tar1090 config exists"""
        default_config = {
            'process': {'detection': {'pfa': 0.001}},
            'tar1090': {
                'adsblol_fallback': True,
                'adsblol_radius': 50,
                'location': {
                    'latitude': -34.9192,
                    'longitude': 138.6027,
                    'altitude': 110
                }
            }
        }
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})

        self.run_merge()

        # Check tar1090.env was created
        env_path = os.path.join(self.config_dir, 'tar1090.env')
        self.assertTrue(os.path.exists(env_path), "tar1090.env should be generated")

        # Read and verify contents
        with open(env_path, 'r') as f:
            env_content = f.read()

        self.assertIn('RECEIVER_LAT=-34.9192', env_content)
        self.assertIn('RECEIVER_LON=138.6027', env_content)
        self.assertIn('RECEIVER_ALT=110', env_content)
        self.assertIn('ADSBLOL_ENABLED=true', env_content)
        self.assertIn('ADSBLOL_RADIUS=50', env_content)

    def test_tar1090_env_not_generated_without_config(self):
        """Test that tar1090.env is not generated when tar1090 config is missing"""
        default_config = {
            'process': {'detection': {'pfa': 0.001}},
            'network': {'ip': '0.0.0.0'}
        }
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})

        self.run_merge()

        # Check tar1090.env was NOT created
        env_path = os.path.join(self.config_dir, 'tar1090.env')
        self.assertFalse(os.path.exists(env_path), "tar1090.env should not be generated without tar1090 config")

    def test_tar1090_env_adsblol_disabled(self):
        """Test that ADSBLOL_ENABLED is false when adsblol_fallback is false"""
        default_config = {
            'tar1090': {
                'adsblol_fallback': False,
                'adsblol_radius': 40,
                'location': {
                    'latitude': 0,
                    'longitude': 0,
                    'altitude': 0
                }
            }
        }
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})

        self.run_merge()

        env_path = os.path.join(self.config_dir, 'tar1090.env')
        with open(env_path, 'r') as f:
            env_content = f.read()

        self.assertIn('ADSBLOL_ENABLED=false', env_content)

    def test_tar1090_env_user_override(self):
        """Test that user config overrides tar1090 settings in .env"""
        default_config = {
            'tar1090': {
                'adsblol_fallback': True,
                'adsblol_radius': 40,
                'location': {
                    'latitude': 0,
                    'longitude': 0,
                    'altitude': 0
                }
            }
        }
        user_config = {
            'tar1090': {
                'adsblol_radius': 100,
                'location': {
                    'latitude': 51.5074
                }
            }
        }
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})
        self.write_yaml(os.path.join(self.config_dir, 'user.yml'), user_config)

        self.run_merge()

        env_path = os.path.join(self.config_dir, 'tar1090.env')
        with open(env_path, 'r') as f:
            env_content = f.read()

        # User overrides should apply
        self.assertIn('RECEIVER_LAT=51.5074', env_content)
        self.assertIn('ADSBLOL_RADIUS=100', env_content)
        # Defaults should remain for non-overridden values
        self.assertIn('RECEIVER_LON=0', env_content)

    def test_actual_config_files(self):
        """Test merge with actual config files from retina-node repo"""
        import subprocess

        # Use actual config files from repo
        merger_dir = os.path.dirname(os.path.dirname(__file__))  # config-merger/
        repo_root = os.path.dirname(merger_dir)                   # retina-node/
        actual_defaults_dir = os.path.join(repo_root, 'config')

        # Verify config files exist
        default_yml_path = os.path.join(actual_defaults_dir, 'default.yml')
        if not os.path.exists(default_yml_path):
            self.skipTest(f"Actual config file not found: {default_yml_path}")

        # Create test user.yml
        user_yml = os.path.join(self.config_dir, 'user.yml')
        user_config = {'network': {'node_id': 'test-node'}}
        self.write_yaml(user_yml, user_config)

        output_yml = os.path.join(self.config_dir, 'config.yml')

        # Run merge with actual config files
        script_path = os.path.join(merger_dir, 'script', 'merge_config.py')
        result = subprocess.run([
            'python3', script_path,
            actual_defaults_dir, user_yml, output_yml
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")

        self.assertEqual(result.returncode, 0, "Merge with actual configs failed")

        # Verify output is valid YAML and has expected structure
        output = self.read_yaml(output_yml)
        self.assertIn('process', output)
        self.assertIn('network', output)
        self.assertEqual(output['network']['node_id'], 'test-node')

        # Verify tar1090.env was generated
        env_path = os.path.join(self.config_dir, 'tar1090.env')
        self.assertTrue(os.path.exists(env_path), "tar1090.env should be generated with actual config")

        with open(env_path, 'r') as f:
            env_content = f.read()

        # Check expected values from default.yml
        self.assertIn('RECEIVER_LAT=-34.9192', env_content)
        self.assertIn('RECEIVER_LON=138.6027', env_content)
        self.assertIn('RECEIVER_ALT=110', env_content)
        self.assertIn('ADSBLOL_ENABLED=true', env_content)
        self.assertIn('ADSBLOL_RADIUS=40', env_content)

    def test_tar1090_env_with_adsb_source(self):
        """Test that ADSB_SOURCE is included in .env when configured"""
        default_config = {
            'tar1090': {
                'adsb_source': '192.168.8.183,30005,beast_in',
                'adsblol_fallback': True,
                'adsblol_radius': 40,
                'location': {
                    'latitude': -34.9192,
                    'longitude': 138.6027,
                    'altitude': 110
                }
            }
        }
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})

        self.run_merge()

        # Check tar1090.env contains ADSB_SOURCE
        env_path = os.path.join(self.config_dir, 'tar1090.env')
        self.assertTrue(os.path.exists(env_path))

        with open(env_path, 'r') as f:
            env_content = f.read()

        self.assertIn('ADSB_SOURCE=192.168.8.183,30005,beast_in', env_content)

    def test_tar1090_env_without_adsb_source(self):
        """Test that ADSB_SOURCE is omitted when not configured (empty string)"""
        default_config = {
            'tar1090': {
                'adsb_source': '',  # Empty string - should not be included in .env
                'adsblol_fallback': True,
                'adsblol_radius': 40,
                'location': {
                    'latitude': -34.9192,
                    'longitude': 138.6027,
                    'altitude': 110
                }
            }
        }
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})

        self.run_merge()

        # Check tar1090.env does NOT contain ADSB_SOURCE
        env_path = os.path.join(self.config_dir, 'tar1090.env')
        self.assertTrue(os.path.exists(env_path))

        with open(env_path, 'r') as f:
            env_content = f.read()

        self.assertNotIn('ADSB_SOURCE', env_content)

if __name__ == '__main__':
    unittest.main()
