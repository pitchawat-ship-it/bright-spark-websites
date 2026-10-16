import { useRef, useState } from "react";
import { Mic, Square } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { transcribeAudio } from "@/lib/voice.functions";

export function VoiceInput({ onText }: { onText: (t: string) => void }) {
  const [state, setState] = useState<"idle" | "rec" | "busy">("idle");
  const rec = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);

  async function start() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunks.current = [];
      mr.ondataavailable = (e) => e.data.size && chunks.current.push(e.data);
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setState("busy");
        try {
          const blob = new Blob(chunks.current, { type: mr.mimeType || "audio/webm" });
          const buf = new Uint8Array(await blob.arrayBuffer());
          let bin = "";
          for (let i = 0; i < buf.length; i += 0x8000) bin += String.fromCharCode(...buf.subarray(i, i + 0x8000));
          const { text } = await transcribeAudio({ data: { audio: btoa(bin), mime: blob.type } });
          if (text.trim()) {
            onText(text.trim());
            toast.success("Transcribed. Please check the text and confirm the amounts below.");
          } else toast.info("No speech detected. Please try again.");
        } catch (e) {
          toast.error(e instanceof Error ? e.message : "Transcription failed.");
        } finally {
          setState("idle");
        }
      };
      mr.start();
      rec.current = mr;
      setState("rec");
    } catch {
      toast.error("Microphone access was blocked. Please allow it or type your update.");
    }
  }

  return (
    <Button
      variant="outline"
      type="button"
      disabled={state === "busy"}
      onClick={() => (state === "rec" ? rec.current?.stop() : start())}
    >
      {state === "rec" ? <Square /> : <Mic />}
      {state === "rec" ? "Stop and transcribe" : state === "busy" ? "Transcribing…" : "Speak to update my situation"}
    </Button>
  );
}
