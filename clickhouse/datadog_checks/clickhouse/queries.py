# (C) Datadog, Inc. 2019
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from collections import OrderedDict

from datadog_checks.base.utils import constants
from datadog_checks.base.utils.common import total_time_to_temporal_percent

from .utils import compact_query


class Query(object):
    ignored_columns = set()


class SystemMetrics(Query):
    """
    https://clickhouse.yandex/docs/en/operations/system_tables/#system_tables-metrics
    """

    columns = OrderedDict(
        (
            ('BackgroundPoolTask', (('background_pool.processing.task.active', 'gauge'),)),
            ('BackgroundSchedulePoolTask', (('background_pool.schedule.task.active', 'gauge'),)),
            ('ContextLockWait', (('thread.lock.context.waiting', 'gauge'),)),
            ('DelayedInserts', (('query.insert.delayed', 'gauge'),)),
            ('DictCacheRequests', (('dictionary.request.cache', 'gauge'),)),
            ('DiskSpaceReservedForMerge', (('merge.disk.reserved', 'gauge'),)),
            ('DistributedFilesToInsert', (('table.distributed.file.insert.pending', 'gauge'),)),
            ('DistributedSend', (('table.distributed.connection.inserted', 'gauge'),)),
            ('EphemeralNode', (('zk.node.ephemeral', 'gauge'),)),
            ('GlobalThread', (('thread.global.total', 'gauge'),)),
            ('GlobalThreadActive', (('thread.global.active', 'gauge'),)),
            ('HTTPConnection', (('connection.http', 'gauge'),)),
            ('InterserverConnection', (('connection.interserver', 'gauge'),)),
            ('LeaderElection', (('replica.leader.election', 'gauge'),)),
            ('LeaderReplica', (('table.replicated.leader', 'gauge'),)),
            ('LocalThread', (('thread.local.total', 'gauge'),)),
            ('LocalThreadActive', (('thread.local.active', 'gauge'),)),
            ('MemoryTracking', (('query.memory', 'gauge'),)),
            ('MemoryTrackingForMerges', (('merge.memory', 'gauge'),)),
            ('MemoryTrackingInBackgroundProcessingPool', (('background_pool.processing.memory', 'gauge'),)),
            ('MemoryTrackingInBackgroundSchedulePool', (('background_pool.schedule.memory', 'gauge'),)),
            ('Merge', (('merge.active', 'gauge'),)),
            ('OpenFileForRead', (('file.open.read', 'gauge'),)),
            ('OpenFileForWrite', (('file.open.write', 'gauge'),)),
            ('PartMutation', (('query.mutation', 'gauge'),)),
            ('Query', (('query.active', 'gauge'),)),
            ('QueryPreempted', (('query.waiting', 'gauge'),)),
            ('QueryThread', (('thread.query', 'gauge'),)),
            ('RWLockActiveReaders', (('thread.lock.rw.active.read', 'gauge'),)),
            ('RWLockActiveWriters', (('thread.lock.rw.active.write', 'gauge'),)),
            ('RWLockWaitingReaders', (('thread.lock.rw.waiting.read', 'gauge'),)),
            ('RWLockWaitingWriters', (('thread.lock.rw.waiting.write', 'gauge'),)),
            ('Read', (('syscall.read', 'gauge'),)),
            ('ReadonlyReplica', (('table.replicated.readonly', 'gauge'),)),
            ('ReplicatedChecks', (('table.replicated.part.check', 'gauge'),)),
            ('ReplicatedFetch', (('table.replicated.part.fetch', 'gauge'),)),
            ('ReplicatedSend', (('table.replicated.part.send', 'gauge'),)),
            ('Revision', ()),
            ('SendExternalTables', (('connection.send.external', 'gauge'),)),
            ('SendScalars', (('connection.send.scalar', 'gauge'),)),
            ('StorageBufferBytes', (('table.buffer.size', 'gauge'),)),
            ('StorageBufferRows', (('table.buffer.row', 'gauge'),)),
            ('TCPConnection', (('connection.tcp', 'gauge'),)),
            ('Write', (('syscall.write', 'gauge'),)),
            ('ZooKeeperRequest', (('zk.request', 'gauge'),)),
            ('ZooKeeperSession', (('zk.connection', 'gauge'),)),
            ('ZooKeeperWatch', (('zk.watch', 'gauge'),)),
        )
    )
    ignored_columns = {'VersionInteger'}
    views = ('system.metrics',)
    query = compact_query(
        """
        SELECT
          metric, value
        FROM {view1}
        """.format(
            **{'view{}'.format(i): view for i, view in enumerate(views, 1)}
        )
    )


