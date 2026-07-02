import { motion } from "framer-motion";
import { Bell, Shield, User } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/providers/auth-provider";

export function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="max-w-3xl space-y-8">
      <div>
        <h2 className="text-lg font-semibold text-foreground">Settings</h2>
        <p className="text-sm text-muted-foreground">
          Manage your account settings and preferences
        </p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="space-y-6"
      >
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-sm font-semibold">Profile Information</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Your personal information and email address
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Full name</p>
                <p className="text-sm font-medium text-foreground">{user?.full_name}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Email</p>
                <p className="text-sm font-medium text-foreground">{user?.email}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Bell className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-sm font-semibold">Notifications</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Configure how you receive notifications
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Notification preferences will be available soon.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-sm font-semibold">Security</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Manage your password and account security
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg bg-secondary p-4">
              <p className="text-sm font-medium text-foreground">Password</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Password management will be available in a future update.
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
