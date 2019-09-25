import uuid
import json

import charms.reactive as reactive

from charms.reactive import hook
from charms.reactive import RelationBase
from charms.reactive import scopes


class NeutronPluginAPISubordinate(RelationBase):
    scope = scopes.GLOBAL

    @hook(
        '{provides:neutron-plugin-api-subordinate}-relation-{joined,changed}')
    def changed(self):
        """Set connected state and assess available state"""
        self.set_state('{relation_name}.connected')
        if self.neutron_api_ready() and not self.db_migration_pending():
            self.set_state('{relation_name}.available')

    @hook(
        '{provides:neutron-plugin-api-subordinate}-relation-{broken,departed}')
    def broken(self):
        """Remove connected state"""
        self.remove_state('{relation_name}.available')
        self.remove_state('{relation_name}.connected')

    @property
    def neutron_config_data(self):
        """Retrive and decode ``neutron_config_data`` from relation"""
        return json.loads(self.get_remote('neutron_config_data', "{}"))

    def neutron_api_ready(self):
        """Assess remote readiness"""
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
        self.set_remote(**relation_info)

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

    def request_db_migration(self):
        """Request principal to perform a DB migration"""
        if not self.neutron_api_ready():
            # Ignore the charm request until we are in a relation-changed hook
            # where the prinicpal charm has declared itself ready.
            return
        nonce = str(uuid.uuid4())
        relation_info = {
            'migrate-database-nonce': nonce,
        }
        self.set_remote(**relation_info)
        # NOTE: we use flags instead of RelationBase state here both because of
        #       easier interaction with charm code, and because of how states
        #       interact with RelationBase conversations leading to crashes
        #       when used prior to relation being fully established.
        reactive.set_flag('{relation_name}.db_migration'
                          .format(relation_name=self.relation_name))
        reactive.set_flag('{relation_name}.db_migration.'
                          .format(relation_name=self.relation_name)+nonce)
        reactive.clear_flag('{relation_name}.available'
                            .format(relation_name=self.relation_name))

    def db_migration_pending(self):
        """Assess presence and state of optional DB migration request"""
        # NOTE: we use flags instead of RelationBase state here both because of
        #       easier interaction with charm code, and because of how states
        #       interact with RelationBase conversations leading to crashes
        #       when used prior to relation being fully established.
        flag_prefix = ('{relation_name}.db_migration'
                       .format(relation_name=self.relation_name))
        if not reactive.is_flag_set(flag_prefix):
            return False
        flag_nonce = '.'.join(
            (flag_prefix,
             self.get_remote('migrate-database-nonce', '')))
        if reactive.is_flag_set(flag_nonce):
            # hooks fire in a nondeterministic order, and there will be
            # occations where a different hook run between the
            # ``migrate-database-nonce`` being set and it being returned to us
            # a subsequent relation-changed hook.
            #
            # to avoid buildup of unreaped db_migration nonce flags we remove
            # all of them each time we have a match for one.
            for flag in reactive.get_flags():
                if flag.startswith(flag_prefix):
                    reactive.clear_flag(flag)
            return False
        return True
