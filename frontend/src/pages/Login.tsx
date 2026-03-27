import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Eye, EyeOff, Loader2, ScanFace } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { authApi } from "@/services/authApi";
import { useAuthStore } from "@/store/authStore";
import { getErrorMessage } from "@/services/api";
import darkLogoUrl from "@/assets/dark_logo.png";
import whiteLogoUrl from "@/assets/white_logo.png";

const loginSchema = z.object({
  username: z.string().min(1, "Foydalanuvchi nomi kiritilishi shart"),
  password: z.string().min(1, "Parol kiritilishi shart"),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setTokens, setUser } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const from =
    (location.state as { from?: { pathname: string } })?.from?.pathname ?? "/";

  const onSubmit = async (data: LoginForm) => {
    try {
      const res = await authApi.login(data);
      const { access_token, refresh_token } = res.data.data;
      setTokens(access_token, refresh_token);

      const meRes = await authApi.getMe();
      setUser(meRes.data.data);

      toast.success("Tizimga muvaffaqiyatli kirdingiz");
      navigate(from, { replace: true });
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      {/* Left branding panel — brand navy background */}
      <div className="hidden lg:flex w-[45%] relative flex-col justify-between overflow-hidden bg-[hsl(252,100%,15%)]">
        {/* Subtle light blobs */}
        <div className="absolute inset-0 z-0 pointer-events-none">
          <div className="absolute -top-1/4 -left-1/4 w-3/4 h-3/4 rounded-full bg-primary/30 blur-[80px]" />
          <div className="absolute bottom-0 right-0 w-1/2 h-1/2 rounded-full bg-indigo-500/20 blur-[100px]" />
        </div>

        <div className="relative z-10 flex flex-col h-full p-12 text-white">
          {/* Logo */}
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl overflow-hidden flex-shrink-0">
              <img
                src={darkLogoUrl}
                alt="AttendX Logo"
                className="w-full h-full object-contain"
              />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">AttendX</h1>
              <p className="text-xs text-white/50 mt-0.5">Smart Attendance System</p>
            </div>
          </div>

          {/* Hero text */}
          <div className="mt-auto mb-auto pt-20">
            <div className="inline-flex items-center gap-2 bg-white/10 rounded-full px-4 py-1.5 mb-6">
              <ScanFace className="w-4 h-4 text-indigo-300" />
              <span className="text-xs font-medium text-white/80">
                Yuz tanish texnologiyasi
              </span>
            </div>
            <h2 className="text-4xl font-extrabold leading-tight tracking-tight text-white">
              Muhammad al-Xorazmiy<br />
              <span className="text-indigo-300">IT Maktabi</span><br />
              Nukus filiali
            </h2>
            <p className="mt-5 text-base text-white/60 max-w-sm leading-relaxed">
              Zamonaviy yuz tanish texnologiyasi asosida qurilgan aqlli
              davomat boshqaruv tizimi.
            </p>
          </div>

          {/* Footer note */}
          <p className="text-xs text-white/30 font-medium">
            © 2026 AttendX — Barcha huquqlar himoyalangan
          </p>
        </div>
      </div>

      {/* Right login panel */}
      <div className="flex flex-1 flex-col items-center justify-center p-6 bg-background">
        <div className="w-full max-w-sm animate-in fade-in slide-in-from-bottom-6 duration-500">

          {/* Mobile logo (only on small screens) */}
          <div className="lg:hidden flex flex-col items-center text-center mb-8">
            <div className="w-16 h-16 mb-3 rounded-2xl overflow-hidden ring-4 ring-primary/10">
              <img
                src={whiteLogoUrl}
                alt="AttendX Logo"
                className="w-full h-full object-contain"
              />
            </div>
            <h1 className="text-xl font-bold text-foreground">AttendX</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Al-Xorazmiy IT Maktabi — Nukus
            </p>
          </div>

          {/* Login card */}
          <div className="bg-card rounded-2xl border border-border shadow-sm p-8">
            <div className="mb-7">
              <h2 className="text-2xl font-bold tracking-tight text-foreground">
                Kirish
              </h2>
              <p className="text-sm text-muted-foreground mt-1.5">
                Boshqaruv paneliga kirish uchun ma'lumotlaringizni kiriting
              </p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              <div className="space-y-1.5">
                <Label htmlFor="username" className="text-sm font-semibold">
                  Foydalanuvchi nomi
                </Label>
                <Input
                  id="username"
                  placeholder="admin"
                  autoComplete="username"
                  className="h-11 focus-visible:ring-primary/40 transition-shadow"
                  {...register("username")}
                />
                {errors.username && (
                  <p className="text-xs text-destructive font-medium animate-in fade-in slide-in-from-top-1">
                    {errors.username.message}
                  </p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="password" className="text-sm font-semibold">
                  Parol
                </Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    autoComplete="current-password"
                    className="h-11 focus-visible:ring-primary/40 pr-10 transition-shadow"
                    {...register("password")}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="absolute right-1 top-0.5 h-10 w-10 text-muted-foreground hover:text-foreground hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                {errors.password && (
                  <p className="text-xs text-destructive font-medium animate-in fade-in slide-in-from-top-1">
                    {errors.password.message}
                  </p>
                )}
              </div>

              <Button
                type="submit"
                className="w-full h-11 text-sm font-semibold premium-shadow hover:-translate-y-0.5 transition-all duration-200"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : null}
                {isSubmitting ? "Kirish..." : "Tizimga kirish"}
              </Button>
            </form>
          </div>

          <p className="text-center text-xs text-muted-foreground mt-5">
            Muammo bormi?{" "}
            <span className="text-primary cursor-pointer hover:underline">
              Texnik qo'llab-quvvatlash
            </span>{" "}
            bilan bog'laning.
          </p>
        </div>
      </div>
    </div>
  );
}
