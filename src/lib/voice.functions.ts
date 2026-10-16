import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

const VOICE_ID = "ii0s2u4R3UFnxKL6DOrz";
const MODEL_ID = "eleven_multilingual_v2";

export const speakText = createServerFn({ method: "POST" })
  .inputValidator(z.object({ text: z.string().trim().min(1).max(1200) }))
  .handler(async ({ data }) => {
    const apiKey = process.env["ELEVENLABS_API_KEY"];
    if (!apiKey) throw new Error("Voice is not connected to this project.");
    const res = await fetch(
      `https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}?output_format=mp3_44100_128`,
      {
        method: "POST",
        headers: { "xi-api-key": apiKey, "Content-Type": "application/json" },
        body: JSON.stringify({ text: data.text, model_id: MODEL_ID }),
      },
    );
    if (!res.ok) {
      const body = await res.text();
      console.error(`ElevenLabs failed [${res.status}]: ${body}`);
      throw new Error(`Voice request failed (${res.status}). ${body.slice(0, 200)}`);
    }
    const audio = Buffer.from(await res.arrayBuffer()).toString("base64");
    return { audio };
  });
