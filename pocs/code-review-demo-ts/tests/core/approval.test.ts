import { describe, it, expect, beforeEach, vi } from "vitest";

async function freshModule() {
  vi.resetModules();
  return import("../../src/core/approval.js") as Promise<typeof import("../../src/core/approval.js")>;
}

describe("approval", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it("resolveApproval returns false when no approval is pending", async () => {
    const { resolveApproval } = await freshModule();
    expect(resolveApproval(true)).toBe(false);
    expect(resolveApproval(false)).toBe(false);
  });

  it("waitForApproval resolves true when approved", async () => {
    const { waitForApproval, resolveApproval } = await freshModule();
    const promise = waitForApproval();
    const hadPending = resolveApproval(true);
    expect(hadPending).toBe(true);
    await expect(promise).resolves.toBe(true);
  });

  it("waitForApproval resolves false when rejected", async () => {
    const { waitForApproval, resolveApproval } = await freshModule();
    const promise = waitForApproval();
    resolveApproval(false);
    await expect(promise).resolves.toBe(false);
  });

  it("resolveApproval returns false after the pending promise is already resolved", async () => {
    const { waitForApproval, resolveApproval } = await freshModule();
    const promise = waitForApproval();
    resolveApproval(true);
    await promise;
    expect(resolveApproval(true)).toBe(false);
  });

  it("only the first resolveApproval call wins when called twice", async () => {
    const { waitForApproval, resolveApproval } = await freshModule();
    const promise = waitForApproval();
    resolveApproval(true);
    resolveApproval(false); // no pending resolver, no-op
    await expect(promise).resolves.toBe(true);
  });
});
