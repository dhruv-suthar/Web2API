import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "info"
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        {
          "border-transparent bg-amber-600 text-white shadow hover:bg-amber-700": variant === "default",
          "border-transparent bg-zinc-800 text-zinc-50 hover:bg-zinc-700": variant === "secondary",
          "border-transparent bg-red-600 text-white shadow hover:bg-red-700": variant === "destructive",
          "text-zinc-50 border-zinc-700": variant === "outline",
          "border-transparent bg-green-600 text-white shadow hover:bg-green-700": variant === "success",
          "border-transparent bg-yellow-600 text-white shadow hover:bg-yellow-700": variant === "warning",
          "border-transparent bg-blue-600 text-white shadow hover:bg-blue-700": variant === "info",
        },
        className
      )}
      {...props}
    />
  )
}

export { Badge }

