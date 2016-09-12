import uuid
import json

from charms.reactive import hook
from charms.reactive import RelationBase
from charms.reactive import scopes


class NeutronPluginAPISubordinate(RelationBase):
    scope = scopes.GLOBAL

    @hook('{provides:neutron-plugin-api-subordinate}-relation-{joined,changed}')
    def changed(self):
        self.set_state('{relation_name}.connected')

    @hook('{provides:neutron-plugin-api-subordinate}-relation-{broken,departed}')
    def broken(self):
        self.remove_state('{relation_name}.connected')

    def configure_plugin(self, plugin=None, core_plugin=None,
                         neutron_plugin_config=None, service_plugins=None,
                         subordinate_configuration=None):
        conversation = self.conversation()
        relation_info = {
            'neutron-plugin': plugin,
            'core-plugin': core_plugin,
            'neutron-plugin-config': neutron_plugin_config,
            'service-plugins': service_plugins,
            'subordinate_configuration': json.dumps(subordinate_configuration),
        }
        conversation.set_remote(**relation_info)

    def request_restart(self, service_type=None):
        """Request a restart of a set of remote services

        :param service_type: string Service types to be restarted eg 'neutron'.
                                    If ommitted a request to restart all
                                    services is sent
        """
        if service_type:
            key = 'restart-trigger-{}'.format(service_type)
        else:
            key = 'restart-trigger'
        relation_info = {
            key: str(uuid.uuid4()),
        }
        print(relation_info)
        self.set_remote(**relation_info)
