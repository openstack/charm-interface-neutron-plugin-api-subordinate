# Copyright 2019 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import mock

import charms_openstack.test_utils as test_utils

import provides


_hook_args = {}


def mock_hook(*args, **kwargs):

    def inner(f):
        # remember what we were passed.  Note that we can't actually determine
        # the class we're attached to, as the decorator only gets the function.
        _hook_args[f.__name__] = dict(args=args, kwargs=kwargs)
        return f
    return inner


class TestNeutronPluginApiSubordinateProvides(test_utils.PatchHelper):

    @classmethod
    def setUpClass(cls):
        cls._patched_hook = mock.patch('charms.reactive.hook', mock_hook)
        cls._patched_hook_started = cls._patched_hook.start()
        # force providesto rerun the mock_hook decorator:
        # try except is Python2/Python3 compatibility as Python3 has moved
        # reload to importlib.
        try:
            reload(provides)
        except NameError:
            import importlib
            importlib.reload(provides)

    @classmethod
    def tearDownClass(cls):
        cls._patched_hook.stop()
        cls._patched_hook_started = None
        cls._patched_hook = None
        # and fix any breakage we did to the module
        try:
            reload(provides)
        except NameError:
            import importlib
            importlib.reload(provides)

    def setUp(self):
        self._patches = {}
        self._patches_start = {}
        conversation = mock.MagicMock()
        self.target = provides.NeutronPluginAPISubordinate(
            'some-relation', [conversation])

    def tearDown(self):
        self.target = None
        for k, v in self._patches.items():
            v.stop()
            setattr(self, k, None)
        self._patches = None
        self._patches_start = None

    def patch_target(self, attr, return_value=None):
        mocked = mock.patch.object(self.target, attr)
        self._patches[attr] = mocked
        started = mocked.start()
        started.return_value = return_value
        self._patches_start[attr] = started
        setattr(self, attr, started)

    def patch_topublish(self):
        self.patch_target('_relations')
        relation = mock.MagicMock()
        to_publish = mock.PropertyMock()
        type(relation).to_publish = to_publish
        self._relations.__iter__.return_value = [relation]
        return relation.to_publish

    def test_registered_hooks(self):
        # test that the hooks actually registered the relation expressions that
        # are meaningful for this interface: this is to handle regressions.
        # The keys are the function names that the hook attaches to.
        hook_patterns = {
            'changed': (
                '{provides:neutron-plugin-api-subordinate}-'
                'relation-{joined,changed}', ),
            'broken': (
                '{provides:neutron-plugin-api-subordinate}-'
                'relation-{broken,departed}', ),
        }
        for k, v in _hook_args.items():
            self.assertEqual(hook_patterns[k], v['args'])

    def test_changed(self):
        conversation = mock.MagicMock()
        self.patch_target('conversation', conversation)
        self.patch_target('set_state')
        self.patch_target('get_remote')
        self.get_remote.return_value = None
        self.target.changed()
        self.set_state.assert_called_once_with('{relation_name}.connected')
        self.set_state.reset_mock()
        self.get_remote.return_value = 'yes'
        self.target.changed()
        self.set_state.assert_has_calls([
            mock.call('{relation_name}.connected'),
            mock.call('{relation_name}.available'),
        ])

    def test_broken(self):
        conversation = mock.MagicMock()
        self.patch_target('conversation', conversation)
        self.patch_target('remove_state')
        self.target.broken()
        self.remove_state.assert_has_calls([
            mock.call('{relation_name}.available'),
            mock.call('{relation_name}.connected'),
        ])

    def test_neutron_api_ready(self):
        self.patch_target('get_remote')
        self.get_remote.return_value = 'yes'
        self.assertTrue(self.target.neutron_api_ready())
        self.get_remote.return_value = None
        self.assertFalse(self.target.neutron_api_ready())

    def teat_neutron_config_data(self):
        self.patch_target('get_remote')
        self.get_remote = json.dumps({'k': 'v'})
        self.assertEquals(self.target.neutron_config_data, {'k': 'v'})

    def test_configure_plugin(self):
        conversation = mock.MagicMock()
        self.patch_target('conversation', conversation)
        self.target.configure_plugin('aPlugin',
                                     'aCorePlugin',
                                     'aNeutronPluginConfig',
                                     'servicePlugins1,servicePlugin2',
                                     {'aKey': 'aValue'},
                                     'extensionDriver1,extensionDriver2',
                                     'mechanismDriver1,mechanismDriver2',
                                     'typeDriver1,typeDriver2',
                                     'toggleSecurityGroups',
                                     )
        conversation.set_remote.assert_called_once_with(
            **{
                'core-plugin': 'aCorePlugin',
                'neutron-plugin': 'aPlugin',
                'neutron-plugin-config': 'aNeutronPluginConfig',
                'service-plugins': 'servicePlugins1,servicePlugin2',
                'extension-drivers': 'extensionDriver1,extensionDriver2',
                'mechanism-drivers': 'mechanismDriver1,mechanismDriver2',
                'tenant-network-types': 'typeDriver1,typeDriver2',
                'neutron-security-groups': 'toggleSecurityGroups',
                'subordinate_configuration': json.dumps({'aKey': 'aValue'})},
        )

    def test_request_restart(self):
        conversation = mock.MagicMock()
        self.patch_target('conversation', conversation)
        self.patch_object(provides.uuid, 'uuid4')
        self.uuid4.return_value = 'fake-uuid'
        self.target.request_restart()
        conversation.set_remote.assert_called_once_with(
            None, None, None, **{'restart-trigger': 'fake-uuid'},
        )
        conversation.set_remote.reset_mock()
        self.target.request_restart('aServiceType')
        conversation.set_remote.assert_called_once_with(
            None, None, None, **{'restart-trigger-aServiceType': 'fake-uuid'},
        )
