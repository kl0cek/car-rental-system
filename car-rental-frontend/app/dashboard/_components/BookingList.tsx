"use client"

import { MoreHorizontal, Eye } from "lucide-react"

const bookings = [
  {
    id: "BK-001",
    customer: "Sarah Johnson",
    email: "sarah.j@email.com",
    car: "BMW 3 Series",
    licensePlate: "ABC-1234",
    startDate: "Mar 14, 2026",
    endDate: "Mar 18, 2026",
    status: "active",
    total: "$420",
  },
  {
    id: "BK-002",
    customer: "Michael Chen",
    email: "m.chen@email.com",
    car: "Mercedes C-Class",
    licensePlate: "XYZ-5678",
    startDate: "Mar 15, 2026",
    endDate: "Mar 17, 2026",
    status: "pending",
    total: "$280",
  },
  {
    id: "BK-003",
    customer: "Emily Davis",
    email: "emily.d@email.com",
    car: "Audi A4",
    licensePlate: "DEF-9012",
    startDate: "Mar 12, 2026",
    endDate: "Mar 14, 2026",
    status: "completed",
    total: "$320",
  },
  {
    id: "BK-004",
    customer: "James Wilson",
    email: "j.wilson@email.com",
    car: "Tesla Model 3",
    licensePlate: "GHI-3456",
    startDate: "Mar 16, 2026",
    endDate: "Mar 20, 2026",
    status: "confirmed",
    total: "$560",
  },
  {
    id: "BK-005",
    customer: "Lisa Anderson",
    email: "lisa.a@email.com",
    car: "Porsche Cayenne",
    licensePlate: "JKL-7890",
    startDate: "Mar 14, 2026",
    endDate: "Mar 21, 2026",
    status: "active",
    total: "$980",
  },
]

const statusStyles: Record<string, string> = {
  active: "bg-accent/15 text-accent",
  pending: "bg-yellow-500/15 text-yellow-600",
  completed: "bg-muted text-muted-foreground",
  confirmed: "bg-primary/15 text-primary",
}

export default function BookingsList() {
  return (
    <div className="bg-card rounded-xl border border-border">
      <div className="flex items-center justify-between p-5 border-b border-border">
        <div>
          <h2 className="font-semibold text-foreground">Recent Bookings</h2>
          <p className="text-sm text-muted-foreground mt-0.5">Manage your rental reservations</p>
        </div>
        <button className="text-sm text-primary font-medium hover:text-primary/80 transition-colors">
          View all
        </button>
      </div>

      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-5 py-3">
                Customer
              </th>
              <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-5 py-3">
                Vehicle
              </th>
              <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-5 py-3">
                Duration
              </th>
              <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-5 py-3">
                Status
              </th>
              <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-5 py-3">
                Total
              </th>
              <th className="text-right text-xs font-medium text-muted-foreground uppercase tracking-wider px-5 py-3">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {bookings.map((booking) => (
              <tr key={booking.id} className="hover:bg-secondary/50 transition-colors">
                <td className="px-5 py-4">
                  <div>
                    <p className="font-medium text-foreground">{booking.customer}</p>
                    <p className="text-sm text-muted-foreground">{booking.email}</p>
                  </div>
                </td>
                <td className="px-5 py-4">
                  <div>
                    <p className="font-medium text-foreground">{booking.car}</p>
                    <p className="text-sm text-muted-foreground">{booking.licensePlate}</p>
                  </div>
                </td>
                <td className="px-5 py-4">
                  <div>
                    <p className="text-sm text-foreground">{booking.startDate}</p>
                    <p className="text-sm text-muted-foreground">to {booking.endDate}</p>
                  </div>
                </td>
                <td className="px-5 py-4">
                  <span
                    className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium capitalize ${statusStyles[booking.status]}`}
                  >
                    {booking.status}
                  </span>
                </td>
                <td className="px-5 py-4">
                  <p className="font-medium text-foreground">{booking.total}</p>
                </td>
                <td className="px-5 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button className="p-2 rounded-lg text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors">
                      <Eye className="w-4 h-4" />
                    </button>
                    <button className="p-2 rounded-lg text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors">
                      <MoreHorizontal className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="md:hidden divide-y divide-border">
        {bookings.map((booking) => (
          <div key={booking.id} className="p-4 space-y-3">
            <div className="flex items-start justify-between">
              <div>
                <p className="font-medium text-foreground">{booking.customer}</p>
                <p className="text-sm text-muted-foreground">{booking.car}</p>
              </div>
              <span
                className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium capitalize ${statusStyles[booking.status]}`}
              >
                {booking.status}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                {booking.startDate} - {booking.endDate}
              </span>
              <span className="font-medium text-foreground">{booking.total}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
