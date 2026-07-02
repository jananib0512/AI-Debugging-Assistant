import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import type { ReactNode } from "react";

import { api } from "@/lib/api";
import type { AuthResponse, LoginInput, RegisterInput, User } from "@/types/auth";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  lastLogin: string | null;
  login: (input: LoginInput) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastLogin, setLastLogin] = useState<string | null>(
    () => localStorage.getItem("last_login"),
  );

  const isAuthenticated = user !== null;

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setIsLoading(false);
      return;
    }
    api
      .get<User>("/auth/me")
      .then((res) => setUser(res.data))
      .catch(() => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        localStorage.removeItem("last_login");
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (input: LoginInput) => {
    const res = await api.post<AuthResponse>("/auth/login", input);
    localStorage.setItem("access_token", res.data.access_token);
    const now = new Date().toISOString();
    localStorage.setItem("last_login", now);
    setLastLogin(now);
    setUser(res.data.user);
  }, []);

  const register = useCallback(async (input: RegisterInput) => {
    const res = await api.post<AuthResponse>("/auth/register", input);
    localStorage.setItem("access_token", res.data.access_token);
    const now = new Date().toISOString();
    localStorage.setItem("last_login", now);
    setLastLogin(now);
    setUser(res.data.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post("/auth/logout");
    } finally {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      localStorage.removeItem("last_login");
      setUser(null);
      setLastLogin(null);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated, isLoading, lastLogin, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
