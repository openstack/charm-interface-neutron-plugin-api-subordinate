import uuid
import json

from charms.reactive import hook
from charms.reactive import RelationBase
from charms.reactive import scopes


class NeutronPluginAPISubordinate(RelationBase):
    scope = scopes.GLOBAL

    @hook(
        '{provides:neutron-plugin-api-subordinate}-relation-{joined,changed}')
    def changed(self):
        """Set connected state"""
        self.set_state('{relation_name}.connected')

    @hook(
        '{provides:neutron-plugin-api-subordinate}-relation-{broken,departed}')
    def broken(self):
        """Remove connected state"""
        self.remove_state('{relation_name}.connected')

    def configure_plugin(self, neutron_plugin=None, core_plugin=None,
                         neutron_plugin_config=None, service_plugins=None,
                         subordinate_configuration=None):
        """Send principle plugin information

        :param neutron_plugin: str Neutron plugin name eg odl
        :param core_plugin: str eg neutron.plugins.ml2.plugin.Ml2Plugin
        :param neutron-plugin-config: str /etc/neutron/plugins/ml2/ml2_conf.ini
        :param service-plugins str: Comma delimited list of service plugins eg
                                    router,firewall,lbaas,vpnaas,metering
        :param subordinate_configuration dict: Configuration for the principle
                                               to inject into a configuration
                                               file it is managing eg:
        # Add sections and tuples to insert values into neutron-server's
        # neutron.conf e.g.
        # {
        #     "neutron-api": {
        #        "/etc/neutron/neutron.conf": {
        #             "sections": {
        #                 'DEFAULT': [
        #                     ('key1', 'val1')
        #                     ('key2', 'val2')
        #                 ],
        #                 'agent': [
        #                     ('key3', 'val3')
        #                 ],
        #             }
        #         }
        #     }
        # }
        """
        conversation = self.conversation()
        relation_info = {
            'neutron-plugin': neutron_plugin,
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
