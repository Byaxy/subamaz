import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { useLogin } from "@/lib/queries/auth"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"

export const Route = createFileRoute("/login")({
  component: LoginPage,
})

export function LoginPage() {
  const navigate = useNavigate()
  const login = useLogin()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    try {
      await login.mutateAsync({ username: email, password })
      navigate({ to: "/" })
    } catch (err: any) {
      setError(err?.message || "Login failed")
    }
  }

  return (
    <div className="min-h-screen flex" data-testid="portal-login">
      <div className="hidden md:flex w-1/2 flex-col justify-between p-10 text-white" style={{ background: "linear-gradient(135deg, #1A1A1A 0%, #000 100%)" }}>
        <div>
          <div className="size-12 rounded bg-[var(--app-primary)] text-[var(--app-btn-primary-text)] flex items-center justify-center font-bold">GM</div>
          <h1 className="text-3xl font-bold mt-6">Customer Portal</h1>
          <p className="text-white/70 mt-2">Track your vehicle service</p>
        </div>
        <div className="text-sm text-white/60">© {new Date().getFullYear()} SubaMaz</div>
      </div>
      <div className="flex-1 flex items-center justify-center bg-muted/30 p-6">
        <Card className="w-full max-w-sm">
          <CardHeader><CardTitle>Sign in</CardTitle><CardDescription>Customer portal — email + password</CardDescription></CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="flex flex-col gap-4" data-testid="login-form">
              <div className="flex flex-col gap-1.5"><Label htmlFor="email">Email</Label><Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required data-testid="login-email" /></div>
              <div className="flex flex-col gap-1.5"><Label htmlFor="password">Password</Label><Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required data-testid="login-password" /></div>
              {error && <div className="text-sm text-destructive" data-testid="login-error">{error}</div>}
              <Button type="submit" disabled={login.isPending} className="w-full" data-testid="login-submit">{login.isPending ? "Signing in..." : "Continue"}</Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
