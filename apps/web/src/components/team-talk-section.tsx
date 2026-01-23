import { HypePlayer } from "@/components/hype-player";
import type { HypeState } from "@/hooks/use-hype-generation";

type TeamTalkSectionProps = {
  hypeState: HypeState;
  managerName: string;
  onRegenerate: () => void;
};

export const TeamTalkSection = ({
  hypeState,
  managerName,
  onRegenerate,
}: TeamTalkSectionProps) => {
  if (hypeState.status === "idle") {
    return null;
  }

  return (
    <div className="pt-4">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Your Team Talk</h2>
      <HypePlayer
        hypeText={hypeState.hypeText}
        audioUrl={hypeState.audioUrl}
        status={hypeState.status}
        managerName={managerName}
        onRegenerate={onRegenerate}
      />
    </div>
  );
};
