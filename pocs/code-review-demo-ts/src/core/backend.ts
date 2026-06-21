import { ChatModel } from "beeai-framework/backend/chat";

export async function getLLM() {
  const model = process.env.ANTHROPIC_CHAT_MODEL ?? "claude-sonnet-4-6";
  return ChatModel.fromName(`anthropic:${model}`);
}
