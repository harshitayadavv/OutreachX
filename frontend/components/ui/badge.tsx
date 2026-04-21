import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-[#7F77DD]/20 text-[#7F77DD]",
        draft: "bg-gray-100 text-gray-600",
        approved: "bg-green-50 text-green-700",
        sent: "bg-blue-50 text-blue-700",
        opened: "bg-amber-50 text-amber-700",
        replied: "bg-purple-50 text-purple-700",
        active: "bg-green-50 text-green-700",
        paused: "bg-amber-50 text-amber-700",
        completed: "bg-blue-50 text-blue-700",
      },
    },
    defaultVariants: { variant: "default" },
  }
)

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }