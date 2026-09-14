#!/usr/bin/env python3
"""
Tests for merge_config.py in retina-node config-merger

Adapted from blah2-arm tests for the simplified 3-argument version.
"""

import os
import shutil
import tempfile
import unittest

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
        with open(path) as f:
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
        with open(env_path) as f:
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
        with open(env_path) as f:
            env_content = f.read()

        self.assertIn('ADSBLOL_ENABLED=false', env_content)

    def test_tar1090_env_omits_an_unset_location(self):
        """This used to write RECEIVER_LAT=0, which is Null Island: a real
        place the node then claimed to be."""
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), {
            'tar1090': {'adsblol_fallback': True, 'adsblol_radius': 40},
            'location': {'rx': {'latitude': None, 'longitude': None,
                                'altitude': None, 'name': None}},
        })
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})

        self.run_merge()

        with open(os.path.join(self.config_dir, 'tar1090.env')) as f:
            env_content = f.read()

        self.assertNotIn('RECEIVER_LAT=', env_content)
        # The adsb.lol query is a radius around the receiver. With no receiver
        # there is no query to make, only a wrong one feeding blah2 false truth.
        self.assertIn('ADSBLOL_ENABLED=false', env_content)

    def test_tar1090_env_partial_location_is_not_sited(self):
        """A latitude with no longitude is not a position."""
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), {
            'tar1090': {'adsblol_fallback': True, 'adsblol_radius': 40},
            'location': {'rx': {'latitude': 42.241528, 'longitude': None}},
        })
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})

        self.run_merge()

        with open(os.path.join(self.config_dir, 'tar1090.env')) as f:
            env_content = f.read()

        self.assertNotIn('RECEIVER_LAT=', env_content)
        self.assertIn('ADSBLOL_ENABLED=false', env_content)

    def test_tar1090_env_returns_once_the_owner_sets_a_location(self):
        """The unset case must not be sticky."""
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), {
            'tar1090': {'adsblol_fallback': True, 'adsblol_radius': 40},
            'location': {'rx': {'latitude': None, 'longitude': None, 'altitude': None}},
        })
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})
        self.write_yaml(os.path.join(self.config_dir, 'user.yml'), {
            'location': {'rx': {'latitude': 42.241528, 'longitude': -72.648361,
                                'altitude': 619.2, 'name': 'ret4c844c20'}}
        })

        self.run_merge()

        with open(os.path.join(self.config_dir, 'tar1090.env')) as f:
            env_content = f.read()

        self.assertIn('RECEIVER_LAT=42.241528', env_content)
        self.assertIn('ADSBLOL_ENABLED=true', env_content)

    def test_tar1090_env_zero_is_a_real_location(self):
        """0,0 set by an owner is a choice, not an absence."""
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), {
            'tar1090': {'adsblol_fallback': True, 'adsblol_radius': 40},
            'location': {'rx': {'latitude': 0, 'longitude': 0, 'altitude': 0}},
        })
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})

        self.run_merge()

        with open(os.path.join(self.config_dir, 'tar1090.env')) as f:
            env_content = f.read()

        self.assertIn('RECEIVER_LAT=0', env_content)
        self.assertIn('ADSBLOL_ENABLED=true', env_content)

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
        with open(env_path) as f:
            env_content = f.read()

        # User overrides should apply
        self.assertIn('RECEIVER_LAT=51.5074', env_content)
        self.assertIn('ADSBLOL_RADIUS=100', env_content)
        # Defaults should remain for non-overridden values
        self.assertIn('RECEIVER_LON=0', env_content)

    def test_legacy_scalar_gain_reduction_migrated(self):
        """Test that a legacy scalar gainReduction from user.yml is migrated to a per-tuner pair"""
        default_config = {
            'capture': {'device': {'gainReduction': [40, 40]}}
        }
        user_config = {
            'capture': {'device': {'gainReduction': 30}}  # legacy scalar override
        }

        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})
        self.write_yaml(os.path.join(self.config_dir, 'user.yml'), user_config)

        output_yml = self.run_merge()
        output = self.read_yaml(output_yml)

        self.assertEqual(output['capture']['device']['gainReduction'], [30, 30])

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

        # Verify retina-tracker.yaml was generated
        tracker_yaml_path = os.path.join(self.config_dir, 'retina-tracker.yaml')
        self.assertTrue(os.path.exists(tracker_yaml_path),
                         "retina-tracker.yaml should be generated with actual config")

        # Verify tar1090.env was generated
        env_path = os.path.join(self.config_dir, 'tar1090.env')
        self.assertTrue(os.path.exists(env_path), "tar1090.env should be generated with actual config")

        with open(env_path) as f:
            env_content = f.read()

        # Read the expected values from default.yml rather than duplicating
        # them. This test's purpose is that the merger propagates the real
        # config into tar1090.env — not that the config holds any particular
        # site. Hardcoding them meant 64ff0c9, which deliberately replaced the
        # site-specific defaults with generic placeholders, silently broke this.
        defaults = self.read_yaml(default_yml_path)
        rx = defaults['location']['rx']
        tar1090 = defaults.get('tar1090', {})

        sited = rx.get('latitude') is not None and rx.get('longitude') is not None

        if sited:
            self.assertIn(f"RECEIVER_LAT={rx['latitude']}", env_content)
            self.assertIn(f"RECEIVER_LON={rx['longitude']}", env_content)
            self.assertIn(f"RECEIVER_ALT={rx['altitude']}", env_content)
        else:
            # The shipped default carries no location on purpose, so a node
            # nobody has configured must not name a position at all.
            self.assertNotIn("RECEIVER_LAT=", env_content)
            self.assertNotIn("RECEIVER_LON=", env_content)

        self.assertIn(
            f"ADSBLOL_ENABLED={'true' if tar1090.get('adsblol_fallback') and sited else 'false'}",
            env_content,
        )
        self.assertIn(f"ADSBLOL_RADIUS={tar1090['adsblol_radius']}", env_content)

    def test_tar1090_env_with_adsb_source(self):
        """Test that READSB_NET_CONNECTOR is included in .env when configured"""
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

        # Check tar1090.env contains READSB_NET_CONNECTOR
        env_path = os.path.join(self.config_dir, 'tar1090.env')
        self.assertTrue(os.path.exists(env_path))

        with open(env_path) as f:
            env_content = f.read()

        self.assertIn('READSB_NET_CONNECTOR=192.168.8.183,30005,beast_in', env_content)

    def test_tar1090_env_without_adsb_source(self):
        """Test that READSB_NET_CONNECTOR is omitted when not configured (empty string)"""
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

        # Check tar1090.env does NOT contain READSB_NET_CONNECTOR
        env_path = os.path.join(self.config_dir, 'tar1090.env')
        self.assertTrue(os.path.exists(env_path))

        with open(env_path) as f:
            env_content = f.read()

        self.assertNotIn('READSB_NET_CONNECTOR', env_content)

    def test_tar1090_env_uses_location_rx(self):
        """Test that tar1090 uses location.rx for receiver position"""
        default_config = {
            'location': {
                'rx': {
                    'latitude': 37.7644,
                    'longitude': -122.3954,
                    'altitude': 23
                }
            },
            'tar1090': {
                'adsblol_fallback': True,
                'adsblol_radius': 40
            }
        }
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})

        self.run_merge()

        env_path = os.path.join(self.config_dir, 'tar1090.env')
        with open(env_path) as f:
            env_content = f.read()

        # Should use location.rx values
        self.assertIn('RECEIVER_LAT=37.7644', env_content)
        self.assertIn('RECEIVER_LON=-122.3954', env_content)
        self.assertIn('RECEIVER_ALT=23', env_content)

    def test_retina_tracker_yaml_generated(self):
        """Test that retina-tracker.yaml is generated when retina_tracker config exists"""
        default_config = {
            'process': {'detection': {'pfa': 0.001}},
            'retina_tracker': {'min_snr': 7.0},
        }
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})

        self.run_merge()

        tracker_yaml_path = os.path.join(self.config_dir, 'retina-tracker.yaml')
        self.assertTrue(os.path.exists(tracker_yaml_path), "retina-tracker.yaml should be generated")

        output = self.read_yaml(tracker_yaml_path)
        self.assertEqual(output, {'tracker': {'min_snr': 7.0}})

    def test_retina_tracker_yaml_not_generated_without_config(self):
        """Test that retina-tracker.yaml is not generated when retina_tracker config is missing"""
        default_config = {
            'process': {'detection': {'pfa': 0.001}},
            'network': {'ip': '0.0.0.0'},
        }
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})

        self.run_merge()

        tracker_yaml_path = os.path.join(self.config_dir, 'retina-tracker.yaml')
        self.assertFalse(os.path.exists(tracker_yaml_path),
                          "retina-tracker.yaml should not be generated without retina_tracker config")

    def test_retina_tracker_yaml_user_override(self):
        """Test that user config overrides retina_tracker settings in retina-tracker.yaml"""
        default_config = {
            'retina_tracker': {'min_snr': 7.0},
        }
        user_config = {
            'retina_tracker': {'min_snr': 4.5},
        }
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), default_config)
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})
        self.write_yaml(os.path.join(self.config_dir, 'user.yml'), user_config)

        self.run_merge()

        tracker_yaml_path = os.path.join(self.config_dir, 'retina-tracker.yaml')
        output = self.read_yaml(tracker_yaml_path)
        self.assertEqual(output['tracker']['min_snr'], 4.5)


    # --- Doppler span migration -------------------------------------------
    # The merger seeds user.yml from default.yml on first boot, so every node
    # persists the shipped span. These cover which of those persisted values
    # the merger is allowed to move.

    def default_with_span(self, doppler_min=-300, doppler_max=300):
        """A default.yml carrying the shipped ambiguity block."""
        return {
            'process': {
                'ambiguity': {
                    'delayMin': -10,
                    'delayMax': 400,
                    'dopplerMin': doppler_min,
                    'dopplerMax': doppler_max,
                }
            }
        }

    def write_span_configs(self, user_ambiguity, forced_config=None):
        """Write a default/user/forced set differing only in the ambiguity block."""
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), self.default_with_span())
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), forced_config or {})
        self.write_yaml(os.path.join(self.config_dir, 'user.yml'),
                        {'process': {'ambiguity': user_ambiguity}})

    def test_doppler_span_first_boot_copy_migrated(self):
        """A user.yml holding the old shipped span gives way to the new default"""
        self.write_span_configs({'delayMin': -10, 'delayMax': 400,
                                 'dopplerMin': -200, 'dopplerMax': 200})

        output = self.read_yaml(self.run_merge())
        ambiguity = output['process']['ambiguity']

        self.assertEqual(ambiguity['dopplerMin'], -300)
        self.assertEqual(ambiguity['dopplerMax'], 300)
        # Only the Doppler bounds move; the rest of the block is the user's.
        self.assertEqual(ambiguity['delayMin'], -10)
        self.assertEqual(ambiguity['delayMax'], 400)

    def test_doppler_span_deliberate_override_kept(self):
        """A span nobody could have got from a first-boot copy survives"""
        self.write_span_configs({'dopplerMin': -1000, 'dopplerMax': 1000})

        output = self.read_yaml(self.run_merge())

        self.assertEqual(output['process']['ambiguity']['dopplerMin'], -1000)
        self.assertEqual(output['process']['ambiguity']['dopplerMax'], 1000)

    def test_doppler_span_partial_legacy_match_kept(self):
        """One legacy bound is not the legacy pair, so neither bound moves"""
        self.write_span_configs({'dopplerMin': -200, 'dopplerMax': 1000})

        output = self.read_yaml(self.run_merge())

        self.assertEqual(output['process']['ambiguity']['dopplerMin'], -200)
        self.assertEqual(output['process']['ambiguity']['dopplerMax'], 1000)

    def test_doppler_span_asymmetric_legacy_value_kept(self):
        """An asymmetric span that happens to touch 200 is still deliberate"""
        self.write_span_configs({'dopplerMin': -200, 'dopplerMax': 400})

        output = self.read_yaml(self.run_merge())

        self.assertEqual(output['process']['ambiguity']['dopplerMin'], -200)
        self.assertEqual(output['process']['ambiguity']['dopplerMax'], 400)

    def test_doppler_span_forced_still_wins(self):
        """forced.yml keeps the last word over a migrated span"""
        self.write_span_configs(
            {'dopplerMin': -200, 'dopplerMax': 200},
            forced_config={'process': {'ambiguity': {'dopplerMin': -250, 'dopplerMax': 250}}},
        )

        output = self.read_yaml(self.run_merge())

        self.assertEqual(output['process']['ambiguity']['dopplerMin'], -250)
        self.assertEqual(output['process']['ambiguity']['dopplerMax'], 250)

    def test_doppler_span_migration_does_not_rewrite_user_yml(self):
        """The overlay on disk is untouched, so the migration has to stay in place"""
        self.write_span_configs({'dopplerMin': -200, 'dopplerMax': 200})

        self.run_merge()

        user = self.read_yaml(os.path.join(self.config_dir, 'user.yml'))
        self.assertEqual(user['process']['ambiguity']['dopplerMin'], -200)
        self.assertEqual(user['process']['ambiguity']['dopplerMax'], 200)

    def test_doppler_span_absent_from_user_config(self):
        """A user.yml with no ambiguity block just takes the default"""
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), self.default_with_span())
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), {})
        self.write_yaml(os.path.join(self.config_dir, 'user.yml'),
                        {'network': {'node_id': 'test-node'}})

        output = self.read_yaml(self.run_merge())

        self.assertEqual(output['process']['ambiguity']['dopplerMin'], -300)
        self.assertEqual(output['process']['ambiguity']['dopplerMax'], 300)

    # --- tracker_forward migration ----------------------------------------
    # Same first-boot-copy problem as the Doppler span: every node persists the
    # block that shipped when it booted, so default.yml alone cannot move it.

    def default_with_forward(self, enabled=True, host='127.0.0.1', port=30100):
        """A default.yml carrying the shipped tracker_forward block."""
        return {
            'network': {
                'ip': '0.0.0.0',
                'ports': {'api': 3000},
                'tracker_forward': {'enabled': enabled, 'host': host, 'port': port},
            }
        }

    def write_forward_configs(self, user_network, forced_config=None):
        """Write a default/user/forced set differing only in the network block."""
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), self.default_with_forward())
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), forced_config or {})
        self.write_yaml(os.path.join(self.config_dir, 'user.yml'), {'network': user_network})

    def test_tracker_forward_first_boot_copy_migrated(self):
        """The block that shipped with gui-side forwarding gives way to the default"""
        self.write_forward_configs(
            {'node_id': 'test-node',
             'tracker_forward': {'enabled': False, 'host': 'blah2_tracker', 'port': 3012}})

        forward = self.read_yaml(self.run_merge())['network']['tracker_forward']

        self.assertTrue(forward['enabled'])
        self.assertEqual(forward['host'], '127.0.0.1')
        self.assertEqual(forward['port'], 30100)

    def test_tracker_forward_migration_leaves_the_rest_of_network_alone(self):
        """Only the forwarding block moves; everything else is still the user's"""
        self.write_forward_configs(
            {'node_id': 'ret7dd2cb0d', 'ip': '10.0.0.1',
             'tracker_forward': {'enabled': False, 'host': 'blah2_tracker', 'port': 3012}})

        network = self.read_yaml(self.run_merge())['network']

        self.assertEqual(network['node_id'], 'ret7dd2cb0d')
        self.assertEqual(network['ip'], '10.0.0.1')

    def test_tracker_forward_deliberate_target_kept(self):
        """A node aimed somewhere real is a choice, not a first-boot copy"""
        self.write_forward_configs(
            {'tracker_forward': {'enabled': True, 'host': '192.168.0.9', 'port': 9999}})

        forward = self.read_yaml(self.run_merge())['network']['tracker_forward']

        self.assertEqual(forward['host'], '192.168.0.9')
        self.assertEqual(forward['port'], 9999)

    def test_tracker_forward_deliberately_disabled_elsewhere_kept(self):
        """Disabled is only a fossil alongside the rest of the legacy triple"""
        self.write_forward_configs(
            {'tracker_forward': {'enabled': False, 'host': '127.0.0.1', 'port': 30100}})

        forward = self.read_yaml(self.run_merge())['network']['tracker_forward']

        self.assertFalse(forward['enabled'])

    def test_tracker_forward_partial_legacy_match_kept(self):
        """The legacy host on a different port is not the block we shipped"""
        self.write_forward_configs(
            {'tracker_forward': {'enabled': False, 'host': 'blah2_tracker', 'port': 3013}})

        forward = self.read_yaml(self.run_merge())['network']['tracker_forward']

        self.assertFalse(forward['enabled'])
        self.assertEqual(forward['port'], 3013)

    def test_tracker_forward_extra_key_is_not_the_shipped_block(self):
        """Anything added by hand makes it someone's config rather than a copy"""
        self.write_forward_configs(
            {'tracker_forward': {'enabled': False, 'host': 'blah2_tracker',
                                 'port': 3012, 'note': 'left off on purpose'}})

        forward = self.read_yaml(self.run_merge())['network']['tracker_forward']

        self.assertFalse(forward['enabled'])
        self.assertEqual(forward['note'], 'left off on purpose')

    def test_tracker_forward_forced_still_wins(self):
        """forced.yml keeps the last word over a migrated block"""
        self.write_forward_configs(
            {'tracker_forward': {'enabled': False, 'host': 'blah2_tracker', 'port': 3012}},
            forced_config={'network': {'tracker_forward': {'enabled': False}}},
        )

        forward = self.read_yaml(self.run_merge())['network']['tracker_forward']

        self.assertFalse(forward['enabled'])

    def test_tracker_forward_migration_does_not_rewrite_user_yml(self):
        """The overlay on disk is untouched, so the migration has to stay in place"""
        self.write_forward_configs(
            {'tracker_forward': {'enabled': False, 'host': 'blah2_tracker', 'port': 3012}})

        self.run_merge()

        user = self.read_yaml(os.path.join(self.config_dir, 'user.yml'))
        self.assertEqual(user['network']['tracker_forward'],
                         {'enabled': False, 'host': 'blah2_tracker', 'port': 3012})

    def test_tracker_forward_absent_from_user_config(self):
        """A user.yml with no forwarding block just takes the default"""
        self.write_forward_configs({'node_id': 'test-node'})

        forward = self.read_yaml(self.run_merge())['network']['tracker_forward']

        self.assertTrue(forward['enabled'])
        self.assertEqual(forward['port'], 30100)

    # --- ADS-B truth server migration -------------------------------------
    # Same first-boot-copy problem again: the shipped truth server persists in
    # every overlay, so default.yml alone cannot move a node off a dead host.

    def default_with_truth(self, tar1090='localhost:8078'):
        """A default.yml carrying the shipped ADS-B truth block."""
        return {
            'truth': {
                'adsb': {
                    'enabled': True,
                    'tar1090': tar1090,
                    'adsb2dd': 'localhost:49155',
                }
            }
        }

    def write_truth_configs(self, user_adsb, forced_config=None):
        """Write a default/user/forced set differing only in the truth block."""
        self.write_yaml(os.path.join(self.defaults_dir, 'default.yml'), self.default_with_truth())
        self.write_yaml(os.path.join(self.defaults_dir, 'forced.yml'), forced_config or {})
        self.write_yaml(os.path.join(self.config_dir, 'user.yml'), {'truth': {'adsb': user_adsb}})

    def test_adsb_truth_first_boot_copy_migrated(self):
        """The remote host that shipped gives way to the node's own tar1090"""
        self.write_truth_configs({'enabled': True, 'tar1090': 'sfo1.retnode.com'})

        adsb = self.read_yaml(self.run_merge())['truth']['adsb']

        self.assertEqual(adsb['tar1090'], 'localhost:8078')

    def test_adsb_truth_migration_leaves_the_rest_of_adsb_alone(self):
        """Only the truth server moves; every other setting is still the user's"""
        self.write_truth_configs(
            {'enabled': True, 'tar1090': 'sfo1.retnode.com',
             'adsb2dd': 'localhost:49155', 'delay_tolerance': 4.5})

        adsb = self.read_yaml(self.run_merge())['truth']['adsb']

        self.assertEqual(adsb['tar1090'], 'localhost:8078')
        self.assertEqual(adsb['delay_tolerance'], 4.5)

    def test_adsb_truth_deliberate_server_kept(self):
        """A node aimed at some other host is a choice, not a first-boot copy"""
        self.write_truth_configs({'tar1090': 'adsb.example.internal:8080'})

        adsb = self.read_yaml(self.run_merge())['truth']['adsb']

        self.assertEqual(adsb['tar1090'], 'adsb.example.internal:8080')

    def test_adsb_truth_receiver_address_kept(self):
        """A receiver's own address is wrong differently, and not ours to rewrite"""
        self.write_truth_configs({'tar1090': '192.168.1.143:30005'})

        adsb = self.read_yaml(self.run_merge())['truth']['adsb']

        self.assertEqual(adsb['tar1090'], '192.168.1.143:30005')

    def test_adsb_truth_legacy_host_with_a_port_kept(self):
        """The legacy host named with a port is not the string we shipped"""
        self.write_truth_configs({'tar1090': 'sfo1.retnode.com:8078'})

        adsb = self.read_yaml(self.run_merge())['truth']['adsb']

        self.assertEqual(adsb['tar1090'], 'sfo1.retnode.com:8078')

    def test_adsb_truth_forced_still_wins(self):
        """forced.yml keeps the last word over a migrated truth server"""
        self.write_truth_configs(
            {'tar1090': 'sfo1.retnode.com'},
            forced_config={'truth': {'adsb': {'tar1090': 'forced.example:8078'}}},
        )

        adsb = self.read_yaml(self.run_merge())['truth']['adsb']

        self.assertEqual(adsb['tar1090'], 'forced.example:8078')

    def test_adsb_truth_migration_does_not_rewrite_user_yml(self):
        """The overlay on disk is untouched, so the migration has to stay in place"""
        self.write_truth_configs({'tar1090': 'sfo1.retnode.com'})

        self.run_merge()

        user = self.read_yaml(os.path.join(self.config_dir, 'user.yml'))
        self.assertEqual(user['truth']['adsb']['tar1090'], 'sfo1.retnode.com')

    def test_adsb_truth_absent_from_user_config(self):
        """A user.yml with no truth server just takes the default"""
        self.write_truth_configs({'enabled': True})

        adsb = self.read_yaml(self.run_merge())['truth']['adsb']

        self.assertEqual(adsb['tar1090'], 'localhost:8078')


if __name__ == '__main__':
    unittest.main()
