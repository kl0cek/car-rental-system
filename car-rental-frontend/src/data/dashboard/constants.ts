import {
  Car,
  LayoutDashboard,
  CalendarDays,
  Users,
  Settings,
  HelpCircle,
} from "lucide-react"
import type { BookingStatus, NavItem } from "@/src/types/dashboard/booking"

export const navigation: NavItem[] = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Bookings", href: "/dashboard/bookings", icon: CalendarDays },
  { name: "Fleet", href: "/dashboard/fleet", icon: Car },
  { name: "Customers", href: "/dashboard/customers", icon: Users },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
]

export const secondaryNavigation: NavItem[] = [
  { name: "Help Center", href: "#", icon: HelpCircle },
]

export const bookingStatusStyles: Record<BookingStatus, string> = {
  active: "bg-accent/15 text-accent",
  pending: "bg-yellow-500/15 text-yellow-600",
  completed: "bg-muted text-muted-foreground",
  confirmed: "bg-primary/15 text-primary",
}
