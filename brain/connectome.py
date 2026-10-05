class Connectome:
    def __init__(self):
        # Base activation levels (0.0 to 1.0)
        self.nodes = {
            "cortex": 0.5,
            "thalamus": 0.5,
            "hippocampus": 0.5,
            "amygdala": 0.1,
            "global_workspace": 0.5,
            "decision": 0.0
        }
        
        # Directional edges and weights
        self.edges = {
            "thalamus": {"cortex": 0.8, "global_workspace": 0.9},
            "cortex": {"global_workspace": 0.9, "hippocampus": 0.5},
            "hippocampus": {"global_workspace": 0.7, "cortex": 0.4},
            "amygdala": {"global_workspace": 0.8, "hippocampus": 0.6},
            "global_workspace": {"decision": 1.0, "cortex": 0.5},
            "decision": {}
        }

    def update_node(self, node, value):
        """Set the activation of a specific brain region."""
        if node in self.nodes:
            self.nodes[node] = max(0.0, min(1.0, value))

    def propagate(self):
        """Spreads activation through the network based on edge weights."""
        new_state = self.nodes.copy()
        for source, targets in self.edges.items():
            source_val = self.nodes[source]
            for target, weight in targets.items():
                # Activation flows from source to target
                new_state[target] = min(1.0, new_state[target] + (source_val * weight * 0.2))
        
        # Decay (homeostasis)
        for node in new_state:
            new_state[node] *= 0.95
            
        self.nodes = new_state
