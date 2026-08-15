import { ChannelSearch } from "@/components/channel-search";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-10 bg-zinc-50 px-6 py-24 dark:bg-black">
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-black dark:text-white">
          ShimaVault
        </h1>
        <p className="text-zinc-600 dark:text-zinc-400">
          Search a channel to browse VODs, clips, and chat history.
        </p>
      </div>
      <ChannelSearch />
    </div>
  );
}
