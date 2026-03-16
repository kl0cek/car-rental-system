import { Car, CalendarCheck, Users, TrendingUp, Clock, MapPin, ArrowUpRight, ArrowDownRight } from "lucide-react"
import BookingsList from "@/src/components/dashboard/BookingList"
import UpcomingReturns from "@/src/components/dashboard/UpcomingReturns"

const stats = [
  {
    name: "Active Bookings",
    value: "24",
    change: "+12%",
    trend: "up",
    icon: CalendarCheck,
  },
  {
    name: "Available Cars",
    value: "156",
    change: "-3%",
    trend: "down",
    icon: Car,
  },
  {
    name: "Total Customers",
    value: "1,429",
    change: "+8%",
    trend: "up",
    icon: Users,
  },
  {
    name: "Revenue This Month",
    value: "$48,250",
    change: "+23%",
    trend: "up",
    icon: TrendingUp,
  },
]

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Welcome back! Here&apos;s your rental overview.
          </p>
        </div>
        <button className="inline-flex items-center justify-center h-10 px-4 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors">
          + New Booking
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="bg-card rounded-xl border border-border p-5 hover:shadow-sm transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center">
                <stat.icon className="w-5 h-5 text-foreground" />
              </div>
              <div
                className={`flex items-center gap-1 text-xs font-medium ${
                  stat.trend === "up" ? "text-accent" : "text-destructive"
                }`}
              >
                {stat.change}
                {stat.trend === "up" ? (
                  <ArrowUpRight className="w-3 h-3" />
                ) : (
                  <ArrowDownRight className="w-3 h-3" />
                )}
              </div>
            </div>
            <div className="mt-4">
              <p className="text-2xl font-semibold text-foreground">{stat.value}</p>
              <p className="text-sm text-muted-foreground mt-1">{stat.name}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <BookingsList />
        </div>

        <div>
          <UpcomingReturns />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <button className="flex items-center gap-4 p-4 bg-card rounded-xl border border-border hover:border-primary/50 hover:shadow-sm transition-all text-left">
          <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
            <CalendarCheck className="w-6 h-6 text-primary" />
          </div>
          <div>
            <p className="font-medium text-foreground">Schedule Pickup</p>
            <p className="text-sm text-muted-foreground">Arrange customer pickup</p>
          </div>
        </button>
        <button className="flex items-center gap-4 p-4 bg-card rounded-xl border border-border hover:border-primary/50 hover:shadow-sm transition-all text-left">
          <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center">
            <Clock className="w-6 h-6 text-accent" />
          </div>
          <div>
            <p className="font-medium text-foreground">Extend Rental</p>
            <p className="text-sm text-muted-foreground">Modify booking duration</p>
          </div>
        </button>
        <button className="flex items-center gap-4 p-4 bg-card rounded-xl border border-border hover:border-primary/50 hover:shadow-sm transition-all text-left">
          <div className="w-12 h-12 rounded-lg bg-secondary flex items-center justify-center">
            <MapPin className="w-6 h-6 text-foreground" />
          </div>
          <div>
            <p className="font-medium text-foreground">Track Vehicle</p>
            <p className="text-sm text-muted-foreground">Real-time location</p>
          </div>
        </button>
      </div>
    </div>
  )
}
