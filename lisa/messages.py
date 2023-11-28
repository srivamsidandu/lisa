from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, TypeVar

from lisa import notifier
from lisa.schema import NetworkDataPath
from lisa.util import dict_to_fields

if TYPE_CHECKING:
    from lisa import Node
    from lisa.testsuite import TestResult


@dataclass
class MessageBase:
    type: str = "Base"
    time: datetime = datetime.min
    elapsed: float = 0


TestRunStatus = Enum(
    "TestRunStatus",
    [
        "INITIALIZING",
        "RUNNING",
        "SUCCESS",
        "FAILED",
    ],
)

TestStatus = Enum(
    "TestStatus",
    [
        # A test result is created, but not assigned to any running queue.
        "QUEUED",
        # A test result is assigned to an environment, may be run later or not
        # able to run. It may be returned to QUEUED status, if the environment
        # doesn't fit this case.
        "ASSIGNED",
        # A test result is running
        "RUNNING",
        "FAILED",
        "PASSED",
        # A test result is skipped, won't be run anymore.
        "SKIPPED",
        # A test result is failed with known issue.
        "ATTEMPTED",
    ],
)


@dataclass
class TestRunMessage(MessageBase):
    type: str = "TestRun"
    status: TestRunStatus = TestRunStatus.INITIALIZING
    runbook_name: str = ""
    test_project: str = ""
    test_pass: str = ""
    tags: Optional[List[str]] = None
    run_name: str = ""
    message: str = ""


@dataclass
class TestResultMessageBase(MessageBase):
    # id is used to identify the unique test result
    id_: str = ""
    type: str = "TestResultMessageBase"
    name: str = ""
    status: TestStatus = TestStatus.QUEUED
    message: str = ""
    stacktrace: Optional[str] = None
    information: Dict[str, str] = field(default_factory=dict)

    @property
    def is_completed(self) -> bool:
        return _is_completed_status(self.status)


@dataclass
class TestResultMessage(TestResultMessageBase):
    type: str = "TestResult"
    full_name: str = ""
    suite_name: str = ""
    suite_full_name: str = ""
    log_file: str = ""


@dataclass
class SubTestMessage(TestResultMessageBase):
    hardware_platform: str = ""
    type: str = "SubTestResult"
    parent_test: str = ""


class NetworkProtocol(str, Enum):
    IPv4 = "IPv4"
    IPv6 = "IPv6"


class TransportProtocol(str, Enum):
    Tcp = "TCP"
    Udp = "UDP"


@dataclass
class PerfMessage(MessageBase):
    type: str = "Performance"
    tool: str = ""
    test_case_name: str = ""
    platform: str = ""
    location: str = ""
    host_version: str = ""
    guest_os_type: str = "Linux"
    distro_version: str = ""
    vmsize: str = ""
    kernel_version: str = ""
    lis_version: str = ""
    ip_version: str = NetworkProtocol.IPv4
    protocol_type: str = TransportProtocol.Tcp
    data_path: str = ""
    test_date: datetime = datetime.utcnow()
    role: str = ""
    test_result_id: str = ""


T = TypeVar("T", bound=PerfMessage)

DiskSetupType = Enum(
    "DiskSetupType",
    [
        "unknown",
        "raw",
        "raid0",
    ],
)


DiskType = Enum(
    "DiskType",
    [
        "unknown",
        "nvme",
        "premiumssd",
        "ultradisk",
    ],
)


@dataclass
class SysbenchPerfMessage:
    # Sysbench common params
    min_latency_ms: float = 0.00
    max_latency_ms: float = 0.00
    avg_latency_ms: float = 0.00
    percentile_95_latency_ms: float = 0.00
    sum_latency_ms: float = 0.00
    total_time: float = 0.00
    events_avg: float = 0.00
    events_stddev: float = 0.00
    execution_time_avg: float = 0.00
    execution_time_stddev: float = 0.00
    total_events: Decimal = Decimal(0)
    threads: int = 0
    events: int = 0
    time_limit_sec: int = 0


