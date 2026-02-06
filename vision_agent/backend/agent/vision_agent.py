from agent.decision_policy import DecisionPolicy

class VisionAgent:
    def __init__(self, perception, executor):
        self.perception = perception
        self.policy = DecisionPolicy()
        self.executor = executor

    def run(self, image_tensor):
        probs = self.perception.infer(image_tensor)
        action, confidence, reason = self.policy.decide(probs)

        tool_output = self.executor.execute(action, image_tensor)

        return {
            "probs": probs,
            "action": action.value,
            "confidence": confidence,
            "reason": reason,
            "tool_output": tool_output
        }