class SystemEvents(Query):
    """
    https://clickhouse.yandex/docs/en/operations/system_tables/#system_tables-events
    """

    columns = OrderedDict(
        (
            ('CannotRemoveEphemeralNode', (('node.remove.count', 'monotonic_count'), ('node.remove.total', 'gauge'))),
            (
                'CannotWriteToWriteBufferDiscard',
                (('buffer.write.discard.count', 'monotonic_count'), ('buffer.write.discard.total', 'gauge')),
            ),
            (
                'CompileAttempt',
                (('compilation.attempt.count', 'monotonic_count'), ('compilation.attempt.total', 'gauge')),
            ),
            (
                'CompileExpressionsBytes',
                (('compilation.size.count', 'monotonic_count'), ('compilation.size.total', 'gauge')),
            ),
            (
                'CompileExpressionsMicroseconds',
                (
                    (
                        'compilation.time',
                        lambda value: ('rate', total_time_to_temporal_percent(value, scale=constants.MICROSECOND)),
                    ),
                ),
            ),
            (
                'CompileFunction',
                (('compilation.llvm.attempt.count', 'monotonic_count'), ('compilation.llvm.attempt.total', 'gauge')),
            ),
            (
                'CompileSuccess',
                (('compilation.success.count', 'monotonic_count'), ('compilation.success.total', 'gauge')),
            ),
            (
                'CompiledFunctionExecute',
                (
                    ('compilation.function.execute.count', 'monotonic_count'),
                    ('compilation.function.execute.total', 'gauge'),
                ),
            ),
            (
                'ContextLock',
                (('lock.context.acquisition.count', 'monotonic_count'), ('lock.context.acquisition.total', 'gauge')),
            ),
            (
                'CreatedHTTPConnections',
                (('connection.http.create.count', 'monotonic_count'), ('connection.http.create.total', 'gauge')),
            ),
            (
                'DelayedInserts',
                (
                    ('table.mergetree.insert.delayed.count', 'monotonic_count'),
                    ('table.mergetree.insert.delayed.total', 'gauge'),
                ),
            ),
            (
                'DelayedInsertsMilliseconds',
                (
                    (
                        'table.mergetree.insert.delayed.time',
                        lambda value: ('rate', total_time_to_temporal_percent(value, scale=constants.MILLISECOND)),
                    ),
                ),
            ),
            (
                'DiskReadElapsedMicroseconds',
                (
                    (
                        'syscall.read.wait',
                        lambda value: ('rate', total_time_to_temporal_percent(value, scale=constants.MICROSECOND)),
                    ),
                ),
            ),
            (
                'DiskWriteElapsedMicroseconds',
                (
                    (
                        'syscall.write.wait',
                        lambda value: ('rate', total_time_to_temporal_percent(value, scale=constants.MICROSECOND)),
                    ),
                ),
            ),
            (
                'DuplicatedInsertedBlocks',
                (
                    ('table.mergetree.replicated.insert.deduplicate.count', 'monotonic_count'),
                    ('table.mergetree.replicated.insert.deduplicate.total', 'gauge'),
                ),
            ),
            ('FileOpen', (('file.open.count', 'monotonic_count'), ('file.open.total', 'gauge'))),
            ('InsertQuery', (('query.insert.count', 'monotonic_count'), ('query.insert.total', 'gauge'))),
            ('InsertedBytes', (('table.insert.size.count', 'monotonic_count'), ('table.insert.size.total', 'gauge'))),
            ('InsertedRows', (('table.insert.row.count', 'monotonic_count'), ('table.insert.row.total', 'gauge'))),
            (
                'LeaderElectionAcquiredLeadership',
                (
                    ('table.mergetree.replicated.leader.elected.count', 'monotonic_count'),
                    ('table.mergetree.replicated.leader.elected.total', 'gauge'),
                ),
            ),
            ('Merge', (('merge.count', 'monotonic_count'), ('merge.total', 'gauge'))),
            (
                'MergeTreeDataWriterBlocks',
                (
                    ('table.mergetree.insert.block.count', 'monotonic_count'),
                    ('table.mergetree.insert.block.total', 'gauge'),
                ),
            ),
            (
                'MergeTreeDataWriterBlocksAlreadySorted',
                (
                    ('table.mergetree.insert.block.already_sorted.count', 'monotonic_count'),
                    ('table.mergetree.insert.block.already_sorted.total', 'gauge'),
                ),
            ),
            (
                'MergeTreeDataWriterCompressedBytes',
                (
                    ('table.mergetree.insert.write.size.compressed.count', 'monotonic_count'),
                    ('table.mergetree.insert.write.size.compressed.total', 'gauge'),
                ),
            ),
            (
                'MergeTreeDataWriterRows',
                (
                    ('table.mergetree.insert.row.count', 'monotonic_count'),
                    ('table.mergetree.insert.row.total', 'gauge'),
                ),
            ),
            (
                'MergeTreeDataWriterUncompressedBytes',
                (
                    ('table.mergetree.insert.write.size.uncompressed.count', 'monotonic_count'),
                    ('table.mergetree.insert.write.size.uncompressed.total', 'gauge'),
                ),
            ),
            ('MergedRows', (('merge.row.read.count', 'monotonic_count'), ('merge.row.read.total', 'gauge'))),
            (
                'MergedUncompressedBytes',
                (
                    ('merge.read.size.uncompressed.count', 'monotonic_count'),
                    ('merge.read.size.uncompressed.total', 'gauge'),
                ),
            ),
            (
                'MergesTimeMilliseconds',
                (
                    (
                        'merge.time',
                        lambda value: ('rate', total_time_to_temporal_percent(value, scale=constants.MILLISECOND)),
                    ),
                ),
            ),
            (
                'OSCPUVirtualTimeMicroseconds',
                (
                    (
                        'cpu.time',
                        lambda value: ('rate', total_time_to_temporal_percent(value, scale=constants.MICROSECOND)),
                    ),
                ),
            ),
            (
                'OSCPUWaitMicroseconds',
                (
                    (
                        'thread.cpu.wait',
                        lambda value: ('rate', total_time_to_temporal_percent(value, scale=constants.MICROSECOND)),
                    ),
                ),
            ),
            (
                'OSIOWaitMicroseconds',
                (
                    (
                        'thread.io.wait',
                        lambda value: ('rate', total_time_to_temporal_percent(value, scale=constants.MICROSECOND)),
                    ),
                ),
            ),
            ('OSReadBytes', (('disk.read.size.count', 'monotonic_count'), ('disk.read.size.total', 'gauge'))),
            ('OSReadChars', (('fs.read.size.count', 'monotonic_count'), ('fs.read.size.total', 'gauge'))),
            ('OSWriteBytes', (('disk.write.size.count', 'monotonic_count'), ('disk.write.size.total', 'gauge'))),
            ('OSWriteChars', (('fs.write.size.count', 'monotonic_count'), ('fs.write.size.total', 'gauge'))),
            ('Query', (('query.count', 'monotonic_count'), ('query.total', 'gauge'))),
            (
                'QueryMaskingRulesMatch',
                (('query.mask.match.count', 'monotonic_count'), ('compilation.llvm.attempt.total', 'gauge')),
            ),
            (
                'QueryProfilerSignalOverruns',
                (('query.signal.dropped.count', 'monotonic_count'), ('query.signal.dropped.total', 'gauge')),
            ),
            ('ReadBackoff', (('query.read.backoff.count', 'monotonic_count'), ('query.read.backoff.total', 'gauge'))),
            (
                'ReadBufferFromFileDescriptorRead',
                (('file.read.count', 'monotonic_count'), ('file.read.total', 'gauge')),
            ),
            (
                'ReadBufferFromFileDescriptorReadBytes',
                (('file.read.size.count', 'monotonic_count'), ('file.read.size.total', 'gauge')),
            ),
            (
                'ReadBufferFromFileDescriptorReadFailed',
                (('file.read.fail.count', 'monotonic_count'), ('file.read.fail.total', 'gauge')),
            ),
            (
                'RealTimeMicroseconds',
                (
                    (
                        'thread.process_time',
                        lambda value: ('rate', total_time_to_temporal_percent(value, scale=constants.MICROSECOND)),
                    ),
                ),
            ),
            ('RegexpCreated', (('compilation.regex.count', 'monotonic_count'), ('compilation.regex.total', 'gauge'))),
            (
                'RejectedInserts',
                (
                    ('table.mergetree.insert.block.rejected.count', 'monotonic_count'),
                    ('table.mergetree.insert.block.rejected.total', 'gauge'),
                ),
            ),
            (
                'ReplicaYieldLeadership',
                (
                    ('table.replicated.leader.yield.count', 'monotonic_count'),
                    ('table.replicated.leader.yield.total', 'gauge'),
                ),
            ),
            (
                'ReplicatedDataLoss',
                (
                    ('table.replicated.part.loss.count', 'monotonic_count'),
                    ('table.replicated.part.loss.total', 'gauge'),
                ),
            ),
            (
                'ReplicatedPartFetches',
                (
                    ('table.mergetree.replicated.fetch.replica.count', 'monotonic_count'),
                    ('table.mergetree.replicated.fetch.replica.total', 'gauge'),
                ),
            ),
            (
                'ReplicatedPartFetchesOfMerged',
                (
                    ('table.mergetree.replicated.fetch.merged.count', 'monotonic_count'),
                    ('table.mergetree.replicated.fetch.merged.total', 'gauge'),
                ),
            ),
            ('Seek', (('file.seek.count', 'monotonic_count'), ('file.seek.total', 'gauge'))),
            ('SelectQuery', (('query.select.count', 'monotonic_count'), ('query.select.total', 'gauge'))),
            (
                'SelectedMarks',
                (
                    ('table.mergetree.mark.selected.count', 'monotonic_count'),
                    ('table.mergetree.mark.selected.total', 'gauge'),
                ),
            ),
            (
                'SelectedParts',
                (
                    ('table.mergetree.part.selected.count', 'monotonic_count'),
                    ('table.mergetree.part.selected.total', 'gauge'),
                ),
            ),
            (
                'SelectedRanges',
                (
                    ('table.mergetree.range.selected.count', 'monotonic_count'),
                    ('table.mergetree.range.selected.total', 'gauge'),
                ),
            ),
            ('SlowRead', (('file.read.slow.count', 'monotonic_count'), ('file.read.slow.total', 'gauge'))),
            (
                'SystemTimeMicroseconds',
                (
                    (
                        'thread.system.process_time',
                        lambda value: ('rate', total_time_to_temporal_percent(value, scale=constants.MICROSECOND)),
                    ),
                ),
            ),
            (
                'ThrottlerSleepMicroseconds',
                (
                    (
                        'query.sleep.time',
                        lambda value: ('rate', total_time_to_temporal_percent(value, scale=constants.MICROSECOND)),
                    ),
                ),
            ),
            (
                'UserTimeMicroseconds',
                (
                    (
                        'thread.user.process_time',
                        lambda value: ('rate', total_time_to_temporal_percent(value, scale=constants.MICROSECOND)),
                    ),
                ),
            ),
            (
                'WriteBufferFromFileDescriptorWrite',
                (('file.write.count', 'monotonic_count'), ('file.write.total', 'gauge')),
            ),
            (
                'WriteBufferFromFileDescriptorWriteBytes',
                (('file.write.size.count', 'monotonic_count'), ('file.write.size.total', 'gauge')),
            ),
            (
                'WriteBufferFromFileDescriptorWriteFailed',
                (('file.write.fail.count', 'monotonic_count'), ('file.write.fail.total', 'gauge')),
            ),
        )
    )
    views = ('system.events',)
    query = compact_query(
        """
        SELECT
          event, value
        FROM {view1}
        """.format(
            **{'view{}'.format(i): view for i, view in enumerate(views, 1)}
        )
    )


