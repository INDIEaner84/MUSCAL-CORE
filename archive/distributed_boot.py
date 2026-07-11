"""
⚠️ DEPRECATED — Uses deprecated `kernel_core.Kernel` + `distributed_kernel`.
    The active production system uses `MuscalOS` from `muscal_os.py`.
"""
from distributed_kernel import DistributedKernel
from kernel_core import Kernel
from message_broker import MessageBroker
from muscal_node import MUSCALNode


def boot_system():
    broker = MessageBroker()

    nodeA = MUSCALNode("A", Kernel())
    nodeB = MUSCALNode("B", Kernel())
    nodeC = MUSCALNode("C", Kernel())

    broker.subscribe(nodeA)
    broker.subscribe(nodeB)
    broker.subscribe(nodeC)

    system = DistributedKernel(
        [nodeA, nodeB, nodeC],
        broker
    )

    return system


if __name__ == "__main__":
    system = boot_system()

    while True:
        user = input(">> ")

        result = system.run(user)

        print(result)
