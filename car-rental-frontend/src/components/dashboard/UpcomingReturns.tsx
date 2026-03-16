import { Clock, ChevronRight } from "lucide-react"
import type { Return } from "@/src/types/dashboard/booking"
import { mockReturns } from "@/src/data/dashboard/mockReturns"

interface UpcomingReturnsProps {
  returns?: Return[]
}

export default function UpcomingReturns({ returns = mockReturns }: UpcomingReturnsProps) {
  return (
    <div className="bg-card rounded-xl border border-border h-full">

      <div className="flex items-center justify-between p-5 border-b border-border">
        <div>
          <h2 className="font-semibold text-foreground">Upcoming Returns</h2>
          <p className="text-sm text-muted-foreground mt-0.5">Vehicles due for return</p>
        </div>
        <div className="w-8 h-8 rounded-lg bg-secondary flex items-center justify-center">
          <Clock className="w-4 h-4 text-foreground" />
        </div>
      </div>

      <div className="divide-y divide-border">
        {returns.map((item) => (
          <button
            key={item.id}
            className="w-full flex items-center gap-3 p-4 hover:bg-secondary/50 transition-colors text-left"
          >
            <div
              className={`w-2 h-2 rounded-full shrink-0 ${
                item.urgent ? "bg-destructive" : "bg-accent"
              }`}
            />
            <div className="flex-1 min-w-0">
              <p className="font-medium text-foreground truncate">{item.customer}</p>
              <p className="text-sm text-muted-foreground truncate">{item.car}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-muted-foreground">{item.returnTime}</span>
                <span className="text-xs text-muted-foreground">•</span>
                <span className="text-xs text-muted-foreground truncate">{item.location}</span>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />
          </button>
        ))}
      </div>

      <div className="p-4 border-t border-border">
        <button className="w-full text-sm text-primary font-medium hover:text-primary/80 transition-colors">
          View all returns
        </button>
      </div>

    </div>
  )
}
