# (C) Datadog, Inc. 2010-2019
# All rights reserved
# Licensed under Simplified BSD License (see LICENSE)
import ipaddress
import os
from collections import defaultdict

import pysnmp_mibs
from pyasn1.type.univ import OctetString
from pysmi.codegen import PySnmpCodeGen
from pysmi.compiler import MibCompiler
from pysmi.parser import SmiStarParser
from pysmi.reader import HttpReader
from pysmi.writer import PyFileWriter
from pysnmp import hlapi
from pysnmp.smi import builder, view
from pysnmp.smi.error import MibNotFoundError

from datadog_checks.base import ConfigurationError, is_affirmative


class InstanceConfig:
    """Parse and hold configuration about a single instance."""

    DEFAULT_RETRIES = 5
    DEFAULT_TIMEOUT = 1
    DEFAULT_ALLOWED_FAILURES = 3
    DEFAULT_BULK_THRESHOLD = 5

    def __init__(self, instance, warning, log, global_metrics, mibs_path, profiles, profiles_by_oid):
        self.instance = instance
        self.tags = instance.get('tags', [])
        self.metrics = instance.get('metrics', [])
        profile = instance.get('profile')
        if is_affirmative(instance.get('use_global_metrics', True)):
            self.metrics.extend(global_metrics)
        if profile:
            if profile not in profiles:
                raise ConfigurationError("Unknown profile '{}'".format(profile))
            self.metrics.extend(profiles[profile]['definition']['metrics'])
        self.enforce_constraints = is_affirmative(instance.get('enforce_mib_constraints', True))
        self.snmp_engine, self.mib_view_controller = self.create_snmp_engine(mibs_path)
        self.ip_address = None
        self.ip_network = None
        self.discovered_instances = {}
        self.failing_instances = defaultdict(int)
        self.allowed_failures = int(instance.get('discovery_allowed_failures', self.DEFAULT_ALLOWED_FAILURES))
        self.bulk_threshold = int(instance.get('bulk_threshold', self.DEFAULT_BULK_THRESHOLD))

        timeout = int(instance.get('timeout', self.DEFAULT_TIMEOUT))
        retries = int(instance.get('retries', self.DEFAULT_RETRIES))

        ip_address = instance.get('ip_address')
        network_address = instance.get('network_address')

        if not ip_address and not network_address:
            raise ConfigurationError('An IP address or a network address needs to be specified')

        if ip_address and network_address:
            raise ConfigurationError('Only one of IP address and network address must be specified')

        if ip_address:
            self.transport = self.get_transport_target(instance, timeout, retries)

            self.ip_address = ip_address
            self.tags.append('snmp_device:{}'.format(self.ip_address))

        if network_address:
            if isinstance(network_address, bytes):
                network_address = network_address.decode('utf-8')
            self.ip_network = ipaddress.ip_network(network_address)

        if not self.metrics and not profiles_by_oid:
            raise ConfigurationError('Instance should specify at least one metric or profiles should be defined')

        self.table_oids, self.raw_oids, self.mibs_to_load = self.parse_metrics(self.metrics, warning, log)

        self.auth_data = self.get_auth_data(instance)
        self.context_data = hlapi.ContextData(*self.get_context_data(instance))

    def refresh_with_profile(self, profile, warning, log):
        self.metrics.extend(profile['definition']['metrics'])
        self.table_oids, self.raw_oids, self.mibs_to_load = self.parse_metrics(self.metrics, warning, log)

    def call_cmd(self, cmd, *args, **kwargs):
        return cmd(self.snmp_engine, self.auth_data, self.transport, self.context_data, *args, **kwargs)

    @staticmethod
    def create_snmp_engine(mibs_path):
        """
        Create a command generator to perform all the snmp query.
        If mibs_path is not None, load the mibs present in the custom mibs
        folder. (Need to be in pysnmp format)
        """
        snmp_engine = hlapi.SnmpEngine()
        mib_builder = snmp_engine.getMibBuilder()
        if mibs_path is not None:
            mib_builder.addMibSources(builder.DirMibSource(mibs_path))

        mib_view_controller = view.MibViewController(mib_builder)

        return snmp_engine, mib_view_controller

    @staticmethod
    def get_transport_target(instance, timeout, retries):
        """
        Generate a Transport target object based on the instance's configuration
        """
        ip_address = instance['ip_address']
        port = int(instance.get('port', 161))  # Default SNMP port
        return hlapi.UdpTransportTarget((ip_address, port), timeout=timeout, retries=retries)

    @staticmethod
    def get_auth_data(instance):
        """
        Generate a Security Parameters object based on the instance's
        configuration.
        See http://pysnmp.sourceforge.net/docs/current/security-configuration.html
        """
        if 'community_string' in instance:
            # SNMP v1 - SNMP v2

            # See http://pysnmp.sourceforge.net/docs/current/security-configuration.html
            if int(instance.get('snmp_version', 2)) == 1:
                return hlapi.CommunityData(instance['community_string'], mpModel=0)
            return hlapi.CommunityData(instance['community_string'], mpModel=1)

        elif 'user' in instance:
            # SNMP v3
            user = instance['user']
            auth_key = None
            priv_key = None
            auth_protocol = None
            priv_protocol = None
            if 'authKey' in instance:
                auth_key = instance['authKey']
                auth_protocol = hlapi.usmHMACMD5AuthProtocol
            if 'privKey' in instance:
                priv_key = instance['privKey']
                auth_protocol = hlapi.usmHMACMD5AuthProtocol
                priv_protocol = hlapi.usmDESPrivProtocol
            if 'authProtocol' in instance:
                auth_protocol = getattr(hlapi, instance['authProtocol'])
            if 'privProtocol' in instance:
                priv_protocol = getattr(hlapi, instance['privProtocol'])
            return hlapi.UsmUserData(user, auth_key, priv_key, auth_protocol, priv_protocol)
        else:
            raise ConfigurationError('An authentication method needs to be provided')

    @staticmethod
    def get_context_data(instance):
        """
        Generate a Context Parameters object based on the instance's
        configuration.
        We do not use the hlapi currently, but the rfc3413.oneliner.cmdgen
        accepts Context Engine Id (always None for now) and Context Name parameters.
        """
        context_engine_id = None
        context_name = ''

        if 'user' in instance:
            if 'context_engine_id' in instance:
                context_engine_id = OctetString(instance['context_engine_id'])
            if 'context_name' in instance:
                context_name = instance['context_name']

        return context_engine_id, context_name

    def parse_metrics(self, metrics, warning, log):
        """Parse configuration and returns data to be used for SNMP queries.

        `raw_oids` is a list of SNMP numerical OIDs to query.
        `table_oids` is a dictionnary of SNMP tables to symbols to query.
        `mibs_to_load` contains the relevant MIBs used for querying.
        """
        raw_oids = []
        table_oids = {}
        mibs_to_load = set()

        def get_table_symbols(mib, table):
            key = (mib, table)
            if key in table_oids:
                return table_oids[key][1]

            table_object = hlapi.ObjectType(hlapi.ObjectIdentity(mib, table))
            symbols = []
            table_oids[key] = (table_object, symbols)
            return symbols

        # Check the metrics completely defined
        for metric in metrics:
            if 'MIB' in metric:
                if not ('table' in metric or 'symbol' in metric):
                    raise ConfigurationError('When specifying a MIB, you must specify either table or symbol')
                mibs_to_load.add(metric['MIB'])
                if 'symbol' in metric:
                    to_query = metric['symbol']
                    try:
                        get_table_symbols(metric['MIB'], to_query)
                    except Exception as e:
                        warning("Can't generate MIB object for variable : %s\nException: %s", metric, e)
                elif 'symbols' not in metric:
                    raise ConfigurationError('When specifying a table, you must specify a list of symbols')
                else:
                    symbols = get_table_symbols(metric['MIB'], metric['table'])
                    for symbol in metric['symbols']:
                        try:
                            symbols.append(hlapi.ObjectType(hlapi.ObjectIdentity(metric['MIB'], symbol)))
                        except Exception as e:
                            warning("Can't generate MIB object for variable : %s\nException: %s", metric, e)
                    if 'metric_tags' in metric:
                        for metric_tag in metric['metric_tags']:
                            if not ('tag' in metric_tag and ('index' in metric_tag or 'column' in metric_tag)):
                                raise ConfigurationError(
                                    'When specifying metric tags, you must specify a tag, and an index or column'
                                )
                            if 'column' in metric_tag:
                                # In case it's a column, we need to query it as well
                                mib = metric_tag.get('MIB', metric['MIB'])
                                try:
                                    object_type = hlapi.ObjectType(hlapi.ObjectIdentity(mib, metric_tag['column']))
                                except Exception as e:
                                    warning("Can't generate MIB object for variable : %s\nException: %s", metric, e)
                                else:
                                    if 'table' in metric_tag:
                                        tag_symbols = get_table_symbols(mib, metric_tag['table'])
                                        tag_symbols.append(object_type)
                                    elif mib != metric['MIB']:
                                        raise ConfigurationError(
                                            'When tagging from a different MIB, the table must be specified'
                                        )
                                    else:
                                        symbols.append(object_type)

            elif 'OID' in metric:
                raw_oids.append(hlapi.ObjectType(hlapi.ObjectIdentity(metric['OID'])))
            else:
                raise ConfigurationError('Unsupported metric in config file: {}'.format(metric))

        for mib in mibs_to_load:
            try:
                self.mib_view_controller.mibBuilder.loadModule(mib)
            except MibNotFoundError:
                log.debug("Couldn't found mib %s, trying to fetch it", mib)
                self.fetch_mib(mib)

        return dict(table_oids.values()), raw_oids, mibs_to_load

    @staticmethod
    def fetch_mib(mib):
        target_directory = os.path.dirname(pysnmp_mibs.__file__)

        reader = HttpReader('mibs.snmplabs.com', 80, '/asn1/@mib@')
        mibCompiler = MibCompiler(SmiStarParser(), PySnmpCodeGen(), PyFileWriter(target_directory))

        mibCompiler.addSources(reader)

        mibCompiler.compile(mib)