@dataclass
class CPUPerformanceMessage(PerfMessage, SysbenchPerfMessage):
    benchmark: str = ""
    cpu_speed: Decimal = Decimal(0)


@dataclass
class DiskPerformanceMessage(PerfMessage, SysbenchPerfMessage):
    disk_setup_type: DiskSetupType = DiskSetupType.raw
    block_size: int = 0
    disk_type: DiskType = DiskType.nvme
    core_count: int = 0
    disk_count: int = 0
    qdepth: int = 0
    iodepth: int = 0
    numjob: int = 0
    read_iops: Decimal = Decimal(0)
    read_lat_usec: Decimal = Decimal(0)
    randread_iops: Decimal = Decimal(0)
    randread_lat_usec: Decimal = Decimal(0)
    write_iops: Decimal = Decimal(0)
    write_lat_usec: Decimal = Decimal(0)
    randwrite_iops: Decimal = Decimal(0)
    randwrite_lat_usec: Decimal = Decimal(0)

    # Sysbench FileIO params
    read_mib_per_sec: Decimal = Decimal(0)
    write_mib_per_sec: Decimal = Decimal(0)
    fsyncs_per_sec: Decimal = Decimal(0)
    file_fsync_all: str = ""
    file_fsync_end: str = ""
    total_file: int = 0
    file_total_size_in_gb: int = 0
    file_async_backlog: int = 0
    file_fsync_freq: int = 0
    file_merged_requests: int = 0
    file_rw_ratio: float = 0
    file_ops: str = ""
    file_io_mode: str = ""
    file_fsync_mode: str = ""


@dataclass
class MemoryPerformanceMessage(PerfMessage, SysbenchPerfMessage):
    total_mib_transferred: int = 0
    block_size_in_kb: int = 0
    memory_total_size_in_gb: int = 0
    mib_per_second: float = 0.0
    operations_per_second: float = 0
    scope: str = ""
    hugetlb_on: bool = False
    access_mode: str = ""
    operation: str = ""


@dataclass
class NetworkLatencyPerformanceMessage(PerfMessage):
    max_latency_us: Decimal = Decimal(0)
    average_latency_us: Decimal = Decimal(0)
    min_latency_us: Decimal = Decimal(0)
    latency95_percentile_us: Decimal = Decimal(0)
    latency99_percentile_us: Decimal = Decimal(0)
    interval_us: int = 0
    frequency: int = 0


@dataclass
class NetworkPPSPerformanceMessage(PerfMessage):
    test_type: str = ""
    rx_pps_minimum: Decimal = Decimal(0)
    rx_pps_average: Decimal = Decimal(0)
    rx_pps_maximum: Decimal = Decimal(0)
    tx_pps_minimum: Decimal = Decimal(0)
    tx_pps_average: Decimal = Decimal(0)
    tx_pps_maximum: Decimal = Decimal(0)
    rx_tx_pps_minimum: Decimal = Decimal(0)
    rx_tx_pps_average: Decimal = Decimal(0)
    rx_tx_pps_maximum: Decimal = Decimal(0)
    fwd_pps_maximum: Decimal = Decimal(0)
    fwd_pps_average: Decimal = Decimal(0)
    fwd_pps_minimum: Decimal = Decimal(0)


@dataclass
class NetworkTCPPerformanceMessage(PerfMessage):
    connections_num: int = 0
    throughput_in_gbps: Decimal = Decimal(0)
    latency_us: Decimal = Decimal(0)
    buffer_size: Decimal = Decimal(0)
    tx_packets: Decimal = Decimal(0)
    rx_packets: Decimal = Decimal(0)
    pkts_interrupts: Decimal = Decimal(0)
    number_of_receivers: int = 1
    number_of_senders: int = 1
    sender_cycles_per_byte: Decimal = Decimal(0)
    connections_created_time: int = 0
    retrans_segments: int = 0
    receiver_cycles_rer_byte: Decimal = Decimal(0)
    # iperf tcp fields
    buffer_size_bytes: Decimal = Decimal(0)
    tx_throughput_in_gbps: Decimal = Decimal(0)
    rx_throughput_in_gbps: Decimal = Decimal(0)
    retransmitted_segments: Decimal = Decimal(0)
    congestion_windowsize_kb: Decimal = Decimal(0)


