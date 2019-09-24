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
        if self.neutron_api_ready():
            self.set_state('{relation_name}.available')

    @hook(
        '{provides:neutron-plugin-api-subordinate}-relation-{broken,departed}')
    def broken(self):
        """Remove connected state"""
        self.remove_state('{relation_name}.available')
        self.remove_state('{relation_name}.connected')

    @property
    def neutron_config_data(self):
        return json.loads(self.get_remote('neutron_config_data', "{}"))

    def neutron_api_ready(self):
        if self.get_remote('neutron-api-ready') == 'yes':
            return True
        return False

    def configure_plugin(self, neutron_plugin, core_plugin=None,
                         neutron_plugin_config=None, service_plugins=None,
                         subordinate_configuration=None,
                         extension_drivers=None, mechanism_drivers=None,
                         tenant_network_types=None,
                         neutron_security_groups=None):
        """Send principle plugin information

        :param neutron_plugin: Neutron plugin name
        :type neutron_plugin: str
        :param core_plugin: Entry point eg neutron.plugins.ml2.plugin.Ml2Plugin
        :type core_plugin: str
        :param neutron-plugin-config: /etc/neutron/plugins/ml2/ml2_conf.ini
        :type neutron-plugin-config: str
        :param service-plugins: Comma delimited list of service plugins eg
                                router,firewall,lbaas,vpnaas,metering
        :type service-plugins: str
        :param subordinate_configuration: Configuration for the principle
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
        :type subordinate_configuration:
            Dict[str, Dict[
                str Dict[
                    str, List[
                        Union[str, str]]]]]
        :param extension_drivers: Extension drivers eg dns,port_security
        :type extension_drivers: str
        :param mechanism_drivers: Mechanism drivers eg openvswitch,hyperv
        :type mechanism_drivers: str
        :param tenant_network_types: Tenant network types eg local,gre
                                     Note that this also configures
                                     ``type_drivers``
        :type tenant_network_types: str
        :param neutron_security_groups: 'true' to enable security groups
        :type neutron_security_groups: str
        """
        if subordinate_configuration is None:
            subordinate_configuration = {}
        conversation = self.conversation()
        relation_info = {
            'neutron-plugin': neutron_plugin,
            'core-plugin': core_plugin,
            'neutron-plugin-config': neutron_plugin_config,
            'service-plugins': service_plugins,
            'extension-drivers': extension_drivers,
            'mechanism-drivers': mechanism_drivers,
            'tenant-network-types': tenant_network_types,
            'neutron-security-groups': neutron_security_groups,
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
        self.set_remote(**relation_info)
