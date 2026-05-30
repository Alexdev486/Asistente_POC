import { type ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils/cn";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "gradient";
type ButtonSize = "sm" | "md" | "lg";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
};

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-accent-1 text-white hover:bg-blue-500 active:bg-blue-700 disabled:opacity-50",
  secondary:
    "border border-border-default bg-surface-tertiary text-text-primary hover:bg-surface-elevated hover:border-border-hover disabled:opacity-50",
  ghost:
    "text-text-secondary hover:text-text-primary hover:bg-surface-tertiary disabled:opacity-50",
  danger:
    "border border-red-800 bg-red-950/40 text-red-300 hover:bg-red-900/60 disabled:opacity-50",
  gradient:
    "text-white disabled:opacity-50 relative overflow-hidden",
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "px-2.5 py-1 text-xs rounded-lg",
  md: "px-4 py-2 text-sm rounded-xl",
  lg: "px-6 py-3 text-base rounded-xl",
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", loading, className, children, disabled, ...props }, ref) => {
    const isGradient = variant === "gradient";

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          "inline-flex items-center justify-center gap-2 font-semibold transition-all duration-200",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-1/40",
          "disabled:cursor-not-allowed",
          variantStyles[variant],
          sizeStyles[size],
          isGradient && "bg-gradient-to-r from-accent-1 to-accent-2 hover:shadow-glow active:scale-[0.98]",
          !isGradient && "hover:scale-[1.02] active:scale-[0.98]",
          className,
        )}
        {...props}
      >
        {loading ? (
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
        ) : null}
        {children}
      </button>
    );
  },
);

Button.displayName = "Button";
export { Button };
export type { ButtonProps };
