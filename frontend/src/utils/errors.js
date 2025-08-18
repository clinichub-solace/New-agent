// app/frontend/src/utils/errors.js
export function formatErrorMessage(detail) {
  if (!detail) return "An error occurred";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map(e => (e?.msg || e?.message || "Validation error")).join(", ");
  }
  if (typeof detail === "object") {
    if (detail.detail) return formatErrorMessage(detail.detail);
    return detail.msg || detail.message || JSON.stringify(detail);
  }
  return String(detail);
}

export const toDisplayError = (err) => formatErrorMessage(err);