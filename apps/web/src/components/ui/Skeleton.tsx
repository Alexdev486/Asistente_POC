import { cn } from "@/lib/utils/cn";

type SkeletonProps = {
  className?: string;
  variant?: "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
};

export function Skeleton({ className, variant = "text", width, height }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-shimmer rounded-md bg-shimmer bg-[length:200%_100%]",
        variant === "circular" && "rounded-full",
        variant === "text" && "h-4 w-full",
        variant === "rectangular" && "h-24 w-full",
        className,
      )}
      style={{ width, height }}
    />
  );
}

export function ChatSkeleton() {
  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="flex justify-end">
        <div className="w-3/5 space-y-2">
          <Skeleton variant="text" className="h-10 rounded-[18px] rounded-br-[4px]" />
        </div>
      </div>
      <div className="flex justify-start">
        <div className="w-4/5 space-y-2">
          <Skeleton variant="text" className="h-16 rounded-[18px] rounded-bl-[4px]" />
        </div>
      </div>
      <div className="flex justify-end">
        <div className="w-2/5 space-y-2">
          <Skeleton variant="text" className="h-8 rounded-[18px] rounded-br-[4px]" />
        </div>
      </div>
      <div className="flex justify-start">
        <div className="w-3/4 space-y-2">
          <Skeleton variant="text" className="h-12 rounded-[18px] rounded-bl-[4px]" />
        </div>
      </div>
    </div>
  );
}
