import { Car } from "lucide-react"
import { BrandingSidebar } from "./_components/BrandingSidebar"
import { LoginForm } from "./_components/LoginForm"

export default function LoginPage() {
  return (
    <main className="min-h-screen flex">
      <BrandingSidebar />

      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <div className="lg:hidden flex items-center gap-3 justify-center absolute top-8">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
            <Car className="w-6 h-6 text-primary-foreground" />
          </div>
          <span className="text-xl font-semibold tracking-tight text-foreground">DriveEase</span>
        </div>

        <LoginForm />
      </div>
    </main>
  )
}