class SystemAsynchronousMetrics(Query):
    """
    https://clickhouse.yandex/docs/en/operations/system_tables/#system_tables-asynchronous_metrics
    """

    columns = OrderedDict(
        (
            ('CompiledExpressionCacheCount', (('CompiledExpressionCacheCount', 'gauge'),)),
            ('MarkCacheBytes', (('table.mergetree.storage.mark.cache', 'gauge'),)),
            ('MarkCacheFiles', (('MarkCacheFiles', 'gauge'),)),
            ('MaxPartCountForPartition', (('part.max', 'gauge'),)),
            ('NumberOfDatabases', (('database.total', 'gauge'),)),
            ('NumberOfTables', (('table.total', 'gauge'),)),
            ('ReplicasMaxAbsoluteDelay', (('replica.delay.absolute', 'gauge'),)),
            ('ReplicasMaxInsertsInQueue', (('ReplicasMaxInsertsInQueue', 'gauge'),)),
            ('ReplicasMaxMergesInQueue', (('ReplicasMaxMergesInQueue', 'gauge'),)),
            ('ReplicasMaxQueueSize', (('ReplicasMaxQueueSize', 'gauge'),)),
            ('ReplicasMaxRelativeDelay', (('replica.delay.relative', 'gauge'),)),
            ('ReplicasSumInsertsInQueue', (('ReplicasSumInsertsInQueue', 'gauge'),)),
            ('ReplicasSumMergesInQueue', (('ReplicasSumMergesInQueue', 'gauge'),)),
            ('ReplicasSumQueueSize', (('replica.queue.size', 'gauge'),)),
            ('UncompressedCacheBytes', (('UncompressedCacheBytes', 'gauge'),)),
            ('UncompressedCacheCells', (('UncompressedCacheCells', 'gauge'),)),
            ('Uptime', (('uptime', 'gauge'),)),
            ('jemalloc.active', (('jemalloc.active', 'gauge'),)),
            ('jemalloc.allocated', (('jemalloc.allocated', 'gauge'),)),
            ('jemalloc.background_thread.num_runs', (('jemalloc.background_thread.num_runs', 'gauge'),)),
            ('jemalloc.background_thread.num_threads', (('jemalloc.background_thread.num_threads', 'gauge'),)),
            ('jemalloc.background_thread.run_interval', (('jemalloc.background_thread.run_interval', 'gauge'),)),
            ('jemalloc.mapped', (('jemalloc.mapped', 'gauge'),)),
            ('jemalloc.metadata', (('jemalloc.metadata', 'gauge'),)),
            ('jemalloc.metadata_thp', (('jemalloc.metadata_thp', 'gauge'),)),
            ('jemalloc.resident', (('jemalloc.resident', 'gauge'),)),
            ('jemalloc.retained', (('jemalloc.retained', 'gauge'),)),
        )
    )
    views = ('system.asynchronous_metrics',)
    query = compact_query(
        """
        SELECT
          metric, value
        FROM {view1}
        """.format(
            **{'view{}'.format(i): view for i, view in enumerate(views, 1)}
        )
    )