@dataclass
class NetworkUDPPerformanceMessage(PerfMessage):
    connections_num: int = 0
    number_of_receivers: int = 1
    number_of_senders: int = 1
    connections_created_time: int = 0
    receiver_cycles_rer_byte: Decimal = Decimal(0)
    send_buffer_size: Decimal = Decimal(0)
    tx_throughput_in_gbps: Decimal = Decimal(0)
    rx_throughput_in_gbps: Decimal = Decimal(0)
    data_loss: Decimal = Decimal(0)
    packet_size_kbytes: Decimal = Decimal(0)


@dataclass
class IPCLatency(PerfMessage):
    average_time_sec: Decimal = Decimal(0)
    min_time_sec: Decimal = Decimal(0)
    max_time_sec: Decimal = Decimal(0)


@dataclass
class DescriptorPollThroughput(PerfMessage):
    average_ops: Decimal = Decimal(0)
    min_ops: Decimal = Decimal(0)
    max_ops: Decimal = Decimal(0)


@dataclass
class ProvisionBootTimeMessage(MessageBase):
    type: str = "ProvisionBootTime"

    # boot times collected from `last reboot` entries
    boot_times: int = 0
    provision_time: float = 0
    kernel_boot_time: float = 0
    initrd_boot_time: float = 0
    userspace_boot_time: float = 0
    firmware_boot_time: float = 0
    loader_boot_time: float = 0
    information: Dict[str, str] = field(default_factory=dict)


@dataclass
class KernelBuildMessage(MessageBase):
    type: str = "KernelBuild"
    old_kernel_version: str = ""
    new_kernel_version: str = ""
    is_success: bool = False
    error_message: str = ""


def _is_completed_status(status: TestStatus) -> bool:
    return status in [
        TestStatus.FAILED,
        TestStatus.PASSED,
        TestStatus.SKIPPED,
        TestStatus.ATTEMPTED,
    ]


def create_perf_message(
    message_type: Type[T],
    node: "Node",
    test_result: "TestResult",
    test_case_name: str = "",
    other_fields: Optional[Dict[str, Any]] = None,
) -> T:
    environment = test_result.environment
    assert environment, "fail to get environment from testresult"

    data_path: str = ""
    if node.capability.network_interface and isinstance(
        node.capability.network_interface.data_path, NetworkDataPath
    ):
        data_path = node.capability.network_interface.data_path.value
    message = message_type()
    dict_to_fields(environment.get_information(force_run=False), message)
    message.test_case_name = test_case_name
    message.data_path = data_path
    message.test_result_id = test_result.id_
    if other_fields:
        dict_to_fields(other_fields, message)
    return message


TestResultMessageType = TypeVar("TestResultMessageType", bound=TestResultMessageBase)


def send_sub_test_result_message(
    test_result: "TestResult",
    test_case_name: str = "",
    test_status: TestStatus = TestStatus.QUEUED,
    test_message: str = "",
    other_fields: Optional[Dict[str, Any]] = None,
) -> SubTestMessage:
    message = SubTestMessage()
    dict_to_fields(test_result.environment_information, message)
    message.id_ = test_result.id_
    message.name = test_case_name
    message.status = test_status
    message.message = test_message
    message.elapsed = test_result.get_elapsed()

    if not other_fields:
        other_fields = {}
    other_fields.update({"parent_test": test_result.runtime_data.name})
    dict_to_fields(other_fields, message)

    notifier.notify(message)

    return message
