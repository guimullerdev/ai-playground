let _resolver: ((approved: boolean) => void) | null = null;

export function waitForApproval(): Promise<boolean> {
  return new Promise((resolve) => {
    _resolver = resolve;
  });
}

export function resolveApproval(approved: boolean): boolean {
  if (!_resolver) return false;
  const fn = _resolver;
  _resolver = null;
  fn(approved);
  return true;
}
