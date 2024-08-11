from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from functools import cached_property
from itertools import chain
from types import MappingProxyType
from typing import Any, Generator, Generic, Hashable, Iterable, Mapping, TypeVar

from microchat.hashing import HashableItem


Node = TypeVar("Node", bound=Hashable)

AnyHashable = TypeVar("AnyHashable", bound=Hashable)
AnyHashableItem = TypeVar("AnyHashableItem", bound=HashableItem)


def empty_mapping() -> Mapping[Any, Any]:
    return MappingProxyType({})


@dataclass(frozen=True)
class HashableItemWrapper(Generic[AnyHashableItem]):
    wrapped: AnyHashableItem

    @cached_property
    def hash(self) -> int:
        return int.from_bytes(self.wrapped.hash.raw, byteorder='big', signed=True)

    def __hash__(self) -> int:
        return self.hash


@dataclass(frozen=True)
class DAG(Generic[Node]):
    links: Mapping[Node, frozenset[Node]] = field(default_factory=empty_mapping)  # outer links for nodes
    unsafe: InitVar[bool] = False

    def __post_init__(self, unsafe: bool) -> None:
        if unsafe:
            return None
        # TODO: done checking for cycles
        cycles_participants = {}
        if cycles_participants:
            raise ValueError(f"Found one or more cycles with following nodes: {', '.join(map(str, cycles_participants))}")
        return None

    @property
    def levels(self) -> Generator[set[Node], Any, None]:
        nodes = self.nodes
        successors = self.successors
        visited: set[Node] = set()
        level = self.sinks
        while level:
            yield level
            visited.update(level)
            nodes.difference_update(level)
            level = {
                node for node in nodes
                if all(successor in visited for successor in successors[node])
            }

    @property
    def topological_order(self) -> Generator[Node, Any, None]:
        for level in self.levels:
            yield from level

    @property
    def nodes(self) -> set[Node]:
        return set(self.links)

    @property
    def sources(self) -> set[Node]:
        # source is node which has no links from other nodes
        return self.nodes.difference(chain.from_iterable(self.links.values()))

    @property
    def sinks(self) -> set[Node]:
        # sink is node which has no links to other nodes
        return {node for node, links in self.links.items() if not links}

    @property
    def successors(self) -> dict[Node, set[Node]]:
        # in A->B->C successors of node A is B and C
        return _recursive_expand(self.links)

    @property
    def predecessors(self) -> dict[Node, set[Node]]:
        # in A<-B<-C predecessors of node A is B and C
        return self.reverse().successors

    def reverse(self) -> DAG[Node]:
        reversed: dict[Node, set[Node]] = {node: set() for node in self.nodes}
        for source, successors in self.links.items():
            for successor in successors:
                reversed[successor].add(source)
        reversed_freeze = {node: frozenset(successors) for node, successors in reversed.items()}
        return DAG(MappingProxyType(reversed_freeze), unsafe=True)

    def merge(self, other: DAG[Node]) -> DAG[Node]:
        EMPTY: frozenset[Node] = frozenset()
        merged = {
            key: self.links.get(key, EMPTY).union(other.links.get(key, EMPTY))
            for key in chain(self.links, other.links)
        }
        return DAG(MappingProxyType(merged))


def _recursive_expand(input: Mapping[AnyHashable, Iterable[AnyHashable]]) -> dict[AnyHashable, set[AnyHashable]]:
    result: dict[AnyHashable, set[AnyHashable]] = {key: {value for value in values} for key, values in input.items()}
    prev_update: dict[AnyHashable, set[AnyHashable]] = {key: values.copy() for key, values in result.items()}
    while any(prev_update.values()):
        update = {
            key: set(
                new_key
                for updated_key in values
                for new_key in result.setdefault(updated_key, set())
            ).difference(result[key])
            for key, values in prev_update.items()
        }
        for key, value in update.items():
            result[key].update(value)
        prev_update = update
    return result


if __name__ == "__main__":
    test_dict = {
        1: {2, 3},
        2: {4},
        3: {5},
        4: {6},
        5: {6},
    }
    test_dict.update((i, {i+1}) for i in range(6, 10))
    test_dict[10] = set()

    dag_mapping = MappingProxyType({key: frozenset(value) for key, value in test_dict.items()})
    test_dag = DAG(dag_mapping)

    print("Nodes:", test_dag.nodes)
    print("Links:")
    for node, links in sorted(test_dag.links.items()):
        print(f"  {node}: {', '.join(map(str, sorted(links))) or 'None'}")
    print("Predecessors:")
    for node, predecessors in sorted(test_dag.predecessors.items()):
        print(f"  {node}: {', '.join(map(str, sorted(predecessors))) or 'None'}")
    print("Successors:")
    for node, successors in sorted(test_dag.successors.items()):
        print(f"  {node}: {', '.join(map(str, sorted(successors))) or 'None'}")
    print("Sources:", test_dag.sources)
    print("Sinks:", test_dag.sinks)
    print("Levels:")
    for level in test_dag.levels:
        print(' ', ', '.join(str(node) for node in sorted(level)))
