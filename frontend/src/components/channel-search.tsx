"use client";

import Image from "next/image";
import { useActionState } from "react";
import { useFormStatus } from "react-dom";

import { searchChannel } from "@/app/actions";
import { initialChannelSearchState } from "@/lib/channel-search-state";

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="rounded-full bg-purple-600 px-6 py-2 font-medium text-white transition-colors hover:bg-purple-500 disabled:opacity-50"
    >
      {pending ? "Searching…" : "Search"}
    </button>
  );
}

export function ChannelSearch() {
  const [state, formAction] = useActionState(searchChannel, initialChannelSearchState);

  return (
    <div className="flex w-full max-w-md flex-col items-center gap-6">
      <form action={formAction} className="flex w-full gap-2">
        <input
          type="text"
          name="username"
          placeholder="Twitch username"
          autoComplete="off"
          className="flex-1 rounded-full border border-zinc-300 bg-white px-4 py-2 text-black outline-none focus:border-purple-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-white"
        />
        <SubmitButton />
      </form>

      {state.error !== null && <p className="text-sm text-red-500">{state.error}</p>}

      {state.notFound && (
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          No channel found for &ldquo;{state.query}&rdquo;.
        </p>
      )}

      {state.channel !== null && (
        <a
          href={`https://twitch.tv/${state.channel.login}`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex w-full items-center gap-4 rounded-2xl border border-zinc-200 p-4 transition-colors hover:border-purple-400 dark:border-zinc-800"
        >
          {state.channel.profile_image_url !== "" && (
            <Image
              src={state.channel.profile_image_url}
              alt={state.channel.display_name}
              width={56}
              height={56}
              className="rounded-full"
            />
          )}
          <div>
            <p className="font-semibold">{state.channel.display_name}</p>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              @{state.channel.login}
            </p>
          </div>
        </a>
      )}
    </div>
  );
}
