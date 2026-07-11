import logging
from dataclasses import dataclass, field
from typing import Any

from runtime.optimizer.base_pass import OptimizationPass, VerificationResult
from runtime.optimizer.cost_optimizer import CostVector, default_cost_estimator
from runtime.optimizer.dead_node import DeadCodeElimination
from runtime.optimizer.graph import DAGNode, ExecutionDAG
from runtime.optimizer.node_fusion import NodeFusion
from runtime.optimizer.parallelization import ParallelizationPass
from runtime.optimizer.report import OptimizationReport
from runtime.optimizer.verification import verify_full_pipeline

log = logging.getLogger("muscal.optimizer")


@dataclass
class OptimizedPlan:
    dag: ExecutionDAG
    layers: list[list[dict]]
    total_cost: float = 0.0

    @classmethod
    def from_dag(cls, dag: ExecutionDAG) -> "OptimizedPlan":
        layers_raw = dag.topological_sort()
        layers = [
            [
                {
                    "id": n.id,
                    "tool": n.op,
                    "args": n.metadata.get("args", {}) if isinstance(n.metadata, dict) else {},
                    "cost_vector": n.cost_vector.to_dict(),
                    "deps": list(n.dependencies),
                    "layer": layer_idx,
                    "metadata": n.metadata,
                }
                for n in layer_nodes
            ]
            for layer_idx, layer_nodes in enumerate(layers_raw)
        ]

        total_cpu: float = 0.0
        total_ram: float = 0.0
        total_latency: float = 0.0
        total_tokens: int = 0
        total_retries: int = 0
        total_cost_est: float = 0.0
        total_risk: float = 0.0
        total_tool_calls: int = 0
        total_complexity: float = 0.0

        for n in dag.nodes:
            cv = n.cost_vector
            total_cpu += cv.cpu
            total_ram += cv.ram
            total_latency += cv.latency
            total_tokens += cv.tokens
            total_retries += cv.retries
            total_cost_est += cv.estimated_cost
            total_risk = max(total_risk, cv.risk)
            total_tool_calls += cv.tool_calls
            total_complexity = max(total_complexity, cv.graph_complexity)

        aggregated = CostVector(
            cpu=total_cpu,
            ram=total_ram,
            latency=total_latency,
            tokens=total_tokens,
            retries=total_retries,
            estimated_cost=total_cost_est,
            risk=total_risk,
            tool_calls=total_tool_calls,
            graph_complexity=total_complexity,
        )

        return cls(dag=dag, layers=layers, total_cost=aggregated.total())

    @property
    def num_layers(self) -> int:
        return len(self.layers)

    @property
    def num_nodes(self) -> int:
        return len(self.dag.nodes)

    def to_dict(self) -> dict:
        return {
            "layers": self.layers,
            "total_cost": self.total_cost,
            "num_nodes": self.num_nodes,
            "num_layers": self.num_layers,
        }


class OptimizerPipeline:
    def __init__(self) -> None:
        self.passes: list[OptimizationPass] = [
            DeadCodeElimination(),
            NodeFusion(),
            ParallelizationPass(),
        ]

    def optimize(self, plan: Any) -> tuple[OptimizedPlan, OptimizationReport]:
        dag = ExecutionDAG.from_plan(plan)

        if dag.num_nodes == 0:
            plan_layers = []
            total_cost = 0.0
            opt_plan = OptimizedPlan(dag=dag, layers=plan_layers, total_cost=total_cost)
            empty_ver = verify_full_pipeline(dag, dag, [])
            report = OptimizationReport.from_pipeline(dag, dag, [], empty_ver)
            return opt_plan, report

        before_dag = dag
        pass_results: list[dict] = []

        for opt_pass in self.passes:
            pass_before_hash = opt_pass._hash_dag(dag)
            dag = opt_pass.optimize(dag)
            pass_after_hash = opt_pass._hash_dag(dag)

            if dag.num_nodes > 0:
                verify_result = opt_pass.verify(before_dag, dag)
            else:
                verify_result = VerificationResult(passed=True, errors=[])

            pass_result = {
                "name": opt_pass.name,
                "version": opt_pass.version,
                "passed": verify_result.passed,
                "errors": verify_result.errors,
                "hash_before": pass_before_hash,
                "hash_after": pass_after_hash,
                "metadata": {
                    "cost": opt_pass.metadata().cost,
                    "gain": opt_pass.metadata().gain,
                },
            }
            pass_results.append(pass_result)

            if not verify_result.passed:
                log.warning(
                    "Optimizer pass %s failed verification: %s",
                    opt_pass.name,
                    verify_result.errors,
                )
            before_dag = dag

        opt_plan = OptimizedPlan.from_dag(dag)

        full_ver = verify_full_pipeline(
            ExecutionDAG.from_plan(plan),
            dag,
            pass_results,
        )

        report = OptimizationReport.from_pipeline(
            ExecutionDAG.from_plan(plan),
            dag,
            pass_results,
            full_ver,
        )

        log.info(
            "Optimization complete: %d nodes -> %d, %d passes, cost=%.2f",
            ExecutionDAG.from_plan(plan).num_nodes,
            dag.num_nodes,
            len(self.passes),
            opt_plan.total_cost,
        )

        return opt_plan, report
