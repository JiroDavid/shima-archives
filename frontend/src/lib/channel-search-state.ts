import type { TwitchChannel } from "@/lib/types";

export type ChannelSearchState = {
  query: string;
  channel: TwitchChannel | null;
  notFound: boolean;
  error: string | null;
};

export const initialChannelSearchState: ChannelSearchState = {
  query: "",
  channel: null,
  notFound: false,
  error: null,
};
