from agent.perception import PerceptionModule
from agent.vision_agent import VisionAgent
from utils.preprocess import load_and_preprocess
from services.tool_executor import ToolExecutor


MODEL_PATH = "best_multitask_model.pth"
IMAGE_PATH = "sample.jpg"

perception = PerceptionModule(MODEL_PATH)

image_tensor = load_and_preprocess(IMAGE_PATH)

executor = ToolExecutor()
agent = VisionAgent(perception, executor)

result = agent.run(image_tensor)
print(result)

