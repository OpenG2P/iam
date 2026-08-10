export async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result;
      if (typeof result !== "string") {
        reject(new Error("Failed to read file"));
        return;
      }
      const comma = result.indexOf(",");
      resolve(comma >= 0 ? result.slice(comma + 1) : result);
    };
    reader.onerror = () => reject(reader.error ?? new Error("Failed to read file"));
    reader.readAsDataURL(file);
  });
}

export function iconDataUrl(
  base64: string | null | undefined,
  mimeType = "image/png",
): string | null {
  if (!base64?.trim()) return null;
  if (base64.startsWith("data:")) return base64;
  return `data:${mimeType};base64,${base64}`;
}

export function detectMimeType(base64: string): string {
  // Try to detect MIME type from base64 string patterns
  if (base64.startsWith('PHN2Zy') || base64.startsWith('<?xml') || base64.includes('<svg')) {
    return 'image/svg+xml';
  }
  if (base64.startsWith('/9j/')) {
    return 'image/jpeg';
  }
  if (base64.startsWith('iVBORw0KGgo')) {
    return 'image/png';
  }
  if (base64.startsWith('R0lGODdh') || base64.startsWith('R0lGODlh')) {
    return 'image/gif';
  }
  if (base64.startsWith('Qk0')) {
    return 'image/bmp';
  }
  // Default to PNG for IAM staff UI
  return 'image/png';
}
