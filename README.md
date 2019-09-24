# Overview

This interface is used for a charm to send configuration information to the
neutron-api principle charm and request a restart of a service managed by
that charm.

# Usage

## Flags and States
The interface provides the `{relation-name}.connected` and
`{relation_name}.available` flags and states.

## neutron\_config\_data

The neutron\_config\_data property allows the charm author to introspect a
subset of the principle charm context values prior to applying the context
provided by this relation.

This enables the subordinate charm to make informed decisions about how it
should configure Neutron based on how the deployment is configured.

```python
@reactive.when('neutron-plugin-api-subordinate.connected')
def configure_principle():
    api_principle = reactive.endpoint_from_flag(
        'neutron-plugin-api-subordinate.connected')
    if 'dns' in api_principle.neutron_config_data['extension_drivers']:
        ...

## configure\_plugin

The configure\_plugin method allows the following to be configured in the
principle charm:

* **neutron\_plugin**: Name of the plugin type eg 'ovs', 'ovn' etc. This is not
                       currently used in the principle but should be set to
                       something representitve of the plugin type.
* **core\_plugin**:    Value of core\_plugin to be set in neutron.conf
* **neutron\_plugin\_config**: File containing plugin config. This config file
                               is appended to the list of configs the neutron
                               services read on startup.
* **service\_plugins**: Value of service\_plugins to be set in neutron.conf
* **subordinate\_configuration**: Config to be inserted into a configuration
                                  file that the principle manages.
* **extension\_drivers**: Value of extension\_drivers to be set in
                          ml2\_conf.ini
* **neutron\_security\_groups**: Toggle whether the Neutron security group
                                 feature should be enabled or not.

Request `foo = bar` is inserted into the `DEFAULT` section of neutron.conf

```python
@reactive.when('neutron-plugin-api-subordinate.connected')
def configure_principle(api_principle):
    ...
    inject_config = {
        "neutron-api": {
            "/etc/neutron/neutron.conf": {
                "sections": {
                    'DEFAULT': [
                        ('foo', 'bar')
                    ],
                }
            }
        }
    }
    service_plugins = ','.join((
        api_principle.neutron_config_data.get('service_plugins', ''),
        'networking_ovn.l3.l3_ovn.OVNL3RouterPlugin'),
    )
    api_principle.configure_plugin(
        neutron_plugin='ovn',
        core_plugin='neutron.plugins.ml2.plugin.Ml2Plugin',
        neutron_plugin_config='/etc/neutron/plugins/ml2/ml2_conf.ini',
        service_plugins=service_plugins,
        subordinate_configuration=inject_config)
```

## request\_restart

Requesting a restart of all remote services:

```python
@reactive.when('neutron-plugin-api-subordinate.connected')
def remote_restart(api_principle):
    ...
    api_principle.request_restart()
```

Requesting a restart of a specific type of remote services:

```python
@reactive.when('neutron-plugin-api-subordinate.connected')
def remote_restart(api_principle):
    ...
    api_principle.request_restart(service_type='neutron')
```

# Metadata

To consume this interface in your charm or layer, add the following to
`layer.yaml`:

```yaml
includes: ['interface:neutron-plugin-api-subordinate']
```

and add a provides interface of type `neutron-plugin-api-subordinate` to your
charm or layers `metadata.yaml` eg:

```yaml
provides:
  neutron-plugin-api-subordinate:
    interface: neutron-plugin-api-subordinate
    scope: container
```

# Bugs

Please report bugs on
[Launchpad](https://bugs.launchpad.net/openstack-charms/+filebug).

For development questions please refer to the OpenStack [Charm
Guide](https://github.com/openstack/charm-guide).
