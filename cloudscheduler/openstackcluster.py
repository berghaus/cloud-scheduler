import os
import sys
import time
import string
import shutil
import logging
import nimbus_xml
import subprocess
import cluster_tools
import cloudscheduler.config as config
import cloudscheduler.utilities as utilities
from cloudscheduler.job_management import _attr_list_to_dict
try:
    import novaclient.v1_1.client as nvclient
    import keystoneclient.v2_0.client as ksclient
except:
    print "Unable to import novaclient - cannot use native openstack cloudtypes"
    sys.exit(1)
log = utilities.get_cloudscheduler_logger()

class OpenStackCluster(cluster_tools.ICluster):
    def __init__(self, name="Dummy Cluster", host="localhost", cloud_type="Dummy",
                 memory=[], max_vm_mem= -1, cpu_archs=[], networks=[], vm_slots=0,
                 cpu_cores=0, storage=0,
                 access_key_id=None, secret_access_key=None, security_group=None,
                 username=None, password=None, tenant_name=None, auth_url=None,
                 hypervisor='xen', key_name=None, boot_timeout=None, secure_connection="",
                 regions=[], vm_domain_name="", reverse_dns_lookup=False,placement_zone=None):

        # Call super class's init
        cluster_tools.ICluster.__init__(self,name=name, host=host, cloud_type=cloud_type,
                         memory=memory, max_vm_mem=max_vm_mem, cpu_archs=cpu_archs, networks=networks,
                         vm_slots=vm_slots, cpu_cores=cpu_cores,
                         storage=storage, hypervisor=hypervisor, boot_timeout=boot_timeout)

        if not security_group:
            security_group = ["default"]
        self.security_groups = security_group

        if not access_key_id or not secret_access_key:
            log.error("Cannot connect to cluster %s "
                      "because you haven't specified an access_key_id or "
                      "a secret_access_key" % self.name)

        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.username = username
        self.password = password
        self.tenant_name = tenant_name
        self.auth_url = auth_url
        self.key_name = key_name
        self.secure_connection = secure_connection in ['True', 'true', 'TRUE']
        self.total_cpu_cores = -1
        self.regions = regions
        self.vm_domain_name = vm_domain_name if vm_domain_name != None else ""
        self.reverse_dns_lookup = reverse_dns_lookup in ['True', 'true', 'TRUE']
        self.placement_zone = placement_zone
    
    def vm_create(self, **args):
        pass

    def vm_destroy(self, vm, return_resources=True, reason=""):
        nova = self._get_creds_nova()
        instance = nova.servers.get(vm.id)
        instance.delete()
        pass

    def vm_poll(self, vm):
        """ Query OpenStack for status information of VMs."""
        nova = self._get_creds_nova()
        instance = nova.servers.get(vm.id)
        vm.status = instance.status
        pass
    
    def _get_creds_ks(self):
        """Get an auth token to Keystone."""
        return ksclient.Client(username=self.username, password=self.password, auth_url=self.auth_url, tenant_name=self.tenant_name)
    def _get_creds_nova(self):
        """Get an auth token to Nova."""
        return nvclient.Client(username=self.username, api_key=self.password, auth_url=self.auth_url, project_id=self.tenant_name)