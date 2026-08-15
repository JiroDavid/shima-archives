import "server-only";

import type { TwitchChannel } from "@/lib/types";

const API_URL = process.env.API_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {}

export async function getChannel(username: string): Promise<TwitchChannel | null> {
  const response = await fetch(`${API_URL}/channel/${encodeURIComponent(username)}`, {
    cache: "no-store",
  });

  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new ApiError(`Channel lookup failed (${response.status})`);
  }

  return (await response.json()) as TwitchChannel;
}