class SystemParts(Query):
    """
    https://clickhouse.yandex/docs/en/operations/system_tables/#system_tables-parts
    """

    columns = ('database', 'table', 'bytes', 'parts', 'rows')
    views = ('system.parts',)
    query = compact_query(
        """
        SELECT
          database,
          table,
          sum(bytes_on_disk) AS bytes,
          count() AS parts,
          sum(rows) AS rows
        FROM {view1}
        WHERE active = 1
        GROUP BY
          database,
          table
        """.format(
            **{'view{}'.format(i): view for i, view in enumerate(views, 1)}
        )
    )


class SystemReplicas(Query):
    """
    https://clickhouse.yandex/docs/en/operations/system_tables/#system_tables-replicas
    """

    columns = (
        'database',
        'table',
        'is_leader',
        'is_readonly',
        'is_session_expired',
        'future_parts',
        'parts_to_check',
        'columns_version',
        'queue_size',
        'inserts_in_queue',
        'merges_in_queue',
        'log_max_index',
        'log_pointer',
        'total_replicas',
        'active_replicas',
    )
    views = ('system.replicas',)
    query = compact_query(
        """
        SELECT
          {columns}
        FROM {view1}
        """.format(
            columns=', '.join(columns), **{'view{}'.format(i): view for i, view in enumerate(views, 1)}
        )
    )


class SystemDictionaries(Query):
    """
    https://clickhouse.yandex/docs/en/operations/system_tables/#system-dictionaries
    """

    columns = ('name', 'bytes_allocated', 'element_count', 'load_factor')
    views = ('system.dictionaries',)
    query = compact_query(
        """
        SELECT
          {columns}
        FROM {view1}
        """.format(
            columns=', '.join(columns), **{'view{}'.format(i): view for i, view in enumerate(views, 1)}
        )
    )
