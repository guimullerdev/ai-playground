import { BeeAgent } from "bee-agent-framework/agents/bee/agent";
import { OllamaChatModel } from "bee-agent-framework/adapters/ollama/backend/chat";
import { TokenMemory } from "bee-agent-framework/memory/tokenMemory";
import { DuckDuckGoSearchTool } from "bee-agent-framework/tools/search/duckDuckGoSearch";
import { OpenMeteoTool } from "bee-agent-framework/tools/weather/openMeteo";

const llm = new OllamaChatModel({
  modelId: "llama3.1",
});

const agent = new BeeAgent({
  llm,
  memory: new TokenMemory({ llm }),
  tools: [
    new DuckDuckGoSearchTool(),
    new OpenMeteoTool(),
  ],
});

const response = await agent.run({
  prompt: "What is the current weather in São Paulo, and any recent news about it?",
});

console.log("Agent response:", response.result.text);