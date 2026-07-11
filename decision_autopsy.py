from causality_engine import CausalityEngine
from decision_analyzer import DecisionAnalyzer
from explanation_builder import ExplanationBuilder


class DecisionAutopsy:
    def __init__(self, graph_store):
        self.graph = graph_store
        self.causality = CausalityEngine()
        self.analyzer = DecisionAnalyzer()
        self.explainer = ExplanationBuilder()

    def run(self, node_id):
        causality = self.causality.infer(self.graph, node_id)

        node = self.graph.nodes[node_id]

        analysis = self.analyzer.analyze(node, causality)

        explanation = self.explainer.build(analysis, causality)

        return {
            "analysis": analysis,
            "explanation": explanation
        }
