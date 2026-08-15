// Mirrors backend/app/schemas/channel.py TwitchChannel
export interface TwitchChannel {
  twitch_id: string;
  login: string;
  display_name: string;
  description: string;
  profile_image_url: string;
  broadcaster_type: string;
  created_at: string | null;
}
