import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

type GoogleReconnectBannerProps = {
  onReconnect: () => void;
};

export const GoogleReconnectBanner = ({ onReconnect }: GoogleReconnectBannerProps) => {
  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <AlertCircle className="h-5 w-5 text-amber-600" />
        <div>
          <p className="font-medium text-amber-800">Connect your Google Calendar</p>
          <p className="text-sm text-amber-600">Grant access to see your meetings</p>
        </div>
      </div>
      <Button
        onClick={onReconnect}
        className="bg-amber-600 hover:bg-amber-700"
      >
        Connect Google
      </Button>
    </div>
  );
};
