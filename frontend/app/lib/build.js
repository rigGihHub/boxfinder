import packageInfo from "../../package.json";

export const APP_VERSION = packageInfo.version;

export function buildLabel() {
  const sha = process.env.RENDER_GIT_COMMIT;
  return sha ? `v${APP_VERSION} · ${sha.slice(0, 7)}` : `v${APP_VERSION}`;
}
