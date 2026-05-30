"use client";

import { DotLottieReact } from "@lottiefiles/dotlottie-react";
import { cn } from "@/lib/utils/cn";

type LoaderProps = {
  src?: string;
  size?: number;
  className?: string;
  loop?: boolean;
  autoplay?: boolean;
};

export function Loader({
  src = "/design/robotloading.lottie",
  size = 48,
  className,
  loop = true,
  autoplay = true,
}: LoaderProps) {
  return (
    <div
      className={cn("flex items-center justify-center", className)}
      style={{ width: size, height: size }}
    >
      <DotLottieReact
        src={src}
        loop={loop}
        autoplay={autoplay}
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
}
