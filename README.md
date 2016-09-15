# Overview

This interface is used for a charm to send configuration information to the
neutron-api principle charm and request a restart of a service managed by
that charm.

# Usage

## States
The interface provides the `{relation-name}.connected` and
`{relation_name}.available` states.

## configure\_plugin

The configure\_plugin method allows the following to be configured in the
principle charm:

* neutron\_plugin: Name of the plugin type eg 'ovs', 'odl' etc. This is not
                   currently used in the principle but should be set to
                   something representitve of the plugin type.
* core\_plugin:    Value of core\_plugin to be set in neutron.conf
* neutroni\_plugin\_config: File containing plugin config. This config file is
                            appended to the list of configs the neutron
                            services read on startup.
* service\_plugins: Value of service\_plugins to be set in neutron.conf
* subordinate\_configuration: Config to be inserted into a configuration file
                              that the principle manages.

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
    api_principle.configure_plugin(                                         
        neutron_plugin='odl',                                               
        core_plugin='neutron.plugins.ml2.plugin.Ml2Plugin',                 
        neutron_plugin_config='/etc/neutron/plugins/ml2/ml2_conf.ini',      
        service_plugins='router,firewall,lbaas,vpnaas,metering',            
        subordinate_configuration=inject_config)  
```

## Restart requests

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
