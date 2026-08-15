"use server";

import { ApiError, getChannel } from "@/lib/api";
import type { ChannelSearchState } from "@/lib/channel-search-state";

export async function searchChannel(
  _prevState: ChannelSearchState,
  formData: FormData,
): Promise<ChannelSearchState> {
  const query = String(formData.get("username") ?? "").trim();
  if (query === "") {
    return { query, channel: null, notFound: false, error: "Enter a channel name." };
  }

  try {
    const channel = await getChannel(query);
    if (channel === null) {
      return { query, channel: null, notFound: true, error: null };
    }
    return { query, channel, notFound: false, error: null };
  } catch (err) {
    const message = err instanceof ApiError ? err.message : "Something went wrong.";
    return { query, channel: null, notFound: false, error: message };
  }
}
