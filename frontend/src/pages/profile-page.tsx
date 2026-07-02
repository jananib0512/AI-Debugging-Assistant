import { motion } from "framer-motion";
import {
  Calendar,
  Clock,
  Mail,
  User,
} from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "@/providers/auth-provider";

function formatDate(dateString: string) {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(dateString));
}

export function ProfilePage() {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <div className="max-w-3xl space-y-8">
      <div>
        <h2 className="text-lg font-semibold text-foreground">Profile</h2>
        <p className="text-sm text-muted-foreground">
          Your account information
        </p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card className="mb-6">
          <CardContent className="p-8">
            <div className="flex items-center gap-6">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-50">
                <span className="text-2xl font-bold text-primary">
                  {user.full_name.charAt(0).toUpperCase()}
                </span>
              </div>
              <div>
                <h2 className="text-xl font-bold text-foreground">{user.full_name}</h2>
                <p className="text-sm text-muted-foreground">{user.email}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 sm:grid-cols-2">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-muted-foreground" />
                <CardTitle className="text-sm font-semibold">Full name</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-foreground">{user.full_name}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <CardTitle className="text-sm font-semibold">Email</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-foreground">{user.email}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <CardTitle className="text-sm font-semibold">
                  Member since
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-foreground">{formatDate(user.created_at)}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <CardTitle className="text-sm font-semibold">
                  Last updated
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-foreground">{formatDate(user.updated_at)}</p>
            </CardContent>
          </Card>
        </div>
      </motion.div>
    </div>
  );
}
