export function buildLabel() {
  const sha = process.env.RENDER_GIT_COMMIT;
  return sha ? `Build ${sha.slice(0, 7)}` : "Lokal version";
}
