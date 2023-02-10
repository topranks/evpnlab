To start:

Modify Homer so we can use the ipaddr module from Ansible

pip3 install ansible

Then insert into the homer templates.py file:
```
from ansible_collections.ansible.utils.plugins.filter import ipaddr
```

And add this line at the end of the __init__ function in the Renderer class:
```
        self._env.filters.update(ipaddr.FilterModule().filters())
```


